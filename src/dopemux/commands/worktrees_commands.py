"""
Worktree Management Commands

Git worktree commands for managing parallel ADHD-optimized development workflows.
"""

import logging
import sys
from pathlib import Path

import click

logger = logging.getLogger(__name__)


@click.group()
def worktrees():
    """Manage git worktrees for parallel development."""
    pass


@worktrees.command("list")
@click.pass_context
def worktrees_list_cmd(ctx):
    """List all git worktrees with status."""
    from ..worktree_commands import list_worktrees
    list_worktrees()


@worktrees.command("current")
@click.option("--no-cache", is_flag=True, help="Skip cache and detect fresh")
@click.pass_context
def worktrees_current_cmd(ctx, no_cache: bool):
    """Get current worktree path (cached for MCP efficiency)."""
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
    """Output worktree path for shell integration (use with shell function)."""
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
@click.option("--no-fuzzy", is_flag=True, help="Disable fuzzy matching")
@click.pass_context
def worktrees_switch_cmd(ctx, branch: str, no_fuzzy: bool):
    """[DEPRECATED] Use shell integration instead - see 'dopemux shell-setup'."""
    click.secho("\nWARNING: This command cannot change your shell's directory", fg="yellow", bold=True)
    click.secho("This is a fundamental POSIX limitation, not a bug.\n", fg="yellow")

    click.secho("Why it doesn't work:", fg="cyan")
    click.echo("  • Python runs in a subprocess")
    click.echo("  • Subprocesses cannot modify the parent shell's working directory")
    click.echo("  • This affects ALL programming languages, not just Python\n")

    click.secho("Solution: Install shell integration", fg="green", bold=True)

    from ..shell_integration_installer import ShellIntegrationInstaller

    installer = ShellIntegrationInstaller()

    if installer.is_supported() and not installer.is_installed():
        click.echo("\n[Option 1] Automated installation (recommended):")
        click.echo("  We can install shell integration automatically right now!")

        if click.confirm("  Install automatically?", default=True):
            success, message = installer.install(auto_confirm=True)

            if success:
                click.secho(f"\n{message}", fg="green", bold=True)
                click.echo(f"\nActivate now: source ~/{'.' + installer.shell_name + 'rc'}")
                click.echo(f"Then try: dwt {branch}\n")
                ctx.exit(0)
            else:
                click.secho(f"\n{message}", fg="red")
                click.echo("Falling back to manual instructions...\n")
        else:
            click.echo("\n[Option 2] Manual installation:")
    else:
        click.echo("\n[Manual installation]:")

    click.echo("  1. Run: dopemux shell-setup bash >> ~/.bashrc")
    click.echo("  2. Run: source ~/.bashrc")
    click.echo(f"  3. Use: dwt {branch}\n")

    click.secho("Alternative: Use the workaround command", fg="cyan")
    click.echo(f"  cd $(dopemux worktrees switch-path {branch})\n")

    ctx.exit(1)


@worktrees.command("cleanup")
@click.option("--force", "-f", is_flag=True, help="Remove dirty worktrees")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without removing")
@click.pass_context
def worktrees_cleanup_cmd(ctx, force: bool, dry_run: bool):
    """Clean up unused worktrees."""
    from ..worktree_commands import cleanup_worktrees
    workspace = Path.cwd()
    cleanup_worktrees(workspace, force=force, dry_run=dry_run)
