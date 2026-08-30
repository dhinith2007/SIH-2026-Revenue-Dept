from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel


class AddressDetail(BaseModel):
    house_no: str
    street: str
    village: str
    taluka: str
    district: str
    pincode: str


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
    citizen_reference_id: str
    citizen_name: str
    service_type: str
    requested_operation: str
    priority: str
    status: str
    required_action: str
    received_at: datetime
    taluka: str
    district: str


class ApplicationDetail(BaseModel):
    id: str
    application_id: str
    correlation_id: str
    citizen_reference_id: str
    service_type: str
    requested_operation: str
    purpose: str
    consent_reference: str
    priority: str
    status: str
    required_action: str
    citizen_name: str
    received_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_officer_id: Optional[str] = None
    data_payload: Dict[str, Any]
    workflow_history: List[Dict[str, Any]]


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
