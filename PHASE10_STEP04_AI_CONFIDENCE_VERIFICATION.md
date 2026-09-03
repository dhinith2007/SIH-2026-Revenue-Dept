# Phase 10 — Step 04: AI Confidence & Intelligent Verification Recommendation Report
**GovMesh SIH26129 — Revenue & Forest Department of Maharashtra**

> **Mandatory Statutory Principle:** AI/OCR verification is assistive evidence analysis. It does not constitute or execute a statutory decision. The Revenue Officer remains the sole statutory decision-maker.

---

## 1. Objective

Phase 10 Step 04 implements an **explainable AI-assisted verification confidence engine** for document verification within the Revenue & Forest Department system.

The engine evaluates:
1. Provider OCR extraction confidence (`ocr_confidence`)
2. Field-level document/application comparison scores (`match_confidence`)
3. Critical-field mismatch indicators (`pincode`, `district`, `taluka`, `citizen_name`)
4. Document extraction status & evidence completeness
5. OCR/document quality signals and script differences

It produces:
- `overall_confidence` (weighted 0.0 to 1.0)
- `recommendation` band (`HIGH_CONFIDENCE_MATCH`, `MEDIUM_CONFIDENCE_REVIEW`, `LOW_CONFIDENCE_REVIEW`, `MISMATCH_REVIEW`, `INSUFFICIENT_EVIDENCE`)
- `evidence_quality` assessment (`COMPLETE`, `PARTIAL`, `INSUFFICIENT`, `FAILED`)
- Structured `risk_flags` list
- Human-readable decision `reasons`
- Clear statutory `officer_guidance`

---

## 2. Architecture & Provider-Independent Abstraction

The confidence engine follows a provider-independent architecture:

```
                            +------------------------------------+
                            | BaseVerificationConfidenceEngine   |
                            |               (ABC)                |
                            +------------------------------------+
                                              ^
               +------------------------------+------------------------------+
               |                                                             |
+------------------------------------------+               +-----------------------------------+
| RuleBasedVerificationConfidenceEngine    |               | FutureMLVerificationConfidenceEngine|
|      (Deterministic Offline)             |               |      (Future ML/AI Provider)      |
+------------------------------------------+               +-----------------------------------+
```

- **`BaseVerificationConfidenceEngine` (Abstract Base Class):** Defines `evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score, context)` returning `VerificationConfidenceResult`.
- **`RuleBasedVerificationConfidenceEngine` (Deterministic Implementation):** Completely offline, deterministic rule-based scoring engine operating without external ML/LLM/Cloud dependencies.
- **Future AI Boundary:** Cleanly designed so future ML models or Cloud AI providers can replace the rule-based evaluator without changing backend contracts or API schemas.

---

## 3. Input Signals & Weighting Model

The confidence engine consumes 7 distinct input signals:

| Input Signal | Description | Scoring Impact |
| :--- | :--- | :--- |
| **`ocr_confidence`** | Provider extraction accuracy score (0.0 to 1.0) | 35% base score weight; caps overall confidence if < 0.70. |
| **`match_confidence`** | Field comparison similarity score (0.0 to 1.0) | 65% base score weight; reflects name and address component alignment. |
| **Name Match Status** | `MATCH`, `PARTIAL_MATCH`, `MISMATCH`, `NOT_EXTRACTED` | Exact match boosts score; partial/script difference adds risk flag; mismatch forces `MISMATCH_REVIEW`. |
| **Address Component Statuses** | 6-part departmental address status (`house_no`, `street`, `village`, `taluka`, `district`, `pincode`) | Component matches contribute positively; street/village partial matches add risk flags. |
| **Critical Field Signals** | `pincode`, `district`, `taluka`, `citizen_name` | Mismatches in any of these 4 fields trigger **Critical Override Rules**, overriding positive signals. |
| **Evidence Completeness** | Number of extracted critical fields | Determines `evidence_quality` (`COMPLETE`, `PARTIAL`, `INSUFFICIENT`, `FAILED`). |
| **SHA-256 Fingerprint** | Binary hash of proof document | Provides audit trailing and tamper identification. |

---

## 4. Recommendation Bands & Thresholds

