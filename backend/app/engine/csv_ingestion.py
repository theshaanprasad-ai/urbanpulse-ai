"""
CSV / JSON complaint import with validation, normalization and provenance.

Rules:
  * Rows without usable text or a parseable timestamp are rejected (timestamps are never invented).
  * Invalid or out-of-bounds coordinates reject the row; missing coordinates are allowed but flagged,
    and the location is resolved only from a verified landmark gazetteer or a recognised zone.
  * Unknown category labels fall back to rules-based text classification (flagged).
"""

import csv
import hashlib
import io
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.engine.civic_intelligence import CivicIntelligenceEngine

COLUMN_ALIASES: Dict[str, List[str]] = {
    "raw_text": ["raw_text", "description", "complaint", "text", "issue_description", "grievance", "details", "complaint_text", "summary"],
    "issue_category": ["issue_category", "category", "complaint_type", "type", "service", "category_name", "department"],
    "subcategory": ["subcategory", "sub_category", "subtype", "sub_type"],
    "reported_at": ["reported_at", "timestamp", "created_at", "complaint_date", "date", "created_date", "entry_time", "datetime"],
    "lat": ["lat", "latitude", "geo_lat", "location_lat"],
    "lon": ["lon", "lng", "longitude", "geo_lon", "location_lon", "long"],
    "landmark": ["landmark", "location", "address", "area", "street", "place_name", "locality"],
    "zone_id": ["zone_id", "zone", "ward", "ward_no", "ward_id", "division", "zone_name"],
    "tracking_number": ["tracking_number", "tracking_id", "complaint_id", "ticket_no", "ticket_id", "reference_no", "id"],
    "severity_score": ["severity_score", "severity", "priority", "urgency"],
    "status": ["status", "state"],
}

TIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M",
    "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y %H:%M", "%d-%m-%Y",
]
STATUS_VALUES = {"OPEN", "IN_INVESTIGATION", "IN_PROGRESS", "RESOLVED", "CLOSED", "REJECTED"}


def _norm_header(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(h).strip().lower()).strip("_")


def map_columns(header: List[str]) -> Dict[str, str]:
    """Exact alias matches first, then prefix/suffix matches; each source column is used once."""
    norm = {h: _norm_header(h) for h in header}
    mapping: Dict[str, str] = {}
    used: Set[str] = set()
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            hit = next((h for h, n in norm.items() if n == alias and h not in used), None)
            if hit:
                mapping[canonical] = hit
                used.add(hit)
                break
    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical in mapping:
            continue
        for alias in (a for a in aliases if len(a) >= 4):
            hit = next((h for h, n in norm.items() if h not in used and (n.startswith(alias) or n.endswith(alias))), None)
            if hit:
                mapping[canonical] = hit
                used.add(hit)
                break
    return mapping


def parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        pass
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(s.split(".")[0], fmt)
        except ValueError:
            continue
    return None


def _match_zone(value: Optional[str], zones: List[Dict[str, Any]]) -> Optional[str]:
    if not value:
        return None
    v = str(value).strip().lower()
    for z in zones:
        if v == z["id"].lower() or v == z["name"].lower():
            return z["id"]
    digits = re.findall(r"\d+", v)
    if digits:
        n = int(digits[-1])
        for z in zones:
            if z.get("zone_number") == n:
                return z["id"]
    for z in zones:
        if len(v) >= 4 and (v in z["name"].lower() or z["name"].lower() in v):
            return z["id"]
    return None


def _records_from_payload(content: str, fmt: str) -> Tuple[List[str], List[Dict[str, Any]], Optional[str]]:
    if fmt == "JSON":
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return [], [], f"Invalid JSON: {e.msg} (line {e.lineno})"
        if isinstance(data, dict):
            data = data.get("records") or data.get("complaints") or data.get("data")
        if not isinstance(data, list):
            return [], [], "JSON must be an array of objects or an object with a 'records' array"
        rows = [r for r in data if isinstance(r, dict)]
        if len(rows) != len(data):
            return [], [], "Every JSON record must be an object"
        header: List[str] = []
        for r in rows:
            for k in r.keys():
                if k not in header:
                    header.append(k)
        return header, rows, None

    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    if not reader.fieldnames:
        return [], [], "Empty CSV file (no header row)"
    return list(reader.fieldnames), list(reader), None


