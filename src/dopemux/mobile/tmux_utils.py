"""Utility helpers for interacting with tmux from Dopemux commands."""

from __future__ import annotations

from dataclasses import dataclass
import shlex
import subprocess
from typing import Dict, Iterable, List, Optional


class TmuxError(RuntimeError):
    """Raised when tmux operations fail."""


@dataclass
class TmuxPane:
    """Simplified view of a tmux pane."""

    pane_id: str
    title: str
    command: str
    window: str
    session: str
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
        stderr = proc.stderr.strip() if proc.stderr else ""
        stdout = proc.stdout.strip() if proc.stdout else ""
        message = stderr or stdout or "tmux command failed"
        raise TmuxError(message)
    return proc


def session_exists(session: str) -> bool:
    """Return True if tmux session exists."""

    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def list_sessions() -> List[str]:
    """List tmux sessions by name."""

    proc = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise TmuxError(proc.stderr.strip() or proc.stdout.strip() or "Failed to list tmux sessions")
    output = proc.stdout.strip()
    return output.splitlines() if output else []


def create_session(
    session: str,
    *,
    start_directory: Optional[str] = None,
    window_name: str = "main",
    command: Optional[str] = None,
) -> None:
    """Create a detached tmux session."""

    args: List[str] = [
        "new-session",
        "-d",
        "-s",
        session,
        "-n",
        window_name,
    ]
    if start_directory:
        args.extend(["-c", start_directory])
    if command:
        args.append(command)

    proc = _run_tmux(args, capture_output=True)
    if proc.returncode != 0:
        raise TmuxError(proc.stderr.strip() or proc.stdout.strip() or "Failed to create tmux session")

    try:
        _run_tmux(["set-option", "-t", session, "exit-empty", "off"], capture_output=True)
    except Exception as e:
        pass


        logger.error(f"Error: {e}")
def list_windows(session: Optional[str] = None) -> List[str]:
    """Return the list of tmux window names."""

    args = ["list-windows", "-F", "#{window_name}"]
    if session:
        args.extend(["-t", session])
    proc = _run_tmux(args, capture_output=True)
    output = proc.stdout.strip()
    if not output:
        return []
    return output.splitlines()


def select_window(session: str, window: str) -> None:
    """Focus a specific tmux window inside a session."""

    target = f"{session}:{window}" if ":" not in window else window
    _run_tmux(["select-window", "-t", target])


def list_panes(all_sessions: bool = True) -> List[TmuxPane]:
    """Return panes with metadata."""

    args: List[str] = [
        "list-panes",
        "-F",
        "#{pane_id}|#{pane_title}|#{pane_current_command}|#{window_name}|#{session_name}|#{pane_active}|#{pane_current_path}",
    ]
    if all_sessions:
        args.insert(1, "-a")

    proc = _run_tmux(args, capture_output=True)
    panes: List[TmuxPane] = []
    for line in proc.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("|", 6)
        if len(parts) != 7:
            continue
        pane_id, title, command, window, session, active, path = parts
        panes.append(
            TmuxPane(
                pane_id=pane_id.strip(),
                title=title.strip(),
                command=command.strip(),
                window=window.strip(),
                session=session.strip(),
                active=active.strip() == "1",
                path=path.strip(),
            )
        )
    return panes


def new_window(
    window_name: str,
    command: str,
    *,
    session: Optional[str] = None,
    start_directory: Optional[str] = None,
    attach: bool = False,
    environment: Optional[Dict[str, str]] = None,
) -> str:
    """Create a new tmux window running command and return the pane id."""

    args: List[str] = [
        "new-window",
        "-P",
        "-F",
        "#{pane_id}",
        "-n",
        window_name,
    ]
    if not attach:
        args.append("-d")
    if session:
        args.extend(["-t", f"{session}:"])
    if start_directory:
        args.extend(["-c", start_directory])

    full_command = build_env_command(command, environment or {})
    args.append(full_command)

    proc = _run_tmux(args, capture_output=True)
    return proc.stdout.strip()


def split_window(
    target: Optional[str],
    command: str,
    *,
    vertical: bool = False,
    start_directory: Optional[str] = None,
    attach: bool = False,
    environment: Optional[Dict[str, str]] = None,
    session: Optional[str] = None,
    percent: Optional[int] = None,
) -> str:
    """Split an existing window and run command, returning pane id."""

    split_flag = "-v" if vertical else "-h"
    args: List[str] = [
        "split-window",
        split_flag,
        "-P",
        "-F",
        "#{pane_id}",
    ]
    if percent is not None:
        args.extend(["-p", str(percent)])
    if not attach:
        args.append("-d")
    if target:
        pane_target = target
        if (
            session
            and ":" not in pane_target
            and (not pane_target or pane_target[0] not in {"%", "@"})
        ):
            pane_target = f"{session}:{pane_target}"
        args.extend(["-t", pane_target])
    if start_directory:
        args.extend(["-c", start_directory])

    full_command = build_env_command(command, environment or {})
    args.append(full_command)

    proc = _run_tmux(args, capture_output=True)
    return proc.stdout.strip()


