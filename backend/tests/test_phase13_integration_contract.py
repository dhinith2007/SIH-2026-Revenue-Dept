import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.repositories.application_repository import _MEM_APPLICATIONS
from app.repositories.consent_repository import _MEM_CONSENTS
from app.models.application import Application
from app.models.consent import ConsentRecord
from app.models.audit import AuditLog, ApplicationStatusHistory
from app.db.session import SessionLocal, is_db_available

client = TestClient(app)

VALID_API_KEY = settings.GOVMESH_API_KEY


@pytest.fixture(autouse=True)
def cleanup_test_records():
    """Removes test applications starting with GM-TEST- between test runs to ensure isolation."""
    def _do_clean():
        keys_to_del = [k for k in list(_MEM_APPLICATIONS.keys()) if k.startswith("GM-TEST-")]
        for k in keys_to_del:
            _MEM_APPLICATIONS.pop(k, None)

        c_to_del = [k for k in list(_MEM_CONSENTS.keys()) if "TEST" in k or k.startswith("CONSENT-TEST-")]
        for k in c_to_del:
            _MEM_CONSENTS.pop(k, None)

        if is_db_available():
            with SessionLocal() as db:
                try:
                    db.query(Application).filter(Application.application_id.like("GM-TEST-%")).delete(synchronize_session=False)
                    db.query(ConsentRecord).filter(ConsentRecord.application_id.like("GM-TEST-%")).delete(synchronize_session=False)
                    db.query(AuditLog).filter(AuditLog.application_id.like("GM-TEST-%")).delete(synchronize_session=False)
                    db.query(ApplicationStatusHistory).filter(ApplicationStatusHistory.application_id.like("GM-TEST-%")).delete(synchronize_session=False)
                    db.commit()
                except Exception:
                    db.rollback()

    _do_clean()
    yield


def _officer_token() -> str:
    return create_access_token(
        data={"sub": "USR-REV-001", "role": "REVENUE_OFFICER"},
        expires_delta=timedelta(minutes=30),
    )


def _admin_token() -> str:
    return create_access_token(
        data={"sub": "USR-REV-ADMIN", "role": "DEPARTMENT_ADMINISTRATOR"},
        expires_delta=timedelta(minutes=30),
    )


def _base_payload(application_id: str, citizen_name: str = "Pooja Suresh Sharma") -> dict:
    return {
        "application_id": application_id,
        "correlation_id": f"CORR-{application_id}",
        "request_version": "1.0",
        "source_department": "GOVMESH",
        "service_type": "ADDRESS_CHANGE",
        "priority": "NORMAL",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "citizen": {
            "name": citizen_name,
            "identifier": f"CIT-MH-{application_id.replace('GM-', '')}",
            "contact": {
                "phone": "9819922334",
                "email": "pooja.sharma@example.com",
            },
        },
        "application_data": {
            "existing_address": {
                "house_no": "12/A, Gokuldham",
                "street": "FC Road, Shivajinagar",
                "village": "Shivajinagar",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411005",
            },
            "new_address": {
                "house_no": "B-304, Green Acres",
                "street": "Baner-Pashan Link Road",
                "village": "Baner",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411045",
            },
            "proof_documents": [
                {
                    "document_id": f"DOC-{application_id}",
                    "document_type": "ELECTRICITY_BILL",
                    "document_name": "MSEDCL_Bill_Aug2026.pdf",
                    "upload_date": datetime.now(timezone.utc).isoformat(),
                    "verification_status": "VALIDATED",
                    "file_size": "1.1 MB",
                    "extracted_name": citizen_name,
                    "extracted_address": "B-304, Green Acres, Baner-Pashan Link Road, Baner, Taluka: Haveli, Dist: Pune - 411045",
                }
            ],
            "remarks": "Change of residence following property acquisition.",
        },
        "consent": {
            "consent_reference": f"CONSENT-{application_id.replace('GM-', '')}",
            "purpose": "Update Revenue address record & 7/12 land registry linkage",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "granted": True,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        },
        "integrity": {
            "canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "document_hash": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
        },
    }


