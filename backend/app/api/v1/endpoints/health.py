from fastapi import APIRouter, status
from app.schemas.health import ServiceHealthResponse, DatabaseHealthResponse, SystemInfoResponse
from app.schemas.common import BaseResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/health",
    response_model=ServiceHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get revenue department service health",
)
@router.get(
    "/revenue/health",
    response_model=ServiceHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get revenue department service health (alias)",
)
def get_service_health():
    """Returns basic service health status."""
    return HealthService.get_service_health()


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get PostgreSQL database connectivity health",
)
def get_database_health():
    """Validates connectivity to PostgreSQL database and reports latency."""
    return HealthService.get_database_health()


@router.get(
    "/revenue/system-info",
    response_model=BaseResponse[SystemInfoResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Revenue Department metadata for GovMesh interoperability",
)
def get_system_info():
    """Returns departmental metadata, simulated flag, and phase info."""
    info = HealthService.get_system_info()
    return BaseResponse(
        success=True,
        data=info,
        message="Revenue Department system information retrieved successfully.",
    )
