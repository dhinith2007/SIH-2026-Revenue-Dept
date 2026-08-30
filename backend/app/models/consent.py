from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base


class ConsentRecord(Base):
    """
    Revenue Department Legal Consent Record Model.
    Tracks citizen consent references for DPDP compliance.
    """
    __tablename__ = "revenue_consents"

    id = Column(String(50), primary_key=True, index=True)
    consent_reference = Column(String(100), unique=True, index=True, nullable=False)
    application_id = Column(String(50), index=True, nullable=False)
    status = Column(String(30), default="VALID", index=True, nullable=False)  # VALID, EXPIRED, REVOKED, INVALID, MISSING
    purpose = Column(String(255), nullable=False)
    data_scope = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validation_result = Column(JSON, nullable=True)
