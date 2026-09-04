from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status, Body, Request
from app.schemas.common import BaseResponse
from app.schemas.application import (
    ApplicationListResponse,
    ApplicationSummary,
    PaginationMetadata,
)
from app.schemas.workflow import (
    ConsentValidationResult,
    DataValidationResult,
    DocumentVerificationResult,
    OfficerDecisionRequest,
    InformationRequestPayload,
    WorkflowActionResponse,
    AddressVerificationResponse,
    AuditLogListResponse,
    AuditLogEntry,
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.consent_repository import ConsentRepository
from app.services.consent_service import ConsentService
from app.services.data_validation_service import DataValidationService
from app.services.document_verification_service import DocumentVerificationService
from app.services.workflow_service import WorkflowService
from app.api.deps import (
    get_application_repository,
    get_audit_repository,
    get_consent_repository,
    get_workflow_service,
    get_current_user,
    require_permission,
)
from app.core.permissions import PermissionEnum
from app.core.errors import ResourceNotFoundError
from app.core.simulation import check_simulated_failure, get_current_failure_mode, set_runtime_failure_mode
from app.core.logging import logger

router = APIRouter()


# ============================================================================
# 1. Comprehensive Address Verification Probe (REST/JSON Contract)
# ============================================================================
@router.post(
    "/revenue/address/verify",
    response_model=BaseResponse[AddressVerificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute Comprehensive Address Verification Probe",
    description="Validates Consent, Data, and Supporting Proof Document for an application. Does not automatically approve.",
)
async def verify_address(
    request: Request,
    payload: Dict[str, Any] = Body(..., example={"application_id": "GM-2026-000124"}),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    consent_repo: ConsentRepository = Depends(get_consent_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    app_id = payload.get("application_id", "")
    await check_simulated_failure(request, correlation_id=app_id)
    app = app_repo.get_by_application_id(app_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{app_id}' not found.")

    consent_res = ConsentService.validate_consent(app, consent_repo=consent_repo)
    data_res = DataValidationService.validate_application_data(app, app_repo.get_all_applications())
    doc_res = DocumentVerificationService.verify_document(app)

    validation_map = {
        "consent": "VALID" if consent_res.valid else consent_res.status,
        "data": "VALID" if data_res.valid else "INVALID",
        "document": doc_res.match_status,
    }

    return BaseResponse(
        success=True,
        data=AddressVerificationResponse(
            applicationId=app_id,
            status=app.get("status", "PENDING"),
            department="REVENUE",
            validation=validation_map,
            message="Verification probe executed successfully. Officer decision required.",
        ),
        message="Address verification evaluation completed.",
    )


# ============================================================================
# 2. Interactive Prerequisite Validation Endpoints
# ============================================================================
@router.post(
    "/revenue/application/{application_id}/start-review",
    response_model=BaseResponse[WorkflowActionResponse],
    status_code=status.HTTP_200_OK,
    summary="Start Application Review (PENDING -> PROCESSING)",
)
async def start_review(
    request: Request,
    application_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.APPLICATION_VIEW_ASSIGNED)),
):
    await check_simulated_failure(request, correlation_id=application_id)
    updated = workflow_service.start_review(
        application_id=application_id,
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
    )
    return BaseResponse(
        success=True,
        data=WorkflowActionResponse(
            applicationId=application_id,
            status=updated.get("status", "PROCESSING"),
            action="START_REVIEW",
            changedBy=current_user["username"],
            timestamp=datetime.now(timezone.utc),
            reason="Desk scrutiny started",
        ),
        message=f"Review initiated for application {application_id}.",
    )


@router.post(
    "/revenue/application/{application_id}/validate-consent",
    response_model=BaseResponse[ConsentValidationResult],
    status_code=status.HTTP_200_OK,
    summary="Authoritatively Validate Citizen Consent (Rules 1-8)",
)
async def validate_consent_endpoint(
    request: Request,
    application_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    consent_repo: ConsentRepository = Depends(get_consent_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id=application_id)
    app = app_repo.get_by_application_id(application_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")
    result = ConsentService.validate_consent(app, consent_repo=consent_repo)
    return BaseResponse(
        success=True,
        data=result,
        message=f"Consent evaluation complete: Status={result.status}, Valid={result.valid}",
    )


@router.post(
    "/revenue/consent/validate",
    response_model=BaseResponse[ConsentValidationResult],
    status_code=status.HTTP_200_OK,
    summary="Authoritatively Validate Citizen Consent via Request Payload",
)
async def validate_consent_payload(
    request: Request,
    payload: Dict[str, Any] = Body(..., example={"application_id": "GM-2026-000124"}),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    consent_repo: ConsentRepository = Depends(get_consent_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    app_id = payload.get("application_id", "")
    await check_simulated_failure(request, correlation_id=app_id)
    app = app_repo.get_by_application_id(app_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{app_id}' not found.")
    result = ConsentService.validate_consent(app, consent_repo=consent_repo)
    return BaseResponse(
        success=True,
        data=result,
        message=f"Consent evaluation complete: Status={result.status}, Valid={result.valid}",
    )


@router.post(
    "/revenue/application/{application_id}/validate-data",
    response_model=BaseResponse[DataValidationResult],
    status_code=status.HTTP_200_OK,
    summary="Authoritatively Validate Address Completeness & Data",
)
async def validate_data_endpoint(
    request: Request,
    application_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id=application_id)
    app = app_repo.get_by_application_id(application_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")
    all_apps = app_repo.get_all_applications()
    result = DataValidationService.validate_application_data(app, all_apps)
    return BaseResponse(
        success=True,
        data=result,
        message=f"Data validation complete: Valid={result.valid}, Errors={len(result.errors)}",
    )


@router.post(
    "/revenue/address/validate",
    response_model=BaseResponse[DataValidationResult],
    status_code=status.HTTP_200_OK,
    summary="Authoritatively Validate Address Completeness via Request Payload",
)
async def validate_address_payload(
    request: Request,
    payload: Dict[str, Any] = Body(..., example={"application_id": "GM-2026-000124"}),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    app_id = payload.get("application_id", "")
    await check_simulated_failure(request, correlation_id=app_id)
    app = app_repo.get_by_application_id(app_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{app_id}' not found.")
    all_apps = app_repo.get_all_applications()
    result = DataValidationService.validate_application_data(app, all_apps)
    return BaseResponse(
        success=True,
        data=result,
        message=f"Data validation complete: Valid={result.valid}, Errors={len(result.errors)}",
    )


@router.post(
    "/revenue/application/{application_id}/verify-document",
    response_model=BaseResponse[DocumentVerificationResult],
    status_code=status.HTTP_200_OK,
    summary="Verify Supporting Proof Document (Simulated OCR)",
)
async def verify_document_endpoint(
    request: Request,
    application_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id=application_id)
    app = app_repo.get_by_application_id(application_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")
    result = DocumentVerificationService.verify_document(app)
    return BaseResponse(
        success=True,
        data=result,
        message=f"Document verification complete: MatchStatus={result.match_status}, Valid={result.valid}",
    )


# ============================================================================
# 3. Officer Decision Actions (APPROVE, REJECT, REQUEST INFO, REPROCESS, RETRY)
# ============================================================================
@router.post(
    "/revenue/application/{application_id}/approve",
    response_model=BaseResponse[WorkflowActionResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve Address Change (Officer Authority)",
)
async def approve_application_endpoint(
    request: Request,
    application_id: str,
    payload: Optional[OfficerDecisionRequest] = None,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.APPLICATION_APPROVE)),
):
    await check_simulated_failure(request, correlation_id=application_id)
    reason = payload.reason if payload else "Address proof matches requested new residence record."
    updated = workflow_service.approve_application(
        application_id=application_id,
        reason=reason,
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
    )
    return BaseResponse(
        success=True,
        data=WorkflowActionResponse(
            applicationId=application_id,
            status="VERIFIED",
            action="APPROVED",
            changedBy=current_user["username"],
            timestamp=datetime.now(timezone.utc),
            reason=reason,
        ),
        message=f"Application '{application_id}' successfully approved and marked VERIFIED.",
    )


@router.post(
    "/revenue/application/{application_id}/reject",
    response_model=BaseResponse[WorkflowActionResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject Address Change (Mandatory Statutory Reason)",
)
async def reject_application_endpoint(
    request: Request,
    application_id: str,
    payload: OfficerDecisionRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.APPLICATION_REJECT)),
):
    await check_simulated_failure(request, correlation_id=application_id)
    reason = payload.reason or ""
    updated = workflow_service.reject_application(
        application_id=application_id,
        reason=reason,
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
    )
    return BaseResponse(
        success=True,
        data=WorkflowActionResponse(
            applicationId=application_id,
            status="REJECTED",
            action="REJECTED",
            changedBy=current_user["username"],
            timestamp=datetime.now(timezone.utc),
            reason=reason,
        ),
        message=f"Application '{application_id}' rejected.",
    )


@router.post(
    "/revenue/application/{application_id}/request-info",
    response_model=BaseResponse[WorkflowActionResponse],
    status_code=status.HTTP_200_OK,
    summary="Request Additional Information / Proof (ACTION_REQUIRED)",
)
async def request_info_endpoint(
    request: Request,
    application_id: str,
    payload: InformationRequestPayload,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.REQUEST_INFORMATION)),
):
    await check_simulated_failure(request, correlation_id=application_id)
    updated = workflow_service.request_additional_information(
        application_id=application_id,
        request_type=payload.request_type,
        message=payload.message,
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
    )
    return BaseResponse(
        success=True,
        data=WorkflowActionResponse(
            applicationId=application_id,
            status="ACTION_REQUIRED",
            action="INFORMATION_REQUESTED",
            changedBy=current_user["username"],
            timestamp=datetime.now(timezone.utc),
            reason=f"[{payload.request_type}] {payload.message}",
            requiredAction=payload.request_type,
        ),
        message=f"Information requested for application '{application_id}'. Status set to ACTION_REQUIRED.",
    )


@router.post(
    "/revenue/application/{application_id}/reprocess",
    response_model=BaseResponse[WorkflowActionResponse],
    status_code=status.HTTP_200_OK,
    summary="Reprocess Application following Citizen Response (ACTION_REQUIRED -> PROCESSING)",
)
async def reprocess_application_endpoint(
    request: Request,
    application_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.APPLICATION_VIEW_ASSIGNED)),
):
    await check_simulated_failure(request, correlation_id=application_id)
    updated = workflow_service.reprocess_application(
        application_id=application_id,
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
    )
    return BaseResponse(
        success=True,
        data=WorkflowActionResponse(
            applicationId=application_id,
            status="PROCESSING",
            action="REPROCESSED",
            changedBy=current_user["username"],
            timestamp=datetime.now(timezone.utc),
            reason="Reprocessing initiated",
        ),
        message=f"Application '{application_id}' reprocessed back to PROCESSING for re-verification.",
    )


@router.post(
    "/revenue/application/{application_id}/retry",
    response_model=BaseResponse[WorkflowActionResponse],
    status_code=status.HTTP_200_OK,
    summary="Controlled Operational Retry (Phase 05 Failure Recovery)",
)
async def retry_application_endpoint(
    request: Request,
    application_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.APPLICATION_VIEW_ASSIGNED)),
):
    await check_simulated_failure(request, correlation_id=application_id)
    updated = workflow_service.retry_application(
        application_id=application_id,
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
    )
    return BaseResponse(
        success=True,
        data=WorkflowActionResponse(
            applicationId=application_id,
            status=updated.get("status", "PROCESSING"),
            action="RETRY_RECEIVED",
            changedBy=current_user["username"],
            timestamp=datetime.now(timezone.utc),
            reason="Operational retry initiated",
        ),
        message=f"Controlled operational retry for '{application_id}' executed successfully.",
    )


# ============================================================================
# 4. SIH Demonstration Failure Simulation Controls
# ============================================================================
@router.post(
    "/revenue/simulation/failure-mode",
    response_model=BaseResponse[Dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="Set Failure Simulation Mode (SIH Demo)",
)
def set_failure_mode_endpoint(
    payload: Dict[str, str] = Body(..., example={"mode": "API_UNAVAILABLE"}),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    mode = payload.get("mode", "NONE")
    set_mode = set_runtime_failure_mode(mode)
    return BaseResponse(
        success=True,
        data={"failure_mode": set_mode},
        message=f"Simulation failure mode set to '{set_mode}'.",
    )


@router.get(
    "/revenue/simulation/failure-mode",
    response_model=BaseResponse[Dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="Get Current Simulation Failure Mode",
)
def get_failure_mode_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    return BaseResponse(
        success=True,
        data={"failure_mode": get_current_failure_mode()},
        message="Simulation failure mode retrieved.",
    )


# ============================================================================
# 6. Departmental Audit Logs
# ============================================================================
@router.get(
    "/revenue/audit-logs",
    response_model=BaseResponse[AuditLogListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Departmental Audit Logs",
)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    application_id: Optional[str] = Query(None),
    officer_id: Optional[str] = Query(None),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    items, total, total_pages = audit_repo.list_audit_logs(
        page=page,
        page_size=page_size,
        application_id=application_id,
        officer_id=officer_id,
    )
    entries = [AuditLogEntry(**it) for it in items]
    return BaseResponse(
        success=True,
        data=AuditLogListResponse(
            items=entries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        message=f"Retrieved {len(entries)} audit log records (Total: {total}).",
    )

