import io
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.services.auth_service import create_access_token
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_repository import AuditRepository

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
# 1. Scenario A — Complete End-to-End Happy Path (Approval)
# ============================================================================
def test_e2e_happy_path_approval(desk_officer_token):
    # App ID GM-2026-000125 (Pune Division, assigned to USR-REV-001)
    app_id = "GM-2026-000125"
    headers = auth_header(desk_officer_token)

    # Step 1: Query initial application detail
    res_init = client.get(f"/api/v1/revenue/application/{app_id}", headers=headers)
    assert res_init.status_code == 200
    app_data = res_init.json()["data"]
    assert app_data.get("application_id", app_data.get("id")) == app_id

    # Step 2: Validate DPDP Consent
    res_consent = client.post(f"/api/v1/revenue/application/{app_id}/validate-consent", headers=headers)
    assert res_consent.status_code == 200
    assert res_consent.json()["data"]["valid"] is True

    # Step 3: Validate Address Completeness
    res_data = client.post(f"/api/v1/revenue/application/{app_id}/validate-data", headers=headers)
    assert res_data.status_code == 200
    assert res_data.json()["data"]["valid"] is True

    # Step 4: Upload Proof Document (PDF)
    pdf_bytes = b"%PDF-1.4 E2E Test Proof Document Content for Validation"
    files = {"file": ("electricity_bill_e2e.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_upload = client.post(f"/api/v1/revenue/application/{app_id}/documents", files=files, headers=headers)
    assert res_upload.status_code in (200, 201)
    doc_info = res_upload.json()["data"]
    doc_id = doc_info.get("document_id", doc_info.get("id"))
    assert doc_id is not None

    # Step 5: Execute Local OCR Extraction Evidence & Bilingual Match
    res_ocr = client.post(f"/api/v1/revenue/document/{doc_id}/verify?provider=SIMULATED", headers=headers)
    assert res_ocr.status_code == 200
    ver_data = res_ocr.json()["data"]
    assert ver_data["valid"] is True
    assert ver_data["ocr_confidence"] >= 0.80

    # Step 6: Execute Comprehensive Address Verification Probe
    res_probe = client.post("/api/v1/revenue/address/verify", json={"application_id": app_id}, headers=headers)
    assert res_probe.status_code == 200

    # Step 6b: Officer validates document evidence on desk (DOC-REV-9081)
    res_override = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/override",
        json={"decision": "VALIDATED", "reason": "Officer verified physical 7/12 extract and electricity bill evidence during desk review."},
        headers=headers,
    )
    assert res_override.status_code == 200

    # Step 7: Transition to PROCESSING (Start Review)
    client.post(f"/api/v1/revenue/application/{app_id}/start-review", headers=headers)

    # Step 8: Statutory Approval by Revenue Officer
    res_approve = client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        json={"reason": "Officer verified physical 7/12 extract and electricity bill evidence."},
        headers=headers,
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["data"]["status"] == "VERIFIED"

    # Step 9: Verify Immutability on Finalized Application
    res_mut = client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        json={"reason": "Second approval attempt should fail."},
        headers=headers,
    )
    assert res_mut.status_code == 409

    # Step 10: Verify Immutable Audit Trail Entry Exists
    res_audit = client.get(f"/api/v1/revenue/audit-logs?application_id={app_id}", headers=headers)
    assert res_audit.status_code == 200
    logs = res_audit.json()["data"]["items"]
    assert len(logs) > 0

    # Step 11: Verify Dashboard Analytics Reflects Application State
    res_dash = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert res_dash.status_code == 200
    kpis = res_dash.json()["data"]["kpis"]
    assert "approved" in kpis


# ============================================================================
# 2. Scenario B — Complete End-to-End Rejection Flow
# ============================================================================
def test_e2e_rejection_flow(desk_officer_token):
    # App ID GM-2026-000127 (Pune Division, assigned to USR-REV-001)
    app_id = "GM-2026-000127"
    headers = auth_header(desk_officer_token)

    # Step 1: Start Review
    client.post(f"/api/v1/revenue/application/{app_id}/start-review", headers=headers)

    # Step 2: Officer Rejection without Reason (Fails Validation)
    res_noreason = client.post(f"/api/v1/revenue/application/{app_id}/reject", json={"reason": ""}, headers=headers)
    assert res_noreason.status_code in (400, 409, 422)

    # Step 3: Officer Rejection with Valid Statutory Reason
    res_reject = client.post(
        f"/api/v1/revenue/application/{app_id}/reject",
        json={"reason": "Name on uploaded electricity bill completely mismatches application record."},
        headers=headers,
    )
    assert res_reject.status_code in (200, 409)

    # Step 4: Verify Immutability after Rejection
    res_reapprove = client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        json={"reason": "Attempting approval on rejected application."},
        headers=headers,
    )
    assert res_reapprove.status_code == 409

    # Step 5: Verify Audit Log Event
    res_audit = client.get(f"/api/v1/revenue/audit-logs?application_id={app_id}", headers=headers)
    assert res_audit.status_code == 200
    logs = res_audit.json()["data"]["items"]
    assert len(logs) > 0
