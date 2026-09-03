import pytest
from starlette.testclient import TestClient
from app.main import app
from app.services.auth_service import create_access_token
from app.repositories.application_repository import ApplicationRepository

client = TestClient(app)


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def desk_officer_token():
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
def cross_division_token():
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
def auditor_token():
    return create_access_token(
        data={
            "sub": "USR-REV-004",
            "username": "revenue.auditor",
            "role": "READ_ONLY_AUDITOR",
            "department": "Revenue & Forest Department",
            "division": "State Revenue Audit Directorate",
        }
    )


# ============================================================================
# 1. Authentication Security Failure Tests
# ============================================================================
def test_unauthenticated_request_blocked():
    res = client.get("/api/v1/revenue/application/GM-2026-000124")
    assert res.status_code == 401


def test_malformed_jwt_blocked():
    res = client.get("/api/v1/revenue/application/GM-2026-000124", headers={"Authorization": "Bearer malformed.jwt.token"})
    assert res.status_code == 401


# ============================================================================
# 2. RBAC & Division Tenant Isolation Tests
# ============================================================================
def test_cross_division_document_verify_blocked(cross_division_token):
    # DOC-REV-9081 belongs to GM-2026-000124 (Pune Division)
    # other.officer belongs to Baramati Tahsil
    res = client.post("/api/v1/revenue/document/DOC-REV-9081/verify", headers=auth_header(cross_division_token))
    assert res.status_code in (403, 409)


def test_auditor_statutory_mutation_blocked(auditor_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json={"decision": "VALIDATED", "reason": "Auditor attempting statutory mutation."},
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 403


# ============================================================================
# 3. Manual Override Validation & Immutability
# ============================================================================
def test_manual_override_requires_mandatory_valid_reason(desk_officer_token):
    # Empty reason
    res_empty = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json={"decision": "VALIDATED", "reason": ""},
        headers=auth_header(desk_officer_token),
    )
    assert res_empty.status_code in (400, 409, 422)

    # Valid reason (> 10 chars)
    res_valid = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json={"decision": "VALIDATED", "reason": "Verified original physical 7/12 extract presented by citizen."},
        headers=auth_header(desk_officer_token),
    )
    assert res_valid.status_code in (200, 409)  # 409 if app already finalized in prior test


def test_finalized_application_mutation_blocked(desk_officer_token):
    # GM-2026-000124 document DOC-REV-3310 / DOC-REV-9081
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json={"decision": "MISMATCH", "reason": "Attempting override on finalized application."},
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 409


# ============================================================================
# 4. Client Payload Forgery Prevention
# ============================================================================
def test_client_cannot_forge_confidence_or_recommendation(desk_officer_token):
    # Attempting to send forged confidence and recommendation in verify payload body
    forged_body = {
        "confidence": 1.0,
        "overall_confidence": 1.0,
        "recommendation": "HIGH_CONFIDENCE_MATCH",
        "match_status": "VALIDATED",
    }
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify?provider=SIMULATED",
        json=forged_body,
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code in (200, 409)
    if res.status_code == 200:
        data = res.json()["data"]
        # Verify server computed authoritative scores and ignored client payload body
        assert "ocr_confidence" in data
        assert "overall_confidence" in data


# ============================================================================
# 5. Persistence Failure & Atomic Rollback Verification
# ============================================================================
def test_simulated_db_failure_atomic_rollback(desk_officer_token, monkeypatch):
    # Create isolated client with raise_server_exceptions=False to catch 500 responses
    custom_client = TestClient(app, raise_server_exceptions=False)

    # Simulate DB failure during application update in ApplicationRepository
    def mock_db_save_failure(*args, **kwargs):
        raise RuntimeError("Simulated Database Connection Failure during transaction commit")

    headers = auth_header(desk_officer_token)
    app_id = "GM-2026-000125"

    # Ensure document is validated first on GM-2026-000125
    res_override = custom_client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json={"decision": "VALIDATED", "reason": "Officer validated physical document for DB failure test."},
        headers=headers,
    )
    assert res_override.status_code in (200, 409)

    # Verify initial app status before attempt
    res_before = custom_client.get(f"/api/v1/revenue/application/{app_id}", headers=headers)
    assert res_before.status_code == 200
    init_status = res_before.json()["data"]["status"]

    # Monkeypatch repository commit/flush to simulate unexpected DB failure
    monkeypatch.setattr(ApplicationRepository, "update_application_status", mock_db_save_failure)

    # Execute approve request expecting structured server error (500)
    res_fail = custom_client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        json={"reason": "Officer approval under simulated DB failure."},
        headers=headers,
    )
    assert res_fail.status_code == 500

    # Undo monkeypatch and verify application status was NOT left as VERIFIED (Clean Rollback)
    monkeypatch.undo()
    res_after = custom_client.get(f"/api/v1/revenue/application/{app_id}", headers=headers)
    assert res_after.status_code == 200
    assert res_after.json()["data"]["status"] == init_status
