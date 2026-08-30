export type ApplicationStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'VERIFIED'
  | 'ACTION_REQUIRED'
  | 'REJECTED'
  | 'COMPLETED'
  | 'FAILED'
  | 'QUEUED';

export type PriorityLevel = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export interface AddressDetail {
  house_no: string;
  street: string;
  village: string;
  taluka: string;
  district: string;
  pincode: string;
}

export interface ProofDocument {
  document_id: string;
  document_type: string;
  document_name: string;
  upload_date: string;
  verification_status: ApplicationStatus | string;
  file_size?: string;
  extracted_name?: string;
  extracted_address?: string;
}

export interface WorkflowTimelineEvent {
  step_name: string;
  actor: string;
  action: string;
  timestamp: string;
  notes?: string;
}

export interface ApplicationDataPayload {
  citizen_name: string;
  existing_address: AddressDetail;
  new_address: AddressDetail;
  proof_documents: ProofDocument[];
  remarks?: string;
}

export interface ApplicationSummary {
  id: string;
  application_id: string;
  correlation_id: string;
  citizen_reference_id: string;
  citizen_name: string;
  service_type: string;
  requested_operation: string;
  priority: PriorityLevel;
  status: ApplicationStatus;
  required_action: string;
  received_at: string;
  taluka: string;
  district: string;
}

export interface ApplicationDetail {
  id: string;
  application_id: string;
  correlation_id: string;
  citizen_reference_id: string;
  service_type: string;
  requested_operation: string;
  purpose: string;
  consent_reference: string;
  priority: PriorityLevel;
  status: ApplicationStatus;
  required_action: string;
  citizen_name: string;
  received_at: string;
  updated_at: string;
  processing_started_at?: string | null;
  completed_at?: string | null;
  assigned_officer_id?: string | null;
  data_payload: ApplicationDataPayload;
  workflow_history: WorkflowTimelineEvent[];
}

export interface RevenueApplication {
  id?: string;
  application_id: string;
  correlation_id?: string;
  citizen_reference_id?: string;
  citizen_name: string;
  service_code?: string;
  service_name?: string;
  service_type?: string;
  requested_operation?: string;
  purpose?: string;
  consent_reference?: string;
  priority: PriorityLevel;
  status: ApplicationStatus;
  required_action?: string;
  received_at: string;
  updated_at?: string;
  processing_started_at?: string | null;
  completed_at?: string | null;
  assigned_officer_id?: string | null;
  house_no?: string;
  street?: string;
  village?: string;
  taluka?: string;
  district?: string;
  pincode?: string;
  data_payload?: ApplicationDataPayload;
  proof_documents?: ProofDocument[];
  workflow_history: WorkflowTimelineEvent[];
}

