"""
Orchestrator SessionStart context injector.

Provides two public functions used by native_hooks.py:
  write_context_cache(project_root, tool_response)
    — called from PostToolUse when mcp__task-orchestrator__get_context
      fires in health-check mode (no itemId, no since).
  emit_session_context(project_root) -> str | None
    — called from SessionStart to inject active item summary.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_CACHE_FILENAME = ".orchestrator-context-cache.json"
_CACHE_MAX_AGE_HOURS = 4


def _cache_path(project_root: Path) -> Path:
    return project_root / ".claude" / _CACHE_FILENAME


def read_context_cache(project_root: Path) -> Optional[dict]:
    """Return parsed cache dict, or None if missing/stale/malformed."""
    path = _cache_path(project_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        written_at_raw = data.get("written_at", "")
        if written_at_raw:
            written_at = datetime.fromisoformat(written_at_raw)
            age_hours = (datetime.now(timezone.utc) - written_at).total_seconds() / 3600
            if age_hours > _CACHE_MAX_AGE_HOURS:
                return None
        return data
    except Exception:
        return None


def write_context_cache(project_root: Path, tool_response: Any) -> None:
    """
    Parse a get_context() health-check response and persist to cache.
    tool_response may be a JSON string or already-parsed dict.
    Silently ignores errors — hook failures must never block work.
    """
    try:
        if isinstance(tool_response, str):
            data = json.loads(tool_response)
        elif isinstance(tool_response, dict):
            data = dict(tool_response)
        else:
            return
        # Only cache health-check responses (mode field present)
        if data.get("mode") not in ("health-check", None):
            if "activeItems" not in data:
                return
        data["written_at"] = datetime.now(timezone.utc).isoformat()
        _cache_path(project_root).write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def short_id(uuid: str) -> str:
    return uuid[:8] if uuid else "?"


def emit_session_context(project_root: Path) -> Optional[str]:
    """
    Return a formatted orchestrator context block for SessionStart injection,
    or None if there's nothing useful to show (no active items in cache).
    """
    cache = read_context_cache(project_root)

    if not cache:
        return None

    active = cache.get("activeItems") or []
    blocked = cache.get("blockedItems") or []
    stalled = cache.get("stalledItems") or []

    if not active and not blocked and not stalled:
        return None

    lines = ["🔧 Orchestrator (cached):"]

    shown = 0
    for item in active:
        if shown >= 3:  # ADHD cap: max 3 items
            remaining = len(active) - shown
            lines.append(f"  … {remaining} more active item(s)")
            break
        short = short_id(item.get("id", ""))
        _raw_title = item.get("title") or "Unknown"
        title = (_raw_title[:54] + "…") if len(_raw_title) > 55 else _raw_title
        role = item.get("role", "")
        lines.append(f"  ▸ [{short}] {title}  ({role})")
        shown += 1

    if blocked:
        lines.append(f"  ⛔ {len(blocked)} blocked")
    if stalled:
        lines.append(f"  ⚠️  {len(stalled)} stalled")

    lines.append("▹ /dx:context <id> for gates · get_context() to refresh")
    return "\n".join(lines)
