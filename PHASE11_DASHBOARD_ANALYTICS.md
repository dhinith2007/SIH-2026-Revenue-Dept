# Phase 11 — Dashboard & Analytics Documentation
**GovMesh SIH26129 — Revenue & Forest Department of Maharashtra**

> **Statutory Principle:** AI/OCR metrics are assistive evidence analytics. They do not constitute statutory decisions. Final decisions remain the responsibility of the authorized Revenue Officer.

---

## 1. Executive Summary

Phase 11 implements a secure, backend-authoritative **Revenue Department Dashboard & Analytics Layer** for the Maharashtra Revenue & Forest Department (`ADDRESS_CHANGE` MVP workflow).

The dashboard provides Revenue Officers and authorized departmental administrators with operational visibility into application queues, daily application trends, document verification rates, local OCR performance, AI confidence distributions, evidence risk flags, officer workloads, and recent audit activity streams.

---

## 2. Dashboard Architecture

The architecture enforces strict backend authority. No raw application lists or documents are fetched into the browser to compute statistics locally.

```
+--------------------------+     +-------------------------------+     +--------------------------------+
| Client / Frontend UI     | --> | Analytics Endpoint            | --> | Analytics Service              |
| (React + DashboardPage)  |     | GET /api/v1/analytics/dashboard |   | (Backend Scoping & Aggregation)|
+--------------------------+     +-------------------------------+     +--------------------------------+
                                                                                       |
                                                                                       v
                                                                       +--------------------------------+
                                                                       | Repositories (PostgreSQL & Mem)|
                                                                       | App, Evidence, Audit           |
                                                                       +--------------------------------+
```

---

## 3. Analytics APIs Exposed (`/api/v1/analytics/`)

| Endpoint | Method | Response Schema | Description |
| :--- | :---: | :--- | :--- |
| `/api/v1/analytics/dashboard` | `GET` | `FullDashboardAnalyticsResponse` | Complete backend-authoritative dashboard metrics package |
| `/api/v1/analytics/summary` | `GET` | `AnalyticsSummaryKPI` | Core operational KPI counters |
| `/api/v1/analytics/trends` | `GET` | `AnalyticsTrendsResponse` | Time-series daily aggregation (`7d`, `30d`, `90d`) |
| `/api/v1/analytics/verification` | `GET` | `VerificationAnalyticsResponse` | Proof document verification & OCR performance |
| `/api/v1/analytics/confidence` | `GET` | `ConfidenceAnalyticsResponse` | AI recommendation bands distribution |
| `/api/v1/analytics/risks` | `GET` | `RiskAnalyticsResponse` | Structured evidence risk flag frequency |

---

## 4. KPI Definitions

- **Total Applications:** Count of applications in the authorized division scope.
- **Pending Applications:** Status `PENDING` (Awaiting scrutiny).
- **Under Review:** Status `PROCESSING` (Officer actively scrutinizing).
- **Info Requested:** Status `ACTION_REQUIRED` (Query raised to citizen).
- **Approved:** Status `VERIFIED` / `COMPLETED` (Statutorily approved by officer).
- **Rejected:** Status `REJECTED` (Rejected by officer).
- **Doc Verification Pending:** Attached proof documents awaiting verification.
- **Review Required:** Applications with low AI confidence, mismatches, or active risk flags.

---

## 5. Application Status Analytics

Authoritative breakdown across system state machine:
- `PENDING`
- `PROCESSING`
- `ACTION_REQUIRED`
- `VERIFIED`
- `REJECTED`
- `FAILED` / `QUEUED`

Includes exact count and percentage distribution.

---

## 6. Time-Series Trend Analytics

Daily time-series aggregation over configurable time windows (`7`, `30`, `90` days):
- `date` ("YYYY-MM-DD")
- `incoming`: Submitted applications count
- `approved`: Statutorily approved applications count
- `rejected`: Rejected applications count

All date comparisons use timezone-aware UTC datetime bounds to eliminate offset-naive errors.

---

## 7. Document Verification & OCR Analytics

Metrics derived from persisted `DocumentVerificationRecord` entities:
- Total Proof Documents
- Verified Proof Documents
- Pending Proof Documents
- OCR Success Rate (%)
- Average OCR Confidence (%)
- Average Field Match Confidence (%)
- Average Overall Confidence (%)

Does NOT re-run OCR or mutate document evidence records.

---

## 8. AI Confidence Analytics

Consumes authoritative Phase 10 recommendation bands:
- `HIGH_CONFIDENCE_MATCH`
- `MEDIUM_CONFIDENCE_REVIEW`
- `LOW_CONFIDENCE_REVIEW`
- `MISMATCH_REVIEW`
- `INSUFFICIENT_EVIDENCE`

Consumes evidence quality levels: `COMPLETE`, `PARTIAL`, `INSUFFICIENT`, `FAILED`.

---

## 9. Risk & Discrepancy Analytics

Tracks structured risk flags across all documents in scope:
- `OCR_LOW_CONFIDENCE`
- `NAME_PARTIAL_MATCH`
- `NAME_MISMATCH`
- `PINCODE_MISMATCH`
- `DISTRICT_MISMATCH`
- `TALUKA_MISMATCH`
- `VILLAGE_MISMATCH`
- `MISSING_CRITICAL_FIELD`
- `OCR_FAILED`
- `SCRIPT_DIFFERENCE`
- `DOCUMENT_REFERENCE_MISMATCH`

---

## 10. Officer Workload Analytics

Operational workload distribution scoped to authorized division:
- Officer ID & Full Name
- Assigned Applications Count
- Pending Scrutiny Count
- Completed Statutory Decisions Count

---

