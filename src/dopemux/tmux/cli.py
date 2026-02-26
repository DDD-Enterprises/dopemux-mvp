"""Click command group exposing tmux controller operations."""

from __future__ import annotations

import os
import shlex
import shutil
import sys
import logging
import subprocess
import yaml
from pathlib import Path
from typing import Optional, Tuple, Sequence, List, Dict
from dataclasses import dataclass

import click
from rich.table import Table
from rich.prompt import Confirm
from click.shell_completion import CompletionItem

from ..config import ConfigManager
from ..console import console
from .controller import TmuxController, PaneInfo
from ..mobile.runtime import ensure_dependency, env_for_happy
from ..mobile import tmux_utils
from ..roles.catalog import available_roles, resolve_role, RoleNotFoundError
from ..litellm_proxy import (
    DEFAULT_LITELLM_CONFIG,
    ensure_master_key,
    LiteLLMProxyError,
    sync_litellm_database,
)


@dataclass
class OrchestratorLayout:
    monitors: list[str]
    orchestrator: str
    agent: str
    sandbox: Optional[str] = None
    secondary_agent: Optional[str] = None
    metrics_bar: Optional[str] = None


HOUSE_THEME = {
    "pane_styles": {
        "monitor:worktree": "fg=#a6e3a1,bg=#1e1e2e",
        "monitor:logs": "fg=#89dceb,bg=#1e1e2e",
        "monitor:metrics": "fg=#f9e2af,bg=#1e1e2e",
        "monitor:attention": "fg=#f9e2af,bg=#1e1e2e",
        "monitor:adhd": "fg=#a6e3a1,bg=#1e1e2e",
        "monitor:system": "fg=#89dceb,bg=#1e1e2e",
        "monitor:pm-hierarchy": "fg=#f9e2af,bg=#1e1e2e",
        "monitor:task-detail": "fg=#f5c2e7,bg=#1e1e2e",
        "monitor": "fg=#cdd6f4,bg=#1e1e2e",
        "metrics:bar": "fg=#89b4fa,bg=#11111b",
        "orchestrator:control": "fg=#cdd6f4,bg=#181825",
        "sandbox:shell": "fg=#f5c2e7,bg=#302d41",
        "agent:primary": "fg=#a6e3a1,bg=#1f1d2e",
        "agent:secondary": "fg=#b4befe,bg=#262335",
    },
    "pane_border_styles": {
        "monitor:worktree": "fg=#a6e3a1,bg=#181825",
        "monitor:logs": "fg=#89dceb,bg=#181825",
        "monitor:metrics": "fg=#f9e2af,bg=#181825",
        "monitor:attention": "fg=#f9e2af,bg=#181825",
        "monitor:adhd": "fg=#a6e3a1,bg=#181825",
        "monitor:system": "fg=#89dceb,bg=#181825",
        "monitor:pm-hierarchy": "fg=#f9e2af,bg=#181825",
        "monitor:task-detail": "fg=#f5c2e7,bg=#181825",
        "monitor": "fg=#cdd6f4,bg=#181825",
        "metrics:bar": "fg=#89b4fa,bg=#181825",
        "orchestrator:control": "fg=#cdd6f4,bg=#11111b",
        "sandbox:shell": "fg=#f5c2e7,bg=#11111b",
        "agent:primary": "fg=#a6e3a1,bg=#11111b",
        "agent:secondary": "fg=#b4befe,bg=#11111b",
    },
    "status_style": "bg=#1e1e2e,fg=#cdd6f4",
    "status_left": (
        "#[fg=#1e1e2e,bg=#89b4fa]"
        "#[fg=#11111b,bg=#89b4fa,bold] DOPMUX "
        "#[fg=#89b4fa,bg=#1e1e2e] "
        "#[fg=#a6e3a1]#H #[default]"
    ),
    "status_right": (
        "#[fg=#a6e3a1]#{@dopemux_mobile_indicator:-📱 idle} #[default]"
        "#[fg=#b4befe]#(./scripts/ccr_model_tracker.sh 2>/dev/null || echo '🤖') #[default]"
        "#[fg=#f5c2e7]  %R #[fg=#89dceb]%a %b %d "
        "#[fg=#cdd6f4]#{window_index}:#{window_name} "
        "#[fg=#f9e2af]#{pane_index}:#{pane_title}"
    ),
    "status_palette": {
        "accent": "#89b4fa",
        "background": "#1e1e2e",
        "foreground": "#cdd6f4",
        "warning": "#f9e2af",
        "success": "#a6e3a1",
        "info": "#89dceb",
        "alert": "#f5c2e7",
    },
}

NEON_THEME = {
    "pane_styles": {
        "monitor:worktree": "fg=#0f172a,bg=#94fadb",
        "monitor:logs": "fg=#020617,bg=#f5f26d",
        "monitor:metrics": "fg=#020617,bg=#ff8bd1",
        "monitor:attention": "fg=#020617,bg=#ff8bd1",
        "monitor:adhd": "fg=#020617,bg=#94fadb",
        "monitor:system": "fg=#020617,bg=#f5f26d",
        "monitor:pm-hierarchy": "fg=#020617,bg=#ff8bd1",
        "monitor:task-detail": "fg=#020617,bg=#ff66a3",
        "monitor": "fg=#020617,bg=#7dfbf6",
        "metrics:bar": "fg=#7dfbf6,bg=#020617",
        "orchestrator:control": "fg=#7dfbf6,bg=#0a1628",
        "sandbox:shell": "fg=#ff8bd1,bg=#1a0520",
        "agent:primary": "fg=#94fadb,bg=#041628",
        "agent:secondary": "fg=#020617,bg=#ffcf78",
    },
    "pane_border_styles": {
        "monitor:worktree": "fg=#94fadb,bg=#0f172a",
        "monitor:logs": "fg=#f5f26d,bg=#0f172a",
        "monitor:metrics": "fg=#ff8bd1,bg=#0f172a",
        "monitor:attention": "fg=#ff8bd1,bg=#0f172a",
        "monitor:adhd": "fg=#94fadb,bg=#0f172a",
        "monitor:system": "fg=#f5f26d,bg=#0f172a",
        "monitor:pm-hierarchy": "fg=#ff8bd1,bg=#0f172a",
        "monitor:task-detail": "fg=#ff66a3,bg=#0f172a",
        "monitor": "fg=#7dfbf6,bg=#020617",
        "metrics:bar": "fg=#7dfbf6,bg=#020617",
        "orchestrator:control": "fg=#7dfbf6,bg=#020617",
        "sandbox:shell": "fg=#ff8bd1,bg=#020617",
        "agent:primary": "fg=#94fadb,bg=#020617",
        "agent:secondary": "fg=#ffcf78,bg=#020617",
    },
    "status_style": "bg=#020617,fg=#e0f2fe",
    "status_left": (
        "#[fg=#020617,bg=#7dfbf6]"
        "#[fg=#041024,bg=#7dfbf6,bold] DOPMUX "
        "#[fg=#7dfbf6,bg=#020617] "
        "#[fg=#94fadb]#H #[default]"
    ),
    "status_right": (
        "#[fg=#94fadb]#{@dopemux_mobile_indicator:-📱 idle} #[default]"
        "#[fg=#ffcf78]#(./scripts/ccr_model_tracker.sh 2>/dev/null || echo '🤖') #[default]"
        "#[fg=#ff8bd1]  %R #[fg=#7dfbf6]%a %b %d "
        "#[fg=#9b78ff]#{window_index}:#{window_name} "
        "#[fg=#f5f26d]#{pane_index}:#{pane_title}"
    ),
    "status_palette": {
        "accent": "#7dfbf6",
        "background": "#020617",
        "foreground": "#e0f2fe",
        "warning": "#ffcf78",
        "success": "#94fadb",
        "info": "#7dfbf6",
        "alert": "#ff8bd1",
    },
}

THEME_PRESETS: Dict[str, Dict[str, Dict[str, str]]] = {
    "muted": HOUSE_THEME,
    "neon": NEON_THEME,
}


def _resolve_theme(config) -> Dict[str, Dict[str, str]]:
    """Merge theme preset with user overrides from configuration."""
    theme_key = (getattr(config, "theme", None) or "muted").lower()
    base = THEME_PRESETS.get(theme_key, HOUSE_THEME)

    merged = {
        "pane_styles": dict(base.get("pane_styles", {})),
        "pane_border_styles": dict(base.get("pane_border_styles", {})),
        "status_palette": dict(base.get("status_palette", {})),
        "status_style": base.get("status_style"),
        "status_left": base.get("status_left"),
        "status_right": base.get("status_right"),
    }

    # Apply config overrides
    merged["pane_styles"].update(getattr(config, "pane_styles", {}) or {})
    merged["pane_border_styles"].update(getattr(config, "pane_border_styles", {}) or {})
    if getattr(config, "status_palette", None):
        merged["status_palette"].update(config.status_palette or {})
    if getattr(config, "status_style", None):
        merged["status_style"] = config.status_style
    if getattr(config, "status_left", None):
        merged["status_left"] = config.status_left
    if getattr(config, "status_right", None):
        merged["status_right"] = config.status_right

    return merged


def _apply_status_theme(session: str, theme: Dict[str, Dict[str, str]]) -> None:
    """Set status line styling based on resolved theme."""
    status_style = theme.get("status_style")
    status_left = theme.get("status_left")
    status_right = theme.get("status_right")

    try:
        if status_style:
            tmux_utils.set_session_option(session, "status-style", status_style)
        if status_left:
            tmux_utils.set_session_option(session, "status-left", status_left)
        if status_right:
            tmux_utils.set_session_option(session, "status-right", status_right)
    except Exception:
        pass


