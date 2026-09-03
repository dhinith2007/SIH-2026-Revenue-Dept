import io
import hashlib
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.services.ocr.base import BaseOCRProvider, OCRRawResult, OCRExtractedField
from app.services.ocr.simulated_provider import SimulatedOCRProvider
from app.services.ocr.tesseract_provider import LocalTesseractOCRProvider
from app.services.ocr import get_ocr_provider
from app.services.ocr.normalization import (
    normalize_text,
    normalize_name,
    normalize_pincode,
    is_devanagari_text,
)
from app.services.document_verification_service import DocumentVerificationService
from app.repositories.document_evidence_repository import DocumentEvidenceRepository
from app.models.document_evidence import DocumentVerificationRecord


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
# Category A: Provider Contract
# ============================================================================
def test_simulated_provider_returns_valid_ocr_raw_result():
    provider = SimulatedOCRProvider()
    result = provider.extract_text(
        document_data=b"%PDF-1.4 Mock valid content",
        filename="Utility_Bill.pdf",
        context={"citizen_name": "Rajesh Shantaram Patil"},
        correlation_id="CORR-TEST-001",
        document_id="DOC-REV-9081",
    )
    assert isinstance(result, OCRRawResult)
    assert result.provider == "SIMULATED"
    assert result.is_simulated is True
    assert result.status == "SUCCESS"
    assert result.overall_confidence >= 0.90
    assert result.processing_duration_ms >= 0.0
    assert result.document_hash is not None
    assert result.correlation_id == "CORR-TEST-001"
    assert "name" in result.fields
    assert "address" in result.fields
    assert "taluka" in result.fields
    assert "district" in result.fields
    assert "pincode" in result.fields


def test_provider_health_check():
    sim = SimulatedOCRProvider()
    health = sim.health_check()
    assert health["status"] == "UP"
    assert health["available"] is True
    assert health["provider"] == "SIMULATED"


# ============================================================================
# Category B: Unicode & Devanagari / Marathi Support
# ============================================================================
def test_devanagari_detection():
    assert is_devanagari_text("राजेश पाटील") is True
    assert is_devanagari_text("Rajesh Patil") is False
    assert is_devanagari_text("Flat 402, हवेली") is True


def test_devanagari_text_normalization():
    raw_marathi = "  श्री  राजेश   शांताराम   पाटील ।  "
    norm = normalize_text(raw_marathi)
    # Punctuation danda removed, spaces collapsed
    assert "श्री राजेश शांताराम पाटील" in norm
    assert "।" not in norm


def test_marathi_honorifics_removal():
    name1 = "श्री. राजेश शांताराम पाटील"
    norm1 = normalize_name(name1)
    assert norm1 == "राजेश शांताराम पाटील"

    name2 = "श्रीमती सुनंदा विठ्ठलराव देशमुख"
    norm2 = normalize_name(name2)
    assert norm2 == "सुनंदा विठ्ठलराव देशमुख"

    name3 = "सौ. अनिता सुरेश कुलकर्णी"
    norm3 = normalize_name(name3)
    assert norm3 == "अनिता सुरेश कुलकर्णी"


def test_mixed_english_marathi_normalization():
    mixed = "Taluka: हवेली, District: पुणे - 411038"
    norm = normalize_text(mixed)
    assert "taluka हवेली district पुणे 411038" == norm


def test_devanagari_pincode_translation():
    # Marathi numerals ४११०३८ -> 411038
    marathi_pin = "४११०३८"
    converted = normalize_pincode(marathi_pin)
    assert converted == "411038"

    # Mixed text with Devanagari numerals
    pin_in_text = "पिनकोड: ४१३१०२"
    assert normalize_pincode(pin_in_text) == "413102"


# ============================================================================
# Category C: SHA-256 Evidence Integrity
# ============================================================================
def test_sha256_deterministic_hashing():
    content_a = b"%PDF-1.4 Official Pune Land Record Proof"
    content_b = b"%PDF-1.4 Official Pune Land Record Proof"
    content_modified = b"%PDF-1.4 Tampered Pune Land Record Proof"

    hash_a = hashlib.sha256(content_a).hexdigest()
    hash_b = hashlib.sha256(content_b).hexdigest()
    hash_mod = hashlib.sha256(content_modified).hexdigest()

    assert hash_a == hash_b
    assert hash_a != hash_mod
    assert len(hash_a) == 64


