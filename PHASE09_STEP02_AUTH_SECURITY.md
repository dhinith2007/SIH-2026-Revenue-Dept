# GovMesh SIH26129 — Authentication & Rate-Limiting Hardening
## Department: Revenue & Forest Department of Maharashtra
**Document Version:** 1.0.0  
**Phase:** Phase 09 — Step 02: Authentication & Rate-Limiting Hardening  
**Date:** September 2026  
**Status:** Verified & Complete  
**Test Suite Coverage:** 137 / 137 Tests Passing (121 baseline + 16 new security tests)

---

## 1. Authentication Architecture Overview

The Revenue & Forest Department system implements a multi-layered, standards-compliant authentication system for departmental personnel (Revenue Officers, Senior Revenue Officers, Department Administrators, and Read-only Auditors).

### Key Architectural Pillars:
- **Password Hashing:** Passlib with BCrypt (12 rounds standard salt generation) via `app/core/security.py`. Plaintext passwords are never logged, persisted, or returned in API responses.
- **Session Tokens:** Stateless JSON Web Tokens (JWT) signed using HMAC-SHA256 (`HS256`) containing user identifier (`sub`), username, and assigned role. Tokens strictly expire after 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 30`).
- **Flexible Login Identifiers:** Officers can authenticate using their assigned `username`, registered departmental `email`, or 10-digit `mobile` phone number.
- **Active Status Check:** The system verifies `is_active` status before processing authentication attempts. Inactive accounts are immediately rejected with HTTP 403 `ACCOUNT_INACTIVE`.
- **Sensitive Operation Re-Authentication:** High-privilege actions (e.g. manual exception overrides, administrative operations) require a dedicated password re-authentication challenge (`POST /api/v1/auth/reauthenticate`).
- **PostgreSQL & Memory Parity:** User authentication state is persistently managed in the PostgreSQL `users` table, with seamless fallback synchronization for standalone mode.

---

## 2. Account Lockout Policy & Implementation

To mitigate automated brute-force password guessing and targeted credential stuffing, a stateful account lockout mechanism is enforced at runtime.

### 2.1 Policy Rules:
- **Failure Threshold:** 5 consecutive failed login attempts.
- **Lock Duration:** 15 minutes from the timestamp of the 5th failed attempt.
- **Account State Isolation:** Inactive accounts are checked prior to credential verification; deactivation is never masked or overwritten by lockout state.
- **Generic Responses:** Failed login attempts for non-existent users return the exact same HTTP 401 generic error (`INVALID_CREDENTIALS`) as existing users with bad passwords to prevent user enumeration.

### 2.2 Control Flow & Concurrency Protection:
1. **Pre-Authentication Check:** When a user initiates authentication, `AuthService.authenticate` queries the user record and evaluates `locked_until`. If `locked_until > current UTC time`, the request is immediately rejected with HTTP 403 `ACCOUNT_LOCKED`.
2. **Lock Expiration:** If `locked_until <= current UTC time`, the temporary lock is considered expired and the user is permitted to attempt authentication again.
3. **Failure Tracking:** Upon password verification failure, `UserRepository.record_failed_login` increments `failed_login_attempts`.
   - On PostgreSQL, `with_for_update()` row-level locking is utilized to ensure concurrent requests cannot bypass the lockout threshold.
   - If previous lock expired, the failed attempt counter is reset to 1.
   - When the counter reaches 5, `locked_until` is set to `current UTC time + 15 minutes`.
4. **Post-Threshold Response:** The 5th failed attempt immediately returns HTTP 403 `ACCOUNT_LOCKED`.
5. **Success Reset:** A successful login executes `UserRepository.update_last_login`, resetting `failed_login_attempts = 0` and `locked_until = None`.

---

## 3. Authentication Rate Limiting Policy

### 3.1 Policy Configuration:
- **Protected Endpoints:**
  - `POST /api/v1/auth/login` (and alias `/api/v1/revenue/auth/login`)
  - `POST /api/v1/auth/reauthenticate`
- **Rate Limit Threshold:** 5 requests per 60 seconds per client IP.
- **Exceeded Response:** HTTP 429 `RATE_LIMIT_EXCEEDED` accompanied by a mandatory `Retry-After: <seconds>` HTTP response header.

### 3.2 Limiter Engine (`app/core/rate_limit.py`):
- Implements a thread-safe sliding window algorithm (`AuthRateLimiter`) with automatic eviction of expired timestamps.
- **Client IP Extraction:** Uses direct TCP peer host (`request.client.host`) to prevent attackers from bypassing the limiter by forging spoofed `X-Forwarded-For` HTTP headers.
- **Non-Interference:** Only authentication routes are throttled; regular authenticated application APIs (e.g. `GET /api/v1/revenue/applications`, workflow transitions) remain unthrottled.

---

## 4. Production Secret Fail-Fast Requirements

In accordance with audit finding **SEC-03**, default development credentials must never be active in production environments.

### 4.1 Fail-Fast Validation (`app/core/config.py`):
When `APP_ENV=production` or `APP_ENV=prod`, Pydantic Settings model validation executes immediately upon configuration load / application startup:

1. **JWT_SECRET Validation:**
   - Must be non-empty and at least 32 characters long.
   - Must NOT match any known development keys (e.g. `"dev-revenue-department-secret-key-sih26129-do-not-use-in-prod-32bytes"`, `"secret"`, `"changeme"`).
   - Must NOT contain `"do-not-use-in-prod"`.
   - Failure raises an immediate startup `ValueError`.
2. **DATABASE_URL Validation:**
   - Must be explicitly configured.
   - Must NOT match known insecure development URLs (e.g. `"postgresql://postgres:postgres@localhost:5432/revenue_db"`).
   - Must NOT contain `"postgres:postgres@localhost"` or `"postgres:postgres@127.0.0.1"`.
   - Failure raises an immediate startup `ValueError`.
3. **Secret Hygiene:** Error messages never print actual secret values or partial strings.
4. **Development Preservation:** When `APP_ENV=development`, safe local defaults continue to operate seamlessly.

---

## 5. Security Response Behavior

| Scenario | HTTP Status | Error Code | Response Message / Headers |
| :--- | :--- | :--- | :--- |
| **Invalid Password (< 5 failures)** | 401 Unauthorized | `INVALID_CREDENTIALS` | `"Invalid credentials. Please verify your identifier and password."` (`WWW-Authenticate: Bearer`) |
| **Unknown User Identifier** | 401 Unauthorized | `INVALID_CREDENTIALS` | `"Invalid credentials. Please verify your identifier and password."` (`WWW-Authenticate: Bearer`) |
| **Inactive Account** | 403 Forbidden | `ACCOUNT_INACTIVE` | `"This department account has been deactivated. Please contact your Department Administrator."` |
| **5th Failed Login Attempt** | 403 Forbidden | `ACCOUNT_LOCKED` | `"This department account has been temporarily locked due to multiple failed login attempts. Please try again in 15 minutes."` |
| **Attempt While Locked** | 403 Forbidden | `ACCOUNT_LOCKED` | `"This department account is temporarily locked due to multiple failed login attempts. Please try again in 15 minutes."` |
| **Rate Limit Exceeded** | 429 Too Many Requests | `RATE_LIMIT_EXCEEDED` | `"Too many authentication attempts. Please retry after <sec> seconds."` (`Retry-After: <sec>`) |
| **Successful Authentication** | 200 OK | N/A | Returns JWT token, `token_type: bearer`, `expires_in: 1800`, user summary, and permission list. |

---

## 6. Configuration Variables

| Variable | Type | Default (Dev) | Production Requirement |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | String | `development` | Must be set to `production` in production deployment. |
| `JWT_SECRET` | String | `dev-revenue-department-...` | Must be an externally configured random 32+ byte cryptographic key. |
| `JWT_ALGORITHM` | String | `HS256` | HMAC-SHA256 signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `30` | Access token lifespan in minutes. |
| `DATABASE_URL` | String | `postgresql://postgres:...` | Must point to a secure, password-protected PostgreSQL instance. |
| `DB_POOL_SIZE` | Integer | `5` | SQLAlchemy connection pool size. |
| `DB_MAX_OVERFLOW` | Integer | `10` | Maximum pool overflow connections. |

