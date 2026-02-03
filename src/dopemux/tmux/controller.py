"""High-level tmux controller for Dopemux."""

from __future__ import annotations

import re
import shlex
import subprocess
import time
import warnings
from dataclasses import dataclass
import os
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ..config.manager import (
    ConfigManager,
    TmuxControllerConfig,
    TmuxPresetConfig,
    TmuxPresetConfig,
)
from .common import PaneInfo, TmuxError

try:  # pragma: no cover - optional dependency
    import libtmux  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    libtmux = None  # type: ignore


# PaneInfo moved to .common


@dataclass
class PaneSnapshot:
    pane: PaneInfo
    content: str


class BaseTmuxBackend:
    """Abstract backend for interacting with tmux."""

    def list_panes(self) -> List[PaneInfo]:
        raise NotImplementedError

    def split_window(
        self,
        *,
        target: str,
        command: str,
        vertical: bool,
        start_directory: Optional[str],
        focus: bool,
        environment: Dict[str, str],
        session: Optional[str],
        percent: Optional[int] = None,
    ) -> str:
        raise NotImplementedError

    def switch_client(self, target: str) -> None:
        raise NotImplementedError

    def attach_session(self, target: str) -> None:
        raise NotImplementedError

    def new_window(
        self,
        *,
        session: str,
        window_name: str,
        command: str,
        start_directory: Optional[str],
        attach: bool,
        environment: Dict[str, str],
    ) -> str:
        raise NotImplementedError

    def kill_window(self, session: str, window_name: str) -> None:
        raise NotImplementedError

    def session_exists(self, session: str) -> bool:
        raise NotImplementedError

    def create_session(self, session: str, start_directory: Optional[str] = None, window_name: Optional[str] = None) -> None:
        raise NotImplementedError

    def rename_window(self, session: str, window_id: str, new_name: str) -> None:
        raise NotImplementedError

    def select_window(self, session: str, window_target: str) -> None:
        raise NotImplementedError

    def rename_pane(self, pane_id: str, title: str) -> None:
        raise NotImplementedError

    def focus_pane(self, pane_id: str) -> None:
        raise NotImplementedError

    def capture_pane(self, pane_id: str, lines: Optional[int]) -> str:
        raise NotImplementedError

    def send_literal(self, pane_id: str, text: str, enter: bool) -> None:
        raise NotImplementedError

    def send_key(self, pane_id: str, key: str) -> None:
        raise NotImplementedError

    def get_pane(self, pane_id: str) -> Optional[PaneInfo]:
        raise NotImplementedError

    def kill_pane(self, pane_id: str) -> None:
        raise NotImplementedError

    def set_pane_style(self, pane_id: str, style: str) -> None:
        raise NotImplementedError

    def set_pane_border_style(self, pane_id: str, style: str) -> None:
        raise NotImplementedError

    def set_pane_title(self, pane_id: str, title: str) -> None:
        raise NotImplementedError

    def set_layout(self, window: str, layout: str) -> None:
        raise NotImplementedError

    def display_popup(self, command: str, width: str = "80%", height: str = "80%") -> None:
        raise NotImplementedError

    def set_environment(self, session: str, key: str, value: str) -> None:
        raise NotImplementedError

    def enable_pane_titles(self, session: str) -> None:
        raise NotImplementedError

    def kill_session(self, session: str) -> None:
        raise NotImplementedError

    def set_session_option(self, session: str, option: str, value: str) -> None:
        raise NotImplementedError

    def set_global_option(self, option: str, value: str) -> None:
        raise NotImplementedError