# ============================================================================
# Test A: New Application Ingestion
# ============================================================================
def test_a_new_application_ingestion():
    app_id = "GM-TEST-PHASE13-001"
    payload = _base_payload(app_id, citizen_name="Aarav Vikas Shinde")

    # 1. Ingest application via dedicated integration endpoint
    res = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )

    assert res.status_code == 201, f"Expected 201 Created, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["success"] is True
    assert body["status"] == "RECEIVED"
    assert body["application_id"] == app_id
    assert body["correlation_id"] == f"CORR-{app_id}"
    assert "successfully received" in body["message"].lower()

    # 2. Verify application is immediately visible and retrievable via normal Revenue APIs
    token = _officer_token()
    detail_res = client.get(
        f"/api/v1/revenue/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_res.status_code == 200
    detail_body = detail_res.json()
    assert detail_body["success"] is True
    data = detail_body["data"]
    assert data["application_id"] == app_id
    assert data["citizen_name"] == "Aarav Vikas Shinde"
    assert data["status"] == "PENDING"
    assert data["service_type"] == "ADDRESS_CHANGE"
    assert data["data_payload"]["new_address"]["taluka"] == "Haveli"
    assert data["data_payload"]["new_address"]["pincode"] == "411045"


# ============================================================================
# Test B: Duplicate Delivery / Idempotency Check
# ============================================================================
def test_b_duplicate_delivery_idempotent_response():
    app_id = "GM-TEST-PHASE13-DUP-001"
    payload = _base_payload(app_id, citizen_name="Aarav Vikas Shinde")

    # First send -> 201 Created
    first_res = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )
    assert first_res.status_code == 201
    assert first_res.json()["status"] == "RECEIVED"

    # Resend the exact same request -> 200 OK, ALREADY_RECEIVED
    res = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )

    assert res.status_code == 200, f"Expected 200 OK for idempotent duplicate, got {res.status_code}"
    body = res.json()
    assert body["success"] is True
    assert body["status"] == "ALREADY_RECEIVED"
    assert body["application_id"] == app_id
    assert "already received" in body["message"].lower()

    # Check that alias endpoint also acknowledges duplicate safely
    alias_res = client.post(
        "/api/v1/revenue/applications/ingest",
        json=payload,
        headers={"X-API-Key": VALID_API_KEY},
    )
    assert alias_res.status_code == 200
    alias_body = alias_res.json()
    assert alias_body["status"] == "ALREADY_RECEIVED"