---

## 7. Test Verification & Coverage

A dedicated test suite was implemented in `backend/tests/test_phase09_auth_security.py`. All 16 tests pass deterministically alongside the 121 existing baseline tests.

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
collected 137 items

tests\test_api.py ...                                                    [  2%]
tests\test_applications.py .........                                     [  8%]
tests\test_auth.py ............                                          [ 17%]
tests\test_health.py ....                                                [ 20%]
tests\test_phase05_operations.py ...................                     [ 34%]
tests\test_phase06_documents.py .......................                  [ 51%]
tests\test_phase08_persistence.py ...........                            [ 59%]
tests\test_phase08_postgresql_e2e.py .................                   [ 71%]
tests\test_phase09_auth_security.py ................                     [ 83%]
tests\test_rbac.py ....                                                  [ 86%]
tests\test_workflow.py ...................                               [100%]

================= 137 passed, 10 warnings in 84.64s =================
```

### Detailed Breakdown of Phase 09 Security Tests:
1. `test_01_first_failed_login_increments_counter`: Verifies counter increments to 1 on bad password.
2. `test_02_four_failed_attempts_do_not_lock_account`: Verifies 4 attempts remain unlocked with HTTP 401.
3. `test_03_fifth_failed_attempt_locks_account`: Verifies 5th failure returns HTTP 403 `ACCOUNT_LOCKED` and sets `locked_until`.
4. `test_04_locked_account_cannot_authenticate_even_with_correct_password`: Verifies locked user is blocked with HTTP 403 on correct password.
5. `test_05_lock_expiration_allows_authentication`: Verifies authentication is allowed once `locked_until` has passed.
6. `test_06_successful_login_resets_failed_login_counter`: Verifies successful login resets counter to 0 and clears `locked_until`.
7. `test_07_lockout_state_persists_in_postgresql`: Verifies lockout attributes persist in the PostgreSQL database.
8. `test_08_login_rate_limit_returns_http_429`: Verifies 6th login request from an IP within 1 minute returns HTTP 429.
9. `test_09_reauthentication_rate_limit_returns_http_429`: Verifies 6th re-auth request returns HTTP 429.
10. `test_10_rate_limit_does_not_affect_unrelated_authenticated_apis`: Verifies application APIs remain responsive when auth limiter triggers.
11. `test_11_production_config_rejects_missing_jwt_secret`: Verifies fail-fast on empty/short JWT secret in production.
12. `test_12_production_config_rejects_known_default_jwt_secret`: Verifies fail-fast on default dev JWT secret in production.
13. `test_13_production_config_rejects_unsafe_default_database_url`: Verifies fail-fast on default localhost DB URL in production.
14. `test_14_production_config_accepts_secure_production_settings`: Verifies valid production settings are accepted.
15. `test_15_development_config_continues_working_with_defaults`: Verifies development mode continues using local defaults.
16. `test_16_non_existent_account_returns_same_generic_credential_error`: Verifies prevention of user enumeration attacks.

---

## 8. Deployment Considerations

1. **Proxy & WAF Integration:** In a production multi-tier deployment (e.g. AWS ALB, Cloudflare, Nginx), the reverse proxy should be configured to set standard forwarding headers. The application server should sit in a private subnet.
2. **Database Permissions:** The database connection user should have permissions restricted to the `revenue_db` schema without superuser privileges.
3. **Environment Injection:** In production CI/CD (Kubernetes Secrets, HashiCorp Vault, AWS Secrets Manager), inject `JWT_SECRET` and `DATABASE_URL` as container environment variables.

---

## 9. Known Limitations

1. **In-Memory Rate Limiter Scope:** The current rate limiter runs in-process memory. In horizontally scaled multi-instance deployments without sticky sessions, rate limits apply per instance unless backed by a shared Redis cluster. For single-container / dedicated server deployments, this provides robust brute-force deterrence with zero external dependencies.
2. **Permanent Account Disabling:** By policy, accounts are temporarily locked for 15 minutes rather than permanently disabled to prevent denial-of-service against legitimate officers. Administrators can manually deactivate accounts via `User.is_active = False` if permanent suspension is required.
