from typing import Generator, Optional, List, Dict, Any, Callable
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.consent_repository import ConsentRepository
from app.repositories.document_evidence_repository import DocumentEvidenceRepository
from app.services.auth_service import AuthService
from app.services.workflow_service import WorkflowService
from app.services.notification_service import NotificationService
from app.core.security import decode_access_token
from app.core.permissions import RoleEnum, PermissionEnum, has_permission, get_permissions_for_role
from app.core.errors import (
    AuthenticationError,
    InactiveAccountError,
    InsufficientPermissionError,
    TokenInvalidError,
)
from app.core.logging import logger

security_scheme = HTTPBearer(auto_error=False)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_application_repository(db: Session = Depends(get_db)) -> ApplicationRepository:
    return ApplicationRepository(db)


def get_audit_repository(db: Session = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


def get_notification_repository(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)


def get_consent_repository(db: Session = Depends(get_db)) -> ConsentRepository:
    return ConsentRepository(db)


def get_document_evidence_repository(db: Session = Depends(get_db)) -> DocumentEvidenceRepository:
    return DocumentEvidenceRepository(db)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


def get_notification_service(
    notif_repo: NotificationRepository = Depends(get_notification_repository),
) -> NotificationService:
    return NotificationService(notif_repo)


def get_workflow_service(
    app_repo: ApplicationRepository = Depends(get_application_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    notif_repo: NotificationRepository = Depends(get_notification_repository),
    consent_repo: ConsentRepository = Depends(get_consent_repository),
) -> WorkflowService:
    return WorkflowService(app_repo, audit_repo, notif_repo, consent_repo)


def get_analytics_service(
    app_repo: ApplicationRepository = Depends(get_application_repository),
    evidence_repo: DocumentEvidenceRepository = Depends(get_document_evidence_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    from app.services.analytics_service import AnalyticsService
    return AnalyticsService(app_repo, evidence_repo, audit_repo)


def get_integration_service(
    app_repo: ApplicationRepository = Depends(get_application_repository),
    consent_repo: ConsentRepository = Depends(get_consent_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    notif_repo: NotificationRepository = Depends(get_notification_repository),
):
    from app.services.integration_service import IntegrationService
    return IntegrationService(app_repo, consent_repo, audit_repo, notif_repo)


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Dict[str, Any]:
    """
    Extracts Bearer token from header, validates JWT claims, and retrieves user.
    """
    if not auth_header or not auth_header.credentials:
        logger.warning("Request rejected: missing or invalid Bearer authentication header")
        raise AuthenticationError(
            message="Authentication required. Please provide a valid Bearer token.",
            code="AUTHENTICATION_REQUIRED",
        )

    token = auth_header.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise TokenInvalidError()

    user = user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationError(
            message="User session not found or account was deleted.",
            code="AUTHENTICATION_REQUIRED",
        )

    if not user.get("is_active", False):
        raise InactiveAccountError()

    return user


def require_role(*allowed_roles: RoleEnum) -> Callable:
    """
    FastAPI dependency factory to enforce specific departmental roles.
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role_str = current_user.get("role")
        try:
            user_role = RoleEnum(user_role_str)
        except ValueError:
            raise InsufficientPermissionError(
                message=f"Unknown role '{user_role_str}' assigned to user."
            )

        if user_role not in allowed_roles:
            allowed_names = [r.value for r in allowed_roles]
            logger.warning(
                "Access forbidden: user '%s' with role '%s' tried to access endpoint requiring one of %s",
                current_user["username"],
                user_role.value,
                allowed_names,
            )
            raise InsufficientPermissionError(
                message=f"Access forbidden for role '{user_role.value}'. Required role: {', '.join(allowed_names)}."
            )
        return current_user

    return role_checker


def require_permission(*required_permissions: PermissionEnum) -> Callable:
    """
    FastAPI dependency factory to enforce granular RBAC permissions.
    """
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        user_perms = get_permissions_for_role(user_role)

        missing_perms = [p for p in required_permissions if p not in user_perms]
        if missing_perms:
            missing_names = [p.value for p in missing_perms]
            logger.warning(
                "Access forbidden: user '%s' lacks required permissions: %s",
                current_user["username"],
                missing_names,
            )
            raise InsufficientPermissionError(
                message=f"You do not possess the required departmental permissions: {', '.join(missing_names)}."
            )
        return current_user

    return permission_checker
