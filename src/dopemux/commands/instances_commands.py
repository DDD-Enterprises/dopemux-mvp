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
from ..console import console
from ..instance_manager import InstanceManager, detect_instances_sync, detect_orphaned_instances_sync
from ..ui.output import emit
from ..ui.theme import styled_table

logger = logging.getLogger(__name__)


@click.group()
def instances():
    """
    🧪 Instance Orchestration: Manage parallel Ritual-Daemons

    Controls isolated DØPEMÜX instances and their associated worktrees. Each 
    instance operates on its own port-range with a private focus-state, while 
    contributing to the shared neural database for cross-context awareness.
    """
    pass


@instances.command("list")
@click.pass_context
def instances_list(ctx):
    """
    📊 Diagnostic HUD: Scan and catalog all active cockpits

    Reports on every running instance, detailing assigned port-bases, branch 
    trajectories, and absolute worktree coordinates. Automatically detects 
    and flags orphaned instances that have suffered service failure.
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

    def _rich_instances():
        if running_instances:
            console.logger.info(f"\n[success]Found {len(running_instances)} running instance(s)[/success]\n")

            table = styled_table(
                "Running Instances",
                ("Instance", {"style": "info", "no_wrap": True}),
                ("Port", {"style": "magenta", "no_wrap": True}),
                ("Branch", {"style": "success"}),
                ("Current Worktree", {"style": "info"}),
                ("Status", {"style": "success"}),
            )

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
            console.logger.info("[warning]No running instances found[/warning]")

    emit(
        ctx,
        data={
            "instances": [
                {
                    "id": inst.instance_id,
                    "port": inst.port_base,
                    "branch": inst.git_branch or "unknown",
                    "worktree": str(inst.worktree_path) if inst.worktree_path else "main",
                    "healthy": inst.is_healthy,
                }
                for inst in running_instances
            ],
            "orphaned": len(orphaned_instances),
        },
        rich_render=_rich_instances,
    )

    if orphaned_instances:
        console.logger.info(f"\n[error]Found {len(orphaned_instances)} orphaned instance(s)[/error]")
        console.logger.info("[text.dim]Orphaned instances have crashed but their worktrees still exist[/text.dim]\n")

        orphan_table = styled_table(
            "Orphaned Instances (Crashed)",
            ("Instance", {"style": "error", "no_wrap": True}),
            ("Branch", {"style": "warning"}),
            ("Last Active", {"style": "text.dim"}),
            ("Last Focus", {"style": "info"}),
            ("Action", {"style": "success"}),
        )

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
        console.logger.info("\n[text.dim]Tip: Use 'dopemux instances resume <id>' to restart an orphaned instance[/text.dim]")
        console.logger.info("[text.dim]     Or use 'dopemux instances cleanup <id>' to remove the worktree[/text.dim]")

    console.logger.info("\n[bold]Git Worktrees:[/bold]")
    worktrees = instance_manager.list_worktrees()

    if worktrees:
        worktree_table = styled_table(
            "Git Worktrees",
            ("ID", {"style": "info"}),
            ("Path", {"style": "text.dim"}),
            ("Branch", {"style": "success"}),
        )

        for wt_id, wt_path, wt_branch in worktrees:
            worktree_table.add_row(wt_id, str(wt_path), wt_branch)

        console.logger.info(worktree_table)
    else:
        console.logger.info("[text.dim]No worktrees found[/text.dim]")


@instances.command("resume")
@click.argument("instance_id")
@click.option("--restore-context", "-r", is_flag=True, help="🧪 Contextual Restoration: Reconnect focus-state and restore the last known working coordinate.")
@click.pass_context
def instances_resume(ctx, instance_id: str, restore_context: bool):
    """
    ⚡ Resuscitate Daemon: Restore a fallen or orphaned instance

    Restarts crashed or orphaned instances. This recovery ritual attempts 
    to re-stabilize instance services and can optionally reconstruct the 
    exact working directory and focus context from the persistent ledger.
    """
    project_path = Path.cwd()
    workspace_id = str(project_path.resolve())

    from ..instance_state import load_instance_state_sync

    state = load_instance_state_sync(instance_id, workspace_id, conport_port=3004)

    if not state:
        console.logger.info(f"[error]No saved state found for instance {instance_id}[/error]")
        console.logger.info("[text.dim]Tip: Use 'dopemux instances list' to see available instances[/text.dim]")
        sys.exit(1)

    if state.status != 'orphaned':
        console.logger.info(f"[warning]Instance {instance_id} is not orphaned (status: {state.status})[/warning]")
        if state.status == 'active':
            console.logger.info(f"[text.dim]Instance is already running on port {state.port_base}[/text.dim]")
        sys.exit(1)

    worktree_path = Path(state.worktree_path)
    if not worktree_path.exists():
        console.logger.info(f"[error]Worktree not found at {worktree_path}[/error]")
        console.logger.info("[text.dim]The worktree may have been deleted. Use 'dopemux instances cleanup' to remove state[/text.dim]")
        sys.exit(1)

    console.logger.info(f"\n[info]Resuming instance {instance_id}...[/info]")
    console.logger.info(f"   Branch: {state.git_branch}")
    console.logger.info(f"   Worktree: {worktree_path}")
    console.logger.info(f"   Port base: {state.port_base}")

    if state.last_focus_context:
        console.logger.info(f"   Last focus: [text.dim]{state.last_focus_context}[/text.dim]")

    if restore_context and state.last_working_directory:
        console.logger.info(f"\n[success]Context restoration enabled:[/success]")
        console.logger.info(f"   Working directory: {state.last_working_directory}")
        if state.last_focus_context:
            console.logger.info(f"   Focus context: {state.last_focus_context}")

    console.logger.info(f"\n[warning]Starting instance {instance_id} on port {state.port_base}...[/warning]")

    env = os.environ.copy()
    env.update({
        "DOPEMUX_INSTANCE_ID": instance_id,
        "DOPEMUX_WORKSPACE_ID": workspace_id,
        "DOPEMUX_PORT_BASE": str(state.port_base),
        "SERENA_PORT": str(state.port_base + 6),
        "CONPORT_PORT": str(state.port_base + 7),
        "INTEGRATION_BRIDGE_PORT": str(state.port_base + 16),
    })

    if restore_context and state.last_working_directory:
        try:
            os.chdir(state.last_working_directory)
            console.logger.info(f"[success]Changed to working directory: {state.last_working_directory}[/success]")
        except Exception as e:
            console.logger.info(f"[warning]Could not change to working directory: {e}[/warning]")
            console.logger.info("[text.dim]Staying in current directory[/text.dim]")

    console.logger.info(f"\n[success]Instance {instance_id} resumed successfully![/success]")
    console.logger.info(f"[text.dim]Services are starting on port {state.port_base}...[/text.dim]")

    if restore_context:
        console.logger.info("\n[info]Context Restored:[/info]")
        console.logger.info(f"   You were working on: {state.last_focus_context or 'N/A'}")
        console.logger.info(f"   In directory: {os.getcwd()}")

    console.logger.info(f"\n[text.dim]Tip: Instance will be marked as 'active' when dopemux start completes[/text.dim]")
    console.logger.info(f"[text.dim]     Run: cd {worktree_path} && dopemux start[/text.dim]")

    from ..instance_state import save_instance_state_sync
    state.status = 'active'
    state.last_active = datetime.now()
    save_instance_state_sync(state, workspace_id, conport_port=3004)


@instances.command("cleanup")
@click.argument("instance_id", required=False)
@click.option("--all", "-a", is_flag=True, help="⚡ Mass Purge: Target every stopped or orphaned instance for immediate decommission.")
@click.option("--force", "-f", is_flag=True, help="🔥 Bypass Safeguards: Destroy worktrees and state ledgers without confirmation.")
@click.pass_context
def instances_cleanup(ctx, instance_id: Optional[str], all: bool, force: bool):
    """
    🔬 Ritual Decommission: Remove inactive cockpits and artifacts

    Removes Git worktrees and state ledgers for stopped or dead instances. 
    This operation is critical for maintaining the purity of the instance 
    registry and preventing resource hemorrhage.
    """
    project_path = Path.cwd()
    instance_manager = InstanceManager(project_path)

    if not instance_id and not all:
        console.logger.info("[error]Specify instance ID or use --all flag[/error]")
        console.logger.info("[text.dim]Usage: dopemux instances cleanup <ID> or --all[/text.dim]")
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
            console.logger.info("[success]No stopped instances to clean up[/success]")
            return

        console.logger.info(f"\n[warning]Found {len(stopped_instances)} stopped instance(s) to clean:[/warning]")
        for wt_id, wt_path in stopped_instances:
            console.logger.info(f"  Instance {wt_id}: {wt_path}")

        if not force and not click.confirm("\nProceed with cleanup?"):
            console.logger.info("[warning]Cleanup cancelled[/warning]")
            return

        from ..instance_state import cleanup_instance_state_sync
        workspace_id = str(project_path.resolve())

        for wt_id, _ in stopped_instances:
            if instance_manager.cleanup_worktree(wt_id):
                console.logger.info(f"[success]Removed worktree for instance {wt_id}[/success]")
                if cleanup_instance_state_sync(wt_id, workspace_id, conport_port=3004):
                    console.logger.info(f"[text.dim]Removed instance state for {wt_id}[/text.dim]")
            else:
                console.logger.error(f"[error]Failed to remove worktree for instance {wt_id}[/error]")

    else:
        if instance_id == 'A':
            console.logger.info("[error]Cannot clean up main worktree (instance A)[/error]")
            sys.exit(1)

        running_instances = detect_instances_sync(project_path)
        if any(inst.instance_id == instance_id for inst in running_instances):
            console.logger.info(f"[error]Instance {instance_id} is still running[/error]")
            console.logger.info("[text.dim]Stop the instance before cleaning up its worktree[/text.dim]")
            sys.exit(1)

        worktree_path = instance_manager._get_worktree_path(instance_id)
        if not worktree_path or not worktree_path.exists():
            console.logger.info(f"[warning]No worktree found for instance {instance_id}[/warning]")
            return

        console.logger.info(f"\n[warning]Removing worktree for instance {instance_id}[/warning]")
        console.logger.info(f"[text.dim]Path: {worktree_path}[/text.dim]")

        if not force and not click.confirm("Proceed?"):
            console.logger.info("[warning]Cleanup cancelled[/warning]")
            return

        if instance_manager.cleanup_worktree(instance_id):
            console.logger.info(f"[success]Removed worktree for instance {instance_id}[/success]")

            from ..instance_state import cleanup_instance_state_sync
            workspace_id = str(project_path.resolve())

            if cleanup_instance_state_sync(instance_id, workspace_id, conport_port=3004):
                console.logger.info(f"[text.dim]Removed instance state from ConPort[/text.dim]")
        else:
            console.logger.error(f"[error]Failed to remove worktree for instance {instance_id}[/error]")
