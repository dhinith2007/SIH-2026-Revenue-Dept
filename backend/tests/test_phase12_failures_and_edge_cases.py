import io
import math
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.services.auth_service import create_access_token
from app.services.ocr.normalization import normalize_name, convert_devanagari_digits
from app.services.ocr.matcher import compare_pincode, check_initials_compatibility
from app.services.ocr.confidence_engine import RuleBasedVerificationConfidenceEngine, OCRRawResult
from app.services.ocr.simulated_provider import SimulatedOCRProvider

client = TestClient(app)


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


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


# ============================================================================
# 1. Document Upload & Storage Failure Simulations
# ============================================================================
def test_doc_failure_path_traversal_rejected(desk_officer_token):
    pdf_bytes = b"%PDF-1.4 Test PDF for security path traversal check"
    files = {"file": ("../../../../etc/passwd.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/revenue/application/GM-2026-000125/documents", files=files, headers=auth_header(desk_officer_token))
    assert res.status_code == 422
    assert "Invalid document filename" in res.json()["error"]["message"]


def test_doc_failure_unsupported_mime_rejected(desk_officer_token):
    exe_bytes = b"MZExecutableBinaryData"
    files = {"file": ("malicious_script.exe", io.BytesIO(exe_bytes), "application/x-msdownload")}
    res = client.post("/api/v1/revenue/application/GM-2026-000125/documents", files=files, headers=auth_header(desk_officer_token))
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["error"]["message"]


def test_doc_failure_empty_file_rejected(desk_officer_token):
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    res = client.post("/api/v1/revenue/application/GM-2026-000125/documents", files=files, headers=auth_header(desk_officer_token))
    assert res.status_code == 400


def test_doc_failure_oversized_file_rejected(desk_officer_token):
    # 11MB file exceeding 10MB limit
    huge_bytes = b"0" * (11 * 1024 * 1024)
    files = {"file": ("huge_document.pdf", io.BytesIO(huge_bytes), "application/pdf")}
    res = client.post("/api/v1/revenue/application/GM-2026-000125/documents", files=files, headers=auth_header(desk_officer_token))
    assert res.status_code == 400
    assert "exceeds maximum allowed" in res.json()["error"]["message"]


# ============================================================================
# 2. OCR Failure & Provider Resilience Simulations
# ============================================================================
def test_ocr_failure_mode_corrupt_file(desk_officer_token):
    provider = SimulatedOCRProvider()
    res = provider.extract_text(b"CorruptUnreadableBytes", mime_type="application/pdf", filename="corrupt.pdf")
    assert res.status == "FAILED"
    assert res.overall_confidence == 0.0
    assert res.error_message is not None


def test_ocr_failure_does_not_cause_automatic_rejection(desk_officer_token):
    # App GM-2026-000128 has document failure / missing OCR evidence
    headers = auth_header(desk_officer_token)
    res = client.get("/api/v1/revenue/application/GM-2026-000128", headers=headers)
    assert res.status_code == 200
    app_data = res.json()["data"]
    # Verify application remains active for manual officer review (NOT REJECTED)
    assert app_data["status"] != "REJECTED"


# ============================================================================
# 3. Bilingual Matching & Devanagari Edge Cases
# ============================================================================
def test_bilingual_devanagari_numerals():
    assert convert_devanagari_digits("४११०३८") == "411038"
    assert convert_devanagari_digits("गट क्र. १२३") == "गट क्र. 123"
    res_pin = compare_pincode("411038", "४११०३८")
    assert res_pin["result"] == "MATCH"


def test_bilingual_name_and_initials_matching():
    assert normalize_name("Shri Rajesh Patil") == "rajesh patil"
    assert "राजेश पाटील" in normalize_name("श्री राजेश पाटील")
    assert check_initials_compatibility("R S Patil", "Rajesh Shantaram Patil") is True
    assert check_initials_compatibility("R P", "Rajesh Patil") is True


# ============================================================================
# 4. Confidence Engine Bounds & Numeric Safety
# ============================================================================
def test_confidence_engine_numeric_bounds_and_clamping():
    engine = RuleBasedVerificationConfidenceEngine()

    # Case 1: NaN input
    nan_ocr = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=float("nan"))
    res_nan = engine.evaluate_confidence(nan_ocr, {}, {}, float("nan"))
    assert res_nan.ocr_confidence == 0.0
    assert res_nan.match_confidence == 0.0
    assert 0.0 <= res_nan.overall_confidence <= 1.0

    # Case 2: Infinity input
    inf_ocr = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=float("inf"))
    res_inf = engine.evaluate_confidence(inf_ocr, {}, {}, float("inf"))
    assert res_inf.ocr_confidence == 0.0
    assert res_inf.match_confidence == 0.0

    # Case 3: Out of bounds (1.8 and -0.5)
    oob_ocr = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=1.8)
    res_oob = engine.evaluate_confidence(oob_ocr, {}, {}, -0.5)
    assert res_oob.ocr_confidence == 1.0
    assert res_oob.match_confidence == 0.0


# ============================================================================
# 5. Recommendation Semantics (Recommendation != Decision)
# ============================================================================
def test_recommendation_band_does_not_mutate_application(desk_officer_token):
    headers = auth_header(desk_officer_token)
    app_id = "GM-2026-000125"

    # Client tries to verify document returning recommendation
    res_ver = client.post(f"/api/v1/revenue/document/DOC-REV-9081/verify?provider=SIMULATED", headers=headers)
    assert res_ver.status_code == 200
    rec_band = res_ver.json()["data"]["recommendation"]

    # Verify application status remains PROCESSING (NOT automatically APPROVED or REJECTED)
    res_app = client.get(f"/api/v1/revenue/application/{app_id}", headers=headers)
    assert res_app.status_code == 200
    assert res_app.json()["data"]["status"] in ("PENDING", "PROCESSING")
    assert res_app.json()["data"]["status"] not in ("VERIFIED", "COMPLETED", "REJECTED")
