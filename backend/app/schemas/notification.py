from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationItem(BaseModel):
    id: str
    type: str = Field(..., description="NEW_APPLICATION | CONSENT_RECEIVED | CITIZEN_RESPONSE | RETRY_RECEIVED | ESCALATION | WORKFLOW_COMPLETION | FAILURE | ACTION_REQUIRED")
    application_id: str
    title: str
    message: str
    timestamp: datetime
    read: bool = False
    severity: str = "INFO"  # INFO | WARNING | CRITICAL | SUCCESS
    target_role: str = "ALL"


class NotificationListResponse(BaseModel):
    items: List[NotificationItem]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    id: str
    read: bool = True
