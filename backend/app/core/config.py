import os
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

KNOWN_INSECURE_JWT_SECRETS = {
    "dev-revenue-department-secret-key-sih26129-do-not-use-in-prod-32bytes",
    "secret",
    "changeme",
    "default",
    "password",
}

KNOWN_INSECURE_DB_URLS = {
    "postgresql://postgres:postgres@localhost:5432/revenue_db",
    "postgresql://postgres:postgres@127.0.0.1:5432/revenue_db",
}


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

    # Phase 10: OCR Engine Configuration
    OCR_PROVIDER: str = "SIMULATED"  # SIMULATED | TESSERACT
    TESSERACT_CMD: str = ""  # Optional custom executable path
    TESSERACT_LANG: str = "eng+mar"  # Configured languages
    OCR_TIMEOUT_SECONDS: int = 15  # Bounded execution time limit

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

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # Transport & HTTP Security (Phase 09 Step 05)
    ENABLE_HSTS: bool = False
    ENABLE_DOCS: bool = True
    ALLOWED_HOSTS: Union[List[str], str] = ["*"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
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

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """
        Fails fast during application initialization if running in production mode
        with missing, unsafe, or default development credentials.
        Never prints secret values in error messages.
        """
        if self.APP_ENV.lower() in ("production", "prod"):
            # 1. Validate JWT_SECRET
            if not self.JWT_SECRET or len(self.JWT_SECRET.strip()) < 32:
                raise ValueError(
                    "Production configuration error: JWT_SECRET must be configured with a secure key of at least 32 bytes."
                )
            if (
                self.JWT_SECRET.strip() in KNOWN_INSECURE_JWT_SECRETS
                or "do-not-use-in-prod" in self.JWT_SECRET.lower()
            ):
                raise ValueError(
                    "Production configuration error: JWT_SECRET is set to a known development/insecure default key."
                )

            # 2. Validate DATABASE_URL
            if not self.DATABASE_URL or not self.DATABASE_URL.strip():
                raise ValueError(
                    "Production configuration error: DATABASE_URL must be configured."
                )
            if (
                self.DATABASE_URL.strip() in KNOWN_INSECURE_DB_URLS
                or "postgres:postgres@localhost" in self.DATABASE_URL.lower()
                or "postgres:postgres@127.0.0.1" in self.DATABASE_URL.lower()
            ):
                raise ValueError(
                    "Production configuration error: DATABASE_URL is using known development credentials or localhost host."
                )

            # 3. Validate CORS origins (SEC-06: Wildcard '*' cannot be combined with credentials in production)
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Production configuration error: CORS_ORIGINS must not contain wildcard '*' when credentials are enabled."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
