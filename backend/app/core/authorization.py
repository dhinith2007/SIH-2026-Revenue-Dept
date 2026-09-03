from typing import Dict, Any, Optional
from app.core.permissions import RoleEnum, PermissionEnum, has_permission
from app.core.errors import (
    InsufficientPermissionError,
    ApplicationFinalizedError,
    InactiveAccountError,
)
from app.core.logging import logger


def verify_application_access(
    current_user: Dict[str, Any],
    app: Dict[str, Any],
    for_mutation: bool = False,
    is_override: bool = False,
) -> None:
    """
    Authorizes an officer's access to an application and its associated proof documents.
    Enforces:
    1. Active account status
    2. Auditor read-only boundary (cannot mutate)
    3. Finalized application immutability (VERIFIED/REJECTED cannot mutate)
    4. Senior Officer / Administrator department-wide access
    5. Revenue Officer ownership boundaries (cannot view/mutate other officers' assigned applications)
    6. Document override specific privileges (requires EXCEPTION_OVERRIDE or assigned officer status)
    """
    if not current_user.get("is_active", False):
        raise InactiveAccountError(message="This department account is inactive. Access denied.")

    user_role = current_user.get("role")
    user_id = current_user.get("id")
    app_id = app.get("application_id", "UNKNOWN")
    app_status = app.get("status", "PENDING")
    assigned_officer_id = app.get("assigned_officer_id")

    # 1. Finalized application check for mutations (takes precedence across all roles)
    if (for_mutation or is_override) and app_status in ("VERIFIED", "REJECTED"):
        logger.warning(
            "Access denied: Attempted mutation on finalized application '%s' (status: %s) by '%s'",
            app_id,
            app_status,
            current_user.get("username"),
        )
        raise ApplicationFinalizedError(
            message=f"Application '{app_id}' has already been finalized ({app_status}) and is strictly immutable."
        )

    # 2. Auditor read-only guarantee
    if user_role == RoleEnum.READ_ONLY_AUDITOR.value:
        if for_mutation or is_override:
            logger.warning(
                "Access forbidden: Auditor '%s' attempted mutation on application '%s'",
                current_user.get("username"),
                app_id,
            )
            raise InsufficientPermissionError(
                message="Auditor role has read-only access and cannot upload, verify, or modify documents."
            )
        # Read operations permitted for auditor
        return

    # 3. Privileged roles: Senior Officer & Department Administrator
    if user_role in (RoleEnum.SENIOR_REVENUE_OFFICER.value, RoleEnum.DEPARTMENT_ADMINISTRATOR.value):
        # Has broad department-wide operational and override authority
        return

    # 4. Standard Revenue Officer
    if user_role == RoleEnum.REVENUE_OFFICER.value:
        # Check assignment boundary (IDOR protection)
        if assigned_officer_id and assigned_officer_id != user_id:
            logger.warning(
                "IDOR access forbidden: Officer '%s' (ID: %s) tried to access application '%s' assigned to '%s'",
                current_user.get("username"),
                user_id,
                app_id,
                assigned_officer_id,
            )
            raise InsufficientPermissionError(
                message="You do not possess authorization to access or modify records for an application assigned to another officer."
            )

        # For manual override: only allowed if assigned to this officer
        if is_override and assigned_officer_id != user_id:
            logger.warning(
                "Override forbidden: Officer '%s' attempted override on unassigned application '%s'",
                current_user.get("username"),
                app_id,
            )
            raise InsufficientPermissionError(
                message="Manual document override requires case assignment or senior officer privileges."
            )

        return

    # Unknown role
    logger.warning("Access forbidden: unrecognized role '%s' for user '%s'", user_role, current_user.get("username"))
    raise InsufficientPermissionError(message=f"Role '{user_role}' is not authorized for departmental operations.")
