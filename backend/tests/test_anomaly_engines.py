"""
Unit tests for the statistical engines: temporal anomaly tests, FDR correction, spatial clusters,
neighbourhood pooling, cross-category hypotheses and the synthetic benchmark.
"""

from datetime import datetime, timedelta

import numpy as np
import pytest

from backend.app.engine import temporal_anomaly_engine as tae
from backend.app.engine.cross_category_engine import DISCLAIMER, discover_patterns
from backend.app.engine.spatiotemporal_engine import neighbourhood_tests, point_clusters, zone_neighbours

AS_OF = datetime(2026, 10, 1, 12, 0)


def _poisson_counts(rate, seed=1, n=tae.N_WINDOWS):
    return np.random.default_rng(seed).poisson(rate, n)


# ---------------- temporal ----------------

def test_window_index_boundaries():
    assert tae.window_index(AS_OF, AS_OF) == 0
    assert tae.window_index(AS_OF - timedelta(hours=24), AS_OF) == 0
    assert tae.window_index(AS_OF - timedelta(hours=24, seconds=1), AS_OF) == 1
    assert tae.window_index(AS_OF + timedelta(minutes=1), AS_OF) == -1


def test_normal_cell_is_not_flagged():
    counts = _poisson_counts(2.0, seed=3)
    counts[0] = 2
    cell = tae.evaluate_cell(counts, covered=tae.N_WINDOWS)
    assert cell.status == "TESTED"
    assert cell.test_1d.p_value > 0.05
    assert tae.classify_level(cell.test_1d.p_value, cell.test_1d.p_value, cell.test_1d.observed) == "NORMAL"


def test_spike_is_detected_with_expected_and_ci():
    counts = _poisson_counts(1.0, seed=4)
    counts[0] = 12
    cell = tae.evaluate_cell(counts, covered=tae.N_WINDOWS)
    t = cell.test_1d
    assert t.observed == 12
    assert t.p_value < 1e-4
    assert t.expected < 3
    lo, hi = t.expected_ci95
    assert lo <= t.expected <= hi
    assert t.upper_prediction95 < 12
    assert tae.temporal_pattern(counts, cell) == "SPIKE"


def test_sustained_increase_pattern():
    counts = _poisson_counts(1.0, seed=5)
    counts[0], counts[1], counts[2] = 6, 7, 6
    cell = tae.evaluate_cell(counts, covered=tae.N_WINDOWS)
    assert cell.test_3d.p_value < 1e-4
    assert tae.temporal_pattern(counts, cell) == "SUSTAINED_INCREASE"


def test_sparse_history_is_insufficient_not_flagged():
    counts = np.zeros(tae.N_WINDOWS, dtype=int)
    counts[0] = 10
    cell = tae.evaluate_cell(counts, covered=10)
    assert cell.status == "INSUFFICIENT_HISTORY"
    assert cell.test_1d is None


def test_zero_baseline_rare_issue():
    counts = np.zeros(tae.N_WINDOWS, dtype=int)
    counts[0] = 4
    cell = tae.evaluate_cell(counts, covered=tae.N_WINDOWS)
    assert cell.status == "TESTED"
    assert cell.robust_z is None  # MAD = 0 -> no robust z
    assert np.isfinite(cell.test_1d.expected) and cell.test_1d.expected > 0
    assert cell.test_1d.p_value < 0.01
    assert tae.lifecycle(cell) == "NEW_OR_RARE"


def test_empty_cell_never_significant():
    counts = np.zeros(tae.N_WINDOWS, dtype=int)
    cell = tae.evaluate_cell(counts, covered=tae.N_WINDOWS)
    assert cell.test_1d.p_value == 1.0
    assert cell.test_3d.p_value == 1.0


def test_overdispersed_baseline_uses_negative_binomial_and_is_more_conservative():
    rng = np.random.default_rng(7)
    counts = rng.negative_binomial(1, 1 / 4, tae.N_WINDOWS)  # mean 3, var 12
    counts[0] = 12
    cell = tae.evaluate_cell(counts, covered=tae.N_WINDOWS)
    assert cell.overdispersed
    assert cell.test_1d.method == tae.METHOD_NB
    # same data under a Poisson assumption gives a smaller p-value
    f = np.ones(tae.N_WINDOWS)
    base_idx = list(range(3, 31))
    poisson = tae._test_window(counts, f, [0], base_idx, None)
    assert cell.test_1d.p_value > poisson.p_value


