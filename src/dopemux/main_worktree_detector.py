"""
Main Worktree Protection Detector.

Detects when user is working in main worktree with uncommitted changes
and triggers protection flow to suggest worktree creation.

ADHD Optimization: Gentle guidance to prevent accumulating mess in main.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

from .uncommitted_detector import UncommittedChangeDetector, ChangesSummary

logger = logging.getLogger(__name__)


@dataclass
class ProtectionTrigger:
    """
    Trigger information for main worktree protection.

    ADHD Context: Provides all information needed to guide user
    toward worktree creation without cognitive overload.
    """

    workspace_path: str
    git_branch: str
    changes: ChangesSummary
    trigger_reason: str  # Why protection triggered
    suggested_action: str  # What user should do

    def format_warning(self) -> str:
        """
        Format ADHD-friendly warning message.

        Returns:
            Concise, actionable warning with clear next steps
        """
        return (
            f"⚠️  Main Worktree Protection\n\n"
            f"Branch: {self.git_branch}\n"
            f"Changes: {self.changes.format_summary()}\n\n"
            f"💡 {self.suggested_action}\n"
        )


class MainWorktreeDetector:
    """
    Detects and manages main worktree protection.

    ADHD Optimization:
    - Non-intrusive detection
    - Clear, actionable guidance
    - Optional enforcement (warn vs block)
    """

    def __init__(
        self,
        workspace_path: str,
        enforce_protection: bool = False
    ):
        """
        Initialize main worktree detector.

        Args:
            workspace_path: Absolute path to workspace root
            enforce_protection: If True, block operations; if False, warn only
        """
        self.workspace_path = Path(workspace_path)
        self.enforce_protection = enforce_protection
        self.detector = UncommittedChangeDetector(workspace_path)

    def check_protection_needed(self) -> Optional[ProtectionTrigger]:
        """
        Check if main worktree protection should trigger.

        Returns:
            ProtectionTrigger if protection needed, None otherwise
        """
        # Only protect if on main/master branch
        if not self.detector.is_on_main_branch():
            return None

        # Check for uncommitted changes
        changes = self.detector.check_changes()

        # Only trigger if changes exist
        if not changes.needs_worktree_suggestion():
            return None

        # Determine trigger reason
        if changes.staged_count > 0:
            reason = "staged changes in main"
        elif changes.unstaged_count > 0:
            reason = "uncommitted modifications in main"
        elif changes.untracked_count > 0:
            reason = "untracked files in main"
        elif changes.stashed_count > 0:
            reason = "stashed changes in main"
        else:
            reason = "changes detected in main"

        # Create protection trigger
        return ProtectionTrigger(
            workspace_path=str(self.workspace_path),
            git_branch=self.detector._run_git_command(["branch", "--show-current"]).strip(),
            changes=changes,
            trigger_reason=reason,
            suggested_action=(
                "Create a worktree to keep main clean. "
                "Run 'dopemux start' to create a new worktree automatically."
            )
        )

    def should_block_operation(self, operation: str) -> bool:
        """
        Check if operation should be blocked due to main protection.

        Args:
            operation: Operation being attempted (e.g., "commit", "push")

        Returns:
            True if should block, False if should allow with warning
        """
        if not self.enforce_protection:
            return False

        trigger = self.check_protection_needed()
        if not trigger:
            return False

        # Block operations that would persist changes to main
        blocking_operations = {"commit", "push", "merge"}
        return operation.lower() in blocking_operations

    def get_interactive_prompt(self) -> Optional[str]:
        """
        Get interactive prompt for user to create worktree.

        ADHD Optimization: Simple yes/no question with safe default.

        Returns:
            Prompt text or None if no protection needed
        """
        trigger = self.check_protection_needed()
        if not trigger:
            return None

        return (
            f"{trigger.format_warning()}\n"
            f"Would you like to create a worktree now? [y/N]: "
        )


# Synchronous helper functions for CLI usage

def check_main_protection(workspace_path: str) -> Optional[ProtectionTrigger]:
    """
    Check if main worktree protection should trigger.

    Args:
        workspace_path: Absolute path to workspace root

    Returns:
        ProtectionTrigger if protection needed, None otherwise
    """
    try:
        detector = MainWorktreeDetector(workspace_path)
        return detector.check_protection_needed()
    except Exception as e:
        logger.debug(f"Main protection check failed: {e}")
        return None


def should_warn_user(workspace_path: str) -> bool:
    """
    Check if should display warning to user about working in main.

    Args:
        workspace_path: Absolute path to workspace root

    Returns:
        True if warning should be shown
    """
    trigger = check_main_protection(workspace_path)
    return trigger is not None