## 11. Security & RBAC Enforcement

- **Authentication Required:** All analytics endpoints require valid JWT (`HTTP 401` if unauthenticated).
- **Division Isolation:** Analytics Service filters applications strictly by user division (`Pune Division`, `Baramati Tahsil`). Cross-division analytics access is blocked.
- **Auditor Access:** Read-only viewing permitted without statutory mutation capabilities.

---

## 12. Data Privacy & Data Minimization (DPDP Compliance)

Analytics responses expose **aggregate counts, percentages, and operational metadata only**. Personal Identifiable Information (PII), raw document binary bytes, and citizen secret records are completely omitted from analytics payloads.

---

## 13. Frontend Implementation

Updated [`frontend/src/pages/DashboardPage.tsx`](file:///d:/SIH%202026/revenue-department/frontend/src/pages/DashboardPage.tsx):
- Statutory AI/OCR Disclaimer Banner
- Server-Side Analytics Filters Bar (`Time Range`, `Status`, `Recommendation Band`, `Risk Flag`)
- Primary KPI Cards Grid
- Processing Trends Daily Table & Status Distribution Progress Bars
- Document Verification & Local OCR Performance Grid
- Recommendation Bands & Risk Flags Breakdown Cards
- Operational Officer Workload Distribution Table
- Recent Applications Scrutiny Queue Table
- GovMesh Interoperability & System Indicators Bar
- SIH Demonstration Failure Simulator Controls

---

## 14. Testing Matrix

### Backend Tests (`backend/tests/test_phase11_analytics.py`)
| Test | Objective | Status |
| :--- | :--- | :---: |
| `test_full_dashboard_analytics_authenticated` | Full analytics payload structure & statutory disclaimer | **PASS** |
| `test_analytics_summary_kpi` | Summary KPI endpoint | **PASS** |
| `test_analytics_trends_date_window` | 30-day time series aggregation | **PASS** |
| `test_analytics_verification_and_ocr` | OCR & document verification metrics | **PASS** |
| `test_analytics_confidence_and_risks` | Recommendation bands & risk flags | **PASS** |
| `test_analytics_unauthenticated_blocked` | Unauthenticated HTTP 401 protection | **PASS** |
| `test_analytics_cross_division_isolation` | Cross-division RBAC scoping | **PASS** |

### Frontend Vitest (`frontend/src/tests/Dashboard.test.tsx`)
| Test | Objective | Status |
| :--- | :--- | :---: |
| `renders full dashboard analytics...` | Disclaimer banner, KPI cards, filter bar, and workload tables | **PASS** |

---

## 15. Full Regression Results

### Backend Pytest Suite
```bash
python -m pytest tests/test_phase06_documents.py tests/test_phase10_step02_ocr.py tests/test_phase10_step03_matching.py tests/test_phase10_step04_confidence.py tests/test_phase10_step06_hardening.py tests/test_phase09_auth_security.py tests/test_phase09_rbac_document_security.py tests/test_phase09_step04_consent_input_sanitization.py tests/test_phase09_step05_http_security.py tests/test_phase11_analytics.py
# Result: 205 / 205 PASSED (100%) in 26.78s
```

### Frontend Vitest Suite
```bash
npx vitest run --pool=forks
# Result: 21 / 21 PASSED (100%) across 7 test files
```

### Frontend Production Build
```bash
npm run build
# Result: tsc -b && vite build SUCCEEDED cleanly in 2.19s
```

---

## 16. Files Changed in Phase 11

1. [`backend/app/schemas/analytics.py`](file:///d:/SIH%202026/revenue-department/backend/app/schemas/analytics.py): New Pydantic analytics schemas.
2. [`backend/app/services/analytics_service.py`](file:///d:/SIH%202026/revenue-department/backend/app/services/analytics_service.py): New Analytics Service for backend-authoritative calculation.
3. [`backend/app/api/v1/endpoints/analytics.py`](file:///d:/SIH%202026/revenue-department/backend/app/api/v1/endpoints/analytics.py): New Analytics API router.
4. [`backend/app/api/v1/router.py`](file:///d:/SIH%202026/revenue-department/backend/app/api/v1/router.py): Registered analytics router.
5. [`backend/app/api/deps.py`](file:///d:/SIH%202026/revenue-department/backend/app/api/deps.py): Added `get_analytics_service` factory.
6. [`frontend/src/types/application.ts`](file:///d:/SIH%202026/revenue-department/frontend/src/types/application.ts): Added Phase 11 analytics TypeScript interfaces.
7. [`frontend/src/services/api.ts`](file:///d:/SIH%202026/revenue-department/frontend/src/services/api.ts): Added `getFullDashboardAnalytics` method.
8. [`frontend/src/pages/DashboardPage.tsx`](file:///d:/SIH%202026/revenue-department/frontend/src/pages/DashboardPage.tsx): Updated Dashboard UI with full analytics sections.
9. [`backend/tests/test_phase11_analytics.py`](file:///d:/SIH%202026/revenue-department/backend/tests/test_phase11_analytics.py): Created backend analytics tests.
10. [`frontend/src/tests/Dashboard.test.tsx`](file:///d:/SIH%202026/revenue-department/frontend/src/tests/Dashboard.test.tsx): Created frontend dashboard tests.
11. [`PHASE11_DASHBOARD_ANALYTICS.md`](file:///d:/SIH%202026/revenue-department/PHASE11_DASHBOARD_ANALYTICS.md): Phase 11 documentation.

---

## 17. Remaining Known Limitations

- All analytics are computed dynamically backend-side without modifying stored data or triggering AI statutory decision capabilities.

---

## 18. Final Verdict

# PASS
