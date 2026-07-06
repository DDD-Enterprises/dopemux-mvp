"""Session-level untracked-work surfacing (lite probe).

Detects uncommitted work in the current worktree and (a) returns a gentle
one-line advisory for session-start surfaces, (b) emits a promotable
``work.untracked_detected`` capture event so the chronicle records it.

This intentionally does NOT duplicate Serena F001 "Untracked Work Detection"
(services/serena/untracked_work_*.py — the canonical detect → remind →
convert → auto-close engine with ConPort-persisted state, being exposed via
MCP in PR #1007). This module is the always-on, zero-dependency probe at the
live session entry points (``dopemux start``, SessionStart hook); F001 owns
the actionable lifecycle, including ``work.untracked_converted``.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Optional

from .uncommitted_detector import ChangesSummary, UncommittedChangeDetector

logger = logging.getLogger(__name__)

PROBE_SOURCE = "dopemux.untracked_work"


def check_untracked_work(workspace_path: str) -> Optional[ChangesSummary]:
    """Return a ChangesSummary when uncommitted work exists, else None.

    None also covers: not a git repo, clean worktree, and detection failure
    (detection failure is surfaced by main-worktree protection; this probe
    is advisory and stays quiet rather than guessing).
    """
    try:
        detector = UncommittedChangeDetector(workspace_path)
    except ValueError:
        return None
    changes = detector.check_changes()
    if changes.detection_failed or not changes.has_changes:
        return None
    return changes


def current_branch(workspace_path: str) -> Optional[str]:
    """Best-effort current branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = result.stdout.strip()
        return branch or None
    except Exception:
        return None


def format_advisory(changes: ChangesSummary, branch: Optional[str]) -> str:
    """One-line, gentle advisory (no prompt — decision reduction)."""
    where = f" on [bold]{branch}[/bold]" if branch else ""
    return (
        f"📂 Untracked work{where}: {changes.format_summary()}. "
        "If this is task work, log it (e.g. `dopemux capture note`) so it isn't lost."
    )


def emit_untracked_detected(
    workspace_path: str,
    changes: ChangesSummary,
    branch: Optional[str],
    *,
    source_probe: str,
    session_id: Optional[str] = None,
) -> bool:
    """Best-effort promotable capture event; never raises."""
    try:
        from .memory.capture_client import try_emit_promotable_capture_event
    except Exception:  # pragma: no cover - capture stack unavailable
        return False
    result = try_emit_promotable_capture_event(
        "work.untracked_detected",
        {
            "branch": branch or "",
            "workspace_path": workspace_path,
            "staged_count": changes.staged_count,
            "unstaged_count": changes.unstaged_count,
            "untracked_count": changes.untracked_count,
            "total_files": changes.total_files,
            "source_probe": source_probe,
        },
        source=PROBE_SOURCE,
        session_id=session_id,
    )
    return result is not None


def probe_untracked_work(
    workspace_path: str,
    *,
    source_probe: str,
    session_id: Optional[str] = None,
) -> Optional[str]:
    """Full probe: detect, emit capture event, return advisory line (or None)."""
    changes = check_untracked_work(workspace_path)
    if changes is None:
        return None
    branch = current_branch(workspace_path)
    emit_untracked_detected(
        workspace_path,
        changes,
        branch,
        source_probe=source_probe,
        session_id=session_id,
    )
    return format_advisory(changes, branch)
