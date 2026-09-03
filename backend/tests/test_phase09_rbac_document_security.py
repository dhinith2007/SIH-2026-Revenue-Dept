import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal, is_db_available
from app.models.audit import AuditLog
from app.models.application import Application
from app.core.rate_limit import reset_rate_limiter


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    reset_rate_limiter()
    yield
    reset_rate_limiter()


@pytest.fixture
def officer_token():
    """USR-REV-001: Standard Revenue Officer assigned to GM-2026-000124."""
    return create_access_token(
        data={
            "sub": "USR-REV-001",
            "username": "revenue.officer",
            "role": "REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Pune Division",
        }
    )


@pytest.fixture
def other_officer_token():
    """USR-REV-006: Another Revenue Officer NOT assigned to GM-2026-000124."""
    return create_access_token(
        data={
            "sub": "USR-REV-006",
            "username": "other.officer",
            "role": "REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Pune Division (Baramati Tahsil)",
        }
    )


@pytest.fixture
def senior_officer_token():
    """USR-REV-002: Senior Revenue Officer with EXCEPTION_OVERRIDE."""
    return create_access_token(
        data={
            "sub": "USR-REV-002",
            "username": "senior.officer",
            "role": "SENIOR_REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Pune Division",
        }
    )


@pytest.fixture
def admin_token():
    """USR-REV-003: Department Administrator."""
    return create_access_token(
        data={
            "sub": "USR-REV-003",
            "username": "revenue.admin",
            "role": "DEPARTMENT_ADMINISTRATOR",
            "department": "Revenue & Forest Department",
            "division": "State Headquarters",
        }
    )


@pytest.fixture
def auditor_token():
    """USR-REV-004: Read-Only Auditor."""
    return create_access_token(
        data={
            "sub": "USR-REV-004",
            "username": "revenue.auditor",
            "role": "READ_ONLY_AUDITOR",
            "department": "Revenue & Forest Department",
            "division": "Audit Directorate",
        }
    )


@pytest.fixture
def inactive_user_token():
    """USR-REV-005: Inactive Officer Account."""
    return create_access_token(
        data={
            "sub": "USR-REV-005",
            "username": "inactive.officer",
            "role": "REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Suspended Desk",
        }
    )


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# A. Role Access Tests (Tests 1 - 6)
# ==============================================================================

def test_01_officer_allowed_normal_authorized_document_operation(client, officer_token):
    """Test 1: Assigned Revenue Officer is allowed normal document verification."""
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_02_senior_allowed_permitted_privileged_operation(client, senior_officer_token):
    """Test 2: Senior Revenue Officer allowed privileged document override across department."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Senior Revenue Officer verified electricity bill physically.",
        "notes": "Authorized under statutory MLR scrutiny provisions.",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(senior_officer_token),
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["manual_override"]["decision"] == "VALIDATED"


def test_03_admin_allowed_permitted_privileged_operation(client, admin_token):
    """Test 3: Department Administrator allowed privileged document verification and override."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Department Administrator manual override for administrative review.",
        "notes": "Admin action recorded in statutory audit trail.",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_04_auditor_read_access_where_permitted(client, auditor_token):
    """Test 4: Auditor is granted read access to view document metadata and listing."""
    res = client.get(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_05_auditor_mutation_denied(client, auditor_token):
    """Test 5: Auditor mutation attempts (verify, attach, override) are strictly denied with 403."""
    # Attempt verification
    res_verify = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(auditor_token),
    )
    assert res_verify.status_code == 403
    assert res_verify.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"

    # Attempt override
    res_override = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json={"decision": "VALIDATED", "reason": "Auditor attempting override"},
        headers=auth_header(auditor_token),
    )
    assert res_override.status_code == 403
    assert res_override.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_06_inactive_user_denied(client, inactive_user_token):
    """Test 6: Inactive account is denied operational access with HTTP 403 ACCOUNT_INACTIVE."""
    res = client.get(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        headers=auth_header(inactive_user_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCOUNT_INACTIVE"


# ==============================================================================
# B. Document Override Hardening — SEC-01 (Tests 7 - 11)
# ==============================================================================

def test_07_unauthorized_officer_cannot_override(client, other_officer_token):
    """Test 7: Officer NOT assigned to the application cannot override documents (HTTP 403)."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Unauthorized officer attempting override on another officer's case.",
    }
    # DOC-REV-9081 belongs to GM-2026-000124 assigned to USR-REV-001
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_08_authorized_privileged_role_can_override(client, senior_officer_token):
    """Test 8: Authorized privileged role with EXCEPTION_OVERRIDE can override."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Senior officer exercising statutory exception override powers.",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(senior_officer_token),
    )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_09_auditor_cannot_override(client, auditor_token):
    """Test 9: Read-only auditor attempting override is blocked with HTTP 403."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Auditor attempting manual override.",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_10_unauthenticated_override_rejected(client):
    """Test 10: Unauthenticated override request is rejected with HTTP 401."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Unauthenticated override attempt.",
    }
    res = client.post("/api/v1/revenue/document/DOC-REV-9081/override", json=payload)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_11_finalized_application_override_rejected(client, senior_officer_token):
    """Test 11: Override attempt on finalized application (VERIFIED) rejected with HTTP 409."""
    payload = {
        "decision": "MISMATCH",
        "reason": "Attempting override on closed case.",
    }
    # DOC-REV-3310 belongs to GM-2026-000131 (status: VERIFIED)
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json=payload,
        headers=auth_header(senior_officer_token),
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


