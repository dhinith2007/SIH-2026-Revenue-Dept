# Phase 09 — Step 03: RBAC & Document Security Hardening Report
**GovMesh SIH26129 — Revenue & Forest Department of Maharashtra**

---

## 1. Objective

Phase 09 Step 03 delivers rigorous, backend-enforced Role-Based Access Control (RBAC) and document security across the Revenue & Forest Department module. It prevents Insecure Direct Object References (IDOR), eliminates privilege escalation vulnerabilities, enforces departmental case assignment boundaries, protects immutable finalized applications, guarantees strict read-only compliance for auditors, and establishes non-repudiable audit logging for sensitive document operations.

---

## 2. Security Findings Addressed

| Vulnerability / ID | Severity | Description | Status in Step 03 |
| :--- | :--- | :--- | :--- |
| **SEC-01** | **HIGH** | **Document Override Permission:** Document override endpoint (`POST /revenue/document/{document_id}/override`) previously permitted desk officers with `DOCUMENT_VERIFY` to perform manual overrides without verifying application assignment boundaries or enforcing `EXCEPTION_OVERRIDE` authority. | **RESOLVED** — Privileged override now strictly requires either senior departmental exception authority (`SENIOR_REVENUE_OFFICER`, `DEPARTMENT_ADMINISTRATOR` with `EXCEPTION_OVERRIDE`) or legitimate case assignment (`assigned_officer_id == current_user["id"]`). Client-supplied role/identity injections are strictly ignored. Finalized applications block overrides with HTTP 409. |
| **IDOR Exposure** | **HIGH** | Document retrieval, SVG previews, attachment, and verification allowed any authenticated officer with valid JWT to query or mutate documents across cases assigned to other officers. | **RESOLVED** — `verify_application_access()` enforces server-side ownership boundaries on all document operations. |
| **Auditor Mutation Risk** | **MEDIUM** | Auditor role was not strictly prohibited from mutating document states if calling modification endpoints directly. | **RESOLVED** — Auditors are restricted strictly to read-only access (HTTP 403 on upload, verify, override, approve, reject). |

*Note: Findings SEC-02 (Consent DB sync), SEC-04 (MIME magic-byte validation), SEC-05 (SVG sanitization), SEC-06 (HTTP headers), and SEC-09 (pincode regex) are intentionally reserved for subsequent Phase 09 steps.*

---

## 3. RBAC Architecture & Roles

The system uses server-side JWT authentication where the client identity is cryptographically verified on every request. Roles are defined in `app/core/permissions.py`:

```
                    ┌──────────────────────────────────────────────┐
                    │            Authenticated Officer             │
                    │               (JWT Bearer)                   │
                    └──────────────────────┬───────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
             [Operational Hierarchy]               [Independent Oversight]
                        │                                     │
         ┌──────────────┼──────────────┐                      ▼
         ▼              ▼              ▼               READ_ONLY_AUDITOR
  REVENUE_OFFICER    SENIOR_REV_    DEPARTMENT_        - Read-only queries
  - Desk scrutiny    OFFICER        ADMINISTRATOR      - Audit trail inspect
  - Assigned cases   - Dept-wide    - Dept-wide        - No mutation rights
  - Normal verify      oversight    - User management
  - Desk override    - Exception    - Exception
                       override       override
```

---

## 4. Document Authorization Matrix

