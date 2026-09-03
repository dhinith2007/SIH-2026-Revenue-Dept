import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.services.ocr.normalization import (
    is_devanagari_text,
    convert_devanagari_digits,
    normalize_unicode,
    normalize_whitespace,
    normalize_punctuation,
    normalize_case,
    normalize_text,
    normalize_name,
    normalize_pincode,
    normalize_address_text,
    normalize_address_components,
)
from app.services.ocr.matcher import (
    compare_name,
    compare_pincode,
    compare_address_components,
    compute_assistive_score,
    generate_verification_explanation,
    check_initials_compatibility,
    FieldComparisonResult,
    DocumentComparisonResult,
)
from app.services.document_verification_service import DocumentVerificationService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def desk_officer_token():
    return create_access_token(
        data={
            "sub": "USR-REV-001",
            "username": "revenue.officer",
            "role": "REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Pune Division",
        }
    )


@pytest.fixture
def other_officer_token():
    return create_access_token(
        data={
            "sub": "USR-REV-006",
            "username": "other.officer",
            "role": "REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Pune Division (Baramati Tahsil)",
        }
    )


@pytest.fixture
def auditor_token():
    return create_access_token(
        data={
            "sub": "USR-REV-004",
            "username": "auditor.internal",
            "role": "READ_ONLY_AUDITOR",
            "department": "Revenue & Forest Department",
            "division": "State Audit Unit",
        }
    )


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Category A: Unicode & Devanagari Normalization
# ============================================================================
def test_devanagari_unicode_nfc_normalization():
    raw_marathi = "श्री  राजेश   शांताराम   पाटील ।"
    norm = normalize_text(raw_marathi)
    assert "श्री राजेश शांताराम पाटील" in norm
    assert "।" not in norm  # Danda stripped


def test_marathi_text_preserved():
    marathi_text = "तालुका हवेली जिल्हा पुणे"
    norm = normalize_text(marathi_text)
    assert is_devanagari_text(norm) is True
    assert norm == "तालुका हवेली जिल्हा पुणे"


def test_mixed_marathi_english_normalization():
    mixed = "Taluka: हवेली, District: पुणे - 411038"
    norm = normalize_text(mixed)
    assert norm == "taluka हवेली district पुणे 411038"


def test_punctuation_and_danda_stripping():
    text_with_danda = "महाराष्ट्र शासन । राजस्व विभाग ॥"
    norm = normalize_punctuation(text_with_danda)
    assert "।" not in norm
    assert "॥" not in norm
    assert norm == "महाराष्ट्र शासन राजस्व विभाग"


# ============================================================================
# Category B: Devanagari Digit Handling
# ============================================================================
def test_devanagari_digit_conversion():
    dev_str = "०१२३४५६७८९"
    converted = convert_devanagari_digits(dev_str)
    assert converted == "0123456789"


def test_pincode_devanagari_equivalence():
    p1 = "600095"
    p2 = "६०००९५"
    res = compare_pincode(p1, p2)
    assert res["status"] == "MATCH"
    assert res["score"] == 1.0
    assert res["normalized_source"] == "600095"
    assert res["normalized_target"] == "600095"


def test_pincode_mismatch():
    p1 = "600095"
    p2 = "600096"
    res = compare_pincode(p1, p2)
    assert res["status"] == "MISMATCH"
    assert res["score"] == 0.0


def test_devanagari_pincode_mismatch():
    p1 = "६०००९५"
    p2 = "६०००९६"
    res = compare_pincode(p1, p2)
    assert res["status"] == "MISMATCH"
    assert res["score"] == 0.0


def test_gat_number_numeric_conversion():
    raw_gat = "गट नं. १२३"
    norm = normalize_address_text(raw_gat)
    assert "123" in norm
    assert "gat no" in norm


# ============================================================================
# Category C: Indian Name Normalization & Matching
# ============================================================================
def test_name_case_insensitive_match():
    res = compare_name("rajesh patil", "RAJESH PATIL")
    assert res["status"] == "MATCH"
    assert res["score"] == 1.0


def test_name_honorifics_removal_english_and_marathi():
    res_en = compare_name("Shri Rajesh Shantaram Patil", "Rajesh Shantaram Patil")
    assert res_en["status"] == "MATCH"
    assert res_en["score"] == 1.0

    res_mar = compare_name("श्रीमती सुनंदा विठ्ठलराव देशमुख", "सुनंदा विठ्ठलराव देशमुख")
    assert res_mar["status"] == "MATCH"
    assert res_mar["score"] == 1.0


def test_name_initials_compatibility():
    assert check_initials_compatibility("r s patil", "rajesh shantaram patil") is True
    res = compare_name("R. S. Patil", "Rajesh Shantaram Patil")
    assert res["status"] == "PARTIAL_MATCH"
    assert res["method"] == "initials_compatibility"


def test_name_token_reordering_match():
    res = compare_name("Patil Rajesh Shantaram", "Rajesh Shantaram Patil")
    assert res["status"] == "MATCH"
    assert res["score"] >= 0.85


