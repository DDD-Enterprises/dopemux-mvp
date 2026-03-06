"""
Instance Management Commands

Commands for managing parallel Dopemux instances and worktrees
in ADHD-optimized development workflows.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.table import Table

from ..console import console
from ..instance_manager import InstanceManager, detect_instances_sync, detect_orphaned_instances_sync

logger = logging.getLogger(__name__)


@click.group()
def instances():
    """
    Manage multiple Dopemux instances and worktrees

    Commands for managing parallel ADHD-optimized development workflows
    with isolated worktrees and shared database.
    """
    pass


@instances.command("list")
@click.pass_context
def instances_list(ctx):
    """
    List all running instances and worktrees

    Shows currently active instances with their ports, branches, and paths.
    Automatically detects and reports orphaned instances (crashed).
    """
    project_path = Path.cwd()
    workspace_id = str(project_path.resolve())

    instance_manager = InstanceManager(project_path)
    running_instances = detect_instances_sync(project_path)

    orphaned_instances = detect_orphaned_instances_sync(
        project_path,
        workspace_id,
        conport_port=3004
    )

    if running_instances:
        console.logger.info(f"\n[green]Found {len(running_instances)} running instance(s)[/green]\n")

        table = Table(title="Running Instances")
        table.add_column("Instance", style="cyan", no_wrap=True)
        table.add_column("Port", style="magenta", no_wrap=True)
        table.add_column("Branch", style="green")
        table.add_column("Current Worktree", style="blue")
        table.add_column("Status", style="green")

        for inst in running_instances:
            status = "Healthy" if inst.is_healthy else "Unknown"
            table.add_row(
                inst.instance_id,
                str(inst.port_base),
                inst.git_branch or "unknown",
                str(inst.worktree_path) if inst.worktree_path else "main",
                status
            )

        console.logger.info(table)
    else:
        console.logger.info("[yellow]No running instances found[/yellow]")

    if orphaned_instances:
        console.logger.info(f"\n[red]Found {len(orphaned_instances)} orphaned instance(s)[/red]")
        console.logger.info("[dim]Orphaned instances have crashed but their worktrees still exist[/dim]\n")

        orphan_table = Table(title="Orphaned Instances (Crashed)")
        orphan_table.add_column("Instance", style="red", no_wrap=True)
        orphan_table.add_column("Branch", style="yellow")
        orphan_table.add_column("Last Active", style="dim")
        orphan_table.add_column("Last Focus", style="cyan")
        orphan_table.add_column("Action", style="green")

        for orphan in orphaned_instances:
            if isinstance(orphan['last_active'], str):
                last_active = datetime.fromisoformat(orphan['last_active'])
            else:
                last_active = orphan['last_active']

            time_diff = datetime.now() - last_active
            if time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            else:
                time_ago = f"{time_diff.seconds // 60}m ago"

            orphan_table.add_row(
                orphan['instance_id'],
                orphan['git_branch'],
                time_ago,
                orphan.get('last_focus_context', 'N/A')[:40] or "N/A",
                f"dopemux instances resume {orphan['instance_id']}"
            )

        console.logger.info(orphan_table)
        console.logger.info("\n[dim]Tip: Use 'dopemux instances resume <id>' to restart an orphaned instance[/dim]")
        console.logger.info("[dim]     Or use 'dopemux instances cleanup <id>' to remove the worktree[/dim]")

    console.logger.info("\n[bold]Git Worktrees:[/bold]")
    worktrees = instance_manager.list_worktrees()

    if worktrees:
        worktree_table = Table()
        worktree_table.add_column("ID", style="cyan")
        worktree_table.add_column("Path", style="dim")
        worktree_table.add_column("Branch", style="green")

        for wt_id, wt_path, wt_branch in worktrees:
            worktree_table.add_row(wt_id, str(wt_path), wt_branch)

        console.logger.info(worktree_table)
    else:
        console.logger.info("[dim]No worktrees found[/dim]")


@instances.command("resume")
@click.argument("instance_id")
@click.option("--restore-context", "-r", is_flag=True, help="Restore working directory and focus context")
@click.pass_context
def instances_resume(ctx, instance_id: str, restore_context: bool):
    """
    Resume an orphaned instance (one-click crash recovery)

    Restarts services for an orphaned instance, optionally restoring
    the last working directory and focus context.

    \b
    Examples:
        dopemux instances resume B              # Restart instance B
        dopemux instances resume B --restore-context  # Restart and restore context
    """
    project_path = Path.cwd()
    workspace_id = str(project_path.resolve())

    from ..instance_state import load_instance_state_sync

    state = load_instance_state_sync(instance_id, workspace_id, conport_port=3004)

    if not state:
        console.logger.info(f"[red]No saved state found for instance {instance_id}[/red]")
        console.logger.info("[dim]Tip: Use 'dopemux instances list' to see available instances[/dim]")
        sys.exit(1)

    if state.status != 'orphaned':
        console.logger.info(f"[yellow]Instance {instance_id} is not orphaned (status: {state.status})[/yellow]")
        if state.status == 'active':
            console.logger.info(f"[dim]Instance is already running on port {state.port_base}[/dim]")
        sys.exit(1)

    worktree_path = Path(state.worktree_path)
    if not worktree_path.exists():
        console.logger.info(f"[red]Worktree not found at {worktree_path}[/red]")
        console.logger.info("[dim]The worktree may have been deleted. Use 'dopemux instances cleanup' to remove state[/dim]")
        sys.exit(1)

    console.logger.info(f"\n[cyan]Resuming instance {instance_id}...[/cyan]")
    console.logger.info(f"   Branch: {state.git_branch}")
    console.logger.info(f"   Worktree: {worktree_path}")
    console.logger.info(f"   Port base: {state.port_base}")

    if state.last_focus_context:
        console.logger.info(f"   Last focus: [dim]{state.last_focus_context}[/dim]")

    if restore_context and state.last_working_directory:
        console.logger.info(f"\n[green]Context restoration enabled:[/green]")
        console.logger.info(f"   Working directory: {state.last_working_directory}")
        if state.last_focus_context:
            console.logger.info(f"   Focus context: {state.last_focus_context}")

    console.logger.info(f"\n[yellow]Starting instance {instance_id} on port {state.port_base}...[/yellow]")

    env = os.environ.copy()
    env.update({
        "DOPEMUX_INSTANCE_ID": instance_id,
        "DOPEMUX_WORKSPACE_ID": workspace_id,
        "DOPEMUX_PORT_BASE": str(state.port_base),
        "TASK_MASTER_PORT": str(state.port_base + 5),
        "SERENA_PORT": str(state.port_base + 6),
        "CONPORT_PORT": str(state.port_base + 7),
        "INTEGRATION_BRIDGE_PORT": str(state.port_base + 16),
    })

    if restore_context and state.last_working_directory:
        try:
            os.chdir(state.last_working_directory)
            console.logger.info(f"[green]Changed to working directory: {state.last_working_directory}[/green]")
        except Exception as e:
            console.logger.info(f"[yellow]Could not change to working directory: {e}[/yellow]")
            console.logger.info("[dim]Staying in current directory[/dim]")

    console.logger.info(f"\n[green]Instance {instance_id} resumed successfully![/green]")
    console.logger.info(f"[dim]Services are starting on port {state.port_base}...[/dim]")

    if restore_context:
        console.logger.info("\n[cyan]Context Restored:[/cyan]")
        console.logger.info(f"   You were working on: {state.last_focus_context or 'N/A'}")
        console.logger.info(f"   In directory: {os.getcwd()}")

    console.logger.info(f"\n[dim]Tip: Instance will be marked as 'active' when dopemux start completes[/dim]")
    console.logger.info(f"[dim]     Run: cd {worktree_path} && dopemux start[/dim]")

    from ..instance_state import save_instance_state_sync
    state.status = 'active'
    state.last_active = datetime.now()
    save_instance_state_sync(state, workspace_id, conport_port=3004)


@instances.command("cleanup")
@click.argument("instance_id", required=False)
@click.option("--all", "-a", is_flag=True, help="Clean up all stopped instances")
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
@click.pass_context
def instances_cleanup(ctx, instance_id: Optional[str], all: bool, force: bool):
    """
    Clean up stopped instance worktrees

    Removes git worktrees for stopped instances to free up disk space.

    \b
    Examples:
        dopemux instances cleanup B          # Remove instance B worktree
        dopemux instances cleanup --all      # Remove all stopped instances
    """
    project_path = Path.cwd()
    instance_manager = InstanceManager(project_path)

    if not instance_id and not all:
        console.logger.info("[red]Specify instance ID or use --all flag[/red]")
        console.logger.info("[dim]Usage: dopemux instances cleanup <ID> or --all[/dim]")
        sys.exit(1)

    if all:
        worktrees = instance_manager.list_worktrees()
        running_instances = detect_instances_sync(project_path)
        running_ids = {inst.instance_id for inst in running_instances}

        stopped_instances = [
            (wt_id, wt_path) for wt_id, wt_path, _ in worktrees
            if wt_id not in running_ids and wt_id != 'A'
        ]

        if not stopped_instances:
            console.logger.info("[green]No stopped instances to clean up[/green]")
            return

        console.logger.info(f"\n[yellow]Found {len(stopped_instances)} stopped instance(s) to clean:[/yellow]")
        for wt_id, wt_path in stopped_instances:
            console.logger.info(f"  Instance {wt_id}: {wt_path}")

        if not force and not click.confirm("\nProceed with cleanup?"):
            console.logger.info("[yellow]Cleanup cancelled[/yellow]")
            return

        from ..instance_state import cleanup_instance_state_sync
        workspace_id = str(project_path.resolve())

        for wt_id, _ in stopped_instances:
            if instance_manager.cleanup_worktree(wt_id):
                console.logger.info(f"[green]Removed worktree for instance {wt_id}[/green]")
                if cleanup_instance_state_sync(wt_id, workspace_id, conport_port=3004):
                    console.logger.info(f"[dim]Removed instance state for {wt_id}[/dim]")
            else:
                console.logger.error(f"[red]Failed to remove worktree for instance {wt_id}[/red]")

    else:
        if instance_id == 'A':
            console.logger.info("[red]Cannot clean up main worktree (instance A)[/red]")
            sys.exit(1)

        running_instances = detect_instances_sync(project_path)
        if any(inst.instance_id == instance_id for inst in running_instances):
            console.logger.info(f"[red]Instance {instance_id} is still running[/red]")
            console.logger.info("[dim]Stop the instance before cleaning up its worktree[/dim]")
            sys.exit(1)

        worktree_path = instance_manager._get_worktree_path(instance_id)
        if not worktree_path or not worktree_path.exists():
            console.logger.info(f"[yellow]No worktree found for instance {instance_id}[/yellow]")
            return

        console.logger.info(f"\n[yellow]Removing worktree for instance {instance_id}[/yellow]")
        console.logger.info(f"[dim]Path: {worktree_path}[/dim]")

        if not force and not click.confirm("Proceed?"):
            console.logger.info("[yellow]Cleanup cancelled[/yellow]")
            return

        if instance_manager.cleanup_worktree(instance_id):
            console.logger.info(f"[green]Removed worktree for instance {instance_id}[/green]")

            from ..instance_state import cleanup_instance_state_sync
            workspace_id = str(project_path.resolve())

            if cleanup_instance_state_sync(instance_id, workspace_id, conport_port=3004):
                console.logger.info(f"[dim]Removed instance state from ConPort[/dim]")
        else:
            console.logger.error(f"[red]Failed to remove worktree for instance {instance_id}[/red]")
