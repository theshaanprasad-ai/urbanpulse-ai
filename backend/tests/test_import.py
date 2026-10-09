"""
Unit tests for CSV / JSON import validation, normalisation and provenance.
"""

import json
from datetime import datetime

from backend.app.engine.csv_ingestion import map_columns, parse_import, parse_timestamp

ZONES = [
    {"id": "chennai-zone-09", "name": "Teynampet (T. Nagar)", "zone_number": 9, "center_lat": 13.0420, "center_lon": 80.2450},
    {"id": "chennai-zone-14", "name": "Perungudi (Velachery / Madipakkam)", "zone_number": 14, "center_lat": 12.9710, "center_lon": 80.2240},
]
BBOX = [12.75, 79.95, 13.35, 80.45]
NOW = datetime(2026, 10, 1, 12, 0)


def _run(content, fmt="CSV", **kw):
    return parse_import(content, fmt, "chennai", ZONES, bbox=BBOX, now=NOW, **kw)


def test_column_mapping_aliases():
    m = map_columns(["Complaint ID", "Description", "Created Date", "Latitude", "Longitude", "Ward", "Category"])
    assert m["tracking_number"] == "Complaint ID"
    assert m["raw_text"] == "Description"
    assert m["reported_at"] == "Created Date"
    assert m["lat"] == "Latitude" and m["lon"] == "Longitude"
    assert m["zone_id"] == "Ward"
    assert m["issue_category"] == "Category"


def test_parse_timestamp_formats():
    assert parse_timestamp("2026-09-30 10:15:00") == datetime(2026, 9, 30, 10, 15)
    assert parse_timestamp("2026-09-30T10:15:00+05:30") == datetime(2026, 9, 30, 4, 45)
    assert parse_timestamp("30/09/2026") == datetime(2026, 9, 30)
    assert parse_timestamp("yesterday") is None
    assert parse_timestamp("") is None


def test_valid_csv_import_with_provenance():
    csv_text = (
        "id,description,category,timestamp,lat,lon,ward\n"
        "A1,Garbage not collected near market,Waste,2026-09-30 08:00:00,13.041,80.244,9\n"
        "A2,Big pothole on 100 ft road,Roads,2026-09-30 09:00:00,12.972,80.221,chennai-zone-14\n"
    )
    r = _run(csv_text, provenance="GCC_PORTAL_EXPORT")
    assert r["valid_rows"] == 2 and r["rejected_rows"] == 0
    a1, a2 = r["records"]
    assert a1["issue_category"] == "WASTE_MANAGEMENT" and a1["zone_id"] == "chennai-zone-09"
    assert a2["issue_category"] == "ROADS_INFRASTRUCTURE" and a2["zone_id"] == "chennai-zone-14"
    assert all(x["provenance"] == "GCC_PORTAL_EXPORT" for x in r["records"])
    assert a1["source"] == "CSV_IMPORT"


def test_invalid_rows_are_rejected_with_reasons():
    csv_text = (
        "id,description,timestamp,lat,lon\n"
        "B1,,2026-09-30 08:00:00,13.04,80.24\n"            # missing text
        "B2,Drain blocked,not-a-date,13.04,80.24\n"         # bad timestamp
        "B3,Drain blocked,2027-01-01 00:00:00,13.04,80.24\n"  # future
        "B4,Drain blocked,2026-09-30 08:00:00,28.6,77.2\n"   # outside bbox
        "B5,Drain blocked,2026-09-30 08:00:00,abc,80.24\n"   # non-numeric
        "B6,Drain blocked,2026-09-30 08:00:00,13.04,80.24\n"
        "B6,Drain blocked again,2026-09-30 09:00:00,13.04,80.24\n"  # duplicate id in file
    )
    r = _run(csv_text)
    assert r["valid_rows"] == 1
    assert r["rejected_rows"] == 6
    reasons = " | ".join(x["reason"] for x in r["rejection_log"])
    for fragment in ("too-short", "unparseable", "future", "bounding box", "Invalid coordinates", "within file"):
        assert fragment in reasons
    assert {x["line"] for x in r["rejection_log"]} == {2, 3, 4, 5, 6, 8}


def test_missing_coordinates_are_kept_but_not_invented():
    csv_text = (
        "description,timestamp,zone\n"
        "Streetlight not working,2026-09-30 20:00:00,Perungudi\n"
        "Streetlight not working,2026-09-30 21:00:00,\n"
        "Water pipe burst near Velachery bus stand,2026-09-30 21:00:00,\n"
    )
    r = _run(csv_text)
    assert r["valid_rows"] == 3
    zone_only, unresolved, gazetteer = r["records"]
    assert zone_only["lat"] is None and zone_only["zone_id"] == "chennai-zone-14"
    assert unresolved["lat"] is None and unresolved["zone_id"] is None
    assert gazetteer["lat"] is not None  # matched a known landmark, disclosed as a warning
    warnings = " | ".join(w for x in r["warning_log"] for w in x["warnings"])
    assert "excluded from geographic analysis" in warnings
    assert "gazetteer" in warnings
    assert r["flagged_rows"] == 3


def test_existing_tracking_numbers_rejected():
    csv_text = "id,description,timestamp\nOLD-1,Garbage pile,2026-09-30 08:00:00\n"
    r = _run(csv_text, existing_tracking={"OLD-1"})
    assert r["valid_rows"] == 0 and "already imported" in r["rejection_log"][0]["reason"]


def test_missing_required_column_rejects_everything():
    r = _run("description,lat,lon\nGarbage,13.0,80.2\n")
    assert r["valid_rows"] == 0 and r["rejected_rows"] == 1
    assert "reported_at" in r["rejection_log"][0]["reason"]


def test_empty_payloads():
    assert _run("")["valid_rows"] == 0
    assert _run("")["rejection_log"]
    assert _run("description,timestamp\n")["total_rows"] == 0
    assert _run("[]", fmt="JSON")["valid_rows"] == 0


def test_json_import_and_row_limit():
    payload = json.dumps({"records": [
        {"complaint": "No water supply since morning", "created_at": "2026-09-30T07:00:00", "latitude": 13.04, "longitude": 80.24},
    ]})
    r = _run(payload, fmt="JSON")
    assert r["valid_rows"] == 1
    assert r["records"][0]["issue_category"] == "WATER_SUPPLY"
    assert r["records"][0]["source"] == "JSON_IMPORT"
    assert r["records"][0]["tracking_number"].startswith("IMP-")

    bad = _run("{not json", fmt="JSON")
    assert bad["valid_rows"] == 0 and bad["rejection_log"]

    many = "description,timestamp\n" + "\n".join(f"Garbage {i},2026-09-30 08:00:00" for i in range(11))
    assert "Too many rows" in _run(many, max_rows=10)["rejection_log"][0]["reason"]
