"""Utility helpers for interacting with tmux from Dopemux mobile commands."""

from __future__ import annotations

from dataclasses import dataclass
import shlex
import subprocess
from typing import Dict, Iterable, List


class TmuxError(RuntimeError):
    """Raised when tmux operations fail."""


@dataclass
class TmuxPane:
    """Simplified view of a tmux pane."""

    pane_id: str
    title: str
    command: str
    window: str
    active: bool
    path: str

    @property
    def label(self) -> str:
        return self.title or self.window or self.pane_id


def _run_tmux(args: Iterable[str], capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run a tmux command and return the completed process."""

    proc = subprocess.run(
        ["tmux", *args],
        check=False,
        text=True,
        capture_output=capture_output,
    )
    if proc.returncode != 0:
        raise TmuxError(proc.stderr.strip() or proc.stdout.strip() or "tmux command failed")
    return proc


def list_windows() -> List[str]:
    """Return the list of tmux window names."""

    proc = _run_tmux(["list-windows", "-F", "#{window_name}"], capture_output=True)
    output = proc.stdout.strip()
    if not output:
        return []
    return output.splitlines()


def list_panes(all_sessions: bool = True) -> List[TmuxPane]:
    """Return panes with metadata."""

    args = ["list-panes", "-F", "#{pane_id}|#{pane_title}|#{pane_current_command}|#{window_name}|#{pane_active}|#{pane_current_path}"]
    if all_sessions:
        args.insert(1, "-a")

    proc = _run_tmux(args, capture_output=True)
    panes: List[TmuxPane] = []
    for line in proc.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("|", 5)
        if len(parts) != 6:
            continue
        pane_id, title, command, window, active, path = parts
        panes.append(
            TmuxPane(
                pane_id=pane_id.strip(),
                title=title.strip(),
                command=command.strip(),
                window=window.strip(),
                active=active.strip() == "1",
                path=path.strip(),
            )
        )
    return panes


def new_window(window_name: str, command: str) -> str:
    """Create a new tmux window running command and return the pane id."""

    proc = _run_tmux(
        [
            "new-window",
            "-d",
            "-P",
            "-F",
            "#{pane_id}",
            "-n",
            window_name,
            command,
        ],
        capture_output=True,
    )
    return proc.stdout.strip()


def split_window(target: str, command: str, vertical: bool = False) -> str:
    """Split an existing window and run command, returning pane id."""

    split_flag = "-v" if vertical else "-h"
    proc = _run_tmux(
        [
            "split-window",
            split_flag,
            "-d",
            "-P",
            "-F",
            "#{pane_id}",
            "-t",
            target,
            command,
        ],
        capture_output=True,
    )
    return proc.stdout.strip()


def set_layout(window_name: str, layout: str = "tiled") -> None:
    """Apply layout to a tmux window."""

    _run_tmux(["select-layout", "-t", window_name, layout])


def set_pane_title(pane_id: str, title: str) -> None:
    """Set the title of a tmux pane."""

    _run_tmux(["select-pane", "-t", pane_id, "-T", title])


def send_interrupt(pane_id: str) -> None:
    """Send Ctrl-C to a tmux pane."""

    _run_tmux(["send-keys", "-t", pane_id, "C-c"])


def kill_pane(pane_id: str) -> None:
    """Kill a tmux pane."""

    _run_tmux(["kill-pane", "-t", pane_id])


def build_env_command(command: str, env: Dict[str, str]) -> str:
    """Return command prefixed with environment variables."""

    if not env:
        return command
    assignments = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
    return f"{assignments} {command}"


def display_popup(command: str, width: str = "80%", height: str = "85%") -> None:
    """Launch a tmux popup running the given command."""

    _run_tmux([
        "display-popup",
        "-E",
        "-w",
        width,
        "-h",
        height,
        command,
    ])
