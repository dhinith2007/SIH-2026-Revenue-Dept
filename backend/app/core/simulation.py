import asyncio
from typing import Optional
from fastapi import Request
from app.core.config import settings
from app.core.errors import ServiceUnavailableError, GatewayTimeoutError, InternalServerError
from app.core.logging import logger

_RUNTIME_FAILURE_MODE: Optional[str] = None


def get_current_failure_mode() -> str:
    global _RUNTIME_FAILURE_MODE
    if _RUNTIME_FAILURE_MODE is not None:
        return _RUNTIME_FAILURE_MODE
    return settings.FAILURE_MODE.upper()


def set_runtime_failure_mode(mode: str) -> str:
    global _RUNTIME_FAILURE_MODE
    valid_modes = {"NONE", "API_UNAVAILABLE", "TIMEOUT", "INTERNAL_ERROR"}
    clean_mode = mode.strip().upper()
    if clean_mode not in valid_modes:
        clean_mode = "NONE"
    _RUNTIME_FAILURE_MODE = clean_mode
    logger.info("Runtime failure simulation mode set to: %s", _RUNTIME_FAILURE_MODE)
    return _RUNTIME_FAILURE_MODE


async def check_simulated_failure(request: Request, correlation_id: Optional[str] = None):
    """
    Checks if a simulated failure should be triggered on this request.
    Exempts health probes, auth endpoints, and simulation management routes.
    """
    path = request.url.path
    if (
        path.startswith("/health")
        or "/auth" in path
        or "/simulation" in path
        or path.endswith("/docs")
        or path.endswith("/openapi.json")
    ):
        return

    # Check header override first
    header_mode = request.headers.get("X-Simulate-Failure", "").strip().upper()
    mode = header_mode if header_mode in ("API_UNAVAILABLE", "TIMEOUT", "INTERNAL_ERROR") else get_current_failure_mode()

    if mode == "NONE":
        return

    corr_id = correlation_id or request.headers.get("X-Correlation-ID") or "CORR-SIMULATED"

    if mode == "API_UNAVAILABLE":
        logger.warning("Triggering simulated failure [API_UNAVAILABLE] on %s", path)
        raise ServiceUnavailableError(
            message="Revenue Department verification service is temporarily unavailable.",
            details={"simulation": True, "mode": "API_UNAVAILABLE"},
            correlation_id=corr_id,
        )
    elif mode == "TIMEOUT":
        logger.warning("Triggering simulated failure [TIMEOUT] on %s", path)
        if settings.SIMULATION_LATENCY_MS > 0:
            await asyncio.sleep(settings.SIMULATION_LATENCY_MS / 1000.0)
        raise GatewayTimeoutError(
            message="Revenue Department verification request timed out while contacting departmental data store.",
            details={"simulation": True, "mode": "TIMEOUT"},
            correlation_id=corr_id,
        )
    elif mode == "INTERNAL_ERROR":
        logger.warning("Triggering simulated failure [INTERNAL_ERROR] on %s", path)
        raise InternalServerError(
            message="An unexpected departmental processing exception occurred.",
            details={"simulation": True, "mode": "INTERNAL_ERROR"},
            correlation_id=corr_id,
        )
