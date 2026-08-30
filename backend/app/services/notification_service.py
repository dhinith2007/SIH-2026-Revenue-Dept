from typing import List, Dict, Any, Optional
from app.repositories.notification_repository import NotificationRepository
from app.core.errors import ResourceNotFoundError
from app.core.logging import logger

VALID_NOTIFICATION_TYPES = {
    "NEW_APPLICATION",
    "CONSENT_RECEIVED",
    "CITIZEN_RESPONSE",
    "RETRY_RECEIVED",
    "ESCALATION",
    "WORKFLOW_COMPLETION",
    "FAILURE",
    "ACTION_REQUIRED",
}


class NotificationService:
    def __init__(self, notif_repo: NotificationRepository):
        self.notif_repo = notif_repo

    def emit_notification(
        self,
        notif_type: str,
        application_id: str,
        title: str,
        message: str,
        severity: str = "INFO",
        target_role: str = "ALL",
    ) -> Dict[str, Any]:
        """Dispatches an internal departmental notification."""
        clean_type = notif_type.upper()
        if clean_type not in VALID_NOTIFICATION_TYPES:
            clean_type = "NEW_APPLICATION"

        notif = self.notif_repo.create_notification(
            type=clean_type,
            application_id=application_id,
            title=title,
            message=message,
            severity=severity,
            target_role=target_role,
        )
        logger.info("Departmental notification [%s] emitted for app '%s': %s", clean_type, application_id, title)
        return notif

    def list_notifications(
        self,
        role: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> Dict[str, Any]:
        items, total, unread_count = self.notif_repo.list_notifications(role=role, unread_only=unread_only, limit=limit)
        return {
            "items": items,
            "total": total,
            "unread_count": unread_count,
        }

    def mark_read(self, notification_id: str) -> Dict[str, Any]:
        success = self.notif_repo.mark_as_read(notification_id)
        if not success:
            raise ResourceNotFoundError(message=f"Notification '{notification_id}' not found.")
        return {"id": notification_id, "read": True}

    def mark_all_read(self, role: Optional[str] = None) -> int:
        return self.notif_repo.mark_all_read(role=role)

    def get_unread_count(self, role: Optional[str] = None) -> int:
        return self.notif_repo.get_unread_count(role=role)