def test_weekday_factors_require_history_and_normalise():
    weekdays = tae.window_weekdays(AS_OF)
    counts = np.array([5 if w >= 5 else 1 for w in weekdays])
    assert tae.weekday_factors(counts, weekdays, covered=20) is None
    f = tae.weekday_factors(counts, weekdays, covered=tae.N_WINDOWS)
    assert f is not None
    assert f.mean() == pytest.approx(1.0)
    assert f[5] > 1 and f[0] < 1


def test_weekday_adjustment_suppresses_expected_weekend_peak():
    sunday_evening = datetime(2026, 10, 4, 23, 0)
    weekdays = tae.window_weekdays(sunday_evening)
    assert weekdays[0] == 6
    counts = np.array([6 if w >= 5 else 1 for w in weekdays])
    f = tae.weekday_factors(counts, weekdays, covered=tae.N_WINDOWS)
    adj = tae._test_window(counts, f[weekdays], [0], list(range(3, 31)), None)
    raw = tae._test_window(counts, np.ones(len(counts)), [0], list(range(3, 31)), None)
    assert adj.p_value > raw.p_value
    assert adj.p_value > 0.05


def test_benjamini_hochberg():
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    q = tae.benjamini_hochberg(p)
    assert q[0] == pytest.approx(0.01)
    assert np.all(q >= np.array(p))
    assert np.all(q <= 1)
    assert sum(q <= 0.05) == 2
    assert len(tae.benjamini_hochberg([])) == 0


def test_classify_level_requires_minimum_count():
    assert tae.classify_level(0.001, 0.0001, 2) == "NORMAL"
    assert tae.classify_level(0.01, 0.001, 3) == "ANOMALY"
    assert tae.classify_level(0.2, 0.005, 3) == "WATCH"


def test_large_but_stable_area_not_flagged():
    counts = _poisson_counts(40.0, seed=11)
    counts[0] = 42
    cell = tae.evaluate_cell(counts, covered=tae.N_WINDOWS)
    assert cell.test_1d.p_value > 0.05


def test_share_test_separates_general_volume_rise():
    # category share unchanged (10%) while overall zone volume doubled
    assert tae.share_test(10, 100, 50, 500) > 0.3
    # category share jumped from 10% to 40%
    assert tae.share_test(40, 100, 50, 500) < 1e-6
    assert tae.share_test(0, 10, 5, 50) is None


# ---------------- spatial ----------------

def _rec(i, lat, lon, ts, cat="WASTE_MANAGEMENT", zone="z1"):
    return {"id": i, "lat": lat, "lon": lon, "reported_at": ts, "issue_category": cat, "zone_id": zone, "landmark": "X"}


def test_point_cluster_new_hotspot_significant():
    recs = [_rec(i, 13.0 + i * 1e-4, 80.2, AS_OF - timedelta(hours=i + 1)) for i in range(6)]
    # background elsewhere so history coverage exists but not at this spot
    recs += [_rec(100 + d, 13.05, 80.25, AS_OF - timedelta(days=d + 4)) for d in range(28)]
    out = point_clusters(recs, AS_OF, covered_days=35)
    hot = [c for c in out if abs(c["center_lat"] - 13.00025) < 0.001]
    assert hot and hot[0]["observed"] == 6
    assert hot[0]["baseline_count"] == 0
    assert hot[0]["significant"]


def test_point_cluster_chronic_location_not_significant():
    recs = []
    k = 0
    for d in range(31):
        for h in (3, 15):
            recs.append(_rec(k, 13.0, 80.2 + (k % 3) * 1e-4, AS_OF - timedelta(days=d, hours=h)))
            k += 1
    out = point_clusters(recs, AS_OF, covered_days=35)
    assert out and not out[0]["significant"]


