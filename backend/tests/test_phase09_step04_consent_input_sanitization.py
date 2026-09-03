"""
GovMesh SIH26129 — Phase 09 Step 04: Consent Synchronization & Input Sanitization Tests

Validates:
- SEC-02: Authoritative Consent Synchronization (DB record precedence, live revocation, expiration, approval block)
- SEC-04: Document Magic-Byte Inspection (binary signatures for PDF, PNG, JPEG, spoofing rejection)
- SEC-04: Filename Safety Checks (path traversal, null bytes, control characters, max length)
- SEC-05: SVG Document Preview XML Entity Sanitization (XSS mitigation, entity encoding)
- SEC-09: 6-Digit Indian Postal PIN Code Format Validation (regex ^[1-9][0-9]{5}$)
- Sorting Whitelist: Safe fallback to received_at on arbitrary sort attributes
"""
import io
import pytest
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.services.consent_service import ConsentService
from app.services.data_validation_service import DataValidationService
from app.repositories.consent_repository import ConsentRepository
from app.repositories.application_repository import ApplicationRepository
from app.core.security_utils import (
    sanitize_svg_text,
    validate_file_magic_bytes,
    validate_filename_safety,
)

client = TestClient(app)

_FUTURE = datetime.now(timezone.utc) + timedelta(days=90)
_PAST = datetime.now(timezone.utc) - timedelta(days=30)