def _apply_theme_to_session(
    controller: TmuxController,
    session: str,
    theme: Dict[str, Dict[str, str]],
) -> None:
    """Apply pane and status theming to an existing session."""
    pane_palette = theme.get("pane_styles", {})
    border_palette = theme.get("pane_border_styles", {})
    status_palette = theme.get("status_palette", {})

    try:
        _apply_status_theme(session, theme)
        tmux_utils.set_session_option(
            session,
            "pane-border-style",
            f"fg={status_palette.get('foreground', '#cdd6f4')},bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "pane-active-border-style",
            f"fg={status_palette.get('warning', '#ffcf78')},bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "window-style",
            f"bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "window-active-style",
            f"bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "@dopemux_title_fg",
            status_palette.get("foreground", "#cdd6f4"),
        )
        tmux_utils.set_session_option(
            session,
            "@dopemux_title_bg",
            status_palette.get("background", "#1e1e2e"),
        )
        tmux_utils.set_session_option(session, "aggressive-resize", "on")
    except Exception:
        pass

    panes = controller.backend.list_panes()
    for pane in panes:
        title = pane.title or ""
        if not title:
            title = pane.window or pane.command or ""
        key = title.split(":")[0] if ":" in title else title
        style = pane_palette.get(title) or pane_palette.get(key)
        border_style = border_palette.get(title) or border_palette.get(key)
        if style:
            try:
                tmux_utils.set_pane_style(pane.pane_id, style)
            except Exception:
                pass
        if border_style:
            try:
                tmux_utils.set_pane_border_style(pane.pane_id, border_style)
            except Exception:
                pass

def _get_controller(ctx: click.Context, force_cli_backend: bool = False) -> TmuxController:
    manager = ctx.obj.get("config_manager") if ctx.obj else None
    if not isinstance(manager, ConfigManager):
        manager = ConfigManager()
    
    # Force CLI backend when creating new sessions from outside tmux
    if force_cli_backend:
        from .controller import CliTmuxBackend
        backend = CliTmuxBackend()
        return TmuxController(config_manager=manager, backend=backend)
    
    return TmuxController(config_manager=manager)


def _pane_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str):
    controller = _get_controller(ctx)
    panes = controller.list_panes()
    completions = []
    needle = incomplete.lower()
    seen: set[str] = set()

    for pane in panes:
        candidates = [
            pane.pane_id,
            pane.title,
            pane.window,
            f"{pane.session}:{pane.window}",
        ]
        for candidate in candidates:
            if not candidate:
                continue
            value = candidate.strip()
            lowered = value.lower()
            if needle and needle not in lowered:
                continue
            if lowered in seen:
                continue
            seen.add(lowered)
            help_text = f"{pane.session}:{pane.window} · {pane.title or pane.command or ''}".strip()
            completions.append(CompletionItem(value=value, help=help_text))
    return completions


def _resolve_config_manager(ctx: click.Context) -> ConfigManager:
    manager = ctx.obj.get("config_manager") if ctx.obj else None
    if isinstance(manager, ConfigManager):
        return manager
    return ConfigManager()


def _launch_happy_for_targets(
    controller: TmuxController,
    cfg_manager: ConfigManager,
   targets: Sequence[Optional[str]],
   *,
   vertical: bool,
   focus_flag: bool,
    popup_override: Optional[bool] = None,
) -> None:
    mobile_cfg = cfg_manager.get_mobile_config()
    env = env_for_happy(mobile_cfg)
    all_panes = controller.backend.list_panes()
    existing_titles = {pane.title for pane in all_panes if pane.title}

    def _match_pane(identifier: Optional[str]) -> Optional[PaneInfo]:
        if not all_panes:
            return None
        if identifier is None:
            return next((pane for pane in all_panes if pane.active), all_panes[0])
        for pane in all_panes:
            if pane.pane_id == identifier:
                return pane
        lowered = identifier.lower()
        for pane in all_panes:
            candidates = filter(None, [pane.title, pane.window, f"{pane.session}:{pane.window}"])
            if any(lowered == candidate.lower() for candidate in candidates):
                return pane
        return None

    resolved: List[Tuple[PaneInfo, str, str]] = []
    for raw_target in targets:
        pane = _match_pane(raw_target)
        if pane is None:
            label = raw_target or "active"
            click.echo(f"❌ Pane not found: {label}")
            continue
        label = _happy_label(pane)
        title = f"mobile:{label}"
        resolved.append((pane, label, title))

    popup_mode = popup_override if popup_override is not None else bool(getattr(mobile_cfg, "popup_mode", False))
    if popup_mode and not os.environ.get("TMUX"):
        click.echo("[yellow]⚠️  No active tmux client detected; launching Happy in a pane instead of popup.[/yellow]")
        popup_mode = False
    command = tmux_utils.build_env_command("happy", env)

    if popup_mode:
        labels = [label for _, label, _ in resolved] or ["primary"]
        label_text = ", ".join(labels)
        try:
            tmux_utils.display_popup(command, width="85%", height="90%")
            click.echo(f"🪟 Happy popup launched for {label_text}. Close it when connected.")
        except tmux_utils.TmuxError as exc:
            click.echo(f"❌ Failed to launch Happy popup: {exc}")
        return

    for pane, label, title in resolved:
        if title in existing_titles:
            click.echo(f"ℹ️  Happy already running for {label}; skipping.")
            continue

        new_pane = controller.open(
            "happy",
            target=pane.pane_id,
            vertical=vertical,
            focus=focus_flag,
            name=title,
            environment_override=env,
        )
        existing_titles.add(title)
        all_panes.append(new_pane)
        click.echo(f"✅ Happy ready for {label} in pane {new_pane.pane_id}.")


@click.group()
@click.pass_context
def tmux(ctx: click.Context) -> None:
    """🧭 Dopemux tmux controller utilities."""


@tmux.command("list")
@click.option("--session", help="Filter panes by tmux session name")
@click.pass_context
def list_panes(ctx: click.Context, session: Optional[str]) -> None:
    """List tmux panes visible to Dopemux."""

    controller = _get_controller(ctx)
    panes = controller.list_panes(session=session)
    if not panes:
        click.echo("No tmux panes detected.")
        return

    table = Table(title="Active tmux panes", show_lines=False, expand=False)
    table.add_column("Pane ID", style="cyan")
    table.add_column("Session", style="magenta")
    table.add_column("Window", style="green")
    table.add_column("Title", style="yellow")
    table.add_column("Command", style="white")
    table.add_column("Path", style="dim")
    table.add_column("Active", style="blue")

    for pane in panes:
        table.add_row(
            pane.pane_id,
            pane.session or "-",
            pane.window or "-",
            pane.title or "(untitled)",
            pane.command or "-",
            pane.path or "-",
            "✅" if pane.active else "",
        )

    console.print(table)


@tmux.command("open")
@click.argument("spec")
@click.option(
    "--target",
    help="Pane id/title/window to split (defaults to active pane)",
    shell_complete=_pane_shell_complete,
)
@click.option(
    "--vertical/--horizontal",
    default=False,
    help="Split vertically (side-by-side) or horizontally (stacked).",
)
@click.option("--name", help="Optional pane title to apply after launch")
@click.option(
    "--cwd",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Working directory for the new pane",
)
@click.option(
    "--command",
    "command_override",
    help="Override command when using a preset (:alias)",
)
@click.option(
    "--focus/--no-focus",
    "focus_flag",
    default=None,
    help="Control whether the new pane becomes active.",
)
@click.pass_context
def open_pane(
    ctx: click.Context,
    spec: str,
    target: Optional[str],
    vertical: bool,
    name: Optional[str],
    cwd: Optional[Path],
    command_override: Optional[str],
    focus_flag: Optional[bool],
) -> None:
    """Open a new pane using presets (:claude) or raw commands."""

    controller = _get_controller(ctx)
    pane = controller.open(
        spec,
        target=target,
        vertical=vertical,
        focus=focus_flag,
        name=name,
        cwd=str(cwd) if cwd else None,
        command_override=command_override,
    )
    click.echo(
        f"Opened pane {pane.pane_id} in {pane.session}:{pane.window} "
        f"({'active' if pane.active else 'background'})"
    )


@tmux.command("capture")
@click.argument("target", shell_complete=_pane_shell_complete)
@click.option("--lines", "-n", default=100, help="Number of lines to capture")
@click.option("--start", type=int, help="Start line (for range capture)")
@click.option("--end", type=int, help="End line (for range capture)")
@click.pass_context
def capture_pane_output(
    ctx: click.Context,
    target: str,
    lines: int,
    start: Optional[int],
    end: Optional[int],
) -> None:
    """Capture output from a tmux pane (useful for orchestrator to inspect agents)."""
    
    controller = _get_controller(ctx)
    pane = controller.resolve_pane(target)
    
    if not pane:
        click.echo(f"❌ Pane not found: {target}")
        return
    
    if start is not None:
        content = tmux_utils.get_pane_content(pane.pane_id, start, end or -1)
    else:
        content = tmux_utils.capture_pane(pane.pane_id, lines)
    
    click.echo(content)


@tmux.command("send")
@click.argument("target", shell_complete=_pane_shell_complete)
@click.argument("text", nargs=-1, required=True)
@click.option("--enter/--no-enter", default=True, help="Append Enter after sending")
@click.option("--raw", is_flag=True, help="Send text verbatim (no <KEY> parsing)")
@click.option(
    "--no-rate-limit",
    is_flag=True,
    help="Bypass controller rate limiting for this send operation",
)
@click.pass_context
def send_keys(
    ctx: click.Context,
    target: str,
    text: Tuple[str, ...],
    enter: bool,
    raw: bool,
    no_rate_limit: bool,
) -> None:
    """Send keystrokes or literal text to a pane."""

    controller = _get_controller(ctx)
    payload = " ".join(text)
    controller.send_keys(
        target,
        payload,
        enter=enter,
        raw=raw,
        respect_rate_limit=not no_rate_limit,
    )


