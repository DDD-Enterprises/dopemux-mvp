#!/usr/bin/env python3
"""
Enhanced Worktree Manager for Dopemux.

Addresses branch conflicts, provides ADHD-optimized UX, and ensures
one-branch-per-worktree policy with safety guardrails.

Improvements over existing implementation:
- Branch conflict detection before creation
- Interactive conflict resolution
- Main branch protection
- Orphaned worktree cleanup
- ADHD-friendly status displays
"""

import os

import logging

logger = logging.getLogger(__name__)

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .console import console


@dataclass
class WorktreeInfo:
    """Information about a git worktree."""
    path: Path
    branch: str
    commit: str
    is_current: bool
    is_dirty: bool
    last_commit_time: Optional[datetime] = None

    @property
    def age_display(self) -> str:
        """Human-readable age of last commit."""
        if not self.last_commit_time:
            return "unknown"

        delta = datetime.now() - self.last_commit_time
        hours = int(delta.total_seconds() / 3600)

        if hours < 1:
            return "< 1 hour"
        elif hours < 24:
            return f"{hours} hours"
        else:
            days = hours // 24
            return f"{days} days"


class EnhancedWorktreeManager:
    """
    Enhanced worktree manager with conflict resolution and ADHD optimizations.
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        """Initialize worktree manager."""
        self.workspace_path = workspace_path or Path.cwd()
        self.main_branches = {"main", "master"}
        self.max_display_options = 3  # ADHD optimization

    def check_branch_availability(self, branch_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if branch is already checked out in another worktree.

        Returns:
            (is_available, worktree_path_if_in_use)
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return True, None

            # Parse worktree list
            current_worktree = None
            for line in result.stdout.split('\n'):
                if line.startswith('worktree '):
                    current_worktree = line.split(' ', 1)[1]
                elif line.startswith('branch refs/heads/') and current_worktree:
                    current_branch = line.split('/')[-1]
                    if current_branch == branch_name:
                        return False, current_worktree

            return True, None

        except Exception as e:
            console.print(f"[error]Error checking branch availability: {e}[/error]")
            return True, None

    def get_all_worktrees(self) -> List[WorktreeInfo]:
        """Get information about all worktrees."""
        worktrees = []

        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse worktree information
            current_info = {}
            for line in result.stdout.split('\n'):
                if line.startswith('worktree '):
                    if current_info:
                        worktrees.append(self._create_worktree_info(current_info))
                    current_info = {'path': line.split(' ', 1)[1]}
                elif line.startswith('HEAD '):
                    current_info['commit'] = line.split(' ', 1)[1]
                elif line.startswith('branch '):
                    # Strip only the refs/heads/ prefix, preserve branch path structure
                    current_info['branch'] = line.split(' ', 1)[1].replace('refs/heads/', '')
                elif line.startswith('detached'):
                    current_info['branch'] = 'detached'

            # Add last worktree
            if current_info:
                worktrees.append(self._create_worktree_info(current_info))

        except subprocess.CalledProcessError as e:
            console.print(f"[error]Error listing worktrees: {e}[/error]")

        return worktrees

    def _create_worktree_info(self, info: Dict) -> WorktreeInfo:
        """Create WorktreeInfo from parsed data."""
        path = Path(info['path'])

        # Check if this is the current worktree
        is_current = path == self.workspace_path.resolve()

        # Check if worktree is dirty
        is_dirty = self._check_dirty_status(path)

        # Get last commit time
        last_commit_time = self._get_last_commit_time(path)

        return WorktreeInfo(
            path=path,
            branch=info.get('branch', 'unknown'),
            commit=info.get('commit', 'unknown')[:8],
            is_current=is_current,
            is_dirty=is_dirty,
            last_commit_time=last_commit_time
        )

    def _check_dirty_status(self, worktree_path: Path) -> bool:
        """Check if worktree has uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False
            )
            return bool(result.stdout.strip())
        except Exception as e:
            logger.debug("Failed to inspect dirty status for %s: %s", worktree_path, e)
            return False
    def _get_last_commit_time(self, worktree_path: Path) -> Optional[datetime]:
        """Get timestamp of last commit in worktree."""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                timestamp = int(result.stdout.strip())
                return datetime.fromtimestamp(timestamp)
        except Exception as e:
            logger.error(f"Error: {e}")
        return None

    def create_worktree(self, branch_name: str, base_branch: str = "main") -> bool:
        """
        Create a new worktree with conflict detection and safety checks.

        Args:
            branch_name: Name of branch to create worktree for
            base_branch: Base branch to create from (default: main)

        Returns:
            True if worktree created successfully
        """
        # Check if branch name is protected
        if branch_name in self.main_branches:
            console.print(
                f"[error]❌ Cannot create worktree for protected branch '{branch_name}'[/error]\n"
                f"[warning]💡 Tip: Use a feature branch name instead[/warning]"
            )
            return False

        # Check if branch is already checked out
        is_available, existing_path = self.check_branch_availability(branch_name)

        if not is_available:
            console.print(
                f"[warning]⚠️  Branch '{branch_name}' is already checked out at:[/warning]\n"
                f"    {existing_path}"
            )

            if Confirm.ask("Would you like to switch to that worktree instead?"):
                return self.switch_to_worktree(branch_name)
            return False

        # Check if branch exists remotely or locally
        branch_exists = self._check_branch_exists(branch_name)

        # Determine worktree path
        worktree_name = branch_name.replace('/', '-')
        worktree_path = self.workspace_path.parent / f"dopemux-{worktree_name}"

        if worktree_path.exists():
            console.print(f"[error]❌ Directory already exists: {worktree_path}[/error]")
            return False

        try:
            if branch_exists:
                # Branch exists, just create worktree
                console.print(f"[info]🌳 Creating worktree for existing branch '{branch_name}'...[/info]")
                cmd = ["git", "worktree", "add", str(worktree_path), branch_name]
            else:
                # Create new branch and worktree
                console.print(f"[info]🌳 Creating new branch '{branch_name}' from '{base_branch}'...[/info]")
                cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch]

            result = subprocess.run(
                cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                console.print(f"[error]❌ Failed to create worktree:[/error]\n{result.stderr}")
                return False

            console.print(f"[success]✅ Worktree created at: {worktree_path}[/success]")

            # Set up worktree configuration
            self._configure_worktree(worktree_path)

            # Offer to switch to new worktree
            if Confirm.ask("Switch to the new worktree now?"):
                os.chdir(worktree_path)
                console.print(f"[success]📍 Switched to: {worktree_path}[/success]")

            return True

        except Exception as e:
            console.print(f"[error]❌ Error creating worktree: {e}[/error]")
            return False

    def _check_branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists locally or remotely."""
        try:
            # Check local branches
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=False
            )
            if result.stdout.strip():
                return True

            # Check remote branches
            result = subprocess.run(
                ["git", "branch", "-r", "--list", f"origin/{branch_name}"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=False
            )
            return bool(result.stdout.strip())

        except Exception as e:
            logger.debug("Failed to inspect branch existence for %s: %s", branch_name, e)
            return False
    def _configure_worktree(self, worktree_path: Path):
        """Configure worktree with hooks and settings."""
        try:
            # Enable worktree-specific config
            subprocess.run(
                ["git", "config", "extensions.worktreeConfig", "true"],
                cwd=worktree_path,
                check=False
            )

            # Add pre-checkout hook to prevent checking out main
            hooks_dir = worktree_path / ".git" / "hooks"
            if not hooks_dir.exists():
                # For worktrees, hooks might be in a different location
                git_dir = worktree_path / ".git"
                if git_dir.is_file():
                    # It's a worktree, read the actual git dir
                    with open(git_dir) as f:
                        actual_git_dir = f.read().strip().split(': ')[1]
                        hooks_dir = Path(actual_git_dir) / "hooks"

            if hooks_dir and hooks_dir.exists():
                pre_checkout_hook = hooks_dir / "pre-checkout"
                hook_content = '''#!/bin/bash
# Prevent checking out main/master in worktree
if [[ "$GIT_DIR" =~ worktree ]] && [[ "$3" =~ ^(main|master)$ ]]; then
    echo "❌ ERROR: Cannot checkout main/master in a worktree"
    echo "💡 Tip: Create a feature branch instead"
    exit 1
fi
'''
                pre_checkout_hook.write_text(hook_content)
                pre_checkout_hook.chmod(0o755)

        except Exception as e:
            console.print(f"[warning]⚠️  Warning: Could not configure worktree hooks: {e}[/warning]")

    def switch_to_worktree(self, branch_name: str) -> bool:
        """
        Switch to an existing worktree by branch name with fuzzy matching.

        ADHD Optimization: Supports case-insensitive partial matching to reduce
        cognitive load of remembering exact branch names.

        Args:
            branch_name: Exact or partial branch name to switch to

        Returns:
            True if switch successful, False otherwise
        """
        worktrees = self.get_all_worktrees()

        if not worktrees:
            console.print("[error]❌ No worktrees found[/error]")
            return False

        # Check if already on target worktree
        current_wt = next((wt for wt in worktrees if wt.is_current), None)
        if current_wt and current_wt.branch == branch_name:
            console.print(f"[warning]ℹ️  Already on worktree: {branch_name}[/warning]")
            return True

        # Try exact match first
        exact_matches = [wt for wt in worktrees if wt.branch == branch_name]
        if exact_matches:
            wt = exact_matches[0]
            console.print(f"[info]🔀 Switching to worktree: {wt.path}[/info]")
            console.print(f"[text.dim]Branch: {wt.branch}[/text.dim]")
            os.chdir(wt.path)
            console.print(f"[success]📍 Now in: {wt.path}[/success]")
            return True

        # Try fuzzy matching (case-insensitive partial match)
        branch_lower = branch_name.lower()
        fuzzy_matches = [
            wt for wt in worktrees
            if branch_lower in wt.branch.lower()
        ]

        if len(fuzzy_matches) == 1:
            wt = fuzzy_matches[0]
            console.print(f"[info]🔎 Fuzzy matched: '{branch_name}' → '{wt.branch}'[/info]")
            console.print(f"[info]🔀 Switching to worktree: {wt.path}[/info]")
            os.chdir(wt.path)
            console.print(f"[success]📍 Now in: {wt.path}[/success]")
            return True
        elif len(fuzzy_matches) > 1:
            console.print(f"[warning]⚠️  Multiple matches found for '{branch_name}':[/warning]")
            for wt in fuzzy_matches:
                console.print(f"  • {wt.branch}")
            console.print("\n[warning]💡 Tip: Please specify the exact branch name[/warning]")
            return False

        # No matches found - show available worktrees
        console.print(f"[error]❌ No worktree found for branch '{branch_name}'[/error]")
        console.print("\n[info]Available worktrees:[/info]")
        for wt in worktrees:
            current_marker = "→ " if wt.is_current else "  "
            console.print(f"{current_marker}• {wt.branch}")
        return False

    def get_worktree_path_for_switch(self, branch_name: str) -> Optional[str]:
        """
        Get worktree path for shell integration (no directory change).

        This method provides the same fuzzy matching logic as switch_to_worktree
        but returns the path instead of changing directories. Designed for shell
        integration where the shell function will execute cd.

        ADHD Optimization: Same case-insensitive partial matching to reduce
        cognitive load of remembering exact branch names.

        Args:
            branch_name: Exact or partial branch name to find

        Returns:
            Absolute path to worktree if found, None otherwise
        """
        worktrees = self.get_all_worktrees()

        if not worktrees:
            return None

        # Check if already on target worktree
        current_wt = next((wt for wt in worktrees if wt.is_current), None)
        if current_wt and current_wt.branch == branch_name:
            return str(current_wt.path)

        # Try exact match first
        exact_matches = [wt for wt in worktrees if wt.branch == branch_name]
        if exact_matches:
            return str(exact_matches[0].path)

        # Try fuzzy matching (case-insensitive partial match)
        branch_lower = branch_name.lower()
        fuzzy_matches = [
            wt for wt in worktrees
            if branch_lower in wt.branch.lower()
        ]

        if len(fuzzy_matches) == 1:
            return str(fuzzy_matches[0].path)
        elif len(fuzzy_matches) > 1:
            # Multiple matches - return None and let caller handle error
            return None

        # No matches found
        return None

    def cleanup_orphaned_worktrees(self, dry_run: bool = False, force: bool = False) -> int:
        """
        Clean up worktrees safely with ADHD-friendly safeguards.

        Cleans:
        - Orphaned worktrees (directories that don't exist)
        - Feature branch worktrees (with safety checks)

        Skips:
        - Main/master worktrees (always protected)
        - Current worktree
        - Dirty worktrees (unless force=True)

        Args:
            dry_run: If True, only show what would be cleaned
            force: If True, clean even dirty worktrees

        Returns:
            Number of worktrees cleaned
        """
        console.print("[info]🧹 Checking for worktrees to clean...[/info]")

        if dry_run:
            console.print("[warning]⚠️  Dry run mode - no changes will be made[/warning]\n")

        cleaned = 0
        try:
            # First, prune truly orphaned entries
            if not dry_run:
                subprocess.run(
                    ["git", "worktree", "prune"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    check=False
                )

            # Check all worktrees
            worktrees = self.get_all_worktrees()
            candidates = []

            for wt in worktrees:
                # Skip main/master worktrees (always protected)
                if wt.branch in self.main_branches:
                    console.print(f"[text.dim]  ⏭️  Skipping main worktree: {wt.branch}[/text.dim]")
                    continue

                # Skip current worktree
                if wt.is_current:
                    console.print(f"[text.dim]  ⏭️  Skipping current worktree: {wt.branch}[/text.dim]")
                    continue

                # Check if directory exists
                if not wt.path.exists():
                    console.print(f"[warning]  • Orphaned worktree: {wt.branch} (directory missing)[/warning]")
                    candidates.append((wt, "orphaned"))
                    continue

                # Check if worktree is dirty
                if wt.is_dirty:
                    if force:
                        console.print(f"[warning]  • Dirty worktree: {wt.branch} (has uncommitted changes) [error]Force mode: Will remove anyway[/error][/warning]")
                        candidates.append((wt, "dirty (forced)"))
                    else:
                        console.print(f"[warning]  ⚠️  Skipping dirty worktree: {wt.branch} (has uncommitted changes, use --force to remove)[/warning]")
                    continue

                # Clean feature branch candidate
                console.print(f"[warning]  • Clean worktree: {wt.branch}[/warning]")
                candidates.append((wt, "clean"))

            # Show summary and process
            if not candidates:
                console.print("\n[success]✅ No worktrees need cleanup[/success]")
                return 0

            console.print(f"\n[info]Found {len(candidates)} worktree(s) to clean[/info]")

            if dry_run:
                console.print("\n[warning]📋 Dry run - no changes made[/warning]")
                for wt, reason in candidates:
                    console.print(f"  • Would remove: {wt.branch} ({reason})")
                return len(candidates)

            # Actually clean (interactive confirmation would go here in real usage)
            for wt, reason in candidates:
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", str(wt.path), "--force"],
                        cwd=self.workspace_path,
                        capture_output=True,
                        check=True
                    )
                    console.print(f"[success]  ✅ Removed: {wt.branch}[/success]")
                    cleaned += 1
                except subprocess.CalledProcessError as e:
                    console.print(f"[error]  ❌ Failed to remove {wt.branch}: {e}[/error]")

            console.print(f"\n[success]✅ Cleaned {cleaned} worktree(s)[/success]")

        except Exception as e:
            console.print(f"[error]❌ Error during cleanup: {e}[/error]")

        return cleaned

    def display_worktrees(self, show_all: bool = False):
        """
        Display worktrees with ADHD-friendly formatting.

        Args:
            show_all: If False, limit to 3 most recent (ADHD optimization)
        """
        worktrees = self.get_all_worktrees()

        if not worktrees:
            console.print("[warning]No worktrees found[/warning]")
            console.print("\n[text.dim]💡 Tip: Create a worktree with 'git worktree add <path> -b <branch>'[/text.dim]")
            return

        # Sort by last commit time (most recent first)
        worktrees.sort(
            key=lambda w: w.last_commit_time or datetime.min,
            reverse=True
        )

        # ADHD optimization: limit display unless requested
        if not show_all and len(worktrees) > self.max_display_options:
            displayed = worktrees[:self.max_display_options]
            hidden_count = len(worktrees) - self.max_display_options
        else:
            displayed = worktrees
            hidden_count = 0

        # Create table
        table = Table(title="🌳 Git Worktrees", show_header=True)
        table.add_column("Branch", style="info", no_wrap=True)
        table.add_column("Path", style="text.dim")
        table.add_column("Status", justify="center")
        table.add_column("Current", justify="center")

        for wt in displayed:
            # Status indicators
            if wt.is_dirty:
                status = Text("● dirty", style="warning")
            else:
                status = Text("✓ clean", style="success")

            # Current indicator
            current = "→" if wt.is_current else ""

            # Branch display
            branch_display = wt.branch
            if wt.branch in self.main_branches:
                branch_display = Text(wt.branch, style="error")

            # Path display (shortened for ADHD friendliness)
            path_display = str(wt.path.name)

            table.add_row(
                branch_display,
                path_display,
                status,
                current
            )

        console.print(table)

        if hidden_count > 0:
            console.print(
                f"\n[text.dim]... and {hidden_count} more. Use --all to see all worktrees[/text.dim]"
            )

        # Tips for ADHD
        console.print("\n💡 Tip: Use 'dopemux worktree switch <branch>' to switch worktrees")

    def archive_completed_worktree(self, branch_name: str) -> bool:
        """
        Archive a completed feature worktree.

        This removes the worktree but keeps the branch for historical reference.
        """
        worktrees = self.get_all_worktrees()

        for wt in worktrees:
            if wt.branch == branch_name:
                if wt.branch in self.main_branches:
                    console.print(f"[error]❌ Cannot archive protected branch '{branch_name}'[/error]")
                    return False

                if wt.is_dirty:
                    console.print(f"[warning]⚠️  Worktree has uncommitted changes[/warning]")
                    if not Confirm.ask("Archive anyway?"):
                        return False

                console.print(f"[info]📦 Archiving worktree for branch '{branch_name}'...[/info]")

                try:
                    # Remove worktree but keep branch
                    subprocess.run(
                        ["git", "worktree", "remove", str(wt.path), "--force"],
                        cwd=self.workspace_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    console.print(f"[success]✅ Archived worktree at: {wt.path}[/success]")
                    console.print(f"[text.dim]Branch '{branch_name}' preserved for historical reference[/text.dim]")

                    return True

                except subprocess.CalledProcessError as e:
                    console.print(f"[error]❌ Failed to archive worktree: {e}[/error]")
                    return False

        console.print(f"[error]❌ No worktree found for branch '{branch_name}'[/error]")
        return False


# Convenience functions for CLI integration
def create_worktree_safe(branch_name: str, base_branch: str = "main", workspace_path: Optional[Path] = None) -> bool:
    """Create worktree with safety checks."""
    manager = EnhancedWorktreeManager(workspace_path)
    return manager.create_worktree(branch_name, base_branch)


def list_worktrees_adhd(show_all: bool = False, workspace_path: Optional[Path] = None):
    """List worktrees with ADHD-friendly display."""
    manager = EnhancedWorktreeManager(workspace_path)
    manager.display_worktrees(show_all)


def cleanup_worktrees_safe(dry_run: bool = False, force: bool = False, workspace_path: Optional[Path] = None) -> int:
    """Clean up orphaned worktrees."""
    manager = EnhancedWorktreeManager(workspace_path)
    return manager.cleanup_orphaned_worktrees(dry_run, force)


def switch_worktree_safe(branch_name: str, workspace_path: Optional[Path] = None) -> bool:
    """Switch to worktree by branch name."""
    manager = EnhancedWorktreeManager(workspace_path)
    return manager.switch_to_worktree(branch_name)


def archive_worktree_safe(branch_name: str, workspace_path: Optional[Path] = None) -> bool:
    """Archive completed worktree."""
    manager = EnhancedWorktreeManager(workspace_path)
    return manager.archive_completed_worktree(branch_name)