@pytest.fixture
def senior_officer_headers():
    token = create_access_token({
        "sub": "USR-REV-002",
        "username": "sro_patil",
        "role": "SENIOR_REVENUE_OFFICER",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def desk_officer_headers():
    token = create_access_token({
        "sub": "USR-REV-001",
        "username": "ro_deshmukh",
        "role": "REVENUE_OFFICER",
    })
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. SEC-02: Authoritative Consent Synchronization Tests
# ===========================================================================

def test_consent_db_revocation_overrides_client_payload():
    """Authoritative DB revocation must override any 'VALID' claims in client payload."""
    consent_ref = "CONSENT-SYNC-REVOKED-01"
    app_id = "GM-2026-SYNC-01"

    # Seed an authoritative revoked record into repository
    repo = ConsentRepository()
    repo.save_consent({
        "consent_reference": consent_ref,
        "application_id": app_id,
        "status": "REVOKED",
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "data_scope": "address.change",
        "recipient": "Revenue & Forest Department",
        "issued_at": datetime.now(timezone.utc),
        "expires_at": _FUTURE,
        "revoked_at": datetime.now(timezone.utc),
    })

    # Client payload deceptively asserts status is 'VALID'
    app_dict = {
        "application_id": app_id,
        "consent_reference": consent_ref,
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "consent_record": {
            "status": "VALID",
            "purpose": "Update Revenue address record & 7/12 land registry linkage",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE.isoformat(),
        },
    }

    result = ConsentService.validate_consent(app_dict, consent_repo=repo)
    assert result.valid is False
    assert result.status == "REVOKED"
    assert any("revoked" in e.lower() for e in result.errors)
    assert result.rules_evaluated["rule_5_not_revoked"] == "FAILED"


def test_consent_db_expiration_overrides_client_payload():
    """Authoritative DB expiration must override non-expired client claims."""
    consent_ref = "CONSENT-SYNC-EXPIRED-01"
    app_id = "GM-2026-SYNC-02"

    repo = ConsentRepository()
    repo.save_consent({
        "consent_reference": consent_ref,
        "application_id": app_id,
        "status": "VALID",
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "data_scope": "address.change",
        "recipient": "Revenue & Forest Department",
        "issued_at": _PAST - timedelta(days=10),
        "expires_at": _PAST,
        "revoked_at": None,
    })

    app_dict = {
        "application_id": app_id,
        "consent_reference": consent_ref,
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "consent_record": {
            "status": "VALID",
            "expires_at": _FUTURE.isoformat(),
        },
    }

    result = ConsentService.validate_consent(app_dict, consent_repo=repo)
    assert result.valid is False
    assert result.status == "EXPIRED"
    assert result.rules_evaluated["rule_4_not_expired"] == "FAILED"


def test_consent_db_application_mismatch_fails_rule_2():
    """Consent issued for another application must be rejected."""
    consent_ref = "CONSENT-SYNC-MISMATCH-01"
    repo = ConsentRepository()
    repo.save_consent({
        "consent_reference": consent_ref,
        "application_id": "GM-2026-ORIGINAL-APP",
        "status": "VALID",
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "data_scope": "address.change",
        "recipient": "Revenue & Forest Department",
        "issued_at": datetime.now(timezone.utc),
        "expires_at": _FUTURE,
        "revoked_at": None,
    })

    app_dict = {
        "application_id": "GM-2026-DIFFERENT-APP",
        "consent_reference": consent_ref,
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
    }

    result = ConsentService.validate_consent(app_dict, consent_repo=repo)
    assert result.valid is False
    assert result.rules_evaluated["rule_2_application_match"] == "FAILED"


def test_consent_api_endpoint_uses_authoritative_sync(desk_officer_headers):
    """Calling /revenue/application/{id}/validate-consent honors live repo sync."""
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/validate-consent",
        headers=desk_officer_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is True
    assert data["status"] == "VALID"
    assert data["consent_reference"] == "CONSENT-2026-00124"


# ===========================================================================
# 2. SEC-04: Document Magic-Byte Binary Verification Tests
# ===========================================================================

def test_magic_bytes_valid_pdf():
    content = b"%PDF-1.7\nSample PDF stream binary content"
    is_valid, err = validate_file_magic_bytes(content, "application/pdf", "test.pdf")
    assert is_valid is True
    assert err == ""


def test_magic_bytes_valid_png():
    content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    is_valid, err = validate_file_magic_bytes(content, "image/png", "test.png")
    assert is_valid is True
    assert err == ""


def test_magic_bytes_valid_jpeg():
    content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
    is_valid, err = validate_file_magic_bytes(content, "image/jpeg", "test.jpg")
    assert is_valid is True
    assert err == ""


def test_magic_bytes_spoofed_pdf_rejected():
    """A plain text file renamed to .pdf must be rejected by magic bytes."""
    fake_pdf = b"This is just plain text, not a real PDF document."
    is_valid, err = validate_file_magic_bytes(fake_pdf, "application/pdf", "fake.pdf")
    assert is_valid is False
    assert "binary signature does not match" in err
    assert "spoofing" in err.lower()


def test_magic_bytes_spoofed_png_rejected():
    fake_png = b"<html><body>Not a PNG</body></html>"
    is_valid, err = validate_file_magic_bytes(fake_png, "image/png", "fake.png")
    assert is_valid is False
    assert "binary signature does not match" in err


def test_upload_api_rejects_spoofed_pdf(desk_officer_headers):
    """Uploading a non-PDF file claiming to be PDF returns HTTP 422 DOCUMENT_INVALID."""
    fake_pdf_bytes = b"Plain text payload pretending to be a PDF"
    files = {
        "file": ("forged_proof.pdf", io.BytesIO(fake_pdf_bytes), "application/pdf")
    }
    data = {"document_type": "ELECTRICITY_BILL"}

    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        data=data,
        headers=desk_officer_headers,
    )
    assert response.status_code == 422
    err = response.json()
    assert err["success"] is False
    msg = err.get("error", {}).get("message", "")
    code = err.get("error", {}).get("code", "")
    assert "binary signature does not match" in msg or "DOCUMENT_INVALID" in code


def test_upload_api_accepts_genuine_pdf(desk_officer_headers):
    """Uploading a file with authentic %PDF- header succeeds (HTTP 201)."""
    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>%%EOF"
    files = {
        "file": ("genuine_electricity_bill.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")
    }
    data = {"document_type": "ELECTRICITY_BILL"}

    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        data=data,
        headers=desk_officer_headers,
    )
    assert response.status_code == 201
    res_data = response.json()["data"]
    assert res_data["document_name"] == "genuine_electricity_bill.pdf"
    assert res_data["verification_status"] == "PENDING"


