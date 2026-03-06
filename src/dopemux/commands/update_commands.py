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
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
def update():
    """🔄 Update and upgrade dopemux system components."""
    pass


@update.command()
@click.option(
    "--check",
    is_flag=True,
    help="Check for updates without applying them (dry run)"
)
@click.option(
    "--minimal",
    is_flag=True,
    help="Skip Docker rebuilds if possible (faster update)"
)
@click.option(
    "--skip-backups",
    is_flag=True,
    help="Skip backup creation (not recommended)"
)
@click.option(
    "--skip-docker",
    is_flag=True,
    help="Skip Docker image updates"
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Timeout in minutes for update operations"
)
@click.pass_context
def run(ctx, check: bool, minimal: bool, skip_backups: bool, skip_docker: bool, timeout: int):
    """
    🚀 Run comprehensive system update

    Updates all dopemux components including:
    - Git repository (with local change preservation)
    - Docker containers and images
    - Python and Node.js dependencies
    - Database migrations
    - Configuration updates

    Includes automatic backup, rollback capability, and ADHD-friendly progress tracking.
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
            console.logger.info("[cyan]🔍 Checking for available updates...[/cyan]")
            # Run dry run
            plan = asyncio.run(manager.dry_run())

            # Display update plan
            _show_update_plan(plan)

        else:
            # Run actual update
            console.logger.info("[cyan]🚀 Starting dopemux update...[/cyan]")
            result = asyncio.run(manager.run_update())

            # Show result
            if result.value == "success":
                console.logger.info("[green]✅ Update completed successfully![/green]")
            elif result.value == "rolled_back":
                console.logger.error("[yellow]🔄 Update failed but rollback successful[/yellow]")
            elif result.value == "interrupted":
                console.logger.info("[yellow]⏸️ Update interrupted - resume with 'dopemux update resume'[/yellow]")
            else:
                console.logger.error("[red]❌ Update failed[/red]")
                sys.exit(1)

    except Exception as e:
        console.logger.error(f"[red]❌ Update command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def resume(ctx):
    """
    ▶️ Resume interrupted update from last checkpoint

    Continues an update that was interrupted by user or system failure.
    Uses automatic checkpointing to resume from the exact point of interruption.
    """
    import asyncio
    from ..update import UpdateManager, UpdateConfig

    try:
        # Create manager with resume configuration
        config = UpdateConfig(checkpoint_saves=True)
        manager = UpdateManager(config=config, project_root=Path.cwd())

        console.logger.info("[cyan]🔄 Resuming interrupted update...[/cyan]")
        result = asyncio.run(manager.run_update())

        if result.value == "success":
            console.logger.info("[green]✅ Update resumed and completed successfully![/green]")
        else:
            console.logger.error(f"[red]❌ Update resume failed: {result.value}[/red]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[red]❌ Resume command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.option(
    "--backup-name",
    help="Specific backup to rollback to (interactive selection if not provided)"
)
@click.option(
    "--list-backups",
    is_flag=True,
    help="List available backups and exit"
)
@click.pass_context
def rollback(ctx, backup_name: Optional[str], list_backups: bool):
    """
    ⏪ Rollback to previous system state

    Safely restore the system to a previous working state using automatic backups.
    Includes database restoration, configuration rollback, and service restart.
    """
    import asyncio
    from ..update import RollbackManager

    try:
        manager = RollbackManager(project_root=Path.cwd())

        if list_backups:
            # List available backups
            backups = manager.list_available_backups()

            if not backups:
                console.logger.info("[yellow]No backups available[/yellow]")
                return

            console.logger.info("\n[bold]Available Backups:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Created", style="dim")
            table.add_column("Version", style="green")
            table.add_column("Size", style="blue")

            for backup in backups:
                backup_path = Path(backup['path'])
                created = backup['created_at'][:19].replace('T', ' ')
                version = backup.get('version_from', 'unknown')
                size = backup.get('size', 'unknown')

                table.add_row(backup_path.name, created, version, size)

            console.logger.info(table)
            return

        # Perform rollback
        console.logger.info("[yellow]🔄 Initiating system rollback...[/yellow]")
        success = asyncio.run(manager.manual_rollback(backup_name))

        if success:
            console.logger.info("[green]✅ Rollback completed successfully![/green]")
        else:
            console.logger.error("[red]❌ Rollback failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[red]❌ Rollback command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def update_status_cmd(ctx):
    """
    📊 Show system update status and health

    Displays current version, available updates, system health,
    and update history.
    """
    import asyncio
    from ..update import UpdateManager
    from ..update.health import HealthChecker

    try:
        manager = UpdateManager(project_root=Path.cwd())
        health_checker = HealthChecker(project_root=Path.cwd())

        console.logger.info("[cyan]📊 Dopemux System Status[/cyan]\n")

        # Version information
        version_info = manager.check_for_updates()
        console.logger.info(f"[bold]Current Version:[/bold] {version_info.current}")
        console.logger.info(f"[bold]Latest Version:[/bold] {version_info.target}")

        if version_info.current != version_info.target:
            console.logger.info(f"[yellow]📦 Update available: {version_info.current} → {version_info.target}[/yellow]")
        else:
            console.logger.info("[green]✅ System is up to date[/green]")

        # Health status
        console.logger.info("\n[bold]System Health:[/bold]")
        health_results = asyncio.run(health_checker.check_all_services())

        healthy_count = sum(health_results.values())
        total_count = len(health_results)

        if healthy_count == total_count:
            console.logger.info(f"[green]✅ All services healthy ({healthy_count}/{total_count})[/green]")
        else:
            console.logger.info(f"[yellow]⚠️ {total_count - healthy_count} services need attention ({healthy_count}/{total_count})[/yellow]")

            # Show unhealthy services
            unhealthy = [service for service, healthy in health_results.items() if not healthy]
            for service in unhealthy:
                console.logger.info(f"  [red]❌ {service}[/red]")

    except Exception as e:
        console.logger.error(f"[red]❌ Status command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _show_update_plan(plan):
    """Show update plan in user-friendly format."""
    version_info = plan['version_info']

    console.logger.info(f"\n[bold]📋 Update Plan: v{version_info['current']} → v{version_info['target']}[/bold]")

    if version_info['current'] == version_info['target']:
        console.logger.info("[green]✅ Already up to date![/green]")
        return

    # Show what will be updated
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Action", style="yellow")
    table.add_column("Details")

    table.add_row("Code", "🔄 Update", "Pull latest changes from git")
    table.add_row("Dependencies", "📦 Update", "Python and Node.js packages")
    table.add_row("Docker", "🐳 Rebuild", "Update container images")
    table.add_row("Configuration", "⚙️ Merge", "Preserve local customizations")

    if version_info.get('requires_migration'):
        table.add_row("Database", "🔄 Migrate", "Apply schema changes")

    console.logger.info(table)

    # Show estimates
    console.logger.info(f"\n[dim]⏱️ Estimated time: {plan.get('estimated_time', '15-20 minutes')}[/dim]")
    console.logger.info(f"[dim]💾 Backup size: {plan.get('backup_size', '~250 MB')}[/dim]")

    # Show phases
    phases = plan.get('phases', [])
    if phases:
        console.logger.info(f"\n[bold]Phases:[/bold] {' → '.join(phases)}")


# =============================================================================
# Profile Management Commands (Epic 1)
# =============================================================================

