import re
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, field_validator

CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
PINCODE_RE = re.compile(r"^[1-9][0-9]{5}$")


class AddressDetail(BaseModel):
    house_no: str
    street: str
    village: str
    taluka: str
    district: str
    pincode: str

    @field_validator("house_no", "street", "village", "taluka", "district", mode="before")
    @classmethod
    def validate_text_fields(cls, v: Any, info) -> str:
        if v is None:
            return ""
        s = str(v).strip()
        if CONTROL_CHAR_RE.search(s):
            raise ValueError(f"Field '{info.field_name}' contains illegal control characters.")
        if len(s) > 150:
            raise ValueError(f"Field '{info.field_name}' exceeds maximum length of 150 characters.")
        return s

    @field_validator("pincode", mode="before")
    @classmethod
    def validate_pincode(cls, v: Any) -> str:
        if v is None:
            return ""
        s = str(v).strip()
        if not PINCODE_RE.match(s):
            raise ValueError(f"Invalid postal pincode '{s}'. Must be a 6-digit number not starting with 0.")
        return s


class ProofDocumentMetadata(BaseModel):
    document_id: str
    document_type: str
    document_name: str
    upload_date: str
    verification_status: str
    file_size: Optional[str] = "1.2 MB"


class TimelineEvent(BaseModel):
    step_name: str
    actor: str
    action: str
    timestamp: str
    notes: Optional[str] = None


class ApplicationDataPayload(BaseModel):
    citizen_name: str
    existing_address: AddressDetail
    new_address: AddressDetail
    proof_documents: List[ProofDocumentMetadata]
    remarks: Optional[str] = None


class ApplicationSummary(BaseModel):
    id: str
    application_id: str
    correlation_id: str
    citizen_reference_id: Optional[str] = "CIT-GEN"
    citizen_name: str
    service_type: Optional[str] = "ADDRESS_CHANGE"
    requested_operation: Optional[str] = "UPDATE_REVENUE_ADDRESS"
    priority: Optional[str] = "NORMAL"
    status: str
    required_action: Optional[str] = ""
    received_at: Optional[Union[datetime, str]] = None
    taluka: Optional[str] = "Haveli"
    district: Optional[str] = "Pune"


class ApplicationDetail(BaseModel):
    id: str
    application_id: str
    correlation_id: str
    citizen_reference_id: Optional[str] = "CIT-GEN"
    service_type: Optional[str] = "ADDRESS_CHANGE"
    requested_operation: Optional[str] = "UPDATE_REVENUE_ADDRESS"
    purpose: Optional[str] = "Change of Residence / Address Updation"
    consent_reference: Optional[str] = ""
    priority: Optional[str] = "NORMAL"
    status: str
    required_action: Optional[str] = ""
    citizen_name: str
    received_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None
    processing_started_at: Optional[Union[datetime, str]] = None
    completed_at: Optional[Union[datetime, str]] = None
    assigned_officer_id: Optional[str] = None
    data_payload: Optional[Dict[str, Any]] = {}
    workflow_history: Optional[List[Dict[str, Any]]] = []


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ApplicationListResponse(BaseModel):
    items: List[ApplicationSummary]
    pagination: PaginationMetadata


class DashboardSummary(BaseModel):
    total_incoming: int
    pending: int
    processing: int
    completed: int
    rejected: int
    action_required: int
    failed_or_queued: int
    average_processing_time: str
    today_applications: int
    govmesh_connection: str = "DEMO ONLINE"
    api_status: str = "ONLINE"
    pending_events: int = 2