# ===========================================================================
# 3. SEC-04: Upload Filename Safety & Path Traversal Tests
# ===========================================================================

def test_filename_safety_valid():
    assert validate_filename_safety("address_proof_2026.pdf") == "address_proof_2026.pdf"
    assert validate_filename_safety("Electricity-Bill_Pune.jpg") == "Electricity-Bill_Pune.jpg"


def test_filename_safety_path_traversal():
    with pytest.raises(ValueError, match="path traversal"):
        validate_filename_safety("../../etc/passwd.pdf")

    with pytest.raises(ValueError, match="path traversal"):
        validate_filename_safety("..\\..\\windows\\system32\\calc.exe.pdf")


def test_filename_safety_null_bytes():
    with pytest.raises(ValueError, match="null byte"):
        validate_filename_safety("innocent.pdf\x00.exe")


def test_filename_safety_control_characters():
    with pytest.raises(ValueError, match="control character"):
        validate_filename_safety("document\x07bell.pdf")


def test_filename_safety_excessive_length():
    oversized = "a" * 256 + ".pdf"
    with pytest.raises(ValueError, match="maximum length"):
        validate_filename_safety(oversized)


def test_upload_api_rejects_path_traversal_filename(desk_officer_headers):
    """Uploading a document with path traversal in filename returns HTTP 422."""
    valid_pdf = b"%PDF-1.4 header"
    files = {
        "file": ("../../malicious_file.pdf", io.BytesIO(valid_pdf), "application/pdf")
    }
    response = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        data={"document_type": "ELECTRICITY_BILL"},
        headers=desk_officer_headers,
    )
    assert response.status_code == 422
    err = response.json()
    assert err["success"] is False
    assert "Invalid document filename" in err.get("error", {}).get("message", "")


# ===========================================================================
# 4. SEC-05: SVG Document Preview XML Entity Sanitization Tests
# ===========================================================================

def test_sanitize_svg_text_escapes_xml_special_characters():
    payload = '<script>alert("XSS & injection")</script>\'test\''
    sanitized = sanitize_svg_text(payload)
    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized
    assert "&amp;" in sanitized
    assert "&quot;" in sanitized
    assert "&#39;" in sanitized


def test_sanitize_svg_text_strips_control_characters():
    dirty = "Valid Text\x00\x08\x0b\x0c\x1fClean"
    clean = sanitize_svg_text(dirty)
    assert clean == "Valid TextClean"


