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


def run_command(
    cmd: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: int = 600,
) -> CommandResult:
    try:
        completed = subprocess.run(
            list(cmd),
            cwd=str(cwd) if cwd else None,
            env=None if env is None else {**os.environ, **env},
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        return CommandResult(list(cmd), completed.returncode, completed.stdout, completed.stderr, False)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            list(cmd),
            124,
            exc.stdout or "",
            (exc.stderr or "") + f"\nCommand timed out after {timeout_seconds} seconds.",
            True,
        )


def json_loads_or_empty(raw: str) -> Any:
    if not raw.strip():
        return {}
    return json.loads(raw)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    path.write_text(text, encoding="utf-8")


def append_command_log(path: Path, result: CommandResult, *, dry_run: bool = False) -> None:
    ensure_parent(path)
    mode = "a" if path.exists() else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(f"$ {shell_join(result.command)}\n")
        handle.write(f"exit={result.returncode}")
        if dry_run:
            handle.write(" (dry-run)")
        if result.timed_out:
            handle.write(" (timed-out)")
        handle.write("\n")
        if result.stdout:
            handle.write("--- stdout ---\n")
            handle.write(result.stdout.rstrip() + "\n")
        if result.stderr:
            handle.write("--- stderr ---\n")
            handle.write(result.stderr.rstrip() + "\n")
        handle.write("\n")


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
    result = run_command(cmd, cwd=cwd, timeout_seconds=timeout_seconds) if execute else dry_run_result(cmd)
    append_command_log(commands_log, result, dry_run=not execute)
    return result


def fingerprint_payload(payload: Any) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


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
        "python": os.environ.get("PYENV_VERSION") or os.environ.get("VIRTUAL_ENV") or "system",
        "platform": os.uname().sysname if hasattr(os, "uname") else os.name,
        "pid": os.getpid(),
    }
