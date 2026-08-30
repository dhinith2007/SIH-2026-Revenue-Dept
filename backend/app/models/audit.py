from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base


class AuditLog(Base):
    """
    Departmental Audit Log Model.
    Immutable, append-only record of all officer actions, state changes, and decisions.
    """
    __tablename__ = "revenue_audit_logs"

    id = Column(String(50), primary_key=True, index=True)
    officer_id = Column(String(50), index=True, nullable=False)
    officer_name = Column(String(255), nullable=False)
    application_id = Column(String(50), index=True, nullable=False)
    action = Column(String(50), index=True, nullable=False)  # START_REVIEW, APPROVE, REJECT, REQUEST_INFO, etc.
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    reason = Column(String(1000), nullable=True)
    correlation_id = Column(String(100), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    details = Column(JSON, nullable=True)


class ApplicationStatusHistory(Base):
    """
    Application Status History Model.
    Tracks state transitions and actions in chronological order for the application timeline.
    """
    __tablename__ = "application_status_history"

    id = Column(String(50), primary_key=True, index=True)
    application_id = Column(String(50), index=True, nullable=False)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False)
    changed_by = Column(String(255), nullable=False)
    reason = Column(String(1000), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    correlation_id = Column(String(100), index=True, nullable=False)
