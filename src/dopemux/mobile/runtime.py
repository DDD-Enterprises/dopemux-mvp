"""Runtime helpers for Dopemux Happy mobile integration."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from ..config.manager import ConfigManager, MobileConfig
from ..tmux.utils import (
    TmuxError,
    TmuxPane,
    build_env_command,
    display_popup,
    kill_pane,
    list_panes,
    list_windows,
    new_window,
    send_interrupt,
    set_global_option,
    set_layout,
    set_pane_title,
    split_window,
)

MOBILE_WINDOW_NAME = "mobile"


@dataclass
class LaunchOutcome:
    """Result of launching Happy sessions."""

    started: List[str]
    skipped_existing: List[str]


@dataclass
class MobileStatus:
    """Snapshot of mobile readiness and active sessions."""

    enabled: bool
    happy_ok: bool
    claude_ok: bool
    sessions: List[TmuxPane]
    tmux_error: Optional[str]


def ensure_dependency(binary: str) -> Tuple[bool, Optional[str]]:
    """Check if binary is available on PATH."""

    path = shutil.which(binary)
    if path:
        return True, path
    return False, None


def check_cli_health(binary: str, timeout: float = 3.0) -> bool:
    """Run a lightweight version command to confirm CLI availability."""

    ok, path = ensure_dependency(binary)
    if not ok or not path:
        return False

    try:
        subprocess.run(
            [path, "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return True
    except Exception as e:
        return False



def env_for_happy(config: MobileConfig) -> dict[str, str]:
    """Build environment variables for Happy CLI."""

    env: dict[str, str] = {}
    if config.happy_server_url:
        env["HAPPY_SERVER_URL"] = config.happy_server_url
    if config.happy_webapp_url:
        env["HAPPY_WEBAPP_URL"] = config.happy_webapp_url
    return env


def list_claude_panes() -> List[TmuxPane]:
    """Return panes that appear to host Claude sessions."""

    try:
        panes = list_panes()
    except TmuxError:
        return []

    claude_like: List[TmuxPane] = []
    for pane in panes:
        haystack = " ".join(
            filter(
                None,
                [pane.title.lower(), pane.command.lower(), pane.window.lower()],
            )
        )
        if any(keyword in haystack for keyword in ("claude", "anthropic", "agent")):
            claude_like.append(pane)
    return claude_like


def _match_panes(panes: Sequence[TmuxPane], selectors: Sequence[str]) -> List[TmuxPane]:
    selected: List[TmuxPane] = []
    normalized = [selector.lower() for selector in selectors]
    for selector in normalized:
        for pane in panes:
            candidates = {
                pane.pane_id.lower(),
                pane.title.lower(),
                pane.window.lower(),
                pane.label.lower(),
            }
            if selector in candidates or any(selector in value for value in candidates):
                if pane not in selected:
                    selected.append(pane)
    return selected


def resolve_targets(
    launch_all: bool,
    explicit_panes: Sequence[str],
    mobile_config: MobileConfig,
    mapping_strategy: Optional[str] = None,
) -> List[TmuxPane]:
    """Resolve requested panes to Claude pane metadata."""

    panes = list_claude_panes()
    if not panes:
        return []

    if explicit_panes:
        matched = _match_panes(panes, explicit_panes)
        return matched

    if mapping_strategy == "agents":
        return panes

    if launch_all:
        return panes

    default = mobile_config.default_panes
    if isinstance(default, list):
        matched = _match_panes(panes, default)
        if matched:
            return matched
    else:
        if default == "all":
            return panes
        if default == "primary":
            active = next((pane for pane in panes if pane.active), None)
            if active:
                return [active]
            return [panes[0]]
        matched = _match_panes(panes, [default])
        if matched:
            return matched

    # Fallback to first pane
    return [panes[0]]


def _existing_mobile_labels() -> List[str]:
    labels: List[str] = []
    try:
        panes = list_panes()
    except TmuxError:
        return labels

    for pane in panes:
        if pane.window == MOBILE_WINDOW_NAME and pane.command == "happy":
            if pane.title.startswith("mobile:"):
                labels.append(pane.title.split(":", 1)[1])
            else:
                labels.append(pane.title)
    return labels


def _label_for_pane(pane: TmuxPane) -> str:
    base = pane.title or pane.window or pane.pane_id
    cleaned = base.replace("mobile:", "").strip() or pane.pane_id
    return cleaned


def launch_happy_sessions(
    targets: Sequence[TmuxPane],
    env: dict[str, str],
    mobile_config: MobileConfig,
    labels: Optional[Sequence[str]] = None,
) -> LaunchOutcome:
    """Launch Happy instances for each target pane."""

    if not targets:
        return LaunchOutcome(started=[], skipped_existing=[])

    existing_labels = set(label.lower() for label in _existing_mobile_labels())
    started_labels: List[str] = []
    skipped_labels: List[str] = []
    command = build_env_command("happy", env)

    if mobile_config.popup_mode:
        # Popup mode launches one session at a time
        display_popup(command)
        return LaunchOutcome(started=["popup"], skipped_existing=[])

    windows = list_windows()
    window_exists = MOBILE_WINDOW_NAME in windows

    for index, pane in enumerate(targets):
        if labels and index < len(labels) and labels[index].strip():
            label = labels[index].strip()
        else:
            label = _label_for_pane(pane)
        normalized = label.lower()
        if normalized in existing_labels:
            skipped_labels.append(label)
            continue

        if not window_exists and index == 0:
            pane_id = new_window(MOBILE_WINDOW_NAME, command)
        else:
            pane_id = split_window(MOBILE_WINDOW_NAME, command, vertical=index % 2 == 0)
        set_pane_title(pane_id, f"mobile:{label}")
        started_labels.append(label)
        window_exists = True

    if started_labels:
        set_layout(MOBILE_WINDOW_NAME, "tiled")

    return LaunchOutcome(started=started_labels, skipped_existing=skipped_labels)


def list_mobile_panes() -> List[TmuxPane]:
    try:
        panes = list_panes()
    except TmuxError:
        return []
    return [pane for pane in panes if pane.window == MOBILE_WINDOW_NAME and pane.command == "happy"]


def detach_mobile_sessions(selected_labels: Optional[Sequence[str]] = None) -> List[str]:
    """Detach Happy processes running in the mobile window."""

    panes = list_mobile_panes()
    if not panes:
        return []

    targets = panes
    if selected_labels:
        normalized = {label.lower() for label in selected_labels}
        targets = [
            pane
            for pane in panes
            if pane.title.lower().startswith("mobile:")
            and pane.title.split(":", 1)[1].lower() in normalized
        ]
        if not targets:
            return []

    detached: List[str] = []
    for pane in targets:
        send_interrupt(pane.pane_id)
        time.sleep(0.1)
        kill_pane(pane.pane_id)
        if pane.title.startswith("mobile:"):
            detached.append(pane.title.split(":", 1)[1])
        else:
            detached.append(pane.title or pane.pane_id)

    return detached


def mobile_notify(message: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    """Send a Happy push notification."""

    command = ["happy", "notify", message]
    merged_env = os.environ.copy()
    merged_env.update(env)
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=merged_env,
        timeout=5,
    )


def notify_mobile_event(config_manager: ConfigManager, message: str) -> bool:
    """Send a mobile notification if mobile mode is enabled."""

    try:
        mobile_cfg = config_manager.get_mobile_config()
    except Exception as e:
        return False


    if not mobile_cfg.enabled:
        return False

    happy_ok, _ = ensure_dependency("happy")
    if not happy_ok:
        return False

    result = mobile_notify(message, env_for_happy(mobile_cfg))
    return result.returncode == 0


def get_mobile_status(config_manager: ConfigManager) -> MobileStatus:
    """Collect mobile CLI health and session information."""

    mobile_cfg = config_manager.get_mobile_config()
    happy_ok = check_cli_health("happy")
    claude_ok = check_cli_health("claude")

    try:
        sessions = list_mobile_panes()
        tmux_error: Optional[str] = None
    except TmuxError as exc:
        sessions = []
        tmux_error = str(exc)


    return MobileStatus(
        enabled=mobile_cfg.enabled,
        happy_ok=happy_ok,
        claude_ok=claude_ok,
        sessions=sessions,
        tmux_error=tmux_error,
    )


def format_mobile_indicator(status: MobileStatus) -> str:
    """Return a tmux-friendly colored indicator string."""

    def colored(text: str, color: str) -> str:
        return f"#[fg={color}]{text}#[default]"

    if status.tmux_error:
        return colored("📱 tmux", "#f9e2af")

    if not status.enabled:
        return colored("📵 off", "#f9e2af")

    if not status.happy_ok:
        return colored("📱 down", "#f38ba8")

    if not status.claude_ok:
        return colored("📱 warn", "#f9e2af")

    session_count = len(status.sessions)
    if session_count:
        return colored(f"📱 {session_count}", "#a6e3a1")

    return colored("📱 idle", "#89b4fa")


def update_tmux_mobile_indicator(config_manager: ConfigManager) -> None:
    """Refresh the tmux statusline indicator for mobile readiness."""

    try:
        status = get_mobile_status(config_manager)
        indicator = format_mobile_indicator(status)
        set_global_option("@dopemux_mobile_indicator", indicator)
        _persist_mobile_status(config_manager, status)
    except Exception as e:
        # tmux might not be available; ignore silently
        pass



def _persist_mobile_status(config_manager: ConfigManager, status: MobileStatus) -> None:
    """Write mobile status snapshot to cache for other UIs."""

    try:
        cache_dir = Path(config_manager.paths.cache_dir) / "status"
        cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "enabled": status.enabled,
            "happy_ok": status.happy_ok,
            "claude_ok": status.claude_ok,
            "tmux_error": status.tmux_error,
            "sessions": [
                {
                    "pane_id": pane.pane_id,
                    "title": pane.title,
                    "window": pane.window,
                    "session": pane.session,
                    "path": pane.path,
                    "active": pane.active,
                }
                for pane in status.sessions
            ],
            "updated_at": time.time(),
        }
        snapshot_path = cache_dir / "mobile_status.json"
        snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        pass
