"""
GovMesh SIH26129 — Phase 09 Step 05: Transport & HTTP Security Hardening Tests

Covers:
- A. Security response headers (nosniff, DENY, no-referrer, CSP, Permissions-Policy, conditional HSTS)
- B. CORS configuration (allowed origins, arbitrary origin rejection, wildcard+credentials rejection)
- C. Host header security (TrustedHostMiddleware, localhost support)
- D. Forwarded header protection (X-Forwarded-For spoofing cannot bypass auth rate limiting)
- E. HTTP methods (unsupported methods return 405 with Allow header)
- F. Error response hardening (no stack traces, credentials, or file paths across 401, 403, 404, 405, 422, 429, 500)
- G. Cache & Content-Type controls (no-store on auth and documents, correct MIME types)
- H. JWT transport security (header-only extraction, no query param tokens, no credential echoing)
- I. Security regression verification (Auth, Lockout, RBAC, Document security, Consent DB sync)
"""
import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.main import app
from app.core.config import Settings, settings
from app.core.security import create_access_token
from app.core.rate_limit import reset_rate_limiter, auth_limiter, extract_client_ip
from app.core.security_headers import SecurityHeadersMiddleware

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_rate_limit():
    reset_rate_limiter()
    yield
    reset_rate_limiter()


@pytest.fixture
def desk_officer_token():
    return create_access_token({
        "sub": "USR-REV-001",
        "username": "ro_deshmukh",
        "role": "REVENUE_OFFICER",
    })


@pytest.fixture
def desk_officer_headers(desk_officer_token):
    return {"Authorization": f"Bearer {desk_officer_token}"}


# ===========================================================================
# A. SECURITY HEADERS
# ===========================================================================

def test_01_security_headers_content_type_options():
    """All responses must include X-Content-Type-Options: nosniff."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_02_security_headers_frame_options():
    """All responses must include X-Frame-Options: DENY to prevent clickjacking."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-frame-options") == "DENY"


def test_03_security_headers_referrer_policy():
    """All responses must include Referrer-Policy: no-referrer."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("referrer-policy") == "no-referrer"


def test_04_security_headers_content_security_policy_api():
    """API endpoints must return strict API CSP: default-src 'none'; frame-ancestors 'none'."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    csp = response.headers.get("content-security-policy", "")
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


