import jwt
from app.core.config import settings


def test_admin_user_can_access_admin_endpoint(client):
    # Log in as Department Administrator
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.admin", "password": "Admin@2026"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Access protected admin users endpoint
    resp = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 4


def test_revenue_officer_cannot_access_admin_endpoint_returns_403(client):
    # Log in as Revenue Officer
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Attempt to access admin endpoint
    resp = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_auditor_cannot_access_admin_endpoint_returns_403(client):
    # Log in as Read-only Auditor
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.auditor", "password": "Auditor@2026"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Attempt to access admin endpoint
    resp = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_PERMISSION"


def test_tampered_token_signature_rejected(client):
    # Create fake token signed with invalid secret
    fake_token = jwt.encode(
        {"sub": "USR-REV-001", "username": "revenue.officer", "role": "DEPARTMENT_ADMINISTRATOR"},
        "fake-wrong-secret-key",
        algorithm="HS256",
    )

    resp = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOKEN_INVALID"
