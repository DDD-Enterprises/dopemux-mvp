"""
Claude-Code-Tools Integration with Dopemux

Provides hooks and integration points for Claude-Code-Tools functionality
into Dopemux's existing architecture.

This module serves as the bridge between Claude-Code-Tools components
and Dopemux's execution pipeline.
"""

import logging
from typing import Dict, Any, Optional, Callable

from .command_interceptor import CommandInterceptor, get_global_interceptor
from .safety_hooks import SafetyHooks
from .tmux_cli import TmuxCli
from .env_safe import EnvSafe
from .session_manager import SessionManager
from .agent_communication import AgentCommunicator, AgentMessage
from .debugging_support import InteractiveDebugger, DebugSession, DebuggerType

from ..adhd.context_manager import ContextManager
from ..tmux.controller import TmuxController

logger = logging.getLogger(__name__)


class ClaudeToolsIntegration:
    """
    Main integration point for Claude-Code-Tools in Dopemux.

    Provides unified interface to all Claude-Code-Tools functionality
    and integrates with Dopemux's existing systems.
    """

    def __init__(self, context_manager: ContextManager,
                 tmux_controller: Optional[TmuxController] = None):
        """
        Initialize Claude-Code-Tools integration.

        Args:
            context_manager: Dopemux context manager
            tmux_controller: Optional TmuxController instance
        """
        self.context_manager = context_manager
        self.tmux_controller = tmux_controller or TmuxController()

        # Initialize components
        self.safety_hooks = SafetyHooks()
        self.tmux_cli = TmuxCli(self.tmux_controller)
        self.env_safe = EnvSafe()
        self.session_manager = SessionManager(context_manager)
        self.agent_communicator = AgentCommunicator(self.tmux_cli, self.safety_hooks)
        self.interactive_debugger = InteractiveDebugger(self.tmux_cli, self.agent_communicator)

        # Set up command interception
        self.command_interceptor = get_global_interceptor()

        logger.info("Claude-Code-Tools integration initialized")

    def intercept_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Intercept and check a command for safety.

        Args:
            command: Command to check
            context: Optional context information

        Returns:
            Dict with interception results
        """
        try:
            result = self.command_interceptor.check_command(command, context)

            return {
                'allowed': result.result.name == 'ALLOW',
                'result': result.result.name,
                'message': result.message,
                'safe_command': result.safe_command,
                'confirmed': result.confirmed
            }

        except Exception as e:
            logger.error(f"Command interception failed: {e}")
            return {
                'allowed': False,
                'result': 'ERROR',
                'message': f'Interception failed: {e}',
                'safe_command': None,
                'confirmed': False
            }

    def execute_safe_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a command with safety interception.

        Args:
            command: Command to execute
            context: Optional context information

        Returns:
            Command execution result
        """
        def executor(cmd: str) -> Any:
            # This would integrate with Dopemux's command execution system
            # For now, we'll simulate execution
            logger.info(f"Executing safe command: {cmd}")
            return f"Executed: {cmd}"

        return self.command_interceptor.execute_safe_command(command, executor, context)

    # Tmux CLI interface
    def tmux_launch(self, command: str, session_name: Optional[str] = None):
        """Launch command in tmux pane."""
        return self.tmux_cli.launch(command, session_name)

    def tmux_send(self, text: str, pane_id: str, **kwargs):
        """Send text to tmux pane."""
        return self.tmux_cli.send(text, pane_id, **kwargs)

    def tmux_capture(self, pane_id: str, lines: int = 100):
        """Capture output from tmux pane."""
        return self.tmux_cli.capture(pane_id, lines)

    def tmux_interrupt(self, pane_id: str):
        """Interrupt tmux pane."""
        return self.tmux_cli.interrupt(pane_id)

    def tmux_kill(self, pane_id: str):
        """Kill tmux pane."""
        return self.tmux_cli.kill(pane_id)

    def tmux_list_panes(self, session_name: Optional[str] = None):
        """List tmux panes."""
        return self.tmux_cli.list_panes(session_name)

    def tmux_wait_idle(self, pane_id: str, **kwargs):
        """Wait for tmux pane to become idle."""
        return self.tmux_cli.wait_idle(pane_id, **kwargs)

    def tmux_status(self):
        """Get tmux status."""
        return self.tmux_cli.status()

    # Environment Safe interface
    def env_list(self, show_status: bool = False):
        """List environment variables safely."""
        return self.env_safe.list(show_status)

    def env_check(self, key: str):
        """Check if environment variable exists."""
        return self.env_safe.check(key)

    def env_count(self):
        """Count environment variables."""
        return self.env_safe.count()

    def env_validate(self):
        """Validate .env file syntax."""
        return self.env_safe.validate()

    # Session Manager interface
    def session_find(self, keywords: Optional[str] = None,
                    agent_filter: Optional[str] = None,
                    limit: int = 20):
        """Find sessions."""
        return self.session_manager.find_sessions(keywords, agent_filter, limit)

    def session_display(self, sessions):
        """Display sessions in table format."""
        return self.session_manager.display_sessions(sessions)

    def session_resume(self, session):
        """Resume a session."""
        return self.session_manager.resume_session(session)

    # Agent Communication interface
    def send_agent_message(self, pane_id, message, **kwargs):
        """Send message to agent in pane."""
        return self.agent_communicator.send_message(pane_id, message, **kwargs)

    def receive_agent_message(self, pane_id, **kwargs):
        """Receive message from agent in pane."""
        return self.agent_communicator.receive_message(pane_id, **kwargs)

    def collaborate_on_task(self, primary_pane, secondary_pane, task_description, **kwargs):
        """Enable agent collaboration on task."""
        return self.agent_communicator.collaborate_on_task(primary_pane, secondary_pane, task_description, **kwargs)

    def debug_collaboratively(self, debugger_pane, assistant_pane, error_description):
        """Enable collaborative debugging."""
        return self.agent_communicator.debug_collaboratively(debugger_pane, assistant_pane, error_description)

    # Interactive Debugging interface
    def start_debug_session(self, command, debugger=DebuggerType.PDB, **kwargs):
        """Start debugging session."""
        return self.interactive_debugger.start_debug_session(command, debugger, **kwargs)

    def set_debug_breakpoint(self, session, file_path, line):
        """Set breakpoint in debug session."""
        return self.interactive_debugger.set_breakpoint(session, file_path, line)

    def continue_debugging(self, session):
        """Continue execution in debug session."""
        return self.interactive_debugger.continue_execution(session)

    def step_debugging(self, session, step_type='step'):
        """Step through debug session."""
        return self.interactive_debugger.step_execution(session, step_type)

    def inspect_debug_variable(self, session, variable_name):
        """Inspect variable in debug session."""
        return self.interactive_debugger.inspect_variable(session, variable_name)

    def get_debug_stack_trace(self, session):
        """Get stack trace from debug session."""
        return self.interactive_debugger.get_stack_trace(session)

    def get_debug_locals(self, session):
        """Get local variables from debug session."""
        return self.interactive_debugger.get_local_variables(session)

    def quit_debugging(self, session):
        """Quit debug session."""
        return self.interactive_debugger.quit_debugging(session)

    def analyze_error(self, error_output):
        """Analyze error output."""
        return self.interactive_debugger.analyze_error(error_output)


