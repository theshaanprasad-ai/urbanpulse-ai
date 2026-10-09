"""
Spatial and spatiotemporal hotspot detection.

1. Point clusters: complaints of one category in the last 72h are grouped greedily within a
   fixed radius. Each cluster is compared with the *same location's* history (same category,
   same radius, previous 28 days excluding a 3-day guard) using an exact conditional Poisson
   rate test, so large-but-normal areas are not flagged for raw volume alone.
2. Neighbourhood pooling: for each zone and category the zone is pooled with neighbouring zones
   (centroid distance threshold) to detect coordinated increases that may be too weak to be
   significant in any single zone.
Both families are corrected separately with Benjamini-Hochberg.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.engine.civic_intelligence import haversine_m
from backend.app.engine.temporal_anomaly_engine import (
    BASELINE_WINDOWS, FDR_ALPHA, GUARD_WINDOWS, MIN_BASELINE_WINDOWS, benjamini_hochberg, pooled_test,
)

CLUSTER_RADIUS_M = 400.0
CLUSTER_MIN_SIZE = 3
CLUSTER_WINDOW_HOURS = 72
NEIGHBOUR_RADIUS_KM = 7.0
NEIGHBOURHOOD_MIN_OBSERVED = 5

METHOD_CLUSTER = (
    "Greedy fixed-radius clustering (400 m, last 72 h) + exact conditional Poisson test against the "
    "same location's 28-day history; BH-corrected across clusters"
)
METHOD_NEIGHBOURHOOD = (
    "Pooled zone + neighbouring zones (centroids within 7 km), 72 h vs 28-day baseline, exact conditional "
    "Poisson test; BH-corrected across zone-category neighbourhoods"
)


def zone_neighbours(zones: List[Dict[str, Any]], radius_km: float = NEIGHBOUR_RADIUS_KM) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {z["id"]: [] for z in zones}
    for i, a in enumerate(zones):
        for b in zones[i + 1:]:
            if haversine_m(a["center_lat"], a["center_lon"], b["center_lat"], b["center_lon"]) <= radius_km * 1000:
                out[a["id"]].append(b["id"])
                out[b["id"]].append(a["id"])
    return out


def _local_distances(lat0: float, lon0: float, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Equirectangular approximation; accurate to well under 1% at city scale."""
    k = 111_320.0
    dx = (lons - lon0) * k * np.cos(np.radians(lat0))
    dy = (lats - lat0) * k
    return np.sqrt(dx * dx + dy * dy)


