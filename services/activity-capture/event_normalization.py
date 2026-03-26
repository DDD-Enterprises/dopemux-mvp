"""
Normalize legacy event names and payload shapes for Activity Capture.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple


EVENT_ALIASES = {
    "workspace.switched": "workspace.switched",
    "workspace_switched": "workspace.switched",
    "session.started": "session.started",
    "session_started": "session.started",
    "progress.updated": "progress.updated",
    "progress_updated": "progress.updated",
    "task.progress.updated": "progress.updated",
    "task_progress_updated": "progress.updated",
    "break.taken": "break.taken",
    "break_taken": "break.taken",
}


def normalize_event_type(event_type: str) -> str:
    """Map legacy dotted and underscored names to one canonical shape."""
    normalized = (event_type or "").strip()
    return EVENT_ALIASES.get(normalized, normalized)


def normalize_event(event_type: str, event_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Normalize event name and payload for downstream activity tracking."""
    normalized_type = normalize_event_type(event_type)
    normalized_data = dict(event_data or {})

    if normalized_type == "workspace.switched":
        normalized_data = normalize_workspace_switch(normalized_data)
    elif normalized_type == "progress.updated":
        normalized_data = normalize_progress_update(normalized_data)
    elif normalized_type == "session.started":
        normalized_data = normalize_session_started(normalized_data)
    elif normalized_type == "break.taken":
        normalized_data = normalize_break_taken(normalized_data)

    return normalized_type, normalized_data


def normalize_workspace_switch(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten watcher payloads into a single file activity summary."""
    normalized = dict(event_data)
    context_capture = normalized.get("adhd_context_capture") or {}
    raw_file_activity = normalized.get("file_activity") or context_capture.get("file_activity") or {}

    if not isinstance(raw_file_activity, dict):
        raw_file_activity = {}

    files_modified = int(raw_file_activity.get("files_modified", 0) or 0)
    normalized["file_activity"] = {
        "has_recent_activity": bool(raw_file_activity.get("has_recent_activity", files_modified > 0)),
        "files_modified": files_modified,
        "most_recent_file": raw_file_activity.get("most_recent_file"),
        "seconds_since_last_save": raw_file_activity.get("seconds_since_last_save"),
    }
    normalized["from_app"] = normalized.get("from_app")
    normalized["to_app"] = normalized.get("to_app")
    normalized["switch_type"] = normalized.get("switch_type")
    normalized["workspace_id"] = normalized.get("workspace_id") or normalized.get("to_workspace") or "unknown"
    normalized.pop("adhd_context_capture", None)
    return normalized


def normalize_progress_update(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Accept bridge and task-orchestrator payload variants."""
    normalized = dict(event_data)
    status = normalized.get("status") or normalized.get("to_status") or normalized.get("new_status")
    progress = normalized.get("progress")

    if progress is None:
        if status in {"DONE", "COMPLETED"}:
            progress = 1.0
        elif status:
            progress = 0.5
        else:
            progress = 0.0

    normalized["status"] = status or "UNKNOWN"
    normalized["progress"] = progress
    normalized["task_id"] = normalized.get("task_id") or normalized.get("id") or "unknown"
    return normalized


def normalize_session_started(event_data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(event_data)
    normalized["session_id"] = normalized.get("session_id") or normalized.get("task_id") or "unknown"
    return normalized


def normalize_break_taken(event_data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(event_data)
    normalized["duration_minutes"] = (
        normalized.get("duration_minutes")
        or normalized.get("minutes")
        or normalized.get("duration")
        or 5
    )
    return normalized
