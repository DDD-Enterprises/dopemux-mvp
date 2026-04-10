from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def synthetic_id(prefix: str, suffix: str) -> str:
    normalized_prefix = prefix.strip().lower()
    normalized_suffix = suffix.strip().replace(" ", "_").replace("/", "_").replace("-", "_").lower()
    return f"{normalized_prefix}_{normalized_suffix}"


def synthetic_run_id(tag: str = "smoke") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"br_{tag}_{stamp}"

