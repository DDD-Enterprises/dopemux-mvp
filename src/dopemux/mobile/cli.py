"""Click command group for Dopemux mobile (Happy) integration."""

from __future__ import annotations

import sys
import time
from typing import List, Optional, Sequence

import click
from click.shell_completion import CompletionItem

from ..config import ConfigManager
from ..config.manager import MobileConfig
from .runtime import (
    check_cli_health,
    detach_mobile_sessions,
    env_for_happy,
    get_mobile_status,
    launch_happy_sessions,
    list_claude_panes,
    mobile_notify,
    resolve_targets,
    update_tmux_mobile_indicator,
)
from .tmux_utils import TmuxError


def _get_config_manager(ctx: click.Context) -> ConfigManager:
    manager = ctx.obj.get("config_manager") if ctx.obj else None
    if isinstance(manager, ConfigManager):
        return manager
    return ConfigManager()


def _dependency_warnings(mobile_cfg: MobileConfig) -> None:
    if not mobile_cfg.enabled:
        click.echo("⚠️  Mobile mode disabled in config; running in manual mode.")


def _pane_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str):
    try:
        panes = list_claude_panes()
    except TmuxError:
        return []

    completions = []
    seen = set()
    needle = incomplete.lower()

    for pane in panes:
        candidates = [pane.label, pane.title, pane.window, pane.pane_id]
        for candidate in candidates:
            if not candidate:
                continue
            value = candidate.strip()
            lowered = value.lower()
            if lowered in seen:
                continue
            if needle and not lowered.startswith(needle):
                continue
            seen.add(lowered)
            help_text = f"{pane.window or 'pane'} · {pane.command or ''}".strip()
            completions.append(CompletionItem(value=value, help=help_text))

    return completions


@click.group()
@click.pass_context
def mobile(ctx: click.Context):
    """📱 Happy mobile client integration commands."""


