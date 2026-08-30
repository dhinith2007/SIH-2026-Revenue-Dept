from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base


class SystemHealthPing(Base):
    """
    Lightweight health verification model for Revenue Department database.
    Used in Phase 01 to validate database read/write readiness.
    """
    __tablename__ = "system_health_pings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(100), default="revenue-department", nullable=False)
    ping_type = Column(String(50), default="startup_check", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
