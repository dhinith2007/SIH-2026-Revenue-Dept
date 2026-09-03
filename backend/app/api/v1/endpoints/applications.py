from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, status, Request
from app.schemas.application import (
    ApplicationListResponse,
    ApplicationDetail,
    DashboardSummary,
    PaginationMetadata,
    ApplicationSummary,
)
from app.schemas.common import BaseResponse
from app.repositories.application_repository import ApplicationRepository
from app.api.deps import get_application_repository, get_current_user
from app.core.errors import ResourceNotFoundError
from app.core.authorization import verify_application_access
from app.core.simulation import check_simulated_failure
from app.core.logging import logger

router = APIRouter()


@router.get(
    "/revenue/dashboard/summary",
    response_model=BaseResponse[DashboardSummary],
    status_code=status.HTTP_200_OK,
    summary="Get Department Dashboard Operational Metrics",
    description="Returns live counts for pending, processing, verified, rejected, action-required cases, today's applications, and system connectivity indicators.",
)
def get_dashboard_summary(
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    logger.info("Dashboard summary requested by officer '%s' (%s)", current_user["username"], current_user["role"])
    summary_data = app_repo.get_dashboard_summary()
    return BaseResponse(
        success=True,
        data=DashboardSummary(**summary_data),
        message="Revenue Department dashboard metrics calculated successfully.",
    )


@router.get(
    "/revenue/applications",
    response_model=BaseResponse[ApplicationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List and Filter Incoming Applications",
    description="Retrieves paginated departmental applications queue with search, status/priority filtering, and sorting.",
)
async def list_applications(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. PENDING, PROCESSING, VERIFIED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (e.g. LOW, NORMAL, HIGH, URGENT)"),
    service_type: Optional[str] = Query(None, description="Filter by service code (e.g. ADDRESS_CHANGE)"),
    search: Optional[str] = Query(None, description="Search term for ID, Citizen Name, or Location"),
    sort_by: str = Query("received_at", description="Field to sort by: received_at, priority, status, application_id"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request)
    logger.info(
        "Application list requested by '%s' [page=%d, status=%s, priority=%s, search=%s]",
        current_user["username"],
        page,
        status,
        priority,
        search,
    )
    items, total, total_pages = app_repo.list_applications(
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        service_type=service_type,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    summaries = [ApplicationSummary(**item) for item in items]
    pagination = PaginationMetadata(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )

    return BaseResponse(
        success=True,
        data=ApplicationListResponse(items=summaries, pagination=pagination),
        message=f"Retrieved {len(summaries)} applications (Total: {total}).",
    )


# ============================================================================
# Dedicated Operational Queues (Completed, Rejected, Action Required)
# ============================================================================
@router.get(
    "/revenue/applications/completed",
    response_model=BaseResponse[ApplicationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Completed & Verified Applications",
)
def get_completed_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("completed_at"),
    sort_order: str = Query("desc"),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    items, total, total_pages = app_repo.list_applications(
        page=page,
        page_size=page_size,
        status="VERIFIED",
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    summaries = [ApplicationSummary(**item) for item in items]
    pagination = PaginationMetadata(page=page, page_size=page_size, total=total, total_pages=total_pages)
    return BaseResponse(
        success=True,
        data=ApplicationListResponse(items=summaries, pagination=pagination),
        message=f"Retrieved {len(summaries)} completed application records.",
    )


@router.get(
    "/revenue/applications/rejected",
    response_model=BaseResponse[ApplicationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Rejected Applications with Statutory Reasons",
)
def get_rejected_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("received_at"),
    sort_order: str = Query("desc"),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    items, total, total_pages = app_repo.list_applications(
        page=page,
        page_size=page_size,
        status="REJECTED",
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    summaries = [ApplicationSummary(**item) for item in items]
    pagination = PaginationMetadata(page=page, page_size=page_size, total=total, total_pages=total_pages)
    return BaseResponse(
        success=True,
        data=ApplicationListResponse(items=summaries, pagination=pagination),
        message=f"Retrieved {len(summaries)} rejected application records.",
    )


@router.get(
    "/revenue/applications/action-required",
    response_model=BaseResponse[ApplicationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Action-Required Cases Awaiting Citizen Clarification",
)
def get_action_required_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("received_at"),
    sort_order: str = Query("desc"),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    items, total, total_pages = app_repo.list_applications(
        page=page,
        page_size=page_size,
        status="ACTION_REQUIRED",
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    summaries = [ApplicationSummary(**item) for item in items]
    pagination = PaginationMetadata(page=page, page_size=page_size, total=total, total_pages=total_pages)
    return BaseResponse(
        success=True,
        data=ApplicationListResponse(items=summaries, pagination=pagination),
        message=f"Retrieved {len(summaries)} action-required application records.",
    )


@router.get(
    "/revenue/applications/{application_id}",
    response_model=BaseResponse[ApplicationDetail],
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Application Metadata & Scrutiny Record",
    description="Retrieves complete metadata, legal consent reference, correlation ID, internal address data model, proof documents, and workflow history for a single application.",
)
@router.get(
    "/revenue/application/{application_id}",
    response_model=BaseResponse[ApplicationDetail],
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Application Metadata & Scrutiny Record (Alias)",
)
async def get_application_detail(
    request: Request,
    application_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    corr = application_id.replace("GM-", "CORR-") if application_id.startswith("GM-") else application_id
    await check_simulated_failure(request, correlation_id=corr)
    logger.info("Application detail '%s' accessed by officer '%s'", application_id, current_user["username"])
    app = app_repo.get_by_application_id(application_id)
    if not app:
        raise ResourceNotFoundError(
            message=f"Application '{application_id}' was not found in departmental records.",
            correlation_id=corr,
        )

    verify_application_access(current_user, app, for_mutation=False)

    return BaseResponse(
        success=True,
        data=ApplicationDetail(**app),
        message=f"Application '{application_id}' scrutiny metadata retrieved successfully.",
    )


# ============================================================================
# Backward-Compatible Mock Endpoints for Phase 01 Shell Compatibility
# ============================================================================
@router.get(
    "/applications/mock",
    response_model=BaseResponse[List[Dict[str, Any]]],
    status_code=status.HTTP_200_OK,
    summary="Get synthetic development applications for UI shell (Phase 01)",
)
def list_mock_applications(
    app_repo: ApplicationRepository = Depends(get_application_repository),
):
    """Returns synthetic mock application list formatted for Phase 01 test compatibility."""
    from app.db.seed_applications import get_seeded_applications
    raw_apps = get_seeded_applications()
    flattened = []
    for a in raw_apps:
        data = a.get("data_payload", {})
        new_addr = data.get("new_address", {})
        item = {
            "application_id": a["application_id"],
            "citizen_name": a["citizen_name"],
            "service_code": "REV-ADDR-CHG",
            "service_name": "Change of Residence / Address Updation",
            "status": a["status"],
            "priority": a["priority"],
            "received_at": a["received_at"].isoformat() if hasattr(a["received_at"], "isoformat") else str(a["received_at"]),
            "house_no": new_addr.get("house_no", ""),
            "street": new_addr.get("street", ""),
            "village": new_addr.get("village", ""),
            "taluka": new_addr.get("taluka", ""),
            "district": new_addr.get("district", ""),
            "pincode": new_addr.get("pincode", ""),
            "proof_documents": data.get("proof_documents", []),
            "workflow_history": a.get("workflow_history", []),
        }
        flattened.append(item)

    return BaseResponse(
        success=True,
        data=flattened,
        message="Mock applications retrieved for development compatibility.",
    )


@router.get(
    "/applications/mock/{application_id}",
    response_model=BaseResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get single mock application details (Phase 01)",
)
def get_mock_application_detail(
    application_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
):
    """Returns single mock application detail or 404."""
    app = app_repo.get_by_application_id(application_id)
    if not app:
        raise ResourceNotFoundError(
            message=f"Application with ID '{application_id}' was not found in simulated records."
        )
    data = app.get("data_payload", {})
    new_addr = data.get("new_address", {})
    flattened = {
        "application_id": app["application_id"],
        "citizen_name": app["citizen_name"],
        "service_code": "REV-ADDR-CHG",
        "service_name": "Change of Residence / Address Updation",
        "status": app["status"],
        "priority": app["priority"],
        "received_at": app["received_at"].isoformat() if hasattr(app["received_at"], "isoformat") else str(app["received_at"]),
        "house_no": new_addr.get("house_no", ""),
        "street": new_addr.get("street", ""),
        "village": new_addr.get("village", ""),
        "taluka": new_addr.get("taluka", ""),
        "district": new_addr.get("district", ""),
        "pincode": new_addr.get("pincode", ""),
        "proof_documents": data.get("proof_documents", []),
        "workflow_history": app.get("workflow_history", []),
    }
    return BaseResponse(
        success=True,
        data=flattened,
        message=f"Application {application_id} retrieved successfully.",
    )