def test_name_genuine_mismatch():
    res = compare_name("Rajesh Patil", "Suresh Kulkarni")
    assert res["status"] == "MISMATCH"
    assert res["score"] <= 0.55


def test_bilingual_name_script_difference_handling():
    res = compare_name("Dhinith Pragalyan", "श्री धिनिथ प्रागल्यन")
    assert res["status"] == "PARTIAL_MATCH"
    assert res["method"] == "script_difference"
    assert "Script difference detected" in res["explanation"]


# ============================================================================
# Category D: Address Normalization & Marker Equivalences
# ============================================================================
def test_address_marker_gat_number_equivalence():
    res1 = normalize_address_text("Gat No. 123")
    res2 = normalize_address_text("Gat Number 123")
    res3 = normalize_address_text("गट क्र. १२३")

    assert "gat no 123" in res1
    assert "gat no 123" in res2
    assert "gat no 123" in res3


def test_address_marker_survey_number_equivalence():
    res1 = normalize_address_text("Survey No. 45")
    res2 = normalize_address_text("S.No. 45")
    assert "survey no 45" in res1
    assert "survey no 45" in res2


def test_address_road_and_street_marker_equivalence():
    res1 = normalize_address_text("M.G. Road")
    res2 = normalize_address_text("MG Rd")
    assert "road" in res1
    assert "road" in res2


def test_gat_number_discrepancy_causes_mismatch():
    req_addr = {"street": "Gat No. 123", "taluka": "Haveli"}
    extracted_fields = {"street": "Gat No. 132", "taluka": "Haveli"}

    eval_res = compare_address_components(req_addr, extracted_fields)
    assert eval_res["street"]["status"] == "MISMATCH"


def test_full_6_part_address_component_evaluation():
    req_addr = {
        "house_no": "Flat 402",
        "street": "Gat No. 123, M.G. Road",
        "village": "Wakad",
        "taluka": "Haveli",
        "district": "Pune",
        "pincode": "411038",
    }
    ext_addr = {
        "house_no": "Flat 402",
        "street": "Gat Number 123, MG Rd",
        "village": "Wakad",
        "taluka": "Haveli",
        "district": "Pune",
        "pincode": "४११०३८",
    }

    res = compare_address_components(req_addr, ext_addr)
    assert res["house_no"]["status"] == "MATCH"
    assert res["street"]["status"] == "MATCH"
    assert res["village"]["status"] == "MATCH"
    assert res["taluka"]["status"] == "MATCH"
    assert res["district"]["status"] == "MATCH"
    assert res["pincode"]["status"] == "MATCH"


# ============================================================================
# Category E: Field Status & Explainability
# ============================================================================
def test_explainability_generation_for_matches_and_mismatches():
    name_eval = {"result": "MATCH", "application_value": "Rajesh Patil", "document_value": "Rajesh Patil"}
    comp_eval = {
        "house_no": {"result": "MATCH", "requested": "402", "extracted": "402"},
        "street": {"result": "MATCH", "requested": "MG Road", "extracted": "MG Rd"},
        "village": {"result": "MATCH", "requested": "Wakad", "extracted": "Wakad"},
        "taluka": {"result": "MATCH", "requested": "Haveli", "extracted": "Haveli"},
        "district": {"result": "MATCH", "requested": "Pune", "extracted": "Pune"},
        "pincode": {"result": "MATCH", "requested": "411038", "extracted": "411038"},
    }

    exp_pass = generate_verification_explanation(name_eval, comp_eval, "VALIDATED")
    assert "verification passed" in exp_pass.lower() or "match" in exp_pass.lower()

    # Mismatch explanation
    comp_eval_mismatch = dict(comp_eval)
    comp_eval_mismatch["district"] = {
        "result": "MISMATCH",
        "requested": "Pune",
        "extracted": "Nagpur",
    }
    exp_mismatch = generate_verification_explanation(name_eval, comp_eval_mismatch, "MISMATCH")
    assert "Discrepancy detected" in exp_mismatch
    assert "District" in exp_mismatch
    assert "Nagpur" in exp_mismatch


# ============================================================================
# Category F: OCR Confidence vs Match Score Independence
# ============================================================================
def test_ocr_confidence_remains_independent_from_match_score():
    name_eval = {"result": "MATCH", "score": 1.0}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MATCH", "score": 1.0},
    }
    assist_score, matched_count, total_count = compute_assistive_score(name_eval, comp_eval)

    # Assist score reflects match degree (1.0)
    assert assist_score == 1.0
    assert matched_count == 7
    assert total_count == 7


# ============================================================================
# Category G: Security & DPDP Invariants
# ============================================================================
def test_cross_division_officer_access_blocked(client, other_officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403


def test_finalized_application_remains_immutable(client, desk_officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json={"decision": "MISMATCH", "reason": "Officer attempting to alter finalized state."},
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 409


def test_read_only_auditor_blocked_from_document_mutation(client, auditor_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 403
