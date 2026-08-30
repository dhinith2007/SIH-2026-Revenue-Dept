import time
from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base

# Configure engine with pooling and connection timeouts
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args={"connect_timeout": settings.DB_TIMEOUT_SECONDS} if "postgresql" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    try:
        # Import models so Base metadata is populated
        import app.models.health       # noqa: F401
        import app.models.user         # noqa: F401
        import app.models.application  # noqa: F401
        import app.models.audit        # noqa: F401
        import app.models.consent      # noqa: F401
        import app.models.notification # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully (health, users, applications, audit, consents, notifications).")
    except Exception as exc:
        logger.warning("Could not automatically initialize DB tables: %s", exc)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> Dict[str, Any]:
    """
    Validates PostgreSQL connectivity and measures latency in milliseconds.
    """
    start_time = time.perf_counter()
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if result == 1:
                return {
                    "status": "connected",
                    "database": "PostgreSQL",
                    "latency_ms": latency_ms,
                    "error": None,
                }
            else:
                return {
                    "status": "degraded",
                    "database": "PostgreSQL",
                    "latency_ms": latency_ms,
                    "error": "Unexpected query response",
                }
    except SQLAlchemyError as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error("Database health check failed: %s", exc)
        return {
            "status": "disconnected",
            "database": "PostgreSQL",
            "latency_ms": latency_ms,
            "error": str(exc),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error("Unexpected error in database health check: %s", exc)
        return {
            "status": "error",
            "database": "PostgreSQL",
            "latency_ms": latency_ms,
            "error": str(exc),
        }