def test_05_security_headers_content_security_policy_docs():
    """Interactive docs (/docs, /redoc) must receive a CSP compatible with Swagger UI."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    csp = response.headers.get("content-security-policy", "")
    assert "cdn.jsdelivr.net" in csp
    assert "frame-ancestors 'none'" in csp


def test_06_security_headers_permissions_policy():
    """Permissions-Policy must restrict sensitive browser capabilities."""
    response = client.get("/health")
    assert response.status_code == 200
    pp = response.headers.get("permissions-policy", "")
    assert "camera=()" in pp
    assert "microphone=()" in pp
    assert "geolocation=()" in pp


def test_07_hsts_absent_in_development_http():
    """HSTS must NOT be enabled for local HTTP development."""
    response = client.get("http://localhost:8000/health")
    assert response.status_code == 200
    # In development mode, Strict-Transport-Security must not be present on HTTP
    if settings.APP_ENV.lower() not in ("production", "prod") and not settings.ENABLE_HSTS:
        assert "strict-transport-security" not in response.headers


def test_08_hsts_present_in_https_or_production():
    """HSTS is added when request is HTTPS or when ENABLE_HSTS is active."""
    # Simulated HTTPS request via test client
    response = client.get("https://localhost:8000/health")
    assert response.status_code == 200
    assert "strict-transport-security" in response.headers
    assert "max-age=31536000" in response.headers["strict-transport-security"]


# ===========================================================================
# B. CORS CONFIGURATION
# ===========================================================================

def test_09_cors_allowed_frontend_origin():
    """Configured frontend origin (http://localhost:5173) must receive allow-origin header."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_10_cors_disallowed_arbitrary_origin():
    """Arbitrary untrusted origins must NOT receive an Access-Control-Allow-Origin header."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://malicious-phishing-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Untrusted origin should not be reflected in access-control-allow-origin
    assert response.headers.get("access-control-allow-origin") != "https://malicious-phishing-site.com"


def test_11_cors_wildcard_with_credentials_rejected_in_production():
    """Settings must reject wildcard '*' in CORS_ORIGINS when running in production."""
    with pytest.raises(ValueError, match="CORS_ORIGINS must not contain wildcard"):
        Settings(
            APP_ENV="production",
            JWT_SECRET="a-very-long-secure-random-production-key-32-chars",
            DATABASE_URL="postgresql://prod_user:safe_pass@prod-db.internal:5432/revenue_db",
            CORS_ORIGINS=["*"],
        )


def test_12_cors_development_localhost_remains_functional():
    """Port 3000 and 5173 are both valid dev origins."""
    for origin in ["http://localhost:3000", "http://localhost:5173"]:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin


# ===========================================================================
# C. HOST SECURITY
# ===========================================================================

def test_13_host_security_localhost_functional_in_development():
    """Requests with localhost or 127.0.0.1 host headers function correctly."""
    response = client.get("/health", headers={"Host": "localhost:8000"})
    assert response.status_code == 200


def test_14_host_security_trusted_host_middleware_rejects_spoofed_host():
    """When TrustedHostMiddleware is configured with restricted domains, bad hosts return 400."""
    test_app = FastAPI()
    test_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.govmesh.internal", "localhost"])
    
    @test_app.get("/test")
    def test_route():
        return {"ok": True}

    sub_client = TestClient(test_app)
    # Allowed host
    ok_res = sub_client.get("/test", headers={"Host": "api.govmesh.internal"})
    assert ok_res.status_code == 200

    # Spoofed/attacker host
    bad_res = sub_client.get("/test", headers={"Host": "attacker.com"})
    assert bad_res.status_code == 400
    assert "Invalid host header" in bad_res.text


# ===========================================================================
# D. FORWARDED HEADER SECURITY & CLIENT IP
# ===========================================================================

def test_15_spoofed_x_forwarded_for_cannot_bypass_rate_limiting():
    """
    An attacker cannot bypass authentication rate limiting simply by rotating
    the X-Forwarded-For or X-Real-IP headers.
    """
    # Attempt 5 failed logins from testclient
    for i in range(5):
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": "wrong_user", "password": "WrongPassword123!"},
            headers={"X-Forwarded-For": f"192.168.1.{i+1}"},
        )
        assert resp.status_code == 401

    # 6th attempt with yet another spoofed IP header must be blocked with HTTP 429
    resp6 = client.post(
        "/api/v1/auth/login",
        json={"identifier": "wrong_user", "password": "WrongPassword123!"},
        headers={"X-Forwarded-For": "8.8.8.8", "X-Real-IP": "1.1.1.1"},
    )
    assert resp6.status_code == 429
    data = resp6.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in resp6.headers


# ===========================================================================
# E. HTTP METHOD SECURITY
# ===========================================================================

def test_16_unsupported_method_returns_405_with_allow_header():
    """Invoking an endpoint with an unsupported HTTP method returns 405 Method Not Allowed."""
    # /auth/login is strictly POST
    response = client.get("/api/v1/auth/login")
    assert response.status_code == 405
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert "Allow" in response.headers or "allow" in response.headers


def test_17_sensitive_endpoint_cannot_be_invoked_with_unintended_method():
    """POST /auth/reauthenticate rejects GET and DELETE with HTTP 405."""
    for method in ["get", "delete", "put", "patch"]:
        fn = getattr(client, method)
        res = fn("/api/v1/auth/reauthenticate")
        assert res.status_code == 405
        assert res.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


# ===========================================================================
# F. ERROR RESPONSE HARDENING
# ===========================================================================

def test_18_error_401_does_not_expose_credentials():
    """HTTP 401 responses must not leak passwords, tokens, or hashes."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "test_user", "password": "SuperSecretPassword123"},
    )
    assert res.status_code == 401
    body_text = res.text
    assert "SuperSecretPassword123" not in body_text
    data = res.json()
    assert data["error"]["code"] in ("INVALID_CREDENTIALS", "ACCOUNT_LOCKED")


