import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


from app.services.auth_service import create_access_token


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


# ============================================================================
# 1. Full Analytics Dashboard Endpoints
# ============================================================================
def test_full_dashboard_analytics_authenticated(desk_officer_token):
    res = client.get("/api/v1/analytics/dashboard", headers=auth_header(desk_officer_token))
    assert res.status_code == 200
    data = res.json()["data"]

    # Verify root sections
    assert "division" in data
    assert "disclaimer" in data
    assert "kpis" in data
    assert "status_distribution" in data
    assert "trends" in data
    assert "verification" in data
    assert "confidence" in data
    assert "risks" in data
    assert "officer_workload" in data
    assert "recent_activity" in data

    # Verify Statutory Disclaimer Presence
    assert "assistive evidence analytics" in data["disclaimer"].lower()
    assert "revenue officer" in data["disclaimer"].lower()


def test_analytics_summary_kpi(desk_officer_token):
    res = client.get("/api/v1/analytics/summary", headers=auth_header(desk_officer_token))
    assert res.status_code == 200
    kpis = res.json()["data"]
    assert "total_applications" in kpis
    assert "pending_applications" in kpis
    assert "under_review" in kpis
    assert "approved" in kpis
    assert "rejected" in kpis
    assert "review_required" in kpis


def test_analytics_trends_date_window(desk_officer_token):
    res = client.get("/api/v1/analytics/trends?days=30", headers=auth_header(desk_officer_token))
    assert res.status_code == 200
    trends_data = res.json()["data"]
    assert len(trends_data["items"]) == 30
    assert trends_data["range_type"] == "30d"


def test_analytics_verification_and_ocr(desk_officer_token):
    res = client.get("/api/v1/analytics/verification", headers=auth_header(desk_officer_token))
    assert res.status_code == 200
    v_data = res.json()["data"]
    assert "total_documents" in v_data
    assert "ocr_success_rate" in v_data
    assert "average_ocr_confidence" in v_data


def test_analytics_confidence_and_risks(desk_officer_token):
    res_c = client.get("/api/v1/analytics/confidence", headers=auth_header(desk_officer_token))
    assert res_c.status_code == 200
    c_data = res_c.json()["data"]
    assert "HIGH_CONFIDENCE_MATCH" in c_data["recommendation_counts"]

    res_r = client.get("/api/v1/analytics/risks", headers=auth_header(desk_officer_token))
    assert res_r.status_code == 200
    r_data = res_r.json()["data"]
    assert "risk_flag_counts" in r_data


# ============================================================================
# 2. RBAC & Security Boundary Enforcement
# ============================================================================
def test_analytics_unauthenticated_blocked():
    res = client.get("/api/v1/analytics/dashboard")
    assert res.status_code == 401


def test_analytics_cross_division_isolation(cross_division_token):
    res = client.get("/api/v1/analytics/dashboard", headers=auth_header(cross_division_token))
    assert res.status_code == 200
    data = res.json()["data"]
    # Verify division is scoped to user's division (Baramati Tahsil / Division)
    assert "Baramati" in data["division"]