class CliTmuxBackend(BaseTmuxBackend):
    """Backend using direct tmux CLI invocations."""

    def _run_tmux(self, args: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
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

    def list_panes(self) -> List[PaneInfo]:
        args: List[str] = [
            "list-panes",
            "-a",
            "-F",
            "#{pane_id}|#{pane_title}|#{pane_current_command}|#{window_name}|#{session_name}|#{pane_active}|#{pane_current_path}",
        ]
        proc = self._run_tmux(args, capture_output=True)
        panes: List[PaneInfo] = []
        for line in proc.stdout.strip().splitlines():
             if not line:
                 continue
             parts = line.split("|", 6)
             if len(parts) != 7:
                 continue
             pane_id, title, command, window, session, active, path = parts
             panes.append(
                 PaneInfo(
                     pane_id=pane_id.strip(),
                     title=title.strip(),
                     command=command.strip(),
                     window=window.strip(),
                     session=session.strip(),
                     path=path.strip(),
                     active=active.strip() == "1",
                 )
             )
        return panes

    def split_window(
        self,
        *,
        target: str,
        command: str,
        vertical: bool,
        start_directory: Optional[str],
        focus: bool,
        environment: Dict[str, str],
        session: Optional[str],
        percent: Optional[int] = None,
    ) -> str:
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
        if not focus:
            args.append("-d")
        if target:
            # Logic from utils: handle sess:target
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

        full_command = self._build_env_command(command, environment or {})
        args.append(full_command)

        proc = self._run_tmux(args, capture_output=True)
        return proc.stdout.strip()

    def switch_client(self, target: str) -> None:
        subprocess.run(["tmux", "switch-client", "-t", target])

    def attach_session(self, target: str) -> None:
        subprocess.run(["tmux", "attach-session", "-t", target])

    def new_window(
        self,
        *,
        session: str,
        window_name: str,
        command: str,
        start_directory: Optional[str],
        attach: bool,
        environment: Dict[str, str],
    ) -> str:
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

        full_command = self._build_env_command(command, environment)
        args.append(full_command)

        proc = self._run_tmux(args, capture_output=True)
        return proc.stdout.strip()

    def kill_window(self, session: str, window_name: str) -> None:
        target = f"{session}:{window_name}"
        self._run_tmux(["kill-window", "-t", target])

    def session_exists(self, session: str) -> bool:
        proc = subprocess.run(
            ["tmux", "has-session", "-t", session],
            check=False,
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0

    def create_session(self, session: str, start_directory: Optional[str] = None, window_name: Optional[str] = None) -> None:
         args: List[str] = [
            "new-session",
            "-d",
            "-s",
            session,
            "-n",
            window_name or "main",
        ]
         if start_directory:
            args.extend(["-c", start_directory])
         
         self._run_tmux(args, capture_output=True)
         # Optional: turn off exit-empty
         try:
             self._run_tmux(["set-option", "-t", session, "exit-empty", "off"], capture_output=True)
         except Exception:
             pass

    def rename_window(self, session: str, window_id: str, new_name: str) -> None:
        target_window = window_id
        if window_id.startswith("%"):
             try:
                 proc = self._run_tmux(["display-message", "-p", "-t", window_id, "#{window_index}"], capture_output=True)
                 target_window = proc.stdout.strip() or "0"
             except TmuxError:
                 target_window = "0"
        target = f"{session}:{target_window}"
        self._run_tmux(["rename-window", "-t", target, new_name])

    def select_window(self, session: str, window_target: str) -> None:
        target = f"{session}:{window_target}" if ":" not in window_target else window_target
        self._run_tmux(["select-window", "-t", target])

    def rename_pane(self, pane_id: str, title: str) -> None:
        self.set_pane_title(pane_id, title)

    def focus_pane(self, pane_id: str) -> None:
        self._run_tmux(["select-pane", "-t", pane_id])

    def capture_pane(self, pane_id: str, lines: Optional[int]) -> str:
        args: List[str] = ["capture-pane", "-t", pane_id, "-p"]
        if lines is not None:
            args.extend(["-S", f"-{max(lines, 0)}"])
        try:
            proc = self._run_tmux(args, capture_output=True)
            return proc.stdout
        except TmuxError:
            return ""

    def send_literal(self, pane_id: str, text: str, enter: bool) -> None:
        if text:
            self._run_tmux(["send-keys", "-t", pane_id, "-l", text])
        if enter:
            self._run_tmux(["send-keys", "-t", pane_id, "Enter"])

    def send_key(self, pane_id: str, key: str) -> None:
         self._run_tmux(["send-keys", "-t", pane_id, key])

    def get_pane(self, pane_id: str) -> Optional[PaneInfo]:
        return next(
            (pane for pane in self.list_panes() if pane.pane_id == pane_id),
            None,
        )

    def kill_pane(self, pane_id: str) -> None:
         self._run_tmux(["kill-pane", "-t", pane_id])

    def set_pane_style(self, pane_id: str, style: str) -> None:
         self._run_tmux(["select-pane", "-t", pane_id, "-P", style])

    def set_pane_border_style(self, pane_id: str, style: str) -> None:
         if not style:
             return
         self._run_tmux(["select-pane", "-t", pane_id, "-P", f"border-style {style}"])

    def set_pane_title(self, pane_id: str, title: str) -> None:
         self._run_tmux(["select-pane", "-t", pane_id, "-T", title])

    def set_layout(self, window: str, layout: str) -> None:
         self._run_tmux(["select-layout", "-t", window, layout])

    def display_popup(self, command: str, width: str = "80%", height: str = "80%") -> None:
        self._run_tmux([
            "display-popup",
            "-E",
            "-w",
            width,
            "-h",
            height,
            command,
        ])

    def set_environment(self, session: str, key: str, value: str) -> None:
        self._run_tmux(["set-environment", "-t", session, key, value])

    def enable_pane_titles(self, session: str) -> None:
        self._run_tmux([
            "set-option", "-t", session,
            "pane-border-format",
            "#[default]"
            "#{?pane_active,#[bold],#[dim]}"
            "#[bg=#{@dopemux_title_bg:-#1e1e2e}]"
            "#[fg=#{@dopemux_title_fg:-#cdd6f4}] "
            "#{pane_title} "
            "#[default]"
        ])
        self._run_tmux(["set-option", "-t", session, "pane-border-status", "top"])

    def kill_session(self, session: str) -> None:
         self._run_tmux(["kill-session", "-t", session])

    def set_session_option(self, session: str, option: str, value: str) -> None:
         self._run_tmux(["set-option", "-t", session, option, value])
    
    def set_global_option(self, option: str, value: str) -> None:
         self._run_tmux(["set-option", "-g", option, value])

    
    def _build_env_command(self, command: str, env: Dict[str, str]) -> str:
        """Return command prefixed with environment variables."""
        if not env:
            return command
        assignments = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
        return f"{assignments} {command}"


class LibTmuxBackend(BaseTmuxBackend):  # pragma: no cover - depends on libtmux
    """Backend built on libtmux."""

    def __init__(self) -> None:
        if libtmux is None:  # pragma: no cover - defensive
            raise RuntimeError("libtmux is not available")
        self.server = libtmux.Server()  # type: ignore[attr-defined]

    def list_panes(self) -> List[PaneInfo]:
        panes: List[PaneInfo] = []
        for session in self.server.sessions:
            for window in session.windows:
                for pane in window.panes:
                    panes.append(self._pane_to_info(pane))
        return panes

    def split_window(
        self,
        *,
        target: str,
        command: str,
        vertical: bool,
        start_directory: Optional[str],
        focus: bool,
        environment: Dict[str, str],
        session: Optional[str],
        percent: Optional[int] = None,
    ) -> str:
        pane = self._get_pane(target)
        if pane is None:
            raise ValueError(f"Pane not found: {target}")
        window = pane.window
        new_pane = window.split_window(
            target=pane.id,
            vertical=vertical,
            attach=focus,
            start_directory=start_directory,
            shell=command or None,
            environment=environment or None,
            percent=percent,
        )
        return new_pane.id

    def switch_client(self, target: str) -> None:
        # libtmux doesn't easily support switch-client as it's a client operation
        # But we can shell out or try to access underlying cmd
        if not self.server.has_session(target):
            raise ValueError(f"Session not found: {target}")
        self.server.cmd("switch-client", "-t", target)

    def attach_session(self, target: str) -> None:
        # attach-session is also tricky via libtmux server object
        if not self.server.has_session(target):
             raise ValueError(f"Session not found: {target}")
        self.server.cmd("attach-session", "-t", target)

    def new_window(
        self,
        *,
        session: str,
        window_name: str,
        command: str,
        start_directory: Optional[str],
        attach: bool,
        environment: Dict[str, str],
    ) -> str:
        s = self.server.find_where({"session_name": session})
        if not s:
            raise ValueError(f"Session not found: {session}")
        w = s.new_window(
            window_name=window_name,
            start_directory=start_directory,
            attach=attach,
            window_shell=command,
            environment=environment,
        )
        return w.panes[0].id

    def kill_window(self, session: str, window_name: str) -> None:
        s = self.server.find_where({"session_name": session})
        if not s:
            raise ValueError(f"Session not found: {session}")
        w = s.find_where({"window_name": window_name})
        if not w:
            # Try as window ID
             w = s.find_where({"window_id": window_name})
        if w:
            w.kill_window()

    def session_exists(self, session: str) -> bool:
        return self.server.has_session(session)

    def create_session(self, session: str, start_directory: Optional[str] = None, window_name: Optional[str] = None) -> None:
        if self.session_exists(session):
            raise ValueError(f"Session already exists: {session}")
        self.server.new_session(
            session_name=session,
            start_directory=start_directory,
            window_name=window_name
        )

    def rename_window(self, session: str, window_id: str, new_name: str) -> None:
        s = self.server.find_where({"session_name": session})
        if not s:
            raise ValueError(f"Session not found: {session}")
        w = s.find_where({"window_id": window_id}) or s.find_where({"window_name": window_id})
        if not w:
             # Try index
             try:
                 w = s.windows[int(window_id)]
             except (ValueError, IndexError):
                 pass
        if not w:
            raise ValueError(f"Window not found: {window_id}")
        w.rename_window(new_name)

    def select_window(self, session: str, window_target: str) -> None:
        s = self.server.find_where({"session_name": session})
        if not s:
             raise ValueError(f"Session not found: {session}")
        w = s.find_where({"window_id": window_target}) or s.find_where({"window_name": window_target})
        if not w:
             try:
                 w = s.windows[int(window_target)]
             except (ValueError, IndexError):
                 pass
        if not w:
             raise ValueError(f"Window not found: {window_target}")
        w.select_window()

    def set_pane_style(self, pane_id: str, style: str) -> None:
        self.server.cmd("select-pane", "-t", pane_id, "-P", f"style={style}")

    def set_pane_border_style(self, pane_id: str, style: str) -> None:
        # Not directly supported by simple select-pane -P in some versions but valid in newer tmux
        # Using server cmd to be safe
        self.server.cmd("select-pane", "-t", pane_id, "-P", f"border-style={style}")

    def set_pane_title(self, pane_id: str, title: str) -> None:
        # Same as rename_pane basically
        self.rename_pane(pane_id, title)

    def set_layout(self, window: str, layout: str) -> None:
        # Window can be session:window
        self.server.cmd("select-layout", "-t", window, layout)

    def display_popup(self, command: str, width: str = "80%", height: str = "80%") -> None:
         self.server.cmd("display-popup", "-w", width, "-h", height, "-E", command)

    def set_environment(self, session: str, key: str, value: str) -> None:
         self.server.cmd("set-environment", "-t", session, key, value)

    def enable_pane_titles(self, session: str) -> None:
        self.server.cmd("set-option", "-t", session, "pane-border-status", "top")
        self.server.cmd("set-option", "-t", session, "pane-border-format", "#{pane_title}")

    def rename_pane(self, pane_id: str, title: str) -> None:
        pane = self._get_pane(pane_id)
        if pane is None:
            raise ValueError(f"Pane not found: {pane_id}")
        pane.cmd("select-pane", "-t", pane.id, "-T", title)

    def focus_pane(self, pane_id: str) -> None:
        pane = self._get_pane(pane_id)
        if pane is None:
            raise ValueError(f"Pane not found: {pane_id}")
        pane.select_pane()

    def capture_pane(self, pane_id: str, lines: Optional[int]) -> str:
        pane = self._get_pane(pane_id)
        if pane is None:
            raise ValueError(f"Pane not found: {pane_id}")
        start = -abs(lines) if lines is not None else None
        captured = pane.capture_pane(start=start)
        return "\n".join(captured)

    def send_literal(self, pane_id: str, text: str, enter: bool) -> None:
        pane = self._get_pane(pane_id)
        if pane is None:
            raise ValueError(f"Pane not found: {pane_id}")
        pane.send_keys(text, enter=enter, literal=True)

    def send_key(self, pane_id: str, key: str) -> None:
        pane = self._get_pane(pane_id)
        if pane is None:
            raise ValueError(f"Pane not found: {pane_id}")
        pane.send_keys(key, enter=False)

    def get_pane(self, pane_id: str) -> Optional[PaneInfo]:
        pane = self._get_pane(pane_id)
        return self._pane_to_info(pane) if pane else None

    def kill_pane(self, pane_id: str) -> None:
        pane = self._get_pane(pane_id)
        if pane is None:
            raise ValueError(f"Pane not found: {pane_id}")
        pane.kill()

    def kill_session(self, session: str) -> None:
        if libtmux is None:
            raise RuntimeError("libtmux not available")
        tmux_session = self.server.sessions.get(session_name=session)
        if tmux_session is None:
            raise ValueError(f"Session not found: {session}")
        tmux_session.kill()

    def set_session_option(self, session: str, option: str, value: str) -> None:
        if libtmux is None:
            raise RuntimeError("libtmux not available")
        s = self.server.sessions.get(session_name=session)
        if s is None:
             raise ValueError(f"Session not found: {session}")
        s.set_option(option, value)

    def set_global_option(self, option: str, value: str) -> None:
        # libtmux server.set_option sets global server options usually?
        # Or cmd.
        self.server.cmd("set-option", "-g", option, value)


    def _get_pane(self, pane_id: str):
        for session in self.server.sessions:
            for window in session.windows:
                for pane in window.panes:
                    if pane.id == pane_id:
                        return pane
        return None

    def _pane_to_info(self, pane) -> PaneInfo:
        window = pane.window
        session = window.session if window else None
        return PaneInfo(
            pane_id=pane.get("pane_id"),
            title=pane.get("pane_title") or "",
            command=pane.get("pane_current_command") or "",
            window=window.name if window else "",
            session=session.name if session else "",
            path=pane.get("pane_current_path") or "",
            active=pane.get("pane_active") == "1",
        )


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


class TmuxController:
    """High-level controller orchestrating tmux actions."""

    _SPECIAL_KEY_PATTERN = re.compile(r"<([^<>]+)>")

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        *,
        backend: Optional[BaseTmuxBackend] = None,
        config: Optional[TmuxControllerConfig] = None,
        time_provider: Optional[Callable[[], float]] = None,
        sleep_func: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._config_manager = config_manager
        self.config = config or self._load_config()
        self.backend = backend or self._select_backend()
        self._time = time_provider or time.monotonic
        self._sleep = sleep_func or time.sleep
        self._last_send_ts: Optional[float] = None

    def list_panes(self, session: Optional[str] = None) -> List[PaneInfo]:
        """Return panes filtered by allowed sessions."""
        panes = self.backend.list_panes()
        panes = self._filter_allowed_sessions(panes)
        if session:
            panes = [pane for pane in panes if pane.session == session]
        return panes

    def resolve_pane(self, identifier: Optional[str] = None) -> Optional[PaneInfo]:
        """Public helper to resolve pane metadata by id/title/window."""
        return self._resolve_pane(identifier)

    def open(
        self,
        spec: str,
        *,
        target: Optional[str] = None,
        vertical: bool = False,
        focus: Optional[bool] = None,
        name: Optional[str] = None,
        cwd: Optional[str] = None,
        command_override: Optional[str] = None,
        environment_override: Optional[Dict[str, str]] = None,
    ) -> PaneInfo:
        """Open a new pane using a preset or arbitrary command."""
        panes = self.list_panes()
        original_active = next((pane for pane in panes if pane.active), None)
        target_pane = self._select_target_pane(panes, target)
        if target_pane is None:
            raise RuntimeError(
                "No tmux pane available to split; specify --target or attach to tmux."
            )

        alias = spec[1:].strip() if spec.startswith(":") else None
        preset, command, environment = self._resolve_command_spec(
            spec,
            command_override=command_override,
        )
        if not command:
            raise ValueError("Command to launch cannot be empty.")

        if focus is None:
            pane_focus = preset.focus if preset else True
        else:
            pane_focus = focus

        pane_cwd = cwd or (preset.cwd if preset else None)
        pane_title = name or (alias if alias else None)
        final_environment = dict(environment)
        if environment_override:
            for key, value in environment_override.items():
                if value is not None:
                    final_environment[key] = value

        new_pane_id = self.backend.split_window(
            target=target_pane.pane_id,
            command=command,
            vertical=vertical,
            start_directory=pane_cwd,
            focus=pane_focus,
            environment=final_environment,
            session=target_pane.session,
        )

        if pane_title:
            self.backend.rename_pane(new_pane_id, pane_title)

        if not pane_focus:
            if original_active:
                self.backend.focus_pane(original_active.pane_id)
            else:
                self.backend.focus_pane(target_pane.pane_id)

        new_pane = self.backend.get_pane(new_pane_id)
        if new_pane is None:
            raise RuntimeError("New pane was created but could not be located.")
        return new_pane

    def send_keys(
        self,
        target: str,
        text: str,
        *,
        enter: bool = True,
        raw: bool = False,
        respect_rate_limit: bool = True,
    ) -> None:
        """Send keystrokes or literal text to a pane."""
        pane = self._resolve_pane(target)
        if pane is None:
            raise ValueError(f"Pane not found: {target}")

        if respect_rate_limit:
            self._enforce_rate_limit()

        if raw:
            self.backend.send_literal(pane.pane_id, text, enter=enter)
            if respect_rate_limit:
                self._record_send()
            return

        actions = self._parse_send_payload(text)
        for action_type, value in actions:
            if action_type == "text":
                if value:
                    self.backend.send_literal(pane.pane_id, value, enter=False)
            elif action_type == "key":
                self.backend.send_key(pane.pane_id, value)
        if enter:
            self.backend.send_key(pane.pane_id, "Enter")
        if respect_rate_limit:
            self._record_send()

    def capture(
        self,
        target: str,
        *,
        lines: Optional[int] = None,
    ) -> str:
        """Capture recent output from a pane."""
        pane = self._resolve_pane(target)
        if pane is None:
            raise ValueError(f"Pane not found: {target}")

        count = lines if lines is not None else self.config.capture_default_lines
        output = self.backend.capture_pane(pane.pane_id, count)
        return output.rstrip("\n")

    def snapshot(
        self,
        target: str,
        *,
        lines: Optional[int] = None,
    ) -> PaneSnapshot:
        pane = self._resolve_pane(target)
        if pane is None:
            raise ValueError(f"Pane not found: {target}")
        data = self.backend.capture_pane(pane.pane_id, lines if lines is not None else self.config.capture_default_lines)
        return PaneSnapshot(pane=pane, content=data)

    def close_pane(self, target: Optional[str] = None) -> PaneInfo:
        pane = self._resolve_pane(target or "")
        if pane is None:
            raise ValueError("Unable to determine pane to close")
        self.backend.kill_pane(pane.pane_id)
        return pane

    def close_session(self, session: str) -> None:
        self.backend.kill_session(session)

    def set_session_option(self, session: str, option: str, value: str) -> None:
        """Set a tmux session option."""
        self.backend.set_session_option(session, option, value)

    def set_global_option(self, option: str, value: str) -> None:
        """Set a global tmux option."""
        self.backend.set_global_option(option, value)


    def new_window(
        self,
        *,
        session: str,
        window_name: str,
        command: str = "",
        start_directory: Optional[str] = None,
        attach: bool = True,
        environment: Optional[Dict[str, str]] = None,
    ) -> str:
        return self.backend.new_window(
            session=session,
            window_name=window_name,
            command=command,
            start_directory=start_directory,
            attach=attach,
            environment=environment or {},
        )

    def rename_window(self, session: str, window_id: str, new_name: str) -> None:
        self.backend.rename_window(session, window_id, new_name)

    def select_window(self, session: str, window_target: str) -> None:
        self.backend.select_window(session, window_target)

    def get_active_session_name(self) -> Optional[str]:
        """Return the name of the currently active session."""
        try:
             # Find active pane
             panes = self.list_panes()
             active = next((p for p in panes if p.active), None)
             if active:
                 return active.session
             # Fallback if no pane is active (should be rare)
             return None
        except Exception:
             return None

    # ------------------------------------------------------------------ #
    # Session Management                                                 #
    # ------------------------------------------------------------------ #

    def session_exists(self, session: str) -> bool:
        return self.backend.session_exists(session)

    def create_session(self, session: str, start_directory: Optional[str] = None, window_name: Optional[str] = None) -> None:
        self.backend.create_session(session, start_directory=start_directory, window_name=window_name)

    def kill_window(self, session: str, window_name: str) -> None:
        self.backend.kill_window(session, window_name)

    def switch_client(self, target: str) -> None:
        self.backend.switch_client(target)

    def attach_session(self, target: str) -> None:
        self.backend.attach_session(target)

    def set_pane_style(self, pane_id: str, style: str) -> None:
        self.backend.set_pane_style(pane_id, style)

    def set_pane_border_style(self, pane_id: str, style: str) -> None:
        self.backend.set_pane_border_style(pane_id, style)

    def set_pane_title(self, pane_id: str, title: str) -> None:
        self.backend.set_pane_title(pane_id, title)

    def set_layout(self, window: str, layout: str) -> None:
        self.backend.set_layout(window, layout)

    def display_popup(self, command: str, width: str = "80%", height: str = "80%") -> None:
        """Display a popup with the given command."""
        self.backend.display_popup(command, width=width, height=height)

    def set_environment(self, session: str, key: str, value: str) -> None:
        self.backend.set_environment(session, key, value)

    def enable_pane_titles(self, session: str) -> None:
        self.backend.enable_pane_titles(session)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _load_config(self) -> TmuxControllerConfig:
        manager = self._config_manager or ConfigManager()
        return manager.get_tmux_config()

    def _select_backend(self) -> BaseTmuxBackend:
        if libtmux is not None:
            try:
                return LibTmuxBackend()
            except Exception as exc:  # pragma: no cover - defensive
                warnings.warn(
                    f"libtmux backend unavailable ({exc}); falling back to tmux CLI.",
                    RuntimeWarning,
                )
                logger.error(f"Error: {exc}")
        return CliTmuxBackend()

    def _filter_allowed_sessions(self, panes: Iterable[PaneInfo]) -> List[PaneInfo]:
        allowed = self.config.allowed_sessions
        if not allowed:
            return list(panes)
        allowed_set = {session.lower() for session in allowed}
        return [pane for pane in panes if pane.session.lower() in allowed_set]

    def _select_target_pane(
        self,
        panes: Sequence[PaneInfo],
        target: Optional[str],
    ) -> Optional[PaneInfo]:
        if not panes:
            return None

        if target:
            normalized = target.strip()
            # Direct pane id match
            for pane in panes:
                if pane.pane_id == normalized:
                    return pane
            lowered = normalized.lower()
            for pane in panes:
                if lowered in {
                    pane.title.lower(),
                    pane.window.lower(),
                    pane.session.lower(),
                    pane.pane_id.lower(),
                }:
                    return pane
                if lowered == f"{pane.session}:{pane.window}".lower():
                    return pane
            return None

        session_hint = self.config.default_session
        if session_hint:
            for pane in panes:
                if pane.session == session_hint and pane.active:
                    return pane
            for pane in panes:
                if pane.session == session_hint:
                    return pane

        for pane in panes:
            if pane.active:
                return pane
        return panes[0]

    def _resolve_pane(self, target: Optional[str]) -> Optional[PaneInfo]:
        panes = self.list_panes()
        return self._select_target_pane(panes, target)

    def _resolve_command_spec(
        self,
        spec: str,
        *,
        command_override: Optional[str],
    ) -> Tuple[Optional[TmuxPresetConfig], str, Dict[str, str]]:
        if spec.startswith(":"):
            preset_name = spec[1:].strip()
            if not preset_name:
                raise ValueError("Preset name cannot be empty (e.g. :claude).")
            try:
                preset = self.config.presets[preset_name]
            except KeyError:
                raise ValueError(f"Unknown tmux preset: {preset_name}")
            command = self._expand_text(command_override or preset.command)
            environment = self._expand_environment(preset.environment)
            return preset, command, environment

        command = self._expand_text(command_override or spec)
        environment: Dict[str, str] = {}
        return None, command, environment

    def _enforce_rate_limit(self) -> None:
        limit = self.config.send_rate_limit_seconds
        if limit <= 0:
            return
        if self._last_send_ts is None:
            return
        elapsed = self._time() - self._last_send_ts
        if elapsed < limit:
            self._sleep(limit - elapsed)

    def _record_send(self) -> None:
        self._last_send_ts = self._time()

    def _parse_send_payload(self, payload: str) -> List[Tuple[str, str]]:
        if not payload:
            return []

        actions: List[Tuple[str, str]] = []
        index = 0
        while index < len(payload):
            match = self._SPECIAL_KEY_PATTERN.search(payload, index)
            if not match:
                actions.append(("text", payload[index:]))
                break

            if match.start() > index:
                actions.append(("text", payload[index : match.start()]))

            key_token = match.group(1)
            resolved = self._resolve_special_key(key_token)
            if resolved:
                actions.append(("key", resolved))
            else:
                raise ValueError(f"Unsupported key token: <{key_token}>")

            index = match.end()

        return actions

    def _resolve_special_key(self, token: str) -> Optional[str]:
        normalized = token.strip().upper().replace(" ", "")

        basic_map = {
            "ENTER": "Enter",
            "RETURN": "Enter",
            "ESC": "Escape",
            "ESCAPE": "Escape",
            "TAB": "Tab",
            "BACKSPACE": "Backspace",
            "BS": "Backspace",
            "SPACE": "Space",
            "UP": "Up",
            "DOWN": "Down",
            "LEFT": "Left",
            "RIGHT": "Right",
            "PGUP": "PageUp",
            "PGDN": "PageDown",
            "HOME": "Home",
            "END": "End",
            "DEL": "Delete",
            "DELETE": "Delete",
        }
        if normalized in basic_map:
            return basic_map[normalized]

        if normalized.startswith(("CTRL+", "CONTROL+")):
            suffix = normalized.split("+", 1)[-1]
            if suffix.startswith("SHIFT+"):
                key = suffix.split("+", 1)[-1].lower()
                return f"C-S-{key}"
            if suffix.startswith("ALT+"):
                key = suffix.split("+", 1)[-1].lower()
                return f"C-M-{key}"
            suffix = suffix.lower()
            return f"C-{suffix}"

        if normalized.startswith("C-"):
            suffix = normalized[2:]
            if suffix.startswith("S-"):
                return f"C-S-{suffix[2:].lower()}"
            return f"C-{suffix.lower()}"

        if normalized.startswith(("SHIFT+", "S-")):
            suffix = normalized.split("+", 1)[-1] if "+" in normalized else normalized[2:]
            suffix = suffix.capitalize()
            return f"S-{suffix}"

        if normalized.startswith(("ALT+", "META+")):
            suffix = normalized.split("+", 1)[-1]
            if suffix.startswith("SHIFT+"):
                key = suffix.split("+", 1)[-1].lower()
                return f"M-S-{key}"
            suffix = suffix.lower()
            return f"M-{suffix}"

        if normalized.startswith("M-"):
            suffix = normalized[2:]
            if suffix.startswith("S-"):
                return f"M-S-{suffix[2:].lower()}"
            return f"M-{suffix.lower()}"

        if normalized.startswith("F") and normalized[1:].isdigit():
            return normalized

        return None

    def _expand_text(self, value: str) -> str:
        def repl(match: re.Match[str]) -> str:
            body = match.group(1)
            if ":" in body:
                var, default = body.split(":", 1)
            else:
                var, default = body, ""
            return os.getenv(var, default)

        expanded = _VAR_PATTERN.sub(repl, value)
        expanded = os.path.expandvars(expanded)
        expanded = os.path.expanduser(expanded)
        return expanded

    def _expand_environment(self, env: Dict[str, str]) -> Dict[str, str]:
        return {key: self._expand_text(val) for key, val in env.items()}

    def resolve_pane(self, identifier: Optional[str] = None) -> Optional[PaneInfo]:
        """Public helper to resolve a pane identifier."""
        panes = self.list_panes()
        return self._select_target_pane(panes, identifier)
