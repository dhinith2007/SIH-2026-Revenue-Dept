"""
Phase 08 - Step 05: Repository Write-backs & Persistence Hardening Tests

Validates:
1. Status write-back persists to PostgreSQL database.
2. Audit record write-back persists to revenue_audit_logs.
3. Status history write-back persists to application_status_history.
4. Application approval write-back persists across fresh DB sessions.
5. Application rejection write-back persists across fresh DB sessions.
6. Notifications write-back persists to notifications table.
7. Atomic workflow transaction rollback on mid-operation exception.
8. Session isolation and committed visibility.
9. Persistent state retention after session closing / restart.
10. Document attachment JSONB write-back persists to database.
11. Document override JSONB write-back persists to database.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, is_db_available
from app.db.seed import seed_database
from app.models.application import Application
from app.models.audit import AuditLog, ApplicationStatusHistory
from app.models.notification import Notification
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.workflow_service import WorkflowService


@pytest.fixture(autouse=True)
def reset_db_state():
    """Restores baseline demo seed before each test."""
    if is_db_available():
        with SessionLocal() as db:
            seed_database(db=db, refresh_apps=True)
    yield


def get_officer_token(client) -> str:
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    return login_resp.json()["access_token"]


def test_01_status_write_back_persists_to_db(client):
    """Test 1: Starting review persists PROCESSING status to PostgreSQL table."""
    token = get_officer_token(client)
    app_id = "GM-2026-000124"

    response = client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PROCESSING"

    if is_db_available():
        with SessionLocal() as db:
            db_app = db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app is not None
            assert db_app.status == "PROCESSING"
            assert db_app.assigned_officer_id is not None
            assert db_app.processing_started_at is not None


def test_02_audit_log_write_back_persists_to_db(client):
    """Test 2: Workflow action inserts row in revenue_audit_logs table."""
    token = get_officer_token(client)
    app_id = "GM-2026-000124"

    client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )

    if is_db_available():
        with SessionLocal() as db:
            audit = (
                db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "START_REVIEW")
                .first()
            )
            assert audit is not None
            assert audit.new_status == "PROCESSING"
            assert audit.officer_id is not None


def test_03_status_history_write_back_persists_to_db(client):
    """Test 3: Status transition records row in application_status_history table."""
    token = get_officer_token(client)
    app_id = "GM-2026-000124"

    client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )

    if is_db_available():
        with SessionLocal() as db:
            hist = (
                db.query(ApplicationStatusHistory)
                .filter(ApplicationStatusHistory.application_id == app_id, ApplicationStatusHistory.new_status == "PROCESSING")
                .first()
            )
            assert hist is not None
            assert hist.action == "START_REVIEW"
            assert hist.previous_status == "PENDING"


def test_04_approve_write_back_persists_to_db(client):
    """Test 4: Approving application commits VERIFIED status to database."""
    token = get_officer_token(client)
    app_id = "GM-2026-000124"

    # Start review first
    client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Approve
    response = client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "All statutory proof checks verified successfully."},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "VERIFIED"

    if is_db_available():
        with SessionLocal() as db:
            db_app = db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app is not None
            assert db_app.status == "VERIFIED"
            assert db_app.completed_at is not None

            audit = (
                db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "APPROVE")
                .first()
            )
            assert audit is not None
            assert audit.new_status == "VERIFIED"


def test_05_reject_write_back_persists_to_db(client):
    """Test 5: Rejecting application commits REJECTED status to database."""
    token = get_officer_token(client)
    app_id = "GM-2026-000126"

    # Start review
    client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Reject
    response = client.post(
        f"/api/v1/revenue/application/{app_id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Discrepancy detected in revenue land title documentation."},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "REJECTED"

    if is_db_available():
        with SessionLocal() as db:
            db_app = db.query(Application).filter(Application.application_id == app_id).first()
            assert db_app is not None
            assert db_app.status == "REJECTED"

            audit = (
                db.query(AuditLog)
                .filter(AuditLog.application_id == app_id, AuditLog.action == "REJECT")
                .first()
            )
            assert audit is not None
            assert audit.new_status == "REJECTED"


def test_06_notification_write_back_persists_to_db(client):
    """Test 6: Notification write-back persists to notifications table."""
    token = get_officer_token(client)
    app_id = "GM-2026-000124"

    client.post(
        f"/api/v1/revenue/application/{app_id}/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Statutory verification complete."},
    )

    if is_db_available():
        with SessionLocal() as db:
            notif = (
                db.query(Notification)
                .filter(Notification.application_id == app_id, Notification.type == "WORKFLOW_COMPLETION")
                .first()
            )
            assert notif is not None
            assert notif.severity == "SUCCESS"


def test_07_workflow_transaction_rollback_on_failure():
    """Test 7: Atomic rollback when mid-operation exception occurs in WorkflowService."""
    if not is_db_available():
        pytest.skip("PostgreSQL not available for rollback test.")

    with SessionLocal() as db:
        app_repo = ApplicationRepository(db=db)
        audit_repo = AuditRepository(db=db)
        notif_repo = NotificationRepository(db=db)
        service = WorkflowService(app_repo=app_repo, audit_repo=audit_repo, notif_repo=notif_repo)

        app_id = "GM-2026-000124"
        initial_app = app_repo.get_by_application_id(app_id)
        assert initial_app["status"] == "PENDING"

        # Monkeypatch create_audit_entry on audit_repo to simulate mid-workflow failure
        def failing_audit_entry(*args, **kwargs):
            raise RuntimeError("Simulated mid-transaction failure during audit log insertion")

        audit_repo.create_audit_entry = failing_audit_entry

        with pytest.raises(RuntimeError, match="Simulated mid-transaction failure"):
            service.start_review(application_id=app_id, officer_id="REV-OFF-9999", officer_name="Officer Test")

    # In a brand new DB session, verify state was NOT committed
    with SessionLocal() as fresh_db:
        fresh_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
        assert fresh_app.status == "PENDING"
        assert fresh_app.processing_started_at is None


def test_08_session_isolation_and_committed_visibility():
    """Test 8: Data mutated in transaction is visible to fresh session after commit."""
    if not is_db_available():
        pytest.skip("PostgreSQL not available for isolation test.")

    app_id = "GM-2026-000128"

    # Session A: Mutate and commit
    with SessionLocal() as session_a:
        repo_a = ApplicationRepository(db=session_a)
        repo_a.update_application_status(
            application_id=app_id,
            new_status="PROCESSING",
            assigned_officer_id="REV-OFF-1001",
            auto_commit=True,
        )

    # Session B: Independent session should immediately read the committed status
    with SessionLocal() as session_b:
        repo_b = ApplicationRepository(db=session_b)
        fetched = repo_b.get_by_application_id(app_id)
        assert fetched is not None
        assert fetched["status"] == "PROCESSING"
        assert fetched["assigned_officer_id"] == "REV-OFF-1001"


def test_09_restart_persistence_retention():
    """Test 9: Database state remains preserved across session closes and reopens."""
    if not is_db_available():
        pytest.skip("PostgreSQL not available for persistence test.")

    app_id = "GM-2026-000124"

    with SessionLocal() as session:
        repo = ApplicationRepository(db=session)
        audit = AuditRepository(db=session)
        service = WorkflowService(app_repo=repo, audit_repo=audit)
        service.start_review(application_id=app_id, officer_id="REV-OFF-4412", officer_name="Sanjay Shinde")

    # Reconnect fresh session
    with SessionLocal() as new_session:
        db_app = new_session.query(Application).filter(Application.application_id == app_id).first()
        assert db_app.status == "PROCESSING"
        assert len(db_app.workflow_history) >= 1

        db_audit = new_session.query(AuditLog).filter(AuditLog.application_id == app_id).all()
        assert len(db_audit) >= 1


def test_10_document_attachment_jsonb_write_back(client):
    """Test 10: Attaching document updates JSONB payload in PostgreSQL."""
    app_id = "GM-2026-000124"
    doc_payload = {
        "document_id": "DOC-TEST-9988",
        "document_type": "ELECTRICITY_BILL",
        "file_name": "electricity_nov_2026.pdf",
        "mime_type": "application/pdf",
        "file_size_kb": 245,
        "verification_status": "VALIDATED",
        "extracted_name": "Smt. Sunita Rao",
        "extracted_address": "Plot 42, Viman Nagar, Pune 411014",
    }

    if is_db_available():
        with SessionLocal() as db:
            repo = ApplicationRepository(db=db)
            repo.attach_document(app_id, doc_payload)

        # Verify from fresh session
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            proofs = db_app.data_payload.get("proof_documents", [])
            matched = [d for d in proofs if d.get("document_id") == "DOC-TEST-9988"]
            assert len(matched) == 1
            assert matched[0]["document_type"] == "ELECTRICITY_BILL"


def test_11_document_override_jsonb_write_back(client):
    """Test 11: Overriding document updates JSONB manual_override metadata in PostgreSQL."""
    app_id = "GM-2026-000124"
    doc_id = "DOC-REV-9081"

    token = get_officer_token(client)
    override_body = {
        "decision": "VALIDATED",
        "reason": "Physical municipal tax receipt verified against Taluka municipal ledger.",
    }

    response = client.post(
        f"/api/v1/revenue/document/{doc_id}/override",
        headers={"Authorization": f"Bearer {token}"},
        json=override_body,
    )
    assert response.status_code == 200

    if is_db_available():
        with SessionLocal() as fresh_db:
            db_app = fresh_db.query(Application).filter(Application.application_id == app_id).first()
            proofs = db_app.data_payload.get("proof_documents", [])
            target = next((d for d in proofs if d.get("document_id") == doc_id), None)
            assert target is not None
            assert target["verification_status"] == "VALIDATED"
            assert target["manual_override"]["reason"] == "Physical municipal tax receipt verified against Taluka municipal ledger."
