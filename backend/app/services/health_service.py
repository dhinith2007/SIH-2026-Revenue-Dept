from datetime import datetime, timezone
from typing import Dict, Any
from app.core.config import settings
from app.db.session import check_database_health


class HealthService:
    @staticmethod
    def get_service_health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "environment": settings.APP_ENV,
            "version": settings.VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def get_database_health() -> Dict[str, Any]:
        return check_database_health()

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        return {
            "department": "Revenue & Forest Department",
            "sub_department": "Land Records & Citizen Revenue Services",
            "state": "Maharashtra",
            "project_code": "SIH26129",
            "architecture_role": "Independent Department System (Department 1)",
            "current_phase": "Phase 01 - Foundation & UI Shell",
            "simulated": True,
            "status": "OPERATIONAL",
        }
