"""
Synthetic-injection benchmark for the temporal detector.

Generates seeded synthetic complaint-count series (Poisson and overdispersed negative-binomial),
injects known anomalies (x3 one-day spikes, x2 three-day sustained increases), runs the production
detector with the same BH correction, and reports confusion counts. These numbers describe detector
behaviour on simulated data only; they are not real-world accuracy.
"""

from typing import Any, Dict, List

import numpy as np

from backend.app.engine.temporal_anomaly_engine import (
    N_WINDOWS, benjamini_hochberg, classify_level, evaluate_cell,
)

RATE_BUCKETS = [0.3, 0.7, 1.5, 3.0, 6.0]
SCENARIOS = ["NONE", "SPIKE_X3", "SUSTAINED_X2"]


def _counts(rng: np.random.Generator, rate: float, n: int, overdispersed: bool) -> np.ndarray:
    if overdispersed:
        size = 4.0
        return rng.negative_binomial(size, size / (size + rate), n)
    return rng.poisson(rate, n)


def _metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, Any]:
    return {
        "true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": tn,
        "precision": round(tp / (tp + fp), 3) if tp + fp else None,
        "recall": round(tp / (tp + fn), 3) if tp + fn else None,
        "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else None,
    }


def run_benchmark(seed: int = 20261009, null_per_rate: int = 240, injected_per_rate: int = 30) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    series: List[Dict[str, Any]] = []
    for rate in RATE_BUCKETS:
        for scenario in SCENARIOS:
            for k in range(null_per_rate if scenario == "NONE" else injected_per_rate):
                over = k % 2 == 1
                c = _counts(rng, rate, N_WINDOWS, over)
                if scenario == "SPIKE_X3":
                    c[0] = _counts(rng, rate * 3, 1, over)[0]
                elif scenario == "SUSTAINED_X2":
                    c[0:3] = _counts(rng, rate * 2, 3, over)
                series.append({"rate": rate, "scenario": scenario, "overdispersed": over, "counts": c})

    pvals: List[float] = []
    obs: List[int] = []
    for s in series:
        r = evaluate_cell(s["counts"], covered=N_WINDOWS, with_history=False)
        s["raw_count_3d"] = int(s["counts"][:3].sum())
        for t in (r.test_1d, r.test_3d):
            pvals.append(t.p_value)
            obs.append(t.observed)
    q = benjamini_hochberg(pvals)
    for i, s in enumerate(series):
        levels = [classify_level(q[2 * i + j], pvals[2 * i + j], obs[2 * i + j]) for j in (0, 1)]
        s["flagged"] = "ANOMALY" in levels

    def tally(rows: List[Dict[str, Any]], flag_key: str = "flagged") -> Dict[str, Any]:
        tp = sum(1 for r in rows if r[flag_key] and r["scenario"] != "NONE")
        fp = sum(1 for r in rows if r[flag_key] and r["scenario"] == "NONE")
        fn = sum(1 for r in rows if not r[flag_key] and r["scenario"] != "NONE")
        tn = sum(1 for r in rows if not r[flag_key] and r["scenario"] == "NONE")
        return _metrics(tp, fp, fn, tn)

    by_rate = []
    for rate in RATE_BUCKETS:
        rows = [s for s in series if s["rate"] == rate]
        by_rate.append({"baseline_rate_per_day": rate, **tally(rows)})
    by_scenario = []
    for scen in SCENARIOS[1:]:
        rows = [s for s in series if s["scenario"] in ("NONE", scen)]
        by_scenario.append({"scenario": scen, **tally(rows)})
    by_dispersion = []
    for over in (False, True):
        rows = [s for s in series if s["overdispersed"] == over]
        by_dispersion.append({"overdispersed": over, **tally(rows)})

    # Comparator: flag the same number of series by largest raw 72h count (what a volume ranking would do).
    n_flagged = sum(1 for s in series if s["flagged"])
    ranked = sorted(range(len(series)), key=lambda i: series[i]["raw_count_3d"], reverse=True)
    top = set(ranked[:n_flagged])
    for i, s in enumerate(series):
        s["flagged_raw"] = i in top

    return {
        "benchmark": "Synthetic anomaly-injection benchmark (temporal detector)",
        "is_synthetic": True,
        "seed": seed,
        "series_total": len(series),
        "series_per_rate": {"NONE": null_per_rate, "SPIKE_X3": injected_per_rate, "SUSTAINED_X2": injected_per_rate},
        "anomaly_prevalence": round(2 * injected_per_rate / (null_per_rate + 2 * injected_per_rate), 3),
        "windows_per_series": N_WINDOWS,
        "rate_buckets_per_day": RATE_BUCKETS,
        "injections": {
            "SPIKE_X3": "Most recent day drawn at 3x baseline rate",
            "SUSTAINED_X2": "Last 3 days drawn at 2x baseline rate",
        },
        "noise_models": "Half Poisson, half negative-binomial (size 4, overdispersed)",
        "decision_rule": "Flag if BH q <= 0.05 (24 h or 72 h test, single family) and observed >= 3",
        "overall": tally(series),
        "by_baseline_rate": by_rate,
        "by_scenario": by_scenario,
        "by_noise_model": by_dispersion,
        "raw_volume_comparator": {
            "description": f"Flag the {n_flagged} series with the largest raw 72 h counts (same number as the detector).",
            **tally(series, "flagged_raw"),
        },
        "limitations": [
            "Simulated data; real complaint streams have reporting artefacts, holidays and drift not modelled here.",
            "No day-of-week effect is simulated, so weekday adjustment is not exercised by this benchmark.",
            "Low-rate series (< 1/day) have little power: a x3 spike may still be only 1-2 complaints.",
            "Metrics are per series at a single evaluation time, not per-alert lead time.",
        ],
    }
