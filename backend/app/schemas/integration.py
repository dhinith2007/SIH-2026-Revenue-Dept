from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from app.schemas.application import AddressDetail, CONTROL_CHAR_RE


class CitizenContactDto(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None


class CitizenInfoDto(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Full legal name of the citizen")
    identifier: str = Field(..., min_length=2, max_length=100, description="Citizen reference identifier or masked ID")
    contact: Optional[CitizenContactDto] = None

    @field_validator("name", "identifier", mode="before")
    @classmethod
    def clean_strings(cls, v: Any, info) -> str:
        if v is None:
            return ""
        s = str(v).strip()
        if CONTROL_CHAR_RE.search(s):
            raise ValueError(f"Field '{info.field_name}' contains illegal control characters.")
        return s


class ProofDocumentIngestDto(BaseModel):
    document_id: str = Field(..., description="Unique document ID from external system")
    document_type: str = Field(default="ELECTRICITY_BILL", description="Document type (e.g. ELECTRICITY_BILL, WATER_BILL, TAX_RECEIPT)")
    document_name: str = Field(default="Document.pdf", description="Filename of supporting document")
    upload_date: Optional[str] = None
    verification_status: Optional[str] = "PENDING"
    file_size: Optional[str] = "1.2 MB"
    document_hash: Optional[str] = None
    extracted_name: Optional[str] = None
    extracted_address: Optional[str] = None


class ApplicationDataIngestDto(BaseModel):
    existing_address: Optional[AddressDetail] = None
    new_address: AddressDetail = Field(..., description="Mandatory 6-part target residential address in Maharashtra")
    proof_documents: Optional[List[ProofDocumentIngestDto]] = Field(default_factory=list)
    remarks: Optional[str] = None


class ConsentIngestDto(BaseModel):
    consent_reference: Optional[str] = None
    consent_id: Optional[str] = None  # Alias support for GovMesh format
    purpose: Optional[str] = "Update Revenue address record & 7/12 land registry linkage"
    data_scope: Optional[str] = "address.change"
    recipient: Optional[str] = "Revenue & Forest Department"
    granted: bool = True
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def get_effective_reference(self, default_app_id: str) -> str:
        ref = self.consent_reference or self.consent_id
        if ref and ref.strip():
            return ref.strip()
        return f"CONSENT-{default_app_id.replace('GM-', '')}"


class IntegrityMetadataDto(BaseModel):
    canonical_hash: Optional[str] = None
    document_hash: Optional[str] = None


class ApplicationIngestRequest(BaseModel):
    application_id: str = Field(..., min_length=3, max_length=50, description="External unique application ID (e.g. GM-2026-000001)")
    correlation_id: str = Field(..., min_length=3, max_length=100, description="End-to-end tracing correlation ID")
    request_version: str = Field(default="1.0", description="Integration contract specification version")
    source_department: str = Field(default="GOVMESH", description="Source initiating system/department")
    service_type: str = Field(default="ADDRESS_CHANGE", description="Service category code")
    priority: Optional[str] = Field(default="NORMAL", description="Processing priority (LOW, NORMAL, HIGH, URGENT)")
    submitted_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    citizen: CitizenInfoDto = Field(..., description="Citizen identity and contact attributes")
    application_data: ApplicationDataIngestDto = Field(..., description="Residential address mutation details")
    consent: Optional[ConsentIngestDto] = None
    integrity: Optional[IntegrityMetadataDto] = None

    @field_validator("application_id", "correlation_id", mode="before")
    @classmethod
    def clean_ids(cls, v: Any, info) -> str:
        if not v or not str(v).strip():
            raise ValueError(f"Field '{info.field_name}' is mandatory and cannot be empty.")
        s = str(v).strip()
        if CONTROL_CHAR_RE.search(s):
            raise ValueError(f"Field '{info.field_name}' contains illegal control characters.")
        return s


class ApplicationIngestResponse(BaseModel):
    success: bool = True
    status: str = Field(..., description="Status of ingestion: RECEIVED | ALREADY_RECEIVED")
    application_id: str
    correlation_id: str
    message: str
    received_at: datetime
