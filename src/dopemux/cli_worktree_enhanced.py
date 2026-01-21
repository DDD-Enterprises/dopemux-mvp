#!/usr/bin/env python3
"""
Enhanced CLI commands for worktree management.

This module can be imported into the main CLI to add enhanced worktree commands
that address the issues found in the multi-instance Docker removal analysis.
"""

import click

import logging

logger = logging.getLogger(__name__)

from pathlib import Path
from rich.console import Console

from .worktree_manager_enhanced import (
    EnhancedWorktreeManager,
    create_worktree_safe,
    list_worktrees_adhd,
    cleanup_worktrees_safe,
    switch_worktree_safe,
    archive_worktree_safe
)

console = Console()


def register_enhanced_worktree_commands(cli_group):
    """
    Register enhanced worktree commands with the main CLI.

    This function should be called from the main cli.py to add
    the enhanced worktree commands.

    Args:
        cli_group: The click group to add commands to (usually @cli.group())
    """

    @cli_group.group(name="worktree")
    def worktree():
        """
        🌳 Enhanced worktree management with conflict resolution.

        Provides ADHD-optimized parallel work support with:
        - Branch conflict detection
        - Main branch protection
        - Interactive conflict resolution
        - Orphaned worktree cleanup
        """
        pass

    @worktree.command("create")
    @click.argument("branch_name")
    @click.option(
        "--base", "-b",
        default="main",
        help="Base branch to create from (default: main)"
    )
    @click.pass_context
    def worktree_create(ctx, branch_name: str, base: str):
        """
        🌱 Create a new worktree with conflict detection.

        Checks for branch conflicts and offers resolution options.
        Prevents creating worktrees for main/master branches.

        Examples:
            dopemux worktree create feature/auth
            dopemux worktree create fix/bug-123 --base develop
        """
        if create_worktree_safe(branch_name, base):
            console.logger.info(f"[green]✅ Successfully created worktree for '{branch_name}'[/green]")
        else:
            console.logger.error(f"[red]❌ Failed to create worktree[/red]")
            ctx.exit(1)

    @worktree.command("list")
    @click.option(
        "--all", "-a",
        is_flag=True,
        help="Show all worktrees (default: show 3 most recent)"
    )
    @click.pass_context
    def worktree_list(ctx, all: bool):
        """
        📋 List worktrees with ADHD-friendly display.

        By default shows only 3 most recent worktrees to reduce
        cognitive load. Use --all to see everything.

        Status indicators:
        - ● dirty: Has uncommitted changes
        - ✓ clean: No uncommitted changes
        - → : Current worktree
        """
        list_worktrees_adhd(show_all=all)

    @worktree.command("switch")
    @click.argument("branch_name")
    @click.pass_context
    def worktree_switch(ctx, branch_name: str):
        """
        🔀 Switch to an existing worktree.

        Changes directory to the worktree for the specified branch.

        Example:
            dopemux worktree switch feature/auth
        """
        if not switch_worktree_safe(branch_name):
            console.logger.error(f"[red]❌ Failed to switch to worktree[/red]")
            ctx.exit(1)

    @worktree.command("cleanup")
    @click.option(
        "--dry-run", "-n",
        is_flag=True,
        help="Preview what would be cleaned without actually removing"
    )
    @click.pass_context
    def worktree_cleanup(ctx, dry_run: bool):
        """
        🧹 Clean up orphaned worktrees.

        Removes worktrees whose directories no longer exist.
        Use --dry-run to preview what would be removed.

        Example:
            dopemux worktree cleanup --dry-run
            dopemux worktree cleanup
        """
        cleaned = cleanup_worktrees_safe(dry_run)
        if cleaned > 0 and not dry_run:
            console.logger.info(f"[green]✅ Cleanup complete[/green]")

    @worktree.command("archive")
    @click.argument("branch_name")
    @click.pass_context
    def worktree_archive(ctx, branch_name: str):
        """
        📦 Archive a completed worktree.

        Removes the worktree directory but preserves the branch
        for historical reference. Cannot archive main/master.

        Example:
            dopemux worktree archive feature/completed-feature
        """
        if archive_worktree_safe(branch_name):
            console.logger.info(f"[green]✅ Successfully archived worktree[/green]")
        else:
            console.logger.error(f"[red]❌ Failed to archive worktree[/red]")
            ctx.exit(1)

    @worktree.command("check")
    @click.argument("branch_name")
    @click.pass_context
    def worktree_check(ctx, branch_name: str):
        """
        🔍 Check if a branch is available for worktree creation.

        Verifies whether a branch is already checked out in another
        worktree and reports its location if found.

        Example:
            dopemux worktree check feature/new-feature
        """
        manager = EnhancedWorktreeManager()
        is_available, existing_path = manager.check_branch_availability(branch_name)

        if is_available:
            console.logger.info(f"[green]✅ Branch '{branch_name}' is available for worktree creation[/green]")
        else:
            console.print(
                f"[yellow]⚠️  Branch '{branch_name}' is already checked out at:[/yellow]\n"
                f"    {existing_path}"
            )
            console.logger.info("\n[dim]Tip: Use 'dopemux worktree switch' to go to that worktree[/dim]")
            ctx.exit(1)

    return worktree


