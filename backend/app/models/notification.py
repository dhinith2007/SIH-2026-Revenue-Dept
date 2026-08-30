from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean
from app.db.base import Base


class Notification(Base):
    """
    Departmental Internal Notification Model (Phase 05).
    Tracks internal alerts, citizen response notices, escalations, and workflow milestones.
    """
    __tablename__ = "revenue_notifications"

    id = Column(String(50), primary_key=True, index=True)
    type = Column(String(50), index=True, nullable=False)  # NEW_APPLICATION, ACTION_REQUIRED, CITIZEN_RESPONSE, etc.
    application_id = Column(String(50), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    read = Column(Boolean, default=False, index=True, nullable=False)
    severity = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, CRITICAL, SUCCESS
    target_role = Column(String(50), default="ALL", index=True, nullable=False)  # ALL, REVENUE_OFFICER, SENIOR_REVENUE_OFFICER, etc.