# ============================================================================
# Test C: Different Legitimate Application
# ============================================================================
def test_c_different_application_ingestion():
    app_id_1 = "GM-TEST-PHASE13-001"
    payload_1 = _base_payload(app_id_1, citizen_name="Aarav Vikas Shinde")
    res_1 = client.post(
        "/api/v1/revenue/applications/ingest",
        json=payload_1,
        headers={"X-API-Key": VALID_API_KEY},
    )
    assert res_1.status_code == 201

    app_id_2 = "GM-TEST-PHASE13-002"
    payload_2 = _base_payload(app_id_2, citizen_name="Ananya Pradeep Joshi")
    res_2 = client.post(
        "/api/v1/revenue/applications/ingest",
        json=payload_2,
        headers={"X-API-Key": VALID_API_KEY},
    )
    assert res_2.status_code == 201
    body = res_2.json()
    assert body["status"] == "RECEIVED"
    assert body["application_id"] == app_id_2

    # Verify both applications exist independently in list
    token = _officer_token()
    list_res = client.get(
        "/api/v1/revenue/applications?search=PHASE13",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    list_body = list_res.json()
    app_ids = [item["application_id"] for item in list_body["data"]["items"]]
    assert "GM-TEST-PHASE13-001" in app_ids
    assert "GM-TEST-PHASE13-002" in app_ids


# ============================================================================
# Test D: Invalid Request Payload Validation
# ============================================================================
def test_d_invalid_request_validation():
    # 1. Missing mandatory new_address
    invalid_payload = {
        "application_id": "GM-TEST-INVALID-001",
        "correlation_id": "CORR-TEST-INVALID-001",
        "citizen": {"name": "Test Citizen", "identifier": "CIT-001"},
        "application_data": {},  # missing new_address
    }
    res = client.post(
        "/api/v1/integrations/applications",
        json=invalid_payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )
    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"

    # 2. Invalid Pincode (must be 6 digits, not starting with 0)
    payload = _base_payload("GM-TEST-INVALID-002")
    payload["application_data"]["new_address"]["pincode"] = "012345"  # invalid
    res2 = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"


# ============================================================================
# Test E: Unauthorized Source Rejection
# ============================================================================
def test_e_unauthorized_source():
    payload = _base_payload("GM-TEST-UNAUTH-001")

    # 1. Missing authentication header entirely
    res_no_auth = client.post("/api/v1/integrations/applications", json=payload)
    assert res_no_auth.status_code == 401
    assert res_no_auth.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    # 2. Invalid API key
    res_bad_key = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"X-GovMesh-API-Key": "completely-invalid-key-xyz"},
    )
    assert res_bad_key.status_code == 401
    assert res_bad_key.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    # Verify that nothing was persisted for the unauthorized request
    token = _officer_token()
    get_res = client.get(
        "/api/v1/revenue/applications/GM-TEST-UNAUTH-001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 404


# ============================================================================
# Test F: Unsupported Contract Version
# ============================================================================
def test_f_unsupported_contract_version():
    payload = _base_payload("GM-TEST-UNSUPPORTED-VER")
    payload["request_version"] = "99.0"  # unsupported

    res = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNSUPPORTED_CONTRACT_VERSION"


# ============================================================================
# Test G: Conflicting Application Identity
# ============================================================================
def test_g_conflicting_application_identity():
    # First create valid application
    app_id = "GM-TEST-PHASE13-CONFLICT"
    valid_payload = _base_payload(app_id, citizen_name="Original Valid Citizen")
    init_res = client.post(
        "/api/v1/integrations/applications",
        json=valid_payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )
    assert init_res.status_code == 201

    # Send application with same ID but completely different citizen
    conflict_payload = _base_payload(app_id, citizen_name="Mismatched Impostor Name")
    conflict_payload["correlation_id"] = "CORR-DIFFERENT-999"

    res = client.post(
        "/api/v1/integrations/applications",
        json=conflict_payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )
    assert res.status_code == 409
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "APPLICATION_ID_CONFLICT"


# ============================================================================
# Test H: Service-to-Service JWT Authentication
# ============================================================================
def test_h_service_jwt_authentication():
    app_id = "GM-TEST-PHASE13-JWT-001"
    payload = _base_payload(app_id, citizen_name="JWT Authenticated Citizen")

    # Call with Administrator/Service JWT
    admin_tok = _admin_token()
    res = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "RECEIVED"


# ============================================================================
# Test I: End-to-End Workflow Processing of Ingested Application
# ============================================================================
def test_i_full_statutory_workflow_on_ingested_application():
    app_id = "GM-TEST-PHASE13-E2E-001"
    citizen_name = "Kavita Ramesh Kulkarni"
    payload = _base_payload(app_id, citizen_name=citizen_name)

    # 1. Ingest via Cross-Department Contract
    ingest_res = client.post(
        "/api/v1/integrations/applications",
        json=payload,
        headers={"X-GovMesh-API-Key": VALID_API_KEY},
    )
    assert ingest_res.status_code == 201
    assert ingest_res.json()["status"] == "RECEIVED"

    officer_tok = _officer_token()
    headers = {"Authorization": f"Bearer {officer_tok}"}

    # 2. Officer Workspace: Retrieve Application Details
    detail_res = client.get(f"/api/v1/revenue/applications/{app_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["status"] == "PENDING"

    # 3. Start Desk Scrutiny (PENDING -> PROCESSING)
    start_res = client.post(f"/api/v1/revenue/application/{app_id}/start-review", headers=headers)
    assert start_res.status_code == 200
    assert start_res.json()["data"]["status"] == "PROCESSING"

    # 4. Execute Address Verification Probe (POST /revenue/address/verify)
    probe_res = client.post(
        "/api/v1/revenue/address/verify",
        json={"application_id": app_id},
        headers=headers,
    )
    assert probe_res.status_code == 200
    probe_data = probe_res.json()["data"]
    assert probe_data["applicationId"] == app_id
    assert probe_data["validation"]["consent"] == "VALID"

    # 5. Execute Document Verification / OCR Matching
    doc_res = client.post(f"/api/v1/revenue/application/{app_id}/verify-document", headers=headers)
    assert doc_res.status_code == 200
    assert doc_res.json()["data"]["valid"] is True

    # 6. Statutory Officer Approval
    approve_res = client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        json={"decision": "APPROVE", "reason": "Address proof verified against Taluka land registry."},
        headers=headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] == "VERIFIED"

    # 7. Final Verification: Check Application is Finalized
    final_res = client.get(f"/api/v1/revenue/applications/{app_id}", headers=headers)
    assert final_res.status_code == 200
    assert final_res.json()["data"]["status"] == "VERIFIED"
    assert final_res.json()["data"]["completed_at"] is not None
