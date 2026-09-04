def get_officer_token(client) -> str:
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    return login_resp.json()["access_token"]


def get_auditor_token(client) -> str:
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.auditor", "password": "Auditor@2026"},
    )
    return login_resp.json()["access_token"]


# ============================================================================
# 1. Consent Validation Tests (Tests 01 - 06)
# ============================================================================
def test_consent_validation_valid(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/validate-consent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is True
    assert data["status"] == "VALID"
    assert data["rules_evaluated"]["rule_1_reference_exists"] == "PASSED"
    assert data["rules_evaluated"]["rule_4_not_expired"] == "PASSED"


def test_consent_validation_expired(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000127/validate-consent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is False
    assert data["status"] == "EXPIRED"
    assert len(data["errors"]) >= 1


# ============================================================================
# 2. Data Validation Tests (Tests 07 - 11)
# ============================================================================
def test_data_validation_complete_address_passes(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/validate-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is True
    assert data["checks"]["address_completeness"] == "PASSED"
    assert data["checks"]["required_fields"] == "PASSED"


def test_data_validation_incomplete_address_fails(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000130/validate-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is False
    assert data["checks"]["address_completeness"] == "FAILED"
    assert any("taluka" in err.lower() or "village" in err.lower() for err in data["errors"])


# ============================================================================
# 3. Document Verification Tests (Tests 12 - 15)
# ============================================================================
def test_document_verification_validated(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/verify-document",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is True
    assert data["match_status"] == "VALIDATED"
    assert data["name_match"] == "MATCH"
    assert data["is_simulated_ocr"] is True


def test_document_verification_missing_document(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000128/verify-document",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is False
    assert data["match_status"] == "MISSING"


def test_document_verification_mismatched_address(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000129/verify-document",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is False
    assert data["match_status"] == "MISMATCH"


# ============================================================================
# 4. Officer Review & Decision Tests (Tests 16 - 25)
# ============================================================================
def test_start_review_transitions_to_processing(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/start-review",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "PROCESSING"
    assert data["action"] == "START_REVIEW"


def test_approve_valid_application_success(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/approve",
        json={"reason": "Address proof matches the requested new address and 7/12 land registry."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "VERIFIED"
    assert data["action"] == "APPROVED"
    assert data["department"] == "REVENUE"


def test_approve_with_expired_consent_blocked(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000127/approve",
        json={"reason": "Attempting approval on expired consent"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CONSENT_INVALID"


def test_reject_with_reason_success(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000129/reject",
        json={"reason": "Submitted address proof does not match requested address."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "REJECTED"
    assert data["action"] == "REJECTED"


def test_reject_without_reason_returns_422(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000125/reject",
        json={"reason": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_request_information_transitions_to_action_required(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000128/request-info",
        json={
            "request_type": "NEW_DOCUMENT",
            "message": "Please provide a valid utility bill for the new address.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ACTION_REQUIRED"
    assert data["action"] == "INFORMATION_REQUESTED"


def test_reprocess_application_transitions_to_processing(client):
    token = get_officer_token(client)
    # Transition to ACTION_REQUIRED first
    client.post(
        "/api/v1/revenue/application/GM-2026-000128/request-info",
        json={
            "request_type": "NEW_DOCUMENT",
            "message": "Please provide a valid utility bill for the new address.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000128/reprocess",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "PROCESSING"
    assert data["action"] == "REPROCESSED"


def test_cannot_approve_already_finalized_application(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000131/approve",
        json={"reason": "Attempting duplicate approval"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


def test_unauthenticated_approve_returns_401(client):
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/approve",
        json={"reason": "No auth header"},
    )
    assert response.status_code == 401


def test_auditor_cannot_approve_returns_403(client):
    token = get_auditor_token(client)
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/approve",
        json={"reason": "Auditor attempting approval"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


# ============================================================================
# 5. Address Verification Probe & Audit Log Tests (Tests 26 - 28)
# ============================================================================
def test_address_verify_probe_endpoint(client):
    token = get_officer_token(client)
    response = client.post(
        "/api/v1/revenue/address/verify",
        json={"application_id": "GM-2026-000124"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["applicationId"] == "GM-2026-000124"
    assert data["department"] == "REVENUE"
    assert data["validation"]["consent"] == "VALID"
    assert data["validation"]["data"] == "VALID"
    assert data["validation"]["document"] == "VALIDATED"


def test_audit_logs_retrieval(client):
    token = get_officer_token(client)
    response = client.get(
        "/api/v1/revenue/audit-logs?page=1&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert any(it["action"] in ("APPROVE", "REJECT", "START_REVIEW", "REQUEST_INFORMATION") for it in data["items"])
