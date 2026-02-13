"""Pure adapters from dialect events into canonical PM envelopes."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .events import PMEventType, canonical_json, create_pm_event, sha256_hex


_DEFAULT_TS_UTC = "1970-01-01T00:00:00Z"
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(s: str) -> str:
    """Normalize text for deterministic fallback task IDs."""
    return _WHITESPACE_RE.sub(" ", str(s).strip().lower())


def canonical_task_id(
    source: str,
    source_task_id: str | None,
    title: str | None,
    description: str | None,
) -> str:
    """Derive canonical task_id using source ID first, normalized content second."""
    if source_task_id is not None and str(source_task_id) != "":
        return sha256_hex(f"{source}:{source_task_id}")

    norm_title = normalize_text(title or "")
    norm_description = normalize_text(description or "")
    return sha256_hex(f"{source}:{norm_title}:{norm_description}")


def _mapping_get(obj: Any, key: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)


def _to_mapping(obj: Any) -> dict[str, Any]:
    if isinstance(obj, Mapping):
        return dict(obj)
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        dumped = obj.model_dump()
        return dict(dumped) if isinstance(dumped, Mapping) else {}
    if hasattr(obj, "dict") and callable(obj.dict):
        dumped = obj.dict()
        return dict(dumped) if isinstance(dumped, Mapping) else {}
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return {}


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _derive_ts_utc(data: Mapping[str, Any]) -> str:
    return str(
        _first_non_none(
            data.get("ts_utc"),
            data.get("timestamp"),
            data.get("created_at_utc"),
            data.get("updated_at_utc"),
            _DEFAULT_TS_UTC,
        )
    )


def _derive_idempotency_key(
    *,
    source: str,
    dialect_event_type: str,
    raw_data: Mapping[str, Any],
    existing_key: str | None,
) -> str:
    if existing_key:
        return str(existing_key)
    seed = canonical_json(
        {
            "source": source,
            "dialect_event_type": dialect_event_type,
            "raw_data": dict(raw_data),
        }
    )
    return sha256_hex(seed)


def taskmaster_event_to_pm(
    event_type: str,
    data: dict[str, Any],
    source: str = "taskmaster",
) -> dict[str, Any]:
    """Convert taskmaster event surfaces to canonical PM envelope."""
    mapping = {
        "taskmaster.task.created": PMEventType.TASK_CREATED.value,
        "taskmaster.task.status_updated": PMEventType.TASK_STATUS_CHANGED.value,
        "taskmaster.task.completed": PMEventType.TASK_COMPLETED.value,
    }

    mapping_reason: str | None = None
    canonical_event_type = mapping.get(event_type)
    if canonical_event_type is None:
        canonical_event_type = PMEventType.TASK_UPDATED.value
        mapping_reason = "unknown_taskmaster_event_type"

    source_task_id = _first_non_none(
        data.get("source_task_id"),
        data.get("task_id"),
        data.get("id"),
    )
    task_id = canonical_task_id(
        source=source,
        source_task_id=str(source_task_id) if source_task_id is not None else None,
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
    )

    payload = dict(data)
    payload["dialect_event_type"] = event_type
    dialect_status = data.get("status")
    if dialect_status is not None:
        payload["dialect_status"] = str(dialect_status)
    if mapping_reason is not None:
        payload["mapping_reason"] = mapping_reason

    return create_pm_event(
        event_type=canonical_event_type,
        ts_utc=_derive_ts_utc(data),
        idempotency_key=_derive_idempotency_key(
            source=source,
            dialect_event_type=event_type,
            raw_data=data,
            existing_key=data.get("idempotency_key"),
        ),
        source=source,
        task_id=task_id,
        payload=payload,
    )


def orchestrator_event_to_pm(
    coord_event_like: Any,
    source: str = "task-orchestrator",
) -> dict[str, Any]:
    """Convert orchestrator-like event object/dict into canonical PM envelope."""
    root = _to_mapping(coord_event_like)
    payload_obj = _mapping_get(coord_event_like, "payload")
    data_obj = _mapping_get(coord_event_like, "data")
    payload_data = _to_mapping(payload_obj)
    nested_data = _to_mapping(data_obj)

    merged = dict(root)
    merged.update(payload_data)
    merged.update(nested_data)

    dialect_event_type = str(
        _first_non_none(
            _mapping_get(coord_event_like, "event_type"),
            _mapping_get(coord_event_like, "type"),
            root.get("event_type"),
            root.get("type"),
            "unknown",
        )
    )

    mapping = {
        "task_created": PMEventType.TASK_CREATED.value,
        "task_updated": PMEventType.TASK_UPDATED.value,
        "task_completed": PMEventType.TASK_COMPLETED.value,
    }

    mapping_reason: str | None = None
    canonical_event_type = mapping.get(dialect_event_type)
    if canonical_event_type is None:
        canonical_event_type = PMEventType.TASK_UPDATED.value
        mapping_reason = "unknown_orchestrator_event_type"

    source_task_id = _first_non_none(
        _mapping_get(coord_event_like, "task_id"),
        root.get("task_id"),
        payload_data.get("task_id"),
        nested_data.get("task_id"),
        root.get("id"),
        payload_data.get("id"),
        nested_data.get("id"),
    )
    title = _first_non_none(merged.get("title"), merged.get("task_title"), "")
    description = _first_non_none(merged.get("description"), merged.get("task_description"), "")

    task_id = canonical_task_id(
        source=source,
        source_task_id=str(source_task_id) if source_task_id is not None else None,
        title=str(title),
        description=str(description),
    )

    payload = dict(merged)
    payload["dialect_event_type"] = dialect_event_type
    dialect_status = _first_non_none(merged.get("status"), merged.get("task_status"))
    if dialect_status is not None:
        payload["dialect_status"] = str(dialect_status)
    if mapping_reason is not None:
        payload["mapping_reason"] = mapping_reason

    return create_pm_event(
        event_type=canonical_event_type,
        ts_utc=_derive_ts_utc(merged),
        idempotency_key=_derive_idempotency_key(
            source=source,
            dialect_event_type=dialect_event_type,
            raw_data=merged,
            existing_key=str(_first_non_none(merged.get("idempotency_key"), None))
            if _first_non_none(merged.get("idempotency_key"), None) is not None
            else None,
        ),
        source=source,
        task_id=task_id,
        payload=payload,
    )


def pm_to_bus_event(envelope: dict[str, Any]) -> dict[str, Any]:
    """Wrap a PM envelope as a bus event dict."""
    namespace = str(envelope["event_type"])
    if not namespace.startswith("pm."):
        raise ValueError(f"PM namespace must start with 'pm.': {namespace}")
    return {
        "namespace": namespace,
        "payload": {"envelope": envelope},
    }


def pm_to_dopemux_event(envelope: dict[str, Any]) -> dict[str, Any]:
    """Compatibility alias for legacy naming."""
    return pm_to_bus_event(envelope)
