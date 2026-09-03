import pytest
from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal, is_db_available
from app.models.user import User
from app.core.config import Settings
from app.core.rate_limit import reset_rate_limiter, auth_limiter


@pytest.fixture(autouse=True)
def clean_test_user():
    """Ensure revenue.officer starts each test unlocked with 0 failed attempts."""
    reset_rate_limiter()
    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            if user:
                user.failed_login_attempts = 0
                user.locked_until = None
                db.commit()
    yield
    reset_rate_limiter()
    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            if user:
                user.failed_login_attempts = 0
                user.locked_until = None
                db.commit()


# ==============================================================================
# Task 1: Account Lockout Tests (Tests 1 - 7)
# ==============================================================================

def test_01_first_failed_login_increments_counter(client):
    """Test 1: First failed login increments counter to 1."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "WrongPassword1"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            assert user is not None
            assert user.failed_login_attempts == 1
            assert user.locked_until is None


def test_02_four_failed_attempts_do_not_lock_account(client):
    """Test 2: Four failed attempts increment counter to 4 but do not lock the account."""
    for i in range(1, 5):
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": "revenue.officer", "password": f"WrongPassword{i}"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            assert user is not None
            assert user.failed_login_attempts == 4
            assert user.locked_until is None


def test_03_fifth_failed_attempt_locks_account(client):
    """Test 3: Fifth failed attempt triggers account lockout with HTTP 403."""
    for i in range(1, 5):
        client.post(
            "/api/v1/auth/login",
            json={"identifier": "revenue.officer", "password": f"WrongPassword{i}"},
        )

    # 5th attempt
    resp5 = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "WrongPassword5"},
    )
    assert resp5.status_code == 403
    data = resp5.json()
    assert data["success"] is False
    assert data["error"]["code"] == "ACCOUNT_LOCKED"
    assert "temporarily locked" in data["error"]["message"].lower()

    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            assert user is not None
            assert user.failed_login_attempts >= 5
            assert user.locked_until is not None
            assert user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None)


def test_04_locked_account_cannot_authenticate_even_with_correct_password(client):
    """Test 4: Locked account cannot authenticate even when providing correct credentials."""
    # Trigger lockout with 5 failed attempts
    for i in range(1, 6):
        client.post(
            "/api/v1/auth/login",
            json={"identifier": "revenue.officer", "password": f"Wrong{i}"},
        )

    # Reset client IP rate limiter so we test account lockout specifically
    reset_rate_limiter()

    # Attempt login with correct password
    resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_05_lock_expiration_allows_authentication(client):
    """Test 5: After locked_until expires, authentication is permitted again."""
    # Trigger lockout
    for i in range(1, 6):
        client.post(
            "/api/v1/auth/login",
            json={"identifier": "revenue.officer", "password": f"Wrong{i}"},
        )

    # Simulate lock expiration by setting locked_until to past
    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            user.locked_until = past_time.replace(tzinfo=None)
            db.commit()

    # Reset client IP rate limiter so we test post-lockout login
    reset_rate_limiter()

    # Now attempt with valid password
    resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["username"] == "revenue.officer"


def test_06_successful_login_resets_failed_login_counter(client):
    """Test 6: Successful login resets failed_login_attempts to 0 and clears locked_until."""
    # 2 failed attempts
    client.post("/api/v1/auth/login", json={"identifier": "revenue.officer", "password": "Bad1"})
    client.post("/api/v1/auth/login", json={"identifier": "revenue.officer", "password": "Bad2"})

    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            assert user.failed_login_attempts == 2

    # Successful login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert login_resp.status_code == 200

    if is_db_available():
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "revenue.officer").first()
            assert user.failed_login_attempts == 0
            assert user.locked_until is None


def test_07_lockout_state_persists_in_postgresql(client):
    """Test 7: Verify failed attempts and lockout timestamp are persistently stored in PostgreSQL."""
    if not is_db_available():
        pytest.skip("PostgreSQL not available in this environment")

    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "revenue.officer").first()
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    for i in range(5):
        client.post("/api/v1/auth/login", json={"identifier": "revenue.officer", "password": f"Fail{i}"})

    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "revenue.officer").first()
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None


# ==============================================================================
# Task 2: Authentication Rate Limiting Tests (Tests 8 - 11)
# ==============================================================================

def test_08_login_rate_limit_returns_http_429(client):
    """Test 8: Exceeding 5 login requests per minute returns HTTP 429."""
    reset_rate_limiter()

    # 5 allowed requests
    for i in range(5):
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": "unknown.user", "password": "AnyPassword"},
        )
        assert resp.status_code == 401

    # 6th request triggers rate limit
    resp_limit = client.post(
        "/api/v1/auth/login",
        json={"identifier": "unknown.user", "password": "AnyPassword"},
    )
    assert resp_limit.status_code == 429
    data = resp_limit.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in resp_limit.headers
    assert int(resp_limit.headers["Retry-After"]) >= 1


def test_09_reauthentication_rate_limit_returns_http_429(client):
    """Test 9: Exceeding 5 re-authentication requests per minute returns HTTP 429."""
    reset_rate_limiter()

    # Obtain valid officer token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Reset limiter to test reauthenticate endpoint specifically
    reset_rate_limiter()

    # 5 allowed attempts
    for _ in range(5):
        resp = client.post(
            "/api/v1/auth/reauthenticate",
            headers=headers,
            json={"password": "Officer@2026"},
        )
        assert resp.status_code == 200

    # 6th attempt triggers 429
    resp_limit = client.post(
        "/api/v1/auth/reauthenticate",
        headers=headers,
        json={"password": "Officer@2026"},
    )
    assert resp_limit.status_code == 429
    assert resp_limit.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in resp_limit.headers


def test_10_rate_limit_does_not_affect_unrelated_authenticated_apis(client):
    """Test 10: Exhausting auth rate limit does NOT block normal application endpoints."""
    # Obtain token first
    reset_rate_limiter()
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Exhaust rate limiter on login
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"identifier": "test", "password": "test"})

    # Verify login is now blocked
    limit_resp = client.post("/api/v1/auth/login", json={"identifier": "test", "password": "test"})
    assert limit_resp.status_code == 429

    # Verify application API remains fully functional
    app_resp = client.get("/api/v1/revenue/applications", headers=headers)
    assert app_resp.status_code == 200
    assert app_resp.json()["success"] is True


# ==============================================================================
# Task 3: Production Secret Fail-Fast Tests (Tests 11 - 15)
# ==============================================================================

def test_11_production_config_rejects_missing_jwt_secret():
    """Test 11: Production environment fails fast if JWT_SECRET is empty or too short."""
    with pytest.raises(ValueError) as exc_info:
        Settings(
            APP_ENV="production",
            JWT_SECRET="",
            DATABASE_URL="postgresql://prod_user:strongpass@prod-db.gov.in:5432/revenue_db",
        )
    assert "JWT_SECRET must be configured" in str(exc_info.value)


def test_12_production_config_rejects_known_default_jwt_secret():
    """Test 12: Production environment fails fast if default development JWT_SECRET is used."""
    with pytest.raises(ValueError) as exc_info:
        Settings(
            APP_ENV="production",
            JWT_SECRET="dev-revenue-department-secret-key-sih26129-do-not-use-in-prod-32bytes",
            DATABASE_URL="postgresql://prod_user:strongpass@prod-db.gov.in:5432/revenue_db",
        )
    assert "insecure default key" in str(exc_info.value)


def test_13_production_config_rejects_unsafe_default_database_url():
    """Test 13: Production environment fails fast if default localhost development DB URL is used."""
    with pytest.raises(ValueError) as exc_info:
        Settings(
            APP_ENV="production",
            JWT_SECRET="super-secure-production-jwt-key-minimum-32-chars-long",
            DATABASE_URL="postgresql://postgres:postgres@localhost:5432/revenue_db",
        )
    assert "DATABASE_URL is using known development credentials" in str(exc_info.value)


def test_14_production_config_accepts_secure_production_settings():
    """Test 14: Production configuration succeeds when strong production credentials are provided."""
    prod_settings = Settings(
        APP_ENV="production",
        JWT_SECRET="a-very-strong-and-secure-random-jwt-secret-key-for-prod-998877",
        DATABASE_URL="postgresql://dept_app_user:StrongK3y#9821@db.internal.revenue.gov.in:5432/revenue_db",
    )
    assert prod_settings.APP_ENV == "production"


def test_15_development_config_continues_working_with_defaults():
    """Test 15: Development configuration continues to run seamlessly with local defaults."""
    dev_settings = Settings(
        APP_ENV="development",
    )
    assert dev_settings.APP_ENV == "development"
    assert dev_settings.JWT_SECRET is not None
    assert dev_settings.DATABASE_URL is not None


# ==============================================================================
# Task 4 & 5: Existing Authentication & Non-disclosing Errors (Test 16)
# ==============================================================================

def test_16_non_existent_account_returns_same_generic_credential_error(client):
    """Test 16: Non-existent accounts return identical 401 generic error (no user enumeration)."""
    resp_bad_pass = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "WrongPassword"},
    )
    resp_no_user = client.post(
        "/api/v1/auth/login",
        json={"identifier": "completely.nonexistent.user", "password": "WrongPassword"},
    )
    assert resp_bad_pass.status_code == 401
    assert resp_no_user.status_code == 401
    assert resp_bad_pass.json()["error"]["code"] == resp_no_user.json()["error"]["code"]
    assert resp_bad_pass.json()["error"]["message"] == resp_no_user.json()["error"]["message"]
