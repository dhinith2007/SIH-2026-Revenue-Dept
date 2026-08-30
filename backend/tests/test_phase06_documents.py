import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def officer_token():
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
# 1. Document Ingestion & Validation Tests
# ============================================================================
def test_upload_valid_pdf_document(client, officer_token):
    pdf_content = b"%PDF-1.4 Mock valid PDF document content for testing"
    files = {"file": ("Utility_Bill.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {"document_type": "ELECTRICITY_BILL"}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        data=data,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["document_name"] == "Utility_Bill.pdf"
    assert body["data"]["document_type"] == "ELECTRICITY_BILL"
    assert body["data"]["verification_status"] == "PENDING"
    assert "document_id" in body["data"]


def test_upload_unsupported_file_type_rejected(client, officer_token):
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00ExecutableBinary"
    files = {"file": ("malicious.exe", io.BytesIO(exe_content), "application/x-msdownload")}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 400
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DOCUMENT_TYPE_UNSUPPORTED"


def test_upload_empty_document_rejected(client, officer_token):
    empty_content = b""
    files = {"file": ("empty.pdf", io.BytesIO(empty_content), "application/pdf")}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 400
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DOCUMENT_EMPTY"


def test_upload_to_finalized_application_blocked(client, officer_token):
    pdf_content = b"%PDF-1.4 Mock valid PDF"
    files = {"file": ("new_doc.pdf", io.BytesIO(pdf_content), "application/pdf")}

    # GM-2026-000131 is already VERIFIED
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000131/documents",
        files=files,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 409
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


# ============================================================================
# 2. Document Listing & Metadata
# ============================================================================
def test_list_application_documents(client, officer_token):
    res = client.get(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert len(body["data"]) >= 1
    doc = body["data"][0]
    assert "document_id" in doc
    assert "verification_result" in doc
    assert doc["verification_result"]["is_simulated_ocr"] is True


def test_get_document_detail_by_id(client, officer_token):
    res = client.get(
        "/api/v1/revenue/document/DOC-REV-9081",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["document_id"] == "DOC-REV-9081"
    assert body["data"]["document_type"] == "ELECTRICITY_BILL"


def test_get_nonexistent_document_returns_404(client, officer_token):
    res = client.get(
        "/api/v1/revenue/document/DOC-NONEXISTENT-999",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "RESOURCE_NOT_FOUND"


# ============================================================================
# 3. Document Preview
# ============================================================================
def test_preview_document_returns_safe_content(client, officer_token):
    res = client.get(
        "/api/v1/revenue/document/DOC-REV-9081/preview",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers["content-type"]
    assert "MAHARASHTRA STATE ELECTRICITY" in res.text
    assert "DOC-REV-9081" in res.text


# ============================================================================
# 4. OCR Extraction & 6-Part Address Matching
# ============================================================================
def test_verify_document_happy_path_all_components_match(client, officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Matching assertions
    assert data["valid"] is True
    assert data["match_status"] == "VALIDATED"
    assert data["name_match"] == "MATCH"
    assert data["address_match"] == "MATCH"
    assert data["assistive_score"] >= 0.85
    assert data["matched_components_count"] >= 6
    assert data["is_simulated_ocr"] is True

    # 6-part component matching breakdown
    comp_matches = data["component_matches"]
    assert "house_no" in comp_matches
    assert "street" in comp_matches
    assert "village" in comp_matches
    assert "taluka" in comp_matches
    assert "district" in comp_matches
    assert "pincode" in comp_matches

    # Field confidences
    conf = data["field_confidences"]
    assert conf["name"] >= 0.90
    assert conf["taluka"] >= 0.90
    assert conf["pincode"] >= 0.90


def test_verify_document_mismatch_scenario_taluka(client, officer_token):
    # GM-2026-000129 has document with Baramati instead of Maval
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000129/verify-document",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["valid"] is False
    assert data["match_status"] == "MISMATCH"
    assert "taluka" in data["explanation"].lower() or "discrepancy" in data["explanation"].lower()


def test_verify_application_with_no_document_returns_missing(client, officer_token):
    # GM-2026-000128 has empty proof_documents
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000128/verify-document",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["valid"] is False
    assert data["match_status"] == "MISSING"
    assert data["name_match"] == "NOT_EXTRACTED"
    assert data["address_match"] == "NOT_EXTRACTED"
    assert "no supporting proof" in data["explanation"].lower()


# ============================================================================
# 5. Officer Manual Override & Audit Logging
# ============================================================================
def test_officer_manual_override_success(client, officer_token):
    override_payload = {
        "decision": "VALIDATED",
        "reason": "Officer verified physical municipal electricity bill at Taluka desk.",
        "notes": "Override permitted under Maharashtra Land Revenue rules.",
    }

    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=override_payload,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["valid"] is True
    assert data["manual_override"] is not None
    assert data["manual_override"]["decision"] == "VALIDATED"
    assert "physical municipal" in data["manual_override"]["reason"]


def test_manual_override_requires_mandatory_reason(client, officer_token):
    invalid_payload = {
        "decision": "VALIDATED",
        "reason": "ok",  # Less than 5 chars
    }

    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json=invalid_payload,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 422


def test_manual_override_on_finalized_app_blocked(client, officer_token):
    # DOC-REV-3310 belongs to GM-2026-000131 (VERIFIED)
    override_payload = {
        "decision": "MISMATCH",
        "reason": "Attempting to change finalized record.",
    }

    res = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json=override_payload,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 409
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "APPLICATION_ALREADY_FINALIZED"


# ============================================================================
# 6. RBAC & Security Enforcement
# ============================================================================
def test_unauthenticated_document_access_blocked(client):
    res = client.get("/api/v1/revenue/application/GM-2026-000124/documents")
    assert res.status_code == 401


def test_auditor_read_only_document_access(client, auditor_token):
    # Read-only document inspection is permitted
    res = client.get(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 200

    # Document upload must be forbidden (403)
    pdf_content = b"%PDF-1.4 Mock PDF"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(auditor_token),
    )
    assert upload_res.status_code == 403


def test_audit_logs_record_document_actions(client, officer_token):
    # Perform a document verification
    client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(officer_token),
    )

    res = client.get(
        "/api/v1/revenue/audit-logs?application_id=GM-2026-000124",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    actions = [entry["action"] for entry in body["data"]["items"]]
    assert any(a in ("DOCUMENT_UPLOADED", "DOCUMENT_VERIFIED", "OCR_COMPLETED", "MANUAL_OVERRIDE") for a in actions)


# ============================================================================
# 7. Additional Extended Document Scenarios
# ============================================================================
def test_upload_valid_png_image_document(client, officer_token):
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRMockPNG"
    files = {"file": ("RentAgreement.png", io.BytesIO(png_content), "image/png")}
    data = {"document_type": "REGISTERED_RENT_AGREEMENT"}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        data=data,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["document_name"] == "RentAgreement.png"


def test_upload_too_large_document_rejected(client, officer_token):
    large_content = b"0" * (11 * 1024 * 1024)  # 11 MB
    files = {"file": ("huge_scan.pdf", io.BytesIO(large_content), "application/pdf")}

    res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(officer_token),
    )
    assert res.status_code == 400
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DOCUMENT_TOO_LARGE"


def test_verify_document_produces_explainable_rationale(client, officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert "explanation" in data
    assert len(data["explanation"]) > 10
    assert "Simulated AI/OCR" in data["explanation"] or "passed" in data["explanation"]


def test_verify_corrupt_document_returns_invalid(client, officer_token):
    # Upload corrupt document to application
    pdf_content = b"%PDF-corrupt unreadable garbage header"
    files = {"file": ("corrupt_scan.pdf", io.BytesIO(pdf_content), "application/pdf")}
    up_res = client.post(
        "/api/v1/revenue/application/GM-2026-000124/documents",
        files=files,
        headers=auth_header(officer_token),
    )
    doc_id = up_res.json()["data"]["document_id"]

    res = client.post(
        f"/api/v1/revenue/document/{doc_id}/verify",
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["valid"] is False
    assert data["match_status"] == "INVALID"


def test_comprehensive_address_verification_probe_includes_phase06_results(client, officer_token):
    res = client.post(
        "/api/v1/revenue/address/verify",
        json={"application_id": "GM-2026-000124"},
        headers=auth_header(officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["validation"]["document"] == "VALIDATED"


def test_document_verification_with_simulation_failure(client, officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers={
            **auth_header(officer_token),
            "X-Simulate-Failure": "API_UNAVAILABLE",
        },
    )
    assert res.status_code == 503
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"