def parse_import(
    content: str,
    fmt: str,
    city_id: str,
    zones: List[Dict[str, Any]],
    bbox: Optional[List[float]] = None,
    existing_tracking: Optional[Set[str]] = None,
    provenance: str = "USER_IMPORT",
    max_rows: int = 20_000,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    fmt = fmt.upper()
    now = now or datetime.utcnow()
    existing_tracking = existing_tracking or set()
    header, rows, error = _records_from_payload(content, fmt)
    base = {
        "format": fmt, "total_rows": 0, "valid_rows": 0, "rejected_rows": 0, "flagged_rows": 0,
        "records": [], "rejection_log": [], "warning_log": [], "column_mapping": {}, "unmapped_columns": [],
    }
    if error:
        base["rejection_log"] = [{"line": 0, "reason": error}]
        return base
    if len(rows) > max_rows:
        base["rejection_log"] = [{"line": 0, "reason": f"Too many rows ({len(rows)}); limit is {max_rows}"}]
        return base

    mapping = map_columns(header)
    base["column_mapping"] = mapping
    base["unmapped_columns"] = [h for h in header if h not in mapping.values()]
    if "raw_text" not in mapping or "reported_at" not in mapping:
        missing = [k for k in ("raw_text", "reported_at") if k not in mapping]
        base["total_rows"] = len(rows)
        base["rejected_rows"] = len(rows)
        base["rejection_log"] = [{"line": 0, "reason": f"Required column(s) not found: {', '.join(missing)}"}]
        return base

    lat_lo, lon_lo, lat_hi, lon_hi = bbox if bbox else (6.0, 68.0, 37.5, 97.5)
    first_line = 2 if fmt == "CSV" else 1
    seen: Set[str] = set()
    records, rejected, warnings = [], [], []

    def get(row: Dict[str, Any], key: str) -> Optional[str]:
        col = mapping.get(key)
        if not col:
            return None
        v = row.get(col)
        if v is None:
            return None
        v = str(v).strip()
        return v or None

    for offset, row in enumerate(rows):
        line = first_line + offset
        if all(v is None or str(v).strip() == "" for v in row.values()):
            continue
        row_warnings: List[str] = []

        text = CivicIntelligenceEngine.sanitize_input(get(row, "raw_text") or "")
        if len(text) < 3:
            rejected.append({"line": line, "reason": "Missing or too-short complaint text"})
            continue

        ts_raw = get(row, "reported_at")
        ts = parse_timestamp(ts_raw)
        if ts is None:
            rejected.append({"line": line, "reason": f"Missing or unparseable timestamp: {ts_raw!r}"})
            continue
        if ts > now + timedelta(hours=1):
            rejected.append({"line": line, "reason": f"Timestamp is in the future: {ts.isoformat()}"})
            continue
        if ts.year < 2000:
            rejected.append({"line": line, "reason": f"Timestamp before 2000: {ts.isoformat()}"})
            continue

        lat_s, lon_s = get(row, "lat"), get(row, "lon")
        lat = lon = None
        if lat_s is not None or lon_s is not None:
            try:
                lat, lon = float(lat_s), float(lon_s)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                rejected.append({"line": line, "reason": f"Invalid coordinates: ({lat_s}, {lon_s})"})
                continue
            if not (lat_lo <= lat <= lat_hi and lon_lo <= lon <= lon_hi):
                rejected.append({"line": line, "reason": f"Coordinates outside the city bounding box: ({lat}, {lon})"})
                continue

        zone_raw = get(row, "zone_id")
        zone_id = _match_zone(zone_raw, zones)
        if zone_raw and not zone_id:
            row_warnings.append(f"Zone '{zone_raw}' not recognised")
        landmark = get(row, "landmark")
        loc = CivicIntelligenceEngine.resolve_location(text, landmark, lat, lon, zone_id, zones)
        if loc["lat"] is None:
            row_warnings.append(
                "No coordinates; zone from source column" if loc["zone_id"] else
                "No coordinates or recognised zone; excluded from geographic analysis"
            )
        elif loc["method"] == "GAZETTEER_LANDMARK":
            row_warnings.append(f"Coordinates taken from gazetteer landmark '{loc['landmark']}'")

        classified = CivicIntelligenceEngine.classify_complaint(text)
        category, sub = CivicIntelligenceEngine.normalize_category(get(row, "issue_category"))
        if category is None:
            category = classified["issue_category"]
            sub = classified["subcategory"]
            raw_cat = get(row, "issue_category")
            row_warnings.append(
                f"Category '{raw_cat}' not recognised; classified from text as {category}" if raw_cat
                else f"No category column value; classified from text as {category}"
            )
        sub = get(row, "subcategory") or sub or classified["subcategory"]

        sev_s = get(row, "severity_score")
        severity = classified["severity_score"]
        if sev_s is not None:
            try:
                severity = max(1, min(5, int(float(sev_s))))
            except ValueError:
                row_warnings.append(f"Severity '{sev_s}' not numeric; used text heuristic")

        tracking = get(row, "tracking_number")
        if not tracking:
            digest = hashlib.sha1(f"{city_id}|{ts.isoformat()}|{text}".encode("utf-8")).hexdigest()[:12]
            tracking = f"IMP-{digest.upper()}"
        tracking = tracking[:50]
        if tracking in seen:
            rejected.append({"line": line, "reason": f"Duplicate tracking number within file: {tracking}"})
            continue
        if tracking in existing_tracking:
            rejected.append({"line": line, "reason": f"Tracking number already imported: {tracking}"})
            continue
        seen.add(tracking)

        status = (get(row, "status") or "OPEN").upper().replace(" ", "_")
        if status not in STATUS_VALUES:
            status = "OPEN"

        records.append({
            "city_id": city_id,
            "zone_id": loc["zone_id"],
            "tracking_number": tracking,
            "raw_text": text[:1000],
            "parsed_summary": classified["parsed_summary"],
            "language_detected": classified["detected_language"],
            "issue_category": category,
            "subcategory": sub,
            "severity_score": severity,
            "is_severe_hazard": classified["is_severe_hazard"],
            "reported_at": ts,
            "lat": loc["lat"],
            "lon": loc["lon"],
            "landmark": loc["landmark"],
            "status": status,
            "source": f"{fmt}_IMPORT",
            "source_system": "USER_UPLOAD",
            "provenance": provenance,
        })
        if row_warnings:
            warnings.append({"line": line, "tracking_number": tracking, "warnings": row_warnings})

    base.update({
        "total_rows": len(records) + len(rejected),
        "valid_rows": len(records),
        "rejected_rows": len(rejected),
        "flagged_rows": len(warnings),
        "records": records,
        "rejection_log": rejected[:200],
        "warning_log": warnings[:200],
    })
    return base
