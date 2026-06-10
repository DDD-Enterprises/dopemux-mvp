"""
Worktree Management Commands

Git worktree commands for managing parallel ADHD-optimized development workflows.
"""

import logging
import sys
from pathlib import Path

import click

from ..console import console

logger = logging.getLogger(__name__)


@click.group()
def worktrees():
    """
    💊 Ritualize parallel flight-decks.

    Manages Git worktrees for isolated ADHD-optimized focus sessions. Each worktree
    represents a distinct branch context, allowing for instantaneous cockpit jumps
    without polluting the main working directory.
    """
    pass


@worktrees.command("list")
@click.pass_context
def worktrees_list_cmd(ctx):
    """
    📊 Inventory all active flight-decks.

    Displays every Git worktree registered in the current repository. Includes
    the absolute path, associated branch trajectory, and current lock status.
    """
    from ..worktree_commands import list_worktrees
    list_worktrees()


@worktrees.command("current")
@click.option("--no-cache", is_flag=True, help="Bypass the neural cache. Forces fresh detection from the Git filesystem layer to ensure absolute accuracy.")
@click.pass_context
def worktrees_current_cmd(ctx, no_cache: bool):
    """
    ⚡ Ping current cockpit coordinates.

    Retrieves the absolute path of the active worktree. This utilizes the MCP cache
    for ultra-low latency neural retrieval, ensuring the Ritual-Daemon always knows
    where your focus is stationed.
    """
    from ..worktree_commands import get_current_worktree
    path = get_current_worktree(use_cache=not no_cache, quiet=False)
    if path:
        logger.info(path)
    else:
        sys.exit(1)


@worktrees.command("switch-path")
@click.argument("branch")
@click.pass_context
def worktrees_switch_path_cmd(ctx, branch: str):
    """
    💧 Extract worktree trajectory.

    Returns the absolute path of a target branch's worktree. Specifically designed
    for shell-level integration, allowing the parent shell to execute directory
    jumps based on the Daemon's output.
    """
    from ..worktree_commands import get_worktree_path, list_worktrees

    path = get_worktree_path(branch)

    if path:
        from ..auto_configurator import WorktreeAutoConfigurator

        auto_config = WorktreeAutoConfigurator()
        success, message = auto_config.configure_workspace(Path(path))

        if success:
            click.echo("MCP auto-configuration complete", err=True)
        else:
            click.echo(f"MCP auto-configuration: {message}", err=True)

        click.echo(path)
        ctx.exit(0)
    else:
        click.echo(f"Error: Worktree not found for branch '{branch}'", err=True)
        click.echo("\nAvailable worktrees:", err=True)
        list_worktrees()
        ctx.exit(1)


@worktrees.command("switch")
@click.argument("branch")
@click.option("--no-fuzzy", is_flag=True, help="Enforce exact naming. Disables the fuzzy-matching heuristic for branch identification to prevent accidental jumps.")
@click.pass_context
def worktrees_switch_cmd(ctx, branch: str, no_fuzzy: bool):
    """
    🧠 Attempt cockpit jump (Deprecated).

    Attempts to switch the current session to a different worktree. Note: Direct
    directory switching is restricted by POSIX subprocess boundaries. Use the
    'dwt' shell function for seamless flight-deck transitions.
    """
    click.secho("\nWARNING: This command cannot change your shell's directory", fg="yellow", bold=True)
    click.secho("This is a fundamental POSIX limitation, not a bug.\n", fg="yellow")

    click.secho("Why it doesn't work:", fg="cyan")
    console.print("  • Python runs in a subprocess", style="text.dim")
    console.print("  • Subprocesses cannot modify the parent shell's working directory", style="text.dim")
    console.print("  • This affects ALL programming languages, not just Python\n", style="text.dim")

    click.secho("Solution: Install shell integration", fg="green", bold=True)

    from ..shell_integration_installer import ShellIntegrationInstaller

    installer = ShellIntegrationInstaller()

    if installer.is_supported() and not installer.is_installed():
        # markup=False: literal square brackets in option labels
        console.print("\n[Option 1] Automated installation (recommended):", markup=False, style="info")
        console.print("  We can install shell integration automatically right now!", style="text")

        if click.confirm("  Install automatically?", default=True):
            success, message = installer.install(auto_confirm=True)

            if success:
                click.secho(f"\n{message}", fg="green", bold=True)
                console.print(f"\nActivate now: source ~/{'.' + installer.shell_name + 'rc'}", style="success")
                console.print(f"Then try: dwt {branch}\n", style="mint")
                ctx.exit(0)
            else:
                click.secho(f"\n{message}", fg="red")
                console.print("Falling back to manual instructions...\n", style="text.dim")
        else:
            # markup=False: literal square brackets in option label
            console.print("\n[Option 2] Manual installation:", markup=False, style="info")
    else:
        # markup=False: literal square brackets in section header
        console.print("\n[Manual installation]:", markup=False, style="info")

    console.print("  1. Run: dopemux shell-setup bash >> ~/.bashrc", style="text")
    console.print("  2. Run: source ~/.bashrc", style="text")
    console.print(f"  3. Use: dwt {branch}\n", style="text")

    click.secho("Alternative: Use the workaround command", fg="cyan")
    console.print(f"  cd $(dopemux worktrees switch-path {branch})\n", style="mint")

    ctx.exit(1)


@worktrees.command("cleanup")
@click.option("--force", "-f", is_flag=True, help="Override safety interlocks. Forcefully remove worktrees even if they contain uncommitted changes or are marked as locked.")
@click.option("--dry-run", "-n", is_flag=True, help="Simulate the purge. Lists the worktrees targeted for decommission without executing the destructive ritual.")
@click.pass_context
def worktrees_cleanup_cmd(ctx, force: bool, dry_run: bool):
    """
    🧙 Purge stale work-spheres.

    Removes orphaned or inactive Git worktrees. This ritual reclaims disk space
    and prevents cognitive clutter by ensuring only relevant flight-decks
    remain registered in the repository ledger.
    """
    from ..worktree_commands import cleanup_worktrees
    workspace = Path.cwd()
    cleanup_worktrees(workspace, force=force, dry_run=dry_run)
