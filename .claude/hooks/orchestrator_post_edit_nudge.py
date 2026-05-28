"""
Orchestrator post-edit nudge hook.

Provides:
  on_edit_tool(project_root) -> str | None
    — called from PostToolUse whenever tool_name is "Edit" or "Write".
    Returns a nudge string when the edit threshold is reached and there
    is an active orchestrator work-item, or None otherwise.

State is persisted to .claude/.orchestrator-edit-nudge.json so counts
survive across individual tool calls (native_hooks.py runs fresh each time).
Counter resets to zero on each SessionStart (via reset_edit_counter).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import shared cache reader from the session-start module.
# This import is safe because native_hooks.py adds .claude/hooks/ to sys.path
# before importing this module.
try:
    from orchestrator_session_start import read_context_cache, short_id
except ImportError:
    def read_context_cache(_): return None  # type: ignore[misc]
    def short_id(u): return u[:8] if u else "?"  # type: ignore[misc]

_NUDGE_STATE_FILE = ".orchestrator-edit-nudge.json"
EDIT_THRESHOLD = 5   # edits before first nudge
NUDGE_COOLDOWN = 10  # edits between subsequent nudges


def _nudge_path(project_root: Path, session_id: Optional[str] = None) -> Path:
    if session_id:
        filename = f".orchestrator-edit-nudge-{session_id[:8]}.json"
    else:
        filename = _NUDGE_STATE_FILE
    return project_root / ".claude" / filename


def reset_edit_counter(project_root: Path, session_id: Optional[str] = None) -> None:
    """Zero out the edit counter. Called at SessionStart."""
    try:
        path = _nudge_path(project_root, session_id)
        path.write_text(json.dumps({"edits_since_last_nudge": 0, "updated_at": datetime.now(timezone.utc).isoformat()}))
    except Exception:
        pass


def _read_nudge_state(project_root: Path, session_id: Optional[str] = None) -> dict:
    try:
        path = _nudge_path(project_root, session_id)
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {"edits_since_last_nudge": 0}


def _write_nudge_state(project_root: Path, state: dict, session_id: Optional[str] = None) -> None:
    try:
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        _nudge_path(project_root, session_id).write_text(json.dumps(state))
    except Exception:
        pass


def _first_work_item(cache: Optional[dict]) -> Optional[dict]:
    """Return first active item that is in 'work' role, or None."""
    if not cache:
        return None
    for item in cache.get("activeItems") or []:
        if item.get("role") == "work":
            return item
    return None


def on_edit_tool(project_root: Path, session_id: Optional[str] = None) -> Optional[str]:
    """
    Increment the edit counter and return a nudge string if the threshold
    is reached, or None otherwise.
    """
    cache = read_context_cache(project_root)
    work_item = _first_work_item(cache)
    if not work_item:
        return None  # No active work item — skip nudge entirely

    state = _read_nudge_state(project_root, session_id)
    count = state.get("edits_since_last_nudge", 0) + 1
    threshold = NUDGE_COOLDOWN if state.get("nudge_sent") else EDIT_THRESHOLD

    if count < threshold:
        state["edits_since_last_nudge"] = count
        state["nudge_sent"] = state.get("nudge_sent", False)
        _write_nudge_state(project_root, state, session_id)
        return None

    # Threshold reached — emit nudge and reset counter
    state["edits_since_last_nudge"] = 0
    state["nudge_sent"] = True
    _write_nudge_state(project_root, state, session_id)

    item_id = work_item.get("id", "")
    short = short_id(item_id)
    return (
        f"📝 {count} file edits — consider filing progress:\n"
        f'   manage_notes(operation="upsert", notes=[{{'
        f'"itemId": "{item_id}", "key": "implementation-evidence", '
        f'"role": "work", "body": "..."}}])\n'
        f"   Or: /dx:note {short} implementation-evidence"
    )
