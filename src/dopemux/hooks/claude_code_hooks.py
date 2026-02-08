"""
Claude Code Integration Hooks for Dopemux

External hook system that integrates with Claude Code CLI through:
- Shell pre/post execution hooks
- File system monitoring for Claude Code operations
- Git integration for commit workflows
- Environment variable detection

Designed for non-blocking, implicit execution that doesn't interfere
with Claude Code's operation.
"""

import asyncio
import json
import os
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import time
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ClaudeCodeHooks:
    """
    External hook system for Claude Code integration.

    Monitors Claude Code activity through file system events,
    shell commands, and git operations to trigger Dopemux workflows.
    """

    def __init__(self):
        self.active_hooks = {
            'file_change': True,    # Monitor Claude Code file modifications
            'git_commit': False,    # Git operations (risky, disabled by default)
            'shell_command': True,  # Shell command monitoring
            'session_start': True,  # Claude Code session detection
        }
        self.quiet_mode = True
        self.watched_paths: List[Path] = []
        self.monitoring_task: Optional[asyncio.Task] = None

    def is_hook_enabled(self, hook_type: str) -> bool:
        """Check if a hook type is enabled."""
        return self.active_hooks.get(hook_type, False)

    def enable_hook(self, hook_type: str) -> None:
        """Enable a specific hook type."""
        if hook_type in self.active_hooks:
            self.active_hooks[hook_type] = True
            logger.info(f"Claude Code hook enabled: {hook_type}")

    def disable_hook(self, hook_type: str) -> None:
        """Disable a specific hook type."""
        if hook_type in self.active_hooks:
            self.active_hooks[hook_type] = False
            logger.info(f"Claude Code hook disabled: {hook_type}")

    def start_monitoring(self, workspace_path: Optional[str] = None) -> None:
        """Start monitoring Claude Code activity."""
        if workspace_path:
            self.watched_paths = [Path(workspace_path)]
        else:
            # Default to current directory and common project locations
            self.watched_paths = [
                Path.cwd(),
                Path.home() / '.claude',
                Path.home() / 'code'
            ]

        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitor_activity())
            logger.info("Claude Code monitoring started")

    def stop_monitoring(self) -> None:
        """Stop monitoring Claude Code activity."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
            logger.info("Claude Code monitoring stopped")

    async def _monitor_activity(self) -> None:
        """Main monitoring loop for Claude Code activity."""
        try:
            while True:
                try:
                    # Check for Claude Code session indicators
                    if self.is_hook_enabled('session_start'):
                        await self._check_claude_session()

                    # Check for file changes
                    if self.is_hook_enabled('file_change'):
                        await self._check_file_changes()

                    # Check for git operations
                    if self.is_hook_enabled('git_commit'):
                        await self._check_git_activity()

                    # Check for shell commands
                    if self.is_hook_enabled('shell_command'):
                        await self._check_shell_activity()

                except Exception as e:
                    logger.error(f"Monitoring error: {e}")

                # Poll every 2 seconds (not too frequent to avoid overhead)
                await asyncio.sleep(2.0)

        except asyncio.CancelledError:
            logger.info("Claude Code monitoring cancelled")
            raise

    async def _check_claude_session(self) -> None:
        """Check for active Claude Code session."""
        try:
            # Check for Claude Code processes
            result = await asyncio.create_subprocess_shell(
                "pgrep -f 'claude' || pgrep -f 'claude-code'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()

            if stdout.strip():
                # Claude Code is running
                await self._trigger_hook('session-active', {
                    'processes': stdout.decode().strip().split('\n')
                })

        except Exception as e:
            logger.debug(f"Session check failed: {e}")

    async def _check_file_changes(self) -> None:
        """Check for recent file modifications that might be from Claude Code."""
        try:
            # Look for recently modified files in watched paths
            for watch_path in self.watched_paths:
                if not watch_path.exists():
                    continue

                # Find files modified in last 10 seconds
                cmd = f"find '{watch_path}' -type f -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.md' -newermt '10 seconds ago' 2>/dev/null"

                result = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await result.communicate()

                if stdout:
                    files = stdout.decode().strip().split('\n')
                    files = [f for f in files if f.strip()]

                    if files:
                        await self._trigger_hook('files-modified', {
                            'files': files[:10],  # Limit to avoid overwhelm
                            'watch_path': str(watch_path)
                        })

        except Exception as e:
            logger.debug(f"File change check failed: {e}")

    async def _check_git_activity(self) -> None:
        """Check for recent git commits that might be from Claude Code."""
        try:
            # Check if we're in a git repo and if there are recent commits
            result = await asyncio.create_subprocess_shell(
                "git log --oneline -1 --since='2 minutes ago' 2>/dev/null || true",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()

            if stdout.strip():
                commit_info = stdout.decode().strip()
                await self._trigger_hook('git-commit', {
                    'commit': commit_info,
                    'timestamp': time.time()
                })

        except Exception as e:
            logger.debug(f"Git activity check failed: {e}")

    async def _check_shell_activity(self) -> None:
        """Monitor shell commands that might indicate Claude Code usage."""
        try:
            # Check recent shell history for Claude Code commands
            # This is a simplified version - in practice you'd need shell integration
            result = await asyncio.create_subprocess_shell(
                "history | tail -5 | grep -i claude || true",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()

            if stdout.strip():
                commands = stdout.decode().strip().split('\n')
                await self._trigger_hook('claude-commands', {
                    'commands': commands,
                    'timestamp': time.time()
                })

        except Exception as e:
            logger.debug(f"Shell activity check failed: {e}")

    async def _trigger_hook(self, event_type: str, context: Dict[str, Any]) -> None:
        """
        Trigger a hook event with safety guarantees.

        Uses Dopemux capture command for direct memory capture.
        """
        try:
            envelope = {
                "event_type": event_type,
                "source": "claude_hook",
                "session_id": os.getenv("CLAUDE_SESSION_ID"),
                "payload": context,
            }
            command = [
                "dopemux",
                "capture",
                "emit",
                "--mode",
                "plugin",
                "--event",
                json.dumps(envelope, ensure_ascii=True),
                "--quiet",
            ]
            child_env = os.environ.copy()
            child_env["DOPEMUX_CAPTURE_CONTEXT"] = "plugin"

            process = await asyncio.create_subprocess_exec(
                *command,
                env=child_env,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(process.wait(), timeout=2.0)

            if process.returncode != 0:
                logger.debug("Hook trigger command failed (%s): %s", process.returncode, command)
        except FileNotFoundError:
            logger.debug("dopemux executable not found; skipping hook trigger for %s", event_type)
        except asyncio.TimeoutError:
            logger.debug("Hook trigger timed out for %s", event_type)
        except Exception as exc:
            logger.debug("Hook trigger failed for %s: %s", event_type, exc)

    # Shell integration helpers
    def generate_shell_hooks(self) -> Dict[str, str]:
        """
        Generate shell hook scripts for manual installation.

        Returns shell scripts that can be added to .bashrc, .zshrc, etc.
        """
        return {
            'bash_preexec': f'''
# Dopemux Claude Code pre-exec hook
dopemux_trigger_preexec() {{
    local cmd="$1"
    DOPEMUX_CAPTURE_CONTEXT=plugin dopemux trigger shell-command --context "{{\\"command\\": \\"$cmd\\"}}" --async --quiet >/dev/null 2>&1 &
    disown 2>/dev/null || true
}}
trap 'dopemux_trigger_preexec "$BASH_COMMAND"' DEBUG
''',

            'bash_precmd': '''
# Dopemux Claude Code post-exec hook
dopemux_trigger_precmd() {
    DOPEMUX_CAPTURE_CONTEXT=plugin dopemux trigger command-done --async --quiet >/dev/null 2>&1 &
    disown 2>/dev/null || true
}
PROMPT_COMMAND="${PROMPT_COMMAND};dopemux_trigger_precmd"
''',

            'zsh_hooks': '''
# Dopemux Claude Code hooks for zsh
autoload -U add-zsh-hook

dopemux_preexec() {
    local cmd="$1"
    DOPEMUX_CAPTURE_CONTEXT=plugin dopemux trigger shell-command --context "{\"command\": \"$cmd\"}" --async --quiet >/dev/null 2>&1 &!
}

dopemux_precmd() {
    DOPEMUX_CAPTURE_CONTEXT=plugin dopemux trigger command-done --async --quiet >/dev/null 2>&1 &!
}

add-zsh-hook preexec dopemux_preexec
add-zsh-hook precmd dopemux_precmd
'''
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current hook system status."""
        return {
            'active_hooks': self.active_hooks.copy(),
            'monitoring_active': self.monitoring_task is not None,
            'watched_paths': [str(p) for p in self.watched_paths],
            'quiet_mode': self.quiet_mode
        }


# Global instance for easy access
claude_hooks = ClaudeCodeHooks()


# Convenience functions
def setup_claude_hooks(workspace_path: Optional[str] = None) -> None:
    """Setup and start Claude Code hooks."""
    claude_hooks.start_monitoring(workspace_path)


def teardown_claude_hooks() -> None:
    """Stop Claude Code hooks."""
    claude_hooks.stop_monitoring()


def get_shell_hook_scripts() -> Dict[str, str]:
    """Get shell hook scripts for manual installation."""
    return claude_hooks.generate_shell_hooks()