@tmux.command("sessions")
@click.option("--attach/--no-attach", default=True, help="Attach after listing")
@click.option("--session", "session_name", help="Session to attach (defaults to dopemux or first)")
@click.pass_context
def list_sessions(ctx: click.Context, attach: bool, session_name: Optional[str]) -> None:
    """List tmux sessions and optionally attach/switch."""

    cfg_manager = _resolve_config_manager(ctx)
    tmux_cfg = cfg_manager.get_tmux_config()

    try:
        sessions = tmux_utils.list_sessions()
    except tmux_utils.TmuxError as exc:
        click.echo(f"❌ Unable to list tmux sessions: {exc}")
        return

    if not sessions:
        click.echo("ℹ️  No tmux sessions detected.")
        return

    table = Table(title="tmux Sessions", show_lines=False, expand=False)
    table.add_column("Session", style="cyan")
    table.add_column("Default", style="yellow")

    default_session = tmux_cfg.default_session or "dopemux"
    for name in sessions:
        table.add_row(name, "⭐" if name == default_session else "")

    console.print(table)

    if not attach:
        return

    session_env = os.environ.get("DOPEMUX_TMUX_SESSION")
    session_name = None
    if session_env:
        session_name = session_env.split(":")[0]
    else:
        try:
            panes = controller.backend.list_panes()
            active_pane = next((pane for pane in panes if pane.active), panes[0] if panes else None)
            if active_pane:
                session_name = active_pane.session
        except Exception:
            session_name = None

@tmux.command("theme")
@click.argument("preset", required=False, type=click.Choice(sorted(THEME_PRESETS.keys())))
@click.option("--apply", is_flag=True, help="Apply the theme to the active tmux session")
@click.pass_context
def preview_theme(ctx: click.Context, preset: Optional[str], apply: bool) -> None:
    """Preview available tmux themes and optionally apply them."""

    controller = _get_controller(ctx)
    cfg_manager = _resolve_config_manager(ctx)
    tmux_cfg = cfg_manager.get_tmux_config()

    if not preset:
        current = (tmux_cfg.theme or "muted").lower()
        console.print("\n[bold cyan]🎨 Dopemux tmux theme presets[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Preset")
        table.add_column("Status")
        table.add_column("Palette Highlights")

        for name in sorted(THEME_PRESETS.keys()):
            theme = THEME_PRESETS[name]
            status = "⭐ current" if name == current else ""
            accent = theme["status_palette"].get("accent", "")
            info = theme["status_palette"].get("info", "")
            alert = theme["status_palette"].get("alert", "")
            table.add_row(
                name,
                status,
                f"accent {accent} · info {info} · alert {alert}",
            )
        console.print(table)
        console.print(
            "\nUse `dopemux tmux theme <preset> --apply` inside tmux to switch, "
            "or set `tmux.theme = \"<preset>\"` in dopemux.toml for a permanent change.\n"
        )
        return

    theme = THEME_PRESETS[preset]
    console.print(f"[cyan]Previewing theme:[/cyan] [bold]{preset}[/bold]")
    console.print(f"Status palette: {theme['status_palette']}")

    if not apply:
        console.print("\n[yellow]Tip:[/yellow] Run again with --apply from inside tmux to apply live.")
        return

    session_env = os.environ.get("DOPEMUX_TMUX_SESSION")
    session_name = None
    if session_env:
        session_name = session_env.split(":")[0]
    else:
        try:
            panes = controller.backend.list_panes()
            active_pane = next((pane for pane in panes if pane.active), panes[0] if panes else None)
            if active_pane:
                session_name = active_pane.session
        except Exception:
            session_name = None

    if not session_name:
        console.print("[red]❌ No active tmux session detected. Use --apply from inside tmux.[/red]")
        return

    try:
        _apply_theme_to_session(controller, session_name, theme)
        console.print(f"[green]✅ Applied '{preset}' theme to session {session_name}.[/green]")
    except Exception as exc:  # pragma: no cover - tmux errors are environment-specific
        console.print(f"[red]❌ Unable to apply theme: {exc}[/red]")
    target = session_name or (default_session if default_session in sessions else sessions[0])
    if target not in sessions:
        click.echo(f"❌ Session '{target}' not found; skipping attach.")
        return

    inside_tmux = bool(os.environ.get("TMUX"))
    if inside_tmux:
        click.echo(f"🔁 Switching to tmux session '{target}'...")
        tmux_utils.switch_client(target)
    else:
        click.echo(f"🔗 Attaching to tmux session '{target}'...")
        tmux_utils.attach_session(target)


def _happy_label(pane: Optional[PaneInfo]) -> str:
    if pane is None:
        return "primary"
    base = pane.title or pane.window or pane.pane_id
    cleaned = base.replace("mobile:", "").strip() or pane.pane_id
    return cleaned


def _prepare_orchestrator_base(
    controller: TmuxController,
    session: str,
    start_dir: str,
    *,
    window_name: str,
    created_new_session: bool,
) -> PaneInfo:
    """Ensure the orchestrator window starts from a single clean pane."""

    shell_cmd = os.environ.get("SHELL", "/bin/bash")
    current_pane_id = os.environ.get("TMUX_PANE")
    panes = controller.backend.list_panes()
    current_pane = (
        next((pane for pane in panes if pane.pane_id == current_pane_id), None)
        if current_pane_id
        else None
    )
    target_is_current = (
        current_pane is not None
        and current_pane.session == session
        and current_pane.window == window_name
    )

    base_pane: Optional[PaneInfo]
    if not target_is_current:
        recreated_session = False
        # If we just created the session, the window already exists with the correct name
        if not created_new_session:
            try:
                tmux_utils.kill_window(session, window_name)
            except tmux_utils.TmuxError:
                pass
            else:
                # Killing the final window implicitly destroys the session; recreate it so splits work.
                if not tmux_utils.session_exists(session):
                    tmux_utils.create_session(
                        session,
                        start_directory=start_dir,
                        window_name=window_name,
                    )
                    recreated_session = True
        
        # Only create new window if we didn't just create the session
        if created_new_session or recreated_session:
            # Use the existing window from session creation/recreation
            tmux_utils.select_window(session, window_name)
            # Get the pane from the window we created
            refreshed = controller.backend.list_panes()
            base_pane = next(
                (pane for pane in refreshed if pane.session == session and pane.window == window_name),
                None,
            )
            if base_pane is None:
                raise click.ClickException("Unable to find pane in newly created session")
        else:
            pane_id = tmux_utils.new_window(
                window_name,
                shell_cmd,
                session=session,
                start_directory=start_dir,
                attach=False,
            )
            tmux_utils.select_window(session, window_name)
            base_pane = controller.resolve_pane(pane_id)
    else:
        # When invoked from inside the orchestrator window, reuse the active pane
        base_pane = current_pane
        for pane in panes:
            if (
                pane.session == session
                and pane.window == window_name
                and pane.pane_id != base_pane.pane_id
            ):
                try:
                    controller.backend.kill_pane(pane.pane_id)
                except Exception:
                    pass
        tmux_utils.select_window(session, window_name)

    if created_new_session:
        # Window was already created with the correct name, no need to kill "main"
        pass

    if base_pane is None:
        refreshed = controller.backend.list_panes()
        base_pane = next(
            (pane for pane in refreshed if pane.session == session and pane.window == window_name),
            None,
        )
    if base_pane is None:
        raise click.ClickException("Unable to prepare orchestrator tmux window.")
    return base_pane


