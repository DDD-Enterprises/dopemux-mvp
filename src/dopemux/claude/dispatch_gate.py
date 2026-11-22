"""
Advisory client for the optional external Dispatch desk gate.

Runs ``gate.py check`` and maps its exit code to a typed result. The gate is
an external tool: when it is absent nothing runs. This module never raises
from ``check`` and never passes ``--require-approval``.

Identity check: before running, ``gate.py`` and ``ledger.py`` are read as
bytes from the gate's tools/ directory (size-capped) and compared with pinned
SHA-256 digests. Any read error, missing file, oversize file or mismatch gives
UNKNOWN "gate identity unverified" and nothing runs. Only the verified bytes
are executed: they are written to a private temp dir (removed afterwards) and
run from there, so a file swapped on disk after verification is not executed.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

GO = "GO"
PAUSE_REQUESTED = "PAUSE_REQUESTED"
UNAPPROVED = "UNAPPROVED"
NOT_INSTALLED = "NOT_INSTALLED"
UNKNOWN = "UNKNOWN"

# SHA-256 of the helper files at dispatch-desk commit 84bff89.
_PINNED = {
    "gate.py": (
        "d6d13111779ab4058f86a4afdce4ca21c309136039ee89df43c08ebfe41dd386"
    ),
    "ledger.py": (
        "2fec110186e6dfded71001cec2eb74e2aff84f1011623d4a812fe19c961c65fd"
    ),
}
_MAX_HELPER_BYTES = 256 * 1024
_UNVERIFIED = "gate identity unverified"

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


def _read_verified(gate: Path) -> Optional[dict]:
    """Return {name: bytes} when every pinned file matches, else None."""
    files = {}
    try:
        for name, digest in _PINNED.items():
            path = gate.parent / name
            with open(path, "rb") as f:
                data = f.read(_MAX_HELPER_BYTES + 1)
            if len(data) > _MAX_HELPER_BYTES:
                return None
            if hashlib.sha256(data).hexdigest() != digest:
                return None
            files[name] = data
    except OSError:
        return None
    return files


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
        files = _read_verified(gate)
        if files is None:
            return GateResult(UNKNOWN, _UNVERIFIED)
        project = resolve_project(root, timeout)
        if project is None:
            return GateResult(UNKNOWN, "project key unresolved")
        tmp = tempfile.mkdtemp(prefix="dopemux-gate-")
        try:
            for name, data in files.items():
                with open(os.path.join(tmp, name), "wb") as f:
                    f.write(data)
            script = os.path.join(tmp, "gate.py")
            return _run(script, project, by, task, timeout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    except subprocess.TimeoutExpired:
        return GateResult(UNKNOWN, "gate timed out")
    except Exception as exc:  # fail open: the gate is advisory
        return GateResult(UNKNOWN, f"gate error: {type(exc).__name__}")


def _run(
    script: str, project: str, by: str, task: Optional[str], timeout: float
) -> GateResult:
    argv = [
        sys.executable or "python3",
        "-I",
        script,
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
