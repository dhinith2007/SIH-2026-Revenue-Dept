from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConsentValidationResult(BaseModel):
    consent_reference: str
    application_id: str
    valid: bool
    status: str  # VALID, EXPIRED, REVOKED, INVALID, MISSING
    purpose: str
    data_scope: str
    recipient: str
    expires_at: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)
    rules_evaluated: Dict[str, str] = Field(default_factory=dict)


class DataValidationResult(BaseModel):
    application_id: str
    valid: bool
    checks: Dict[str, str] = Field(
        default_factory=lambda: {
            "required_fields": "PENDING",
            "name_format": "PENDING",
            "address_completeness": "PENDING",
            "date_format": "PENDING",
            "document_reference": "PENDING",
            "duplicate_check": "PENDING",
            "consent_validity": "PENDING",
        }
    )
    errors: List[str] = Field(default_factory=list)


class DocumentExtractedFields(BaseModel):
    extracted_name: str
    extracted_address: str
    citizen_name: Optional[str] = None
    house_no: Optional[str] = None
    street: Optional[str] = None
    village: Optional[str] = None
    taluka: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    consumer_number: Optional[str] = None
    document_number: Optional[str] = None
    issue_date: Optional[str] = None
    document_type: str = "ELECTRICITY_BILL"
    document_reference: str = ""
    raw_text: Optional[str] = None


class DocumentVerificationResult(BaseModel):
    document_id: str
    document_name: str
    document_type: str
    valid: bool
    match_status: str  # VALIDATED, MISMATCH, MISSING, INVALID, PARTIAL_MATCH, LOW_CONFIDENCE
    name_match: str    # MATCH, PARTIAL_MATCH, MISMATCH, NOT_EXTRACTED
    address_match: str # MATCH, PARTIAL_MATCH, MISMATCH, NOT_EXTRACTED
    extracted_fields: DocumentExtractedFields
    field_confidences: Dict[str, float] = Field(default_factory=dict)
    component_matches: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    assistive_score: float = 1.0
    matched_components_count: int = 6
    total_components_count: int = 7
    explanation: Optional[str] = None
    details: Optional[str] = None
    provider: str = "SIMULATED"
    is_simulated_ocr: bool = True
    document_hash: Optional[str] = None
    processing_duration_ms: Optional[float] = None
    verification_timestamp: Optional[datetime] = None
    manual_override: Optional[Dict[str, Any]] = None
    # Phase 10 Step 04 Confidence Engine fields
    ocr_confidence: float = 0.95
    match_confidence: float = 1.0
    overall_confidence: float = 1.0
    recommendation: str = "HIGH_CONFIDENCE_MATCH"
    evidence_quality: str = "COMPLETE"
    risk_flags: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    officer_guidance: Optional[str] = None
    score_breakdown: Dict[str, float] = Field(default_factory=dict)



class ProofDocumentMetadata(BaseModel):
    document_id: str
    application_id: Optional[str] = None
    document_name: str
    document_type: str
    mime_type: str = "application/pdf"
    file_size: str = "1.2 MB"
    document_hash: Optional[str] = None
    upload_date: Optional[str] = None
    verification_status: str = "PENDING"
    extracted_name: Optional[str] = None
    extracted_address: Optional[str] = None
    verification_result: Optional[DocumentVerificationResult] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    application_id: str
    document_name: str
    document_type: str
    file_size: str
    mime_type: str
    document_hash: Optional[str] = None
    verification_status: str
    message: str


class DocumentOverrideRequest(BaseModel):
    decision: str = Field(..., description="VALIDATED | MISMATCH | INVALID")
    reason: str = Field(..., min_length=5, max_length=1000, description="Mandatory officer explanation for manual override")
    notes: Optional[str] = None


class OfficerDecisionRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000, description="Mandatory for rejection or notes on approval")
    notes: Optional[str] = Field(None, max_length=1000, description="Departmental scrutiny notes")
    reauth_password: Optional[str] = Field(None, description="Optional password for re-authentication challenge")


class InformationRequestPayload(BaseModel):
    request_type: str = Field(..., description="NEW_DOCUMENT | CORRECT_ADDRESS | MISSING_INFO | CLARIFICATION")
    message: str = Field(..., min_length=5, max_length=1000, description="Detailed instructions for the citizen")


class WorkflowActionResponse(BaseModel):
    applicationId: str
    status: str
    department: str = "REVENUE"
    action: str
    changedBy: str
    timestamp: datetime
    reason: Optional[str] = None
    requiredAction: Optional[str] = None


class AddressVerificationResponse(BaseModel):
    applicationId: str
    status: str
    department: str = "REVENUE"
    validation: Dict[str, str] = Field(default_factory=dict)
    message: Optional[str] = None
    acknowledgementId: Optional[str] = None
    correlationId: Optional[str] = None
    requestVersion: Optional[int] = 1
    requestHash: Optional[str] = None
    documentHash: Optional[str] = None
    hashStatus: Optional[str] = "VERIFIED"
    receivedAt: Optional[str] = None
    validatedAt: Optional[str] = None
    acceptedAt: Optional[str] = None
    completedAt: Optional[str] = None
    sentAt: Optional[str] = None
    createdAt: Optional[str] = None



class AuditLogEntry(BaseModel):
    id: str
    officer_id: str
    officer_name: str
    application_id: str
    action: str
    previous_status: Optional[str] = None
    new_status: str
    reason: Optional[str] = None
    correlation_id: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class AuditLogListResponse(BaseModel):
    items: List[AuditLogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int
