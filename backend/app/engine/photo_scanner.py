"""
Citizen photo scanning for civic issues.

Uses Gemini vision when a key is configured, then falls back to the offline
civic classifier so reports still succeed during demos and network failures.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

from backend.app.engine.civic_intelligence import CANONICAL_CATEGORIES, CivicIntelligenceEngine
from backend.app.engine.gemini_client import gemini_configured, generate

logger = logging.getLogger(__name__)

VISION_TIMEOUT_SECONDS = 25
VISION_BUDGET_SECONDS = 45

SCAN_PROMPT = """You are a municipal field inspector for Indian cities.
Look at this photo of a possible civic problem (pothole, water blockade, flooding,
garbage, blocked drain, streetlight failure, exposed wire, damaged public asset).

Return JSON only with this shape:
{
  "problem_confirmed": true,
  "issue_category": "ROADS_INFRASTRUCTURE",
  "subcategory": "Pothole",
  "severity_score": 3,
  "is_severe_hazard": false,
  "confidence": 0.86,
  "what_is_going_on": "Plain language for the resident.",
  "officer_notes": "Short note for municipal staff.",
  "visible_cues": ["broken asphalt", "standing water"]
}

issue_category MUST be one of:
WASTE_MANAGEMENT, WATER_SUPPLY, ROADS_INFRASTRUCTURE, DRAINAGE_SANITATION,
STREETLIGHTS_ELECTRICITY, POWER_SUPPLY, PUBLIC_ASSETS, ILLEGAL_DUMPING, OTHER.

severity_score is 1-5. Set is_severe_hazard true only for life-safety risks
(open manhole, live wire, deep flooding trapping vehicles, collapse).
If the photo is not a civic issue, set problem_confirmed false and category OTHER.
Citizen note: %s
Hint category: %s
"""


def strip_data_url(image_base64: str) -> tuple[str, Optional[str]]:
    raw = (image_base64 or "").strip()
    mime = None
    match = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", raw, re.DOTALL)
    if match:
        mime = match.group(1)
        raw = match.group(2)
    return re.sub(r"\s+", "", raw), mime


def _local_scan(note: str, hint_category: Optional[str], fallback_reason: Optional[str] = None) -> Dict[str, Any]:
    text = note.strip() or "Citizen uploaded a photo of a local civic problem."
    if hint_category:
        text = f"{hint_category.replace('_', ' ').lower()}: {text}"
    classified = CivicIntelligenceEngine.classify_complaint(text)
    category = hint_category if hint_category in CANONICAL_CATEGORIES else classified["issue_category"]
    summary = classified.get("parsed_summary") or text
    return {
        "problem_confirmed": True,
        "issue_category": category,
        "subcategory": classified.get("subcategory") or (hint_category or "Citizen photo report").replace("_", " ").title(),
        "severity_score": classified["severity_score"],
        "is_severe_hazard": classified.get("is_severe_hazard", False),
        "confidence": 0.55 if note.strip() else 0.4,
        "what_is_going_on": summary,
        "officer_notes": "Photo received. Local rules classified the report because live vision was unavailable.",
        "visible_cues": ["Citizen photo attached"],
        "scan_source": "LOCAL_RULES",
        "scan_fallback_reason": fallback_reason,
        "language_detected": classified.get("detected_language", "English"),
        "sanitized_text": classified.get("sanitized_text", text),
    }


def _parse_gemini_json(raw: str) -> Optional[Dict[str, Any]]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    return data


def _gemini_scan(image_b64: str, mime_type: str, note: str,
                 hint_category: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Vision scan. Returns (result, failure_reason); the caller falls back on failure."""
    if not gemini_configured():
        return None, "GEMINI_API_KEY is not configured"

    prompt = SCAN_PROMPT % (note or "(none)", hint_category or "(none)")
    raw, error = generate(
        [{"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": image_b64}}],
        temperature=0.2,
        json_mode=True,
        per_request_timeout=VISION_TIMEOUT_SECONDS,
        budget_seconds=VISION_BUDGET_SECONDS,
    )
    if error:
        return None, f"Vision scan unavailable ({error})"

    parsed = _parse_gemini_json(raw or "")
    if not parsed:
        return None, "Vision reply was not valid JSON"
    return _normalise_gemini(parsed, hint_category), None


def _normalise_gemini(parsed: Dict[str, Any], hint_category: Optional[str]) -> Dict[str, Any]:
    category = str(parsed.get("issue_category") or "OTHER").upper()
    if category not in CANONICAL_CATEGORIES:
        category = "OTHER"
    try:
        severity = max(1, min(5, int(parsed.get("severity_score") or 3)))
    except (TypeError, ValueError):
        severity = 3
    try:
        confidence = max(0.0, min(1.0, float(parsed.get("confidence") or 0.7)))
    except (TypeError, ValueError):
        confidence = 0.7
    cues = parsed.get("visible_cues") or []
    if not isinstance(cues, list):
        cues = [str(cues)]
    return {
        "problem_confirmed": bool(parsed.get("problem_confirmed", True)),
        "issue_category": hint_category if hint_category in CANONICAL_CATEGORIES and confidence < 0.45 else category,
        "subcategory": str(parsed.get("subcategory") or "Photo-confirmed civic issue")[:120],
        "severity_score": severity,
        "is_severe_hazard": bool(parsed.get("is_severe_hazard", False)),
        "confidence": confidence,
        "what_is_going_on": str(parsed.get("what_is_going_on") or "Civic issue detected from the uploaded photo."),
        "officer_notes": str(parsed.get("officer_notes") or "Gemini vision classified this citizen photo."),
        "visible_cues": [str(item)[:80] for item in cues][:8],
        "scan_source": "GEMINI_VISION",
        "scan_fallback_reason": None,
        "language_detected": "English",
        "sanitized_text": str(parsed.get("what_is_going_on") or "Citizen photo report"),
    }


def scan_citizen_photo(
    image_base64: str,
    mime_type: Optional[str] = None,
    note: str = "",
    hint_category: Optional[str] = None,
) -> Dict[str, Any]:
    cleaned, inferred_mime = strip_data_url(image_base64)
    mime = mime_type or inferred_mime or "image/jpeg"
    if mime not in {"image/jpeg", "image/jpg", "image/png", "image/webp"}:
        mime = "image/jpeg"
    if not cleaned:
        raise ValueError("A photo is required.")
    if len(cleaned) > 5_500_000:
        raise ValueError("Photo is too large. Please upload a smaller image (under 4 MB).")

    gemini, failure_reason = _gemini_scan(cleaned, mime, note, hint_category)
    if gemini:
        return gemini
    if failure_reason:
        logger.warning("Falling back to local civic classifier: %s", failure_reason)
    return _local_scan(note, hint_category, failure_reason)
