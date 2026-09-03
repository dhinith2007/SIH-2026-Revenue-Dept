"""
GovMesh SIH26129 — Revenue & Forest Department
Security Response Headers & Transport Hardening Middleware (SEC-06)

Implements:
- X-Content-Type-Options: nosniff (mitigates MIME type sniffing)
- X-Frame-Options: DENY (clickjacking protection)
- Referrer-Policy: no-referrer (prevents referrer leakage)
- Content-Security-Policy: API default-src 'none'; frame-ancestors 'none'
  (Accommodates Swagger UI assets on /docs and /redoc)
- Permissions-Policy: Disables sensitive browser hardware/device APIs
- Strict-Transport-Security: max-age=31536000; includeSubDomains (production/HTTPS only)
- Cache-Control: no-store on sensitive auth and document routes
"""
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings
from app.core.logging import logger

_SENSITIVE_PATH_PREFIXES = (
    "/auth/",
    "/api/v1/auth/",
    "/api/auth/",
    "/revenue/auth/",
    "/api/v1/revenue/auth/",
    "/revenue/document/",
    "/api/v1/revenue/document/",
    "/api/revenue/document/",
)

_SWAGGER_PATH_PREFIXES = (
    "/docs",
    "/redoc",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/docs",
    "/api/redoc",
)

_CSP_API_POLICY = "default-src 'none'; frame-ancestors 'none'"
_CSP_DOCS_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "frame-ancestors 'none'"
)

_PERMISSIONS_POLICY = (
    "accelerometer=(), "
    "camera=(), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "payment=(), "
    "usb=()"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 1. MIME Sniffing Defense
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. Clickjacking Defense
        response.headers["X-Frame-Options"] = "DENY"

        # 3. Referrer Privacy Policy
        response.headers["Referrer-Policy"] = "no-referrer"

        # 4. Permissions-Policy (Feature Policy)
        response.headers["Permissions-Policy"] = _PERMISSIONS_POLICY

        # 5. Content-Security-Policy
        path = request.url.path.lower()
        if any(path.startswith(p) or path == p for p in _SWAGGER_PATH_PREFIXES):
            response.headers["Content-Security-Policy"] = _CSP_DOCS_POLICY
        else:
            response.headers["Content-Security-Policy"] = _CSP_API_POLICY

        # 6. Strict-Transport-Security (HSTS)
        # Enabled only in production or when explicitly configured, or when request is HTTPS
        is_prod = settings.APP_ENV.lower() in ("production", "prod")
        is_https = request.url.scheme == "https"
        if is_prod or settings.ENABLE_HSTS or is_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 7. Sensitive Endpoint Cache Prevention
        if any(path.startswith(p) for p in _SENSITIVE_PATH_PREFIXES):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response
