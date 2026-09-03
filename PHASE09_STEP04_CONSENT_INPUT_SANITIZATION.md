# Phase 09 — Step 04: Consent Synchronization & Input Sanitization Report
**GovMesh SIH26129 — Revenue & Forest Department of Maharashtra**

---

## 1. Executive Summary

Phase 09 Step 04 delivers comprehensive security hardening across:
1. **Live Consent Synchronization (SEC-02):** Authoritative database precedence for Citizen Consent validation (`revenue_consents` table via `ConsentRepository`), mitigating client-side payload spoofing, honoring external revocations, and enforcing mandatory statutory verification gates.
2. **File Signature / Magic-Byte Binary Inspection (SEC-04):** Byte-level file verification for document uploads (`%PDF-`, `\xFF\xD8\xFF`, `\x89PNG\r\n\x1a\n`), preventing MIME-spoofing and executable-renaming attacks.
3. **Filename Safety & Path Traversal Mitigation (SEC-04):** Strict validation rejecting path traversal sequences (`..`), null bytes (`\x00`), control characters, and oversized filenames.
4. **SVG Preview Entity Sanitization (SEC-05):** Rigorous XML entity escaping and control-character stripping across all citizen/address parameters embedded in SVG previews, neutralizing Stored XSS and XML injection vectors.
5. **Postal PIN Code Format Validation (SEC-09):** Deterministic 6-digit Indian PIN code regex validation (`^[1-9][0-9]{5}$`) for both new and existing residential address structures.
6. **Query Sort Column Whitelisting:** Explicit attribute whitelisting in `ApplicationRepository.list_applications` (`received_at`, `updated_at`, `priority`, `status`, `citizen_name`, `application_id`, `service_type`), preventing arbitrary attribute reflection or ORM injection.

**Test Suite Status:** 193 / 193 automated tests passing across the backend repository (100% pass rate).

---

## 2. Security Findings Addressed

| Vulnerability / ID | Severity | Description | Status in Step 04 |
| :--- | :---: | :--- | :--- |
| **SEC-02** | **MEDIUM** | **Relational Consent Desynchronization:** Previous consent checks relied on client-supplied JSON payloads in `data_payload["consent_record"]`. External revocations or expirations recorded in the authoritative `revenue_consents` table were bypassed. | **RESOLVED** — `ConsentService.validate_consent` now authoritatively resolves `ConsentRepository` live records before inspecting payload claims. Any DB revocation or expiration strictly overrides client data. |
| **SEC-04** | **LOW** | **Header-Only MIME Validation:** Document uploads previously validated only client-declared `Content-Type` headers and file extension strings, allowing attackers to upload arbitrary binaries renamed with `.pdf` or `.png`. | **RESOLVED** — Binary file signatures are inspected on upload. Files claiming to be PDF, PNG, or JPG must match their respective magic-byte signatures (`%PDF-`, `\x89PNG\r\n\x1a\n`, `\xFF\xD8\xFF`) or fail with HTTP 422 `DOCUMENT_INVALID`. |
| **SEC-04 (Aux)** | **LOW** | **Filename Path Traversal & Null Bytes:** Uploaded filenames were not checked against directory traversal (`../`) or null-byte poisoning (`\x00`). | **RESOLVED** — `validate_filename_safety` enforces path traversal, null byte, control character, and length constraints (≤ 255 chars). |
| **SEC-05** | **LOW** | **Unescaped SVG Preview Rendering:** Document preview constructed SVG templates interpolating raw address and citizen name strings without XML entity escaping, presenting a Stored XSS risk. | **RESOLVED** — All dynamic values formatted into SVG templates are sanitized via `sanitize_svg_text()`, escaping XML entities (`&`, `<`, `>`, `"`, `'`) and stripping invalid control characters. |
| **SEC-09** | **INFO** | **Permissive Pincode Validation:** Pincode validation only checked string presence without enforcing Indian postal code format. | **RESOLVED** — `DataValidationService` enforces `^[1-9][0-9]{5}$`, rejecting non-digits, leading zeros, and invalid lengths. |
| **Sort Whitelist** | **INFO** | **Arbitrary Attribute Sorting:** `getattr(Application, sort_by)` allowed callers to specify arbitrary attributes. | **RESOLVED** — Whitelisted to `ALLOWED_SORT_COLUMNS` with safe fallback to `received_at`. |

---

## 3. Technical Architecture & Implementation Details

### 3.1 Authoritative DPDP Consent Synchronization (SEC-02)

```
                       ┌───────────────────────────────┐
                       │  Workflow / Scrutiny Request  │
                       └──────────────┬────────────────┘
                                      │
                                      ▼
                        ConsentService.validate_consent()
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
      [Consent Override (Tests)]               Query ConsentRepository
                 │                             (Live PostgreSQL / Sync Store)
                 │                                         │
                 │                         ┌───────────────┴───────────────┐
                 │                         ▼                               ▼
                 │                 [Record Found]                   [Not in DB]
                 │                 - Precedence: 1                  - Fallback to
                 │                 - Status authoritative             Payload JSON
                 │                 - Revocation authoritative
                 │                                 │
                 └────────────────►┌───────────────┴───────────────┐
                                   │  8-Rule DPDP Validation Gate  │
                                   │  - Rule 1: Reference Exists   │
                                   │  - Rule 2: Application Match  │
                                   │  - Rule 3: Status Valid       │
                                   │  - Rule 4: Not Expired        │
                                   │  - Rule 5: Not Revoked        │
                                   │  - Rule 6: Purpose Match      │
                                   │  - Rule 7: Scope Authorized   │
                                   │  - Rule 8: Recipient Valid    │
                                   └───────────────┬───────────────┘
                                                   │
                                     [Valid] ──────┴─────► [Invalid]
                                        │                      │
                                        ▼                      ▼
                               Approval Permitted     HTTP 422 CONSENT_INVALID
```