# Global integration instance
_global_integration: Optional[ClaudeToolsIntegration] = None


def get_global_integration() -> Optional[ClaudeToolsIntegration]:
    """Get global Claude-Code-Tools integration instance."""
    return _global_integration


def set_global_integration(integration: ClaudeToolsIntegration) -> None:
    """Set global Claude-Code-Tools integration instance."""
    global _global_integration
    _global_integration = integration


def initialize_integration(context_manager: ContextManager,
                          tmux_controller: Optional[TmuxController] = None) -> ClaudeToolsIntegration:
    """
    Initialize Claude-Code-Tools integration for Dopemux.

    Args:
        context_manager: Dopemux context manager
        tmux_controller: Optional TmuxController instance

    Returns:
        Initialized ClaudeToolsIntegration instance
    """
    integration = ClaudeToolsIntegration(context_manager, tmux_controller)
    set_global_integration(integration)

    logger.info("Claude-Code-Tools integration initialized globally")
    return integration


# Convenience functions for easy access
def check_command(command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Check command safety (convenience function)."""
    integration = get_global_integration()
    if integration:
        return integration.intercept_command(command, context)
    else:
        logger.warning("Claude-Code-Tools integration not initialized")
        return {'allowed': True, 'result': 'ALLOW', 'message': 'Integration not active'}


def safe_execute(command: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """Execute command safely (convenience function)."""
    integration = get_global_integration()
    if integration:
        return integration.execute_safe_command(command, context)
    else:
        logger.warning("Claude-Code-Tools integration not initialized")
        raise RuntimeError("Claude-Code-Tools integration not initialized")