"""
Update Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip

@click.group()
def update():
    """
    🔄 System Regeneration: Update and Upgrade DØPEMÜX

    Orchestrates the synchronization and modernization of all cockpit components.
    This command group manages the lifecycle of the ritual engine, ensuring all 
    daemons, Docker containers, and cognitive patterns are aligned with the 
    latest temporal coordinates.

    Capabilities:
    - Full System Synchronization: Updates repository, dependencies, and images.
    - Checkpoint Recovery: Resume interrupted rituals from exact coordinates.
    - Temporal Rollback: Revert the flight-deck to a known stable state.
    """
    pass


@update.command()
@click.option(
    "--check",
    is_flag=True,
    help="🔬 Preview Update: Check for available ritual upgrades without committing to ignition."
)
@click.option(
    "--minimal",
    is_flag=True,
    help="⚡ Streamlined Ignition: Skip Docker rebuilds to accelerate the synchronization sequence."
)
@click.option(
    "--skip-backups",
    is_flag=True,
    help="⚠️ Bypass Safeguards: Skip backup creation (not recommended)."
)
@click.option(
    "--skip-docker",
    is_flag=True,
    help="💧 Isolate Environment: Skip Docker image updates during the ritual."
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="⏱️ Ritual Duration: Maximum time in minutes for synchronization before halting."
)
@click.pass_context
def run(ctx, check: bool, minimal: bool, skip_backups: bool, skip_docker: bool, timeout: int):
    """
    🚀 Initiate Regeneration: Run comprehensive system update

    Synchronizes all DØPEMÜX components including repository state, 
    daemon dependencies, container images, and cognitive schemas.
    """
    import asyncio
    from ..update import UpdateManager, UpdateConfig

    try:
        # Configure update
        config = UpdateConfig(
            dry_run=check,
            minimal=minimal,
            skip_backups=skip_backups,
            skip_docker=skip_docker,
            timeout_minutes=timeout
        )

        # Create update manager
        manager = UpdateManager(config=config, project_root=Path.cwd())

        if check:
            console.logger.info("[info]🔍 Checking for available updates...[/info]")
            # Run dry run
            plan = asyncio.run(manager.dry_run())

            # Display update plan
            _show_update_plan(plan)

        else:
            # Run actual update
            console.logger.info("[info]🚀 Starting dopemux update...[/info]")
            result = asyncio.run(manager.run_update())

            # Show result
            if result.value == "success":
                console.logger.info("[success]✅ Update completed successfully![/success]")
            elif result.value == "rolled_back":
                console.logger.error("[warning]🔄 Update failed but rollback successful[/warning]")
            elif result.value == "interrupted":
                console.logger.info("[warning]⏸️ Update interrupted - resume with 'dopemux update resume'[/warning]")
            else:
                console.logger.error("[error]❌ Update failed[/error]")
                sys.exit(1)

    except Exception as e:
        console.logger.error(f"[error]❌ Update command failed: {e}[/error]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def resume(ctx):
    """
    ▶️ Re-Engage Ritual: Resume interrupted update from last checkpoint

    Restores the synchronization sequence from the exact temporal 
    coordinate where the previous attempt was halted.
    """
    import asyncio
    from ..update import UpdateManager, UpdateConfig

    try:
        # Create manager with resume configuration
        config = UpdateConfig(checkpoint_saves=True)
        manager = UpdateManager(config=config, project_root=Path.cwd())

        console.logger.info("[info]🔄 Resuming interrupted update...[/info]")
        result = asyncio.run(manager.run_update())

        if result.value == "success":
            console.logger.info("[success]✅ Update resumed and completed successfully![/success]")
        else:
            console.logger.error(f"[error]❌ Update resume failed: {result.value}[/error]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[error]❌ Resume command failed: {e}[/error]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.option(
    "--backup-name",
    help="📜 Temporal Anchor: Specific backup to rollback to (interactive selection if not provided)."
)
@click.option(
    "--list-backups",
    is_flag=True,
    help="📋 Catalog Archives: List all available system checkpoints."
)
@click.pass_context
def rollback(ctx, backup_name: Optional[str], list_backups: bool):
    """
    ⏪ Temporal Reversion: Rollback to previous system state

    Restores the cockpit and daemon state to a known stable checkpoint, 
    undoing all changes since the selected archive was captured.
    """
    import asyncio
    from ..update import RollbackManager

    try:
        manager = RollbackManager(project_root=Path.cwd())

        if list_backups:
            # List available backups
            backups = manager.list_available_backups()

            if not backups:
                console.logger.info("[warning]No backups available[/warning]")
                return

            console.logger.info("\n[bold]Available Backups:[/bold]")
            table = styled_table(
                "Available Backups",
                ("Name", {"style": "info"}),
                ("Created", {"style": "text.dim"}),
                ("Version", {"style": "success"}),
                ("Size", {"style": "info"}),
            )

            for backup in backups:
                backup_path = Path(backup['path'])
                created = backup['created_at'][:19].replace('T', ' ')
                version = backup.get('version_from', 'unknown')
                size = backup.get('size', 'unknown')

                table.add_row(backup_path.name, created, version, size)

            console.logger.info(table)
            return

        # Perform rollback
        console.logger.info("[warning]🔄 Initiating system rollback...[/warning]")
        success = asyncio.run(manager.manual_rollback(backup_name))

        if success:
            console.logger.info("[success]✅ Rollback completed successfully![/success]")
        else:
            console.logger.error("[error]❌ Rollback failed[/error]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[error]❌ Rollback command failed: {e}[/error]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def update_status_cmd(ctx):
    """
    📊 Diagnostic HUD: Show system update status and health

    Displays current version coordinates, available upgrades,
    system service health, and temporal update history.
    """
    import asyncio
    from ..update import UpdateManager
    from ..update.health import HealthChecker

    try:
        manager = UpdateManager(project_root=Path.cwd())
        health_checker = HealthChecker(project_root=Path.cwd())

        console.logger.info("[info]📊 Dopemux System Status[/info]\n")

        # Version information
        version_info = manager.check_for_updates()
        console.logger.info(f"[bold]Current Version:[/bold] {version_info.current}")
        console.logger.info(f"[bold]Latest Version:[/bold] {version_info.target}")

        if version_info.current != version_info.target:
            console.logger.info(f"[warning]📦 Update available: {version_info.current} → {version_info.target}[/warning]")
        else:
            console.logger.info("[success]✅ System is up to date[/success]")

        # Health status
        console.logger.info("\n[bold]System Health:[/bold]")
        health_results = asyncio.run(health_checker.check_all_services())

        healthy_count = sum(health_results.values())
        total_count = len(health_results)

        if healthy_count == total_count:
            console.logger.info(f"[success]✅ All services healthy ({healthy_count}/{total_count})[/success]")
        else:
            console.logger.info(f"[warning]⚠️ {total_count - healthy_count} services need attention ({healthy_count}/{total_count})[/warning]")

            # Show unhealthy services
            unhealthy = [service for service, healthy in health_results.items() if not healthy]
            for service in unhealthy:
                console.logger.info(f"  [error]❌ {service}[/error]")

    except Exception as e:
        console.logger.error(f"[error]❌ Status command failed: {e}[/error]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _show_update_plan(plan):
    """Show update plan in user-friendly format."""
    version_info = plan['version_info']

    console.logger.info(f"\n[bold]📋 Update Plan: v{version_info['current']} → v{version_info['target']}[/bold]")

    if version_info['current'] == version_info['target']:
        console.logger.info("[success]✅ Already up to date![/success]")
        return

    # Show what will be updated
    table = styled_table(
        "Update Plan",
        ("Component", {"style": "info"}),
        ("Action", {"style": "warning"}),
        "Details",
    )

    table.add_row("Code", "🔄 Update", "Pull latest changes from git")
    table.add_row("Dependencies", "📦 Update", "Python and Node.js packages")
    table.add_row("Docker", "🐳 Rebuild", "Update container images")
    table.add_row("Configuration", "⚙️ Merge", "Preserve local customizations")

    if version_info.get('requires_migration'):
        table.add_row("Database", "🔄 Migrate", "Apply schema changes")

    console.logger.info(table)

    # Show estimates
    console.logger.info(f"\n[text.dim]⏱️ Estimated time: {plan.get('estimated_time', '15-20 minutes')}[/text.dim]")
    console.logger.info(f"[text.dim]💾 Backup size: {plan.get('backup_size', '~250 MB')}[/text.dim]")

    # Show phases
    phases = plan.get('phases', [])
    if phases:
        console.logger.info(f"\n[bold]Phases:[/bold] {' → '.join(phases)}")


# =============================================================================
# Profile Management Commands (Epic 1)
# =============================================================================
