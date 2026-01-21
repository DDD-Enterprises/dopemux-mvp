"""High-level tmux controller for Dopemux."""

from __future__ import annotations

import re
import time
import warnings
from dataclasses import dataclass
import os
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ..config.manager import (
    ConfigManager,
    TmuxControllerConfig,
    TmuxPresetConfig,
)
from ..mobile import tmux_utils

try:  # pragma: no cover - optional dependency
    import libtmux  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    libtmux = None  # type: ignore


@dataclass
class PaneInfo:
    """Lightweight representation of a tmux pane."""

    pane_id: str
    title: str
    command: str
    window: str
    session: str
    path: str
    active: bool


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

    def kill_session(self, session: str) -> None:
        raise NotImplementedError


class CliTmuxBackend(BaseTmuxBackend):
    """Backend using direct tmux CLI invocations."""

    def list_panes(self) -> List[PaneInfo]:
        panes = []
        for pane in tmux_utils.list_panes():
            panes.append(
                PaneInfo(
                    pane_id=pane.pane_id,
                    title=pane.title,
                    command=pane.command,
                    window=pane.window,
                    session=pane.session,
                    path=pane.path,
                    active=pane.active,
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
        return tmux_utils.split_window(
            target,
            command,
            vertical=vertical,
            start_directory=start_directory,
            attach=focus,
            environment=environment,
            session=session,
            percent=percent,
        )

    def rename_pane(self, pane_id: str, title: str) -> None:
        tmux_utils.set_pane_title(pane_id, title)

    def focus_pane(self, pane_id: str) -> None:
        tmux_utils.focus_pane(pane_id)

    def capture_pane(self, pane_id: str, lines: Optional[int]) -> str:
        return tmux_utils.capture_pane_output(pane_id, lines=lines)

    def send_literal(self, pane_id: str, text: str, enter: bool) -> None:
        tmux_utils.send_literal_text(pane_id, text, enter=enter)

    def send_key(self, pane_id: str, key: str) -> None:
        tmux_utils.send_key(pane_id, key)

    def get_pane(self, pane_id: str) -> Optional[PaneInfo]:
        return next(
            (pane for pane in self.list_panes() if pane.pane_id == pane_id),
            None,
        )

    def kill_pane(self, pane_id: str) -> None:
        tmux_utils.kill_pane(pane_id)

    def kill_session(self, session: str) -> None:
        tmux_utils.kill_session(session)


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
