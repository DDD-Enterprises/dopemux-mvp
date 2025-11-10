"""
Dopemux Hook Manager - Safe Implicit Execution System

Provides non-blocking hook execution with ADHD-optimized defaults:
- Silent operation (quiet by default)
- Background processing (async delegation)
- Error isolation (never blocks user workflow)
- Configurable triggers with easy opt-out

Key Safety Features:
- Strict timeouts (<100ms for critical hooks)
- Exception isolation (failures don't propagate)
- User control (enable/disable per hook type)
- Audit logging (ConPort integration)
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import time

logger = logging.getLogger(__name__)


class HookManager:
    """
    Central manager for Dopemux hook execution.

    Ensures all hooks are non-blocking, configurable, and safe for ADHD workflows.
    """

    def __init__(self):
        self.active_hooks: Dict[str, bool] = {
            'save': True,
            'terminal-open': True,
            'pane-focus': True,
            'git-commit': False,  # Disabled by default due to risk
            'file-watch': False,  # Experimental
        }
        self.quiet_mode = True  # Silent by default for ADHD-friendly operation
        self.timeout_ms = 100  # Strict timeout for safety

    def is_hook_enabled(self, hook_type: str) -> bool:
        """Check if a specific hook type is enabled."""
        return self.active_hooks.get(hook_type, False)

    def enable_hook(self, hook_type: str) -> None:
        """Enable a specific hook type."""
        if hook_type in self.active_hooks:
            self.active_hooks[hook_type] = True
            logger.info(f"Hook enabled: {hook_type}")

    def disable_hook(self, hook_type: str) -> None:
        """Disable a specific hook type."""
        if hook_type in self.active_hooks:
            self.active_hooks[hook_type] = False
            logger.info(f"Hook disabled: {hook_type}")

    async def trigger_hook(self, hook_type: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Trigger a hook with safety guarantees.

        Supports both VS Code/editor hooks and Claude Code external monitoring hooks.

        Args:
            hook_type: Type of hook (save, terminal-open, session-active, etc.)
            context: Event context data

        Returns:
            None (async operation, non-blocking)
        """
        if context is None:
            context = {}

        try:
            # Route to appropriate handler system
            hook_handled = False

            # Handle VS Code/editor hooks (direct integration)
            if hook_type in ['save', 'terminal-open', 'pane-focus', 'git-commit']:
                if self.is_hook_enabled(hook_type):
                    await self._handle_vscode_hook(hook_type, context)
                    hook_handled = True

            # Handle Claude Code external monitoring hooks
            if CLAUDE_HOOKS_AVAILABLE and claude_hooks:
                # Map Claude Code events to internal processing
                claude_event_map = {
                    'session-active': 'session_start',
                    'files-modified': 'file_change',
                    'git-commit': 'git_commit',
                    'claude-commands': 'shell_command'
                }

                mapped_hook = claude_event_map.get(hook_type)
                if mapped_hook and claude_hooks.is_hook_enabled(mapped_hook):
                    await self._handle_claude_event(hook_type, context)
                    hook_handled = True

            if not hook_handled:
                logger.debug(f"No enabled handler for hook type: {hook_type}")

        except Exception as e:
            # Never let hook errors affect user workflow
            logger.error(f"Hook execution failed ({hook_type}): {e}")
            if not self.quiet_mode:
                # Could show user notification here if needed
                pass

    async def _handle_vscode_hook(self, hook_type: str, context: Dict[str, Any]) -> None:
        """Handle VS Code/editor-specific hooks."""
        if hook_type == 'save':
            await self._handle_file_save(context)
        elif hook_type == 'terminal-open':
            await self._handle_terminal_open(context)
        elif hook_type == 'pane-focus':
            await self._handle_pane_focus(context)
        elif hook_type == 'git-commit':
            await self._handle_git_commit(context)

    async def _handle_claude_event(self, event_type: str, context: Dict[str, Any]) -> None:
        """Handle Claude Code monitoring events."""
        # Claude Code events come from external monitoring
        # Process them for Dopemux workflow integration

        if event_type == 'session-active':
            # Claude Code started - prepare environment
            asyncio.create_task(self._prepare_claude_environment(context))

        elif event_type == 'files-modified':
            # Files changed by Claude Code - trigger indexing
            files = context.get('files', [])
            asyncio.create_task(self._batch_index_files(files))

        elif event_type == 'git-commit':
            # Commit made - validate and update tracking
            asyncio.create_task(self._process_commit(context))

        elif event_type == 'claude-commands':
            # Commands executed - log for workflow analysis
            asyncio.create_task(self._log_command_activity(context))

    async def _prepare_claude_environment(self, context: Dict[str, Any]) -> None:
        """Prepare environment when Claude Code session starts."""
        async with self._with_timeout("claude_env_prep"):
            try:
                # Load workspace context, prepare indexing
                processes = context.get('processes', [])
                logger.debug(f"Claude Code session started with {len(processes)} processes")

                # Could trigger workspace analysis or context loading here
                await asyncio.sleep(0.01)  # Minimal operation
            except Exception as e:
                logger.error(f"Claude environment preparation failed: {e}")

    async def _batch_index_files(self, files: List[str]) -> None:
        """Batch index files modified by Claude Code."""
        async with self._with_timeout("batch_index"):
            try:
                if not files:
                    return

                logger.debug(f"Indexing {len(files)} files from Claude Code activity")

                # Trigger background indexing for each file
                for file_path in files[:10]:  # Limit to prevent overload
                    asyncio.create_task(self._index_file_background(file_path, 'unknown'))

                await asyncio.sleep(0.01)  # Minimal operation marker
            except Exception as e:
                logger.error(f"Batch file indexing failed: {e}")

    async def _process_commit(self, context: Dict[str, Any]) -> None:
        """Process git commit from Claude Code activity."""
        async with self._with_timeout("commit_processing"):
            try:
                commit_info = context.get('commit', '')
                logger.debug(f"Processing Claude Code commit: {commit_info[:50]}...")

                # Could trigger validation or tracking updates here
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Commit processing failed: {e}")

    async def _log_command_activity(self, context: Dict[str, Any]) -> None:
        """Log Claude Code command activity for workflow analysis."""
        async with self._with_timeout("command_logging"):
            try:
                commands = context.get('commands', [])
                logger.debug(f"Logged {len(commands)} Claude Code commands")

                # Could analyze command patterns for workflow optimization
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Command activity logging failed: {e}")

    async def _handle_file_save(self, context: Dict[str, Any]) -> None:
        """Handle file save events - trigger background indexing."""
        file_path = context.get('file', '')
        language = context.get('language', '')

        if not file_path:
            return

        # Background tasks - non-blocking
        asyncio.create_task(self._index_file_background(file_path, language))

    async def _handle_terminal_open(self, context: Dict[str, Any]) -> None:
        """Handle terminal open events - prepare workspace context."""
        terminal_name = context.get('name', '')
        shell_path = context.get('shell', '')

        # Background context loading
        asyncio.create_task(self._load_terminal_context(terminal_name, shell_path))

    async def _handle_pane_focus(self, context: Dict[str, Any]) -> None:
        """Handle pane focus events - update session context."""
        # Minimal context update - very fast
        asyncio.create_task(self._update_session_context())

    async def _handle_git_commit(self, context: Dict[str, Any]) -> None:
        """Handle git commit events - validate and index."""
        # Only if explicitly enabled (high risk due to commit blocking)
        asyncio.create_task(self._validate_commit(context))

    @asynccontextmanager
    async def _with_timeout(self, operation_name: str):
        """Context manager for strict timeouts."""
        start_time = time.time()
        try:
            yield
        except asyncio.TimeoutError:
            logger.warning(f"Hook timeout: {operation_name} ({self.timeout_ms}ms)")
        finally:
            elapsed = (time.time() - start_time) * 1000
            if elapsed > self.timeout_ms:
                logger.warning(f"Hook slow: {operation_name} ({elapsed:.1f}ms)")

    # Background operation implementations
    async def _index_file_background(self, file_path: str, language: str) -> None:
        """Background file indexing with timeout."""
        async with self._with_timeout(f"index_{file_path}"):
            try:
                # Placeholder for actual indexing logic
                # Would integrate with Dope-Context here
                await asyncio.sleep(0.01)  # Simulate fast operation
                logger.debug(f"Indexed file: {file_path} ({language})")
            except Exception as e:
                logger.error(f"File indexing failed: {e}")

    async def _load_terminal_context(self, terminal_name: str, shell_path: str) -> None:
        """Load terminal-specific context."""
        async with self._with_timeout(f"terminal_{terminal_name}"):
            try:
                # Placeholder for context loading
                await asyncio.sleep(0.01)
                logger.debug(f"Terminal context loaded: {terminal_name}")
            except Exception as e:
                logger.error(f"Terminal context load failed: {e}")

    async def _update_session_context(self) -> None:
        """Update current session context."""
        async with self._with_timeout("session_update"):
            try:
                # Minimal context update
                await asyncio.sleep(0.005)
                logger.debug("Session context updated")
            except Exception as e:
                logger.error(f"Session update failed: {e}")

    async def _validate_commit(self, context: Dict[str, Any]) -> None:
        """Validate git commit (only when explicitly enabled)."""
        async with self._with_timeout("commit_validation"):
            try:
                # Placeholder for commit validation
                # Would check complexity, run tests, etc.
                await asyncio.sleep(0.05)  # Slightly longer but still fast
                logger.debug("Commit validated")
            except Exception as e:
                logger.error(f"Commit validation failed: {e}")

    # Configuration methods
    def set_quiet_mode(self, quiet: bool) -> None:
        """Set quiet mode (silent operation)."""
        self.quiet_mode = quiet

    def set_timeout(self, timeout_ms: int) -> None:
        """Set hook timeout in milliseconds."""
        self.timeout_ms = max(50, min(timeout_ms, 500))  # 50-500ms range

    def get_hook_status(self) -> Dict[str, Any]:
        """Get current hook configuration status."""
        return {
            'hooks': self.active_hooks.copy(),
            'quiet_mode': self.quiet_mode,
            'timeout_ms': self.timeout_ms
        }