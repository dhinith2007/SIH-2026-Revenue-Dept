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


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Simulated Revenue & Forest Department REST Service for GovMesh SIH26129 Prototype",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Set up CORS and global error handlers
setup_cors(app)
register_error_handlers(app)

# Root-level health endpoints for infrastructure & orchestrator health checks
@app.get(
    "/health",
    response_model=ServiceHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Root Health"],
    summary="Root Service Health Check",
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
def root_db_health():
    """Validates PostgreSQL connectivity status and latency."""
    return HealthService.get_database_health()


# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