def _setup_orchestrator_layout(
    controller: TmuxController,
    session: str,
    base_pane: PaneInfo,
    start_dir: str,
    config,
    dual_agent: bool,
) -> OrchestratorLayout:
    shell_cmd = os.environ.get("SHELL", "/bin/bash")
    theme = _resolve_theme(config)
    pane_palette = theme.get("pane_styles", {})
    border_palette = theme.get("pane_border_styles", {})
    status_palette = theme.get("status_palette", {})

    # Apply session-wide visual defaults before splitting
    try:
        tmux_utils.set_session_option(session, "status", "on")
        tmux_utils.set_session_option(session, "status-interval", "2")
        tmux_utils.set_session_option(session, "status-left-length", "80")
        tmux_utils.set_session_option(session, "status-right-length", "140")
        _apply_status_theme(session, theme)
        default_border_fg = status_palette.get("foreground", "#cdd6f4")
        default_border_bg = status_palette.get("background", "#11111b")
        tmux_utils.set_session_option(
            session,
            "pane-border-style",
            f"fg={default_border_fg},bg={default_border_bg}",
        )
        tmux_utils.set_session_option(
            session,
            "window-style",
            f"bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "window-active-style",
            f"bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "@dopemux_title_fg",
            status_palette.get("foreground", "#cdd6f4"),
        )
        tmux_utils.set_session_option(
            session,
            "@dopemux_title_bg",
            status_palette.get("background", "#1e1e2e"),
        )
    except Exception:
        pass

    # Create bottom agent band (new pane below base). Reserve ~30% height for agents.
    agent_pane_id = controller.backend.split_window(
        target=base_pane.pane_id,
        command=shell_cmd,
        vertical=True,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=30,
    )

    top_band_id = base_pane.pane_id

    # Split top band into monitors (top 35%) and middle layer (orchestrator + sandbox 65%)
    middle_band_id = controller.backend.split_window(
        target=top_band_id,
        command=shell_cmd,
        vertical=True,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=65,
    )

    top_monitors_id = top_band_id
    
    # Split middle band into orchestrator (approx 70%) and sandbox (30%)
    sandbox_id = controller.backend.split_window(
        target=middle_band_id,
        command=shell_cmd,
        vertical=False,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=30,
    )
    
    orchestrator_id = middle_band_id

    # Hard-enforce a single orchestrator pane in session by killing extras
    try:
        existing = controller.backend.list_panes()
        for p in existing:
            if (p.title or "").strip() == "orchestrator:control" and p.pane_id != orchestrator_id:
                try:
                    controller.backend.kill_pane(p.pane_id)
                except Exception:
                    pass
    except Exception:
        pass

    # Split monitors into two columns (60% / 40%)
    monitor_right_id = controller.backend.split_window(
        target=top_monitors_id,
        command=shell_cmd,
        vertical=False,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=40,
    )

    # Always target window index 0 to avoid pane-id confusion
    window_name = "0"
    click.echo(f"[dim]Debug: base_pane.window={base_pane.window}, pane_id={base_pane.pane_id}[/dim]")
    try:
        tmux_utils.rename_window(session, window_name, "dopemux")
    except Exception as e:
        click.echo(f"[dim]Note: Could not rename window: {e}[/dim]")

    # Build bottom row: agent:primary | agent:secondary (if enabled)
    secondary_agent_id: Optional[str] = None
    if dual_agent:
        # Split bottom band to create secondary agent on the right
        secondary_agent_id = controller.backend.split_window(
            target=agent_pane_id,
            command=shell_cmd,
            vertical=False,
            start_directory=start_dir,
            focus=False,
            environment={},
            session=session,
            percent=50,
        )

    pane_titles = [
        (top_monitors_id, "monitor:worktree"),
        (monitor_right_id, "monitor:logs"),
        (orchestrator_id, "orchestrator:control"),
        (sandbox_id, "sandbox:shell"),
        (agent_pane_id, "agent:primary"),
    ]
    if secondary_agent_id:
        pane_titles.append((secondary_agent_id, "agent:secondary"))

    for pane_id, title in pane_titles:
        short_key = title.split(":")[0] if ":" in title else title
        tmux_utils.set_pane_title(pane_id, title)
        style = pane_palette.get(title) or pane_palette.get(short_key)
        if style:
            try:
                tmux_utils.set_pane_style(pane_id, style)
            except Exception:
                pass
        border_style = border_palette.get(title) or border_palette.get(short_key)
        if border_style:
            try:
                tmux_utils.set_pane_border_style(pane_id, border_style)
            except Exception:
                pass

    monitor_commands = getattr(config, "monitor_commands", {}) or {}

    def _prepare_monitor_command(raw: str) -> str:
        raw = (raw or "").strip()
        if not raw:
            return ""
        if raw.startswith("tail"):
            return raw
        if shutil.which("watch") and raw.startswith("watch"):
            return raw
        interval = 8
        return f"while true; do clear; {raw}; sleep {interval}; done"

    for pane_id, title in pane_titles:
        cmd = monitor_commands.get(title)
        if cmd:
            prepared = _prepare_monitor_command(cmd)
            if prepared:
                try:
                    controller.send_keys(
                        pane_id,
                        prepared,
                        enter=True,
                        raw=True,
                        respect_rate_limit=False,
                    )
                except Exception:
                    pass
        else:
            if title.startswith("monitor:"):
                placeholder = (
                    f"clear; printf '📊 Configure monitor_commands[\"{title}\"] in dopemux.toml.\\n'"
                )
                controller.send_keys(
                    pane_id,
                    placeholder,
                    enter=True,
                    raw=True,
                    respect_rate_limit=False,
                )

    orchestrator_cmd = (
        getattr(config, "orchestrator_command", None) or "dopemux start --role orchestrator --no-recovery"
    )
    if orchestrator_cmd:
        # Build orchestrator environment with LiteLLM configuration if enabled
        litellm_env_orch = ""
        if os.environ.get("DOPEMUX_CLAUDE_VIA_LITELLM") == "true":
            litellm_master_key = os.environ.get("DOPEMUX_LITELLM_MASTER_KEY", "")
            litellm_db_url = os.environ.get("DOPEMUX_LITELLM_DB_URL", "")
            litellm_env_orch = (
                f"export DOPEMUX_CLAUDE_VIA_LITELLM=true; "
                f"export ANTHROPIC_BASE_URL=http://localhost:4000; "
                f"export ANTHROPIC_API_KEY={shlex.quote(litellm_master_key)}; "
                f"export LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
                f"export DOPEMUX_LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
                f"export DOPEMUX_LITELLM_DB_URL={shlex.quote(litellm_db_url)}; "
                f"export LITELLM_DATABASE_URL={shlex.quote(litellm_db_url)}; "
                f"export DATABASE_URL={shlex.quote(litellm_db_url)}; "
                f"export CLAUDE_CODE_ROUTER_PROVIDER=litellm; "
                f"export CLAUDE_CODE_ROUTER_UPSTREAM_URL={shlex.quote(os.environ.get('CLAUDE_CODE_ROUTER_UPSTREAM_URL', ''))}; "
                f"export CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR=DOPEMUX_LITELLM_MASTER_KEY; "
                f"export CLAUDE_CODE_ROUTER_MODELS={shlex.quote(os.environ.get('CLAUDE_CODE_ROUTER_MODELS', ''))}; "
            )
        
        orchestrator_prefix = (
            f"{litellm_env_orch}"
            f"export DOPEMUX_DEFAULT_LITELLM=1; "
            f"export DOPEMUX_TMUX_SESSION={session}; "
            f"unset DOPEMUX_NON_INTERACTIVE; "
            f"export DOPEMUX_AGENT_ROLE=orchestrator; "
            f"export DOPEMUX_SANDBOX_PANE={sandbox_id}; "
            f"export DOPEMUX_AGENT_PANE={agent_pane_id}; "
        )
        orchestrator_payload = (
            f"{orchestrator_prefix}"
            "clear; printf '🤖 Launching Orchestrator Claude...\\n'; "
            f"{orchestrator_cmd}"
        )
        controller.send_keys(
            orchestrator_id,
            orchestrator_payload,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )

    sandbox_cmd = getattr(config, "sandbox_command", None)
    if sandbox_cmd:
        sandbox_prefix = f"export DOPEMUX_TMUX_SESSION={session}; "
        sandbox_payload = (
            f"{sandbox_prefix}"
            "clear; printf '🧪 Sandbox shell ready. Orchestrator can target pane $DOPEMUX_SANDBOX_PANE.\\n'; "
            f"{sandbox_cmd}"
        )
        controller.send_keys(
            sandbox_id,
            sandbox_payload,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )
    else:
        controller.send_keys(
            sandbox_id,
            "clear; printf '🧪 Sandbox shell ready. Orchestrator can target pane $DOPEMUX_SANDBOX_PANE.\n'",
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )

    agent_hint = "clear; printf '🟢 Ready for new agent. Run `dopemux start` when needed.\n'"
    
    # Auto-start agent with role configuration
    agent_cmd = getattr(config, "agent_command", None) or "dopemux start --role agent"
    
    # Build agent environment with LiteLLM configuration if enabled
    litellm_env = ""
    if os.environ.get("DOPEMUX_CLAUDE_VIA_LITELLM") == "true":
        litellm_master_key = os.environ.get("DOPEMUX_LITELLM_MASTER_KEY", "")
        litellm_db_url = os.environ.get("DOPEMUX_LITELLM_DB_URL", "")
        litellm_env = (
            f"export DOPEMUX_CLAUDE_VIA_LITELLM=true; "
            f"export ANTHROPIC_BASE_URL=http://localhost:4000; "
            f"export ANTHROPIC_API_KEY={shlex.quote(litellm_master_key)}; "
            f"export LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
            f"export DOPEMUX_LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
            f"export DOPEMUX_LITELLM_DB_URL={shlex.quote(litellm_db_url)}; "
            f"export LITELLM_DATABASE_URL={shlex.quote(litellm_db_url)}; "
            f"export DATABASE_URL={shlex.quote(litellm_db_url)}; "
        )
    
    agent_prefix = (
        f"{litellm_env}"
        f"export DOPEMUX_DEFAULT_LITELLM=1; "
        f"export DOPEMUX_TMUX_SESSION={session}; "
        f"unset DOPEMUX_NON_INTERACTIVE; "
        f"export DOPEMUX_AGENT_ROLE=primary; "
        f"export DOPEMUX_ORCHESTRATOR_PANE={orchestrator_id}; "
    )
    agent_payload = (
        f"{agent_prefix}"
        "clear; printf '🟢 Primary agent booting...\\n'; "
        f"{agent_cmd}"
    )
    controller.send_keys(
        agent_pane_id,
        agent_payload,
        enter=True,
        raw=True,
        respect_rate_limit=False,
    )

    if secondary_agent_id:
        secondary_cmd = getattr(config, "secondary_agent_command", None) or "dopemux start --role secondary"
        secondary_prefix = (
            f"{litellm_env}"
            f"export DOPEMUX_DEFAULT_LITELLM=1; "
            f"export DOPEMUX_TMUX_SESSION={session}; "
            f"export DOPEMUX_NON_INTERACTIVE=1; "
            f"export DOPEMUX_AGENT_ROLE=secondary; "
            f"export DOPEMUX_ORCHESTRATOR_PANE={orchestrator_id}; "
            f"export DOPEMUX_PRIMARY_AGENT_PANE={agent_pane_id}; "
        )
        secondary_payload = (
            f"{secondary_prefix}"
            "clear; printf '🟡 Secondary agent booting...\\n'; "
            f"{secondary_cmd}"
        )
        controller.send_keys(
            secondary_agent_id,
            secondary_payload,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )

    tmux_utils.focus_pane(agent_pane_id)

    return OrchestratorLayout(
        monitors=[top_monitors_id, monitor_right_id],
        orchestrator=orchestrator_id,
        agent=agent_pane_id,
        sandbox=sandbox_id,
        secondary_agent=secondary_agent_id,
    )