Key guarantees:
1. **Live Revocation Enforcement:** If citizen revokes consent in `revenue_consents`, workflow immediately blocks approval with `CONSENT_INVALID`, even if `data_payload` claims `VALID`.
2. **Deterministic Expiration:** UTC comparison against authoritative expiration timestamp.
3. **Application Association:** Rejects cross-application consent reuse (Rule 2).

---

### 3.2 Magic-Byte Binary File Inspection (SEC-04)

Binary inspection is executed in `backend/app/core/security_utils.py` and enforced in `documents.py`:

```python
_MAGIC_SIGNATURES = {
    "application/pdf": b"%PDF-",
    "image/jpeg": b"\xFF\xD8\xFF",
    "image/jpg": b"\xFF\xD8\xFF",
    "image/png": b"\x89PNG\r\n\x1a\n",
}
```

- When a client uploads a file declaring `Content-Type: application/pdf` or named `.pdf`, the initial bytes are compared against `b"%PDF-"`.
- If a text file, binary script, or executable is renamed to `.pdf`, the upload is rejected with HTTP 422 `DOCUMENT_INVALID`:
  > *"File 'forged_proof.pdf' claims to be 'application/pdf' but binary signature does not match. Possible MIME type spoofing — upload rejected."*

---

### 3.3 SVG Preview XML Entity Sanitization (SEC-05)

To prevent Stored XSS or XML entity injection when rendering previews:
1. Dynamic fields (`citizen_name`, `doc_type`, `document_id`, `house_no`, `street`, `village`, `taluka`, `district`, `pincode`) pass through `sanitize_svg_text()`.
2. Escaping follows strict order:
   - `&` → `&amp;`
   - `<` → `&lt;`
   - `>` → `&gt;`
   - `"` → `&quot;`
   - `'` → `&#39;`
3. Illegal ASCII control characters (`\x00-\x08`, `\x0b`, `\x0c`, `\x0e-\x1f`, `\x7f`) are stripped.

---

### 3.4 Postal PIN Code Format Validation (SEC-09)

In `backend/app/services/data_validation_service.py`:
- Regex pattern: `^[1-9][0-9]{5}$`
- Validates:
  - Exactly 6 numeric digits.
  - First digit cannot be `0` (standard Indian PIN numbering system).
  - No alphabet characters, spaces, punctuation, or control characters.
- Evaluated for both `new_address.pincode` and `existing_address.pincode`.

---

### 3.5 Sorting Parameter Whitelisting

In `backend/app/repositories/application_repository.py`:
- Whitelisted attributes:
  ```python
  ALLOWED_SORT_COLUMNS = {
      "received_at",
      "updated_at",
      "priority",
      "status",
      "citizen_name",
      "application_id",
      "service_type",
  }
  ```
- Any unwhitelisted value (e.g. `__class__`, SQL fragments, unknown column names) safely defaults to `"received_at"`.

---

## 4. Verification & Automated Test Suite

A dedicated security test suite `backend/tests/test_phase09_step04_consent_input_sanitization.py` (26 test cases) was created and verified:

```
tests/test_phase09_step04_consent_input_sanitization.py
├── test_consent_db_revocation_overrides_client_payload      PASSED [ 3%]
├── test_consent_db_expiration_overrides_client_payload      PASSED [ 7%]
├── test_consent_db_application_mismatch_fails_rule_2        PASSED [11%]
├── test_consent_api_endpoint_uses_authoritative_sync        PASSED [15%]
├── test_magic_bytes_valid_pdf                               PASSED [19%]
├── test_magic_bytes_valid_png                               PASSED [23%]
├── test_magic_bytes_valid_jpeg                              PASSED [26%]
├── test_magic_bytes_spoofed_pdf_rejected                    PASSED [30%]
├── test_magic_bytes_spoofed_png_rejected                    PASSED [34%]
├── test_upload_api_rejects_spoofed_pdf                      PASSED [38%]
├── test_upload_api_accepts_genuine_pdf                      PASSED [42%]
├── test_filename_safety_valid                               PASSED [46%]
├── test_filename_safety_path_traversal                      PASSED [50%]
├── test_filename_safety_null_bytes                          PASSED [53%]
├── test_filename_safety_control_characters                  PASSED [57%]
├── test_filename_safety_excessive_length                    PASSED [61%]
├── test_upload_api_rejects_path_traversal_filename          PASSED [65%]
├── test_sanitize_svg_text_escapes_xml_special_characters    PASSED [69%]
├── test_sanitize_svg_text_strips_control_characters          PASSED [73%]
├── test_svg_preview_endpoint_escapes_xss_entities           PASSED [76%]
├── test_pincode_valid_formats                               PASSED [80%]
├── test_pincode_invalid_leading_zero                        PASSED [84%]
├── test_pincode_invalid_length                              PASSED [88%]
├── test_pincode_invalid_alphanumeric                        PASSED [92%]
├── test_application_sorting_whitelist_valid_columns         PASSED [96%]
└── test_application_sorting_whitelist_fallback_on_unwhitelisted_column PASSED [100%]
```

### Full Backend Regression Status:
```
================= 193 passed, 12 warnings in 82.96s (0:01:22) =================
```
- Total test suites executed: 11
- Total tests passed: **193 / 193 (100% pass rate)**
- Zero regressions introduced.

---

## 5. Next Steps — Phase 09 Roadmap

With Step 04 successfully completed, the remaining Phase 09 items proceed to:
- **Step 05: Transport & HTTP Security Headers Hardening**
  - Configure defensive middleware for `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Strict-Transport-Security`.
  - Perform comprehensive end-to-end security sign-off across all Phase 09 requirements.
