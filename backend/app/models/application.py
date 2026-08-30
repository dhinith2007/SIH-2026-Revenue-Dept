from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base


class Application(Base):
    """
    Revenue Department Application Model.
    Represents an internal departmental record for citizen requests (e.g. Address Change).
    """
    __tablename__ = "revenue_applications"

    id = Column(String(50), primary_key=True, index=True)
    application_id = Column(String(50), unique=True, index=True, nullable=False)
    correlation_id = Column(String(100), index=True, nullable=False)
    citizen_reference_id = Column(String(50), index=True, nullable=False)
    service_type = Column(String(50), default="ADDRESS_CHANGE", index=True, nullable=False)
    requested_operation = Column(String(100), default="UPDATE_REVENUE_ADDRESS", nullable=False)
    purpose = Column(String(255), nullable=False)
    consent_reference = Column(String(100), nullable=False)
    priority = Column(String(20), default="NORMAL", index=True, nullable=False)
    status = Column(String(30), default="PENDING", index=True, nullable=False)
    required_action = Column(String(255), nullable=False)
    citizen_name = Column(String(255), nullable=False)

    received_at = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    processing_started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    assigned_officer_id = Column(String(50), nullable=True)

    # Department internal structured data representation
    data_payload = Column(JSON, nullable=False)
    workflow_history = Column(JSON, nullable=False)
