from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
import uuid
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.notification import Notification
from app.core.logging import logger

_MEM_NOTIFICATIONS: List[Dict[str, Any]] = []
_LAST_DB_CHECK_FAILED: float = 0.0
_DB_RETRY_INTERVAL_SECONDS: float = 30.0


def _seed_initial_notifications():
    global _MEM_NOTIFICATIONS
    if not _MEM_NOTIFICATIONS:
        now = datetime.now(timezone.utc)
        _MEM_NOTIFICATIONS = [
            {
                "id": "NOTIF-REV-001",
                "type": "NEW_APPLICATION",
                "application_id": "GM-2026-000124",
                "title": "New Revenue Application Received",
                "message": "New ADDRESS_CHANGE application for Rajesh Shantaram Patil (Haveli, Pune) requires verification.",
                "timestamp": now - timedelta(minutes=45),
                "read": False,
                "severity": "INFO",
                "target_role": "REVENUE_OFFICER",
            },
            {
                "id": "NOTIF-REV-002",
                "type": "ACTION_REQUIRED",
                "application_id": "GM-2026-000128",
                "title": "Action Required: Missing Document",
                "message": "Application GM-2026-000128 is missing address proof document. Officer query needed.",
                "timestamp": now - timedelta(hours=1, minutes=30),
                "read": False,
                "severity": "WARNING",
                "target_role": "REVENUE_OFFICER",
            },
            {
                "id": "NOTIF-REV-003",
                "type": "CITIZEN_RESPONSE",
                "application_id": "GM-2026-000126",
                "title": "Citizen Response Ingested",
                "message": "Citizen Anand Mohan Shinde uploaded supplementary electricity bill proof for Nashik jurisdiction.",
                "timestamp": now - timedelta(hours=2),
                "read": False,
                "severity": "INFO",
                "target_role": "REVENUE_OFFICER",
            },
            {
                "id": "NOTIF-REV-004",
                "type": "WORKFLOW_COMPLETION",
                "application_id": "GM-2026-000131",
                "title": "Application Verified & Approved",
                "message": "Application GM-2026-000131 for Deepak Raghunath Jagtap has been approved and marked VERIFIED.",
                "timestamp": now - timedelta(hours=3),
                "read": True,
                "severity": "SUCCESS",
                "target_role": "ALL",
            },
            {
                "id": "NOTIF-REV-005",
                "type": "ESCALATION",
                "application_id": "GM-2026-000133",
                "title": "Urgent Application Priority Escalated",
                "message": "Urgent agricultural subsidy deadline for Meena Chandrakant Bhosale (Shirur) escalated for review.",
                "timestamp": now - timedelta(hours=4),
                "read": False,
                "severity": "CRITICAL",
                "target_role": "SENIOR_REVENUE_OFFICER",
            },
        ]


_seed_initial_notifications()


class NotificationRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        _seed_initial_notifications()

    def _should_skip_db(self) -> bool:
        global _LAST_DB_CHECK_FAILED
        if _LAST_DB_CHECK_FAILED > 0:
            if time.time() - _LAST_DB_CHECK_FAILED < _DB_RETRY_INTERVAL_SECONDS:
                return True
        return False

    def _mark_db_failed(self):
        global _LAST_DB_CHECK_FAILED
        _LAST_DB_CHECK_FAILED = time.time()

    def create_notification(
        self,
        type: str,
        application_id: str,
        title: str,
        message: str,
        severity: str = "INFO",
        target_role: str = "ALL",
    ) -> Dict[str, Any]:
        notif_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.now(timezone.utc)
        record = {
            "id": notif_id,
            "type": type,
            "application_id": application_id,
            "title": title,
            "message": message,
            "timestamp": ts,
            "read": False,
            "severity": severity,
            "target_role": target_role,
        }

        _MEM_NOTIFICATIONS.insert(0, record)

        if self.db and not self._should_skip_db():
            try:
                db_item = Notification(
                    id=notif_id,
                    type=type,
                    application_id=application_id,
                    title=title,
                    message=message,
                    timestamp=ts,
                    read=False,
                    severity=severity,
                    target_role=target_role,
                )
                self.db.add(db_item)
                self.db.commit()
            except SQLAlchemyError as exc:
                self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB insert failed in create_notification: %s", exc)

        return record

    def list_notifications(
        self,
        role: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        all_notifs = _MEM_NOTIFICATIONS

        if self.db and not self._should_skip_db():
            try:
                query = self.db.query(Notification)
                if role and role != "DEPARTMENT_ADMINISTRATOR":
                    query = query.filter((Notification.target_role == "ALL") | (Notification.target_role == role))
                if unread_only:
                    query = query.filter(Notification.read == False)
                
                total = query.count()
                unread = query.filter(Notification.read == False).count()
                db_items = query.order_by(Notification.timestamp.desc()).limit(limit).all()
                items = [
                    {
                        "id": n.id,
                        "type": n.type,
                        "application_id": n.application_id,
                        "title": n.title,
                        "message": n.message,
                        "timestamp": n.timestamp,
                        "read": n.read,
                        "severity": n.severity,
                        "target_role": n.target_role,
                    }
                    for n in db_items
                ]
                return items, total, unread
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in list_notifications, falling back to memory: %s", exc)

        filtered = all_notifs
        if role and role != "DEPARTMENT_ADMINISTRATOR":
            filtered = [n for n in filtered if n.get("target_role") in ("ALL", role)]
        if unread_only:
            filtered = [n for n in filtered if not n.get("read")]

        total = len(filtered)
        unread_count = sum(1 for n in all_notifs if not n.get("read") and (not role or role == "DEPARTMENT_ADMINISTRATOR" or n.get("target_role") in ("ALL", role)))
        items = filtered[:limit]
        return items, total, unread_count

    def mark_as_read(self, notification_id: str) -> bool:
        clean_id = notification_id.strip()
        found = False
        for n in _MEM_NOTIFICATIONS:
            if n["id"] == clean_id:
                n["read"] = True
                found = True
                break

        if self.db and not self._should_skip_db():
            try:
                db_item = self.db.query(Notification).filter(Notification.id == clean_id).first()
                if db_item:
                    db_item.read = True
                    self.db.commit()
                    found = True
            except SQLAlchemyError as exc:
                self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB update failed in mark_as_read: %s", exc)

        return found

    def mark_all_read(self, role: Optional[str] = None) -> int:
        count = 0
        for n in _MEM_NOTIFICATIONS:
            if not n["read"]:
                if not role or role == "DEPARTMENT_ADMINISTRATOR" or n.get("target_role") in ("ALL", role):
                    n["read"] = True
                    count += 1

        if self.db and not self._should_skip_db():
            try:
                query = self.db.query(Notification).filter(Notification.read == False)
                if role and role != "DEPARTMENT_ADMINISTRATOR":
                    query = query.filter((Notification.target_role == "ALL") | (Notification.target_role == role))
                updated = query.update({Notification.read: True}, synchronize_session=False)
                self.db.commit()
                count = max(count, updated)
            except SQLAlchemyError as exc:
                self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB update failed in mark_all_read: %s", exc)

        return count

    def get_unread_count(self, role: Optional[str] = None) -> int:
        _, _, unread = self.list_notifications(role=role, limit=1)
        return unread
