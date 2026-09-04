import sys
import os

# Ensure backend root is on sys.path when invoked directly
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_current_dir, "..", ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import hash_password
from app.core.permissions import RoleEnum
from app.core.logging import logger

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
    {
        "id": "USR-REV-006",
        "username": "other.officer",
        "email": "other.officer@revenue.gov.in",
        "mobile": "9820011228",
        "plain_password": "Officer@2026",
        "full_name": "Kavita Shinde (Secondary Revenue Officer)",
        "role": RoleEnum.REVENUE_OFFICER.value,
        "department": "Revenue & Forest Department",
        "division": "Pune Division (Baramati Tahsil)",
        "is_active": True,
    },
]


import copy

def get_seeded_users_with_hashes() -> List[Dict[str, Any]]:
    """Returns demo users with pre-computed password hashes."""
    seeded = []
    for user_data in DEMO_USERS:
        u = copy.deepcopy(user_data)
        plain_pw = u.pop("plain_password")
        u["password_hash"] = hash_password(plain_pw)
        seeded.append(u)
    return seeded



def _make_json_safe(val: Any) -> Any:
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, dict):
        return {k: _make_json_safe(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_make_json_safe(v) for v in val]
    return val


def seed_database(db: Optional[Session] = None, refresh_apps: bool = False) -> Dict[str, int]:
    """
    Idempotent database seeder for PostgreSQL.
    Populates standard demo officers, synthetic applications, consents, notifications,
    and baseline audit history without modifying existing modified applications or destroying data.
    If refresh_apps=True, resets the 12 synthetic demo applications to their baseline states.
    """
    from app.db.session import SessionLocal, is_db_available
    from app.db.seed_applications import get_seeded_applications
    from app.models.user import User
    from app.models.application import Application
    from app.models.consent import ConsentRecord
    from app.models.audit import AuditLog, ApplicationStatusHistory
    from app.models.notification import Notification

    if not is_db_available():
        logger.info("Database unavailable or serverless mode. Skipping PostgreSQL seed execution.")
        return {"users": 0, "applications": 0, "consents": 0, "notifications": 0, "audit_logs": 0}

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    stats = {
        "users_created": 0,
        "users_existing": 0,
        "applications_created": 0,
        "applications_existing": 0,
        "consents_created": 0,
        "consents_existing": 0,
        "notifications_created": 0,
        "notifications_existing": 0,
        "audit_logs_created": 0,
        "status_history_created": 0,
    }

    try:
        now = datetime.now(timezone.utc)
        future_expiry = now + timedelta(days=365)

        # --------------------------------------------------------------------
        # 1. Seed Demo Users (RBAC Officers)
        # --------------------------------------------------------------------
        demo_users = get_seeded_users_with_hashes()
        for u in demo_users:
            existing_user = db.query(User).filter((User.id == u["id"]) | (User.username == u["username"])).first()
            if not existing_user:
                db_user = User(
                    id=u["id"],
                    username=u["username"],
                    email=u["email"],
                    mobile=u["mobile"],
                    password_hash=u["password_hash"],
                    full_name=u["full_name"],
                    role=u["role"],
                    department=u.get("department", "Revenue & Forest Department"),
                    division=u.get("division", "Pune Division"),
                    is_active=u.get("is_active", True),
                    created_at=now,
                    updated_at=now,
                    last_login_at=None,
                    failed_login_attempts=0,
                    locked_until=None,
                )
                db.add(db_user)
                stats["users_created"] += 1
            else:
                if refresh_apps:
                    existing_user.failed_login_attempts = 0
                    existing_user.locked_until = None
                stats["users_existing"] += 1

        db.flush()

        # --------------------------------------------------------------------
        # 2. Seed Synthetic Applications
        # --------------------------------------------------------------------
        synthetic_apps = get_seeded_applications()
        for a in synthetic_apps:
            payload = dict(a.get("data_payload", {}))
            if "consent_record" in a and "consent_record" not in payload:
                payload["consent_record"] = a["consent_record"]
            safe_payload = _make_json_safe(payload)

            existing_app = db.query(Application).filter(Application.application_id == a["application_id"]).first()
            if not existing_app:
                db_app = Application(
                    id=a["id"],
                    application_id=a["application_id"],
                    correlation_id=a["correlation_id"],
                    citizen_reference_id=a["citizen_reference_id"],
                    service_type=a.get("service_type", "ADDRESS_CHANGE"),
                    requested_operation=a.get("requested_operation", "UPDATE_REVENUE_ADDRESS"),
                    purpose=a.get("purpose", "Update Revenue address record & 7/12 land registry linkage"),
                    consent_reference=a.get("consent_reference", "CONSENT-NONE"),
                    priority=a.get("priority", "NORMAL"),
                    status=a.get("status", "PENDING"),
                    required_action=a.get("required_action", "Desk scrutiny required"),
                    citizen_name=a.get("citizen_name", "Citizen"),
                    received_at=a.get("received_at", now),
                    updated_at=a.get("updated_at", now),
                    processing_started_at=a.get("processing_started_at"),
                    completed_at=a.get("completed_at"),
                    assigned_officer_id=a.get("assigned_officer_id"),
                    data_payload=safe_payload,
                    workflow_history=a.get("workflow_history", []),
                )
                db.add(db_app)
                stats["applications_created"] += 1
            else:
                stats["applications_existing"] += 1
                if refresh_apps:
                    existing_app.status = a.get("status", "PENDING")
                    existing_app.required_action = a.get("required_action", "Desk scrutiny required")
                    existing_app.processing_started_at = a.get("processing_started_at")
                    existing_app.completed_at = a.get("completed_at")
                    existing_app.assigned_officer_id = a.get("assigned_officer_id")
                    existing_app.data_payload = safe_payload
                    existing_app.workflow_history = list(a.get("workflow_history", []))
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(existing_app, "data_payload")
                    flag_modified(existing_app, "workflow_history")
                else:
                    curr_payload = dict(existing_app.data_payload or {})
                    if "consent_record" in a and "consent_record" not in curr_payload:
                        curr_payload["consent_record"] = _make_json_safe(a["consent_record"])
                        existing_app.data_payload = curr_payload
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(existing_app, "data_payload")

            # Also ensure in-memory store matches if refresh requested
            if refresh_apps:
                try:
                    from app.repositories.application_repository import _MEM_APPLICATIONS
                    _MEM_APPLICATIONS[a["application_id"]] = dict(a)
                    from app.repositories.user_repository import _MEM_USERS
                    for du in DEMO_USERS:
                        if du["id"] in _MEM_USERS:
                            _MEM_USERS[du["id"]]["failed_login_attempts"] = 0
                            _MEM_USERS[du["id"]]["locked_until"] = None
                except Exception:
                    pass

            # ----------------------------------------------------------------
            # 3. Seed Consents
            # ----------------------------------------------------------------
            consent_ref = a.get("consent_reference")
            if consent_ref:
                existing_consent = db.query(ConsentRecord).filter(ConsentRecord.consent_reference == consent_ref).first()
                if not existing_consent:
                    c_rec = a.get("consent_record", {})
                    c_status = c_rec.get("status", "VALID")
                    db_consent = ConsentRecord(
                        id=f"CONS-{a['id']}",
                        consent_reference=consent_ref,
                        application_id=a["application_id"],
                        status=c_status,
                        purpose=c_rec.get("purpose", a.get("purpose", "Update Revenue address record")),
                        data_scope=c_rec.get("data_scope", "address.change"),
                        recipient=c_rec.get("recipient", "Revenue & Forest Department"),
                        issued_at=a.get("received_at", now),
                        expires_at=c_rec.get("expires_at", future_expiry),
                        revoked_at=c_rec.get("revoked_at"),
                        validated_at=now if c_status == "VALID" else None,
                        validation_result={"status": c_status, "seeded": True},
                    )
                    db.add(db_consent)
                    stats["consents_created"] += 1
                else:
                    stats["consents_existing"] += 1

            # ----------------------------------------------------------------
            # 4. Seed Baseline Status History & Audit Logs for Apps
            # ----------------------------------------------------------------
            hist_id = f"HIST-{a['id']}"
            existing_hist = db.query(ApplicationStatusHistory).filter(ApplicationStatusHistory.id == hist_id).first()
            if not existing_hist:
                db_hist = ApplicationStatusHistory(
                    id=hist_id,
                    application_id=a["application_id"],
                    previous_status=None,
                    new_status=a.get("status", "PENDING"),
                    action="APPLICATION_INTAKE",
                    changed_by="GovMesh Ingestion Channel",
                    reason="Initial application payload ingested via statutory contract.",
                    timestamp=a.get("received_at", now),
                    correlation_id=a["correlation_id"],
                )
                db.add(db_hist)
                stats["status_history_created"] += 1

            audit_id = f"AUD-{a['id']}"
            existing_audit = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
            if not existing_audit:
                db_audit = AuditLog(
                    id=audit_id,
                    officer_id=a.get("assigned_officer_id") or "SYSTEM",
                    officer_name="GovMesh Intake Channel",
                    application_id=a["application_id"],
                    action="APPLICATION_INTAKE",
                    previous_status=None,
                    new_status=a.get("status", "PENDING"),
                    reason="Initial intake registered in department queue.",
                    correlation_id=a["correlation_id"],
                    timestamp=a.get("received_at", now),
                    details={"seed_record": a["id"], "service_type": a.get("service_type")},
                )
                db.add(db_audit)
                stats["audit_logs_created"] += 1

        # --------------------------------------------------------------------
        # 5. Seed Department Notifications
        # --------------------------------------------------------------------
        initial_notifs = [
            {
                "id": "NOTIF-REV-001",
                "type": "NEW_APPLICATION",
                "application_id": "GM-2026-000124",
                "title": "New Revenue Application Received",
                "message": "New ADDRESS_CHANGE application for Rajesh Shantaram Patil (Haveli, Pune) requires verification.",
                "timestamp": now - timedelta(minutes=45),
                "read": False,
                "severity": "INFO",
                "target_role": "REVENUE_OFFICER",
            },
            {
                "id": "NOTIF-REV-002",
                "type": "ACTION_REQUIRED",
                "application_id": "GM-2026-000128",
                "title": "Action Required: Missing Document",
                "message": "Application GM-2026-000128 is missing address proof document. Officer query needed.",
                "timestamp": now - timedelta(hours=1, minutes=30),
                "read": False,
                "severity": "WARNING",
                "target_role": "REVENUE_OFFICER",
            },
            {
                "id": "NOTIF-REV-003",
                "type": "CITIZEN_RESPONSE",
                "application_id": "GM-2026-000126",
                "title": "Citizen Response Ingested",
                "message": "Citizen Anand Mohan Shinde uploaded supplementary electricity bill proof for Nashik jurisdiction.",
                "timestamp": now - timedelta(hours=2),
                "read": False,
                "severity": "INFO",
                "target_role": "REVENUE_OFFICER",
            },
            {
                "id": "NOTIF-REV-004",
                "type": "WORKFLOW_COMPLETION",
                "application_id": "GM-2026-000131",
                "title": "Application Verified & Approved",
                "message": "Application GM-2026-000131 for Deepak Raghunath Jagtap has been approved and marked VERIFIED.",
                "timestamp": now - timedelta(hours=3),
                "read": True,
                "severity": "SUCCESS",
                "target_role": "ALL",
            },
            {
                "id": "NOTIF-REV-005",
                "type": "ESCALATION",
                "application_id": "GM-2026-000133",
                "title": "Urgent Application Priority Escalated",
                "message": "Urgent agricultural subsidy deadline for Meena Chandrakant Bhosale (Shirur) escalated for review.",
                "timestamp": now - timedelta(hours=4),
                "read": False,
                "severity": "CRITICAL",
                "target_role": "SENIOR_REVENUE_OFFICER",
            },
        ]

        for n in initial_notifs:
            existing_notif = db.query(Notification).filter(Notification.id == n["id"]).first()
            if not existing_notif:
                db_notif = Notification(
                    id=n["id"],
                    type=n["type"],
                    application_id=n["application_id"],
                    title=n["title"],
                    message=n["message"],
                    timestamp=n["timestamp"],
                    read=n["read"],
                    severity=n["severity"],
                    target_role=n["target_role"],
                )
                db.add(db_notif)
                stats["notifications_created"] += 1
            else:
                stats["notifications_existing"] += 1

        db.commit()
        logger.info("Database seeding completed successfully: %s", stats)
        return stats

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to seed database: %s", exc)
        raise
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    # Allow direct invocation: python -m app.db.seed or python backend/app/db/seed.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    backend_dir = os.path.dirname(app_dir)
    for p in [backend_dir, app_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)

    print("Executing PostgreSQL Seed Script...")
    result = seed_database()
    print("Seed execution finished with stats:")
    for k, v in result.items():
        print(f"  - {k}: {v}")
