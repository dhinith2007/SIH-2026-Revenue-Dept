from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging import logger


class RevenueAppException(Exception):
    """Base exception for Revenue Department application."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
        correlation_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.correlation_id = correlation_id
        super().__init__(message)


class DatabaseConnectionError(RevenueAppException):
    def __init__(self, message: str = "Database connection failed", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="DATABASE_CONNECTION_ERROR",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
            correlation_id=correlation_id,
        )


class ServiceUnavailableError(RevenueAppException):
    def __init__(self, message: str = "The Revenue verification service is temporarily unavailable.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
            correlation_id=correlation_id,
        )


class GatewayTimeoutError(RevenueAppException):
    def __init__(self, message: str = "The departmental processing request timed out.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="GATEWAY_TIMEOUT",
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details=details,
            correlation_id=correlation_id,
        )


class InternalServerError(RevenueAppException):
    def __init__(self, message: str = "Internal server processing error occurred.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            correlation_id=correlation_id,
        )


class ResourceNotFoundError(RevenueAppException):
    def __init__(self, message: str = "Requested resource not found", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            correlation_id=correlation_id,
        )


class AuthenticationError(RevenueAppException):
    def __init__(self, message: str = "Invalid credentials.", code: str = "INVALID_CREDENTIALS", correlation_id: Optional[str] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            correlation_id=correlation_id,
        )


class InactiveAccountError(RevenueAppException):
    def __init__(self, message: str = "This department account is inactive.", correlation_id: Optional[str] = None):
        super().__init__(
            code="ACCOUNT_INACTIVE",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            correlation_id=correlation_id,
        )


class TokenExpiredError(RevenueAppException):
    def __init__(self, message: str = "Your session token has expired. Please sign in again.", correlation_id: Optional[str] = None):
        super().__init__(
            code="TOKEN_EXPIRED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            correlation_id=correlation_id,
        )


class TokenInvalidError(RevenueAppException):
    def __init__(self, message: str = "Authentication token is invalid or malformed.", correlation_id: Optional[str] = None):
        super().__init__(
            code="TOKEN_INVALID",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            correlation_id=correlation_id,
        )


class InsufficientPermissionError(RevenueAppException):
    def __init__(self, message: str = "You do not have permission to perform this action.", correlation_id: Optional[str] = None):
        super().__init__(
            code="INSUFFICIENT_PERMISSION",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            correlation_id=correlation_id,
        )


class UnauthorizedActionError(RevenueAppException):
    def __init__(self, message: str = "Unauthorized action attempted for this role.", correlation_id: Optional[str] = None):
        super().__init__(
            code="UNAUTHORIZED_ACTION",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            correlation_id=correlation_id,
        )


class ReauthenticationRequiredError(RevenueAppException):
    def __init__(self, message: str = "Re-authentication required for this sensitive departmental action.", correlation_id: Optional[str] = None):
        super().__init__(
            code="REAUTHENTICATION_REQUIRED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            correlation_id=correlation_id,
        )


# ============================================================================
# Phase 04 & 05: Workflow, Validation & Consent Specific Exceptions
# ============================================================================
class ConsentInvalidError(RevenueAppException):
    def __init__(self, message: str = "Consent validation failed.", code: str = "CONSENT_INVALID", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            correlation_id=correlation_id,
        )


class ConsentExpiredError(RevenueAppException):
    def __init__(self, message: str = "The consent associated with this application has expired.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="CONSENT_EXPIRED",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            correlation_id=correlation_id,
        )


class DataValidationError(RevenueAppException):
    def __init__(self, message: str = "Application data validation failed.", code: str = "DATA_INVALID", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            correlation_id=correlation_id,
        )


class DocumentMismatchError(RevenueAppException):
    def __init__(self, message: str = "Supporting proof document could not be validated or contains mismatched data.", code: str = "DOCUMENT_MISMATCH", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            correlation_id=correlation_id,
        )


class DuplicateApplicationError(RevenueAppException):
    def __init__(self, message: str = "A duplicate application for this citizen and service already exists.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="DUPLICATE_APPLICATION",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            correlation_id=correlation_id,
        )


class DuplicateRequestError(RevenueAppException):
    def __init__(self, message: str = "Duplicate request detected. Action has already been processed.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="DUPLICATE_REQUEST",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            correlation_id=correlation_id,
        )


class InvalidStatusTransitionError(RevenueAppException):
    def __init__(self, message: str = "Invalid application status transition attempted.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="INVALID_STATUS_TRANSITION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            correlation_id=correlation_id,
        )


class ApplicationFinalizedError(RevenueAppException):
    def __init__(self, message: str = "This application has already been finalized and is immutable.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="APPLICATION_ALREADY_FINALIZED",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            correlation_id=correlation_id,
        )


class DocumentTypeUnsupportedError(RevenueAppException):
    def __init__(self, message: str = "The uploaded file format is not supported. Please upload PDF, JPG, or PNG.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="DOCUMENT_TYPE_UNSUPPORTED",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            correlation_id=correlation_id,
        )


class DocumentTooLargeError(RevenueAppException):
    def __init__(self, message: str = "The uploaded file exceeds the maximum allowed size (10 MB).", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="DOCUMENT_TOO_LARGE",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            correlation_id=correlation_id,
        )


class DocumentEmptyError(RevenueAppException):
    def __init__(self, message: str = "The uploaded document file is empty (0 bytes).", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="DOCUMENT_EMPTY",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            correlation_id=correlation_id,
        )


class DocumentInvalidError(RevenueAppException):
    def __init__(self, message: str = "The uploaded file is corrupt or does not contain valid document data.", details: Optional[Any] = None, correlation_id: Optional[str] = None):
        super().__init__(
            code="DOCUMENT_INVALID",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            correlation_id=correlation_id,
        )


def _get_correlation_id(request: Request, exc: Optional[RevenueAppException] = None) -> Optional[str]:
    if exc and exc.correlation_id:
        return exc.correlation_id
    hdr = request.headers.get("X-Correlation-ID")
    if hdr:
        return hdr
    # Try to inspect query/path if app id is available
    path_parts = request.url.path.split("/")
    for part in path_parts:
        if part.startswith("GM-2026-") or part.startswith("CORR-"):
            return part.replace("GM-", "CORR-")
    return None


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RevenueAppException)
    async def revenue_exception_handler(request: Request, exc: RevenueAppException):
        corr_id = _get_correlation_id(request, exc)
        logger.warning("RevenueAppException on %s [corr: %s]: [%s] %s", request.url.path, corr_id, exc.code, exc.message)
        headers = {}
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            headers["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "correlationId": corr_id,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        corr_id = _get_correlation_id(request)
        logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request payload or query parameters",
                    "correlationId": corr_id,
                    "details": exc.errors(),
                },
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        corr_id = _get_correlation_id(request)
        logger.warning("HTTP %d on %s: %s", exc.status_code, request.url.path, exc.detail)
        code = "HTTP_ERROR"
        if exc.status_code == 404:
            code = "ENDPOINT_NOT_FOUND"
        elif exc.status_code == 403:
            code = "INSUFFICIENT_PERMISSION"
        elif exc.status_code == 401:
            code = "AUTHENTICATION_REQUIRED"
        elif exc.status_code == 503:
            code = "SERVICE_UNAVAILABLE"
        elif exc.status_code == 504:
            code = "GATEWAY_TIMEOUT"

        headers = {}
        if exc.status_code == 401:
            headers["WWW-Authenticate"] = "Bearer"

        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "success": False,
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                    "correlationId": corr_id,
                    "details": None,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        corr_id = _get_correlation_id(request)
        logger.error("Unhandled exception on %s: %s", request.url.path, str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred",
                    "correlationId": corr_id,
                    "details": None,
                },
            },
        )
