import os
import time
from typing import Generator, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base

_DB_AVAILABLE: Optional[bool] = None
_LAST_DB_CHECK: float = 0.0

def is_db_available() -> bool:
    global _DB_AVAILABLE, _LAST_DB_CHECK
    now = time.time()
    if _DB_AVAILABLE is False and (now - _LAST_DB_CHECK < 60.0):
        return False
    if os.getenv("VERCEL") and ("localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL):
        _DB_AVAILABLE = False
        _LAST_DB_CHECK = now
        return False
    return True

def mark_db_unavailable():
    global _DB_AVAILABLE, _LAST_DB_CHECK
    _DB_AVAILABLE = False
    _LAST_DB_CHECK = time.time()

# Configure engine with pooling and short connection timeouts for serverless resilience
connect_timeout = 2 if (os.getenv("VERCEL") or "localhost" in settings.DATABASE_URL) else settings.DB_TIMEOUT_SECONDS
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args={"connect_timeout": connect_timeout} if "postgresql" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    if not is_db_available():
        logger.info("Operating in standalone/serverless mode with synchronized memory fallback store.")
        return
    try:
        # Import models so Base metadata is populated
        import app.models.health       # noqa: F401
        import app.models.user         # noqa: F401
        import app.models.application  # noqa: F401
        import app.models.audit        # noqa: F401
        import app.models.consent      # noqa: F401
        import app.models.notification # noqa: F401
        import app.models.document_evidence # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully (health, users, applications, audit, consents, notifications, document_evidence).")

        # Automatically ensure standard demo dataset is seeded idempotently
        with SessionLocal() as db_session:
            from app.db.seed import seed_database
            seed_database(db=db_session)
    except Exception as exc:
        mark_db_unavailable()
        logger.warning("Could not automatically initialize DB tables, falling back to memory store: %s", exc)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session.

    Explicitly rolls back any uncommitted work before closing the session
    so that failed requests never leave the connection in a dirty state.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
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