def _setup_dope_layout(
    controller: TmuxController,
    session: str,
    base_pane: PaneInfo,
    start_dir: str,
    config,
    dual_agent: bool,
    bootstrap: bool,
) -> OrchestratorLayout:
    shell_cmd = os.environ.get("SHELL", "/bin/bash")
    theme = _resolve_theme(config)
    pane_palette = theme.get("pane_styles", {})
    border_palette = theme.get("pane_border_styles", {})
    status_palette = theme.get("status_palette", {})

    try:
        tmux_utils.set_session_option(session, "status", "on")
        tmux_utils.set_session_option(session, "status-interval", "2")
        tmux_utils.set_session_option(session, "status-left-length", "80")
        tmux_utils.set_session_option(session, "status-right-length", "160")
        _apply_status_theme(session, theme)
        default_border_fg = status_palette.get("foreground", "#cdd6f4")
        default_border_bg = status_palette.get("background", "#11111b")
        tmux_utils.set_session_option(
            session,
            "pane-border-style",
            f"fg={default_border_fg},bg={default_border_bg}",
        )
        tmux_utils.set_session_option(
            session,
            "window-style",
            f"bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "window-active-style",
            f"bg={status_palette.get('background', '#11111b')}",
        )
        tmux_utils.set_session_option(
            session,
            "@dopemux_title_fg",
            status_palette.get("foreground", "#cdd6f4"),
        )
        tmux_utils.set_session_option(
            session,
            "@dopemux_title_bg",
            status_palette.get("background", "#1e1e2e"),
        )
    except Exception:
        pass

    # Create top row with metrics bar (15% height, horizontal split for 1/3 width)
    top_row_id = controller.backend.split_window(
        target=base_pane.pane_id,
        command=shell_cmd,
        vertical=True,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=15,
    )

    # Split top row horizontally into 3 parts, metrics bar is 1/3 width
    metrics_placeholder_1 = controller.backend.split_window(
        target=top_row_id,
        command=shell_cmd,
        vertical=False,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=33,
    )

    metrics_placeholder_2 = controller.backend.split_window(
        target=top_row_id,
        command=shell_cmd,
        vertical=False,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=50,
    )

    metrics_bar_id = top_row_id  # The remaining 1/3 is metrics bar

    # Now work with the remaining space (85% height)
    remaining_id = base_pane.pane_id

    # Create bottom band for agents (~25% of remaining height)
    agent_pane_id = controller.backend.split_window(
        target=remaining_id,
        command=shell_cmd,
        vertical=True,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=25,
    )

    # Middle section (~75% of remaining)
    middle_section_id = remaining_id

    # Create middle band within middle section (~60% height)
    middle_band_id = controller.backend.split_window(
        target=middle_section_id,
        command=shell_cmd,
        vertical=True,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=70,
    )

    # Monitors section (~30% of middle section)
    monitors_section_id = middle_section_id

    # Split monitors horizontally into 3 equal columns
    monitor_1_id = controller.backend.split_window(
        target=monitors_section_id,
        command=shell_cmd,
        vertical=False,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=33,
    )

    monitor_2_id = controller.backend.split_window(
        target=monitors_section_id,
        command=shell_cmd,
        vertical=False,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=50,
    )

    monitor_3_id = monitors_section_id  # Remaining third

    # Split middle band into orchestrator (75%) and sandbox (25%)
    # Increased orchestrator from 70% to 75% for more content space
    sandbox_id = controller.backend.split_window(
        target=middle_band_id,
        command=shell_cmd,
        vertical=False,
        start_directory=start_dir,
        focus=False,
        environment={},
        session=session,
        percent=25,
    )
    orchestrator_id = middle_band_id

    # Hard-enforce a single orchestrator pane in session by killing extras
    try:
        existing = controller.backend.list_panes()
        for p in existing:
            if (p.title or "").strip() == "orchestrator:control" and p.pane_id != orchestrator_id:
                try:
                    controller.backend.kill_pane(p.pane_id)
                except Exception:
                    pass
    except Exception:
        pass

    window_name = "0"
    click.echo(f"[dim]Debug: base_pane.window={base_pane.window}, pane_id={base_pane.pane_id}[/dim]")
    try:
        tmux_utils.rename_window(session, window_name, "dopemux")
    except Exception as exc:
        click.echo(f"[dim]Note: Could not rename window: {exc}[/dim]")

    secondary_agent_id: Optional[str] = None
    if dual_agent:
        secondary_agent_id = controller.backend.split_window(
            target=agent_pane_id,
            command=shell_cmd,
            vertical=False,
            start_directory=start_dir,
            focus=False,
            environment={},
            session=session,
            percent=50,
        )

    pane_titles = [
        (monitor_1_id, "📊 monitor:adhd"),
        (monitor_2_id, "⚙️ monitor:system"),
        (monitor_3_id, "🔍 monitor:worktree"),
        (orchestrator_id, "🎯 orchestrator:control"),
        (sandbox_id, "🎮 sandbox:shell"),
        (agent_pane_id, "🤖 agent:primary"),
        (metrics_bar_id, "📈 metrics:bar"),
        (metrics_placeholder_1, "metrics:spacer1"),
        (metrics_placeholder_2, "metrics:spacer2"),
    ]
    if secondary_agent_id:
        pane_titles.append((secondary_agent_id, "🤖 agent:secondary"))

    for pane_id, title in pane_titles:
        short_key = title.split(":")[0] if ":" in title else title
        tmux_utils.set_pane_title(pane_id, title)
        style = pane_palette.get(title) or pane_palette.get(short_key)
        if style:
            try:
                tmux_utils.set_pane_style(pane_id, style)
            except Exception:
                pass
        border_style = border_palette.get(title) or border_palette.get(short_key)
        if border_style:
            try:
                tmux_utils.set_pane_border_style(pane_id, border_style)
            except Exception:
                pass

    python_exec = sys.executable or shutil.which("python3") or "python3"
    python_cmd = shlex.quote(python_exec)
    project_dir = shlex.quote(start_dir)

    if bootstrap:
        dashboard_left_cmd = (
            f"cd {project_dir}; "
            "clear; printf '💡 Loading Neon dashboard (implementation) ...\\n'; "
            "export NEON_DASHBOARD_PANE_ROLE=left; "
            f"{python_cmd} scripts/neon_dashboard/core/app.py"
        )
        controller.send_keys(
            monitor_1_id,
            dashboard_left_cmd,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )

        dashboard_right_cmd = (
            f"cd {project_dir}; "
            "clear; printf '🧭 Loading Neon dashboard (system/PM) ...\\n'; "
            "export NEON_DASHBOARD_PANE_ROLE=right; "
            f"{python_cmd} scripts/neon_dashboard/core/app.py"
        )
        controller.send_keys(
            monitor_2_id,
            dashboard_right_cmd,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )

        metrics_cmd = (
            f"cd {project_dir}; "
            "while true; do clear; dopemux health; sleep 10; done"
        )
        controller.send_keys(
            metrics_bar_id,
            metrics_cmd,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )
    else:
        for pane_id in (monitor_1_id, monitor_2_id, monitor_3_id, metrics_bar_id):
            controller.send_keys(
                pane_id,
                "clear; printf '🟢 Dope layout pane ready. Run dashboard manually when ready.\\n'",
                enter=True,
                raw=True,
                respect_rate_limit=False,
            )

    if bootstrap:
        orchestrator_cmd = (
            getattr(config, "orchestrator_command", None) or "dopemux start --role orchestrator --no-recovery"
        )
        if orchestrator_cmd:
            # Build orchestrator environment with LiteLLM configuration if enabled
            litellm_env_orch = ""
            if os.environ.get("DOPEMUX_CLAUDE_VIA_LITELLM") == "true":
                litellm_master_key = os.environ.get("DOPEMUX_LITELLM_MASTER_KEY", "")
                litellm_db_url = os.environ.get("DOPEMUX_LITELLM_DB_URL", "")
                litellm_env_orch = (
                    f"export DOPEMUX_CLAUDE_VIA_LITELLM=true; "
                    f"export ANTHROPIC_BASE_URL=http://localhost:4000; "
                    f"export ANTHROPIC_API_KEY={shlex.quote(litellm_master_key)}; "
                    f"export LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
                    f"export DOPEMUX_LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
                    f"export DOPEMUX_LITELLM_DB_URL={shlex.quote(litellm_db_url)}; "
                    f"export LITELLM_DATABASE_URL={shlex.quote(litellm_db_url)}; "
                    f"export DOPEMUX_LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
                    f"export DOPEMUX_LITELLM_DB_URL={shlex.quote(litellm_db_url)}; "
                    f"export LITELLM_DATABASE_URL={shlex.quote(litellm_db_url)}; "
                    f"export DATABASE_URL={shlex.quote(litellm_db_url)}; "
                    f"export CLAUDE_CODE_ROUTER_PROVIDER=litellm; "
                    f"export CLAUDE_CODE_ROUTER_UPSTREAM_URL={shlex.quote(os.environ.get('CLAUDE_CODE_ROUTER_UPSTREAM_URL', ''))}; "
                    f"export CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR=DOPEMUX_LITELLM_MASTER_KEY; "
                    f"export CLAUDE_CODE_ROUTER_MODELS={shlex.quote(os.environ.get('CLAUDE_CODE_ROUTER_MODELS', ''))}; "
                )
            
            orchestrator_prefix = (
                f"{litellm_env_orch}"
                f"export DOPEMUX_DEFAULT_LITELLM=1; "
                f"export DOPEMUX_TMUX_SESSION={session}; "
                f"unset DOPEMUX_NON_INTERACTIVE; "
                f"export DOPEMUX_AGENT_ROLE=orchestrator; "
                f"export DOPEMUX_SANDBOX_PANE={sandbox_id}; "
                f"export DOPEMUX_AGENT_PANE={agent_pane_id}; "
            )
            orchestrator_payload = (
                f"{orchestrator_prefix}"
                "clear; printf '🤖 Launching Orchestrator Claude...\\n'; "
                f"{orchestrator_cmd}"
            )
            controller.send_keys(
                orchestrator_id,
                orchestrator_payload,
                enter=True,
                raw=True,
                respect_rate_limit=False,
            )

    sandbox_cmd = getattr(config, "sandbox_command", None)
    if bootstrap and sandbox_cmd:
        sandbox_prefix = f"export DOPEMUX_TMUX_SESSION={session}; "
        sandbox_payload = (
            f"{sandbox_prefix}"
            "clear; printf '🧪 Sandbox shell ready. Orchestrator can target pane $DOPEMUX_SANDBOX_PANE.\\n'; "
            f"{sandbox_cmd}"
        )
        controller.send_keys(
            sandbox_id,
            sandbox_payload,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )
    else:
        controller.send_keys(
            sandbox_id,
            "clear; printf '🧪 Sandbox shell ready. Orchestrator can target pane $DOPEMUX_SANDBOX_PANE.\\n'",
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )

    if bootstrap:
        agent_cmd = getattr(config, "agent_command", None) or "dopemux start --role agent"
        
        # Build agent environment with LiteLLM configuration if enabled
        litellm_env_agent = ""
        if os.environ.get("DOPEMUX_CLAUDE_VIA_LITELLM") == "true":
            litellm_master_key = os.environ.get("DOPEMUX_LITELLM_MASTER_KEY", "")
            litellm_db_url = os.environ.get("DOPEMUX_LITELLM_DB_URL", "")
            litellm_env_agent = (
                f"export DOPEMUX_CLAUDE_VIA_LITELLM=true; "
                f"export ANTHROPIC_BASE_URL=http://localhost:4000; "
                f"export ANTHROPIC_API_KEY={shlex.quote(litellm_master_key)}; "
                f"export LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
                f"export DOPEMUX_LITELLM_MASTER_KEY={shlex.quote(litellm_master_key)}; "
                f"export DOPEMUX_LITELLM_DB_URL={shlex.quote(litellm_db_url)}; "
                f"export LITELLM_DATABASE_URL={shlex.quote(litellm_db_url)}; "
                f"export DATABASE_URL={shlex.quote(litellm_db_url)}; "
                f"export CLAUDE_CODE_ROUTER_PROVIDER=litellm; "
                f"export CLAUDE_CODE_ROUTER_UPSTREAM_URL={shlex.quote(os.environ.get('CLAUDE_CODE_ROUTER_UPSTREAM_URL', ''))}; "
                f"export CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR=DOPEMUX_LITELLM_MASTER_KEY; "
                f"export CLAUDE_CODE_ROUTER_MODELS={shlex.quote(os.environ.get('CLAUDE_CODE_ROUTER_MODELS', ''))}; "
            )
        
        agent_prefix = (
            f"{litellm_env_agent}"
            f"export DOPEMUX_DEFAULT_LITELLM=1; "
            f"export DOPEMUX_TMUX_SESSION={session}; "
            f"export DOPEMUX_NON_INTERACTIVE=1; "
            f"export DOPEMUX_AGENT_ROLE=primary; "
            f"export DOPEMUX_ORCHESTRATOR_PANE={orchestrator_id}; "
        )
        agent_payload = (
            f"{agent_prefix}"
            "clear; printf '🟢 Primary agent booting...\\n'; "
            f"{agent_cmd}"
        )
        controller.send_keys(
            agent_pane_id,
            agent_payload,
            enter=True,
            raw=True,
            respect_rate_limit=False,
        )

        if secondary_agent_id:
            secondary_cmd = getattr(config, "secondary_agent_command", None) or "dopemux start --role secondary"
            secondary_prefix = (
                f"{litellm_env_agent}"
                f"export DOPEMUX_DEFAULT_LITELLM=1; "
                f"export DOPEMUX_TMUX_SESSION={session}; "
                f"export DOPEMUX_NON_INTERACTIVE=1; "
                f"export DOPEMUX_AGENT_ROLE=secondary; "
                f"export DOPEMUX_ORCHESTRATOR_PANE={orchestrator_id}; "
                f"export DOPEMUX_PRIMARY_AGENT_PANE={agent_pane_id}; "
            )
            secondary_payload = (
                f"{secondary_prefix}"
                "clear; printf '🟡 Secondary agent booting...\\n'; "
                f"{secondary_cmd}"
            )
            controller.send_keys(
                secondary_agent_id,
                secondary_payload,
                enter=True,
                raw=True,
                respect_rate_limit=False,
            )

    tmux_utils.focus_pane(agent_pane_id)

    return OrchestratorLayout(
        monitors=[monitor_1_id, monitor_2_id, monitor_3_id],
        orchestrator=orchestrator_id,
        agent=agent_pane_id,
        sandbox=sandbox_id,
        secondary_agent=secondary_agent_id,
        metrics_bar=metrics_bar_id,
    )


