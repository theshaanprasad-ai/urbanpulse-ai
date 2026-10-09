"""
Duplicate candidate detection for complaint records.

Pairs are scored on spatial distance, time gap, text similarity and category agreement.
Candidates are only *suggested* for human review: nothing is deleted or merged automatically.
"""

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
import re

from backend.app.engine.civic_intelligence import haversine_m

MAX_DISTANCE_M = 400.0
MAX_TIME_HOURS = 48.0
DEFAULT_THRESHOLD = 0.60
LIKELY_THRESHOLD = 0.75
W_DISTANCE, W_TIME, W_TEXT = 0.4, 0.2, 0.4
CATEGORY_MISMATCH_FACTOR = 0.6

_STOP = {
    "the", "is", "at", "in", "on", "near", "and", "a", "an", "to", "of", "for", "with", "from", "this", "that",
    "hai", "me", "ke", "ki", "ka", "par", "se", "aur",
}


def _parse_time(t: Any) -> datetime:
    if isinstance(t, str):
        t = datetime.fromisoformat(t.replace("Z", "+00:00"))
    return t.replace(tzinfo=None) if t.tzinfo else t


def _tokens(text: str) -> Set[str]:
    words = re.findall(r"\w+", (text or "").lower())
    return {w for w in words if w not in _STOP and len(w) > 2}


def _trigrams(text: str) -> Set[str]:
    s = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (text or "").lower())).strip()
    return {s[i:i + 3] for i in range(len(s) - 2)} if len(s) >= 3 else set()


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class DuplicateDetector:

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return haversine_m(lat1, lon1, lat2, lon2)

    @staticmethod
    def calculate_token_jaccard(text1: str, text2: str) -> float:
        return round(_jaccard(_tokens(text1), _tokens(text2)), 3)

    @staticmethod
    def text_similarity(text1: str, text2: str) -> float:
        """max(word-token Jaccard, character-trigram Jaccard); trigrams help with mixed scripts and typos."""
        return round(max(_jaccard(_tokens(text1), _tokens(text2)), _jaccard(_trigrams(text1), _trigrams(text2))), 3)

    @classmethod
    def evaluate_pair(
        cls,
        c1: Dict[str, Any],
        c2: Dict[str, Any],
        max_distance_meters: float = MAX_DISTANCE_M,
        max_time_hours: float = MAX_TIME_HOURS,
    ) -> Tuple[float, Optional[Dict[str, Any]]]:
        """Returns (score, details). Score is 0 with details None when a hard gate fails."""
        t1, t2 = _parse_time(c1["reported_at"]), _parse_time(c2["reported_at"])
        dt_min = abs((t1 - t2).total_seconds()) / 60.0
        if dt_min > max_time_hours * 60.0:
            return 0.0, None

        has_coords = all(c.get(k) is not None for c in (c1, c2) for k in ("lat", "lon"))
        if has_coords:
            dist_m = haversine_m(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
            if dist_m > max_distance_meters:
                return 0.0, None
            dist_score = 1.0 - dist_m / max_distance_meters
            location_basis = "coordinates"
        else:
            if not c1.get("zone_id") or c1.get("zone_id") != c2.get("zone_id"):
                return 0.0, None
            dist_m = None
            dist_score = 0.3  # same zone only: weak location evidence
            location_basis = "same zone (coordinates missing)"

        time_score = 1.0 - dt_min / (max_time_hours * 60.0)
        text_sim = cls.text_similarity(c1.get("raw_text", ""), c2.get("raw_text", ""))
        same_category = c1.get("issue_category") == c2.get("issue_category")
        factor = 1.0 if same_category else CATEGORY_MISMATCH_FACTOR

        score = round((W_DISTANCE * dist_score + W_TIME * time_score + W_TEXT * text_sim) * factor, 3)

        explanation = (
            f"Location: {f'{int(dist_m)} m apart' if dist_m is not None else location_basis} "
            f"(component {dist_score:.2f} x {W_DISTANCE}); "
            f"time gap {int(dt_min)} min (component {time_score:.2f} x {W_TIME}); "
            f"text similarity {int(text_sim * 100)}% (x {W_TEXT}); "
            f"category {'same' if same_category else f'different (x {CATEGORY_MISMATCH_FACTOR})'}. "
            "Heuristic similarity score, not a probability."
        )
        suggested = "LIKELY_DUPLICATE" if score >= LIKELY_THRESHOLD else (
            "POSSIBLE_DUPLICATE" if score >= DEFAULT_THRESHOLD else "DISTINCT"
        )
        return score, {
            "distance_meters": round(dist_m, 1) if dist_m is not None else None,
            "time_diff_minutes": round(dt_min, 1),
            "text_similarity_score": text_sim,
            "same_category": same_category,
            "composite_match_score": score,
            "suggested_action": suggested,
            "explanation": explanation,
        }

    @classmethod
    def find_duplicate_candidates(
        cls,
        complaints: List[Dict[str, Any]],
        threshold: float = DEFAULT_THRESHOLD,
        exclude_pairs: Optional[Iterable[Tuple[int, int]]] = None,
        max_time_hours: float = MAX_TIME_HOURS,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Sliding time window scan (sorted by time) so cost grows with local density, not n^2."""
        excluded = {tuple(sorted(p)) for p in (exclude_pairs or [])}
        items = sorted(complaints, key=lambda c: _parse_time(c["reported_at"]))
        times = [_parse_time(c["reported_at"]) for c in items]
        horizon = max_time_hours * 3600.0
        out: List[Dict[str, Any]] = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if (times[j] - times[i]).total_seconds() > horizon:
                    break
                a, b = items[i], items[j]
                if tuple(sorted((a["id"], b["id"]))) in excluded:
                    continue
                if a.get("linked_incident_id") and a.get("linked_incident_id") == b.get("linked_incident_id"):
                    continue
                score, details = cls.evaluate_pair(a, b, max_time_hours=max_time_hours)
                if details and score >= threshold:
                    out.append({"complaint_a": a, "complaint_b": b, **details})
        out.sort(key=lambda x: x["composite_match_score"], reverse=True)
        return out[:limit] if limit else out
