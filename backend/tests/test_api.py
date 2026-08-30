def test_mock_applications_list(client):
    response = client.get("/api/v1/applications/mock")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 5
    app1 = data["data"][0]
    assert app1["application_id"] == "GM-2026-000124"
    assert "house_no" in app1
    assert "taluka" in app1
    assert "district" in app1


def test_mock_application_detail_found(client):
    response = client.get("/api/v1/applications/mock/GM-2026-000124")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["application_id"] == "GM-2026-000124"
    assert data["data"]["citizen_name"] == "Rajesh Shantaram Patil"


def test_mock_application_detail_not_found(client):
    response = client.get("/api/v1/applications/mock/GM-2026-999999")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "999999" in data["error"]["message"]
