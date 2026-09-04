from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.application_repository import ApplicationRepository
from app.api.deps import get_application_repository

client = TestClient(app)

def get_auth_token():
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    assert res.status_code == 200
    data = res.json()
    return data.get("access_token") or data.get("data", {}).get("access_token")


def test_govmesh_dynamic_application_ingress():
    token = get_auth_token()
    app_id = "GM-2026-988979"
    corr_id = "CORR-26-GM-2026-988979"
    created_at = "2026-09-04T08:00:00.000Z"
    sent_at = "2026-09-04T08:00:01.000Z"
    req_hash = "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
    doc_hash = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    payload = {
        "application_id": app_id,
        "correlation_id": corr_id,
        "request_version": 1,
        "canonical_hash": req_hash,
        "document_hash": doc_hash,
        "citizen_name": "Rajesh Shantaram Patil",
        "new_address": {
            "line": "Flat 402, Shiv Shanti Heights, Deccan Gymkhana",
            "house_no": "402",
            "street": "Shiv Shanti Heights",
            "village": "Deccan Gymkhana",
            "taluka": "Haveli",
            "district": "Pune",
            "pincode": "411004"
        },
        "consent_id": "CNS-2026-988979",
        "created_at": created_at,
        "sent_at": sent_at,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Correlation-ID": corr_id,
        "X-GovMesh-App-ID": app_id,
        "X-GovMesh-Request-Hash": req_hash,
        "X-GovMesh-Sent-At": sent_at,
    }

    res = client.post("/api/v1/revenue/address/verify", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["applicationId"] == app_id
    assert data["correlationId"] == corr_id
    assert data["acknowledgementId"] == f"ACK-REV-{app_id.replace('-', '')}"
    assert data["department"] == "REVENUE"
    assert data["hashStatus"] == "VERIFIED"
    assert data["requestHash"] == req_hash
    assert data["documentHash"] == doc_hash
    assert data["receivedAt"] is not None
    assert data["validatedAt"] is not None
    assert data["acceptedAt"] is not None
    assert data["validation"]["consent"] == "VALID"
    assert data["validation"]["data"] == "VALID"

    # Verify application is now in repository
    app_repo = ApplicationRepository()
    saved = app_repo.get_by_application_id(app_id)
    assert saved is not None
    assert saved["citizen_name"] == "Rajesh Shantaram Patil"
    assert saved["status"] == "PENDING"
    assert saved["data_payload"]["canonical_hash"] == req_hash

def test_govmesh_interoperability_address_update_alias():
    token = get_auth_token()
    app_id = "GM-2026-778899"
    corr_id = "CORR-26-GM-2026-778899"
    req_hash = "sha256:55aa55aa55aa55aa55aa55aa55aa55aa55aa55aa55aa55aa55aa55aa55aa55aa"
    doc_hash = "sha256:11bb11bb11bb11bb11bb11bb11bb11bb11bb11bb11bb11bb11bb11bb11bb11bb"

    payload = {
        "application_id": app_id,
        "correlation_id": corr_id,
        "request_version": 1,
        "canonical_hash": req_hash,
        "document_hash": doc_hash,
        "citizen_name": "Suresh Namdeo Shinde",
        "new_address": {
            "house_no": "105",
            "street": "Kothrud Depot Road",
            "village": "Kothrud",
            "taluka": "Haveli",
            "district": "Pune",
            "pincode": "411038"
        },
        "consent_id": "CNS-2026-778899",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    res = client.post(
        "/api/v1/revenue/interoperability/address-update",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["applicationId"] == app_id
    assert data["acknowledgementId"] == f"ACK-REV-{app_id.replace('-', '')}"
    assert data["status"] == "PENDING"

def test_idempotent_duplicate_ingress():
    token = get_auth_token()
    app_id = "GM-2026-988979"

    payload = {
        "application_id": app_id,
        "citizen_name": "Rajesh Shantaram Patil",
        "consent_id": "CNS-2026-988979",
        "new_address": {
            "house_no": "402",
            "street": "Shiv Shanti Heights",
            "village": "Deccan Gymkhana",
            "taluka": "Haveli",
            "district": "Pune",
            "pincode": "411004"
        }
    }

    res1 = client.post("/api/v1/revenue/address/verify", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200

    res2 = client.post("/api/v1/revenue/address/verify", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    assert res1.json()["data"]["acknowledgementId"] == res2.json()["data"]["acknowledgementId"]

def test_officer_lifecycle_and_callback():
    token = get_auth_token()
    app_id = "GM-2026-988979"
    corr_id = "CORR-26-GM-2026-988979"
    headers = {"Authorization": f"Bearer {token}"}

    # First ingest the dynamic application
    ingest_payload = {
        "application_id": app_id,
        "correlation_id": corr_id,
        "citizen_name": "Rajesh Shantaram Patil",
        "consent_id": "CNS-2026-988979",
        "new_address": {
            "house_no": "402",
            "street": "Shiv Shanti Heights",
            "village": "Deccan Gymkhana",
            "taluka": "Haveli",
            "district": "Pune",
            "pincode": "411004"
        }
    }
    res_ingest = client.post("/api/v1/revenue/address/verify", json=ingest_payload, headers=headers)
    assert res_ingest.status_code == 200

    # Start review
    res_review = client.post(f"/api/v1/revenue/application/{app_id}/start-review", headers=headers)
    assert res_review.status_code == 200
    assert res_review.json()["data"]["status"] == "PROCESSING"

    # Approve
    res_approve = client.post(
        f"/api/v1/revenue/application/{app_id}/approve",
        json={"reason": "Live E2E verification confirmed by Revenue Officer"},
        headers=headers,
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["data"]["status"] == "VERIFIED"