| Recommendation Band | Operational Meaning | Action Guidance for Revenue Officer |
| :--- | :--- | :--- |
| **`HIGH_CONFIDENCE_MATCH`** | All critical fields match cleanly; OCR confidence $\ge 0.75$; overall confidence $\ge 0.85$; zero risk flags. | *"Document evidence is highly consistent with application details. Proceed with standard officer statutory review."* |
| **`MEDIUM_CONFIDENCE_REVIEW`** | Overall confidence $\ge 0.70$; minor formatting, script differences, or moderate OCR quality. | *"Document evidence is generally consistent, but minor formatting, script, or confidence differences exist. Officer review required before approval."* |
| **`LOW_CONFIDENCE_REVIEW`** | Overall confidence $< 0.70$ or poor OCR quality. | *"Low confidence OCR extraction or data comparison observed. Thorough officer review of original document scan is required."* |
| **`MISMATCH_REVIEW`** | Mismatch detected in critical field (`pincode`, `district`, `taluka`, or `citizen_name`). | *"Critical discrepancy detected in supporting document evidence. Carefully verify physical proof document before taking statutory action."* |
| **`INSUFFICIENT_EVIDENCE`** | Document OCR failed, unreadable binary, or essential fields unextracted. | *"Supporting document lacks essential field data. Officer action required to request fresh proof copy or issue information request."* |

> **Statutory Safety Rule:** There is **NO** `AUTO_APPROVE` band. Every recommendation mandates Revenue Officer review.

---

## 5. Critical Field Override Rules

To prevent unsafe automated scoring, critical field mismatches dominate the recommendation regardless of other matching fields:

- **Pincode Mismatch:** e.g., Application `600095` vs Document `600096` -> Forces `MISMATCH_REVIEW`, `overall_confidence <= 0.40`, risk flag `"PINCODE_MISMATCH"`.
- **District Mismatch:** e.g., Application `Pune` vs Document `Nagpur` -> Forces `MISMATCH_REVIEW`, risk flag `"DISTRICT_MISMATCH"`.
- **Taluka Mismatch:** e.g., Application `Haveli` vs Document `Baramati` -> Forces `MISMATCH_REVIEW`, risk flag `"TALUKA_MISMATCH"`.
- **Citizen Name Mismatch:** e.g., Application `Rajesh Patil` vs Document `Suresh Kulkarni` -> Forces `MISMATCH_REVIEW`, risk flag `"NAME_MISMATCH"`.

---

## 6. OCR vs Match vs Overall Confidence Metric Separation

The architecture maintains 3 distinct metric fields in `DocumentVerificationResult`:

1. **`ocr_confidence`**: Measures how accurately the OCR engine extracted text from the binary image/PDF (e.g. `0.95`).
2. **`match_confidence`**: Measures data comparison similarity between extracted fields and requested application data (e.g. `0.90`).
3. **`overall_confidence`**: Weighted, risk-adjusted synthesis computed by the confidence engine (e.g. `0.92`).

These 3 metrics are never collapsed into a single opaque score.

---

## 7. Structured Risk Flags & Explainability

The engine produces structured `risk_flags` and human-readable `reasons`:

```json
{
  "ocr_confidence": 0.65,
  "match_confidence": 1.00,
  "overall_confidence": 0.72,
  "recommendation": "MEDIUM_CONFIDENCE_REVIEW",
  "evidence_quality": "COMPLETE",
  "risk_flags": [
    "OCR_LOW_CONFIDENCE"
  ],
  "reasons": [
    "OCR provider extraction confidence is below standard threshold (65%)."
  ],
  "officer_guidance": "Document evidence is generally consistent, but minor formatting, script, or confidence differences exist. Officer review required before approval."
}
```

Available Risk Flags:
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

## 8. Human-in-the-Loop & Statutory Safety Guarantees

1. **No Automatic State Mutations:** The confidence engine is strictly read-only and analytical. It cannot invoke `approve_application()`, `reject_application()`, or alter application workflow status.
2. **Statutory Approval Blocking:** Statutory approval endpoints (`POST /approve`) continue to block applications with un-overridden document mismatches (HTTP 422 `DOCUMENT_MISMATCH`).
3. **Officer Decision Primacy:** The Revenue Officer remains the sole statutory authority capable of approving, rejecting, requesting information, or executing manual overrides.

---

## 9. Security, DPDP & Audit Logging

- **Offline Execution:** Zero external API calls (No Gemini, OpenAI, Azure, or Textract calls).
- **DPDP Compliance:** Raw OCR text and citizen PII are excluded from audit logs and PostgreSQL JSON payloads.
- **Audit Distinctions:** Audit trail explicitly logs `OCR_COMPLETED` and `DOCUMENT_VERIFIED` recommendation events separately from `MANUAL_OVERRIDE` or officer approval actions.
- **RBAC & Isolation:** Enforces multi-tenant division isolation (403), read-only auditor restrictions (403), and finalized application immutability (409).

---

## 10. Comprehensive Test Matrix (`tests/test_phase10_step04_confidence.py`)

