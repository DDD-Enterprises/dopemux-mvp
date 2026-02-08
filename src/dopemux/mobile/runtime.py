"""Runtime helpers for Dopemux Happy mobile integration."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import shutil
import subprocess
import shlex
import time
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from ..config.manager import ConfigManager, MobileConfig
from ..tmux.common import PaneInfo, TmuxError
from ..tmux.controller import TmuxController


MOBILE_WINDOW_NAME = "mobile"
logger = logging.getLogger(__name__)


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
    sessions: List[PaneInfo]
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


def list_claude_panes(controller: Optional[TmuxController] = None) -> List[PaneInfo]:
    """Return panes that appear to host Claude sessions."""
    
    if controller is None:
        controller = TmuxController()

    try:
        panes = controller.list_panes()
    except TmuxError:
        return []

    claude_like: List[PaneInfo] = []
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


def _match_panes(panes: Sequence[PaneInfo], selectors: Sequence[str]) -> List[PaneInfo]:
    selected: List[PaneInfo] = []
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
    controller: Optional[TmuxController] = None,
) -> List[PaneInfo]:
    """Resolve requested panes to Claude pane metadata."""

    panes = list_claude_panes(controller)
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


def _existing_mobile_labels(controller: TmuxController) -> List[str]:
    labels: List[str] = []
    try:
        panes = controller.list_panes()
    except TmuxError:
        return labels

    for pane in panes:
        if pane.window == MOBILE_WINDOW_NAME and "happy" in pane.command:
             # loose match for happy command
            if pane.title.startswith("mobile:"):
                labels.append(pane.title.split(":", 1)[1])
            else:
                labels.append(pane.title)
    return labels


def _label_for_pane(pane: PaneInfo) -> str:
    base = pane.title or pane.window or pane.pane_id
    cleaned = base.replace("mobile:", "").strip() or pane.pane_id
    return cleaned


def launch_happy_sessions(
    targets: Sequence[PaneInfo],
    env: dict[str, str],
    mobile_config: MobileConfig,
    labels: Optional[Sequence[str]] = None,
    controller: Optional[TmuxController] = None,
) -> LaunchOutcome:
    """Launch Happy instances for each target pane."""
    
    if controller is None:
        controller = TmuxController()

    if not targets:
        return LaunchOutcome(started=[], skipped_existing=[])

    existing_labels = set(label.lower() for label in _existing_mobile_labels(controller))
    started_labels: List[str] = []
    skipped_labels: List[str] = []
    
    # helper for env command building (now specialized here or via controller?)
    # Controller doesn't expose build_env_command directly publicly, 
    # but new_window/split_window accept env dict found in TmuxController.
    # However, for display_popup we need a command string.
    
    # We can reconstruct helper or rely on controller options.
    # TmuxController.display_popup takes a command string.
    def build_cmd(cmd: str, environment: dict) -> str:
        if not environment: return cmd
        assigns = " ".join(f"{k}={shlex.quote(v)}" for k, v in environment.items())
        return f"{assigns} {cmd}"

    full_popup_cmd = build_cmd("happy", env)

    if mobile_config.popup_mode:
        controller.display_popup(full_popup_cmd)
        return LaunchOutcome(started=["popup"], skipped_existing=[])

    # Check for window existence. TmuxController doesn't have list_windows directly returning names easily?
    # Actually list_panes gives us windows.
    try:
        current_panes = controller.list_panes()
        windows = {p.window for p in current_panes}
    except TmuxError:
        windows = set()
        
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
            pane_id = controller.new_window(
                session=pane.session, # Create in same session as target? Or active?
                window_name=MOBILE_WINDOW_NAME,
                command="happy",
                environment=env,
                attach=True
            )
        else:
            # Split window logic.
            # We need to target the mobile window.
            # Controller.open uses higher level logic.
            # We can use backend directly or specific split.
            # Let's use controller.open or backend split?
            # Controller `new_window` creates a window.
            # Controller `open` can split.
            # But we want to split the *mobile window*.
            # The mobile window might just have been created.
            # If we just created it, we know the pane_id (returned by new_window).
            # But subsequent iterations?
            
            # The original logic used `split_window(MOBILE_WINDOW_NAME, ...)` which targets window name.
            # TmuxController backend split_window takes target.
            
            # Use backend directly for precise control if needed, 
            # OR use `controller.backend.split_window`.
            # Or `controller.config` based...
            
            # Let's use controller.backend for now to match logic closely.
            pane_id = controller.backend.split_window(
                target=MOBILE_WINDOW_NAME,
                command="happy",
                vertical=index % 2 == 0,
                start_directory=None,
                focus=True,
                environment=env,
                session=None # Target string handles it
            )

        controller.set_pane_title(pane_id, f"mobile:{label}")
        started_labels.append(label)
        window_exists = True

    if started_labels:
        controller.set_layout(MOBILE_WINDOW_NAME, "tiled")

    return LaunchOutcome(started=started_labels, skipped_existing=skipped_labels)


def list_mobile_panes(controller: Optional[TmuxController] = None) -> List[PaneInfo]:
    if controller is None:
        controller = TmuxController()
    try:
        panes = controller.list_panes()
    except TmuxError:
        return []
    return [pane for pane in panes if pane.window == MOBILE_WINDOW_NAME and "happy" in pane.command]


def detach_mobile_sessions(
    selected_labels: Optional[Sequence[str]] = None,
    controller: Optional[TmuxController] = None,
) -> List[str]:
    """Detach Happy processes running in the mobile window."""
    
    if controller is None:
        controller = TmuxController()

    panes = list_mobile_panes(controller)
    if not panes:
        return []

    targets_to_kill = panes
    if selected_labels:
        normalized = {label.lower() for label in selected_labels}
        targets_to_kill = [
            pane
            for pane in panes
            if pane.title.lower().startswith("mobile:")
            and pane.title.split(":", 1)[1].lower() in normalized
        ]
        if not targets_to_kill:
            return []

    detached: List[str] = []
    for pane in targets_to_kill:
        # send_interrupt replacement
        controller.send_keys(pane.pane_id, "C-c", enter=False)
        time.sleep(0.1)
        controller.close_pane(pane.pane_id)
        
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


def get_mobile_status(config_manager: ConfigManager, controller: Optional[TmuxController] = None) -> MobileStatus:
    """Collect mobile CLI health and session information."""

    mobile_cfg = config_manager.get_mobile_config()
    happy_ok = check_cli_health("happy")
    claude_ok = check_cli_health("claude")

    try:
        sessions = list_mobile_panes(controller)
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


def update_tmux_mobile_indicator(config_manager: ConfigManager, controller: Optional[TmuxController] = None) -> None:
    """Refresh the tmux statusline indicator for mobile readiness."""
    
    if controller is None:
        controller = TmuxController(config_manager=config_manager)

    try:
        status = get_mobile_status(config_manager, controller)
        indicator = format_mobile_indicator(status)
        controller.set_session_option(status.sessions[0].session if status.sessions else controller.get_active_session_name() or "", "@dopemux_mobile_indicator", indicator)
        # set_session_option might fail if no session? 
        # Actually mobile indicator is often global or per session. 
        # Utils set_global_option was used.
        # Controller doesn't expose set_global_option (set -g).
        # We should use controller backend call if needed or just set on current session.
        # Let's try to set it globally via backend command if possible or just rely on session.
        # The original code used set_global_option("@dopemux_mobile_indicator", indicator).
        # If I want global, I need to add it or use backend.
        controller.set_global_option("@dopemux_mobile_indicator", indicator)
        
        _persist_mobile_status(config_manager, status)
    except Exception as e:
        # tmux might not be available; keep runtime running and log debug context.
        logger.debug("Failed updating tmux mobile indicator: %s", e)



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
        logger.debug("Failed persisting mobile status snapshot: %s", e)