def test_svg_preview_endpoint_escapes_xss_entities(desk_officer_headers):
    """
    Previewing a document returns properly generated SVG with XML entity protection.
    """
    # 1. Attach a genuine document with special characters in filename
    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>%%EOF"
    files = {
        "file": ("Preview & Test <Safe>.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")
    }
    upload_res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        data={"document_type": "ELECTRICITY_BILL"},
        headers=desk_officer_headers,
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["data"]["document_id"]

    # 2. Fetch preview
    response = client.get(
        f"/api/v1/revenue/document/{doc_id}/preview",
        headers=desk_officer_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    svg_body = response.text

    # Verify SVG structure and no raw injection
    assert "<svg" in svg_body
    assert "</svg>" in svg_body
    assert "<script>" not in svg_body
    assert "</script>" not in svg_body

    # Verify entity escaping on special characters
    assert "&amp;" in svg_body
    assert "&lt;Safe&gt;" in svg_body
    assert "<Safe>" not in svg_body


# ===========================================================================
# 5. SEC-09: 6-Digit Indian Postal PIN Code Validation Tests
# ===========================================================================

def test_pincode_valid_formats():
    """Standard 6-digit Indian PIN codes (starting with 1-9) pass validation."""
    valid_pins = ["411004", "411038", "400001", "110001", "560001", "700001"]
    for pin in valid_pins:
        app_dict = {
            "application_id": "GM-PIN-TEST",
            "citizen_name": "Rajesh Shantaram Patil",
            "consent_reference": "CONS-01",
            "data_payload": {
                "existing_address": {"house_no": "1", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": "411001"},
                "new_address": {"house_no": "2", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": pin},
                "proof_documents": [{"document_id": "DOC-01"}],
            },
        }
        res = DataValidationService.validate_application_data(app_dict)
        assert res.valid is True, f"PIN {pin} unexpectedly failed: {res.errors}"


def test_pincode_invalid_leading_zero():
    """PIN code starting with 0 is invalid in India."""
    app_dict = {
        "application_id": "GM-PIN-TEST",
        "citizen_name": "Rajesh Shantaram Patil",
        "consent_reference": "CONS-01",
        "data_payload": {
            "existing_address": {"house_no": "1", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": "411001"},
            "new_address": {"house_no": "2", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": "012345"},
            "proof_documents": [{"document_id": "DOC-01"}],
        },
    }
    res = DataValidationService.validate_application_data(app_dict)
    assert res.valid is False
    assert any("Invalid postal pincode" in e for e in res.errors)


def test_pincode_invalid_length():
    """PIN code with fewer or more than 6 digits is rejected."""
    for bad_pin in ["4110", "41103", "4110389", "41103800"]:
        app_dict = {
            "application_id": "GM-PIN-TEST",
            "citizen_name": "Rajesh Shantaram Patil",
            "consent_reference": "CONS-01",
            "data_payload": {
                "existing_address": {"house_no": "1", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": "411001"},
                "new_address": {"house_no": "2", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": bad_pin},
                "proof_documents": [{"document_id": "DOC-01"}],
            },
        }
        res = DataValidationService.validate_application_data(app_dict)
        assert res.valid is False
        assert any("Invalid postal pincode" in e for e in res.errors)


def test_pincode_invalid_alphanumeric():
    """PIN code with alphabet characters or symbols is rejected."""
    for bad_pin in ["41103A", "ABCDEF", "411-038", "411 038", "411.03"]:
        app_dict = {
            "application_id": "GM-PIN-TEST",
            "citizen_name": "Rajesh Shantaram Patil",
            "consent_reference": "CONS-01",
            "data_payload": {
                "existing_address": {"house_no": "1", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": "411001"},
                "new_address": {"house_no": "2", "street": "S", "village": "V", "taluka": "T", "district": "D", "pincode": bad_pin},
                "proof_documents": [{"document_id": "DOC-01"}],
            },
        }
        res = DataValidationService.validate_application_data(app_dict)
        assert res.valid is False
        assert any("Invalid postal pincode" in e for e in res.errors)


# ===========================================================================
# 6. Sorting Whitelist Tests in ApplicationRepository
# ===========================================================================

def test_application_sorting_whitelist_valid_columns():
    """Allowed sort columns work properly and return items."""
    repo = ApplicationRepository()
    for col in ["received_at", "updated_at", "priority", "status", "citizen_name", "application_id"]:
        items, total, pages = repo.list_applications(sort_by=col, sort_order="asc")
        assert isinstance(items, list)
        assert total >= 0


def test_application_sorting_whitelist_fallback_on_unwhitelisted_column():
    """Unwhitelisted attributes safely fall back to received_at without error."""
    repo = ApplicationRepository()
    for malicious_col in ["__class__", "password_hash", "nonexistent_field", "sleep(5)", "1; DROP TABLE"]:
        items, total, pages = repo.list_applications(sort_by=malicious_col, sort_order="desc")
        assert isinstance(items, list)
        assert total >= 0
        # Check that results are returned cleanly without raising any exceptions
