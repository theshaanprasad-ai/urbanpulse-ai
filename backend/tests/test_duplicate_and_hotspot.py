"""
Unit tests for duplicate candidate detection and legacy hotspot clustering.
"""

from datetime import datetime, timedelta

from backend.app.engine.duplicate_detector import DuplicateDetector
from backend.app.engine.hotspot_detector import HotspotDetector

NOW = datetime(2026, 10, 1, 12, 0)


def _c(id_, lat, lon, minutes_ago, text, cat="DRAINAGE_SANITATION", zone="chennai-zone-04", linked=None):
    return {
        "id": id_, "lat": lat, "lon": lon, "zone_id": zone, "reported_at": NOW - timedelta(minutes=minutes_ago),
        "raw_text": text, "issue_category": cat, "linked_incident_id": linked,
    }


def test_duplicate_matching_detection():
    c1 = _c(1, 13.1160, 80.2612, 0, "Waterlogging near Vyasarpadi subway. Traffic blocked.")
    c2 = _c(2, 13.1162, 80.2610, 25, "Vyasarpadi subway ke neeche pani bhara hai. Traffic completely blocked.")
    score, details = DuplicateDetector.evaluate_pair(c1, c2)
    assert score >= 0.60
    assert details["suggested_action"] in ["LIKELY_DUPLICATE", "POSSIBLE_DUPLICATE"]
    assert details["distance_meters"] <= 100.0
    assert "not a probability" in details["explanation"]


def test_duplicate_hard_gates():
    base = _c(1, 13.1160, 80.2612, 0, "Garbage pile near bus stop", cat="WASTE_MANAGEMENT")
    far = _c(2, 13.1300, 80.2612, 5, "Garbage pile near bus stop", cat="WASTE_MANAGEMENT")
    old = _c(3, 13.1160, 80.2612, 60 * 72, "Garbage pile near bus stop", cat="WASTE_MANAGEMENT")
    assert DuplicateDetector.evaluate_pair(base, far) == (0.0, None)
    assert DuplicateDetector.evaluate_pair(base, old) == (0.0, None)


def test_duplicate_missing_coordinates_uses_same_zone_only():
    a = _c(1, None, None, 0, "Garbage pile near bus stop not collected", cat="WASTE_MANAGEMENT")
    b = _c(2, None, None, 30, "Garbage pile near bus stop not collected", cat="WASTE_MANAGEMENT")
    other_zone = _c(3, None, None, 30, "Garbage pile near bus stop not collected", cat="WASTE_MANAGEMENT", zone="chennai-zone-09")
    score, details = DuplicateDetector.evaluate_pair(a, b)
    assert details is not None and details["distance_meters"] is None
    assert DuplicateDetector.evaluate_pair(a, other_zone) == (0.0, None)


def test_category_mismatch_lowers_score():
    a = _c(1, 13.1160, 80.2612, 0, "Overflowing drain near the market")
    b = _c(2, 13.1160, 80.2612, 10, "Overflowing drain near the market")
    b_other = dict(b, issue_category="WASTE_MANAGEMENT")
    s_same, _ = DuplicateDetector.evaluate_pair(a, b)
    s_diff, _ = DuplicateDetector.evaluate_pair(a, b_other)
    assert s_diff < s_same


def test_candidate_scan_respects_reviews_and_links():
    a = _c(1, 13.1160, 80.2612, 0, "Drain blocked near the school gate")
    b = _c(2, 13.1161, 80.2612, 15, "Drain blocked near the school gate")
    c = _c(3, 12.9000, 80.2000, 20, "Streetlight off", cat="STREETLIGHTS_ELECTRICITY", zone="chennai-zone-15")
    found = DuplicateDetector.find_duplicate_candidates([a, b, c])
    assert len(found) == 1
    assert {found[0]["complaint_a"]["id"], found[0]["complaint_b"]["id"]} == {1, 2}
    assert DuplicateDetector.find_duplicate_candidates([a, b, c], exclude_pairs=[(2, 1)]) == []
    a2, b2 = dict(a, linked_incident_id=7), dict(b, linked_incident_id=7)
    assert DuplicateDetector.find_duplicate_candidates([a2, b2]) == []
    assert DuplicateDetector.find_duplicate_candidates([]) == []


def test_hotspot_spatial_clustering():
    complaints = [
        {"id": 1, "city_id": "chennai", "zone_id": "chennai-zone-14", "lat": 12.9818, "lon": 80.2182, "landmark": "Velachery Main Rd"},
        {"id": 2, "city_id": "chennai", "zone_id": "chennai-zone-14", "lat": 12.9820, "lon": 80.2180, "landmark": "Velachery Main Rd"},
        {"id": 3, "city_id": "chennai", "zone_id": "chennai-zone-14", "lat": 12.9815, "lon": 80.2185, "landmark": "Velachery Main Rd"},
        {"id": 4, "city_id": "chennai", "zone_id": "chennai-zone-01", "lat": 13.2000, "lon": 80.3200, "landmark": "Ennore"},
    ]
    clusters = HotspotDetector.detect_clusters(complaints, eps_meters=400.0, min_samples=2)
    assert len(clusters) == 1
    assert clusters[0]["complaint_count"] == 3
    assert clusters[0]["anomaly_ratio"] > 1.0
