from typing import Optional
from pydantic import BaseModel


class ServiceHealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    version: str
    timestamp: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
    latency_ms: float
    error: Optional[str] = None


class SystemInfoResponse(BaseModel):
    department: str
    sub_department: str
    state: str
    project_code: str
    architecture_role: str
    current_phase: str
    simulated: bool
    status: str
