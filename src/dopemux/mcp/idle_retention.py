"""Selected-key, worktree-local idle retention; uncertainty never authorizes reap."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

KEY = "DOPEMUX_MCP_RETAIN_IDLE"
ENVRC = ".envrc.dopemux-mcp"
_DECLARATION = re.compile(
    rf"^\s*(?:export\s+)?{KEY}\s*=\s*"
    r"(?:([\"'])(true|false)\1|(true|false))(?:\s+#.*)?\s*$"
)


class IdleRetentionError(ValueError):
    """Only a static reason; policy values/file contents are never included."""


def read_retention_policy(path: Path) -> Optional[bool]:
    """Read only this literal key; no shell evaluation, identity or ambient fallback."""
    selected = []
    total = 0
    try:
        if path.is_symlink():
            raise IdleRetentionError("idle_retention_invalid")
        with path.open(encoding="utf-8") as stream:
            for raw in stream:
                total += len(raw)
                if total > (1 << 20):
                    raise IdleRetentionError("idle_retention_invalid")
                if KEY not in raw or raw.lstrip().startswith("#"):
                    continue
                lexer = shlex.shlex(raw, posix=True, punctuation_chars=";|&()")
                lexer.whitespace_split = True
                tokens = list(lexer)
                if any(token == KEY or token.startswith(KEY + "=") for token in tokens):
                    selected.append(raw.rstrip("\r\n"))
                elif any(KEY in token for token in tokens):
                    # Ignore an unrelated literal assignment containing the key
                    # as data. Commands, interpolation and compound lines can
                    # affect policy and must never be treated as an absent key.
                    assignments = tokens[1:] if tokens[:1] == ["export"] else tokens
                    if not assignments or not all(
                        re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token)
                        and "$" not in token
                        and "`" not in token
                        for token in assignments
                    ):
                        raise IdleRetentionError("idle_retention_invalid")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError):
        raise IdleRetentionError("idle_retention_unreadable") from None
    except ValueError:
        raise IdleRetentionError("idle_retention_invalid") from None
    if not selected:
        return None
    match = _DECLARATION.fullmatch(selected[0]) if len(selected) == 1 else None
    if match is None:
        raise IdleRetentionError("idle_retention_invalid")
    return (match.group(2) or match.group(3)) == "true"


@dataclass(frozen=True)
class IdleRetention:
    hold_idle: bool
    reason: str = ""


def idle_retention(root: Path) -> IdleRetention:
    """A scoped idle hold; callers decide missing-worktree cleanup first."""
    try:
        enabled = read_retention_policy(root / ENVRC)
    except IdleRetentionError as exc:
        return IdleRetention(True, str(exc))
    if not enabled:
        return IdleRetention(False)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if (
            result.returncode != 0
            or Path(result.stdout.strip()).resolve() != root.resolve()
        ):
            return IdleRetention(True, "idle_retention_unbound")
    except (OSError, ValueError, subprocess.SubprocessError):
        return IdleRetention(True, "idle_retention_unbound")
    return IdleRetention(True, "retained_idle")
