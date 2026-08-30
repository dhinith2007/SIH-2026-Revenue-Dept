from typing import List, Dict, Any
from app.core.security import hash_password
from app.core.permissions import RoleEnum

DEMO_USERS: List[Dict[str, Any]] = [
    {
        "id": "USR-REV-001",
        "username": "revenue.officer",
        "email": "officer.pune@revenue.gov.in",
        "mobile": "9820011223",
        "plain_password": "Officer@2026",
        "full_name": "Rajendra Mane (Revenue Officer)",
        "role": RoleEnum.REVENUE_OFFICER.value,
        "department": "Revenue & Forest Department",
        "division": "Pune Division (Haveli Tahsil)",
        "is_active": True,
    },
    {
        "id": "USR-REV-002",
        "username": "senior.officer",
        "email": "senior.pune@revenue.gov.in",
        "mobile": "9820011224",
        "plain_password": "Senior@2026",
        "full_name": "Dr. Sunita Bhosale (Senior Officer / Tahsildar)",
        "role": RoleEnum.SENIOR_REVENUE_OFFICER.value,
        "department": "Revenue & Forest Department",
        "division": "Pune Division (District Collectorate)",
        "is_active": True,
    },
    {
        "id": "USR-REV-003",
        "username": "revenue.admin",
        "email": "admin.revenue@revenue.gov.in",
        "mobile": "9820011225",
        "plain_password": "Admin@2026",
        "full_name": "Amit Kulkarni (Department Administrator)",
        "role": RoleEnum.DEPARTMENT_ADMINISTRATOR.value,
        "department": "Revenue & Forest Department",
        "division": "State Headquarters (Mantralaya)",
        "is_active": True,
    },
    {
        "id": "USR-REV-004",
        "username": "revenue.auditor",
        "email": "auditor.state@revenue.gov.in",
        "mobile": "9820011226",
        "plain_password": "Auditor@2026",
        "full_name": "Meera Deshpande (State Revenue Auditor)",
        "role": RoleEnum.READ_ONLY_AUDITOR.value,
        "department": "Revenue & Forest Department",
        "division": "State Revenue Audit Directorate",
        "is_active": True,
    },
    {
        "id": "USR-REV-005",
        "username": "inactive.officer",
        "email": "inactive@revenue.gov.in",
        "mobile": "9820011227",
        "plain_password": "Inactive@2026",
        "full_name": "Inactive Officer Account (Test)",
        "role": RoleEnum.REVENUE_OFFICER.value,
        "department": "Revenue & Forest Department",
        "division": "Suspended Desk",
        "is_active": False,
    },
]


def get_seeded_users_with_hashes() -> List[Dict[str, Any]]:
    """Returns demo users with pre-computed password hashes."""
    seeded = []
    for user_data in DEMO_USERS:
        u = user_data.copy()
        plain_pw = u.pop("plain_password")
        u["password_hash"] = hash_password(plain_pw)
        seeded.append(u)
    return seeded
