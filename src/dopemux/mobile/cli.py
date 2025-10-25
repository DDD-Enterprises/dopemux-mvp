"""Click command group for Dopemux mobile (Happy) integration."""

from __future__ import annotations

import sys
from typing import Sequence

import click
from click.shell_completion import CompletionItem

from ..config import ConfigManager
from ..config.manager import MobileConfig
from .runtime import (
    detach_mobile_sessions,
    ensure_dependency,
    env_for_happy,
    launch_happy_sessions,
    list_claude_panes,
    mobile_notify,
    resolve_targets,
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
@click.pass_context
def start(ctx: click.Context, launch_all: bool, pane: Sequence[str]):
    """Launch Happy sessions and pair mobile devices."""

    cfg_manager = _get_config_manager(ctx)
    mobile_cfg = cfg_manager.get_mobile_config()
    _dependency_warnings(mobile_cfg)

    happy_ok, _ = ensure_dependency("happy")
    if not happy_ok:
        click.echo("❌ Happy CLI not found. Install with: npm i -g happy-coder")
        sys.exit(1)

    claude_ok, _ = ensure_dependency("claude")
    if not claude_ok:
        click.echo("⚠️  Claude CLI not detected. Happy can still launch but pairing may fail.")

    targets = resolve_targets(launch_all, pane, mobile_cfg)
    if not targets:
        click.echo("No Claude panes found. Start Dopemux dev session first.")
        sys.exit(1)

    env = env_for_happy(mobile_cfg)
    try:
        outcome = launch_happy_sessions(targets, env, mobile_cfg)
    except TmuxError as exc:
        click.echo(f"❌ tmux error: {exc}")
        sys.exit(1)

    if outcome.started:
        for label in outcome.started:
            click.echo(f"✅ Happy session ready: {label}")
    if outcome.skipped_existing:
        skipped_list = ", ".join(outcome.skipped_existing)
        click.echo(f"ℹ️  Skipped existing sessions: {skipped_list}")
    if not outcome.started and not outcome.skipped_existing:
        click.echo("Happy sessions already running for requested panes.")


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

    if not detached:
        click.echo("No Happy sessions found to detach.")
    else:
        for label in detached:
            click.echo(f"👋 Detached Happy session: {label}")


@mobile.command()
@click.argument("message", nargs=-1, required=True)
@click.pass_context
def notify(ctx: click.Context, message: Sequence[str]):
    """Send a push notification via Happy."""

    cfg_manager = _get_config_manager(ctx)
    env = env_for_happy(cfg_manager.get_mobile_config())
    happy_ok, _ = ensure_dependency("happy")
    if not happy_ok:
        click.echo("❌ Happy CLI not found. Install with: npm i -g happy-coder")
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
