"""Fixed read-only git state.

Runs ONLY a hardcoded allowlist of read-only git commands with a fixed argv
list (``shell=False``), ``cwd`` set to an already-resolved workspace, and no
interpolation of caller-supplied input. There is no code path that accepts a
git subcommand, flag, or path from a caller — the only variable is the resolved
workspace directory chosen by the resolver.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

# Internal keys → fixed argv. Keys are never caller-supplied.
_ALLOWED: dict[str, list[str]] = {
    "head": ["git", "rev-parse", "HEAD"],
    "branch": ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    "status": ["git", "status", "--porcelain"],
}

_TIMEOUT_SECONDS = 10


def _run(key: str, cwd: Path) -> Optional[str]:
    argv = _ALLOWED[key]  # KeyError is a programming error, not caller input
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, shell=False, no caller input
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def repo_state(workspace: Path) -> dict:
    """Return ``{branch, head_sha, dirty}``; any field is ``None`` if unavailable."""
    head = _run("head", workspace)
    branch = _run("branch", workspace)
    status = _run("status", workspace)
    dirty: Optional[bool] = None if status is None else bool(status.strip())
    return {"branch": branch, "head_sha": head, "dirty": dirty}
