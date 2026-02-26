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
import inspect
import os
import subprocess
import asyncio
import inspect
import logging

from .instance_state import (
    InstanceState,
    InstanceStateManager,
    resolve_conport_port,
)

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
        conport_port: int = 3004,
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
        # Allow override via env var; default extended to 30 days
        try:
            env_days = int(os.getenv("DOPEMUX_RECOVERY_MAX_DAYS", "0"))
            self.max_age_days = env_days if env_days > 0 else max_age_days
        except Exception:
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

        print(f"\n  0. 🏠 Stay in main worktree (default after {self.timeout_seconds}s; press Enter)")

        if has_more:
            print("  a. 📋 Show all recoverable sessions")

        print("\n" + "=" * 70)
        print("💡 Tip: Choose a session to restore context and continue where you left off")

    async def get_user_input_async(self, prompt: str, timeout: int) -> Optional[str]:
        """
        Get user input asynchronously with timeout.

        Args:
            prompt: Input prompt to display
            timeout: Timeout in seconds

        Returns:
            User input or None on timeout
        """
        import sys
        import selectors

        # Check if stdin is a real file (pytest replaces it with DontReadFromInput)
        try:
            sys.stdin.fileno()
        except (AttributeError, ValueError):
            # stdin is not a real file (e.g., in pytest) - return None immediately
            return None

        print(prompt, end='', flush=True)

        # Use selector for async-compatible input
        selector = selectors.DefaultSelector()

        # Register stdin - may fail with errno 22 if stdin is redirected/pipe/non-terminal
        try:
            selector.register(sys.stdin, selectors.EVENT_READ)
        except OSError as e:
            # errno 22 (Invalid argument) when stdin isn't a proper terminal
            logger.debug(f"Cannot register stdin with selector: {e}")
            selector.close()
            return None

        loop = asyncio.get_event_loop()

        try:
            # Wait for input with timeout
            start_time = asyncio.get_event_loop().time()
            while True:
                remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                if remaining <= 0:
                    raise asyncio.TimeoutError()

                # Check if input is ready (non-blocking)
                events = selector.select(timeout=0.1)
                if events:
                    user_input = sys.stdin.readline().strip()
                    return user_input

                await asyncio.sleep(0.1)  # Yield to event loop

        except asyncio.TimeoutError:
            print()  # Newline after timeout
            return None
        finally:
            selector.unregister(sys.stdin)
            selector.close()

    async def get_user_choice(
        self,
        options: List[RecoveryOption],
        timeout: Optional[int] = None,
        allow_show_all: bool = False
    ) -> Optional[RecoveryOption]:
        """
        Get user's recovery choice with timeout.

        Args:
            options: Available recovery options
            timeout: Timeout in seconds (None = use instance default)
            allow_show_all: Whether to allow 'a' for show all

        Returns:
            Selected RecoveryOption, None (stay in main), or 'show_all' marker
        """
        if not options:
            return None

        timeout_val = timeout if timeout is not None else self.timeout_seconds

        try:
            prompt = f"Your choice (0-{len(options)}"
            if allow_show_all:
                prompt += ", a"
            prompt += f") [{timeout_val}s timeout]: "

            user_input = await self.get_user_input_async(prompt, timeout_val)

            if user_input is None:
                # Timeout - use safe default
                logger.info("⏱️ Timeout - staying in main worktree")
                return None

            # Handle "show all" request
            if user_input.lower() == 'a' and allow_show_all:
                return "show_all"  # Marker for show all

            # Parse numeric choice
            try:
                choice_num = int(user_input)

                # Choice 0 = stay in main
                if choice_num == 0:
                    logger.info("🏠 User chose to stay in main worktree")
                    return None

                # Validate range
                if 1 <= choice_num <= len(options):
                    selected = options[choice_num - 1]
                    logger.info(f"✅ User selected: {selected.git_branch}")
                    return selected
                else:
                    print(f"❌ Invalid choice: {choice_num}. Using default (main).")
                    return None

            except ValueError:
                print(f"❌ Invalid input: '{user_input}'. Using default (main).")
                return None

        except asyncio.TimeoutError:
            logger.info("⏱️ Timeout - staying in main worktree")
            return None

    async def find_all_recoverable_sessions(self) -> List[RecoveryOption]:
        """
        Find ALL recoverable worktree sessions (up to 10).

        Used for "show all" progressive disclosure.

        Returns:
            List of RecoveryOption objects (max 10)
        """
        orphaned = await self.manager.find_orphaned_instances_filtered(
            max_age_days=self.max_age_days,
            limit=10,  # Show up to 10 when user requests "show all"
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

    async def fallback_to_git_worktree_list(self) -> List[RecoveryOption]:
        """
        Fallback to git worktree list when ConPort unavailable.

        Graceful degradation: Use git directly to find worktrees.

        Returns:
            List of RecoveryOption objects from git worktree list
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.workspace_id,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.warning("⚠️ git worktree list failed - no recovery options")
                return []

            # Parse git worktree list output
            options = []
            current_worktree = {}

            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    # Blank line separates worktrees
                    if self._should_include_worktree(current_worktree):
                        options.append(self._create_option_from_git(current_worktree, len(options) + 1))
                    current_worktree = {}
                elif line.startswith("worktree "):
                    current_worktree["path"] = line.split(" ", 1)[1]
                elif line.startswith("branch "):
                    # Format: "branch refs/heads/feature/test" -> "feature/test"
                    branch_ref = line.split(" ", 1)[1]
                    current_worktree["branch"] = branch_ref.replace("refs/heads/", "")

            # Handle last worktree
            if self._should_include_worktree(current_worktree):
                options.append(self._create_option_from_git(current_worktree, len(options) + 1))

            logger.info(f"📋 Found {len(options)} worktrees via git fallback")
            return options[:3]  # ADHD max 3 for initial display

        except Exception as e:
            logger.warning(f"⚠️ Git worktree fallback failed: {e}")
            return []

    def _should_include_worktree(self, worktree_data: dict) -> bool:
        """Check if worktree should be included in recovery options."""
        if not worktree_data:
            return False

        # Exclude main worktree by path
        if worktree_data.get("path") == self.workspace_id:
            return False

        # Exclude main/master branches (these are typically the main worktree)
        branch = worktree_data.get("branch", "")
        if branch in ("main", "master"):
            return False

        return True

    def _create_option_from_git(self, worktree_data: dict, index: int) -> RecoveryOption:
        """Create RecoveryOption from git worktree data."""
        return RecoveryOption(
            instance_id=f"git-{index}",
            worktree_path=worktree_data["path"],
            git_branch=worktree_data.get("branch", "unknown"),
            last_active=datetime.now(),  # No timestamp from git
            last_focus=None,
            display_index=index
        )

    async def show_recovery_menu(self) -> Optional[str]:
        """
        Show recovery menu and get user selection with progressive disclosure.

        ADHD Optimization:
        - Show 3 most recent initially
        - Allow "show all" to expand to 10
        - 30s timeout with safe default (main)
        - Graceful degradation to git worktree list

        Returns:
            Selected worktree path or None (stay in main)
        """
        # Find recoverable sessions
        options = await self.find_recoverable_sessions()

        # Fallback to git worktree list if ConPort unavailable
        if not options and not self.manager.conport_available:
            logger.warning("⚠️ ConPort unavailable - trying git worktree fallback")
            options = await self.fallback_to_git_worktree_list()

        if not options:
            logger.debug("No orphaned sessions found - proceeding to main")
            return None

        # Check if there are more sessions
        has_more = await self.check_has_more_sessions()

        while True:  # Loop for "show all" handling
            # Display menu
            self.display_menu(options, has_more)

            # Get user choice
            choice = await self.get_user_choice(options, allow_show_all=has_more)

            # Handle "show all" request
            if choice == "show_all":
                logger.info("📋 Expanding to show all recoverable sessions...")
                all_options = await self.find_all_recoverable_sessions()
                if all_options:
                    options = all_options
                    has_more = False  # No more to show
                    print()  # Blank line before re-display
                    continue
                else:
                    print("⚠️ No additional sessions found.")
                    has_more = False
                    continue

            # Handle normal choice
            if choice:
                logger.info(f"✅ User selected: {choice.git_branch}")
                return choice.worktree_path
            else:
                logger.info("🏠 Staying in main worktree")
                return None


# Synchronous wrapper for CLI usage
def show_recovery_menu_sync(
    workspace_id: str,
    conport_port: Optional[int] = None
) -> Optional[str]:
    """
    Synchronous wrapper for show_recovery_menu.

    Args:
        workspace_id: Workspace root path
        conport_port: ConPort API port

    Returns:
        Selected worktree path or None
    """
    async def _run_with_cleanup():
        """Run menu and ensure cleanup of aiohttp sessions."""
        resolved_port = resolve_conport_port(conport_port)
        menu = WorktreeRecoveryMenu(workspace_id, resolved_port)
        try:
            return await menu.show_recovery_menu()
        finally:
            manager = getattr(menu, "manager", None)
            cleanup = getattr(manager, "_close_session", None)
            if cleanup:
                try:
                    if inspect.iscoroutinefunction(cleanup):
                        await cleanup()
                    else:
                        maybe_result = cleanup()
                        if inspect.isawaitable(maybe_result):
                            await maybe_result
                except Exception as exc:  # pragma: no cover - best effort cleanup
                    logger.debug("Recovery menu cleanup skipped: %s", exc)

    return asyncio.run(_run_with_cleanup())
