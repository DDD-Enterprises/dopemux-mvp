"""SessionStart untracked-work probe (H5).

Surfaces uncommitted work with a one-line advisory at Claude session start
and emits a promotable ``work.untracked_detected`` capture event so the
chronicle records it. Delegates detection/formatting to
``dopemux.untracked_work`` (lite probe — Serena F001 owns the actionable
detect→remind→convert lifecycle).

Fail-open: any failure returns None and never blocks the session. Cooldown:
fires at most once per session id (fallback: 30-minute time cooldown when no
session id is available), cached under ``.claude/``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_CACHE_FILENAME = ".untracked-work-probe-cache.json"
_FALLBACK_COOLDOWN_MIN = 30


def _cache_path(project_root: Path) -> Path:
    return project_root / ".claude" / _CACHE_FILENAME


def _already_probed(project_root: Path, session_id: Optional[str]) -> bool:
    try:
        data = json.loads(_cache_path(project_root).read_text())
    except Exception:
        return False
    if session_id and data.get("session_id") == session_id:
        return True
    if not session_id:
        ts = data.get("written_at", "")
        try:
            age_min = (
                datetime.now(timezone.utc) - datetime.fromisoformat(ts)
            ).total_seconds() / 60
            return age_min < _FALLBACK_COOLDOWN_MIN
        except Exception:
            return False
    return False


def _save_probe_marker(project_root: Path, session_id: Optional[str]) -> None:
    try:
        path = _cache_path(project_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "session_id": session_id or "",
                    "written_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        )
    except Exception:
        pass


def emit_untracked_work_advisory(
    project_root: Path, session_id: Optional[str] = None
) -> Optional[str]:
    """Return an advisory line for SessionStart context, or None.

    Never raises.
    """
    try:
        root = Path(project_root)
        if _already_probed(root, session_id):
            return None
        from dopemux.untracked_work import probe_untracked_work

        advisory = probe_untracked_work(
            str(root), source_probe="session_start", session_id=session_id
        )
        _save_probe_marker(root, session_id)
        return advisory
    except Exception:
        return None
