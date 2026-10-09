"""
Shared Gemini REST call used by the photo scanner and the operator copilot.

The public Gemini endpoint intermittently returns HTTP 503 under load and can
take longer than a single timeout to answer, so calls are retried inside a fixed
latency budget and every model in the list is tried before the caller falls back.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# gemini-3.8-flash is the current general-access model; older ids now 404 for new keys.
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"]
ATTEMPTS_PER_MODEL = 3


def gemini_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)


def generate(parts: List[Dict[str, Any]], temperature: float = 0.2, json_mode: bool = False,
             per_request_timeout: float = 25.0,
             budget_seconds: float = 45.0) -> Tuple[Optional[str], Optional[str]]:
    """Return (reply_text, error). Exactly one of them is set."""
    if not gemini_configured():
        return None, "GEMINI_API_KEY is not configured"

    body: Dict[str, Any] = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": temperature},
    }
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    payload = json.dumps(body).encode("utf-8")

    deadline = time.monotonic() + budget_seconds
    last_error = "no attempt made"

    for model in GEMINI_MODELS:
        for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 1:
                logger.warning("Gemini abandoned after budget: %s", last_error)
                return None, f"timed out ({last_error})"
            request = urllib.request.Request(
                ENDPOINT.format(model=model) + f"?key={settings.GEMINI_API_KEY}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=min(per_request_timeout, remaining)) as response:
                    data = json.loads(response.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if text and text.strip():
                    return text.strip(), None
                last_error = f"{model}: empty reply"
            except urllib.error.HTTPError as exc:
                last_error = f"{model}: HTTP {exc.code}"
            except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError,
                    TimeoutError, ValueError) as exc:
                last_error = f"{model}: {type(exc).__name__}"

            logger.warning("Gemini attempt failed (%s, try %d/%d)", last_error, attempt, ATTEMPTS_PER_MODEL)
            if attempt < ATTEMPTS_PER_MODEL and time.monotonic() < deadline:
                time.sleep(min(1.5 * attempt, max(0.1, deadline - time.monotonic())))

    return None, last_error