def rename_window(session: str, window: str, new_name: str) -> None:
    """Rename a tmux window. Accepts window index/name or pane id like %6."""
    target_window = window
    if window.startswith("%"):
        try:
            proc = _run_tmux(["display-message", "-p", "-t", window, "#{window_index}"], capture_output=True)
            target_window = proc.stdout.strip() or "0"
        except TmuxError:
            target_window = "0"
    target = f"{session}:{target_window}"
    _run_tmux(["rename-window", "-t", target, new_name])


def set_layout(window_name: str, layout: str = "tiled") -> None:
    """Apply layout to a tmux window."""

    _run_tmux(["select-layout", "-t", window_name, layout])


def set_pane_title(pane_id: str, title: str) -> None:
    """Set the title of a tmux pane."""

    _run_tmux(["select-pane", "-t", pane_id, "-T", title])


def set_pane_style(pane_id: str, style: str) -> None:
    """Apply style (fg/bg) to a tmux pane."""

    _run_tmux(["select-pane", "-t", pane_id, "-P", style])


def set_pane_border_style(pane_id: str, style: str) -> None:
    """Apply a custom border style to a tmux pane."""

    if not style:
        return
    _run_tmux(["select-pane", "-t", pane_id, "-P", f"border-style {style}"])


def set_session_option(session: str, option: str, value: str) -> None:
    """Set a tmux session-scoped option."""

    _run_tmux(["set-option", "-t", session, option, value])


def set_global_option(option: str, value: str) -> None:
    """Set a global tmux option."""

    _run_tmux(["set-option", "-g", option, value])


def set_environment(session: str, key: str, value: str) -> None:
    """Set a tmux session environment variable."""

    _run_tmux(["set-environment", "-t", session, key, value])


def enable_pane_titles(session: str) -> None:
    """Enable pane title display in borders for a tmux session."""

    _run_tmux([
        "set-option", "-t", session,
        "pane-border-format",
        "#[default]"
        "#{?pane_active,#[bold],#[dim]}"
        "#[bg=#{@dopemux_title_bg:-#1e1e2e}]"
        "#[fg=#{@dopemux_title_fg:-#cdd6f4}] "
        "#{pane_title} "
        "#[default]"
    ])
    _run_tmux(["set-option", "-t", session, "pane-border-status", "top"])


def capture_pane(pane_id: str, lines: int = 100) -> str:
    """Capture the last N lines from a tmux pane."""
    try:
        result = _run_tmux([
            "capture-pane", "-t", pane_id, "-p", "-S", f"-{lines}"
        ], capture_output=True)
        return result.stdout
    except TmuxError:
        return ""


def get_pane_content(pane_id: str, start_line: int = 0, end_line: int = -1) -> str:
    """Get specific lines from a tmux pane buffer."""
    try:
        if end_line == -1:
            result = _run_tmux([
                "capture-pane", "-t", pane_id, "-p", "-S", str(start_line)
            ], capture_output=True)
        else:
            result = _run_tmux([
                "capture-pane", "-t", pane_id, "-p",
                "-S", str(start_line), "-E", str(end_line)
            ], capture_output=True)
        return result.stdout
    except TmuxError:
        return ""


def send_interrupt(pane_id: str) -> None:
    """Send Ctrl-C to a tmux pane."""

    _run_tmux(["send-keys", "-t", pane_id, "C-c"])


def kill_pane(pane_id: str) -> None:
    """Kill a tmux pane."""

    _run_tmux(["kill-pane", "-t", pane_id])


def kill_session(session: str) -> None:
    """Kill an entire tmux session."""

    _run_tmux(["kill-session", "-t", session])


def kill_window(session: str, window: str) -> None:
    """Kill a tmux window."""

    target = f"{session}:{window}"
    _run_tmux(["kill-window", "-t", target])


def build_env_command(command: str, env: Dict[str, str]) -> str:
    """Return command prefixed with environment variables."""

    if not env:
        return command
    assignments = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
    return f"{assignments} {command}"


def attach_session(session: str) -> None:
    """Attach to an existing tmux session."""

    subprocess.run(["tmux", "attach-session", "-t", session])


def switch_client(session: str) -> None:
    """Switch current tmux client to another session."""

    subprocess.run(["tmux", "switch-client", "-t", session])


def send_literal_text(pane_id: str, text: str, *, enter: bool = False) -> None:
    """Send literal text to a tmux pane."""

    if text:
        _run_tmux(["send-keys", "-t", pane_id, "-l", text])
    if enter:
        _run_tmux(["send-keys", "-t", pane_id, "Enter"])


def send_key(pane_id: str, key: str) -> None:
    """Send a single tmux key (e.g., 'C-c', 'Enter')."""

    _run_tmux(["send-keys", "-t", pane_id, key])


def focus_pane(pane_id: str) -> None:
    """Select (focus) a pane."""

    _run_tmux(["select-pane", "-t", pane_id])


def capture_pane_output(pane_id: str, *, lines: Optional[int] = None) -> str:
    """Capture output from a pane."""

    args: List[str] = ["capture-pane", "-t", pane_id, "-p"]
    if lines is not None:
        args.extend(["-S", f"-{max(lines, 0)}"])
    proc = _run_tmux(args, capture_output=True)
    return proc.stdout


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
