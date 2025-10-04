"""
Worktree Recovery Menu for ADHD-Optimized Session Recovery.

Provides startup menu for recovering orphaned worktree sessions with:
- Max 3 options to reduce decision paralysis
- 30-second timeout with safe default (stay in main)
- Progressive disclosure (show all if needed)
- Visual status indicators
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import subprocess
import asyncio
import logging

from .instance_state import InstanceState, InstanceStateManager

logger = logging.getLogger(__name__)


@dataclass
class RecoveryOption:
    """A single recovery menu option."""

    instance_id: str
    worktree_path: str
    git_branch: str
    last_active: datetime
    last_focus: Optional[str] = None
    display_index: int = 1

    def age_display(self) -> str:
        """Human-readable age since last active."""
        delta = datetime.now() - self.last_active
        hours = int(delta.total_seconds() / 3600)
        if hours < 1:
            return "< 1 hour ago"
        elif hours < 24:
            return f"{hours} hours ago"
        else:
            days = hours // 24
            return f"{days} days ago"

    def format_menu_line(self) -> str:
        """Format as menu line with visual indicators."""
        focus_info = f" | {self.last_focus[:40]}..." if self.last_focus else ""
        return f"  {self.display_index}. 🌳 {self.git_branch} ({self.age_display()}){focus_info}"


class WorktreeRecoveryMenu:
    """Interactive menu for recovering orphaned worktree sessions."""

    def __init__(
        self,
        workspace_id: str,
        conport_port: int = 3007,
        max_age_days: int = 7,
        timeout_seconds: int = 30
    ):
        """
        Initialize recovery menu.

        Args:
            workspace_id: Absolute path to workspace root
            conport_port: ConPort API port
            max_age_days: Only show worktrees newer than this
            timeout_seconds: Timeout for user input (ADHD-friendly default: 30s)
        """
        self.workspace_id = workspace_id
        self.manager = InstanceStateManager(workspace_id, conport_port)
        self.max_age_days = max_age_days
        self.timeout_seconds = timeout_seconds

    async def find_recoverable_sessions(self) -> List[RecoveryOption]:
        """
        Find recoverable worktree sessions.

        ADHD Optimization: Limits to 3 most recent by default.

        Returns:
            List of RecoveryOption objects (max 3 for menu, more available via "show all")
        """
        orphaned = await self.manager.find_orphaned_instances_filtered(
            max_age_days=self.max_age_days,
            limit=3,  # ADHD max for initial display
            sort_by_recent=True
        )

        options = []
        for idx, state in enumerate(orphaned, start=1):
            options.append(RecoveryOption(
                instance_id=state.instance_id,
                worktree_path=state.worktree_path,
                git_branch=state.git_branch,
                last_active=state.last_active,
                last_focus=state.last_focus_context,
                display_index=idx
            ))

        return options

    async def check_has_more_sessions(self) -> bool:
        """Check if there are more than 3 recoverable sessions."""
        orphaned = await self.manager.find_orphaned_instances_filtered(
            max_age_days=self.max_age_days,
            limit=10,  # Check up to 10
            sort_by_recent=True
        )
        return len(orphaned) > 3

    def display_menu(self, options: List[RecoveryOption], has_more: bool = False) -> None:
        """
        Display recovery menu with ADHD-friendly formatting.

        Args:
            options: Recovery options to display
            has_more: Whether there are more options available
        """
        if not options:
            return

        print("\n" + "=" * 70)
        print("🔄 Found orphaned worktree sessions - would you like to recover one?")
        print("=" * 70)

        for opt in options:
            print(opt.format_menu_line())

        print(f"\n  0. 🏠 Stay in main worktree (default after {self.timeout_seconds}s)")

        if has_more:
            print("  a. 📋 Show all recoverable sessions")

        print("\n" + "=" * 70)
        print("💡 Tip: Choose a session to restore context and continue where you left off")

    async def get_user_choice(
        self,
        options: List[RecoveryOption],
        timeout: Optional[int] = None
    ) -> Optional[RecoveryOption]:
        """
        Get user's recovery choice with timeout.

        Args:
            options: Available recovery options
            timeout: Timeout in seconds (None = use instance default)

        Returns:
            Selected RecoveryOption or None (stay in main)
        """
        if not options:
            return None

        timeout_val = timeout if timeout is not None else self.timeout_seconds

        try:
            # TODO: Implement async input with timeout
            # For now, placeholder for actual implementation
            logger.info(f"Awaiting user input (timeout: {timeout_val}s)...")
            # Will implement actual async input in next step
            return None

        except asyncio.TimeoutError:
            logger.info("⏱️ Timeout - staying in main worktree")
            return None

    async def show_recovery_menu(self) -> Optional[str]:
        """
        Show recovery menu and get user selection.

        Returns:
            Selected worktree path or None (stay in main)
        """
        # Find recoverable sessions
        options = await self.find_recoverable_sessions()

        if not options:
            logger.debug("No orphaned sessions found - proceeding to main")
            return None

        # Check if there are more sessions
        has_more = await self.check_has_more_sessions()

        # Display menu
        self.display_menu(options, has_more)

        # Get user choice
        choice = await self.get_user_choice(options)

        if choice:
            logger.info(f"✅ User selected: {choice.git_branch}")
            return choice.worktree_path
        else:
            logger.info("🏠 Staying in main worktree")
            return None


# Synchronous wrapper for CLI usage
def show_recovery_menu_sync(
    workspace_id: str,
    conport_port: int = 3007
) -> Optional[str]:
    """
    Synchronous wrapper for show_recovery_menu.

    Args:
        workspace_id: Workspace root path
        conport_port: ConPort API port

    Returns:
        Selected worktree path or None
    """
    menu = WorktreeRecoveryMenu(workspace_id, conport_port)
    return asyncio.run(menu.show_recovery_menu())