| Test Case | Scenario Evaluated | Expected Recommendation | Status |
| :--- | :--- | :--- | :---: |
| `test_high_confidence_recommendation` | All fields match cleanly; OCR conf 0.95 | `HIGH_CONFIDENCE_MATCH` | **PASS** |
| `test_medium_confidence_due_to_low_ocr_quality` | All fields match; OCR conf 0.65 | `MEDIUM_CONFIDENCE_REVIEW` | **PASS** |
| `test_insufficient_evidence_when_fields_missing` | All critical fields unextracted | `INSUFFICIENT_EVIDENCE` | **PASS** |
| `test_pincode_mismatch_triggers_mismatch_review` | PIN code mismatch (600095 vs 600096) | `MISMATCH_REVIEW` | **PASS** |
| `test_district_mismatch_triggers_mismatch_review` | District mismatch (Pune vs Nagpur) | `MISMATCH_REVIEW` | **PASS** |
| `test_name_mismatch_triggers_mismatch_review` | Citizen name mismatch | `MISMATCH_REVIEW` | **PASS** |
| `test_script_difference_triggers_medium_review` | English vs Devanagari script difference | `MEDIUM_CONFIDENCE_REVIEW` | **PASS** |
| `test_ocr_failure_yields_failed_quality_and_insufficient_evidence` | OCR status `FAILED` | `INSUFFICIENT_EVIDENCE` | **PASS** |
| `test_ocr_vs_match_vs_overall_confidence_metrics_distinct` | Metric separation validation | All 3 metrics distinct | **PASS** |
| `test_confidence_engine_determinism` | Identical inputs tested twice | 100% Identical outputs | **PASS** |
| `test_confidence_engine_never_causes_statutory_approval` | Application approval on mismatched document | Blocked (HTTP 422) | **PASS** |
| `test_cross_division_officer_cannot_trigger_ocr_verification` | Cross-division access | Blocked (HTTP 403) | **PASS** |
| `test_auditor_read_only_restriction` | Auditor mutation attempt | Blocked (HTTP 403) | **PASS** |
| `test_finalized_application_document_override_blocked` | Override on finalized application | Blocked (HTTP 409) | **PASS** |

---

## 11. Files Changed

1. [`backend/app/services/ocr/confidence_engine.py`](file:///d:/SIH%202026/revenue-department/backend/app/services/ocr/confidence_engine.py): Created `BaseVerificationConfidenceEngine`, `RuleBasedVerificationConfidenceEngine`, and `VerificationConfidenceResult`.
2. [`backend/app/schemas/workflow.py`](file:///d:/SIH%202026/revenue-department/backend/app/schemas/workflow.py): Extended `DocumentVerificationResult` with `ocr_confidence`, `match_confidence`, `overall_confidence`, `recommendation`, `evidence_quality`, `risk_flags`, `reasons`, `officer_guidance`, `score_breakdown`.
3. [`backend/app/services/document_verification_service.py`](file:///d:/SIH%202026/revenue-department/backend/app/services/document_verification_service.py): Integrated confidence engine evaluation in `verify_document`.
4. [`backend/app/api/v1/endpoints/documents.py`](file:///d:/SIH%202026/revenue-department/backend/app/api/v1/endpoints/documents.py): Removed raw `bytes` from `doc_dict` payload to ensure 100% JSON serializability.
5. [`backend/app/repositories/application_repository.py`](file:///d:/SIH%202026/revenue-department/backend/app/repositories/application_repository.py): Filtered raw `bytes` in `attach_document` for PostgreSQL safety.
6. [`backend/tests/test_phase10_step04_confidence.py`](file:///d:/SIH%202026/revenue-department/backend/tests/test_phase10_step04_confidence.py): Created 14 automated unit and integration tests.
7. [`PHASE10_STEP04_AI_CONFIDENCE_VERIFICATION.md`](file:///d:/SIH%202026/revenue-department/PHASE10_STEP04_AI_CONFIDENCE_VERIFICATION.md): Completion report.

---

## 12. Full Phase 10 Regression Results

```bash
python -m pytest tests/test_phase10_step02_ocr.py tests/test_phase10_step03_matching.py tests/test_phase10_step04_confidence.py
# Result: 60 passed in 4.18s
```

- **Step 02 OCR Engine Factory:** 21 / 21 Passed
- **Step 03 Bilingual Matcher:** 25 / 25 Passed
- **Step 04 AI Confidence Engine:** 14 / 14 Passed
- **Total Phase 10 Suite:** **60 / 60 PASSED (100% Pass Rate)**

---

## 13. Hard Stop Boundary

- Phase 10 Step 04 is complete.
- Phase 10 Step 05 (*Asynchronous Processing & Failure Resilience*) has **not** been initiated.
