#!/usr/bin/env python3
"""
Profile Management CLI Commands for Dopemux

Provides user-facing commands for managing configuration profiles.
"""

import click

import logging

logger = logging.getLogger(__name__)

from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import subprocess
from datetime import datetime
from time import perf_counter
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .profile_manager import ProfileManager

console = Console()

def detect_workspace() -> Path:
    """Detect current workspace (git root or cwd)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except Exception as e:
        return Path.cwd()


def get_profiles_directory() -> Path:
    """Return the canonical profile directory used by ProfileManager."""
    return ProfileManager().profiles_dir


def _timed_step(fn: Callable[..., Any], *args, **kwargs) -> Tuple[Any, float]:
    """Execute a step and return (result, elapsed_seconds)."""
    started = perf_counter()
    result = fn(*args, **kwargs)
    return result, perf_counter() - started


def _save_context_for_switch(workspace: Path, previous: Optional[str], target: str) -> Optional[str]:
    """Persist a pre-switch context snapshot if workspace context is initialized."""
    if not (workspace / ".dopemux").exists():
        return None

    from .adhd import ContextManager

    context_manager = ContextManager(workspace)
    message = f"profile switch: {previous or 'none'} -> {target}"
    return context_manager.save_context(message=message, force=True)


def _restore_context_for_switch(workspace: Path) -> Optional[Dict[str, Any]]:
    """Restore latest context snapshot after a switch/restart flow."""
    if not (workspace / ".dopemux").exists():
        return None

    from .adhd import ContextManager

    context_manager = ContextManager(workspace)
    return context_manager.restore_latest()


def _apply_profile_with_backup(claude_config: Any, profile: Any) -> Optional[Path]:
    """Apply profile and return backup path for rollback workflows."""
    _, backup_path = claude_config.apply_profile(
        profile,
        create_backup=True,
        dry_run=False,
        return_backup_path=True,
    )
    return backup_path


@click.command("list")
def list_profiles():
    """📋 List all available profiles"""
    manager = ProfileManager()
    profiles = manager.list_profiles()

    if not profiles:
        console.logger.info("\n[yellow]No profiles found[/yellow]")
        return

    table = Table(title=f"\n📋 Profiles ({len(profiles)})", show_header=True, box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")

    workspace = detect_workspace()
    active = manager.get_active_profile(workspace)

    for p in profiles:
        name = f"[bold]{p.name} ✅[/bold]" if p.name == active else p.name
        table.add_row(name, p.description[:60])

    console.logger.info(table)


@click.command("use")
@click.argument("profile_name")
@click.option(
    "--apply-config/--no-apply-config",
    default=True,
    show_default=True,
    help="Apply profile MCP selection to Claude settings.json before activation.",
)
@click.option(
    "--restart-claude",
    is_flag=True,
    help="After activation, launch 'dopemux start --profile <name>' and verify startup exit status.",
)
@click.option(
    "--save-session/--no-save-session",
    default=True,
    show_default=True,
    help="Save current workspace context before switching profile.",
)
@click.option(
    "--restore-context/--no-restore-context",
    default=True,
    show_default=True,
    help="Restore latest workspace context after switch/restart flow.",
)
@click.option(
    "--target-seconds",
    type=float,
    default=10.0,
    show_default=True,
    help="Switch duration target; command warns when total exceeds this threshold.",
)
def use_profile(
    profile_name: str,
    apply_config: bool,
    restart_claude: bool,
    save_session: bool,
    restore_context: bool,
    target_seconds: float,
):
    """✅ Set active profile"""
    workspace = detect_workspace()
    manager = ProfileManager()

    profile = manager.get_profile(profile_name)
    if not profile:
        console.logger.info(f"\n[red]❌ Profile not found: {profile_name}[/red]")
        return

    previous = manager.get_active_profile(workspace)
    started_at = datetime.utcnow()
    switch_started = perf_counter()
    timings: Dict[str, float] = {}
    saved_session_id: Optional[str] = None

    backup_path: Optional[Path] = None
    claude_config = None

    if apply_config or save_session:
        future_results = {}
        future_errors = {}

        if apply_config:
            from .claude_config import ClaudeConfig

            claude_config = ClaudeConfig()

        worker_count = 2 if (apply_config and save_session) else 1
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            if save_session:
                future_results["save_session"] = executor.submit(
                    _timed_step, _save_context_for_switch, workspace, previous, profile_name
                )
            if apply_config:
                future_results["apply_config"] = executor.submit(
                    _timed_step, _apply_profile_with_backup, claude_config, profile
                )

            for step_name in ("save_session", "apply_config"):
                future = future_results.get(step_name)
                if future is None:
                    continue
                try:
                    step_result, step_elapsed = future.result()
                    timings[step_name] = step_elapsed
                    if step_name == "save_session":
                        saved_session_id = step_result
                    elif step_name == "apply_config":
                        backup_path = step_result
                except Exception as exc:
                    future_errors[step_name] = exc

        if "apply_config" in future_errors:
            exc = future_errors["apply_config"]
            console.logger.info(
                f"\n[red]❌ Failed to apply Claude config for profile '{profile_name}': {exc}[/red]"
            )
            if previous:
                console.logger.info(f"[dim]Active profile remains: {previous}[/dim]")
            return

        if "save_session" in future_errors:
            exc = future_errors["save_session"]
            console.logger.info(f"[yellow]⚠ Session save skipped due to error: {exc}[/yellow]")

    try:
        set_started = perf_counter()
        manager.set_active_profile(workspace, profile_name)
        timings["set_active_profile"] = perf_counter() - set_started
    except Exception as exc:
        # If profile marker write fails after config swap, restore previous config snapshot.
        if claude_config and backup_path:
            rollback_started = perf_counter()
            try:
                claude_config.rollback_to_backup(backup_path)
                console.logger.info("[yellow]↩ Configuration rolled back from backup[/yellow]")
                timings["rollback_config"] = perf_counter() - rollback_started
            except Exception as rollback_exc:
                logger.error("Profile rollback failed: %s", rollback_exc)
        console.logger.info(f"\n[red]❌ Failed to set active profile: {exc}[/red]")
        return

    elapsed_seconds = (datetime.utcnow() - started_at).total_seconds()

    # Best-effort telemetry into ConPort; never block UX if unavailable.
    try:
        from .profile_analytics import log_switch_sync

        log_switch_sync(
            workspace_id=str(workspace),
            to_profile=profile_name,
            from_profile=previous,
            trigger="manual",
        )
    except Exception as exc:
        logger.debug("Profile switch telemetry unavailable: %s", exc)

    if previous and previous != profile_name:
        console.logger.info(
            f"\n✅ Active profile: [cyan]{profile_name}[/cyan] "
            f"(from [dim]{previous}[/dim], {elapsed_seconds:.2f}s)"
        )
    else:
        console.logger.info(
            f"\n✅ Active profile: [cyan]{profile_name}[/cyan] "
            f"({elapsed_seconds:.2f}s)"
        )

    if apply_config:
        console.logger.info("[dim]✓ Claude settings updated with profile MCP selection[/dim]")
    if save_session and saved_session_id:
        console.logger.info(f"[dim]✓ Context saved (session: {saved_session_id[:8]})[/dim]")

    if restart_claude:
        restart_started = perf_counter()
        try:
            subprocess.run(
                ["dopemux", "start", "--profile", profile_name],
                check=True,
            )
            console.logger.info("[dim]✓ Claude restart command completed successfully[/dim]")
        except Exception as exc:
            console.logger.info(f"[red]❌ Claude restart command failed: {exc}[/red]")
        finally:
            timings["restart_claude"] = perf_counter() - restart_started

    if restore_context:
        restore_started = perf_counter()
        restored = _restore_context_for_switch(workspace)
        timings["restore_context"] = perf_counter() - restore_started
        if restored:
            console.logger.info("[dim]✓ Context restored after switch[/dim]")

    total_elapsed = perf_counter() - switch_started
    timings["total"] = total_elapsed
    timing_summary = ", ".join(f"{name}={value:.2f}s" for name, value in timings.items())
    console.logger.info(f"[dim]Switch timing: {timing_summary}[/dim]")
    if total_elapsed > target_seconds:
        console.logger.info(
            f"[yellow]⚠ Switch duration {total_elapsed:.2f}s exceeded target {target_seconds:.2f}s[/yellow]"
        )


@click.command("show")
@click.option("--verbose", "-v", is_flag=True)
def show_profile(verbose: bool):
    """🔍 Show active profile"""
    workspace = detect_workspace()
    manager = ProfileManager()
    active_name = manager.get_active_profile(workspace)

    if not active_name:
        active_name = manager.detect_profile_from_claude_config(workspace=workspace, cache_result=True)
        if not active_name:
            console.logger.info(f"\n[yellow]No active profile[/yellow]")
            return
        console.logger.info(
            f"\n[dim]Detected active profile from Claude config: {active_name}[/dim]"
        )

    profile = manager.get_profile(active_name)
    if not profile:
        return

    content = [
        f"[bold cyan]Profile:[/bold cyan] {profile.name}",
        f"{profile.description}\n",
        f"[bold]MCP Servers:[/bold]",
        f"  Required: {', '.join(profile.mcp_servers.get('required', []))}",
    ]

    console.logger.info(Panel("\n".join(content), border_style="cyan"))

    if verbose:
        merged = manager.load_merged_config(workspace, active_name)
        import yaml
        console.logger.info(f"\n[dim]{yaml.dump(merged, default_flow_style=False)}[/dim]")


@click.command("create")
@click.argument("name")
@click.option("--description", "-d")
@click.option("--based-on", "-b")
@click.option(
    "--interactive/--non-interactive",
    default=False,
    show_default=True,
    help="Use interactive profile wizard for MCP/ADHD preference selection.",
)
def create_profile(name: str, description: str, based_on: str, interactive: bool):
    """➕ Create custom profile"""
    manager = ProfileManager()

    try:
        if interactive:
            from .profile_wizard import ProfileWizard

            wizard = ProfileWizard()
            result_file = wizard.run(profile_name=name, output_dir=manager.profiles_dir)
            if result_file:
                console.logger.info(f"\n✅ Profile created: [cyan]{name}[/cyan]")
                console.logger.info(f"[dim]Wizard output: {result_file}[/dim]")
            else:
                console.logger.info(f"\n[yellow]⚠️  Wizard cancelled for profile: {name}[/yellow]")
            return

        desc = description or f"Custom: {name}"
        profile = manager.create_profile(name, desc, based_on)
        console.logger.info(f"\n✅ Profile created: [cyan]{name}[/cyan]")
        console.logger.info(f"[dim]Edit: ~/.dopemux/profiles/{name}.yaml[/dim]")
    except ValueError as e:
        console.logger.info(f"\n[red]❌ {e}[/red]")


@click.command("copy")
@click.argument("source_profile")
@click.argument("target_profile")
def copy_profile(source_profile: str, target_profile: str):
    """📄 Copy a profile to a new name."""
    manager = ProfileManager()

    source = manager.get_profile(source_profile)
    if not source:
        console.logger.info(f"\n[red]❌ Source profile not found: {source_profile}[/red]")
        return

    target_path = manager.profiles_dir / f"{target_profile}.yaml"
    if Path.exists(target_path):
        console.logger.info(f"\n[red]❌ Target profile already exists: {target_profile}[/red]")
        return

    copied = manager.create_profile(
        name=target_profile,
        description=f"Copy of {source_profile}: {source.description}",
        based_on=source_profile,
    )
    console.logger.info(f"\n✅ Profile copied: [cyan]{source_profile}[/cyan] → [cyan]{copied.name}[/cyan]")


@click.command("delete")
@click.argument("profile_name")
@click.option("--force", "-f", is_flag=True, help="Force delete protected profiles")
def delete_profile(profile_name: str, force: bool):
    """🗑️ Archive a profile."""
    manager = ProfileManager()
    profile_path = manager.profiles_dir / f"{profile_name}.yaml"

    if not Path.exists(profile_path):
        console.logger.info(f"\n[red]❌ Profile not found: {profile_name}[/red]")
        return

    protected_profiles = {"full", "adhd-default"}
    if profile_name in protected_profiles and not force:
        console.logger.info(
            f"\n[yellow]⚠️  '{profile_name}' is protected. Use --force to archive it.[/yellow]"
        )
        return

    archive_dir = manager.profiles_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    archive_path = archive_dir / f"{profile_name}.{timestamp}.yaml"
    shutil.move(str(profile_path), str(archive_path))

    workspace = detect_workspace()
    active = manager.get_active_profile(workspace)
    if active == profile_name:
        marker = workspace / ".dopemux" / "active_profile"
        if Path.exists(marker):
            marker.unlink()

    console.logger.info(
        f"\n✅ Profile archived: [cyan]{profile_name}[/cyan] → [dim]{archive_path}[/dim]"
    )


@click.command("edit")
@click.argument("profile_name")
@click.option("--editor", "-e", help="Editor command (defaults to $EDITOR)")
def edit_profile(profile_name: str, editor: str):
    """✏️ Edit a profile in $EDITOR and validate on save."""
    manager = ProfileManager()
    profile_path = manager.profiles_dir / f"{profile_name}.yaml"

    if not Path.exists(profile_path):
        console.logger.info(f"\n[red]❌ Profile not found: {profile_name}[/red]")
        return

    editor_cmd = editor or os.getenv("EDITOR")
    if not editor_cmd:
        console.logger.info("\n[red]❌ No editor configured. Set $EDITOR or pass --editor.[/red]")
        return

    backup_path = profile_path.with_suffix(".yaml.bak")
    shutil.copy(profile_path, backup_path)

    try:
        subprocess.run([editor_cmd, str(profile_path)], check=True)
        manager.get_profile(profile_name)
        backup_path.unlink(missing_ok=True)
        console.logger.info(f"\n✅ Profile updated: [cyan]{profile_name}[/cyan]")
    except Exception as exc:
        shutil.copy(backup_path, profile_path)
        backup_path.unlink(missing_ok=True)
        console.logger.info(f"\n[red]❌ Edit failed and was rolled back: {exc}[/red]")