| Endpoint | Verb | REVENUE_OFFICER (Assigned) | REVENUE_OFFICER (Unassigned Case) | REVENUE_OFFICER (Other's Case) | SENIOR_OFFICER | DEPT_ADMIN | READ_ONLY_AUDITOR | INACTIVE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `/revenue/application/{id}/documents` (List) | GET | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ✅ Allowed | ✅ Allowed | ✅ Allowed | ❌ 403 Inactive |
| `/revenue/document/{id}` (Metadata) | GET | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ✅ Allowed | ✅ Allowed | ✅ Allowed | ❌ 403 Inactive |
| `/revenue/document/{id}/preview` (SVG) | GET | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ✅ Allowed | ✅ Allowed | ✅ Allowed | ❌ 403 Inactive |
| `/revenue/application/{id}/documents` (Upload) | POST | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ❌ 403 Inactive |
| `/revenue/document/{id}/verify` (OCR) | POST | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ❌ 403 Inactive |
| `/revenue/document/{id}/override` (Override) | POST | ✅ Allowed | ❌ 403 Forbidden | ❌ 403 Forbidden | ✅ Allowed | ✅ Allowed | ❌ 403 Forbidden | ❌ 403 Inactive |

---

## 5. Application Access & IDOR Rules

Application and document access is regulated in `backend/app/core/authorization.py` via `verify_application_access()`:

1. **Active Account Check:** Accounts flagged with `is_active=False` fail immediately with HTTP 403 `ACCOUNT_INACTIVE`.
2. **Assignment Enforcement:** A standard `REVENUE_OFFICER` can only access applications where `assigned_officer_id` matches their own `user_id` or is `None` (unassigned pool). If `assigned_officer_id` belongs to another officer, access is denied with HTTP 403 `INSUFFICIENT_PERMISSION`.
3. **Department-Wide Roles:** `SENIOR_REVENUE_OFFICER` and `DEPARTMENT_ADMINISTRATOR` possess `APPLICATION_VIEW_ALL` and `EXCEPTION_OVERRIDE`, granting department-wide operational access.

---

## 6. Document Override Authorization Rules (SEC-01)

Document override (`POST /revenue/document/{document_id}/override`) modifies algorithmic OCR recommendations (e.g. setting an unreadable document to `VALIDATED`). The hardened rules require:

1. **Authenticated JWT:** Valid, non-expired token.
2. **Server-Side Identity:** User identity resolved from database (`current_user["id"]`); client body or query parameter role/ID overrides are discarded.
3. **Authority Check:**
   - `SENIOR_REVENUE_OFFICER` or `DEPARTMENT_ADMINISTRATOR`: Authorized via `EXCEPTION_OVERRIDE`.
   - `REVENUE_OFFICER`: Permitted **only** if they are the designated assigned officer for that specific application (`assigned_officer_id == current_user["id"]`).
   - `READ_ONLY_AUDITOR`: Strictly denied (HTTP 403).
4. **Mandatory Justification:** Requires `decision` (`VALIDATED` / `REJECTED`) and non-empty `reason`.
5. **State Lock:** Application must not be finalized.
6. **Audit Event:** Persists a `MANUAL_OVERRIDE` record in PostgreSQL with actor attribution.

---

## 7. Finalized Application Protection

Applications in terminal workflow states (`VERIFIED` or `REJECTED`) are strictly immutable:
- Any document mutation (upload, verify, manual override) against a finalized application returns **HTTP 409 `APPLICATION_ALREADY_FINALIZED`**.
- This check executes before any officer assignment evaluation, ensuring no officer or administrator can alter records of closed statutory cases.

---

## 8. Auditor Read-Only Guarantees

The `READ_ONLY_AUDITOR` role enforces:
- **Permitted:**
  - View application lists and detailed scrutiny records.
  - View document metadata and rendered SVG document previews.
  - Inspect statutory audit logs and workflow status histories.
- **Prohibited:**
  - Uploading or attaching proof documents (HTTP 403).
  - Executing document verification / OCR mutation (HTTP 403).
  - Executing manual overrides (HTTP 403).
  - Changing application states (approve, reject, request info) (HTTP 403).

---

## 9. Privilege Escalation Protections

The system prevents all common privilege escalation vectors:
- **Body Role Injection:** Payloads containing `{"role": "admin"}` or `{"role": "DEPARTMENT_ADMINISTRATOR"}` are ignored; Pydantic models reject extra fields and business logic derives role solely from verified JWT token.
- **Query Parameter Forgery:** Parameters like `?role=admin` have no effect on authorization dependencies.
- **Identity Forgery:** Overriding `officer_id` or `officer_name` in request payloads is ignored; audit records bind strictly to `current_user["id"]` from JWT claims.
- **Token Tampering:** Modifying JWT payload or signing key causes HMAC verification failure (HTTP 401 `AUTHENTICATION_REQUIRED`).

---

## 10. Statutory Audit Logging Behavior

Every privileged document action writes an immutable record to PostgreSQL:
- **Events Tracked:** `DOCUMENT_UPLOADED`, `DOCUMENT_VERIFIED`, `DOCUMENT_MISMATCH`, `MANUAL_OVERRIDE`.
- **Metadata Captured:** `officer_id`, `officer_name`, `application_id`, `document_id`, `action`, `previous_status`, `new_status`, `reason`, `correlation_id`, `timestamp`.
- **Sensitive Data Scrubbed:** Passwords, JWT tokens, Bearer headers, and raw file binary contents are excluded from audit storage.

---

## 11. Error Handling & HTTP Semantics

| HTTP Status | Error Code | Circumstance |
| :---: | :--- | :--- |
| **401** | `AUTHENTICATION_REQUIRED` | Missing, invalid, expired, or tampered JWT token. |
| **403** | `ACCOUNT_INACTIVE` | Valid JWT from a suspended or inactive officer account. |
| **403** | `INSUFFICIENT_PERMISSION` | Role boundary violation (Auditor mutation, IDOR access across cases, unauthorized override). |
| **404** | `RESOURCE_NOT_FOUND` | Document or Application ID does not exist in departmental records. |
| **409** | `APPLICATION_ALREADY_FINALIZED` | Attempting document mutation on a `VERIFIED` or `REJECTED` application. |
| **422** | `DATA_VALIDATION_ERROR` | Malformed payload (missing override decision or reason). |

---

## 12. PostgreSQL Persistence & Transaction Integrity

- All authorization decisions evaluate current database state via SQLAlchemy 2.x session.
- Document attachments and manual overrides commit atomically alongside their corresponding `audit_logs` entries.
- If authorization checks fail, the transaction raises an HTTP exception before any repository mutation is executed, ensuring zero partial updates or orphaned records.

---

## 13. Test Coverage Breakdown

A dedicated test suite was implemented in `backend/tests/test_phase09_rbac_document_security.py` containing 30 security tests:

| Category | Test Count | Description | Result |
| :--- | :---: | :--- | :---: |
| **A. Role Access** | 6 | Officer, Senior, Admin permissions; Auditor read access & mutation denial; Inactive account lockout. | **6 / 6 PASSED** |
| **B. Document Override (SEC-01)** | 5 | Unauthorized officer blocked; Privileged role allowed; Auditor blocked; Unauthenticated rejected; Finalized rejected. | **5 / 5 PASSED** |
| **C. Document Attachment** | 4 | Unauthorized officer blocked; Assigned officer allowed; Auditor blocked; Finalized application blocked. | **4 / 4 PASSED** |
| **D. Document Retrieval** | 4 | Authorized retrieval; Cross-case IDOR blocked; Auditor read allowed; Nonexistent ID returns 404. | **4 / 4 PASSED** |
| **E. Privilege Escalation** | 5 | Body role ignored; Query role ignored; Forged user ID ignored; Audit identity binding verified; Cross-app IDOR blocked. | **5 / 5 PASSED** |
| **F. Auditing** | 4 | Override creates persistent audit log; Identity and action captured; Secrets and tokens not logged; Auditor can inspect logs. | **4 / 4 PASSED** |
| **G. Finalized State** | 2 | VERIFIED application blocks document mutation; REJECTED application blocks document mutation. | **2 / 2 PASSED** |
| **Total Step 03 Tests** | **30** | **Comprehensive RBAC & Document Security Suite** | **30 / 30 PASSED** |

---

## 14. Verification Commands & Regression Results

### Dedicated Security Suite:
```powershell
python -m pytest tests/test_phase09_rbac_document_security.py -v
```
**Output:** `30 passed, 5 warnings in 2.10s`

### Complete Regression Suite (Phases 01–09):
```powershell
python -m pytest
```
**Output:** `167 passed, 10 warnings in 99.81s`

```
Test Distribution:
  - tests/test_api.py .................................... 3 passed
  - tests/test_applications.py ........................... 9 passed
  - tests/test_auth.py ................................... 12 passed
  - tests/test_health.py ................................. 4 passed
  - tests/test_phase05_operations.py ..................... 19 passed
  - tests/test_phase06_documents.py ...................... 23 passed
  - tests/test_phase08_persistence.py .................... 11 passed
  - tests/test_phase08_postgresql_e2e.py ................. 17 passed
  - tests/test_phase09_auth_security.py .................. 16 passed
  - tests/test_phase09_rbac_document_security.py ......... 30 passed
  - tests/test_rbac.py ................................... 4 passed
  - tests/test_workflow.py ............................... 19 passed
  ─────────────────────────────────────────────────────────────────
  Total: 167 passed, 0 failures, 0 regressions
```

---

## 15. Remaining Phase 09 Security Findings

| Finding ID | Severity | Description | Target Phase |
| :--- | :--- | :--- | :--- |
| **SEC-02** | MEDIUM | Consent database synchronization | Phase 09 Step 04 |
| **SEC-04** | MEDIUM | MIME magic-byte validation | Phase 09 Step 05 |
| **SEC-05** | MEDIUM | SVG XML escaping & sanitization | Phase 09 Step 05 |
| **SEC-06** | LOW | HTTP security headers | Phase 09 Step 05 |
| **SEC-09** | LOW | Pincode regex validation | Phase 09 Step 04 |
