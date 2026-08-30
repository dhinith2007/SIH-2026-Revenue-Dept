def test_root_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "revenue-department"
    assert "timestamp" in data
    assert "version" in data


def test_v1_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "revenue-department"


def test_root_db_health_endpoint(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "latency_ms" in data
    assert data["database"] == "PostgreSQL" or data["database"] == "disconnected" or "status" in data


def test_revenue_system_info(client):
    response = client.get("/api/v1/revenue/system-info")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["department"] == "Revenue & Forest Department"
    assert data["data"]["project_code"] == "SIH26129"
    assert data["data"]["simulated"] is True
