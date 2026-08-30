import pytest
from app.core.simulation import set_runtime_failure_mode


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
# 1. Failure Simulation & Machine-Readable Error Contract Tests
# ============================================================================
def test_simulation_api_unavailable(client):
    token = get_officer_token(client)
    try:
        set_runtime_failure_mode("API_UNAVAILABLE")
        resp = client.get(
            "/api/v1/revenue/applications",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 503
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "correlationId" in body["error"]
    finally:
        set_runtime_failure_mode("NONE")


def test_simulation_timeout(client):
    token = get_officer_token(client)
    try:
        set_runtime_failure_mode("TIMEOUT")
        resp = client.get(
            "/api/v1/revenue/applications/GM-2026-000124",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 504
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "GATEWAY_TIMEOUT"
        assert body["error"]["correlationId"] == "CORR-2026-000124"
    finally:
        set_runtime_failure_mode("NONE")


def test_simulation_internal_error(client):
    token = get_officer_token(client)
    try:
        set_runtime_failure_mode("INTERNAL_ERROR")
        resp = client.post(
            "/api/v1/revenue/application/GM-2026-000124/start-review",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 500
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "correlationId" in body["error"]
    finally:
        set_runtime_failure_mode("NONE")


def test_per_request_header_simulation_override(client):
    token = get_officer_token(client)
    resp = client.get(
        "/api/v1/revenue/applications",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Simulate-Failure": "API_UNAVAILABLE",
        },
    )
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_simulation_mode_endpoint_get_and_set(client):
    token = get_officer_token(client)
    set_resp = client.post(
        "/api/v1/revenue/simulation/failure-mode",
        json={"mode": "TIMEOUT"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert set_resp.status_code == 200
    assert set_resp.json()["data"]["failure_mode"] == "TIMEOUT"

    get_resp = client.get(
        "/api/v1/revenue/simulation/failure-mode",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["failure_mode"] == "TIMEOUT"

    # Reset
    client.post(
        "/api/v1/revenue/simulation/failure-mode",
        json={"mode": "NONE"},
        headers={"Authorization": f"Bearer {token}"},
    )


# ============================================================================
# 2. Action-Required Queries & Categories
# ============================================================================
def test_request_info_all_categories(client):
    token = get_officer_token(client)
    categories = ["NEW_DOCUMENT", "CORRECT_ADDRESS", "MISSING_INFO", "CLARIFICATION"]
    for cat in categories:
        resp = client.post(
            "/api/v1/revenue/application/GM-2026-000128/request-info",
            json={
                "request_type": cat,
                "message": f"Detailed inquiry regarding {cat} verification.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "ACTION_REQUIRED"
        assert cat in data["requiredAction"]


def test_get_action_required_queue(client):
    token = get_officer_token(client)
    resp = client.get(
        "/api/v1/revenue/applications/action-required",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert all(it["status"] == "ACTION_REQUIRED" for it in data["items"])


# ============================================================================
# 3. Reprocess & Controlled Operational Retry
# ============================================================================
def test_reprocess_from_action_required_succeeds(client):
    token = get_officer_token(client)
    # Ensure it is in ACTION_REQUIRED
    client.post(
        "/api/v1/revenue/application/GM-2026-000128/request-info",
        json={"request_type": "NEW_DOCUMENT", "message": "Please upload bill."},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Reprocess
    resp = client.post(
        "/api/v1/revenue/application/GM-2026-000128/reprocess",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PROCESSING"


def test_cannot_reprocess_finalized_application(client):
    token = get_officer_token(client)
    resp = client.post(
        "/api/v1/revenue/application/GM-2026-000131/reprocess",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (400, 409)


def test_operational_retry_endpoint(client):
    token = get_officer_token(client)
    resp = client.post(
        "/api/v1/revenue/application/GM-2026-000135/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["applicationId"] == "GM-2026-000135"
    assert data["action"] == "RETRY_RECEIVED"


def test_retry_on_finalized_application_blocked(client):
    token = get_officer_token(client)
    resp = client.post(
        "/api/v1/revenue/application/GM-2026-000131/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


# ============================================================================
# 4. Departmental Notification Center
# ============================================================================
def test_list_notifications(client):
    token = get_officer_token(client)
    resp = client.get(
        "/api/v1/revenue/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert data["total"] >= 1
    assert data["unread_count"] >= 0


def test_get_unread_count(client):
    token = get_officer_token(client)
    resp = client.get(
        "/api/v1/revenue/notifications/unread-count",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "unread_count" in resp.json()["data"]


def test_mark_single_notification_as_read(client):
    token = get_officer_token(client)
    resp = client.post(
        "/api/v1/revenue/notifications/NOTIF-REV-001/read",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["read"] is True


def test_mark_all_notifications_as_read(client):
    token = get_officer_token(client)
    resp = client.post(
        "/api/v1/revenue/notifications/mark-all-read",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["marked_read_count"] >= 0


# ============================================================================
# 5. Completed & Rejected Applications Endpoints
# ============================================================================
def test_get_completed_applications_queue(client):
    token = get_officer_token(client)
    resp = client.get(
        "/api/v1/revenue/applications/completed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(it["status"] in ("VERIFIED", "COMPLETED") for it in data["items"])


def test_get_rejected_applications_queue(client):
    token = get_officer_token(client)
    # Reject GM-2026-000130
    client.post(
        "/api/v1/revenue/application/GM-2026-000130/reject",
        json={"reason": "Incomplete address verification failure."},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.get(
        "/api/v1/revenue/applications/rejected",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any(it["application_id"] == "GM-2026-000130" for it in data["items"])


# ============================================================================
# 6. RBAC & Security Enforcement
# ============================================================================
def test_auditor_cannot_retry_application(client):
    token = get_auditor_token(client)
    resp = client.post(
        "/api/v1/revenue/application/GM-2026-000135/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_unauthenticated_notifications_rejected(client):
    resp = client.get("/api/v1/revenue/notifications")
    assert resp.status_code == 401
