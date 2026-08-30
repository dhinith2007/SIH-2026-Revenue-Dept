def get_officer_token(client) -> str:
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "revenue.officer", "password": "Officer@2026"},
    )
    return login_resp.json()["access_token"]


def test_dashboard_summary_unauthenticated_returns_401(client):
    response = client.get("/api/v1/revenue/dashboard/summary")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_dashboard_summary_authenticated_returns_metrics(client):
    token = get_officer_token(client)
    response = client.get(
        "/api/v1/revenue/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    summary = data["data"]
    assert summary["total_incoming"] == 12
    assert summary["pending"] == 4
    assert summary["processing"] == 4
    assert summary["completed"] == 2
    assert summary["action_required"] == 1
    assert summary["failed_or_queued"] == 1
    assert summary["govmesh_connection"] == "DEMO ONLINE"
    assert summary["api_status"] == "ONLINE"
    assert "h" in summary["average_processing_time"] or "m" in summary["average_processing_time"]


def test_applications_list_unauthenticated_returns_401(client):
    response = client.get("/api/v1/revenue/applications")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_applications_list_pagination(client):
    token = get_officer_token(client)
    response = client.get(
        "/api/v1/revenue/applications?page=1&page_size=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["items"]) == 5
    assert data["data"]["pagination"]["page"] == 1
    assert data["data"]["pagination"]["page_size"] == 5
    assert data["data"]["pagination"]["total"] == 12
    assert data["data"]["pagination"]["total_pages"] == 3


def test_applications_list_filter_status_pending(client):
    token = get_officer_token(client)
    response = client.get(
        "/api/v1/revenue/applications?status=PENDING",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 4
    for item in items:
        assert item["status"] == "PENDING"


def test_applications_list_filter_priority_high(client):
    token = get_officer_token(client)
    response = client.get(
        "/api/v1/revenue/applications?priority=HIGH",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) >= 1
    for item in items:
        assert item["priority"] == "HIGH"


def test_applications_list_search_by_id_and_name(client):
    token = get_officer_token(client)
    
    # Search by Application ID
    resp_id = client.get(
        "/api/v1/revenue/applications?search=GM-2026-000124",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_id.status_code == 200
    items_id = resp_id.json()["data"]["items"]
    assert len(items_id) == 1
    assert items_id[0]["application_id"] == "GM-2026-000124"

    # Search by Citizen Name
    resp_name = client.get(
        "/api/v1/revenue/applications?search=Patil",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_name.status_code == 200
    items_name = resp_name.json()["data"]["items"]
    assert len(items_name) >= 1
    assert any("Patil" in it["citizen_name"] for it in items_name)


def test_application_detail_success(client):
    token = get_officer_token(client)
    response = client.get(
        "/api/v1/revenue/applications/GM-2026-000124",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    app = data["data"]
    assert app["application_id"] == "GM-2026-000124"
    assert app["correlation_id"] == "CORR-2026-000124"
    assert app["consent_reference"] == "CONSENT-2026-00124"
    assert "data_payload" in app
    assert "existing_address" in app["data_payload"]
    assert "new_address" in app["data_payload"]
    assert len(app["workflow_history"]) >= 1


def test_application_detail_not_found_returns_404(client):
    token = get_officer_token(client)
    response = client.get(
        "/api/v1/revenue/applications/GM-NONEXISTENT-999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
