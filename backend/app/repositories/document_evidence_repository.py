from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import time
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.document_evidence import DocumentVerificationRecord
from app.core.logging import logger

_MEM_EVIDENCE: Dict[str, Dict[str, Any]] = {}
_LAST_DB_CHECK_FAILED: float = 0.0
_DB_RETRY_INTERVAL_SECONDS: float = 30.0


class DocumentEvidenceRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def _should_skip_db(self) -> bool:
        global _LAST_DB_CHECK_FAILED
        if _LAST_DB_CHECK_FAILED > 0:
            if time.time() - _LAST_DB_CHECK_FAILED < _DB_RETRY_INTERVAL_SECONDS:
                return True
        return False

    def _mark_db_failed(self):
        global _LAST_DB_CHECK_FAILED
        _LAST_DB_CHECK_FAILED = time.time()

    @staticmethod
    def _to_dict(rec: DocumentVerificationRecord) -> Dict[str, Any]:
        return {
            "id": rec.id,
            "document_id": rec.document_id,
            "application_id": rec.application_id,
            "document_hash": rec.document_hash,
            "provider": rec.provider,
            "status": rec.status,
            "confidence": rec.confidence,
            "extracted_fields": dict(rec.extracted_fields or {}),
            "field_confidences": dict(rec.field_confidences or {}),
            "error_message": rec.error_message,
            "processing_duration_ms": rec.processing_duration_ms,
            "correlation_id": rec.correlation_id,
            "verified_at": rec.verified_at,
            "verified_by": rec.verified_by,
        }

    def save_evidence(self, data: Dict[str, Any], auto_commit: bool = True) -> Dict[str, Any]:
        evidence_id = data.get("id") or f"EVID-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        record_dict = {
            "id": evidence_id,
            "document_id": data["document_id"],
            "application_id": data.get("application_id", ""),
            "document_hash": data.get("document_hash"),
            "provider": data.get("provider", "SIMULATED"),
            "status": data.get("status", "SUCCESS"),
            "confidence": float(data.get("confidence", 0.0)),
            "extracted_fields": dict(data.get("extracted_fields", {})),
            "field_confidences": dict(data.get("field_confidences", {})),
            "error_message": data.get("error_message"),
            "processing_duration_ms": data.get("processing_duration_ms"),
            "correlation_id": data.get("correlation_id"),
            "verified_at": data.get("verified_at") or now,
            "verified_by": data.get("verified_by"),
        }

        # Store in-memory
        _MEM_EVIDENCE[evidence_id] = record_dict

        # Store in PostgreSQL if available
        if self.db and not self._should_skip_db():
            try:
                db_rec = DocumentVerificationRecord(
                    id=record_dict["id"],
                    document_id=record_dict["document_id"],
                    application_id=record_dict["application_id"],
                    document_hash=record_dict["document_hash"],
                    provider=record_dict["provider"],
                    status=record_dict["status"],
                    confidence=record_dict["confidence"],
                    extracted_fields=record_dict["extracted_fields"],
                    field_confidences=record_dict["field_confidences"],
                    error_message=record_dict["error_message"],
                    processing_duration_ms=record_dict["processing_duration_ms"],
                    correlation_id=record_dict["correlation_id"],
                    verified_at=record_dict["verified_at"],
                    verified_by=record_dict["verified_by"],
                )
                self.db.add(db_rec)
                if auto_commit:
                    self.db.commit()
                else:
                    self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                    self._mark_db_failed()
                    logger.warning("DB insert failed in save_evidence: %s", exc)
                else:
                    raise

        return record_dict

    def get_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        clean_id = document_id.strip() if document_id else ""
        if not clean_id:
            return []

        if self.db and not self._should_skip_db():
            try:
                results = (
                    self.db.query(DocumentVerificationRecord)
                    .filter(DocumentVerificationRecord.document_id == clean_id)
                    .order_by(DocumentVerificationRecord.verified_at.desc())
                    .all()
                )
                if results:
                    return [self._to_dict(r) for r in results]
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_by_document_id: %s", exc)

        # Fallback to in-memory store
        matches = [r for r in _MEM_EVIDENCE.values() if r.get("document_id") == clean_id]
        matches.sort(key=lambda x: x.get("verified_at") or datetime.min, reverse=True)
        return matches

    def get_latest_by_document_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        records = self.get_by_document_id(document_id)
        return records[0] if records else None

    def get_by_application_id(self, application_id: str) -> List[Dict[str, Any]]:
        clean_id = application_id.strip() if application_id else ""
        if not clean_id:
            return []

        if self.db and not self._should_skip_db():
            try:
                results = (
                    self.db.query(DocumentVerificationRecord)
                    .filter(DocumentVerificationRecord.application_id == clean_id)
                    .order_by(DocumentVerificationRecord.verified_at.desc())
                    .all()
                )
                if results:
                    return [self._to_dict(r) for r in results]
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_by_application_id: %s", exc)

        matches = [r for r in _MEM_EVIDENCE.values() if r.get("application_id") == clean_id]
        matches.sort(key=lambda x: x.get("verified_at") or datetime.min, reverse=True)
        return matches

    def get_by_hash(self, document_hash: str) -> Optional[Dict[str, Any]]:
        clean_hash = document_hash.strip() if document_hash else ""
        if not clean_hash:
            return None

        if self.db and not self._should_skip_db():
            try:
                rec = (
                    self.db.query(DocumentVerificationRecord)
                    .filter(DocumentVerificationRecord.document_hash == clean_hash)
                    .order_by(DocumentVerificationRecord.verified_at.desc())
                    .first()
                )
                if rec:
                    return self._to_dict(rec)
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_by_hash: %s", exc)

        for r in _MEM_EVIDENCE.values():
            if r.get("document_hash") == clean_hash:
                return r
        return None
