from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "GovMesh SIH26129 - Revenue & Forest Department System"
    SERVICE_NAME: str = "revenue-department"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Phase 05: Failure Simulation Controls (NONE | API_UNAVAILABLE | TIMEOUT | INTERNAL_ERROR)
    FAILURE_MODE: str = "NONE"
    SIMULATION_LATENCY_MS: int = 0

    # Server Ports
    BACKEND_PORT: int = int(os.getenv("PORT", "8000"))
    FRONTEND_PORT: int = 5173

    # JWT & Session Configuration
    JWT_SECRET: str = "dev-revenue-department-secret-key-sih26129-do-not-use-in-prod-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SESSION_TIMEOUT_MINUTES: int = 30

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/revenue_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_TIMEOUT_SECONDS: int = 5

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
