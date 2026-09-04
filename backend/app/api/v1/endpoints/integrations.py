from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from app.schemas.integration import ApplicationIngestRequest, ApplicationIngestResponse
from app.schemas.common import BaseResponse
from app.services.integration_service import IntegrationService
from app.core.integration_auth import verify_integration_source
from app.api.deps import (
    get_application_repository,
    get_consent_repository,
    get_audit_repository,
    get_notification_repository,
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.consent_repository import ConsentRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.notification_repository import NotificationRepository
from app.core.simulation import check_simulated_failure
from app.core.logging import logger

router = APIRouter()


def get_integration_service(
    app_repo: ApplicationRepository = Depends(get_application_repository),
    consent_repo: ConsentRepository = Depends(get_consent_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    notif_repo: NotificationRepository = Depends(get_notification_repository),
) -> IntegrationService:
    return IntegrationService(app_repo, consent_repo, audit_repo, notif_repo)


@router.post(
    "/integrations/applications",
    response_model=ApplicationIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit New Cross-Department Citizen Application",
    description="Dedicated integration contract for GovMesh and external departments to submit new address change applications into the Revenue Department.",
    responses={
        201: {"description": "Application successfully ingested and queued for scrutiny."},
        200: {"description": "Idempotent response: application was already received."},
        400: {"description": "Unsupported request contract version."},
        401: {"description": "Missing or invalid integration API key / service credentials."},
        409: {"description": "Conflicting application ID with different identity."},
        422: {"description": "Validation error: missing mandatory address or citizen fields."},
    },
)
@router.post(
    "/revenue/applications/ingest",
    response_model=ApplicationIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit New Cross-Department Citizen Application (Departmental Alias)",
    description="Alias endpoint for GovMesh RevenueAdapter compatibility.",
    include_in_schema=True,
)
async def ingest_application(
    request: Request,
    payload: ApplicationIngestRequest,
    caller_info: Dict[str, Any] = Depends(verify_integration_source),
    integration_service: IntegrationService = Depends(get_integration_service),
):
    """
    Authoritatively receives, verifies source credentials, checks idempotency,
    and atomically persists new citizen applications from GovMesh.
    """
    await check_simulated_failure(request, correlation_id=payload.correlation_id)
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "Cross-department intake: AppID='%s', CorrID='%s', Source='%s', AuthType='%s'",
        payload.application_id,
        payload.correlation_id,
        caller_info.get("source"),
        caller_info.get("auth_type"),
    )

    response_dto, status_code = integration_service.ingest_application(payload, client_ip=client_ip)
    
    # Return 201 for new, 200 for idempotent duplicate
    return JSONResponse(
        status_code=status_code,
        content=response_dto.model_dump(mode="json"),
    )
