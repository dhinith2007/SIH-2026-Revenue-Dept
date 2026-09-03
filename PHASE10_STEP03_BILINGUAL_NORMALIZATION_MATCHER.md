# Phase 10 — Step 03: Devanagari / Bilingual Normalization & Enhanced Document Matcher Report
**GovMesh SIH26129 — Revenue & Forest Department of Maharashtra**

> **Mandatory Statutory Principle:** Document comparison is assistive evidence analysis and does not make the statutory decision. The existing Revenue Officer remains the sole statutory authority.

---

## 1. Objective

Phase 10 Step 03 upgrades the OCR normalization and document comparison layers to handle real-world Maharashtra revenue document variations:
- Marathi / Devanagari script text
- English script text
- Mixed Marathi + English documents
- Devanagari numerals (०-९)
- Indian address structure and marker variations (Gat No, Survey No, S.No, Plot No, Chawl, Wadi, Rd/Road)
- Indian name variations (honorifics, initials, token reordering, bilingual script differences)
- Formatting and OCR noise (whitespace, newlines, dandas । ॥, dashes)

The architecture retains **Original OCR Evidence** intact while creating a distinct **Normalized Comparison Representation** for explainable matching.

---

## 2. Existing Matcher vs Enhanced Step 03 Architecture

| Architectural Dimension | Pre-Step 03 Baseline | Phase 10 Step 03 Enhanced Architecture |
| :--- | :--- | :--- |
| **Normalization Pipeline** | Single-pass regex lowercasing & basic danda stripping. | Modular pipeline: Unicode NFC, case, whitespace, punctuation, Devanagari digit conversion, address marker equivalences. |
| **Devanagari Numerals** | Treated as general Devanagari string characters. | Translated (०-९ -> 0-9) for **numeric comparison only**. Original evidence remains unchanged. |
| **Name Normalization** | Basic honorific stripping (Shri, Smt, श्री). | Comprehensive English & Marathi honorific removal (Shri, Smt, Mr, Mrs, Late, Kumari, Adv, श्री, श्रीमती, सौ, कु, कै, डॉ, माननीय), initials matching, and script difference detection. |
| **Address Normalization** | Simple substring containment checks. | Component-aware 6-part matching (`house_no`, `street`, `village`, `taluka`, `district`, `pincode`), address marker equivalences (Gat No / Survey No / Rd / St), number discrepancy guards. |
| **PIN Code Matching** | Basic substring extraction. | Strict 6-digit PIN matching with Devanagari numeral translation. Mismatched digits trigger explicit `MISMATCH`. |
| **Script Differences** | No explicit script difference detection. | Explicit `script_difference` detection returning `PARTIAL_MATCH` with clear rationale, avoiding false automatic equivalence. |
| **Result Structure** | Dict with basic match status and scores. | Backward-compatible `FieldComparisonResult` & `DocumentComparisonResult` structured models with human-readable rationale. |

---

## 3. Normalization Architecture

The normalization pipeline preserves the original raw OCR evidence while deriving a comparison representation:

```
Original OCR Value (Preserved Intact)
        ↓
1. Unicode NFC Normalization (unicodedata.normalize("NFC", text))
        ↓
2. Case Normalization (Lowercase Latin; Devanagari intact)
        ↓
3. Devanagari Numeral Translation (०१२३४५६७८९ -> 0123456789 for numbers)
        ↓
4. Address Marker / Honorific Normalization (Gat No, Survey No, Shri, श्रीमती)
        ↓
5. Punctuation & Whitespace Collapsing (Danda removal, extra spaces)
        ↓
Normalized Comparison Value
```

---

## 4. Unicode / Marathi & Mixed-Language Support

- **Devanagari Preservation:** Devanagari characters (Unicode range U+0900 to U+097F) are preserved without ASCII transliteration or character replacement. "पुणे" remains "पुणे".
- **Mixed-Language Documents:** Fields containing both Latin and Devanagari tokens (e.g. "Taluka: हवेली, District: पुणे - 411038") normalize cleanly without dropping either script.
- **Danda Removal:** Punctuation stripping removes ASCII punctuation and Devanagari dandas (`।` U+0964, `॥` U+0965) while preserving valid words and numbers.

---

## 5. Devanagari Numeral & Pincode Handling

- **Numeric Translation:** Devanagari digits `०१२३४५६७८९` translate to `0123456789` strictly for numeric comparison functions (`convert_devanagari_digits`).
- **PIN Code Strictness:**
  - `600095` vs `६०००९५` -> `MATCH` (Score 1.0, method `"devanagari_numeral_equivalence"`).
  - `600095` vs `600096` -> `MISMATCH` (Score 0.0, method `"strict_pincode_mismatch"`).
- **Validation Standard:** Enforces Indian Postal PIN code format (`^[1-9][0-9]{5}$`).

---

## 6. Name & Address Matching Improvements

### 6.1 Name Matching (`compare_name`)
- **Honorific Removal:** English (`Shri`, `Smt`, `Mr`, `Mrs`, `Late`, `Kumari`, `Adv`) and Marathi (`श्री`, `श्रीमती`, `सौ`, `कु`, `कै`, `डॉ`, `माननीय`).
- **Initials Compatibility:** `"R. S. Patil"` vs `"Rajesh Shantaram Patil"` -> `PARTIAL_MATCH` (`method="initials_compatibility"`).
- **Bilingual Script Difference:** `"Dhinith Pragalyan"` vs `"श्री धिनिथ प्रागल्यन"` -> `PARTIAL_MATCH` (`method="script_difference"`), returning explicit statutory rationale requiring officer scrutiny.