@mobile.command()
@click.option("--all", "launch_all", is_flag=True, help="Launch Happy for all Claude panes")
@click.option(
    "--pane",
    "pane",
    multiple=True,
    help="Target specific Claude pane names or IDs",
    shell_complete=_pane_shell_complete,
)
@click.option("--map", "mapping", type=click.Choice(["agents"]), help="Apply a session mapping strategy")
@click.option("--label", "labels", multiple=True, help="Custom label for Happy panes (repeat per pane)")
@click.option("--yes", "assume_yes", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def start(
    ctx: click.Context,
    launch_all: bool,
    pane: Sequence[str],
    mapping: Optional[str],
    labels: Sequence[str],
    assume_yes: bool,
):
    """Launch Happy sessions and pair mobile devices."""

    cfg_manager = _get_config_manager(ctx)
    mobile_cfg = cfg_manager.get_mobile_config()
    _dependency_warnings(mobile_cfg)

    if not check_cli_health("happy"):
        click.echo("❌ Happy CLI unavailable. Install with: npm i -g happy-coder and ensure 'happy --version' succeeds.")
        sys.exit(1)

    claude_ok = check_cli_health("claude")
    if not claude_ok:
        click.echo("⚠️  Claude CLI not responding. Happy can still launch but pairing may fail. Run 'claude --version' to troubleshoot.")

    targets = resolve_targets(launch_all, pane, mobile_cfg, mapping_strategy=mapping)
    if not targets:
        click.echo("No Claude panes found. Start Dopemux dev session first.")
        sys.exit(1)

    if len(targets) > 4 and not assume_yes:
        if not click.confirm("Launching more than 4 Happy sessions may be CPU heavy. Continue?", default=False):
            click.echo("Aborted mobile start.")
            sys.exit(1)

    resolved_labels: Optional[List[str]] = None
    if labels:
        cleaned = [label.strip() for label in labels if label.strip()]
        if not cleaned:
            click.echo("❌ Provided labels are empty.")
            sys.exit(1)
        if len(cleaned) not in (1, len(targets)):
            click.echo("❌ Provide one label per Happy session target (or a single label when launching one session).")
            sys.exit(1)
        if len(cleaned) == 1 and len(targets) == 1:
            resolved_labels = cleaned
        elif len(cleaned) == len(targets):
            resolved_labels = cleaned
        else:
            click.echo("❌ Label count does not match target count.")
            sys.exit(1)

    env = env_for_happy(mobile_cfg)
    try:
        outcome = launch_happy_sessions(targets, env, mobile_cfg, labels=resolved_labels)
    except TmuxError as exc:
        click.echo(f"❌ tmux error: {exc}")
        sys.exit(1)

        logger.error(f"Error: {e}")
    if outcome.started:
        for label in outcome.started:
            click.echo(f"✅ Happy session ready: {label}")
    if outcome.skipped_existing:
        skipped_list = ", ".join(outcome.skipped_existing)
        click.echo(f"ℹ️  Skipped existing sessions: {skipped_list}")
    if not outcome.started and not outcome.skipped_existing:
        click.echo("Happy sessions already running for requested panes.")

    update_tmux_mobile_indicator(cfg_manager)


@mobile.command()
@click.option("--pane", "pane", multiple=True, help="Detach specific Happy pane labels")
@click.option("--all", "detach_all", is_flag=True, help="Detach all mobile Happy sessions")
@click.pass_context
def detach(ctx: click.Context, pane: Sequence[str], detach_all: bool):
    """Stop Happy processes running in Dopemux mobile panes."""

    cfg_manager = _get_config_manager(ctx)
    mobile_cfg = cfg_manager.get_mobile_config()
    _dependency_warnings(mobile_cfg)

    labels = list(pane) if pane else (None if detach_all else None)
    try:
        detached = detach_mobile_sessions(labels)
    except TmuxError as exc:
        click.echo(f"❌ tmux error: {exc}")
        sys.exit(1)

        logger.error(f"Error: {e}")
    if not detached:
        click.echo("No Happy sessions found to detach.")
    else:
        for label in detached:
            click.echo(f"👋 Detached Happy session: {label}")

    update_tmux_mobile_indicator(cfg_manager)


@mobile.command()
@click.argument("message", nargs=-1, required=True)
@click.pass_context
def notify(ctx: click.Context, message: Sequence[str]):
    """Send a push notification via Happy."""

    cfg_manager = _get_config_manager(ctx)
    env = env_for_happy(cfg_manager.get_mobile_config())
    if not check_cli_health("happy"):
        click.echo("❌ Happy CLI unavailable. Install with: npm i -g happy-coder and ensure 'happy --version' succeeds.")
        sys.exit(1)

    text = " ".join(message).strip()
    if not text:
        click.echo("Message cannot be empty.")
        sys.exit(1)

    result = mobile_notify(text, env)
    if result.returncode != 0:
        click.echo(f"❌ Failed to send notification: {result.stderr.strip() or result.stdout.strip()}")
        sys.exit(result.returncode)
    click.echo("✅ Notification sent to Happy.")


@mobile.command()
@click.option("--json", "as_json", is_flag=True, help="Output status as JSON")
@click.option("--watch", is_flag=True, help="Refresh status continuously until interrupted")
@click.option("--interval", type=float, default=5.0, show_default=True, help="Seconds between watch refreshes")
@click.pass_context
def status(ctx: click.Context, as_json: bool, watch: bool, interval: float):
    """Show Happy CLI health and active Dopemux mobile sessions."""

    if watch and as_json:
        click.echo("❌ --watch cannot be combined with --json output.")
        sys.exit(1)

    if watch and interval <= 0:
        click.echo("❌ Watch interval must be positive.")
        sys.exit(1)

    cfg_manager = _get_config_manager(ctx)

    def collect():
        status = get_mobile_status(cfg_manager)
        update_tmux_mobile_indicator(cfg_manager)
        return status

    def render_text(status) -> None:
        click.echo(f"Mobile enabled: {'✅' if status.enabled else '❌'}")
        click.echo(f"Happy CLI: {'✅' if status.happy_ok else '❌'}")
        click.echo(f"Claude CLI: {'✅' if status.claude_ok else '⚠️'}")

        if status.tmux_error:
            click.echo(f"tmux error: {status.tmux_error}")
            return

        if not status.sessions:
            click.echo("No active Happy sessions.")
            return

        click.echo("Active sessions:")
        for pane in status.sessions:
            label = pane.title or "(unnamed)"
            click.echo(f"  • {label} — window {pane.window} ({pane.pane_id})")

    def render_json(status) -> None:
        import json

        payload = {
            "mobile_enabled": status.enabled,
            "happy_cli": status.happy_ok,
            "claude_cli": status.claude_ok,
            "sessions": [
                {
                    "pane_id": pane.pane_id,
                    "title": pane.title,
                    "window": pane.window,
                    "session": pane.session,
                    "path": pane.path,
                }
                for pane in status.sessions
            ],
        }
        if status.tmux_error:
            payload["tmux_error"] = status.tmux_error
        click.echo(json.dumps(payload, indent=2))

    if watch:
        try:
            while True:
                snapshot = collect()
                click.clear()
                render_text(snapshot)
                time.sleep(interval)
        except KeyboardInterrupt:
            pass
        return

    snapshot = collect()
    if as_json:
        render_json(snapshot)
    else:
        render_text(snapshot)