def test_point_cluster_skips_missing_coordinates_and_short_history():
    recs = [_rec(i, None, None, AS_OF - timedelta(hours=i)) for i in range(5)]
    assert point_clusters(recs, AS_OF, covered_days=35) == []
    recs = [_rec(i, 13.0, 80.2, AS_OF - timedelta(hours=i)) for i in range(5)]
    assert point_clusters(recs, AS_OF, covered_days=10) == []
    assert point_clusters([], AS_OF, covered_days=35) == []


def test_zone_neighbours_and_neighbourhood_increase():
    zones = [
        {"id": "a", "center_lat": 13.00, "center_lon": 80.20},
        {"id": "b", "center_lat": 13.03, "center_lon": 80.20},
        {"id": "c", "center_lat": 13.50, "center_lon": 80.20},
    ]
    nb = zone_neighbours(zones)
    assert nb["a"] == ["b"] and nb["c"] == []

    def cell(obs):
        return {"observed_3d": obs, "baseline_total": 28, "f_obs_3d": 3.0, "f_base": 28.0, "expected_3d": 3.05}

    cells = {("a", "W"): cell(9), ("b", "W"): cell(9), ("c", "W"): cell(3)}
    out = neighbourhood_tests(cells, nb, {"a": "A", "b": "B", "c": "C"})
    assert len(out) == 1  # a+b and b+a deduplicated
    assert set(out[0]["zones_above_expected"]) == {"a", "b"}
    assert out[0]["q_value"] <= 0.05

    calm = {("a", "W"): cell(3), ("b", "W"): cell(4), ("c", "W"): cell(3)}
    assert neighbourhood_tests(calm, nb, {}) == []


# ---------------- cross-category ----------------

def test_cross_category_pattern_is_hypothesis_with_disclaimer():
    daily = np.zeros(31)
    zone_cells = {
        "z1": {
            "WASTE_MANAGEMENT": {"p_3d": 0.001, "observed_3d": 8, "expected_3d": 2.0, "daily_counts": daily},
            "DRAINAGE_SANITATION": {"p_3d": 0.002, "observed_3d": 6, "expected_3d": 1.5, "daily_counts": daily},
            "POWER_SUPPLY": {"p_3d": 0.5, "observed_3d": 3, "expected_3d": 3.0, "daily_counts": daily},
        }
    }
    recent = {
        ("z1", "WASTE_MANAGEMENT"): [_rec(1, 13.0, 80.2, AS_OF, "WASTE_MANAGEMENT")],
        ("z1", "DRAINAGE_SANITATION"): [_rec(2, 13.001, 80.2, AS_OF - timedelta(hours=2), "DRAINAGE_SANITATION")],
    }
    out = discover_patterns(zone_cells, recent, {"z1": "Zone 1"})
    assert len(out) == 1
    p = out[0]
    assert {p["category_a"], p["category_b"]} == {"WASTE_MANAGEMENT", "DRAINAGE_SANITATION"}
    assert p["disclaimer"] == DISCLAIMER
    assert p["hypothesis_source"] == "DOMAIN_RULE_TEMPLATE"
    assert p["colocated_pair_count"] == 1
    assert p["spearman_rho_daily"] is None  # constant series -> undefined, not invented
    assert "not" in p["disclaimer"].lower() and "caus" in p["disclaimer"].lower()


def test_cross_category_requires_both_elevated():
    zone_cells = {"z1": {"WASTE_MANAGEMENT": {"p_3d": 0.001, "observed_3d": 8, "expected_3d": 2.0, "daily_counts": np.zeros(31)}}}
    assert discover_patterns(zone_cells, {}, {}) == []
    assert discover_patterns({}, {}, {}) == []


# ---------------- benchmark ----------------

def test_benchmark_is_labelled_synthetic_and_reproducible():
    from backend.app.engine.evaluation import run_benchmark

    a = run_benchmark(null_per_rate=40, injected_per_rate=10)
    b = run_benchmark(null_per_rate=40, injected_per_rate=10)
    assert a["is_synthetic"] is True
    assert a["overall"] == b["overall"]
    assert 0.0 <= a["overall"]["false_positive_rate"] <= 1.0
    assert a["limitations"]
