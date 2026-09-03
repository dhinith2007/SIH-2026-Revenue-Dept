from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.cors import setup_cors
from app.core.errors import register_error_handlers
from app.db.session import init_db
from app.api.v1.router import api_router
from app.services.health_service import HealthService
from app.schemas.health import ServiceHealthResponse, DatabaseHealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    setup_logging()
    logger.info("Starting up %s (Version: %s)", settings.PROJECT_NAME, settings.VERSION)
    logger.info("Initializing database connectivity check...")
    init_db()
    yield
    # Shutdown tasks
    logger.info("Shutting down %s", settings.PROJECT_NAME)


from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core.security_headers import SecurityHeadersMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Simulated Revenue & Forest Department REST Service for GovMesh SIH26129 Prototype",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENABLE_DOCS else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.ENABLE_DOCS else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.ENABLE_DOCS else None,
    lifespan=lifespan,
)

# 1. Transport & HTTP Security Middleware (SEC-06)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Host Header Validation (only active when ALLOWED_HOSTS is explicitly restricted)
if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# 3. Set up CORS and global error handlers
setup_cors(app)
register_error_handlers(app)

@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["Root"],
    summary="Root Service Information",
)
def root_info():
    """Returns basic service metadata and links to docs and health checks."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
    }

# Root-level health endpoints for infrastructure & orchestrator health checks
@app.get(
    "/health",
    response_model=ServiceHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Root Health"],
    summary="Root Service Health Check",
)
@app.get(
    "/api/health",
    response_model=ServiceHealthResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def root_health():
    """Returns basic service health status."""
    return HealthService.get_service_health()


@app.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Root Health"],
    summary="Root Database Health Check",
)
@app.get(
    "/api/health/db",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def root_db_health():
    """Validates PostgreSQL connectivity status and latency."""
    return HealthService.get_database_health()


# Mount versioned API routes across all possible rewrite prefixes
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/v1")
app.include_router(api_router, prefix="")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
