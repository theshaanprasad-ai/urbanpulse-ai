import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["app_name"] in ["UrbanPulse AI", "MonsoonWatch India"]


def test_cities_and_zones(client):
    response = client.get("/api/cities")
    assert response.status_code == 200
    cities = response.json()
    assert len(cities) >= 1
    assert any(c["id"] == "chennai" for c in cities)

    zone_resp = client.get("/api/zones?city_id=chennai")
    assert zone_resp.status_code == 200
    zones = zone_resp.json()
    assert len(zones) == 15


def test_rainfall_intelligence_endpoints(client):
    obs_resp = client.get("/api/rainfall/observations?city_id=chennai")
    assert obs_resp.status_code == 200
    assert len(obs_resp.json()) >= 1

    analytics_resp = client.get("/api/rainfall/analytics?city_id=chennai")
    assert analytics_resp.status_code == 200
    analytics = analytics_resp.json()
    assert "imd_24h_category" in analytics
    assert "antecedent_precipitation_index" in analytics


def test_complaints_ingestion_and_classification(client):
    # Submit a complaint in Hinglish
    payload = {
        "city_id": "chennai",
        "raw_text": "Vyasarpadi subway ke neeche 3 feet paani bhara hai, ambulance phansi hui hai!",
        "landmark": "Vyasarpadi Subway"
    }
    resp = client.post("/api/civic/complaints", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["issue_category"] in ["ROAD_FLOODING", "WATERLOGGING", "DRAINAGE_SANITATION"]
    assert created["severity_score"] >= 4
    assert created["zone_id"] == "chennai-zone-04"


def test_risk_assessments_endpoint(client):
    resp_mode1 = client.get("/api/risk/assessments?city_id=chennai&mode=MODE_1_BASELINE")
    assert resp_mode1.status_code == 200
    assessments1 = resp_mode1.json()
    assert len(assessments1) == 15
    assert all("overall_risk_score" in a for a in assessments1)

    resp_mode2 = client.get("/api/risk/assessments?city_id=chennai&mode=MODE_2_ML")
    assert resp_mode2.status_code == 200
    assessments2 = resp_mode2.json()
    assert len(assessments2) == 15


def test_what_if_scenario_endpoint(client):
    payload = {
        "city_id": "chennai",
        "additional_rainfall_mm": 50.0,
        "drainage_blockage_pct": 20.0
    }
    resp = client.post("/api/risk/what-if", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["average_risk_increase_pct"] > 0.0


def test_system_alerts_and_decision_actions(client):
    alerts_resp = client.get("/api/alerts?city_id=chennai")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    # Check alert classes exist
    assert any(a["alert_class"] in ["OFFICIAL_WEATHER_ALERT", "MODEL_IMPACT_RISK", "CIVIC_ANOMALY"] for a in alerts)

    actions_resp = client.get("/api/actions?city_id=chennai")
    assert actions_resp.status_code == 200
    actions = actions_resp.json()
    assert len(actions) >= 1
    first_action_id = actions[0]["id"]

    # Test action state transition & audit log
    update_payload = {
        "status": "ACKNOWLEDGED",
        "assigned_to": "Zone 4 Rapid Response Unit",
        "operator_name": "Duty Officer Karthik",
        "reason": "Immediate priority due to reported hospital ambulance bottleneck"
    }
    up_resp = client.post(f"/api/actions/{first_action_id}/update", json=update_payload)
    assert up_resp.status_code == 200
    assert up_resp.json()["status"] == "ACKNOWLEDGED"


def test_climate_and_evaluation_reports(client):
    clim_resp = client.get("/api/climate/scenarios?city_id=chennai")
    assert clim_resp.status_code == 200
    assert len(clim_resp.json()) >= 3

    eval_resp = client.get("/api/evaluation/report?city_id=chennai")
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["metrics"]["f1_score"] > 0.80
    assert "confusion_matrix" in eval_data


TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_photo_report_creates_complaint(client):
    resp = client.post("/api/civic/photo-report", json={
        "city_id": "chennai",
        "image_base64": TINY_PNG,
        "mime_type": "image/png",
        "note": "Big pothole on Velachery Main Road blocking two-wheelers",
        "hint_category": "ROADS_INFRASTRUCTURE",
        "landmark": "Velachery Main Road",
        "reporter_email": "resident@example.com",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["tracking_number"].startswith("GCC-2026-PHOTO-")
    assert data["complaint"]["issue_category"] in [
        "ROADS_INFRASTRUCTURE", "DRAINAGE_SANITATION", "WASTE_MANAGEMENT", "OTHER"
    ]
    assert data["scan"]["scan_source"] in ["GEMINI_VISION", "LOCAL_RULES"]
    assert "Report" in data["citizen_report"]
    assert data["complaint"]["reporter_email"] == "resident@example.com"

