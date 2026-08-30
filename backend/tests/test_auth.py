def test_login_success_with_username(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800
    assert data["user"]["username"] == "revenue.officer"
    assert data["user"]["role"] == "REVENUE_OFFICER"
    assert "APPLICATION_VIEW_ASSIGNED" in data["permissions"]


def test_login_success_with_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "officer.pune@revenue.gov.in", "password": "Officer@2026"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "revenue.officer"


def test_login_success_with_mobile(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "9820011223", "password": "Officer@2026"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "revenue.officer"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "WrongPassword123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_identifier(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "unknown.officer@example.gov", "password": "SomePassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_inactive_user_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "inactive.officer", "password": "Inactive@2026"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "ACCOUNT_INACTIVE"


def test_get_me_profile_authenticated(client):
    # First login to obtain token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "revenue.officer"
    assert data["data"]["email"] == "officer.pune@revenue.gov.in"
    assert "password_hash" not in data["data"]


def test_get_me_profile_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_get_me_profile_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token.here"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOKEN_INVALID"


def test_logout_endpoint(client):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "LOGGED_OUT"


def test_refresh_token_endpoint(client):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "revenue.officer"


def test_reauthenticate_success_and_failure(client):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    token = login_resp.json()["access_token"]

    # Valid re-authentication
    reauth_ok = client.post(
        "/api/v1/auth/reauthenticate",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "Officer@2026"},
    )
    assert reauth_ok.status_code == 200
    assert reauth_ok.json()["success"] is True

    # Invalid re-authentication
    reauth_fail = client.post(
        "/api/v1/auth/reauthenticate",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "WrongPassword"},
    )
    assert reauth_fail.status_code == 401
    assert reauth_fail.json()["success"] is False
