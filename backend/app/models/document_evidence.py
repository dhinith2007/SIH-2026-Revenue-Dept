from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON
from app.db.base import Base


class DocumentVerificationRecord(Base):
    """
    Relational persistence entity for OCR extraction evidence and verification history.
    Stores structured extracted metadata, SHA-256 integrity hash, provider info, and confidence metrics.
    Raw document binary bytes are excluded from this record for DPDP compliance.
    """
    __tablename__ = "document_verification_records"

    id = Column(String(50), primary_key=True, index=True)
    document_id = Column(String(50), index=True, nullable=False)
    application_id = Column(String(50), index=True, nullable=False)
    document_hash = Column(String(64), index=True, nullable=True)  # SHA-256 fingerprint
    provider = Column(String(50), nullable=False, default="SIMULATED")
    status = Column(String(50), nullable=False, default="SUCCESS")
    confidence = Column(Float, nullable=False, default=0.0)
    extracted_fields = Column(JSON, nullable=False, default=dict)
    field_confidences = Column(JSON, nullable=False, default=dict)
    error_message = Column(String(500), nullable=True)
    processing_duration_ms = Column(Float, nullable=True)
    correlation_id = Column(String(100), index=True, nullable=True)
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_by = Column(String(50), nullable=True)
