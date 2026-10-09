"""
Unit tests for Urban Impact Risk Engine (Mode 1 Baseline & Mode 2 ML & What-If).
"""

import pytest
from backend.app.engine.impact_risk_engine import UrbanImpactRiskEngine


@pytest.fixture
def risk_engine():
    return UrbanImpactRiskEngine()


def test_mode1_baseline_calculation(risk_engine):
    # Low-elevation, high impervious, heavy rain ward (e.g. Velachery / Perungudi)
    res_high = risk_engine.calculate_mode1_baseline(
        zone_name="Perungudi / Velachery",
        forecast_24h_mm=140.0,
        rainfall_3h_mm=50.0,
        api_moisture_index=65.0,
        elevation_m=3.4,
        impervious_fraction=0.85,
        drainage_density_km_per_sqkm=1.5,
        historical_flood_vulnerability=0.95,
        active_complaint_count=5,
        subway_count_nearby=1
    )
    assert res_high["risk_category"] in ["HIGH", "CRITICAL"]
    assert res_high["overall_risk_score"] >= 70.0
    assert len(res_high["contributing_factors"]) == 6
    assert res_high["confidence_score"] > 0.70

    # High elevation, low impervious, zero rain ward (safe highland)
    res_low = risk_engine.calculate_mode1_baseline(
        zone_name="Safe Highland",
        forecast_24h_mm=0.0,
        rainfall_3h_mm=0.0,
        api_moisture_index=0.0,
        elevation_m=20.0,
        impervious_fraction=0.30,
        drainage_density_km_per_sqkm=2.8,
        historical_flood_vulnerability=0.10,
        active_complaint_count=0,
        subway_count_nearby=0
    )
    assert res_low["risk_category"] == "LOW"
    assert res_low["overall_risk_score"] < 25.0


def test_mode2_ml_calculation(risk_engine):
    res_ml = risk_engine.calculate_mode2_ml(
        forecast_24h_mm=120.0,
        api_moisture_index=60.0,
        elevation_m=3.5,
        impervious_fraction=0.88,
        active_complaint_count=8,
        historical_flood_vulnerability=0.9
    )
    assert "calibrated_flood_probability" in res_ml
    assert 0.0 <= res_ml["calibrated_flood_probability"] <= 1.0
    assert len(res_ml["feature_importances"]) == 6


def test_what_if_scenario_simulation(risk_engine):
    baseline_mocks = [
        {
            "zone_id": "z1",
            "zone_name": "Ward 1",
            "overall_risk_score": 50.0,
            "risk_category": "ELEVATED",
            "supporting_evidence": {"elevation_m": 4.0, "impervious_fraction": 0.8}
        },
        {
            "zone_id": "z2",
            "zone_name": "Ward 2",
            "overall_risk_score": 30.0,
            "risk_category": "MODERATE",
            "supporting_evidence": {"elevation_m": 12.0, "impervious_fraction": 0.5}
        }
    ]
    sim = risk_engine.simulate_what_if_scenario(
        baseline_assessments=baseline_mocks,
        additional_rainfall_mm=60.0,
        drainage_blockage_pct=30.0
    )
    assert sim["average_risk_increase_pct"] > 0.0
    assert len(sim["ward_projected_risks"]) == 2
    assert sim["ward_projected_risks"][0]["projected_score"] > 50.0