@tmux.command("happy")
@click.option(
    "--pane",
    "pane_targets",
    multiple=True,
    help="Pane id/title/window to mirror (defaults to active pane)",
    shell_complete=_pane_shell_complete,
)
@click.option(
    "--vertical/--horizontal",
    default=False,
    help="Split vertically (side-by-side) or horizontally (stacked).",
)
@click.option(
    "--focus/--no-focus",
    "focus_flag",
    default=False,
    help="Control whether the Happy pane becomes active (default: no focus).",
)
@click.option(
    "--popup/--pane",
    "popup_mode",
    default=None,
    help="Launch Happy inside a tmux popup instead of creating a pane.",
)
@click.pass_context
def launch_happy(
    ctx: click.Context,
    pane_targets: Tuple[str, ...],
    vertical: bool,
    focus_flag: bool,
    popup_mode: Optional[bool],
) -> None:
    """Launch Happy CLI in new tmux panes anchored to target panes."""

    controller = _get_controller(ctx)
    cfg_manager = _resolve_config_manager(ctx)

    ok, _ = ensure_dependency("happy")
    if not ok:
        click.echo("❌ Happy CLI not found. Install with: npm i -g happy-coder")
        return

    targets = list(pane_targets) or [None]
    _launch_happy_for_targets(
        controller,
        cfg_manager,
        targets,
        vertical=vertical,
        focus_flag=focus_flag,
        popup_override=popup_mode,
    )


@tmux.command("capture")
@click.argument("target")
@click.option("--lines", type=int, help="Limit output to the most recent N lines")
@click.pass_context
def capture_output(
    ctx: click.Context,
    target: str,
    lines: Optional[int],
) -> None:
    """Capture recent output from a tmux pane."""

    controller = _get_controller(ctx)
    output = controller.capture(target, lines=lines)
    click.echo(output)


