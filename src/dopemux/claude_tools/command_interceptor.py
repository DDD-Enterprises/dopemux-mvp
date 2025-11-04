"""
Command Interceptor for Claude-Code-Tools Safety Hooks

Integrates safety hook checking into Dopemux's command execution pipeline.
Intercepts commands before execution to enforce safety policies.

Based on Claude-Code-Tools PreToolUse hooks pattern.
"""

import re
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

from .safety_hooks import SafetyHooks, SafetyHookError

logger = logging.getLogger(__name__)


class InterceptionResult(Enum):
    """Result of command interception check."""
    ALLOW = "allow"
    BLOCK = "block"
    CONFIRM = "confirm"
    REDIRECT = "redirect"


@dataclass
class CommandCheckResult:
    """Result of command safety check."""
    result: InterceptionResult
    message: str
    safe_command: Optional[str] = None
    confirmed: bool = False


class CommandInterceptor:
    """
    Command interceptor for safety hook enforcement.

    Integrates with Dopemux's execution pipeline to check commands
    before they are executed by AI agents.
    """

    def __init__(self, safety_hooks: Optional[SafetyHooks] = None):
        """
        Initialize command interceptor.

        Args:
            safety_hooks: SafetyHooks instance (created if None)
        """
        self.safety_hooks = safety_hooks or SafetyHooks()
        self.interceptors: List[Callable] = []
        self._setup_default_interceptors()

    def _setup_default_interceptors(self) -> None:
        """Set up default safety interceptors."""
        self.interceptors.extend([
            self._intercept_rm_commands,
            self._intercept_git_commands,
            self._intercept_env_access,
            self._intercept_file_operations,
            self._intercept_grep_usage,
        ])

    def check_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> CommandCheckResult:
        """
        Check a command against all safety interceptors.

        Args:
            command: Command string to check
            context: Optional context information

        Returns:
            CommandCheckResult with safety assessment
        """
        context = context or {}

        # Run safety hooks check first
        try:
            hook_result = self.safety_hooks.check_command(command, context)

            if not hook_result['allowed']:
                if hook_result['action'] == 'redirect':
                    return CommandCheckResult(
                        result=InterceptionResult.REDIRECT,
                        message=hook_result['message'],
                        safe_command=hook_result.get('safe_command')
                    )
                elif hook_result['action'] == 'confirm':
                    return CommandCheckResult(
                        result=InterceptionResult.CONFIRM,
                        message=hook_result['message']
                    )
                else:
                    return CommandCheckResult(
                        result=InterceptionResult.BLOCK,
                        message=hook_result['message']
                    )

        except SafetyHookError as e:
            logger.warning(f"Safety hook error: {e}")
            return CommandCheckResult(
                result=InterceptionResult.BLOCK,
                message=f"Safety check failed: {e}"
            )

        # Run additional interceptors
        for interceptor in self.interceptors:
            try:
                result = interceptor(command, context)
                if result.result != InterceptionResult.ALLOW:
                    return result
            except Exception as e:
                logger.error(f"Interceptor error in {interceptor.__name__}: {e}")

        return CommandCheckResult(
            result=InterceptionResult.ALLOW,
            message="Command passed all safety checks"
        )

    def execute_safe_command(self, command: str, executor: Callable[[str], Any],
                           context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a command with safety interception.

        Args:
            command: Command to execute
            executor: Function to execute the command (should take command string)
            context: Optional context information

        Returns:
            Execution result

        Raises:
            SafetyHookError: If command is blocked
            CommandInterceptorError: If execution fails
        """
        # Check command safety
        check_result = self.check_command(command, context)

        if check_result.result == InterceptionResult.BLOCK:
            raise SafetyHookError(f"Command blocked: {check_result.message}")

        elif check_result.result == InterceptionResult.CONFIRM:
            if not context or not context.get('confirmed', False):
                raise SafetyHookError(f"Command requires confirmation: {check_result.message}")

        elif check_result.result == InterceptionResult.REDIRECT:
            if check_result.safe_command:
                logger.info(f"Redirecting command: {command} -> {check_result.safe_command}")
                command = check_result.safe_command
            else:
                raise SafetyHookError("Redirect requested but no safe command provided")

        # Execute the command
        try:
            return executor(command)
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise CommandInterceptorError(f"Failed to execute command: {e}")

    def add_interceptor(self, interceptor: Callable[[str, Dict[str, Any]], CommandCheckResult]) -> None:
        """
        Add a custom interceptor.

        Args:
            interceptor: Function that takes (command, context) and returns CommandCheckResult
        """
        self.interceptors.append(interceptor)

    def _intercept_rm_commands(self, command: str, context: Dict[str, Any]) -> CommandCheckResult:
        """Intercept dangerous rm commands."""
        if not command.startswith('rm '):
            return CommandCheckResult(InterceptionResult.ALLOW, "")

        # Block dangerous rm patterns
        dangerous_patterns = [
            r'rm\s+.*--no-preserve-root',
            r'rm\s+-rf\s*/',
            r'rm\s+-rf\s+/.*',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command):
                return CommandCheckResult(
                    InterceptionResult.BLOCK,
                    "Blocked: Dangerous rm operation that could delete system files"
                )

        return CommandCheckResult(InterceptionResult.ALLOW, "")

    def _intercept_git_commands(self, command: str, context: Dict[str, Any]) -> CommandCheckResult:
        """Intercept dangerous git commands."""
        if not command.startswith('git '):
            return CommandCheckResult(InterceptionResult.ALLOW, "")

        # Block dangerous git patterns
        if re.search(r'git\s+(add|commit)\s+.*(-A|--all|\.)', command):
            return CommandCheckResult(
                InterceptionResult.BLOCK,
                "Blocked: Broad git operation. Add specific files instead."
            )

        if re.search(r'git\s+checkout\s+.*(-f|--force)', command):
            return CommandCheckResult(
                InterceptionResult.BLOCK,
                "Blocked: Force checkout operation"
            )

        # Require confirmation for commits
        if re.search(r'git\s+commit', command) and not context.get('confirmed', False):
            return CommandCheckResult(
                InterceptionResult.CONFIRM,
                "Git commit requires confirmation. Please confirm."
            )

        return CommandCheckResult(InterceptionResult.ALLOW, "")

    def _intercept_env_access(self, command: str, context: Dict[str, Any]) -> CommandCheckResult:
        """Intercept direct environment file access."""
        # Block direct .env file access
        env_patterns = [
            r'\bcat\s+.*\.env',
            r'\bgrep\s+.*\.env',
            r'\bsed\s+.*\.env',
            r'\bopen\s+.*\.env',
            r'\bread\s+.*\.env',
        ]

        for pattern in env_patterns:
            if re.search(pattern, command):
                return CommandCheckResult(
                    InterceptionResult.BLOCK,
                    "Direct .env access blocked. Use 'dmx env list' instead."
                )

        return CommandCheckResult(InterceptionResult.ALLOW, "")

    def _intercept_file_operations(self, command: str, context: Dict[str, Any]) -> CommandCheckResult:
        """Intercept file operations for size limits."""
        # Check for file reading operations
        read_commands = ['cat', 'less', 'more', 'head', 'tail', 'grep', 'sed', 'awk']

        for cmd in read_commands:
            if cmd in command:
                # Extract potential file paths and check sizes
                # This is a simplified implementation - could be enhanced
                break

        return CommandCheckResult(InterceptionResult.ALLOW, "")

    def _intercept_grep_usage(self, command: str, context: Dict[str, Any]) -> CommandCheckResult:
        """Intercept grep usage and suggest ripgrep."""
        if 'grep' in command and 'rg' not in command:
            return CommandCheckResult(
                InterceptionResult.BLOCK,
                "Use 'rg' (ripgrep) instead of 'grep' for better performance."
            )

        return CommandCheckResult(InterceptionResult.ALLOW, "")


class CommandInterceptorError(Exception):
    """Raised when command interception fails."""
    pass


# Global interceptor instance
_global_interceptor: Optional[CommandInterceptor] = None


def get_global_interceptor() -> CommandInterceptor:
    """Get or create global command interceptor."""
    global _global_interceptor
    if _global_interceptor is None:
        _global_interceptor = CommandInterceptor()
    return _global_interceptor


def set_global_interceptor(interceptor: CommandInterceptor) -> None:
    """Set the global command interceptor."""
    global _global_interceptor
    _global_interceptor = interceptor