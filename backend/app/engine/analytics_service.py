"""
Orchestrates complaint analytics for a city: loads records, builds window counts, runs the temporal,
spatial, neighbourhood and cross-category detectors, and assembles explainable results and alerts.

Every number in the output is computed from stored complaint records. Text is template-generated
from those numbers only — no model invents counts, timestamps, locations or statistics.
"""

import math
import threading
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.engine import temporal_anomaly_engine as tae
from backend.app.engine.civic_intelligence import CATEGORY_LABELS, CANONICAL_CATEGORIES
from backend.app.engine.cross_category_engine import discover_patterns
from backend.app.engine.duplicate_detector import DuplicateDetector
from backend.app.engine.spatiotemporal_engine import neighbourhood_tests, point_clusters, zone_neighbours
from backend.app.models.schema import (
    AdministrativeZone, CivicComplaint, ComplaintCategoryConfig, DuplicateReview,
)

DUPLICATE_SCAN_DAYS = 7
HAZARD_WINDOW_HOURS = 72
ANALYSIS_LOOKBACK_DAYS = tae.N_WINDOWS + 1

GENERAL_LIMITATIONS = [
    "Complaint counts measure reporting, not incidence: awareness campaigns, app outages or media coverage change volumes.",
    "An anomaly is an early-warning signal for investigation, not confirmation of an emergency.",
    "Zone attribution uses nearest zone centroid when only coordinates are available (no ward polygons).",
]

