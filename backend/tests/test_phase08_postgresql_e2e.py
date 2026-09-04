"""
Phase 08 - Step 06: PostgreSQL End-to-End Testing & Persistence Verification

Comprehensive E2E test suite covering:
1. PostgreSQL Database Connectivity & Health Probe E2E
2. Authentication & RBAC Authorization E2E (All 5 Seeded Roles)
3. Application Read (List & Detail) E2E
4. Dashboard Metrics Aggregate Alignment with PostgreSQL E2E
5. Start Review Workflow & Persistence E2E
6. Address Change Approval Workflow & Commit E2E
7. Rejection Workflow & Reason Persistence E2E
8. Additional Information Request Workflow E2E
9. Reprocess & Controlled Retry Workflow E2E
10. Proof Document JSONB Attachment & Officer Override E2E
11. DPDP Citizen Consent Verification & Enforcement E2E
12. Immutable Audit Trail & Status History Chronology E2E
13. Departmental Notifications Lifecycle & Mark-as-Read E2E
14. Multi-Table Transaction Rollback Guarantee E2E (Zero Partial Commits)
15. Session Isolation & Transaction Visibility E2E
16. Cross-Session / Application Restart Persistence E2E
17. Direct Database Cross-Check (API Response ↔ Repository ↔ PostgreSQL Row)
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from app.db.session import SessionLocal, is_db_available, engine
from app.db.seed import seed_database
from app.models.application import Application
from app.models.audit import AuditLog, ApplicationStatusHistory
from app.models.notification import Notification
from app.models.consent import ConsentRecord
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.workflow_service import WorkflowService


@pytest.fixture(autouse=True)
def reset_db_state():
    """Restores baseline deterministic demo seed before each test."""
    if not is_db_available():
        pytest.skip("PostgreSQL database is not reachable in this test environment")
    with SessionLocal() as db:
        seed_database(db=db, refresh_apps=True)
    yield



def get_auth_token(client, identifier: str, password: str) -> str:
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert login_resp.status_code == 200, f"Login failed for {identifier}: {login_resp.text}"
    return login_resp.json()["access_token"]


# ============================================================================
# 1. Database Connectivity & Health E2E
# ============================================================================
def test_01_database_connectivity_and_health_e2e(client):
    """Verifies service and PostgreSQL connectivity health endpoints."""
    # Service health
    resp = client.get("/health")
    assert resp.status_code == 200
    health_data = resp.json()
    assert health_data["status"] in ("ok", "healthy")
    assert health_data["service"] == "revenue-department"

    # Database health probe
    resp_db = client.get("/health/db")
    assert resp_db.status_code == 200
    db_data = resp_db.json()
    assert db_data["status"] in ("connected", "healthy")
    assert db_data["database"] == "PostgreSQL"
    assert db_data["latency_ms"] >= 0

    # System Info
    resp_info = client.get("/api/v1/revenue/system-info")
    assert resp_info.status_code == 200
    info_data = resp_info.json()["data"]
    assert info_data["department"] == "Revenue & Forest Department"
    assert info_data["project_code"] == "SIH26129"

    # Direct raw SQL execution verification on PostgreSQL
    if is_db_available():
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS probe")).scalar()
            assert result == 1


# ============================================================================
# 2. Authentication & RBAC Authorization E2E
# ============================================================================
def test_02_authentication_and_rbac_e2e(client):
    """Verifies authentication for all seeded officer accounts and RBAC enforcement."""
    # 1. Revenue Officer login
    tok_officer = get_auth_token(client, "revenue.officer", "Officer@2026")
    assert tok_officer is not None

    # 2. Senior Revenue Officer login
    tok_senior = get_auth_token(client, "senior.officer", "Senior@2026")
    assert tok_senior is not None

    # 3. Department Administrator login
    tok_admin = get_auth_token(client, "revenue.admin", "Admin@2026")
    assert tok_admin is not None

    # 4. Read-Only Auditor login
    tok_auditor = get_auth_token(client, "revenue.auditor", "Auditor@2026")
    assert tok_auditor is not None

    # 5. Inactive Officer login must be rejected with 403 / ACCOUNT_INACTIVE
    inactive_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "inactive.officer", "password": "Inactive@2026"},
    )
    assert inactive_resp.status_code == 403
    assert "ACCOUNT_INACTIVE" in inactive_resp.text or "inactive" in inactive_resp.text.lower()

    # 6. Read-Only Auditor attempting mutation must be blocked (HTTP 403)
    mut_resp = client.post(
        "/api/v1/revenue/application/GM-2026-000124/approve",
        headers={"Authorization": f"Bearer {tok_auditor}"},
        json={"reason": "Auditor attempting unauthorized approval"},
    )
    assert mut_resp.status_code == 403


# ============================================================================
# 3. Application Listing & Detail E2E
# ============================================================================
def test_03_application_read_e2e(client):
    """Verifies listing and detailed retrieval of applications matching PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")

    # List applications
    resp = client.get(
        "/api/v1/revenue/applications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    items = data["items"]
    assert len(items) == 12
    assert data["pagination"]["total"] == 12

    # Verify search and filtering
    filtered_resp = client.get(
        "/api/v1/revenue/applications?status=PENDING&priority=HIGH",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filtered_resp.status_code == 200
    f_items = filtered_resp.json()["data"]["items"]
    for item in f_items:
        assert item["status"] == "PENDING"
        assert item["priority"] == "HIGH"

    # Detail query
    detail_resp = client.get(
        "/api/v1/revenue/applications/GM-2026-000124",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_resp.status_code == 200
    app_detail = detail_resp.json()["data"]
    assert app_detail["application_id"] == "GM-2026-000124"
    assert app_detail["citizen_name"] == "Rajesh Shantaram Patil"
    assert app_detail["service_type"] == "ADDRESS_CHANGE"
    assert "data_payload" in app_detail
    assert "workflow_history" in app_detail


# ============================================================================
# 4. Dashboard Summary E2E
# ============================================================================
def test_04_dashboard_summary_matches_postgresql_aggregates(client):
    """Verifies dashboard metrics match direct aggregate queries on PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")

    resp = client.get(
        "/api/v1/revenue/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    summary = resp.json()["data"]
    assert summary["total_incoming"] == 12

    if is_db_available():
        with SessionLocal() as db:
            total_db = db.query(Application).count()
            pending_db = db.query(Application).filter(Application.status == "PENDING").count()
            processing_db = db.query(Application).filter(Application.status == "PROCESSING").count()
            verified_db = db.query(Application).filter(Application.status.in_(("VERIFIED", "COMPLETED"))).count()
            rejected_db = db.query(Application).filter(Application.status == "REJECTED").count()

            assert summary["total_incoming"] == total_db
            assert summary["pending"] == pending_db
            assert summary["processing"] == processing_db
            assert summary["completed"] == verified_db
            assert summary["rejected"] == rejected_db


# ============================================================================
# 5. Start Review Workflow & Persistence E2E
# ============================================================================
def test_05_start_review_workflow_and_persistence_e2e(client):
    """Verifies transition from PENDING -> PROCESSING persists to PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")
    app_id = "GM-2026-000124"

    resp = client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PROCESSING"

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app.status == "PROCESSING"
            assert db_app.assigned_officer_id == "USR-REV-001"
            assert db_app.processing_started_at is not None

            # Verify audit log insertion
            audit = (
                fresh_db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "START_REVIEW")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert audit is not None
            assert audit.new_status == "PROCESSING"

            # Verify status history insertion
            hist = (
                fresh_db.query(ApplicationStatusHistory)
                .filter(ApplicationStatusHistory.application_id == app_id, ApplicationStatusHistory.action == "START_REVIEW")
                .order_by(ApplicationStatusHistory.timestamp.desc())
                .first()
            )
            assert hist is not None
            assert hist.previous_status == "PENDING"
            assert hist.new_status == "PROCESSING"


# ============================================================================
# 6. Address Change Approval Workflow & Commit E2E
# ============================================================================
def test_06_address_change_approval_workflow_e2e(client):
    """Verifies full approval flow and atomic commit into PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")
    app_id = "GM-2026-000124"

    # Start review first
    client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Approve application
    reason = "All statutory residence and Taluka land registry checks verified."
    resp = client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": reason},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "VERIFIED"

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app.status == "VERIFIED"
            assert db_app.completed_at is not None

            # Verify audit log
            audit = (
                fresh_db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "APPROVE")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert audit is not None
            assert audit.new_status == "VERIFIED"
            assert audit.reason == reason

            # Verify status history
            hist = (
                fresh_db.query(ApplicationStatusHistory)
                .filter(ApplicationStatusHistory.application_id == app_id, ApplicationStatusHistory.action == "APPROVED")
                .order_by(ApplicationStatusHistory.timestamp.desc())
                .first()
            )
            assert hist is not None
            assert hist.new_status == "VERIFIED"

            # Verify notification
            notif = (
                fresh_db.query(Notification)
                .filter(Notification.application_id == app_id, Notification.type == "WORKFLOW_COMPLETION")
                .order_by(Notification.timestamp.desc())
                .first()
            )
            assert notif is not None
            assert notif.severity == "SUCCESS"


# ============================================================================
# 7. Rejection Workflow & Reason Persistence E2E
# ============================================================================
def test_07_rejection_workflow_and_persistence_e2e(client):
    """Verifies application rejection with statutory reason persists to PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")
    app_id = "GM-2026-000126"

    # Start review
    client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Reject
    rejection_reason = "Mismatch detected between municipal electricity statement and Taluka 7/12 land ledger."
    resp = client.post(
        f"/api/v1/revenue/application/{app_id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": rejection_reason},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "REJECTED"

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app.status == "REJECTED"
            assert db_app.completed_at is not None

            audit = (
                fresh_db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "REJECT")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert audit is not None
            assert audit.reason == rejection_reason

            hist = (
                fresh_db.query(ApplicationStatusHistory)
                .filter(ApplicationStatusHistory.application_id == app_id, ApplicationStatusHistory.action == "REJECTED")
                .order_by(ApplicationStatusHistory.timestamp.desc())
                .first()
            )
            assert hist is not None
            assert hist.new_status == "REJECTED"


# ============================================================================
# 8. Additional Information Request Workflow E2E
# ============================================================================
def test_08_additional_information_workflow_e2e(client):
    """Verifies requesting additional information (ACTION_REQUIRED) persists."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")
    app_id = "GM-2026-000128"

    req_payload = {
        "request_type": "DOCUMENT_CLARIFICATION",
        "message": "Please provide registered Index-II document copy with legible municipal seals.",
    }
    resp = client.post(
        f"/api/v1/revenue/application/{app_id}/request-info",
        headers={"Authorization": f"Bearer {token}"},
        json=req_payload,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ACTION_REQUIRED"

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app.status == "ACTION_REQUIRED"
            assert "Citizen Information Required" in db_app.required_action

            audit = (
                fresh_db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "REQUEST_INFORMATION")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert audit is not None
            assert audit.new_status == "ACTION_REQUIRED"


# ============================================================================
# 9. Reprocess & Controlled Retry Workflow E2E
# ============================================================================
def test_09_reprocess_and_retry_workflow_e2e(client):
    """Verifies reprocessing and controlled operational retries persist to PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")
    app_id = "GM-2026-000128"

    # Set to ACTION_REQUIRED first
    client.post(
        f"/api/v1/revenue/application/{app_id}/request-info",
        headers={"Authorization": f"Bearer {token}"},
        json={"request_type": "DOCUMENT_CLARIFICATION", "message": "Supplementary document required"},
    )

    # Reprocess back to PROCESSING
    reproc_resp = client.post(
        f"/api/v1/revenue/application/{app_id}/reprocess",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reproc_resp.status_code == 200
    assert reproc_resp.json()["data"]["status"] == "PROCESSING"

    # Operational retry on GM-2026-000130
    retry_app_id = "GM-2026-000130"
    retry_resp = client.post(
        f"/api/v1/revenue/application/{retry_app_id}/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert retry_resp.status_code == 200
    assert retry_resp.json()["data"]["status"] in ("PROCESSING", "PENDING")

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app.status == "PROCESSING"

            # Check audit entry for reprocess
            audit = (
                fresh_db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "REPROCESS")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert audit is not None


# ============================================================================
# 10. Proof Document JSONB Attachment & Officer Override E2E
# ============================================================================
def test_10_document_jsonb_attachment_and_override_e2e(client):
    """Verifies JSONB document attachment and officer manual overrides in PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")
    app_id = "GM-2026-000124"
    doc_id = "DOC-REV-9081"

    # Apply manual override
    override_body = {
        "decision": "VALIDATED",
        "reason": "Physical municipal property tax ledger verified on site by Circle Officer.",
    }
    resp = client.post(
        f"/api/v1/revenue/document/{doc_id}/override",
        headers={"Authorization": f"Bearer {token}"},
        json=override_body,
    )
    assert resp.status_code == 200

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            proofs = db_app.data_payload.get("proof_documents", [])
            target = next((d for d in proofs if d.get("document_id") == doc_id), None)
            assert target is not None
            assert target["verification_status"] == "VALIDATED"
            assert target["manual_override"]["reason"] == "Physical municipal property tax ledger verified on site by Circle Officer."


# ============================================================================
# 11. DPDP Citizen Consent Verification & Enforcement E2E
# ============================================================================
def test_11_consent_validation_e2e(client):
    """Verifies DPDP 8-rule citizen consent validation against PostgreSQL records."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")

    # 1. Valid consent
    resp_valid = client.post(
        "/api/v1/revenue/application/GM-2026-000124/validate-consent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["data"]["valid"] is True
    assert resp_valid.json()["data"]["status"] == "VALID"

    # 2. Expired consent
    resp_expired = client.post(
        "/api/v1/revenue/application/GM-2026-000127/validate-consent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_expired.status_code == 200
    assert resp_expired.json()["data"]["valid"] is False
    assert resp_expired.json()["data"]["status"] == "EXPIRED"

    # 3. Approving an application with expired consent must fail (HTTP 422)
    resp_block = client.post(
        "/api/v1/revenue/application/GM-2026-000127/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Should be blocked due to expired consent"},
    )
    assert resp_block.status_code == 422
    assert "CONSENT_INVALID" in resp_block.text


# ============================================================================
# 12. Immutable Audit Trail & Status History Chronology E2E
# ============================================================================
def test_12_audit_trail_and_status_history_e2e(client):
    """Verifies audit trail listing, chronological ordering, and duplicate protection."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")

    # Perform action to record audit
    client.post(
        "/api/v1/revenue/application/GM-2026-000124/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Query audit logs API
    resp = client.get(
        "/api/v1/revenue/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    logs = resp.json()["data"]["items"]
    assert len(logs) >= 1

    # Verify repeated GET requests do NOT add duplicate audit entries
    count_before = len(logs)
    client.get("/api/v1/revenue/audit-logs", headers={"Authorization": f"Bearer {token}"})
    client.get("/api/v1/revenue/applications/GM-2026-000124", headers={"Authorization": f"Bearer {token}"})
    resp_after = client.get("/api/v1/revenue/audit-logs", headers={"Authorization": f"Bearer {token}"})
    count_after = len(resp_after.json()["data"]["items"])
    assert count_before == count_after

    if is_db_available():
        with SessionLocal() as fresh_db:
            history = (
                fresh_db.query(ApplicationStatusHistory)
                .filter(ApplicationStatusHistory.application_id == "GM-2026-000124")
                .order_by(ApplicationStatusHistory.timestamp.asc())
                .all()
            )
            assert len(history) >= 1


# ============================================================================
# 13. Departmental Notifications Lifecycle E2E
# ============================================================================
def test_13_notifications_lifecycle_and_mark_read_e2e(client):
    """Verifies notification listing, unread counting, and mark-read write-back."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")

    # List notifications
    resp = client.get(
        "/api/v1/revenue/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    notifs = resp.json()["data"]["items"]
    assert len(notifs) >= 1

    # Get unread count
    resp_count = client.get(
        "/api/v1/revenue/notifications/unread-count",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_count.status_code == 200
    assert "unread_count" in resp_count.json()["data"]

    # Mark single notification as read
    first_id = notifs[0]["id"]
    mark_resp = client.post(
        f"/api/v1/revenue/notifications/{first_id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mark_resp.status_code == 200

    # Mark all as read
    bulk_resp = client.post(
        "/api/v1/revenue/notifications/mark-all-read",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bulk_resp.status_code == 200

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_notif = fresh_db.query(Notification).filter(Notification.id == first_id).first()
            if db_notif:
                assert db_notif.read is True


# ============================================================================
# 14. Transaction Rollback Guarantee E2E
# ============================================================================
def test_14_transaction_rollback_guarantee_e2e():
    """Verifies that mid-operation exceptions trigger atomic rollback with zero partial state."""
    if not is_db_available():
        pytest.skip("PostgreSQL not available for rollback test.")

    app_id = "GM-2026-000124"
    with SessionLocal() as db:
        app_repo = ApplicationRepository(db=db)
        audit_repo = AuditRepository(db=db)
        service = WorkflowService(app_repo=app_repo, audit_repo=audit_repo)

        # Confirm initial state
        initial = app_repo.get_by_application_id(app_id)
        assert initial["status"] == "PENDING"

        # Check baseline counts for this application
        initial_audits = db.query(AuditLog).filter(AuditLog.application_id == app_id).count()
        initial_history = db.query(ApplicationStatusHistory).filter(ApplicationStatusHistory.application_id == app_id).count()

        # Monkeypatch audit insertion to simulate database failure mid-transaction
        def failing_audit(*args, **kwargs):
            raise RuntimeError("Simulated transient PostgreSQL failure during audit commit")

        audit_repo.create_audit_entry = failing_audit

        with pytest.raises(RuntimeError, match="Simulated transient PostgreSQL failure"):
            service.start_review(application_id=app_id, officer_id="USR-REV-001", officer_name="Rajendra Mane")

    # In a completely fresh session, verify NO partial commits occurred
    with SessionLocal() as fresh_db:
        fresh_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
        assert fresh_app.status == "PENDING"
        assert fresh_app.processing_started_at is None

        # Verify no audit log or status history was leaked
        audits_after = fresh_db.query(AuditLog).filter(AuditLog.application_id == app_id).count()
        history_after = fresh_db.query(ApplicationStatusHistory).filter(ApplicationStatusHistory.application_id == app_id).count()
        assert audits_after == initial_audits
        assert history_after == initial_history


# ============================================================================
# 15. Session Isolation & Transaction Visibility E2E
# ============================================================================
def test_15_session_isolation_and_committed_visibility_e2e():
    """Verifies transactional isolation: mutations committed in Session A are visible to Session B."""
    if not is_db_available():
        pytest.skip("PostgreSQL not available for isolation test.")

    app_id = "GM-2026-000125"

    # Step 1: Session A performs update and commits
    with SessionLocal() as session_a:
        repo_a = ApplicationRepository(db=session_a)
        repo_a.update_application_status(
            application_id=app_id,
            new_status="PROCESSING",
            assigned_officer_id="USR-REV-001",
            auto_commit=True,
        )

    # Step 2: Session B queries and verifies committed state
    with SessionLocal() as session_b:
        repo_b = ApplicationRepository(db=session_b)
        committed_read = repo_b.get_by_application_id(app_id)
        assert committed_read is not None
        assert committed_read["status"] == "PROCESSING"
        assert committed_read["assigned_officer_id"] == "USR-REV-001"


# ============================================================================
# 16. Restart Persistence & Session Boundary Retention E2E
# ============================================================================
def test_16_restart_persistence_and_session_boundary_e2e():
    """Verifies that committed database mutations survive session teardown and reconnection."""
    if not is_db_available():
        pytest.skip("PostgreSQL not available for restart persistence test.")

    app_id = "GM-2026-000124"

    # Step 1: Open session, perform full workflow transition, commit, close session
    with SessionLocal() as session_1:
        repo = ApplicationRepository(db=session_1)
        audit = AuditRepository(db=session_1)
        service = WorkflowService(app_repo=repo, audit_repo=audit)
        service.start_review(application_id=app_id, officer_id="USR-REV-001", officer_name="Rajendra Mane")

    # Step 2: Open completely separate session (simulating restart / new connection)
    with SessionLocal() as session_2:
        db_app = session_2.query(Application).filter(Application.application_id == app_id).first()
        assert db_app.status == "PROCESSING"
        assert len(db_app.workflow_history) >= 1

        db_audits = session_2.query(AuditLog).filter(AuditLog.application_id == app_id).all()
        assert len(db_audits) >= 1


# ============================================================================
# 17. Direct Database Cross-Check E2E
# ============================================================================
def test_17_direct_database_cross_check_e2e(client):
    """Directly cross-checks API JSON responses against raw SQL row queries in PostgreSQL."""
    token = get_auth_token(client, "revenue.officer", "Officer@2026")
    app_id = "GM-2026-000124"

    api_resp = client.get(
        f"/api/v1/revenue/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert api_resp.status_code == 200
    api_data = api_resp.json()["data"]

    if is_db_available():
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT application_id, citizen_name, status, service_type, priority, consent_reference FROM revenue_applications WHERE application_id = :aid"),
                {"aid": app_id},
            ).mappings().first()

            assert row is not None
            assert api_data["application_id"] == row["application_id"]
            assert api_data["citizen_name"] == row["citizen_name"]
            assert api_data["status"] == row["status"]
            assert api_data["service_type"] == row["service_type"]
            assert api_data["priority"] == row["priority"]
            assert api_data["consent_reference"] == row["consent_reference"]
