"""
Cross-category association candidates.

A zone is a candidate for categories A and B when both show an unusual 72-hour increase
(nominal p < 0.05, at least 3 complaints each). For each candidate we report descriptive
statistics only — Spearman correlation of daily counts and the number of A-B complaint pairs
that are close in space and time. Results are associations for investigation, never evidence
that one issue causes the other.
"""

from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

from backend.app.engine.civic_intelligence import haversine_m

CANDIDATE_P = 0.05
CANDIDATE_MIN_COUNT = 3
COLOCATION_M = 500.0
COLOCATION_HOURS = 48.0
CORRELATION_DAYS = 31

DISCLAIMER = (
    "Association only: co-occurrence does not establish that one issue causes the other. "
    "Both may share a third driver (e.g. weather, a local event or a reporting campaign)."
)

CROSS_CATEGORY_RULES = [
    {
        "pair": ("WASTE_MANAGEMENT", "DRAINAGE_SANITATION"),
        "hypothesis": "Uncollected waste may be entering open drains and obstructing flow.",
        "recommended_investigation": "Joint inspection by solid-waste and stormwater-drain teams of drains near the reported waste points.",
    },
    {
        "pair": ("WATER_SUPPLY", "ROADS_INFRASTRUCTURE"),
        "hypothesis": "A leaking or burst water main may be undermining the road surface.",
        "recommended_investigation": "Water utility leak-detection survey before road repairs are scheduled.",
    },
    {
        "pair": ("STREETLIGHTS_ELECTRICITY", "PUBLIC_ASSETS"),
        "hypothesis": "Streetlight failures alongside public-asset damage could reflect cable theft/vandalism or a feeder fault.",
        "recommended_investigation": "Inspect feeder pillars and lighting circuits along the affected stretch.",
    },
    {
        "pair": ("ILLEGAL_DUMPING", "ROADS_INFRASTRUCTURE"),
        "hypothesis": "Construction debris dumped on roadsides may be obstructing traffic and damaging road edges.",
        "recommended_investigation": "Enforcement check for unauthorised dumping and debris clearance.",
    },
    {
        "pair": ("POWER_SUPPLY", "WATER_SUPPLY"),
        "hypothesis": "Power interruptions may be stopping water pumping stations, reducing supply.",
        "recommended_investigation": "Verify power continuity at pumping stations serving the area.",
    },
]


def _rule_for(a: str, b: str) -> Optional[Dict[str, Any]]:
    for rule in CROSS_CATEGORY_RULES:
        if set(rule["pair"]) == {a, b}:
            return rule
    return None


def colocated_pairs(recs_a: List[Dict[str, Any]], recs_b: List[Dict[str, Any]]) -> Tuple[int, List[int]]:
    hours = timedelta(hours=COLOCATION_HOURS)
    count = 0
    ids = set()
    for a in recs_a:
        if a.get("lat") is None:
            continue
        for b in recs_b:
            if b.get("lat") is None or abs(a["reported_at"] - b["reported_at"]) > hours:
                continue
            if haversine_m(a["lat"], a["lon"], b["lat"], b["lon"]) <= COLOCATION_M:
                count += 1
                ids.update((int(a["id"]), int(b["id"])))
    return count, sorted(ids)


def discover_patterns(
    zone_cells: Dict[str, Dict[str, Dict[str, Any]]],
    recent_records: Dict[Tuple[str, str], List[Dict[str, Any]]],
    zone_names: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    zone_cells[zone][category] needs: p_3d, observed_3d, expected_3d, daily_counts (np.ndarray, index 0 = latest).
    recent_records[(zone, category)] = records from the last 72 h.
    """
    out: List[Dict[str, Any]] = []
    for zone_id, cats in zone_cells.items():
        elevated = sorted(
            c for c, v in cats.items()
            if v.get("p_3d") is not None and v["p_3d"] < CANDIDATE_P and v["observed_3d"] >= CANDIDATE_MIN_COUNT
        )
        for i, a in enumerate(elevated):
            for b in elevated[i + 1:]:
                ca, cb = cats[a], cats[b]
                xa = ca["daily_counts"][:CORRELATION_DAYS]
                xb = cb["daily_counts"][:CORRELATION_DAYS]
                rho = None
                if np.std(xa) > 0 and np.std(xb) > 0:
                    rho = round(float(stats.spearmanr(xa, xb).statistic), 3)
                n_pairs, pair_ids = colocated_pairs(recent_records.get((zone_id, a), []), recent_records.get((zone_id, b), []))
                rule = _rule_for(a, b)
                supporting = sorted({int(r["id"]) for r in recent_records.get((zone_id, a), []) + recent_records.get((zone_id, b), [])})
                out.append({
                    "key": f"pattern:{zone_id}:{a}:{b}",
                    "zone_id": zone_id,
                    "zone_name": zone_names.get(zone_id, zone_id),
                    "category_a": a,
                    "category_b": b,
                    "observed_a": ca["observed_3d"],
                    "expected_a": ca["expected_3d"],
                    "p_value_a": ca["p_3d"],
                    "observed_b": cb["observed_3d"],
                    "expected_b": cb["expected_3d"],
                    "p_value_b": cb["p_3d"],
                    "window_hours": 72,
                    "spearman_rho_daily": rho,
                    "correlation_days": int(min(len(xa), CORRELATION_DAYS)),
                    "colocated_pair_count": n_pairs,
                    "colocation_rule": f"<= {int(COLOCATION_M)} m and <= {int(COLOCATION_HOURS)} h",
                    "colocated_complaint_ids": pair_ids,
                    "supporting_complaint_ids": supporting,
                    "hypothesis_source": "DOMAIN_RULE_TEMPLATE" if rule else "GENERIC",
                    "hypothesis_text": rule["hypothesis"] if rule else (
                        "Both categories rose together in this zone; the link, if any, is unknown."
                    ),
                    "recommended_investigation": rule["recommended_investigation"] if rule else (
                        "Review supporting complaints from both categories for a shared location or cause."
                    ),
                    "disclaimer": DISCLAIMER,
                    "method": (
                        "Candidate when both categories have nominal 72 h p < 0.05 (exact conditional Poisson test) and "
                        ">= 3 complaints; Spearman correlation over daily counts and spatial-temporal co-location "
                        "are descriptive. Not corrected for multiple comparisons; hypotheses only."
                    ),
                })
    out.sort(key=lambda p: (-(p["colocated_pair_count"]), (p["p_value_a"] + p["p_value_b"])))
    return out