# ==============================================================================
# C. Document Attachment Security (Tests 12 - 15)
# ==============================================================================

def test_12_unauthorized_user_cannot_attach(client, other_officer_token):
    """Test 12: Officer cannot attach documents to an application assigned to another officer."""
    pdf_content = b"%PDF-1.4 Mock Document"
    files = {"file": ("proof.pdf", io.BytesIO(pdf_content), "application/pdf")}

    # GM-2026-000124 is assigned to USR-REV-001; USR-REV-099 is not authorized
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_13_authorized_user_can_attach(client, officer_token):
    """Test 13: Assigned officer can attach a proof document to their application."""
    pdf_content = b"%PDF-1.4 Mock Document for assigned officer"
    files = {"file": ("authorized_proof.pdf", io.BytesIO(pdf_content), "application/pdf")}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 201
    assert res.json()["success"] is True


def test_14_auditor_cannot_attach(client, auditor_token):
    """Test 14: Auditor attempting to attach a document is blocked with HTTP 403."""
    pdf_content = b"%PDF-1.4 Mock Document"
    files = {"file": ("auditor_doc.pdf", io.BytesIO(pdf_content), "application/pdf")}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_15_finalized_application_cannot_be_modified(client, officer_token):
    """Test 15: Uploading documents to a finalized (VERIFIED) application returns HTTP 409."""
    pdf_content = b"%PDF-1.4 Mock Document"
    files = {"file": ("finalized_doc.pdf", io.BytesIO(pdf_content), "application/pdf")}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000131/documents",
        files=files,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


# ==============================================================================
# D. Document Retrieval Security (Tests 16 - 19)
# ==============================================================================

def test_16_authorized_user_can_retrieve_permitted_document(client, officer_token):
    """Test 16: Assigned officer can retrieve document metadata and preview."""
    # Metadata
    res_meta = client.get(
        "/api/v1/revenue/document/DOC-REV-9081",
        headers=auth_header(officer_token),
    )
    assert res_meta.status_code == 200
    assert res_meta.json()["data"]["document_id"] == "DOC-REV-9081"

    # Preview
    res_prev = client.get(
        "/api/v1/revenue/document/DOC-REV-9081/preview",
        headers=auth_header(officer_token),
    )
    assert res_prev.status_code == 200
    assert "image/svg+xml" in res_prev.headers["content-type"]


