"""Canonical PM event envelope utilities.

This module defines deterministic PM event construction rules:
- Stable canonical JSON encoding
- Stable SHA-256 event IDs
- Canonical pm.* event type set
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PMEventType(str, Enum):
    """Canonical PM event types."""

    TASK_CREATED = "pm.task.created"
    TASK_UPDATED = "pm.task.updated"
    TASK_STATUS_CHANGED = "pm.task.status_changed"
    TASK_BLOCKED = "pm.task.blocked"
    TASK_COMPLETED = "pm.task.completed"
    DECISION_LINKED = "pm.decision.linked"
    SYNC_REQUESTED = "pm.sync.requested"
    SYNC_SUCCEEDED = "pm.sync.succeeded"
    SYNC_FAILED = "pm.sync.failed"


PM_EVENT_TYPES = [event_type.value for event_type in PMEventType]


def _datetime_to_utc_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _normalize_for_canonical_json(value: Any) -> Any:
    if isinstance(value, datetime):
        return _datetime_to_utc_z(value)
    if isinstance(value, dict):
        return {str(k): _normalize_for_canonical_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_for_canonical_json(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalize_for_canonical_json(item) for item in value)
    return value


def canonical_json(obj: Any) -> str:
    """Return stable canonical JSON with deterministic key ordering."""
    normalized = _normalize_for_canonical_json(obj)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def sha256_hex(s: str) -> str:
    """Return SHA-256 hex digest for a UTF-8 string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def event_id_for_envelope_core(core: dict[str, Any]) -> str:
    """Compute deterministic event ID from envelope core."""
    return sha256_hex(canonical_json(core))


def normalize_ts_utc(ts_utc: datetime | str) -> str:
    """Normalize timestamp to UTC ISO8601 with trailing Z."""
    if isinstance(ts_utc, datetime):
        return _datetime_to_utc_z(ts_utc)

    if not isinstance(ts_utc, str):
        raise TypeError(f"ts_utc must be datetime or str, got {type(ts_utc)!r}")

    cleaned = ts_utc.strip()
    if not cleaned:
        raise ValueError("ts_utc must not be empty")

    iso_candidate = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
    try:
        parsed = datetime.fromisoformat(iso_candidate)
    except ValueError as exc:
        raise ValueError(f"Invalid ts_utc string: {ts_utc!r}") from exc

    return _datetime_to_utc_z(parsed)


def create_pm_event(
    *,
    event_type: str,
    ts_utc: datetime | str,
    idempotency_key: str,
    source: str,
    task_id: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a deterministic PM envelope dict."""
    if event_type not in PM_EVENT_TYPES:
        raise ValueError(f"Unsupported PM event type: {event_type}")

    core = {
        "event_type": event_type,
        "ts_utc": normalize_ts_utc(ts_utc),
        "idempotency_key": str(idempotency_key),
        "source": str(source),
        "task_id": str(task_id),
        "payload": dict(payload or {}),
    }

    return {
        "event_id": event_id_for_envelope_core(core),
        **core,
    }