### 6.2 Address Matching (`compare_address_components`)
- **Address Markers:** Equivalence maps for `Gat No` / `Gat Number` / `गट क्र.`, `Survey No` / `S.No.` / `सर्व्हे नं.`, `Plot No` / `प्लॉट नं.`, `Road` / `Rd`, `Street` / `St`, `Chawl` / `चाळ`, `Wadi` / `वाडी`.
- **Number Discrepancy Guard:** `Gat No. 123` vs `Gat No. 132` -> `MISMATCH` (detects digit mismatch even if text string similarity is high).

---

## 7. Match Result Contract & Explainability

Comparison outputs provide explainable rationale for Revenue Officers:

```json
{
  "field": "pincode",
  "status": "MATCH",
  "score": 1.0,
  "method": "devanagari_numeral_equivalence",
  "explanation": "PIN code matched exactly after Devanagari numeral conversion."
}
```

```json
{
  "field": "citizen_name",
  "status": "PARTIAL_MATCH",
  "score": 0.50,
  "method": "script_difference",
  "explanation": "Script difference detected: Application name is in English while document name is in Devanagari. Automatic transliteration skipped for statutory safety; officer verification required."
}
```

---

## 8. Separation of OCR Confidence vs Match Score

- **OCR Confidence:** Represents provider extraction accuracy (e.g. `ocr_raw.overall_confidence = 0.95`).
- **Match Score:** Represents similarity between extracted evidence and application data (e.g. `assistive_score = 1.0`).
- **Independence Guarantee:** Both metrics remain distinct attributes in `DocumentVerificationResult` and are never combined into an opaque score.

---

## 9. Security, DPDP & Performance Guarantees

1. **Local Offline Execution:** Zero external API or cloud AI calls.
2. **DPDP Compliance:** Raw document binaries and citizen PII are excluded from audit log traces.
3. **Multi-Tenant Authorization:** Retains Phase 09 RBAC controls, cross-division access restrictions (403), and finalized application immutability (409).
4. **Performance:** Linear execution time ($O(N)$ token comparison) with zero exponential loops or unbounded recursions.

---

## 10. Automated Test Matrix (`tests/test_phase10_step03_matching.py`)

| Test Category | Test Cases | Purpose & Verification | Status |
| :--- | :--- | :--- | :---: |
| **A. Unicode & Normalization** | `test_devanagari_unicode_nfc_normalization`, `test_marathi_text_preserved`, `test_mixed_marathi_english_normalization`, `test_punctuation_and_danda_stripping` | Validates Devanagari NFC normalization, danda stripping, and Marathi script preservation. | **PASS** |
| **B. Devanagari Digits** | `test_devanagari_digit_conversion`, `test_pincode_devanagari_equivalence`, `test_pincode_mismatch`, `test_devanagari_pincode_mismatch`, `test_gat_number_numeric_conversion` | Tests conversion of ०-९ to 0-9, strict PIN code comparison, and numeric Gat No extraction. | **PASS** |
| **C. Indian Name Matching** | `test_name_case_insensitive_match`, `test_name_honorifics_removal_english_and_marathi`, `test_name_initials_compatibility`, `test_name_token_reordering_match`, `test_name_genuine_mismatch`, `test_bilingual_name_script_difference_handling` | Validates honorific removal, initials compatibility, token reordering, and bilingual script difference handling. | **PASS** |
| **D. Address Matching** | `test_address_marker_gat_number_equivalence`, `test_address_marker_survey_number_equivalence`, `test_address_road_and_street_marker_equivalence`, `test_gat_number_discrepancy_causes_mismatch`, `test_full_6_part_address_component_evaluation` | Tests address marker equivalences (Gat/Survey/Rd/St) and number discrepancy detection. | **PASS** |
| **E. Explainability** | `test_explainability_generation_for_matches_and_mismatches` | Verifies human-readable explanations match actual match rationale. | **PASS** |
| **F. Metric Independence** | `test_ocr_confidence_remains_independent_from_match_score` | Confirms OCR confidence and match score remain separate. | **PASS** |
| **G. Security Invariants** | `test_cross_division_officer_access_blocked`, `test_finalized_application_remains_immutable`, `test_read_only_auditor_blocked_from_document_mutation` | Verifies RBAC, cross-division boundaries (403), and immutable state guards (409). | **PASS** |

---

## 11. Files Changed

1. `backend/app/services/ocr/normalization.py`: Added `convert_devanagari_digits`, `normalize_unicode`, `normalize_whitespace`, `normalize_punctuation`, `normalize_case`, `normalize_address_text`, and updated `ADDRESS_MARKERS_MAP`.
2. `backend/app/services/ocr/matcher.py`: Added `FieldComparisonResult`, `DocumentComparisonResult`, `check_initials_compatibility`, `compare_pincode`, number discrepancy detection, and script difference rationale.
3. `backend/app/services/document_verification_service.py`: Updated `verify_document` to incorporate explicit PIN code mismatch handling and enhanced component match statuses.
4. `backend/tests/test_phase10_step03_matching.py`: Created 25 automated unit and integration tests.
5. `PHASE10_STEP03_BILINGUAL_NORMALIZATION_MATCHER.md`: Step 03 completion report.

---

## 12. Known Limitations & Future Step 04 Boundary

- **Cross-Script Transliteration:** Step 03 intentionally avoids automatic phonetic transliteration between English and Devanagari to avoid statutory false positives. Step 04 will introduce structured confidence recommendation boundaries.
- **Hard Stop:** Phase 10 Step 03 is complete. Step 04 has not been initiated.