def point_clusters(
    records: List[Dict[str, Any]],
    as_of: datetime,
    covered_days: int,
    radius_m: float = CLUSTER_RADIUS_M,
    min_size: int = CLUSTER_MIN_SIZE,
    window_hours: int = CLUSTER_WINDOW_HOURS,
) -> List[Dict[str, Any]]:
    recent_start = as_of - timedelta(hours=window_hours)
    guard_days = window_hours // 24
    base_end = recent_start
    base_days = min(BASELINE_WINDOWS, max(0, covered_days - guard_days))
    base_start = base_end - timedelta(days=base_days)
    if base_days < MIN_BASELINE_WINDOWS:
        return []

    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        if r.get("lat") is None or r.get("lon") is None:
            continue
        by_cat.setdefault(r["issue_category"], []).append(r)

    clusters: List[Dict[str, Any]] = []
    for cat, recs in by_cat.items():
        lats = np.array([r["lat"] for r in recs])
        lons = np.array([r["lon"] for r in recs])
        times = np.array([r["reported_at"] for r in recs])
        recent_mask = np.array([recent_start < t <= as_of for t in times])
        base_mask = np.array([base_start < t <= base_end for t in times])
        recent_idx = np.where(recent_mask)[0]
        if len(recent_idx) < min_size:
            continue

        unassigned = set(recent_idx.tolist())
        while len(unassigned) >= min_size:
            ids = np.array(sorted(unassigned))
            best_seed, best_members = None, None
            for i in ids:
                d = _local_distances(lats[i], lons[i], lats[ids], lons[ids])
                members = ids[d <= radius_m]
                if best_members is None or len(members) > len(best_members):
                    best_seed, best_members = i, members
            if best_members is None or len(best_members) < min_size:
                break
            unassigned -= set(best_members.tolist())
            c_lat = float(lats[best_members].mean())
            c_lon = float(lons[best_members].mean())
            d_all = _local_distances(c_lat, c_lon, lats, lons)
            observed = int(((d_all <= radius_m) & recent_mask).sum())
            baseline = int(((d_all <= radius_m) & base_mask).sum())
            expected, p = pooled_test(observed, baseline, float(guard_days), float(base_days))
            member_recs = [recs[i] for i in best_members]
            zones = [m.get("zone_id") for m in member_recs if m.get("zone_id")]
            landmarks = [m.get("landmark") for m in member_recs if m.get("landmark")]
            clusters.append({
                "category": cat,
                "center_lat": round(c_lat, 6),
                "center_lon": round(c_lon, 6),
                "radius_meters": radius_m,
                "zone_id": max(set(zones), key=zones.count) if zones else None,
                "landmark": max(set(landmarks), key=landmarks.count) if landmarks else None,
                "observed": observed,
                "baseline_count": baseline,
                "baseline_days": base_days,
                "window_hours": window_hours,
                "expected": round(expected, 3),
                "ratio": round(observed / expected, 2) if expected > 0 else None,
                "p_value": p,
                "supporting_complaint_ids": sorted(int(m["id"]) for m in member_recs),
                "first_reported_at": min(m["reported_at"] for m in member_recs),
                "last_reported_at": max(m["reported_at"] for m in member_recs),
                "method": METHOD_CLUSTER,
            })

    q = benjamini_hochberg([c["p_value"] for c in clusters])
    for c, qv in zip(clusters, q):
        c["q_value"] = float(qv)
        c["significant"] = bool(qv <= FDR_ALPHA)
    clusters.sort(key=lambda c: (c["q_value"], -c["observed"]))
    return clusters


def neighbourhood_tests(
    cells: Dict[Tuple[str, str], Dict[str, Any]],
    neighbours: Dict[str, List[str]],
    zone_names: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    cells[(zone, cat)] needs: observed_3d, baseline_total, f_obs_3d, f_base, expected_3d.
    Returns deduplicated significant neighbourhood increases (>= 2 member zones above expectation).
    """
    results: List[Dict[str, Any]] = []
    cats = sorted({c for (_, c) in cells})
    for cat in cats:
        for zone_id, nbrs in neighbours.items():
            members = [z for z in [zone_id, *nbrs] if (z, cat) in cells]
            if len(members) < 2:
                continue
            obs = sum(cells[(z, cat)]["observed_3d"] for z in members)
            base = sum(cells[(z, cat)]["baseline_total"] for z in members)
            f_obs = cells[(members[0], cat)]["f_obs_3d"] * len(members)
            f_base = cells[(members[0], cat)]["f_base"] * len(members)
            expected, p = pooled_test(obs, base, f_obs, f_base)
            above = [z for z in members if cells[(z, cat)]["observed_3d"] > cells[(z, cat)]["expected_3d"] * 1.25]
            results.append({
                "anchor_zone_id": zone_id,
                "category": cat,
                "member_zone_ids": members,
                "member_zone_names": [zone_names.get(z, z) for z in members],
                "zones_above_expected": above,
                "observed": obs,
                "expected": round(expected, 3),
                "ratio": round(obs / expected, 2) if expected > 0 else None,
                "p_value": p,
                "window_hours": 72,
                "method": METHOD_NEIGHBOURHOOD,
            })

    q = benjamini_hochberg([r["p_value"] for r in results])
    for r, qv in zip(results, q):
        r["q_value"] = float(qv)

    sig = [
        r for r in results
        if r["q_value"] <= FDR_ALPHA and r["observed"] >= NEIGHBOURHOOD_MIN_OBSERVED and len(r["zones_above_expected"]) >= 2
    ]
    sig.sort(key=lambda r: (r["q_value"], -r["observed"]))
    kept: List[Dict[str, Any]] = []
    for r in sig:
        zs = set(r["zones_above_expected"])
        if any(k["category"] == r["category"] and len(zs & set(k["zones_above_expected"])) / len(zs | set(k["zones_above_expected"])) >= 0.5 for k in kept):
            continue
        kept.append(r)
    return kept
