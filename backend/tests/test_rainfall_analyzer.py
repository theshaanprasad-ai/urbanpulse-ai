"""
Unit tests for Rainfall Analyzer and IMD Threshold Classification.
"""

import pytest
from backend.app.engine.rainfall_analyzer import RainfallAnalyzer, IMDThreshold


def test_imd_classification_thresholds():
    cat, col, level = IMDThreshold.classify_24h(0.0)
    assert cat == "No Rain"
    assert level == "NORMAL"

    cat, col, level = IMDThreshold.classify_24h(10.0)
    assert cat == "Light Rain"

    cat, col, level = IMDThreshold.classify_24h(45.0)
    assert cat == "Moderate Rain"
    assert level == "WATCH"

    cat, col, level = IMDThreshold.classify_24h(85.0)
    assert "Heavy Rain" in cat
    assert level == "WARNING"

    cat, col, level = IMDThreshold.classify_24h(150.0)
    assert "Very Heavy Rain" in cat
    assert level == "ALERT"

    cat, col, level = IMDThreshold.classify_24h(250.0)
    assert "Extremely Heavy Rain" in cat
    assert level == "CRITICAL"


def test_antecedent_precipitation_index():
    # Sequence of dry and wet days
    series = [10.0, 20.0, 0.0, 50.0]
    api = RainfallAnalyzer.calculate_antecedent_precipitation_index(series, decay_factor=0.85)
    assert api > 0.0
    assert isinstance(api, float)

    # Dry sequence must yield 0.0
    dry_series = [0.0, 0.0, 0.0]
    assert RainfallAnalyzer.calculate_antecedent_precipitation_index(dry_series) == 0.0


def test_short_duration_intensity_evaluation():
    # Cloudburst / torrential rate
    res = RainfallAnalyzer.compute_short_duration_intensity(rainfall_1h_mm=65.0, rainfall_3h_mm=90.0)
    assert res["severity"] == "CRITICAL"
    assert res["intensity_status"] == "TORRENTIAL_BURST"

    # Light rain
    res_light = RainfallAnalyzer.compute_short_duration_intensity(rainfall_1h_mm=5.0, rainfall_3h_mm=10.0)
    assert res_light["severity"] == "LOW"


def test_haversine_distance_calculation():
    # Distance between Nungambakkam and Meenambakkam Airport (~11 km)
    dist = RainfallAnalyzer.haversine_distance_km(13.0670, 80.2430, 12.9880, 80.1770)
    assert 10.0 <= dist <= 13.0