@tmux.command("close")
@click.option(
    "--pane",
    "pane_target",
    help="Pane id/title/window to close (defaults to active)",
    shell_complete=_pane_shell_complete,
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def close_pane(ctx: click.Context, pane_target: Optional[str], force: bool) -> None:
    """Close a tmux pane controlled by Dopemux."""

    controller = _get_controller(ctx)
    pane = controller.resolve_pane(pane_target)
    if pane is None:
        label = pane_target or "active"
        click.echo(f"❌ Pane not found: {label}")
        return

    if not force:
        confirm = Confirm.ask(
            f"Close pane {pane.pane_id} ({pane.session}:{pane.window})?",
            default=False,
        )
        if not confirm:
            click.echo("Cancelled.")
            return

    controller.close_pane(pane.pane_id)
    click.echo(f"🗑️ Closed pane {pane.pane_id} ({pane.session}:{pane.window}).")


@tmux.command("stop")
@click.option("--session", "session_name", help="tmux session to kill (defaults to dopemux)")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def stop_session(ctx: click.Context, session_name: Optional[str], force: bool) -> None:
    """Stop a Dopemux tmux session."""

    cfg_manager = _resolve_config_manager(ctx)
    controller = _get_controller(ctx)
    tmux_cfg = cfg_manager.get_tmux_config()
    target_session = session_name or tmux_cfg.default_session or "dopemux"

    if not force:
        confirm = Confirm.ask(
            f"Kill tmux session '{target_session}'?",
            default=False,
        )
        if not confirm:
            click.echo("Cancelled.")
            return

    try:
        controller.close_session(target_session)
        click.echo(f"🛑 Session '{target_session}' terminated.")
    except Exception as exc:
        click.echo(f"❌ Failed to stop session: {exc}")


@tmux.group("agent")
def agent_group() -> None:
    """Agent pane utilities."""


@agent_group.command("switch-role")
@click.argument("role")
@click.option("--session", help="tmux session name (default: dopemux)")
@click.option("--pane", help="Explicit pane id (e.g. %27)")
@click.option(
    "--target",
    type=click.Choice(["primary", "secondary"]),
    default="primary",
    help="Choose which agent pane to retarget (ignored if --pane is provided)",
)
@click.option("--extra", help="Additional arguments to append to dopemux start", default="")
@click.option(
    "--recovery/--no-recovery",
    default=False,
    help="Include worktree recovery menu when relaunching (default: --no-recovery)",
)
@click.pass_context
def agent_switch_role(
    ctx: click.Context,
    role: str,
    session: Optional[str],
    pane: Optional[str],
    target: str,
    extra: str,
    recovery: bool,
) -> None:
    """Switch an agent pane to a different role."""

    try:
        spec = resolve_role(role)
    except RoleNotFoundError:
        available = ", ".join(sorted({*available_roles()}))
        click.echo(f"❌ Unknown role '{role}'. Available: {available}")
        return

    cfg_manager = _resolve_config_manager(ctx)
    tmux_cfg = cfg_manager.get_tmux_config()
    session_name = session or tmux_cfg.default_session or "dopemux"

    controller = _get_controller(ctx)

    target_pane = pane
    panes = controller.backend.list_panes()
    if not target_pane:
        desired_prefix = "agent:secondary" if target == "secondary" else "agent:primary"
        for pane_info in panes:
            if pane_info.session == session_name and pane_info.title and pane_info.title.startswith(desired_prefix):
                target_pane = pane_info.pane_id
                break

    if not target_pane:
        click.echo(
            f"❌ Could not find agent pane (session '{session_name}', target '{target}')"
        )
        return

    config = cfg_manager.load_config()
    available_servers = set(config.mcp_servers.keys())
    required_servers = set(spec.required_servers or []) | {"conport"}
    optional_servers = set(spec.optional_servers or [])

    missing_required = sorted(s for s in required_servers if s not in available_servers)
    missing_optional = sorted(s for s in optional_servers if s not in available_servers)

    if missing_required:
        services_argument = ",".join(missing_required)
        click.echo(
            f"⚠ Required MCP servers unavailable for role '{spec.label}': {', '.join(missing_required)}"
        )
        click.echo(
            f"💡 Start them with: dopemux mcp up --services {services_argument}"
        )
    if missing_optional:
        click.echo(
            f"ℹ Optional MCP servers not running: {', '.join(missing_optional)}"
        )

    # Interrupt current process in pane
    try:
        controller.send_key(target_pane, "C-c")
        controller.send_key(target_pane, "Enter")
    except Exception:
        pass

    command = [
        "clear",
        f"printf '🎭 Switching agent to role {spec.label} ({spec.key})\\n'",
        f"dopemux start --role {spec.key}"
    ]

    if not recovery:
        command[-1] += " --no-recovery"
    if extra.strip():
        command[-1] += f" {extra.strip()}"

    payload = "; ".join(command)

    controller.send_keys(
        target_pane,
        payload,
        enter=True,
        raw=True,
        respect_rate_limit=False,
    )
    try:
        tmux_utils.focus_pane(target_pane)
    except Exception:
        pass

    click.echo(
        f"😀 Requested role switch in pane {target_pane}: {spec.label} ({spec.key})"
    )
@tmux.command("start")
@click.option("--session", "session_name", help="Name of tmux session", default=None)
@click.option(
    "--layout",
    type=click.Choice(["low", "medium", "high", "orchestrator", "dope"]),
    help="Pane layout preset",
    default=None,
)
@click.option(
    "--dual-agent/--single-agent",
    "dual_agent_flag",
    default=None,
    help="Enable a secondary agent pane in the bottom row",
)
@click.option(
    "--secondary-agent-command",
    help="Command to run in the secondary agent pane (defaults to primary agent command)",
)
@click.option("--happy/--no-happy", "happy", default=True, help="Launch Happy mirror")
@click.option("--attach/--no-attach", "attach", default=True, help="Attach to session when ready")
@click.option("--provider", help="Pass through provider to dopemux start")
@click.option(
    "--alt-routing",
    is_flag=True,
    help="🚀 Automatic alternative provider routing (OpenRouter, XAI, Minimax) - starts LiteLLM automatically",
)
@click.option(
    "--cwd",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Working directory for Claude session",
)
@click.option(
    "--bootstrap/--no-bootstrap",
    default=True,
    help="Automatically launch orchestrator, agents, and dashboards inside the layout",
)
@click.option("--debug-log", type=click.Path(file_okay=True, dir_okay=False, path_type=Path), help="Write debug logs to file")
@click.pass_context
def start_tmux(
    ctx: click.Context,
    session_name: Optional[str],
    layout: Optional[str],
    dual_agent_flag: Optional[bool],
    happy: bool,
    attach: bool,
    provider: Optional[str],
    alt_routing: bool,
    cwd: Optional[Path],
    secondary_agent_command: Optional[str],
    bootstrap: bool,
    debug_log: Optional[Path],
) -> None:
    """Create a Dopemux-focused tmux session and launch Claude Code."""

    cfg_manager = _resolve_config_manager(ctx)
    # Force CLI backend for new session creation from outside tmux
    controller = _get_controller(ctx, force_cli_backend=True)
    tmux_cfg = cfg_manager.get_tmux_config()

    if dual_agent_flag is None:
        dual_agent = bool(getattr(tmux_cfg, "dual_agent_default", False))
    else:
        dual_agent = dual_agent_flag

    if dual_agent_flag is None:
        dual_agent = bool(getattr(tmux_cfg, "dual_agent_default", False))
    else:
        dual_agent = dual_agent_flag

    secondary_agent_cmd = secondary_agent_command or getattr(
        tmux_cfg, "secondary_agent_command", None
    )

    session = session_name or tmux_cfg.default_session or "dopemux"
    start_dir = str(cwd or Path.cwd())

    # Optional debug file logging for tmux start
    if debug_log:
        try:
            log_path = Path(debug_log).expanduser().resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                handlers=[logging.FileHandler(log_path, encoding="utf-8")],
            )
            os.environ["DOPEMUX_DEBUG_LOG"] = str(log_path)
        except Exception:
            pass

    logging.debug("dopemux tmux start: session=%s layout=%s dual_agent=%s cwd=%s bootstrap=%s attach=%s", session, layout, dual_agent, start_dir, bootstrap, attach)
    
    # Handle --alt-routing flag (start LiteLLM automatically)
    if alt_routing:
        console.print("[cyan]🚀 Alternative routing enabled - starting LiteLLM automatically...[/cyan]")

        from pathlib import Path as EnvPath
        from ..utils.dotenv_loader import load_dotenv
        import time
        import httpx

        routing_env = EnvPath(start_dir) / ".env.routing"
        if routing_env.exists():
            load_dotenv(routing_env)
            console.print("[dim]✓ Loaded .env.routing[/dim]")
        else:
            console.print("[yellow]⚠️  .env.routing not found - using defaults[/yellow]")

        instance_dir = EnvPath(start_dir) / ".dopemux" / "litellm" / "A"
        instance_dir.mkdir(parents=True, exist_ok=True)
        litellm_log = instance_dir / "litellm.log"
        master_key_path = instance_dir / "master.key"
        db_url_path = instance_dir / "database.url"

        remember_raw = os.getenv("DOPEMUX_LITELLM_REMEMBER_DB", "").strip().lower()
        remember_db = remember_raw not in {"0", "false", "no"}
        db_url = (
            os.getenv("DOPEMUX_LITELLM_DB_URL")
            or os.getenv("LITELLM_DATABASE_URL")
            or os.getenv("DATABASE_URL")
        )
        if not db_url and remember_db and db_url_path.exists():
            try:
                loaded = db_url_path.read_text(encoding="utf-8").strip()
                if loaded:
                    db_url = loaded
            except Exception:
                pass

        if not db_url:
            console.print("[red]❌ LiteLLM metrics database is required for alternative routing.[/red]")
            console.print("[yellow]   Set DOPEMUX_LITELLM_DB_URL in .env.routing and ensure the database is reachable.[/yellow]")
            console.print("\n[cyan]Example:[/cyan]")
            console.print("  DOPEMUX_LITELLM_DB_URL=postgresql://user:password@localhost:5432/litellm")
            raise click.ClickException("LiteLLM metrics database not configured.")

        stored_master_key: Optional[str] = None
        if master_key_path.exists():
            try:
                stored_master_key = master_key_path.read_text(encoding="utf-8").strip()
            except Exception:
                stored_master_key = None

        env_master_key_raw = (os.getenv("LITELLM_MASTER_KEY") or "").strip()
        candidate_keys: List[str] = []
        for key in (stored_master_key, env_master_key_raw):
            if key and key not in candidate_keys:
                candidate_keys.append(key)

        # Check if port 4000 is available, otherwise use an alternative
        import socket
        def is_port_available(port: int) -> bool:
            """Check if a port is available for binding."""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    return True
                except OSError:
                    return False

        litellm_port = 4000
        if not is_port_available(litellm_port):
            # Port 4000 is taken, try 4001
            litellm_port = 4001
            if not is_port_available(litellm_port):
                # Port 4001 is also taken, try 4002
                litellm_port = 4002
                if not is_port_available(litellm_port):
                    console.print("[red]❌ Ports 4000-4002 are all in use.[/red]")
                    console.print("[yellow]   Free up a port or stop an existing LiteLLM instance.[/yellow]")
                    raise click.ClickException("No available ports for LiteLLM proxy.")
            console.print(f"[yellow]⚠️  Port 4000 is in use, using port {litellm_port} instead[/yellow]")

        litellm_master_key = ""
        regenerated_master_key = False
        litellm_running = False

        for candidate in candidate_keys:
            try:
                resp = httpx.get(
                    f"http://127.0.0.1:{litellm_port}/health/readiness",
                    timeout=2,
                )
                if resp.status_code == 200:
                    litellm_master_key = candidate
                    litellm_running = True
                    break
            except httpx.HTTPError as exc:
                cause = getattr(exc, "__cause__", None)
                if isinstance(cause, OSError) and getattr(cause, "errno", None) == 1:
                    console.print(
                        "[yellow]⚠️ LiteLLM health probe blocked by OS (operation not permitted); proceeding without inline check.[/yellow]"
                    )
                    break

        if not litellm_master_key:
            base_candidate = env_master_key_raw or stored_master_key
            litellm_master_key, regenerated_master_key = ensure_master_key(base_candidate)
            if regenerated_master_key:
                console.print("[yellow]⚠️  Generated LiteLLM master key with sk- prefix for proxy auth[/yellow]")
        else:
            regenerated_master_key = False

        os.environ["LITELLM_MASTER_KEY"] = litellm_master_key

        if not stored_master_key or stored_master_key != litellm_master_key:
            try:
                master_key_path.write_text(litellm_master_key, encoding="utf-8")
            except Exception:
                pass

        config_source: Optional[Path] = None
        if (instance_dir / "litellm.config.yaml").exists():
            config_source = instance_dir / "litellm.config.yaml"

        if config_source and config_source.exists():
            try:
                config_data = yaml.safe_load(config_source.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                config_data = {}
        else:
            try:
                config_data = yaml.safe_load(DEFAULT_LITELLM_CONFIG) or {}
            except yaml.YAMLError:
                config_data = {}

        general_settings = config_data.setdefault("general_settings", {})
        general_settings["master_key"] = litellm_master_key

        try:
            db_status_msg, db_enabled = sync_litellm_database(instance_dir, db_url)
        except LiteLLMProxyError as exc:
            console.print(f"[red]❌ LiteLLM database setup failed: {exc}[/red]")
            console.print("[yellow]   Fix the database connection (is Postgres running? credentials valid?) and retry.[/yellow]")
            console.print("\n[cyan]Troubleshooting:[/cyan]")
            console.print("  1. Check if PostgreSQL is running: lsof -i :5432 (or your port)")
            console.print("  2. Verify database credentials in .env.routing")
            console.print("  3. Ensure the 'litellm' database exists")
            console.print("  4. Test connection: psql <your_database_url>")
            raise click.ClickException(str(exc))

        if not db_enabled:
            console.print(f"[red]❌ {db_status_msg}[/red]")
            console.print("[yellow]   LiteLLM metrics must be available. Resolve the database issue and retry.")
            raise click.ClickException("LiteLLM metrics database not ready.")

        console.print(f"[dim]{db_status_msg}[/dim]")
        general_settings["database_url"] = db_url

        config_path = instance_dir / "litellm.config.yaml"
        try:
            config_path.write_text(
                yaml.safe_dump(config_data, sort_keys=False, default_flow_style=False),
                encoding="utf-8",
            )
        except Exception:
            pass

        if litellm_running:
            console.print("[green]✓ LiteLLM already running[/green]")
        else:
            console.print("[blue]🔄 Starting LiteLLM proxy...[/blue]")
            kill_result = subprocess.run(
                ["pkill", "-f", "litellm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if kill_result.returncode not in (0, 1):
                console.print("[red]❌ Unable to manage existing LiteLLM processes automatically (permission denied).")
                console.print(f"[yellow]   Stop the existing LiteLLM proxy on port {litellm_port} manually and rerun the command.")
                raise click.ClickException("LiteLLM proxy still running.")

            time.sleep(1)
            litellm_log.parent.mkdir(parents=True, exist_ok=True)
            with open(litellm_log, "w", encoding="utf-8") as log_file:
                subprocess.Popen(
                    ["litellm", "--config", str(config_path), "--port", str(litellm_port), "--host", "0.0.0.0"],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )

            console.print("[dim]⏳ Waiting for LiteLLM...[/dim]")
            ready = False
            for _ in range(15):
                try:
                    resp = httpx.get(
                        f"http://127.0.0.1:{litellm_port}/health/readiness",
                        timeout=2,
                    )
                    if resp.status_code == 200:
                        ready = True
                        break
                except httpx.HTTPError as exc:
                    cause = getattr(exc, "__cause__", None)
                    if isinstance(cause, OSError) and getattr(cause, "errno", None) == 1:
                        console.print(
                            "[yellow]⚠️ LiteLLM health probe blocked by OS (operation not permitted); assuming proxy is running.[/yellow]"
                        )
                        ready = True
                        break
                time.sleep(1)

            if not ready:
                console.print("[red]❌ LiteLLM proxy did not become healthy.[/red]")
                console.print(f"[yellow]   Check logs: tail -f {litellm_log}[/yellow]")
                console.print("\n[cyan]Common issues:[/cyan]")
                console.print("  • Database connection failed (check PostgreSQL is running)")
                console.print(f"  • Port {litellm_port} became busy during startup")
                console.print("  • Configuration error in litellm.config.yaml")
                raise click.ClickException("LiteLLM proxy failed to start.")

            console.print(f"[green]✅ LiteLLM ready on port {litellm_port}[/green]")

        os.environ["DOPEMUX_CLAUDE_VIA_LITELLM"] = "true"
        os.environ["DOPEMUX_DEFAULT_LITELLM"] = "1"
        os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{litellm_port}"
        os.environ["DOPEMUX_LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["ANTHROPIC_API_KEY"] = litellm_master_key

        os.environ["CLAUDE_CODE_ROUTER_PROVIDER"] = "litellm"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_URL"] = f"http://127.0.0.1:{litellm_port}/v1/chat/completions"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"

        models: List[str] = []
        model_list = config_data.get("model_list")
        if isinstance(model_list, list):
            models = [
                m.get("model_name")
                for m in model_list
                if isinstance(m, dict) and m.get("model_name")
            ]
        if models:
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = ",".join(models)

        os.environ["DOPEMUX_LITELLM_DB_URL"] = db_url
        os.environ.setdefault("LITELLM_DATABASE_URL", db_url)
        os.environ["DATABASE_URL"] = db_url
        if remember_db:
            try:
                db_url_path.parent.mkdir(parents=True, exist_ok=True)
                db_url_path.write_text(db_url, encoding="utf-8")
            except Exception:
                pass
        console.print("[dim]ℹ️ LiteLLM metrics database synchronised[/dim]")
        console.print("[dim]✓ Environment configured for LiteLLM routing[/dim]")
        console.print("")

    # Determine layout and window name before creating session
    layout_choice = layout or getattr(tmux_cfg, "default_layout", None) or "medium"
    orchestrator_window = getattr(tmux_cfg, "orchestrator_window", None) or "dopemux"
    initial_window = orchestrator_window if layout_choice in ("orchestrator", "dope") else "main"

    session_already_exists = tmux_utils.session_exists(session)
    if not session_already_exists:
        try:
            tmux_utils.create_session(session, start_directory=start_dir, window_name=initial_window)
            click.echo(f"✨ Created tmux session '{session}'")
            
            # Give tmux server time to fully initialize the session
            import time
            time.sleep(0.5)
            
            # Verify session was created
            if not tmux_utils.session_exists(session):
                raise click.ClickException(f"Session '{session}' was not created successfully")
        except tmux_utils.TmuxError as e:
            raise click.ClickException(f"Failed to create tmux session: {e}")
    else:
        click.echo(f"ℹ️  Reusing existing tmux session '{session}'")

    # Enable pane title display
    try:
        tmux_utils.enable_pane_titles(session)
        click.echo("[dim]✓ Pane titles enabled[/dim]")
    except tmux_utils.TmuxError as e:
        click.echo(f"[yellow]⚠ Could not enable pane titles: {e}[/yellow]")

    # Enforce alternate-provider routing via LiteLLM/OpenRouter for all panes
    try:
        tmux_utils.set_environment(session, "DOPEMUX_DEFAULT_LITELLM", "1")
        click.echo("[dim]✓ Environment configured[/dim]")
    except tmux_utils.TmuxError as e:
        click.echo(f"[yellow]⚠ Could not set environment: {e}[/yellow]")

    split_vertical = layout_choice != "low"

    layout_handles: Optional[OrchestratorLayout] = None
    if layout_choice == "orchestrator":
        try:
            base_pane = _prepare_orchestrator_base(
                controller,
                session,
                start_dir,
                window_name=orchestrator_window,
                created_new_session=not session_already_exists,
            )
        except Exception as e:
            click.echo(f"[red]❌ Error preparing orchestrator base: {e}[/red]")
            raise
        
        try:
            layout_handles = _setup_orchestrator_layout(
                controller,
                session,
                base_pane,
                start_dir,
                tmux_cfg,
                dual_agent,
            )
        except Exception as e:
            click.echo(f"[red]❌ Error setting up orchestrator layout: {e}[/red]")
            raise
    elif layout_choice == "dope":
        try:
            base_pane = _prepare_orchestrator_base(
                controller,
                session,
                start_dir,
                window_name=orchestrator_window,
                created_new_session=not session_already_exists,
            )
        except Exception as e:
            click.echo(f"[red]❌ Error preparing orchestrator base: {e}[/red]")
            raise

        try:
            layout_handles = _setup_dope_layout(
                controller,
                session,
                base_pane,
                start_dir,
                tmux_cfg,
                dual_agent,
                bootstrap,
            )
        except Exception as e:
            click.echo(f"[red]❌ Error setting up Dope layout: {e}[/red]")
            raise
    else:
        all_panes = [pane for pane in controller.backend.list_panes() if pane.session == session]
        if not all_panes:
            raise click.ClickException(f"Unable to locate panes in tmux session '{session}'")

        base_pane = next((pane for pane in all_panes if pane.active), all_panes[0])
        tmux_utils.set_pane_title(base_pane.pane_id, "shell:main")
        tmux_utils.rename_window(session, base_pane.window or "0", "dopemux")

    claude_cmd = "dopemux start"
    if provider:
        claude_cmd += f" --provider {provider}"

    if layout_handles:
        claude_pane = controller.resolve_pane(layout_handles.agent)
        if bootstrap and layout_choice != "dope" and layout_handles.secondary_agent and secondary_agent_cmd:
            secondary_prefix = (
                f"export DOPEMUX_DEFAULT_LITELLM=1; "
                f"export DOPEMUX_TMUX_SESSION={session}; "
                "export DOPEMUX_AGENT_ROLE=secondary; "
            )
            controller.send_keys(
                layout_handles.secondary_agent,
                secondary_prefix + secondary_agent_cmd,
                enter=True,
                raw=True,
                respect_rate_limit=False,
            )
    else:
        claude_pane = controller.open(
            claude_cmd,
            target=base_pane.pane_id,
            vertical=split_vertical,
            focus=True,
            name="agent:claude",
            cwd=start_dir,
            environment_override={"DOPEMUX_TMUX_SESSION": session},
        )

    if layout_handles:
        orchestrator_pane = controller.resolve_pane(layout_handles.orchestrator)
        if orchestrator_pane:
            if bootstrap:
                click.echo(
                    f"🎯 Orchestrator Claude running in pane {orchestrator_pane.pane_id} ({orchestrator_pane.session}:{orchestrator_pane.window})"
                )
            else:
                click.echo(
                    f"🎯 Orchestrator pane ready in {orchestrator_pane.pane_id} ({orchestrator_pane.session}:{orchestrator_pane.window}); launch manually when ready."
                )
        if claude_pane:
            if bootstrap:
                click.echo(
                    f"🟡 Agent pane {claude_pane.pane_id} ({claude_pane.session}:{claude_pane.window}) ready for new launches."
                )
            else:
                click.echo(
                    f"🟡 Agent pane {claude_pane.pane_id} ({claude_pane.session}:{claude_pane.window}) idle; run your agent command inside."
                )
    else:
        click.echo(
            f"🚀 Claude Code launching in pane {claude_pane.pane_id} ({claude_pane.session}:{claude_pane.window})"
        )

    if happy:
        ok, _ = ensure_dependency("happy")
        if ok:
            targets = []
            if layout_handles:
                # Connect Happy to orchestrator for mobile control
                targets.append(layout_handles.orchestrator)
            if not layout_handles:
                targets.append(claude_pane.pane_id)
            if targets:
                # Use popup mode to avoid splitting orchestrator pane
                _launch_happy_for_targets(
                    controller,
                    cfg_manager,
                    targets,
                    vertical=False,
                    focus_flag=False,
                    popup_override=True,  # Force popup mode for orchestrator
                )
        else:
            click.echo("⚠️  Happy CLI not found; skipping mobile mirror.")

    inside_tmux = bool(os.environ.get("TMUX"))
    if attach and not inside_tmux:
        click.echo(f"🔗 Attaching to tmux session '{session}'...")
        tmux_utils.attach_session(session)
    else:
        if inside_tmux:
            click.echo(f"🔁 Switching to tmux session '{session}'...")
            tmux_utils.switch_client(session)
        else:
            click.echo(f"Session ready. Attach manually with: tmux attach -t {session}")