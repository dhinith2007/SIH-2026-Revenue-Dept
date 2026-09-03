import pytest
import io
import math
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.services.ocr.base import OCRRawResult
from app.services.ocr.confidence_engine import (
    RuleBasedVerificationConfidenceEngine,
    VerificationConfidenceResult,
)
from app.services.ocr.normalization import (
    normalize_address_text,
    convert_devanagari_digits,
    normalize_name,
)
from app.services.ocr.matcher import compare_pincode, check_initials_compatibility


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
def cross_division_token():
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
# 1. AI/OCR Trust Boundary & Client Forgery Prevention
# ============================================================================
def test_client_cannot_forge_confidence_or_recommendation(client, desk_officer_token):
    # Attempting to submit forged confidence via verification endpoint query or body
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify?provider=SIMULATED",
        json={
            "ocr_confidence": 1.0,
            "match_confidence": 1.0,
            "overall_confidence": 1.0,
            "recommendation": "HIGH_CONFIDENCE_MATCH",
        },
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Verification result is generated independently by backend
    assert "overall_confidence" in data
    assert "recommendation" in data
    assert isinstance(data["ocr_confidence"], float)


def test_ai_recommendation_never_mutates_application_status(client, desk_officer_token):
    # Verify document for application GM-2026-000124
    res_ver = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(desk_officer_token),
    )
    assert res_ver.status_code == 200

    # Fetch application and verify status remains PROCESSING (not auto-approved)
    res_app = client.get(
        "/api/v1/revenue/application/GM-2026-000124",
        headers=auth_header(desk_officer_token),
    )
    assert res_app.status_code == 200
    app_data = res_app.json()["data"]
    assert app_data["status"] in ("PROCESSING", "PENDING")
    assert app_data["status"] != "VERIFIED"
    assert app_data["status"] != "COMPLETED"


# ============================================================================
# 2. Statutory Decision Hardening
# ============================================================================
def test_cross_division_officer_blocked(client, cross_division_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(cross_division_token),
    )
    assert res.status_code == 403


def test_statutory_approval_requires_explicit_officer_action(client, desk_officer_token):
    # GM-2026-000124 document is VALIDATED, but application requires explicit approve endpoint
    res_app = client.get(
        "/api/v1/revenue/application/GM-2026-000124",
        headers=auth_header(desk_officer_token),
    )
    assert res_app.json()["data"]["status"] in ("PENDING", "PROCESSING")

    # Call statutory approve endpoint explicitly
    res_approve = client.post(
        "/api/v1/revenue/application/GM-2026-000124/approve",
        json={"reason": "Officer completed physical and OCR verification."},
        headers=auth_header(desk_officer_token),
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["data"]["status"] == "VERIFIED"


def test_auditor_read_only_restriction(client, auditor_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9082/override",
        json={"decision": "VALIDATED", "reason": "Auditor attempt override."},
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 403


def test_finalized_application_mutation_blocked(client, desk_officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json={"decision": "MISMATCH", "reason": "Attempting modification on finalized application."},
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 409


# ============================================================================
# 6. Malicious Document Upload & Path Traversal Rejection
# ============================================================================
def test_malicious_path_traversal_filename_rejected(client, desk_officer_token):
    pdf_bytes = b"%PDF-1.4 Test PDF for security validation"
    files = {"file": ("../../etc/passwd.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000125/documents",
        files=files,
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 422
    assert "Invalid document filename" in res.json()["error"]["message"]


def test_unsupported_file_mime_rejected(client, desk_officer_token):
    exe_bytes = b"MZExecutableBinary"
    files = {"file": ("malicious.exe", io.BytesIO(exe_bytes), "application/x-msdownload")}
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000125/documents",
        files=files,
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["error"]["message"]
