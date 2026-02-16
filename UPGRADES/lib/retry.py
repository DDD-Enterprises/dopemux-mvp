import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional

import requests


def safe_int(raw: Any) -> Optional[int]:
    try:
        if raw is None:
            return None
        return int(str(raw).strip())
    except Exception:
        return None


def parse_retry_after_seconds(raw: str) -> Optional[float]:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        seconds = float(value)
        return max(seconds, 0.0)
    except Exception:
        pass
    try:
        retry_at = parsedate_to_datetime(value)
        now_dt = datetime.now(timezone.utc)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max((retry_at - now_dt).total_seconds(), 0.0)
    except Exception:
        return None


def parse_reset_seconds(raw: str) -> Optional[float]:
    value = str(raw or "").strip().lower()
    if not value:
        return None
    unit_match = re.match(r"^([0-9]*\.?[0-9]+)\s*(ms|s|m|h)$", value)
    if unit_match:
        amount = float(unit_match.group(1))
        unit = unit_match.group(2)
        if unit == "ms":
            return max(amount / 1000.0, 0.0)
        if unit == "s":
            return max(amount, 0.0)
        if unit == "m":
            return max(amount * 60.0, 0.0)
        if unit == "h":
            return max(amount * 3600.0, 0.0)
    return parse_retry_after_seconds(value)


def deterministic_jitter_seconds(seed_material: str, max_ms: int = 250) -> float:
    digest = hashlib.sha256(seed_material.encode("utf-8", errors="ignore")).hexdigest()
    raw = int(digest[:12], 16)
    bucket = raw % (max_ms + 1)
    return float(bucket) / 1000.0


def retry_delay_seconds(attempt: int, retry_after: Optional[float], seed_material: str) -> float:
    jitter = deterministic_jitter_seconds(seed_material=seed_material, max_ms=250)
    if retry_after is not None:
        return max(retry_after, 0.0) + jitter
    base = 1.0
    max_delay = 60.0
    backoff = min(base * (2 ** max(attempt - 1, 0)), max_delay)
    return backoff + jitter


def should_retry_status(status_code: Optional[int]) -> bool:
    if status_code is None:
        return False
    return status_code in {408, 429, 500, 502, 503, 504}


def is_retryable_exception(exc: Exception) -> bool:
    retryable_types = (
        requests.Timeout,
        requests.ConnectionError,
        requests.exceptions.ChunkedEncodingError,
    )
    return isinstance(exc, retryable_types)
