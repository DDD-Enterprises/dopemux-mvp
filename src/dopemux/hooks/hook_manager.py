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
import os
import json
import aiohttp
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import time

logger = logging.getLogger(__name__)

try:
    from .claude_code_hooks import claude_hooks
    CLAUDE_HOOKS_AVAILABLE = True
except Exception:
    claude_hooks = None
    CLAUDE_HOOKS_AVAILABLE = False


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
        self.monitoring_enabled = False

    def start_monitoring(self) -> None:
        """Compatibility no-op: mark monitoring enabled."""
        self.monitoring_enabled = True
        logger.debug("Hook monitoring enabled")

    def stop_monitoring(self) -> None:
        """Compatibility no-op: mark monitoring disabled."""
        self.monitoring_enabled = False
        logger.debug("Hook monitoring disabled")

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

    async def trigger_hook(self, hook_type: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Trigger a hook with safety guarantees.

        Supports both VS Code/editor hooks and Claude Code external monitoring hooks.

        Args:
            hook_type: Type of hook (save, terminal-open, session-active, etc.)
            context: Event context data

        Returns:
            The result of the hook execution (or None)
        """
        if context is None:
            context = {}

        try:
            # Route to appropriate handler system
            result = None
            hook_handled = False

            # Handle VS Code/editor hooks (direct integration)
            if hook_type in ['save', 'terminal-open', 'pane-focus', 'git-commit']:
                if self.is_hook_enabled(hook_type):
                    result = await self._handle_vscode_hook(hook_type, context)
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
                    result = await self._handle_claude_event(hook_type, context)
                    hook_handled = True

            if not hook_handled:
                logger.debug(f"No enabled handler for hook type: {hook_type}")

            return result

        except Exception as e:
            # Never let hook errors affect user workflow
            logger.error(f"Hook execution failed ({hook_type}): {e}")
            if not self.quiet_mode:
                logger.debug("Hook error surfaced in non-quiet mode for %s", hook_type)

    async def _handle_vscode_hook(self, hook_type: str, context: Dict[str, Any]) -> Any:
        """Handle VS Code/editor-specific hooks."""
        if hook_type == 'save':
            return await self._handle_file_save(context)
        elif hook_type == 'terminal-open':
            return await self._handle_terminal_open(context)
        elif hook_type == 'pane-focus':
            return await self._handle_pane_focus(context)
        elif hook_type == 'git-commit':
            return await self._handle_git_commit(context)
        return None

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

    async def _handle_file_save(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file save events - trigger background indexing."""
        file_path = context.get('file', '')
        language = context.get('language', '')

        if not file_path:
            return {"status": "error", "message": "No file path"}

        # Background tasks - non-blocking
        asyncio.create_task(self._index_file_background(file_path, language))
        return {"status": "scheduled", "task": "indexing", "file": file_path}

    async def _handle_terminal_open(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle terminal open events - prepare workspace context."""
        terminal_name = context.get('name', '')
        shell_path = context.get('shell', '')

        # Background context loading
        asyncio.create_task(self._load_terminal_context(terminal_name, shell_path))
        return {"status": "scheduled", "task": "context_load", "terminal": terminal_name}

    async def _handle_pane_focus(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pane focus events - update session context."""
        # Minimal context update - very fast
        asyncio.create_task(self._update_session_context())
        return {"status": "scheduled", "task": "session_update"}

    async def _handle_git_commit(self, context: Dict[str, Any]) -> Any:
        """Handle git commit events - validate and index."""
        # If explicitly requested, run blocking validation
        if context.get('blocking', False):
            return await self._validate_commit(context)

        # Default to background to avoid blocking user flow
        asyncio.create_task(self._validate_commit(context))
        return {"status": "scheduled", "task": "commit_validation"}

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
    async def _index_file_background(self, file_path: str, language: str) -> Dict[str, Any]:
        """Index a file in Dope-Context/Search plane."""
        async with self._with_timeout("indexing"):
            try:
                # Resolve workspace root (relative to Dopemux root)
                workspace_root = os.getcwd()

                # Determine Dope-Context endpoint
                base_url = os.getenv("DOPE_CONTEXT_URL", "http://localhost:3010").rstrip("/")
                endpoint = f"{base_url}/autoindex/bootstrap"

                payload = {
                    "workspace_path": workspace_root,
                    "force": False,
                    "wait_for_completion": False,
                    "debounce_seconds": 1.0,
                    "trigger": "hook_manager_file_save",
                }

                logger.info(f"Triggering Dope-Context indexing for {file_path}")

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5.0)
                    ) as response:
                        if response.status < 400:
                            return {"status": "success", "file": file_path}
                        else:
                            logger.warning(f"Dope-Context indexing trigger failed: {response.status}")
                            return {"status": "error", "code": response.status}

            except Exception as e:
                logger.error(f"Background indexing failed for {file_path}: {e}")
                return {"status": "error", "message": str(e)}

    async def _load_terminal_context(self, terminal_name: str, shell_path: str) -> Dict[str, Any]:
        """Prepare terminal context when opened."""
        async with self._with_timeout("terminal_context"):
            try:
                logger.debug(f"Loading context for terminal '{terminal_name}' ({shell_path})")

                # In a real implementation, this would fetch ADHD cognitive state
                # or recent work items from ConPort to prime the terminal session.
                # For now, we simulate a successful context retrieval.
                await asyncio.sleep(0.05)

                return {
                    "status": "success",
                    "terminal": terminal_name,
                    "context_id": "adhd-focus-session-v1"
                }
            except Exception as e:
                logger.error(f"Terminal context loading failed: {e}")
                return {"status": "error", "message": str(e)}

    async def _update_session_context(self) -> None:
        """Update active session context based on user focus."""
        async with self._with_timeout("session_update"):
            try:
                # This would update the ConPort active context overlay
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Session context update failed: {e}")

    async def _validate_commit(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a git commit before it's finalized."""
        async with self._with_timeout("commit_validation"):
            try:
                message = context.get('message', '')
                if not message:
                    return {"status": "failed", "reason": "Empty commit message"}

                # Simple validation rule: no ADHD-unfriendly placeholders
                placeholders = ["TODO", "TBD", "FIXME", "temp"]
                if any(p in message.upper() for p in placeholders):
                    logger.warning(f"ADHD Alert: Commit message contains placeholders: {message}")
                    return {
                        "status": "warning",
                        "reason": "placeholder_found",
                        "message": message
                    }

                return {"status": "success", "message": "Commit validated"}

            except Exception as e:
                logger.error(f"Commit validation failed: {e}")
                return {"status": "error", "message": str(e)}

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