export interface PaginationMetadata {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApplicationListResult {
  items: ApplicationSummary[];
  pagination: PaginationMetadata;
}

export interface DashboardSummaryData {
  total_incoming: number;
  pending: number;
  processing: number;
  completed: number;
  rejected: number;
  action_required: number;
  failed_or_queued: number;
  average_processing_time: string;
  today_applications: number;
  govmesh_connection: string;
  api_status: string;
  pending_events: number;
}

export interface ApplicationFilterParams {
  page?: number;
  page_size?: number;
  status?: string;
  priority?: string;
  service_type?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ============================================================================
// Phase 04: Verification, Workflow & Audit Types
// ============================================================================
export interface ConsentValidationResult {
  consent_reference: string;
  application_id: string;
  valid: boolean;
  status: 'VALID' | 'EXPIRED' | 'REVOKED' | 'INVALID' | 'MISSING' | string;
  purpose: string;
  data_scope: string;
  recipient: string;
  expires_at?: string;
  errors: string[];
  rules_evaluated: Record<string, string>;
}

export interface DataValidationResult {
  application_id: string;
  valid: boolean;
  checks: {
    required_fields: string;
    name_format: string;
    address_completeness: string;
    date_format: string;
    document_reference: string;
    duplicate_check: string;
    consent_validity: string;
  };
  errors: string[];
}

export interface ComponentMatchDetail {
  result: 'MATCH' | 'PARTIAL_MATCH' | 'MISMATCH' | 'NOT_EXTRACTED' | string;
  score: number;
  requested?: string;
  extracted?: string;
}

export interface DocumentExtractedFields {
  extracted_name: string;
  extracted_address: string;
  house_no?: string;
  street?: string;
  village?: string;
  taluka?: string;
  district?: string;
  pincode?: string;
  consumer_number?: string;
  issue_date?: string;
  document_type: string;
  document_reference: string;
  raw_text?: string;
}

export interface DocumentVerificationResult {
  document_id: string;
  document_name: string;
  document_type: string;
  valid: boolean;
  match_status: 'VALIDATED' | 'MISMATCH' | 'MISSING' | 'INVALID' | 'PARTIAL_MATCH' | 'LOW_CONFIDENCE' | string;
  name_match: 'MATCH' | 'PARTIAL_MATCH' | 'MISMATCH' | 'NOT_EXTRACTED' | string;
  address_match: 'MATCH' | 'PARTIAL_MATCH' | 'MISMATCH' | 'NOT_EXTRACTED' | string;
  extracted_fields: DocumentExtractedFields;
  field_confidences?: Record<string, number>;
  component_matches?: Record<string, ComponentMatchDetail>;
  assistive_score?: number;
  matched_components_count?: number;
  total_components_count?: number;
  explanation?: string;
  details?: string;
  provider?: string;
  is_simulated_ocr: boolean;
  verification_timestamp?: string;
  manual_override?: {
    officer_id: string;
    officer_name: string;
    decision: string;
    reason: string;
    timestamp: string;
  } | null;
}

export interface ProofDocumentMetadata {
  document_id: string;
  application_id?: string;
  document_name: string;
  document_type: string;
  mime_type: string;
  file_size: string;
  upload_date?: string;
  verification_status: string;
  extracted_name?: string;
  extracted_address?: string;
  verification_result?: DocumentVerificationResult;
}

export interface DocumentUploadResponse {
  document_id: string;
  application_id: string;
  document_name: string;
  document_type: string;
  file_size: string;
  mime_type: string;
  verification_status: string;
  message: string;
}

export interface DocumentOverridePayload {
  decision: 'VALIDATED' | 'MISMATCH' | 'INVALID';
  reason: string;
  notes?: string;
}

export interface OfficerDecisionPayload {
  reason?: string;
  notes?: string;
  reauth_password?: string;
}

export interface InformationRequestPayload {
  request_type: 'NEW_DOCUMENT' | 'CORRECT_ADDRESS' | 'MISSING_INFO' | 'CLARIFICATION' | string;
  message: string;
}

export interface WorkflowActionResponse {
  applicationId: string;
  status: ApplicationStatus;
  department: string;
  action: string;
  changedBy: string;
  timestamp: string;
  reason?: string;
  requiredAction?: string;
}

export interface AuditLogEntry {
  id: string;
  officer_id: string;
  officer_name: string;
  application_id: string;
  action: string;
  previous_status?: string;
  new_status: string;
  reason?: string;
  correlation_id: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface AuditLogListResult {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// Phase 05: Departmental Notifications & Operational Management Types
// ============================================================================
export type NotificationType =
  | 'NEW_APPLICATION'
  | 'CONSENT_RECEIVED'
  | 'CITIZEN_RESPONSE'
  | 'RETRY_RECEIVED'
  | 'ESCALATION'
  | 'WORKFLOW_COMPLETION'
  | 'FAILURE'
  | 'ACTION_REQUIRED';

export type NotificationSeverity = 'INFO' | 'WARNING' | 'CRITICAL' | 'SUCCESS';

export interface NotificationItem {
  id: string;
  type: NotificationType | string;
  application_id: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  severity: NotificationSeverity;
  target_role: string;
}

export interface NotificationListResult {
  items: NotificationItem[];
  total: number;
  unread_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export type FailureSimulationMode = 'NONE' | 'API_UNAVAILABLE' | 'TIMEOUT' | 'INTERNAL_ERROR';

export interface FailureModeResponse {
  failure_mode: FailureSimulationMode;
}