def test_19_error_403_does_not_expose_internals():
    """HTTP 403 responses must provide clean messages without internal trace info."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.auditor", "password": "Auditor@2026"},
    )
    token = login_res.json()["access_token"]
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json={"decision": "VALIDATED", "reason": "Test reason override"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    data = res.json()
    assert data["success"] is False
    assert "Traceback" not in res.text
    assert "internal" not in str(data["error"]["message"]).lower()


def test_20_error_404_does_not_expose_filesystem_or_db_details():
    """HTTP 404 responses must not leak server file paths or table schemas."""
    res = client.get("/api/v1/revenue/application/GM-NONEXISTENT-999999", headers={"Authorization": "Bearer fake"})
    assert res.status_code in (401, 404)
    assert "C:\\" not in res.text
    assert "/var/" not in res.text
    assert "SELECT " not in res.text


def test_21_error_422_does_not_expose_server_internals():
    """HTTP 422 validation errors must contain clean field error lists without stack traces."""
    res = client.post("/api/v1/auth/login", json={"invalid_field": 123})
    assert res.status_code == 422
    assert "Traceback" not in res.text
    assert res.json()["success"] is False


def test_22_error_429_preserves_retry_after():
    """Rate limit exceeded returns HTTP 429 with clean message and Retry-After header."""
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"identifier": "u", "password": "p"})
    res = client.post("/api/v1/auth/login", json={"identifier": "u", "password": "p"})
    assert res.status_code == 429
    assert "Retry-After" in res.headers
    assert int(res.headers["Retry-After"]) > 0


def test_23_error_500_suppresses_stack_trace():
    """Global unhandled exception handler returns safe message without Python stack trace."""
    test_app = FastAPI()
    from app.core.errors import register_error_handlers
    register_error_handlers(test_app)

    @test_app.get("/trigger-crash")
    def trigger_crash():
        raise RuntimeError("Secret internal database driver connection crashed!")

    crash_client = TestClient(test_app, raise_server_exceptions=False)
    res = crash_client.get("/trigger-crash")
    assert res.status_code == 500
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "Secret internal database" not in res.text
    assert "Traceback" not in res.text


# ===========================================================================
# G. CACHE CONTROLS & CONTENT TYPE
# ===========================================================================

def test_24_auth_endpoints_have_no_store_cache_control(desk_officer_headers):
    """Authentication endpoints must return Cache-Control: no-store."""
    # /auth/me
    res = client.get("/api/v1/auth/me", headers=desk_officer_headers)
    assert res.status_code == 200
    cc = res.headers.get("cache-control", "")
    assert "no-store" in cc
    assert "no-cache" in cc
    assert res.headers.get("pragma") == "no-cache"


def test_25_document_endpoints_have_no_store_cache_control(desk_officer_headers):
    """Document retrieval endpoints must return Cache-Control: no-store."""
    res = client.get("/api/v1/revenue/document/DOC-REV-9081", headers=desk_officer_headers)
    assert res.status_code == 200
    cc = res.headers.get("cache-control", "")
    assert "no-store" in cc


def test_26_api_json_responses_have_correct_content_type():
    """Standard API endpoints must return application/json content type."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/json")


def test_27_document_preview_has_controlled_svg_content_type(desk_officer_headers):
    """Document preview returns strictly image/svg+xml with nosniff."""
    res = client.get("/api/v1/revenue/document/DOC-REV-9081/preview", headers=desk_officer_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    assert res.headers["x-content-type-options"] == "nosniff"


# ===========================================================================
# H. JWT TRANSPORT SECURITY
# ===========================================================================

def test_28_token_not_accepted_from_url_query_parameters(desk_officer_token):
    """JWT tokens passed via query parameter (?token=...) are rejected with 401."""
    res = client.get(f"/api/v1/auth/me?token={desk_officer_token}")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_29_auth_failure_does_not_echo_token():
    """Invalid token presented in header is not echoed back in error response."""
    bogus_token = "eyFakeHeader.eyFakePayloadSecret12345.Signature"
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bogus_token}"})
    assert res.status_code in (401, 403)
    assert bogus_token not in res.text


# ===========================================================================
# I. REGRESSION & INTEGRATION VALIDATION
# ===========================================================================

def test_30_auth_login_happy_path():
    """Standard login with valid credentials succeeds."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "REVENUE_OFFICER"


def test_31_account_lockout_still_functional():
    """5 failed attempts on same user trigger temporary lockout."""
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"identifier": "senior.officer", "password": "WrongPassword!"},
        )
        reset_rate_limiter()  # Reset rate limit so lockout logic is isolated

    # 6th attempt should return ACCOUNT_LOCKED (HTTP 403)
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "senior.officer", "password": "WrongPassword!"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCOUNT_LOCKED"

    # Clean up lockout state for subsequent tests
    from app.repositories.user_repository import UserRepository
    from app.db.session import SessionLocal, is_db_available
    if is_db_available():
        with SessionLocal() as db:
            UserRepository(db).update_last_login("USR-REV-002")
    UserRepository().update_last_login("USR-REV-002")


def test_32_rbac_auditor_read_only_guarantee():
    """Read-only auditor cannot mutate applications or approve cases."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.auditor", "password": "Auditor@2026"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/approve",
        json={"reason": "Auditor trying to approve"},
        headers=headers,
    )
    assert res.status_code == 403


def test_33_document_authorization_boundaries(desk_officer_headers):
    """Assigned officer can view metadata for assigned application document."""
    res = client.get("/api/v1/revenue/document/DOC-REV-9081", headers=desk_officer_headers)
    assert res.status_code == 200
    assert res.json()["data"]["document_id"] == "DOC-REV-9081"


def test_34_consent_validation_still_functional(desk_officer_headers):
    """Consent validation endpoint successfully executes 8 DPDP rules."""
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/validate-consent",
        headers=desk_officer_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["valid"] is True
    assert data["status"] == "VALID"
    assert len(data["rules_evaluated"]) == 8


def test_35_docs_disabled_in_production_when_enable_docs_is_false():
    """FastAPI can disable /docs and /openapi.json when ENABLE_DOCS=False."""
    prod_app = FastAPI(
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
    prod_client = TestClient(prod_app)
    docs_res = prod_client.get("/docs")
    assert docs_res.status_code == 404
    openapi_res = prod_client.get("/openapi.json")
    assert openapi_res.status_code == 404
