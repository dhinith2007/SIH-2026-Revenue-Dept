import secrets
from typing import Optional, Dict, Any
from fastapi import Request, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.errors import AuthenticationError
from app.core.logging import logger

security_scheme = HTTPBearer(auto_error=False)


async def verify_integration_source(
    request: Request,
    x_govmesh_api_key: Optional[str] = Header(None, alias="X-GovMesh-API-Key"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Validates that incoming cross-department integration requests originate
    from an authorized integration peer (e.g. GovMesh Integration Layer).
    
    Accepts:
    1. Header `X-GovMesh-API-Key` matching configured GOVMESH_API_KEY.
    2. Header `X-API-Key` matching configured GOVMESH_API_KEY.
    3. Bearer JWT Token with subject or role indicating authorized service access.
    
    Rejects unauthorized callers with 401 AuthenticationError.
    """
    provided_key = x_govmesh_api_key or x_api_key
    if provided_key:
        # Constant-time comparison to prevent timing attacks
        expected_key = settings.GOVMESH_API_KEY
        if secrets.compare_digest(provided_key.strip(), expected_key.strip()):
            logger.info("Cross-department request authenticated via API Key from IP %s", request.client.host if request.client else "unknown")
            return {
                "source": "GOVMESH_GATEWAY",
                "auth_type": "API_KEY",
                "authenticated": True,
            }
        else:
            logger.warning("Rejected cross-department request: invalid API key from IP %s", request.client.host if request.client else "unknown")
            raise AuthenticationError(
                message="Invalid integration API key provided.",
                code="AUTHENTICATION_REQUIRED",
            )

    # Alternative: check for Bearer JWT token
    if auth_header and auth_header.credentials:
        try:
            payload = decode_access_token(auth_header.credentials)
            role = payload.get("role", "")
            sub = payload.get("sub", "")
            if role in ("DEPARTMENT_ADMINISTRATOR", "SENIOR_REVENUE_OFFICER") or sub.startswith("GOVMESH") or sub.startswith("SVC-"):
                logger.info("Cross-department request authenticated via JWT token for subject '%s'", sub)
                return {
                    "source": sub,
                    "role": role,
                    "auth_type": "JWT",
                    "authenticated": True,
                }
        except Exception as exc:
            logger.warning("Cross-department JWT validation failed: %s", exc)

    logger.warning("Cross-department request rejected: missing integration authentication header from IP %s", request.client.host if request.client else "unknown")
    raise AuthenticationError(
        message="Authentication required. Please provide a valid 'X-GovMesh-API-Key' header or authorized service Bearer token.",
        code="AUTHENTICATION_REQUIRED",
    )
