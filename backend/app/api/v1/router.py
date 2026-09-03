from fastapi import APIRouter
from app.api.v1.endpoints import health, applications, auth, admin, revenue_workflow, notifications, documents, analytics

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, tags=["Authentication & Session"])
api_router.include_router(admin.router, tags=["Administration & RBAC"])
api_router.include_router(applications.router, tags=["Applications (Intake & Management)"])
api_router.include_router(revenue_workflow.router, tags=["Revenue Address Verification Workflow"])
api_router.include_router(notifications.router, tags=["Departmental Notifications"])
api_router.include_router(documents.router, tags=["Proof Documents & OCR Verification"])
api_router.include_router(analytics.router, tags=["Revenue Department Analytics & Operational Dashboard"])
