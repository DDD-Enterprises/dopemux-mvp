"""
Proof-tracking guard for PostToolUse.

When a Write/Edit lands under proof/ and the basename is in TRACK_TIER,
checks whether the file is gitignored-but-untracked and emits the force-add
advisory so the operator doesn't complete a packet with untracked proof.

All functions are pure and never raise; hook failures must not block work.
Reference: TP-DMX-PROOF-TRACKING-POLICY-001
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

TRACK_TIER = frozenset({
    "PROOF.json", "SUMMARY.md", "AUDIT.md", "MERGE_READINESS.json",
    "VALIDATION.md", "CMD_SUMMARY.md", "MODEL_ROUTING.json", "MANIFEST.json",
})  # source: TP-DMX-PROOF-TRACKING-POLICY-001 TRACK table

_CACHE_FILENAME = ".proof-tracking-nudge.json"


def _load_cache(project_root: Path) -> dict:
    try:
        return json.loads((project_root / ".claude" / _CACHE_FILENAME).read_text())
    except Exception:
        return {}


def _save_cache(project_root: Path, cache: dict) -> None:
    try:
        cache_path = project_root / ".claude" / _CACHE_FILENAME
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache))
    except Exception:
        pass


def on_proof_write(
    project_root: Path,
    file_path: str,
    session_id: str | None,
) -> str | None:
    """When a Write/Edit lands under proof/ and basename ∈ TRACK_TIER:
      1. git check-ignore -q <path>  (exit 0 = ignored)
      2. git ls-files --error-unmatch <path>  (exit 0 = already tracked)
      If ignored AND not tracked → return the force-track advisory.
    Cooldown once per (session, path). Never raises; None on any git error."""
    try:
        # Fast-path: skip anything that can't possibly be under proof/
        if "proof" not in file_path:
            return None

        # Resolve repo-relative parts
        path = Path(file_path)
        try:
            rel = path.relative_to(project_root)
        except ValueError:
            rel = path

        parts = rel.parts
        if not parts or parts[0] != "proof":
            return None
        if rel.name not in TRACK_TIER:
            return None

        # Cooldown: once per (session, path)
        session_key = session_id or "no-session"
        cache_key = f"{session_key}:{file_path}"
        cache = _load_cache(project_root)
        if cache.get(cache_key):
            return None

        cwd = str(project_root)

        # Is the file gitignored?
        ignore_result = subprocess.run(
            ["git", "check-ignore", "-q", file_path],
            cwd=cwd,
            capture_output=True,
            timeout=1,
        )
        if ignore_result.returncode != 0:
            # Not ignored — no advisory needed
            return None

        # Is it already tracked despite the ignore (force-added previously)?
        tracked_result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", file_path],
            cwd=cwd,
            capture_output=True,
            timeout=1,
        )
        if tracked_result.returncode == 0:
            return None

        # Ignored and untracked → emit advisory
        cache[cache_key] = True
        _save_cache(project_root, cache)

        try:
            rel_for_git = str(path.relative_to(project_root))
        except ValueError:
            rel_for_git = file_path

        return (
            f"📌 {rel_for_git} is a TRACK-tier proof artifact but is gitignored by the "
            f"`proof/*` safety net. Policy (TP-DMX-PROOF-TRACKING-POLICY-001): sanitized proof "
            f"MUST be force-tracked before the packet completes — "
            f"`git add -f {rel_for_git}`. "
            f"Un-committed proof for a completed packet is a red-line stop condition."
        )
    except Exception:
        return None
