"""
Uncommitted Change Detection for Main Worktree Protection.

Detects uncommitted changes (staged, unstaged, untracked, stashed) to trigger
worktree creation suggestions when user works in main.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import subprocess
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChangesSummary:
    """Summary of uncommitted changes in a worktree."""

    has_changes: bool
    staged_count: int
    unstaged_count: int
    untracked_count: int
    stashed_count: int
    total_files: int

    def is_clean(self) -> bool:
        """Check if worktree is completely clean (no changes, no stash)."""
        return not self.has_changes and self.stashed_count == 0

    def format_summary(self) -> str:
        """
        Format human-readable summary for ADHD-friendly display.

        Returns:
            Summary string like "3 staged, 2 unstaged, 1 stashed"
        """
        parts = []

        if self.staged_count > 0:
            parts.append(f"{self.staged_count} staged")

        if self.unstaged_count > 0:
            parts.append(f"{self.unstaged_count} unstaged")

        if self.untracked_count > 0:
            parts.append(f"{self.untracked_count} untracked")

        if self.stashed_count > 0:
            parts.append(f"{self.stashed_count} stashed")

        if not parts:
            return "No changes"

        return ", ".join(parts)

    def needs_worktree_suggestion(self) -> bool:
        """
        Determine if changes warrant worktree creation suggestion.

        ADHD Protection: Suggest worktree if any uncommitted changes exist
        to prevent accumulating mess in main.

        Returns:
            True if should suggest worktree creation
        """
        return self.has_changes or self.stashed_count > 0


class UncommittedChangeDetector:
    """Detect uncommitted changes in a git worktree."""

    def __init__(self, workspace_path: str):
        """
        Initialize detector for a workspace.

        Args:
            workspace_path: Absolute path to git repository root
        """
        self.workspace_path = Path(workspace_path)

        if not self._is_git_repo():
            raise ValueError(f"Not a git repository: {workspace_path}")

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository."""
        git_dir = self.workspace_path / ".git"
        return git_dir.exists()

    def _run_git_command(self, args: List[str], timeout: int = 5) -> Optional[str]:
        """
        Run git command and return output.

        Args:
            args: Git command arguments (without 'git' prefix)
            timeout: Command timeout in seconds

        Returns:
            Command output or None on failure
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout
            else:
                logger.warning(f"Git command failed: git {' '.join(args)}")
                logger.debug(f"Error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.warning(f"Git command timed out: git {' '.join(args)}")
            return None
        except Exception as e:
            logger.warning(f"Git command error: {e}")
            return None

    def check_changes(self) -> ChangesSummary:
        """
        Check for uncommitted changes in the worktree.

        Returns:
            ChangesSummary with counts of different change types
        """
        # Get git status in porcelain format (machine-readable)
        status_output = self._run_git_command(["status", "--porcelain"])

        if status_output is None:
            logger.warning("Failed to get git status - assuming no changes")
            return ChangesSummary(
                has_changes=False,
                staged_count=0,
                unstaged_count=0,
                untracked_count=0,
                stashed_count=0,
                total_files=0
            )

        # Parse status output
        staged_count = 0
        unstaged_count = 0
        untracked_count = 0
        seen_files = set()

        for line in status_output.splitlines():
            if not line.strip():
                continue

            # Porcelain format: XY filename
            # X = staged status, Y = unstaged status
            # ' ' = unmodified, M = modified, A = added, D = deleted, etc.
            # ?? = untracked

            if line.startswith("??"):
                # Untracked file
                untracked_count += 1
                seen_files.add(line[3:].strip())
            else:
                # Staged or unstaged change
                x_status = line[0]  # Staged status
                y_status = line[1]  # Unstaged status
                filename = line[3:].strip()

                if filename not in seen_files:
                    seen_files.add(filename)

                    # Check staged status
                    if x_status != ' ' and x_status != '?':
                        staged_count += 1

                    # Check unstaged status
                    if y_status != ' ' and y_status != '?':
                        unstaged_count += 1

        # Check for stashed changes
        stash_output = self._run_git_command(["stash", "list"])
        stashed_count = len(stash_output.splitlines()) if stash_output else 0

        total_files = staged_count + unstaged_count + untracked_count
        has_changes = total_files > 0

        return ChangesSummary(
            has_changes=has_changes,
            staged_count=staged_count,
            unstaged_count=unstaged_count,
            untracked_count=untracked_count,
            stashed_count=stashed_count,
            total_files=total_files
        )

    def is_on_main_branch(self) -> bool:
        """
        Check if current branch is main/master.

        Returns:
            True if on main or master branch
        """
        branch_output = self._run_git_command(["branch", "--show-current"])

        if branch_output is None:
            return False

        current_branch = branch_output.strip()
        return current_branch in ("main", "master")

    def should_suggest_worktree(self) -> bool:
        """
        Determine if should suggest worktree creation.

        ADHD Protection: Suggest if on main with uncommitted changes.

        Returns:
            True if should suggest creating a worktree
        """
        if not self.is_on_main_branch():
            return False

        changes = self.check_changes()
        return changes.needs_worktree_suggestion()

    def get_protection_message(self) -> Optional[str]:
        """
        Get main worktree protection message if applicable.

        Returns:
            Warning message or None if no protection needed
        """
        if not self.is_on_main_branch():
            return None

        changes = self.check_changes()

        if not changes.needs_worktree_suggestion():
            return None

        # Format warning message
        summary = changes.format_summary()

        message = (
            f"⚠️ Main Worktree Protection\n\n"
            f"You have uncommitted changes in main: {summary}\n"
            f"Consider creating a worktree to keep main clean.\n\n"
            f"Would you like to create a worktree for this work?"
        )

        return message


# Synchronous helper for CLI usage
def check_uncommitted_changes(workspace_path: str) -> ChangesSummary:
    """
    Check for uncommitted changes in workspace.

    Args:
        workspace_path: Absolute path to git repository

    Returns:
        ChangesSummary with change counts
    """
    detector = UncommittedChangeDetector(workspace_path)
    return detector.check_changes()


def should_protect_main(workspace_path: str) -> bool:
    """
    Check if main worktree protection should trigger.

    Args:
        workspace_path: Absolute path to git repository

    Returns:
        True if should suggest worktree creation
    """
    try:
        detector = UncommittedChangeDetector(workspace_path)
        return detector.should_suggest_worktree()
    except ValueError:
        # Not a git repo - no protection needed
        return False