_cache_lock = threading.Lock()
_cache: Dict[Tuple, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

_COLS = [
    CivicComplaint.id, CivicComplaint.tracking_number, CivicComplaint.zone_id, CivicComplaint.issue_category,
    CivicComplaint.subcategory, CivicComplaint.reported_at, CivicComplaint.lat, CivicComplaint.lon,
    CivicComplaint.severity_score, CivicComplaint.is_severe_hazard, CivicComplaint.linked_incident_id,
    CivicComplaint.raw_text, CivicComplaint.landmark, CivicComplaint.status, CivicComplaint.language_detected,
    CivicComplaint.provenance, CivicComplaint.source,
]
_KEYS = [c.key for c in _COLS]


def load_records(db: Session, city_id: str, since: Optional[datetime] = None, until: Optional[datetime] = None) -> List[Dict[str, Any]]:
    q = select(*_COLS).where(CivicComplaint.city_id == city_id)
    if since is not None:
        q = q.where(CivicComplaint.reported_at > since)
    if until is not None:
        q = q.where(CivicComplaint.reported_at <= until)
    rows = db.execute(q).all()
    out = []
    for row in rows:
        d = dict(zip(_KEYS, row))
        d["issue_category"] = d["issue_category"] or "OTHER"
        out.append(d)
    return out


def load_zones(db: Session, city_id: str) -> List[Dict[str, Any]]:
    zones = db.query(AdministrativeZone).filter(AdministrativeZone.city_id == city_id).order_by(AdministrativeZone.zone_number).all()
    return [
        {"id": z.id, "name": z.name, "zone_number": z.zone_number, "center_lat": z.center_lat,
         "center_lon": z.center_lon, "population": z.population}
        for z in zones
    ]


def category_departments(db: Session) -> Dict[str, str]:
    return {c.code: c.target_department for c in db.query(ComplaintCategoryConfig).all()}


def reviewed_pairs(db: Session, city_id: str) -> List[Tuple[int, int]]:
    rows = db.query(DuplicateReview.complaint_id_1, DuplicateReview.complaint_id_2).filter(DuplicateReview.city_id == city_id).all()
    return [(a, b) for a, b in rows]


def data_bounds(db: Session, city_id: str) -> Tuple[int, Optional[int], Optional[datetime], Optional[datetime]]:
    n, max_id, first, last = db.execute(
        select(func.count(CivicComplaint.id), func.max(CivicComplaint.id),
               func.min(CivicComplaint.reported_at), func.max(CivicComplaint.reported_at))
        .where(CivicComplaint.city_id == city_id)
    ).one()
    return int(n or 0), max_id, first, last


def _state_key(db: Session, city_id: str, as_of: Optional[datetime]) -> Tuple:
    n, max_id, first, last = data_bounds(db, city_id)
    n_rev = db.query(func.count(DuplicateReview.id)).filter(DuplicateReview.city_id == city_id).scalar() or 0
    n_linked = db.query(func.count(CivicComplaint.id)).filter(
        CivicComplaint.city_id == city_id, CivicComplaint.linked_incident_id.isnot(None)).scalar() or 0
    n_zone = db.query(func.count(AdministrativeZone.id)).filter(AdministrativeZone.city_id == city_id).scalar() or 0
    return (city_id, as_of.isoformat() if as_of else None, n, max_id, str(first), str(last), n_rev, n_linked, n_zone)


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dedupe_linked(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Confirmed-merged complaints (same linked incident) count once, at the earliest report."""
    first: Dict[int, Dict[str, Any]] = {}
    out, dropped = [], 0
    for r in sorted(records, key=lambda r: r["reported_at"]):
        inc = r.get("linked_incident_id")
        if inc is None:
            out.append(r)
        elif inc not in first:
            first[inc] = r
            out.append(r)
        else:
            dropped += 1
    return out, dropped


def _fmt_ratio(obs: float, exp: float) -> str:
    return f"{obs / exp:.1f}x" if exp > 0 else "n/a"


def _per_100k(count: float, population: Optional[int]) -> Optional[float]:
    if not population:
        return None
    return round(count / population * 100_000, 2)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_city(db: Session, city_id: str, as_of: Optional[datetime] = None) -> Dict[str, Any]:
    key = _state_key(db, city_id, as_of)
    with _cache_lock:
        if key in _cache:
            return _cache[key]
    result = _analyze(db, city_id, as_of)
    with _cache_lock:
        if len(_cache) > 32:
            _cache.clear()
        _cache[key] = result
    return result


def _empty_result(city_id: str, as_of: Optional[datetime], zones: List[Dict[str, Any]], reason: str) -> Dict[str, Any]:
    return {
        "city_id": city_id,
        "meta": {
            "as_of": _iso(as_of), "data_start": None, "data_end": None, "covered_days": 0,
            "total_records": 0, "analyzed_records": 0, "records_without_zone": 0, "records_without_coordinates": 0,
            "merged_duplicates_excluded": 0, "tests_in_family": 0, "fdr_alpha": tae.FDR_ALPHA,
            "status": reason, "zones": len(zones), "categories": [],
            "weekday_adjusted_categories": [], "methods": _methods(),
            "limitations": GENERAL_LIMITATIONS,
        },
        "cells": [], "anomalies": [], "clusters": [], "neighbourhoods": [], "patterns": [],
        "duplicates": [], "hazards": [], "zones": zones,
    }


def _methods() -> Dict[str, str]:
    return {
        "temporal": f"{tae.METHOD_POISSON}; switches to: {tae.METHOD_NB} when baseline variance > {tae.OVERDISPERSION_RATIO}x mean. "
                    "24 h and 72 h windows; one Benjamini-Hochberg family across all zone-category cells.",
        "decision_rule": f"ANOMALY: BH q <= {tae.FDR_ALPHA} and observed >= {tae.MIN_OBSERVED}. "
                         f"WATCH: raw p < {tae.WATCH_P} and observed >= {tae.MIN_OBSERVED} but not significant after correction.",
        "robust_z": "Median/MAD z-score of the latest day vs baseline days — descriptive only, not used for decisions.",
        "seasonality": f"Day-of-week multipliers per category (city-wide, shrunk toward 1) when >= {tae.MIN_WEEKDAY_WINDOWS} baseline days exist.",
        "sparse_data": f"Cells with < {tae.MIN_BASELINE_WINDOWS} baseline days are INSUFFICIENT_HISTORY and not tested. "
                       "Exact conditional tests stay valid for zero or low baselines.",
        "lifecycle": f"NEW_OR_RARE: baseline < {tae.RARE_BASELINE_RATE}/day. PERSISTENT: >= 3 of previous 6 days individually elevated "
                     f"(nominal p < {tae.HISTORY_ELEVATED_P}). EMERGING: otherwise. EXPANDING: a neighbouring zone (<= 7 km) is also elevated.",
    }


def _analyze(db: Session, city_id: str, as_of_param: Optional[datetime]) -> Dict[str, Any]:
    zones = load_zones(db, city_id)
    n_total, _, first_ts, last_ts = data_bounds(db, city_id)
    if n_total == 0 or last_ts is None:
        return _empty_result(city_id, as_of_param, zones, "NO_DATA")

    # Default reference time is the latest record so replayed or stale datasets analyse their own "now".
    as_of = as_of_param or last_ts
    since = as_of - timedelta(days=ANALYSIS_LOOKBACK_DAYS)
    raw_records = load_records(db, city_id, since=since, until=as_of)
    records, merged_dropped = _dedupe_linked(raw_records)
    covered = tae.covered_windows(as_of, first_ts)
    if not records:
        res = _empty_result(city_id, as_of, zones, "NO_DATA_IN_WINDOW")
        res["meta"]["total_records"] = n_total
        return res

    zone_ids = [z["id"] for z in zones]
    zone_by_id = {z["id"]: z for z in zones}
    zone_names = {z["id"]: z["name"] for z in zones}
    zi = {z: i for i, z in enumerate(zone_ids)}
    present = {r["issue_category"] for r in records}
    categories = [c for c in CANONICAL_CATEGORIES if c in present] + sorted(present - set(CANONICAL_CATEGORIES))
    ci = {c: i for i, c in enumerate(categories)}

    nW = tae.N_WINDOWS
    counts = np.zeros((len(zone_ids), len(categories), nW), dtype=int)
    cell_records: Dict[Tuple[str, str], List[Tuple[int, Dict[str, Any]]]] = defaultdict(list)
    no_zone = no_coords = 0
    for r in records:
        w = tae.window_index(r["reported_at"], as_of)
        if r.get("lat") is None:
            no_coords += 1
        if r.get("zone_id") not in zi:
            no_zone += 1
            continue
        if 0 <= w < nW:
            counts[zi[r["zone_id"]], ci[r["issue_category"]], w] += 1
            if w < 3:
                cell_records[(r["zone_id"], r["issue_category"])].append((w, r))

    weekdays = tae.window_weekdays(as_of, nW)
    factors: Dict[str, np.ndarray] = {}
    weekday_adjusted: List[str] = []
    for c in categories:
        f7 = tae.weekday_factors(counts[:, ci[c], :].sum(axis=0), weekdays, covered)
        if f7 is not None:
            weekday_adjusted.append(c)
            factors[c] = f7[weekdays]
        else:
            factors[c] = np.ones(nW)

    # --- per-cell tests ---
    evaluated: Dict[Tuple[str, str], tae.CellResult] = {}
    family: List[Tuple[Tuple[str, str], int, float]] = []
    for z in zone_ids:
        for c in categories:
            cell = tae.evaluate_cell(counts[zi[z], ci[c]], covered, factors[c])
            evaluated[(z, c)] = cell
            if cell.status == "TESTED":
                family.append(((z, c), 1, cell.test_1d.p_value))
                family.append(((z, c), 3, cell.test_3d.p_value))
    qvals = tae.benjamini_hochberg([p for _, _, p in family])
    q_by: Dict[Tuple[Tuple[str, str], int], float] = {(k, w): float(q) for (k, w, _), q in zip(family, qvals)}

    base_idx = [i for i in range(1 + tae.GUARD_WINDOWS, 1 + tae.GUARD_WINDOWS + tae.BASELINE_WINDOWS) if i < min(nW, covered)]
    zone_totals = counts.sum(axis=1)  # zones x windows
    city_cat = counts.sum(axis=0)     # categories x windows

    cells_out: List[Dict[str, Any]] = []
    cell_ctx: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for (z, c), cell in evaluated.items():
        entry: Dict[str, Any] = {
            "key": f"temporal:{z}:{c}", "zone_id": z, "zone_name": zone_names[z], "category": c,
            "category_label": CATEGORY_LABELS.get(c, c), "status": cell.status,
            "baseline_days": cell.baseline_windows, "observed_24h": int(counts[zi[z], ci[c], 0]),
            "observed_72h": int(counts[zi[z], ci[c], :3].sum()),
        }
        if cell.status != "TESTED":
            entry.update({"level": "INSUFFICIENT_HISTORY"})
            cells_out.append(entry)
            continue
        q1, q3 = q_by[((z, c), 1)], q_by[((z, c), 3)]
        primary, q = (cell.test_3d, q3) if q3 <= q1 else (cell.test_1d, q1)
        level = tae.classify_level(q, primary.p_value, primary.observed)
        entry.update({
            "level": level,
            "expected_24h": cell.test_1d.expected, "expected_72h": cell.test_3d.expected,
            "p_value_24h": cell.test_1d.p_value, "q_value_24h": q1,
            "p_value_72h": cell.test_3d.p_value, "q_value_72h": q3,
            "ratio_72h": round(cell.test_3d.observed / cell.test_3d.expected, 2) if cell.test_3d.expected else None,
            "baseline_rate_per_day": cell.baseline_rate_per_day,
        })
        cells_out.append(entry)
        cell_ctx[(z, c)] = {
            "cell": cell, "primary": primary, "q": q, "level": level,
            "window_hours": primary.windows * 24,
        }

    # --- neighbourhood context ---
    neighbours = zone_neighbours(zones)
    f_base_by_cat = {c: float(factors[c][base_idx].sum()) if base_idx else 0.0 for c in categories}
    pooled_cells = {}
    for (z, c), cell in evaluated.items():
        if cell.status != "TESTED":
            continue
        pooled_cells[(z, c)] = {
            "observed_3d": cell.test_3d.observed, "baseline_total": cell.baseline_total,
            "f_obs_3d": float(factors[c][:3].sum()), "f_base": f_base_by_cat[c], "expected_3d": cell.test_3d.expected,
        }
    neighbourhood_results = neighbourhood_tests(pooled_cells, neighbours, zone_names)

    def neighbour_elevated(z: str, c: str) -> List[str]:
        out = []
        for n in neighbours.get(z, []):
            ctx = cell_ctx.get((n, c))
            if not ctx:
                continue
            t3 = ctx["cell"].test_3d
            if ctx["level"] in ("ANOMALY", "WATCH") or (t3.p_value < 0.05 and t3.observed >= tae.MIN_OBSERVED):
                out.append(n)
        return out

    # --- anomalies with full explanation ---
    anomalies: List[Dict[str, Any]] = []
    for (z, c), ctx in cell_ctx.items():
        if ctx["level"] not in ("ANOMALY", "WATCH"):
            continue
        cell: tae.CellResult = ctx["cell"]
        primary: tae.WindowTest = ctx["primary"]
        series = counts[zi[z], ci[c]]
        k = primary.windows
        w_start, _ = tae.window_bounds(as_of, k - 1)
        zone = zone_by_id[z]

        zone_obs = int(zone_totals[zi[z], :k].sum())
        zone_base = int(zone_totals[zi[z], base_idx].sum())
        zone_exp = (zone_base + 0.5) * k / len(base_idx)
        cat_base = cell.baseline_total
        share_p = tae.share_test(primary.observed, zone_obs, cat_base, zone_base)
        city_obs = int(city_cat[ci[c], :k].sum())
        city_exp = (int(city_cat[ci[c], base_idx].sum()) + 0.5) * float(factors[c][:k].sum()) / f_base_by_cat[c]
        zone_ratio = zone_obs / zone_exp if zone_exp else None
        city_ratio = city_obs / city_exp if city_exp else None

        if share_p is not None and share_p < 0.05:
            volume_note = "Category-specific: this category's share of all complaints in the zone also rose."
        elif zone_ratio and zone_ratio >= 1.5:
            volume_note = "Zone-wide rise in all reporting; may reflect reporting behaviour rather than a category-specific problem."
        else:
            volume_note = "Share of zone complaints not clearly elevated; interpret with caution."

        nbrs = neighbour_elevated(z, c)
        life = tae.lifecycle(cell)
        pattern = tae.temporal_pattern(series, cell)
        supp = sorted((r for w, r in cell_records.get((z, c), []) if w < k), key=lambda r: r["reported_at"], reverse=True)
        sev = [r["severity_score"] or 3 for r in supp]
        mean_sev = round(float(np.mean(sev)), 2) if sev else None
        f_c = factors[c]
        lam = (cell.baseline_total + 0.5) / float(f_c[base_idx].sum())
        n_hist = min(31, nW)
        daily = [
            {"date": _iso(tae.window_bounds(as_of, i)[1]), "observed": int(series[i]), "expected": round(lam * float(f_c[i]), 3)}
            for i in reversed(range(n_hist)) if i < covered or i == 0
        ]

        limitations = []
        if primary.expected < 1.0:
            limitations.append(f"Very low expected count ({primary.expected:.2f}); a handful of complaints drives this signal.")
        if cell.overdispersed:
            limitations.append("Baseline is overdispersed; negative-binomial plug-in dispersion is approximate.")
        if c not in weekday_adjusted:
            limitations.append("No day-of-week adjustment (insufficient history or no weekly signal estimable).")
        if cell.baseline_windows < tae.BASELINE_WINDOWS:
            limitations.append(f"Baseline covers only {cell.baseline_windows} of {tae.BASELINE_WINDOWS} days.")
        if not zone.get("population"):
            limitations.append("Zone population unknown; rates per 100k not available.")
        if life == "NEW_OR_RARE":
            limitations.append("Issue is rare here historically; confirm reports are genuine and correctly categorised.")
        if ctx["level"] == "WATCH":
            limitations.append("Not significant after multiple-comparison correction (WATCH only).")

        label = CATEGORY_LABELS.get(c, c)
        window_txt = "24 hours" if k == 1 else "72 hours"
        explanation = (
            f"{primary.observed} {label.lower()} complaints in {zone['name']} in the last {window_txt} "
            f"vs {primary.expected:.1f} expected from the previous {cell.baseline_windows} days "
            f"({_fmt_ratio(primary.observed, primary.expected)}; 95% upper prediction bound {primary.upper_prediction95}). "
            f"Raw p = {primary.p_value:.2g}, BH-adjusted q = {ctx['q']:.2g} across {len(family)} tests."
        )

        anomalies.append({
            "key": f"temporal:{z}:{c}",
            "level": ctx["level"],
            "zone_id": z, "zone_name": zone["name"], "category": c, "category_label": label,
            "window_hours": k * 24, "window_start": _iso(w_start), "window_end": _iso(as_of),
            "observed": primary.observed, "expected": primary.expected,
            "expected_ci95": list(primary.expected_ci95), "upper_prediction95": primary.upper_prediction95,
            "ratio": round(primary.observed / primary.expected, 2) if primary.expected else None,
            "excess": round(primary.observed - primary.expected, 2),
            "p_value": primary.p_value, "q_value": ctx["q"], "tests_in_family": len(family),
            "method": primary.method,
            "observed_24h": cell.test_1d.observed, "expected_24h": cell.test_1d.expected,
            "p_value_24h": cell.test_1d.p_value, "q_value_24h": q_by[((z, c), 1)],
            "observed_72h": cell.test_3d.observed, "expected_72h": cell.test_3d.expected,
            "p_value_72h": cell.test_3d.p_value, "q_value_72h": q_by[((z, c), 3)],
            "baseline_days": cell.baseline_windows, "baseline_rate_per_day": cell.baseline_rate_per_day,
            "baseline_median": cell.baseline_median, "baseline_mad": cell.baseline_mad,
            "robust_z": cell.robust_z, "dispersion_ratio": cell.dispersion_ratio, "overdispersed": cell.overdispersed,
            "weekday_adjusted": c in weekday_adjusted,
            "lifecycle": life, "temporal_pattern": pattern,
            "spatial_extent": "EXPANDING" if nbrs else "LOCALIZED",
            "elevated_neighbour_zones": [{"zone_id": n, "zone_name": zone_names[n]} for n in nbrs],
            "previous_days_elevated": int(sum(cell.history_elevated)),
            "reporting_context": {
                "zone_all_categories_observed": zone_obs, "zone_all_categories_expected": round(zone_exp, 2),
                "zone_all_categories_ratio": round(zone_ratio, 2) if zone_ratio else None,
                "city_category_observed": city_obs, "city_category_expected": round(city_exp, 2),
                "city_category_ratio": round(city_ratio, 2) if city_ratio else None,
                "category_share_p_value": share_p,
                "interpretation": volume_note,
            },
            "population": zone.get("population"),
            "observed_per_100k": _per_100k(primary.observed, zone.get("population")),
            "expected_per_100k": _per_100k(primary.expected, zone.get("population")),
            "mean_operational_severity": mean_sev,
            "supporting_complaint_ids": [int(r["id"]) for r in supp][:100],
            "supporting_count": len(supp),
            "daily_series": daily,
            "explanation": explanation,
            "limitations": limitations,
        })
    anomalies.sort(key=lambda a: (0 if a["level"] == "ANOMALY" else 1, a["q_value"], -a["observed"]))

    # --- spatial clusters ---
    clusters = point_clusters(records, as_of, covered)
    for cl in clusters:
        cl["zone_name"] = zone_names.get(cl["zone_id"]) if cl["zone_id"] else None
        cl["category_label"] = CATEGORY_LABELS.get(cl["category"], cl["category"])
        cl["key"] = f"cluster:{cl['category']}:{cl['center_lat']:.4f}:{cl['center_lon']:.4f}"
        ctx = cell_ctx.get((cl["zone_id"], cl["category"])) if cl["zone_id"] else None
        cl["first_reported_at"] = _iso(cl["first_reported_at"])
        cl["last_reported_at"] = _iso(cl["last_reported_at"])
        cl["zone_level"] = ctx["level"] if ctx else None
        if cl["baseline_count"] == 0:
            cl["status"] = "NEW"
        elif ctx and sum(ctx["cell"].history_elevated) >= 3:
            cl["status"] = "PERSISTENT"
        else:
            cl["status"] = "EMERGING"
        if cl["zone_id"] and neighbour_elevated(cl["zone_id"], cl["category"]):
            cl["status"] = "EXPANDING"

    for nb in neighbourhood_results:
        nb["key"] = f"neighbourhood:{nb['anchor_zone_id']}:{nb['category']}"
        nb["category_label"] = CATEGORY_LABELS.get(nb["category"], nb["category"])
        nb["anchor_zone_name"] = zone_names.get(nb["anchor_zone_id"])
        nb["zones_above_expected_names"] = [zone_names.get(z, z) for z in nb["zones_above_expected"]]
        nb["individually_significant_zones"] = [
            z for z in nb["member_zone_ids"] if cell_ctx.get((z, nb["category"]), {}).get("level") == "ANOMALY"
        ]

    # --- cross-category ---
    zone_cells: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for (z, c), ctx in cell_ctx.items():
        cell = ctx["cell"]
        zone_cells[z][c] = {
            "p_3d": cell.test_3d.p_value, "observed_3d": cell.test_3d.observed,
            "expected_3d": cell.test_3d.expected, "daily_counts": counts[zi[z], ci[c], :min(31, covered)],
        }
    recent_by_cell = {k: [r for _, r in v] for k, v in cell_records.items()}
    patterns = discover_patterns(zone_cells, recent_by_cell, zone_names)
    for p in patterns:
        p["category_a_label"] = CATEGORY_LABELS.get(p["category_a"], p["category_a"])
        p["category_b_label"] = CATEGORY_LABELS.get(p["category_b"], p["category_b"])
        p["window_end"] = _iso(as_of)

    # --- duplicates & hazards ---
    dup_since = as_of - timedelta(days=DUPLICATE_SCAN_DAYS)
    dup_pool = [r for r in raw_records if r["reported_at"] > dup_since]
    duplicates = DuplicateDetector.find_duplicate_candidates(dup_pool, exclude_pairs=reviewed_pairs(db, city_id), limit=200)
    hz_since = as_of - timedelta(hours=HAZARD_WINDOW_HOURS)
    hazards = sorted(
        (r for r in raw_records if r.get("is_severe_hazard") and r["reported_at"] > hz_since
         and (r.get("status") or "OPEN") not in ("RESOLVED", "CLOSED", "REJECTED")),
        key=lambda r: r["reported_at"], reverse=True,
    )

    return {
        "city_id": city_id,
        "meta": {
            "as_of": _iso(as_of), "data_start": _iso(first_ts), "data_end": _iso(last_ts),
            "covered_days": covered, "total_records": n_total, "records_in_lookback": len(raw_records),
            "analyzed_records": len(records), "records_without_zone": no_zone, "records_without_coordinates": no_coords,
            "merged_duplicates_excluded": merged_dropped, "tests_in_family": len(family), "fdr_alpha": tae.FDR_ALPHA,
            "status": "OK", "zones": len(zones), "categories": categories,
            "weekday_adjusted_categories": weekday_adjusted,
            "insufficient_history_cells": sum(1 for e in cells_out if e["level"] == "INSUFFICIENT_HISTORY"),
            "methods": _methods(), "limitations": GENERAL_LIMITATIONS,
        },
        "cells": cells_out,
        "anomalies": anomalies,
        "clusters": clusters,
        "neighbourhoods": neighbourhood_results,
        "patterns": patterns,
        "duplicates": duplicates,
        "hazards": hazards,
        "zones": zones,
    }


# ---------------------------------------------------------------------------
# Alerts (computed, explainable). Anomaly evidence is kept separate from operational severity.
# ---------------------------------------------------------------------------

def _signal_strength(q: float) -> float:
    return min(1.0, -math.log10(max(q, 1e-12)) / 6.0)


def priority_breakdown(q: float, mean_severity: Optional[float], observed: int, extent: str, lifecycle: str) -> Dict[str, Any]:
    stat = _signal_strength(q)
    sev = ((mean_severity or 3) - 1) / 4.0
    breadth = min(1.0, observed / 20.0)
    ext = 1.0 if extent == "EXPANDING" or lifecycle == "PERSISTENT" else 0.5
    score = round(100 * (0.4 * stat + 0.3 * sev + 0.2 * breadth + 0.1 * ext), 1)
    return {
        "score": score,
        "formula": "100 x (0.4 x statistical strength + 0.3 x mean operational severity + 0.2 x volume + 0.1 x spread/persistence)",
        "components": {
            "statistical_strength": round(stat, 3), "operational_severity": round(sev, 3),
            "volume": round(breadth, 3), "spread_or_persistence": ext,
        },
    }


def build_alerts(analysis: Dict[str, Any], departments: Dict[str, str]) -> List[Dict[str, Any]]:
    as_of = analysis["meta"]["as_of"]
    alerts: List[Dict[str, Any]] = []

    for a in analysis["anomalies"]:
        pr = priority_breakdown(a["q_value"], a["mean_operational_severity"], a["observed"], a["spatial_extent"], a["lifecycle"])
        dept = departments.get(a["category"], "Ward Office")
        alerts.append({
            "key": a["key"], "alert_class": "STATISTICAL_ANOMALY", "signal_level": a["level"],
            "title": f"{'Unusual' if a['level'] == 'ANOMALY' else 'Watch'}: {a['category_label']} complaints in {a['zone_name']} ({a['ratio']}x expected)",
            "zone_id": a["zone_id"], "zone_name": a["zone_name"], "category": a["category"], "category_label": a["category_label"],
            "observed": a["observed"], "expected": a["expected"], "window_hours": a["window_hours"],
            "window_start": a["window_start"], "window_end": a["window_end"],
            "method": a["method"], "p_value": a["p_value"], "q_value": a["q_value"],
            "lifecycle": a["lifecycle"], "spatial_extent": a["spatial_extent"], "temporal_pattern": a["temporal_pattern"],
            "operational_severity": a["mean_operational_severity"],
            "priority": pr,
            "evidence_text": a["explanation"] + " " + a["reporting_context"]["interpretation"],
            "supporting_complaint_ids": a["supporting_complaint_ids"],
            "limitations": a["limitations"] + GENERAL_LIMITATIONS[:2],
            "recommended_action": f"{dept}: verify on the ground and review the {a['supporting_count']} supporting complaints before dispatching resources.",
            "target_department": dept,
            "queue": "EMERGING_PATTERN_QUEUE",
            "created_at": as_of,
        })

    for cl in analysis["clusters"]:
        if not cl["significant"]:
            continue
        dept = departments.get(cl["category"], "Ward Office")
        place = cl["landmark"] or cl["zone_name"] or f"{cl['center_lat']:.4f}, {cl['center_lon']:.4f}"
        pr = priority_breakdown(cl["q_value"], None, cl["observed"], "EXPANDING" if cl["status"] == "EXPANDING" else "LOCALIZED",
                                "PERSISTENT" if cl["status"] == "PERSISTENT" else "EMERGING")
        alerts.append({
            "key": cl["key"], "alert_class": "SPATIAL_CLUSTER", "signal_level": "ANOMALY",
            "title": f"{cl['status'].title()} {cl['category_label'].lower()} cluster near {place}",
            "zone_id": cl["zone_id"], "zone_name": cl["zone_name"], "category": cl["category"], "category_label": cl["category_label"],
            "observed": cl["observed"], "expected": cl["expected"], "window_hours": cl["window_hours"],
            "window_start": None, "window_end": as_of, "method": cl["method"], "p_value": cl["p_value"], "q_value": cl["q_value"],
            "lifecycle": cl["status"], "spatial_extent": "EXPANDING" if cl["status"] == "EXPANDING" else "LOCALIZED",
            "temporal_pattern": None, "operational_severity": None, "priority": pr,
            "evidence_text": (
                f"{cl['observed']} complaints within {int(cl['radius_meters'])} m in {cl['window_hours']} h vs "
                f"{cl['expected']:.2f} expected from {cl['baseline_count']} complaints at the same spot in the previous "
                f"{cl['baseline_days']} days. q = {cl['q_value']:.2g}."
            ),
            "supporting_complaint_ids": cl["supporting_complaint_ids"],
            "limitations": ["Cluster boundaries come from a greedy fixed-radius heuristic.", *GENERAL_LIMITATIONS[:2]],
            "recommended_action": f"{dept}: site inspection at {place}.",
            "target_department": dept, "queue": "EMERGING_PATTERN_QUEUE", "created_at": as_of,
        })

    for nb in analysis["neighbourhoods"]:
        dept = departments.get(nb["category"], "Ward Office")
        pr = priority_breakdown(nb["q_value"], None, nb["observed"], "EXPANDING", "EMERGING")
        alerts.append({
            "key": nb["key"], "alert_class": "NEIGHBOURHOOD_INCREASE", "signal_level": "ANOMALY",
            "title": f"{nb['category_label']} rising across neighbouring zones: {', '.join(nb['zones_above_expected_names'])}",
            "zone_id": nb["anchor_zone_id"], "zone_name": nb["anchor_zone_name"], "category": nb["category"],
            "category_label": nb["category_label"], "observed": nb["observed"], "expected": nb["expected"],
            "window_hours": nb["window_hours"], "window_start": None, "window_end": as_of, "method": nb["method"],
            "p_value": nb["p_value"], "q_value": nb["q_value"], "lifecycle": "EMERGING", "spatial_extent": "EXPANDING",
            "temporal_pattern": None, "operational_severity": None, "priority": pr,
            "evidence_text": (
                f"Pooled over {len(nb['member_zone_ids'])} neighbouring zones: {nb['observed']} complaints in 72 h vs "
                f"{nb['expected']:.1f} expected ({nb['ratio']}x). {len(nb['zones_above_expected'])} zones individually above "
                f"expectation; {len(nb['individually_significant_zones'])} individually significant."
            ),
            "supporting_complaint_ids": [],
            "limitations": ["Neighbourhoods use centroid distance, not shared boundaries.", *GENERAL_LIMITATIONS[:2]],
            "recommended_action": f"{dept}: check for a shared upstream cause across these zones.",
            "target_department": dept, "queue": "EMERGING_PATTERN_QUEUE", "created_at": as_of,
        })

    for p in analysis["patterns"]:
        alerts.append({
            "key": p["key"], "alert_class": "CROSS_CATEGORY_PATTERN", "signal_level": "HYPOTHESIS",
            "title": f"{p['category_a_label']} and {p['category_b_label']} rising together in {p['zone_name']}",
            "zone_id": p["zone_id"], "zone_name": p["zone_name"], "category": f"{p['category_a']}+{p['category_b']}",
            "category_label": f"{p['category_a_label']} + {p['category_b_label']}",
            "observed": p["observed_a"] + p["observed_b"], "expected": round(p["expected_a"] + p["expected_b"], 2),
            "window_hours": 72, "window_start": None, "window_end": as_of, "method": p["method"],
            "p_value": None, "q_value": None, "lifecycle": None, "spatial_extent": None, "temporal_pattern": None,
            "operational_severity": None,
            "priority": {"score": None, "formula": "Hypotheses are not prioritised automatically.", "components": {}},
            "evidence_text": (
                f"{p['category_a_label']}: {p['observed_a']} vs {p['expected_a']:.1f} expected; "
                f"{p['category_b_label']}: {p['observed_b']} vs {p['expected_b']:.1f} expected (72 h). "
                f"{p['colocated_pair_count']} co-located complaint pairs ({p['colocation_rule']})."
                + (f" Daily Spearman rho = {p['spearman_rho_daily']} over {p['correlation_days']} days." if p["spearman_rho_daily"] is not None else "")
                + f" Hypothesis: {p['hypothesis_text']}"
            ),
            "supporting_complaint_ids": p["supporting_complaint_ids"],
            "limitations": [p["disclaimer"]],
            "recommended_action": p["recommended_investigation"],
            "target_department": "Ward Office (multi-department)", "queue": "EMERGING_PATTERN_QUEUE", "created_at": as_of,
        })

    for h in analysis["hazards"]:
        dept = departments.get(h["issue_category"], "Ward Office")
        label = CATEGORY_LABELS.get(h["issue_category"], h["issue_category"])
        alerts.append({
            "key": f"hazard:{h['id']}", "alert_class": "HIGH_SEVERITY_HAZARD", "signal_level": "OPERATIONAL",
            "title": f"Possible safety hazard reported: {label} — {h.get('landmark') or 'location in complaint'}",
            "zone_id": h.get("zone_id"), "zone_name": None, "category": h["issue_category"], "category_label": label,
            "observed": 1, "expected": None, "window_hours": HAZARD_WINDOW_HOURS, "window_start": None,
            "window_end": as_of, "method": "Rules-based hazard keyword match on complaint text (not a statistical test)",
            "p_value": None, "q_value": None, "lifecycle": None, "spatial_extent": None, "temporal_pattern": None,
            "operational_severity": h.get("severity_score"),
            "priority": {
                "score": round(100 * ((h.get("severity_score") or 3) - 1) / 4.0, 1),
                "formula": "100 x (operational severity - 1) / 4; independent of anomaly statistics",
                "components": {"operational_severity": h.get("severity_score")},
            },
            "evidence_text": f"Complaint {h['tracking_number']} at {_iso(h['reported_at'])}: \"{(h.get('raw_text') or '')[:180]}\"",
            "supporting_complaint_ids": [int(h["id"])],
            "limitations": ["Single citizen report matched by keywords; not verified.", "Keyword rules can miss or misread hazards."],
            "recommended_action": f"{dept}: immediate verification call or field check.",
            "target_department": dept, "queue": "HIGH_SEVERITY_HAZARD_QUEUE", "created_at": _iso(h["reported_at"]),
        })

    for a in alerts:
        if a.get("zone_id") and not a.get("zone_name"):
            a["zone_name"] = next((z["name"] for z in analysis["zones"] if z["id"] == a["zone_id"]), None)
    return alerts


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------

def daily_trends(
    db: Session, city_id: str, days: int = 56, zone_id: Optional[str] = None, category: Optional[str] = None,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    _, _, first, last = data_bounds(db, city_id)
    if last is None:
        return {"as_of": None, "days": [], "series": {}, "categories": []}
    end = as_of or last
    days = max(7, min(days, 180))
    recs = load_records(db, city_id, since=end - timedelta(days=days), until=end)
    recs, _ = _dedupe_linked(recs)
    if zone_id:
        recs = [r for r in recs if r.get("zone_id") == zone_id]
    if category:
        recs = [r for r in recs if r["issue_category"] == category]
    series: Dict[str, List[int]] = defaultdict(lambda: [0] * days)
    for r in recs:
        w = tae.window_index(r["reported_at"], end)
        if 0 <= w < days:
            series[r["issue_category"]][days - 1 - w] += 1
    labels = [_iso(tae.window_bounds(end, days - 1 - i)[1]) for i in range(days)]
    covered = tae.covered_windows(end, first)
    first_covered_index = max(0, days - covered)
    cats = [c for c in CANONICAL_CATEGORIES if c in series] + sorted(set(series) - set(CANONICAL_CATEGORIES))
    total = [sum(series[c][i] for c in cats) for i in range(days)]
    return {
        "as_of": _iso(end), "window_hours": 24, "days": labels, "categories": cats,
        "series": {c: series[c] for c in cats}, "total": total,
        "first_covered_index": first_covered_index,
        "category_labels": {c: CATEGORY_LABELS.get(c, c) for c in cats},
    }


def category_summary(analysis: Dict[str, Any], departments: Dict[str, str]) -> List[Dict[str, Any]]:
    by_cat: Dict[str, Dict[str, Any]] = {}
    pops = {z["id"]: z.get("population") for z in analysis["zones"]}
    for cell in analysis["cells"]:
        c = cell["category"]
        d = by_cat.setdefault(c, {
            "category": c, "category_label": CATEGORY_LABELS.get(c, c), "target_department": departments.get(c),
            "observed_72h": 0, "expected_72h": 0.0, "observed_24h": 0, "anomaly_zones": [], "watch_zones": [],
            "insufficient_history_zones": 0, "zone_rates": [],
        })
        d["observed_72h"] += cell["observed_72h"]
        d["observed_24h"] += cell["observed_24h"]
        d["expected_72h"] += cell.get("expected_72h") or 0.0
        if cell["level"] == "ANOMALY":
            d["anomaly_zones"].append(cell["zone_name"])
        elif cell["level"] == "WATCH":
            d["watch_zones"].append(cell["zone_name"])
        elif cell["level"] == "INSUFFICIENT_HISTORY":
            d["insufficient_history_zones"] += 1
        d["zone_rates"].append({
            "zone_id": cell["zone_id"], "zone_name": cell["zone_name"], "observed_72h": cell["observed_72h"],
            "expected_72h": cell.get("expected_72h"), "ratio_72h": cell.get("ratio_72h"),
            "per_100k_72h": _per_100k(cell["observed_72h"], pops.get(cell["zone_id"])), "level": cell["level"],
        })
    out = []
    for d in by_cat.values():
        d["expected_72h"] = round(d["expected_72h"], 2)
        d["ratio_72h"] = round(d["observed_72h"] / d["expected_72h"], 2) if d["expected_72h"] else None
        d["zone_rates"].sort(key=lambda z: (z["ratio_72h"] or 0), reverse=True)
        out.append(d)
    out.sort(key=lambda d: (len(d["anomaly_zones"]), d["ratio_72h"] or 0), reverse=True)
    return out


def data_quality(db: Session, city_id: str) -> Dict[str, Any]:
    n, _, first, last = data_bounds(db, city_id)
    base = db.query(CivicComplaint).filter(CivicComplaint.city_id == city_id)
    missing_coords = base.filter((CivicComplaint.lat.is_(None)) | (CivicComplaint.lon.is_(None))).count()
    missing_zone = base.filter(CivicComplaint.zone_id.is_(None)).count()
    other = base.filter(CivicComplaint.issue_category == "OTHER").count()
    linked = base.filter(CivicComplaint.linked_incident_id.isnot(None)).count()
    future = base.filter(CivicComplaint.reported_at > datetime.utcnow() + timedelta(hours=1)).count()
    by_prov = dict(db.query(CivicComplaint.provenance, func.count(CivicComplaint.id))
                   .filter(CivicComplaint.city_id == city_id).group_by(CivicComplaint.provenance).all())
    by_source = dict(db.query(CivicComplaint.source, func.count(CivicComplaint.id))
                     .filter(CivicComplaint.city_id == city_id).group_by(CivicComplaint.source).all())
    by_cat = dict(db.query(CivicComplaint.issue_category, func.count(CivicComplaint.id))
                  .filter(CivicComplaint.city_id == city_id).group_by(CivicComplaint.issue_category).all())
    reviews = Counter(d for (d,) in db.query(DuplicateReview.decision).filter(DuplicateReview.city_id == city_id).all())
    zones = load_zones(db, city_id)
    pct = (lambda k: round(100.0 * k / n, 2) if n else 0.0)
    issues = []
    if missing_coords:
        issues.append(f"{missing_coords} records ({pct(missing_coords)}%) lack coordinates: excluded from point clustering and maps.")
    if missing_zone:
        issues.append(f"{missing_zone} records ({pct(missing_zone)}%) lack a zone: excluded from zone-level anomaly tests.")
    if other:
        issues.append(f"{other} records ({pct(other)}%) are uncategorised (OTHER).")
    if future:
        issues.append(f"{future} records have timestamps more than 1 h in the future.")
    if not any(z.get("population") for z in zones):
        issues.append("Zone populations missing: per-capita rates unavailable.")
    if n and "SYNTHETIC_DEMO" in by_prov:
        issues.append(f"{by_prov['SYNTHETIC_DEMO']} records are SYNTHETIC demo data, not real municipal complaints.")
    return {
        "city_id": city_id, "total_records": n, "data_start": _iso(first), "data_end": _iso(last),
        "missing_coordinates": missing_coords, "missing_zone": missing_zone, "uncategorised": other,
        "linked_to_incident": linked, "future_timestamps": future,
        "missing_coordinates_pct": pct(missing_coords), "missing_zone_pct": pct(missing_zone),
        "by_provenance": by_prov, "by_source": by_source, "by_category": by_cat,
        "duplicate_reviews": dict(reviews), "zones_with_population": sum(1 for z in zones if z.get("population")),
        "zones_total": len(zones), "issues": issues,
    }
