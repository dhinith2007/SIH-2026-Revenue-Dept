from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
import uuid
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.audit import AuditLog, ApplicationStatusHistory
from app.core.logging import logger

_MEM_AUDIT_LOGS: List[Dict[str, Any]] = []
_MEM_HISTORY: List[Dict[str, Any]] = []
_LAST_DB_CHECK_FAILED: float = 0.0
_DB_RETRY_INTERVAL_SECONDS: float = 30.0


class AuditRepository:
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

    def create_audit_entry(
        self,
        officer_id: str,
        officer_name: str,
        application_id: str,
        action: str,
        previous_status: Optional[str],
        new_status: str,
        reason: Optional[str],
        correlation_id: str,
        details: Optional[Dict[str, Any]] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """Appends an immutable audit log entry."""
        entry_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.now(timezone.utc)
        record = {
            "id": entry_id,
            "officer_id": officer_id,
            "officer_name": officer_name,
            "application_id": application_id,
            "action": action,
            "previous_status": previous_status,
            "new_status": new_status,
            "reason": reason,
            "correlation_id": correlation_id,
            "timestamp": ts,
            "details": details or {},
        }

        # Persist to memory store
        _MEM_AUDIT_LOGS.insert(0, record)

        # Persist to PostgreSQL if connected
        if self.db and not self._should_skip_db():
            try:
                db_item = AuditLog(
                    id=entry_id,
                    officer_id=officer_id,
                    officer_name=officer_name,
                    application_id=application_id,
                    action=action,
                    previous_status=previous_status,
                    new_status=new_status,
                    reason=reason,
                    correlation_id=correlation_id,
                    timestamp=ts,
                    details=details or {},
                )
                self.db.add(db_item)
                if auto_commit:
                    self.db.commit()
                else:
                    self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                    self._mark_db_failed()
                    logger.warning("DB insert failed in create_audit_entry: %s", exc)
                else:
                    raise

        return record

    def record_audit_event(
        self,
        officer_id: str,
        officer_name: str,
        application_id: str,
        action: str,
        previous_status: Optional[str],
        new_status: str,
        reason: Optional[str],
        correlation_id: str,
        details: Optional[Dict[str, Any]] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """Convenience alias for create_audit_entry."""
        return self.create_audit_entry(
            officer_id=officer_id,
            officer_name=officer_name,
            application_id=application_id,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            correlation_id=correlation_id,
            details=details,
            auto_commit=auto_commit,
        )

    def record_status_history(
        self,
        application_id: str,
        previous_status: Optional[str],
        new_status: str,
        action: str,
        changed_by: str,
        reason: Optional[str],
        correlation_id: str,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """Appends a status transition to the application workflow timeline."""
        hist_id = f"HIST-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.now(timezone.utc)
        record = {
            "id": hist_id,
            "application_id": application_id,
            "previous_status": previous_status,
            "new_status": new_status,
            "action": action,
            "changed_by": changed_by,
            "reason": reason,
            "timestamp": ts,
            "correlation_id": correlation_id,
        }

        _MEM_HISTORY.append(record)

        if self.db and not self._should_skip_db():
            try:
                db_item = ApplicationStatusHistory(
                    id=hist_id,
                    application_id=application_id,
                    previous_status=previous_status,
                    new_status=new_status,
                    action=action,
                    changed_by=changed_by,
                    reason=reason,
                    timestamp=ts,
                    correlation_id=correlation_id,
                )
                self.db.add(db_item)
                if auto_commit:
                    self.db.commit()
                else:
                    self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                    self._mark_db_failed()
                    logger.warning("DB insert failed in record_status_history: %s", exc)
                else:
                    raise

        return record

    def list_audit_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        application_id: Optional[str] = None,
        officer_id: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Lists paginated audit log entries."""
        if self.db and not self._should_skip_db():
            try:
                query = self.db.query(AuditLog)
                if application_id:
                    query = query.filter(AuditLog.application_id == application_id)
                if officer_id:
                    query = query.filter(AuditLog.officer_id == officer_id)
                total = query.count()
                total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                offset = (page - 1) * page_size
                items = (
                    query.order_by(AuditLog.timestamp.desc())
                    .offset(offset)
                    .limit(page_size)
                    .all()
                )
                res = [
                    {
                        "id": it.id,
                        "officer_id": it.officer_id,
                        "officer_name": it.officer_name,
                        "application_id": it.application_id,
                        "action": it.action,
                        "previous_status": it.previous_status,
                        "new_status": it.new_status,
                        "reason": it.reason,
                        "correlation_id": it.correlation_id,
                        "timestamp": it.timestamp,
                        "details": it.details,
                    }
                    for it in items
                ]
                return res, total, total_pages
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in list_audit_logs: %s", exc)

        # In-memory filtering
        filtered = _MEM_AUDIT_LOGS
        if application_id:
            filtered = [x for x in filtered if x["application_id"] == application_id]
        if officer_id:
            filtered = [x for x in filtered if x["officer_id"] == officer_id]

        total = len(filtered)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        offset = (page - 1) * page_size
        items = filtered[offset : offset + page_size]
        return items, total, total_pages
