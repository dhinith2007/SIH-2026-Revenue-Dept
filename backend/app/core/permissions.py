from enum import Enum
from typing import Set, Dict, Union


class RoleEnum(str, Enum):
    REVENUE_OFFICER = "REVENUE_OFFICER"
    SENIOR_REVENUE_OFFICER = "SENIOR_REVENUE_OFFICER"
    DEPARTMENT_ADMINISTRATOR = "DEPARTMENT_ADMINISTRATOR"
    READ_ONLY_AUDITOR = "READ_ONLY_AUDITOR"


class PermissionEnum(str, Enum):
    # Application & Document Scrutiny (Revenue Officer)
    APPLICATION_VIEW_ASSIGNED = "APPLICATION_VIEW_ASSIGNED"
    APPLICATION_VIEW_ALL = "APPLICATION_VIEW_ALL"
    DOCUMENT_VERIFY = "DOCUMENT_VERIFY"
    APPLICATION_APPROVE = "APPLICATION_APPROVE"
    APPLICATION_REJECT = "APPLICATION_REJECT"
    REQUEST_INFORMATION = "REQUEST_INFORMATION"

    # Escalation & Overrides (Senior Revenue Officer)
    ESCALATED_CASE_REVIEW = "ESCALATED_CASE_REVIEW"
    EXCEPTION_OVERRIDE = "EXCEPTION_OVERRIDE"

    # Administration & Configuration (Department Administrator)
    USER_MANAGE = "USER_MANAGE"
    SERVICE_METADATA_CONFIGURE = "SERVICE_METADATA_CONFIGURE"
    SYSTEM_HEALTH_VIEW = "SYSTEM_HEALTH_VIEW"

    # Audit & Compliance (Read-only Auditor)
    AUDIT_VIEW = "AUDIT_VIEW"


# Explicit Role-to-Permissions Matrix
ROLE_PERMISSIONS: Dict[RoleEnum, Set[PermissionEnum]] = {
    RoleEnum.REVENUE_OFFICER: {
        PermissionEnum.APPLICATION_VIEW_ASSIGNED,
        PermissionEnum.DOCUMENT_VERIFY,
        PermissionEnum.APPLICATION_APPROVE,
        PermissionEnum.APPLICATION_REJECT,
        PermissionEnum.REQUEST_INFORMATION,
    },
    RoleEnum.SENIOR_REVENUE_OFFICER: {
        # Inherits normal officer viewing rights + escalation and override powers
        PermissionEnum.APPLICATION_VIEW_ASSIGNED,
        PermissionEnum.APPLICATION_VIEW_ALL,
        PermissionEnum.DOCUMENT_VERIFY,
        PermissionEnum.APPLICATION_APPROVE,
        PermissionEnum.APPLICATION_REJECT,
        PermissionEnum.REQUEST_INFORMATION,
        PermissionEnum.ESCALATED_CASE_REVIEW,
        PermissionEnum.EXCEPTION_OVERRIDE,
    },
    RoleEnum.DEPARTMENT_ADMINISTRATOR: {
        PermissionEnum.USER_MANAGE,
        PermissionEnum.SERVICE_METADATA_CONFIGURE,
        PermissionEnum.SYSTEM_HEALTH_VIEW,
        PermissionEnum.APPLICATION_VIEW_ALL,
        PermissionEnum.DOCUMENT_VERIFY,
        PermissionEnum.EXCEPTION_OVERRIDE,
    },
    RoleEnum.READ_ONLY_AUDITOR: {
        PermissionEnum.AUDIT_VIEW,
        PermissionEnum.APPLICATION_VIEW_ALL,
    },
}


def get_permissions_for_role(role: Union[str, RoleEnum]) -> Set[PermissionEnum]:
    """Resolves permissions assigned to a given departmental role."""
    try:
        role_enum = RoleEnum(role) if isinstance(role, str) else role
        return ROLE_PERMISSIONS.get(role_enum, set())
    except ValueError:
        return set()


def has_permission(role: Union[str, RoleEnum], permission: PermissionEnum) -> bool:
    """Checks whether a role possesses a specific permission."""
    return permission in get_permissions_for_role(role)
