from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.consent import ConsentRecord
from app.core.logging import logger

# In-memory synchronized fallback store for offline / test execution
_MEM_CONSENTS: Dict[str, Dict[str, Any]] = {}
_LAST_DB_CHECK_FAILED: float = 0.0
_DB_RETRY_INTERVAL_SECONDS: float = 30.0


def _init_memory_store():
    global _MEM_CONSENTS
    if not _MEM_CONSENTS:
        # Pre-populate with standard seed consents matching seed_applications.py
        from app.db.seed_applications import DEMO_APPLICATIONS
        now = datetime.now(timezone.utc)
        future_expiry = now + timedelta(days=365)
        for a in DEMO_APPLICATIONS:
            c_ref = a.get("consent_reference")
            if c_ref:
                c_rec = a.get("consent_record", {})
                _MEM_CONSENTS[c_ref] = {
                    "id": f"CONS-{a['id']}",
                    "consent_reference": c_ref,
                    "application_id": a["application_id"],
                    "status": c_rec.get("status", "VALID"),
                    "purpose": c_rec.get("purpose", a.get("purpose", "Update Revenue address record & 7/12 land registry linkage")),
                    "data_scope": c_rec.get("data_scope", "address.change"),
                    "recipient": c_rec.get("recipient", "Revenue & Forest Department"),
                    "issued_at": a.get("received_at", now),
                    "expires_at": c_rec.get("expires_at", future_expiry),
                    "revoked_at": c_rec.get("revoked_at"),
                    "validated_at": None,
                    "validation_result": None,
                }


_init_memory_store()


class ConsentRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        _init_memory_store()

    def _should_skip_db(self) -> bool:
        global _LAST_DB_CHECK_FAILED
        if _LAST_DB_CHECK_FAILED > 0:
            if time.time() - _LAST_DB_CHECK_FAILED < _DB_RETRY_INTERVAL_SECONDS:
                return True
        return False

    def _mark_db_failed(self):
        global _LAST_DB_CHECK_FAILED
        _LAST_DB_CHECK_FAILED = time.time()

    def _to_dict(self, c: ConsentRecord) -> Dict[str, Any]:
        return {
            "id": c.id,
            "consent_reference": c.consent_reference,
            "application_id": c.application_id,
            "status": c.status,
            "purpose": c.purpose,
            "data_scope": c.data_scope,
            "recipient": c.recipient,
            "issued_at": c.issued_at,
            "expires_at": c.expires_at,
            "revoked_at": c.revoked_at,
            "validated_at": c.validated_at,
            "validation_result": c.validation_result,
        }

    def get_by_reference(self, consent_reference: str) -> Optional[Dict[str, Any]]:
        clean_ref = consent_reference.strip() if consent_reference else ""
        if not clean_ref:
            return None

        # Try PostgreSQL first
        if self.db and not self._should_skip_db():
            try:
                db_consent = (
                    self.db.query(ConsentRecord)
                    .filter(ConsentRecord.consent_reference == clean_ref)
                    .first()
                )
                if db_consent:
                    return self._to_dict(db_consent)
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_by_reference, using memory store: %s", exc)

        # Fallback to in-memory store
        return _MEM_CONSENTS.get(clean_ref)

    def get_by_application_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        clean_app_id = application_id.strip() if application_id else ""
        if not clean_app_id:
            return None

        if self.db and not self._should_skip_db():
            try:
                db_consent = (
                    self.db.query(ConsentRecord)
                    .filter(ConsentRecord.application_id == clean_app_id)
                    .first()
                )
                if db_consent:
                    return self._to_dict(db_consent)
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_by_application_id, using memory store: %s", exc)

        for c in _MEM_CONSENTS.values():
            if c.get("application_id") == clean_app_id:
                return c
        return None

    def create_consent(self, consent_data: Dict[str, Any], auto_commit: bool = True) -> Dict[str, Any]:
        c_ref = consent_data["consent_reference"]
        _MEM_CONSENTS[c_ref] = consent_data.copy()

        if self.db and not self._should_skip_db():
            try:
                db_c = ConsentRecord(
                    id=consent_data.get("id", f"CONS-{c_ref}"),
                    consent_reference=c_ref,
                    application_id=consent_data["application_id"],
                    status=consent_data.get("status", "VALID"),
                    purpose=consent_data["purpose"],
                    data_scope=consent_data.get("data_scope", "address.change"),
                    recipient=consent_data.get("recipient", "Revenue & Forest Department"),
                    issued_at=consent_data.get("issued_at", datetime.now(timezone.utc)),
                    expires_at=consent_data["expires_at"],
                    revoked_at=consent_data.get("revoked_at"),
                    validated_at=consent_data.get("validated_at"),
                    validation_result=consent_data.get("validation_result"),
                )
                self.db.add(db_c)
                if auto_commit:
                    self.db.commit()
                else:
                    self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB insert failed in create_consent: %s", exc)

        return self.get_by_reference(c_ref) or consent_data

    # Alias for convenience
    save_consent = create_consent

    def update_validation_result(
        self,
        consent_reference: str,
        status: str,
        validation_result: Dict[str, Any],
        auto_commit: bool = True,
    ) -> Optional[Dict[str, Any]]:
        clean_ref = consent_reference.strip()
        now = datetime.now(timezone.utc)

        if clean_ref in _MEM_CONSENTS:
            _MEM_CONSENTS[clean_ref]["status"] = status
            _MEM_CONSENTS[clean_ref]["validated_at"] = now
            _MEM_CONSENTS[clean_ref]["validation_result"] = validation_result

        if self.db and not self._should_skip_db():
            try:
                db_c = (
                    self.db.query(ConsentRecord)
                    .filter(ConsentRecord.consent_reference == clean_ref)
                    .first()
                )
                if db_c:
                    db_c.status = status
                    db_c.validated_at = now
                    db_c.validation_result = validation_result
                    if auto_commit:
                        self.db.commit()
                    else:
                        self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB update failed in update_validation_result: %s", exc)

        return self.get_by_reference(clean_ref)

    def revoke_consent(
        self, consent_reference: str, reason: str = "Revoked by citizen", auto_commit: bool = True
    ) -> Optional[Dict[str, Any]]:
        clean_ref = consent_reference.strip()
        now = datetime.now(timezone.utc)

        if clean_ref in _MEM_CONSENTS:
            _MEM_CONSENTS[clean_ref]["status"] = "REVOKED"
            _MEM_CONSENTS[clean_ref]["revoked_at"] = now
            res = _MEM_CONSENTS[clean_ref].get("validation_result") or {}
            res["revocation_reason"] = reason
            _MEM_CONSENTS[clean_ref]["validation_result"] = res

        if self.db and not self._should_skip_db():
            try:
                db_c = (
                    self.db.query(ConsentRecord)
                    .filter(ConsentRecord.consent_reference == clean_ref)
                    .first()
                )
                if db_c:
                    db_c.status = "REVOKED"
                    db_c.revoked_at = now
                    res = db_c.validation_result or {}
                    res["revocation_reason"] = reason
                    db_c.validation_result = res
                    if auto_commit:
                        self.db.commit()
                    else:
                        self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB revoke failed in revoke_consent: %s", exc)

        return self.get_by_reference(clean_ref)
