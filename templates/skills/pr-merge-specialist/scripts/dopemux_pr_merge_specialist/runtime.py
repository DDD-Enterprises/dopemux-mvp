from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def run_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def shell_join(cmd: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def contains_marker(text: str, markers: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def dry_run_result(cmd: Sequence[str]) -> CommandResult:
    return CommandResult(list(cmd), 0, "", "")


def execute_or_dry_run(
    cmd: Sequence[str],
    *,
    execute: bool,
    cwd: Optional[Path],
    commands_log: Path,
    timeout_seconds: int = 600,
) -> CommandResult:
    result = (
        run_command(cmd, cwd=cwd, timeout_seconds=timeout_seconds)
        if execute
        else dry_run_result(cmd)
    )
    append_command_log(commands_log, result, dry_run=not execute)
    return result


def fingerprint_payload(payload: Any) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def fingerprint_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def snapshot_environment(repo_root: Path) -> Dict[str, Any]:
    return {
        "cwd": str(repo_root),
        "python": os.environ.get("PYENV_VERSION")
        or os.environ.get("VIRTUAL_ENV")
        or "system",
        "platform": os.uname().sysname if hasattr(os, "uname") else os.name,
        "pid": os.getpid(),
    }