# Git hooks content for installation
PRE_CHECKOUT_HOOK = '''#!/bin/bash
# Dopemux worktree protection hook
# Prevents checking out main/master in worktrees

# Check if we're in a worktree (not the main repository)
if [[ "$GIT_DIR" =~ worktree ]]; then
    # Get the branch being checked out (third parameter)
    TARGET_BRANCH="$3"

    # Prevent checkout of main or master
    if [[ "$TARGET_BRANCH" == "main" ]] || [[ "$TARGET_BRANCH" == "master" ]]; then
        echo "❌ ERROR: Cannot checkout main/master in a worktree"
        echo ""
        echo "💡 ADHD Protection: This prevents accumulating work on main branch"
        echo "   Create a feature branch instead:"
        echo ""
        echo "   git checkout -b feature/your-feature-name"
        echo ""
        exit 1
    fi
fi

exit 0
'''

PRE_COMMIT_HOOK = '''#!/bin/bash
# Dopemux worktree protection hook
# Warns when committing on main branch (even in main worktree)

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "master" ]]; then
    echo "⚠️  WARNING: You're committing directly to $BRANCH"
    echo ""
    echo "💡 ADHD Protection: Consider creating a feature branch:"
    echo "   git checkout -b feature/your-feature-name"
    echo "   git commit ..."
    echo ""
    echo "Press Enter to continue anyway, or Ctrl+C to cancel..."
    read
fi

exit 0
'''


def install_worktree_hooks(workspace_path: Path = None):
    """
    Install Git hooks for worktree protection.

    This function installs hooks in the main repository that will
    be inherited by all worktrees.

    Args:
        workspace_path: Path to the git repository (default: current directory)
    """
    workspace_path = workspace_path or Path.cwd()
    hooks_dir = workspace_path / ".git" / "hooks"

    if not hooks_dir.exists():
        console.logger.info(f"[red]❌ Not a git repository: {workspace_path}[/red]")
        return False

    try:
        # Install pre-checkout hook
        pre_checkout_path = hooks_dir / "pre-checkout"
        pre_checkout_path.write_text(PRE_CHECKOUT_HOOK)
        pre_checkout_path.chmod(0o755)
        console.logger.info(f"[green]✅ Installed pre-checkout hook[/green]")

        # Install pre-commit hook
        pre_commit_path = hooks_dir / "pre-commit"
        if not pre_commit_path.exists():
            pre_commit_path.write_text(PRE_COMMIT_HOOK)
            pre_commit_path.chmod(0o755)
            console.logger.info(f"[green]✅ Installed pre-commit hook[/green]")
        else:
            console.logger.info(f"[yellow]⚠️  Pre-commit hook already exists, skipping[/yellow]")

        console.print(
            "\n[cyan]🛡️  Worktree protection hooks installed:[/cyan]\n"
            "  • Pre-checkout: Prevents checking out main in worktrees\n"
            "  • Pre-commit: Warns when committing to main branch"
        )
        return True

    except Exception as e:
        console.logger.error(f"[red]❌ Failed to install hooks: {e}[/red]")
        return False