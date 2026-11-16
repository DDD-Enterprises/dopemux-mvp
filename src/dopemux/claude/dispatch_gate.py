"""
Advisory client for the optional external Dispatch desk gate.

Runs ``gate.py check`` and maps its exit code to a typed result. The gate is
an external tool: when it is absent nothing runs. This module never raises
from ``check`` and never passes ``--require-approval``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

GO = "GO"
PAUSE_REQUESTED = "PAUSE_REQUESTED"
UNAPPROVED = "UNAPPROVED"
NOT_INSTALLED = "NOT_INSTALLED"
UNKNOWN = "UNKNOWN"

_EXIT_STATES = {0: GO, 3: PAUSE_REQUESTED, 4: UNAPPROVED}


@dataclass(frozen=True)
class GateResult:
    """Gate state plus the gate's one-line message (may be empty)."""

    state: str
    message: str = ""


def _clean(text: str) -> str:
    """First line only, printable characters only, at most 200 chars."""
    lines = (text or "").strip().splitlines()
    first = lines[0] if lines else ""
    return "".join(c for c in first if c.isprintable()).strip()[:200]


def resolve_project(root: "str | Path", timeout: float = 2.0) -> Optional[str]:
    """Return the MAIN checkout folder name, or None when git cannot say."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        common = proc.stdout.strip()
        if proc.returncode == 0 and common:
            return Path(common).parent.name or None
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def resolve_gate() -> Optional[Path]:
    """Return the gate script path, or None when it is not installed."""
    home = os.environ.get("DISPATCH_DESK_HOME")
    if home:
        base = Path(home).expanduser()
    else:
        base = Path.home() / "code" / "dispatch-desk"
    gate = base / "tools" / "gate.py"
    return gate if gate.is_file() else None


def check(
    root: "str | Path",
    by: str,
    task: Optional[str] = None,
    timeout: float = 2.0,
) -> GateResult:
    """Ask the gate whether work may proceed. Never raises."""
    try:
        gate = resolve_gate()
        if gate is None:
            return GateResult(NOT_INSTALLED)
        project = resolve_project(root, timeout)
        if project is None:
            return GateResult(UNKNOWN, "project key unresolved")
        argv = [
            sys.executable or "python3",
            "-I",
            str(gate),
            "check",
            "--project",
            project,
        ]
        if task:
            argv += ["--task", task]
        argv += ["--by", by]
        run_kw = {"capture_output": True, "text": True, "timeout": timeout}
        proc = subprocess.run(argv, **run_kw)
        message = _clean(proc.stdout or proc.stderr or "")
        return GateResult(_EXIT_STATES.get(proc.returncode, UNKNOWN), message)
    except subprocess.TimeoutExpired:
        return GateResult(UNKNOWN, "gate timed out")
    except Exception as exc:  # fail open: the gate is advisory
        return GateResult(UNKNOWN, f"gate error: {type(exc).__name__}")