def test_upload_endpoint_computes_sha256(client, desk_officer_token):
    pdf_bytes = b"%PDF-1.4 Test PDF for SHA-256 hashing verification"
    expected_hash = hashlib.sha256(pdf_bytes).hexdigest()

    files = {"file": ("HashTestDoc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["document_hash"] == expected_hash


# ============================================================================
# Category D: Tesseract Provider Adapter & Graceful Degradation
# ============================================================================
def test_tesseract_adapter_unavailable_handled_safely():
    # Instantiate with a non-existent binary path
    provider = LocalTesseractOCRProvider(executable_path="/nonexistent/bin/tesseract")
    health = provider.health_check()
    assert health["available"] is False
    assert health["status"] == "UNAVAILABLE"

    # Extraction must fail gracefully without throwing unhandled exceptions
    result = provider.extract_text(
        document_data=b"%PDF-1.4 mock binary",
        filename="test.pdf",
    )
    assert isinstance(result, OCRRawResult)
    assert result.provider == "TESSERACT"
    assert result.status == "FAILED"
    assert result.is_simulated is False
    assert "unavailable" in result.error_message.lower()
    # Ensure no internal host filesystem paths are leaked
    assert "/nonexistent/bin" not in result.error_message


def test_tesseract_adapter_empty_file_handling():
    provider = LocalTesseractOCRProvider(executable_path="/nonexistent/bin/tesseract")
    result = provider.extract_text(document_data=b"", filename="empty.pdf")
    assert result.status == "EMPTY"
    assert result.overall_confidence == 0.0
    assert "empty" in result.error_message.lower()


# ============================================================================
# Category E: Provider Selection & Factory
# ============================================================================
def test_get_ocr_provider_simulated():
    p = get_ocr_provider("SIMULATED")
    assert isinstance(p, SimulatedOCRProvider)

    p_lower = get_ocr_provider("simulated")
    assert isinstance(p_lower, SimulatedOCRProvider)


def test_get_ocr_provider_tesseract():
    p = get_ocr_provider("TESSERACT")
    assert isinstance(p, LocalTesseractOCRProvider)


def test_get_ocr_provider_invalid_raises_value_error():
    with pytest.raises(ValueError) as exc:
        get_ocr_provider("UNSUPPORTED_CLOUD_AI")
    assert "Invalid OCR provider" in str(exc.value)


def test_verify_document_with_invalid_provider_fails_safely():
    # DocumentVerificationService should catch invalid provider and return failed status without crashing
    app_dict = {
        "application_id": "GM-2026-TEST",
        "citizen_name": "Test Citizen",
        "data_payload": {
            "proof_documents": [
                {
                    "document_id": "DOC-TEST-1",
                    "document_name": "bill.pdf",
                    "document_type": "ELECTRICITY_BILL",
                }
            ]
        },
    }
    res = DocumentVerificationService.verify_document(
        app_dict, doc_index=0, provider_type="UNKNOWN_PROVIDER_XYZ"
    )
    assert res.valid is False
    assert res.match_status == "INVALID"
    assert "invalid" in res.explanation.lower() or "unsupported" in res.explanation.lower()


# ============================================================================
# Category F: OCR Failure Modes
# ============================================================================
def test_corrupt_file_failure_mode(client, desk_officer_token):
    corrupt_bytes = b"%PDF-corrupt unreadable binary header data"
    files = {"file": ("corrupt_bill.pdf", io.BytesIO(corrupt_bytes), "application/pdf")}
    up_res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(desk_officer_token),
    )
    doc_id = up_res.json()["data"]["document_id"]

    ver_res = client.post(
        f"/api/v1/revenue/document/{doc_id}/verify",
        headers=auth_header(desk_officer_token),
    )
    assert ver_res.status_code == 200
    data = ver_res.json()["data"]
    assert data["valid"] is False
    assert data["match_status"] == "INVALID"


def test_ocr_failure_never_causes_statutory_approval(client, desk_officer_token):
    # GM-2026-000129 has document mismatch (Baramati vs Maval)
    # Attempting to approve without overriding must be blocked (HTTP 422)
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000129/approve",
        json={"reason": "Attempting approval with mismatched document"},
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DOCUMENT_MISMATCH"


# ============================================================================
# Category G: Security & Multi-Tenant Authorization
# ============================================================================
def test_cross_division_officer_cannot_trigger_ocr_on_assigned_app(client, other_officer_token):
    # GM-2026-000124 belongs to Pune Division assigned to USR-REV-001
    # USR-REV-999 belongs to Nagpur Division
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403


def test_auditor_cannot_mutate_or_verify_document(client, auditor_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 403


def test_finalized_application_document_verify_is_read_only(client, desk_officer_token):
    # DOC-REV-3310 belongs to GM-2026-000131 which is finalized as VERIFIED
    # Manual override on finalized document must be blocked (409)
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json={"decision": "MISMATCH", "reason": "Officer attempting to alter finalized state."},
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


# ============================================================================
# Category H: Evidence Relational Persistence
# ============================================================================
def test_document_evidence_repository_persistence():
    repo = DocumentEvidenceRepository(db=None)
    evidence_payload = {
        "document_id": "DOC-REV-TEST-001",
        "application_id": "GM-2026-000124",
        "document_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "provider": "SIMULATED",
        "status": "VALIDATED",
        "confidence": 0.95,
        "extracted_fields": {"taluka": "Haveli", "district": "Pune"},
        "field_confidences": {"taluka": 0.96, "district": 0.98},
        "processing_duration_ms": 12.5,
        "correlation_id": "CORR-2026-000124",
    }
    saved = repo.save_evidence(evidence_payload)
    assert saved["id"].startswith("EVID-")

    # Query back
    records = repo.get_by_document_id("DOC-REV-TEST-001")
    assert len(records) >= 1
    assert records[0]["document_hash"] == evidence_payload["document_hash"]
    assert records[0]["provider"] == "SIMULATED"
    assert records[0]["confidence"] == 0.95

    # Query by hash
    by_hash = repo.get_by_hash(evidence_payload["document_hash"])
    assert by_hash is not None
    assert by_hash["document_id"] == "DOC-REV-TEST-001"