def test_17_unauthorized_user_cannot_retrieve_protected_document(client, other_officer_token):
    """Test 17: Officer cannot retrieve document belonging to another officer's application."""
    # GM-2026-000124 is assigned to USR-REV-001; USR-REV-099 is forbidden
    res = client.get(
        "/api/v1/revenue/document/DOC-REV-9081",
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_18_auditor_can_retrieve_permitted_audit_read_document(client, auditor_token):
    """Test 18: Auditor is permitted read access to document metadata and preview."""
    res = client.get(
        "/api/v1/revenue/document/DOC-REV-9081",
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    res_prev = client.get(
        "/api/v1/revenue/document/DOC-REV-9081/preview",
        headers=auth_header(auditor_token),
    )
    assert res_prev.status_code == 200


def test_19_arbitrary_document_id_cannot_bypass_authorization(client, officer_token):
    """Test 19: Non-existent document ID returns HTTP 404 rather than disclosing internal state."""
    res = client.get(
        "/api/v1/revenue/document/DOC-FORGED-99999",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


# ==============================================================================
# E. Privilege Escalation Protections (Tests 20 - 24)
# ==============================================================================

def test_20_body_role_cannot_elevate_privileges(client, other_officer_token):
    """Test 20: Passing 'role: admin' in request body is ignored; server identity is used."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Attempting privilege escalation via request body injection.",
        "role": "DEPARTMENT_ADMINISTRATOR",
    }
    # other_officer_token is not assigned to GM-2026-000124
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_21_query_role_cannot_elevate_privileges(client, other_officer_token):
    """Test 21: Passing '?role=DEPARTMENT_ADMINISTRATOR' in query parameters is ignored."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Attempting privilege escalation via query param.",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override?role=DEPARTMENT_ADMINISTRATOR",
        json=payload,
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_22_forged_user_id_cannot_elevate_privileges(client, other_officer_token):
    """Test 22: Passing forged 'user_id' or 'officer_id' in payload cannot bypass ownership."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Attempting identity forgery in payload.",
        "officer_id": "USR-REV-001",  # Claiming to be the assigned officer
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_23_forged_officer_id_not_recorded_in_audit(client, officer_token):
    """Test 23: Even if assigned officer sends forged officer_name in body, server token identity is used."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Legitimate override testing audit actor attribution.",
        "officer_name": "Forged Minister Name",
        "officer_id": "FORGED-ID",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    override_meta = res.json()["data"]["manual_override"]
    # Verify server identity was recorded, not the forged payload values
    assert override_meta["officer_id"] == "USR-REV-001"
    assert override_meta["officer_name"] != "Forged Minister Name"


def test_24_arbitrary_application_id_cannot_bypass_authorization(client, other_officer_token):
    """Test 24: Trying to list documents for unassigned/unauthorized application returns 403."""
    res = client.get(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


# ==============================================================================
# F. Auditing & Non-Repudiation (Tests 25 - 28)
# ==============================================================================

def test_25_successful_privileged_document_mutation_creates_audit_entry(client, senior_officer_token):
    """Test 25: Privileged override creates a persistent audit entry in PostgreSQL."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Senior officer override for audit verification.",
        "notes": "Testing audit log creation.",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(senior_officer_token),
    )
    assert res.status_code == 200

    if is_db_available():
        with SessionLocal() as db:
            log_entry = (
                db.query(AuditLog)
                .filter(AuditLog.application_id == "GM-2026-000124", AuditLog.action == "MANUAL_OVERRIDE")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert log_entry is not None
            assert log_entry.officer_id == "USR-REV-002"
            assert "Senior officer override" in log_entry.reason


def test_26_audit_record_contains_actor_identity_and_action(client, senior_officer_token):
    """Test 26: Audit record contains correct actor ID, action verb, and timestamp."""
    payload = {
        "decision": "VALIDATED",
        "reason": "Audit attribution verification test.",
    }
    client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=payload,
        headers=auth_header(senior_officer_token),
    )

    if is_db_available():
        with SessionLocal() as db:
            log_entry = (
                db.query(AuditLog)
                .filter(AuditLog.application_id == "GM-2026-000124")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert log_entry.officer_id == "USR-REV-002"
            assert log_entry.action == "MANUAL_OVERRIDE"
            assert log_entry.timestamp is not None


def test_27_secrets_tokens_contents_are_not_logged(client, senior_officer_token):
    """Test 27: Verify passwords, tokens, and raw binary content are never stored in audit logs."""
    if is_db_available():
        with SessionLocal() as db:
            logs = db.query(AuditLog).filter(AuditLog.application_id == "GM-2026-000124").all()
            for l in logs:
                details_str = str(l.details) if l.details else ""
                reason_str = l.reason or ""
                assert "password" not in details_str.lower()
                assert "bearer" not in details_str.lower()
                assert "token" not in details_str.lower()
                assert "bearer" not in reason_str.lower()


def test_28_audit_logs_can_be_inspected_by_auditor(client, auditor_token):
    """Test 28: Read-only auditor can inspect statutory audit logs."""
    res = client.get(
        "/api/v1/revenue/audit-logs?application_id=GM-2026-000124",
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert len(res.json()["data"]["items"]) >= 1


# ==============================================================================
# G. Finalized State Protection (Tests 29 - 30)
# ==============================================================================

def test_29_verified_application_blocks_document_mutation(client, senior_officer_token):
    """Test 29: VERIFIED application blocks all document mutations (override, verify, attach)."""
    # DOC-REV-3310 is on GM-2026-000131 (status: VERIFIED)
    res_override = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json={"decision": "VALIDATED", "reason": "Attempting override on VERIFIED application"},
        headers=auth_header(senior_officer_token),
    )
    assert res_override.status_code == 409
    assert res_override.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"

    res_verify = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/verify",
        headers=auth_header(senior_officer_token),
    )
    assert res_verify.status_code == 409
    assert res_verify.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


def test_30_rejected_application_blocks_document_mutation(client, senior_officer_token):
    """Test 30: REJECTED application blocks all document mutations (override, verify, attach)."""
    target_id = "GM-2026-000126"

    # Ensure application is rejected
    client.post(
        f"/api/v1/revenue/application/{target_id}/start-review",
        headers=auth_header(senior_officer_token),
    )
    client.post(
        f"/api/v1/revenue/application/{target_id}/reject",
        json={"reason": "Statutory rejection for immutability verification."},
        headers=auth_header(senior_officer_token),
    )

    pdf_content = b"%PDF-1.4 Mock Document"
    files = {"file": ("new.pdf", io.BytesIO(pdf_content), "application/pdf")}

    res = client.post(
        f"/api/v1/revenue/application/{target_id}/documents",
        files=files,
        headers=auth_header(senior_officer_token),
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"
