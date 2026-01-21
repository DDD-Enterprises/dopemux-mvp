"""
Interactive Debugging Support for Claude-Code-Tools

Enables AI agents to perform automated debugging workflows through tmux panes,
supporting pdb interaction, error analysis, and step-through debugging.

Based on Claude-Code-Tools interactive debugging patterns.
"""

import re
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .tmux_cli import TmuxCli, PaneInfo
from .agent_communication import AgentCommunicator, AgentMessage


class DebugState(Enum):
    """Current state of debugging session."""
    IDLE = "idle"
    RUNNING = "running"
    BREAKPOINT = "breakpoint"
    ERROR = "error"
    FINISHED = "finished"


class DebuggerType(Enum):
    """Supported debugger types."""
    PDB = "pdb"
    GDB = "gdb"
    LLDB = "lldb"
    CUSTOM = "custom"


@dataclass
class DebugSession:
    """Debugging session information."""
    session_id: str
    pane_id: str
    debugger_type: DebuggerType
    state: DebugState
    start_time: float
    last_activity: float
    breakpoints: List[str] = None
    variables: Dict[str, Any] = None
    call_stack: List[str] = None

    def __post_init__(self):
        if self.breakpoints is None:
            self.breakpoints = []
        if self.variables is None:
            self.variables = {}
        if self.call_stack is None:
            self.call_stack = []


class DebuggingError(Exception):
    """Raised when debugging operations fail."""
    pass


class InteractiveDebugger:
    """
    Interactive debugging support for AI agents.

    Enables automated debugging workflows where agents can:
    - Launch programs under debuggers
    - Set breakpoints and inspect variables
    - Step through code execution
    - Analyze errors and stack traces
    - Collaborate with other agents on debugging tasks
    """

    def __init__(self, tmux_cli: TmuxCli, agent_communicator: Optional[AgentCommunicator] = None):
        """
        Initialize interactive debugger.

        Args:
            tmux_cli: TmuxCli instance for pane operations
            agent_communicator: Optional AgentCommunicator for collaboration
        """
        self.tmux_cli = tmux_cli
        self.agent_communicator = agent_communicator
        self.active_sessions: Dict[str, DebugSession] = {}
        self.debug_patterns = self._initialize_debug_patterns()

    def _initialize_debug_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize debugger-specific patterns and commands."""
        return {
            'pdb': {
                'prompt_pattern': r'^\(Pdb\) ',
                'breakpoint_cmd': 'b {line}',
                'continue_cmd': 'c',
                'step_cmd': 's',
                'next_cmd': 'n',
                'print_cmd': 'p {var}',
                'quit_cmd': 'q',
                'stack_cmd': 'w',
                'locals_cmd': 'locals()',
            },
            'gdb': {
                'prompt_pattern': r'^\(gdb\) ',
                'breakpoint_cmd': 'b {file}:{line}',
                'continue_cmd': 'c',
                'step_cmd': 's',
                'next_cmd': 'n',
                'print_cmd': 'p {var}',
                'quit_cmd': 'q',
                'stack_cmd': 'bt',
                'locals_cmd': 'info locals',
            }
        }

    def start_debug_session(self, command: str, debugger: DebuggerType = DebuggerType.PDB,
                           pane_name: Optional[str] = None) -> DebugSession:
        """
        Start a new debugging session.

        Args:
            command: Command to debug (e.g., "python script.py")
            debugger: Debugger type to use
            pane_name: Optional pane name

        Returns:
            DebugSession object
        """
        try:
            # Prepare debug command
            debug_cmd = self._prepare_debug_command(command, debugger)

            # Launch in tmux pane
            pane = self.tmux_cli.launch(debug_cmd, pane_name)

            # Create session
            session_id = f"debug_{int(time.time())}_{pane.pane_id.replace(':', '_').replace('.', '_')}"
            session = DebugSession(
                session_id=session_id,
                pane_id=pane.pane_id,
                debugger_type=debugger,
                state=DebugState.RUNNING,
                start_time=time.time(),
                last_activity=time.time()
            )

            self.active_sessions[session_id] = session

            # Wait for debugger to start
            self._wait_for_debugger_prompt(session)

            return session

        except Exception as e:
            raise DebuggingError(f"Failed to start debug session: {e}")

            logger.error(f"Error: {e}")
    def _prepare_debug_command(self, command: str, debugger: DebuggerType) -> str:
        """Prepare command for debugging."""
        if debugger == DebuggerType.PDB:
            # For Python, use -m pdb
            if command.startswith('python'):
                return command.replace('python', 'python -m pdb', 1)
            else:
                return f'python -m pdb -c "{command}"'
        elif debugger == DebuggerType.GDB:
            return f'gdb --args {command}'
        else:
            return command  # Custom debugger

    def _wait_for_debugger_prompt(self, session: DebugSession, timeout: float = 10.0) -> None:
        """
        Wait for debugger prompt to appear.

        Args:
            session: Debug session
            timeout: Maximum wait time
        """
        patterns = self.debug_patterns.get(session.debugger_type.value, {})
        prompt_pattern = patterns.get('prompt_pattern', r'> ')

        start_time = time.time()
        while time.time() - start_time < timeout:
            output = self.tmux_cli.capture(session.pane_id, lines=5)

            if re.search(prompt_pattern, output, re.MULTILINE):
                session.state = DebugState.IDLE
                session.last_activity = time.time()
                return

            time.sleep(0.1)

        raise DebuggingError(f"Debugger prompt not found within {timeout} seconds")

    def set_breakpoint(self, session: DebugSession, file_path: str, line: int) -> bool:
        """
        Set a breakpoint in the debugging session.

        Args:
            session: Debug session
            file_path: File path for breakpoint
            line: Line number

        Returns:
            True if successful, False otherwise
        """
        try:
            patterns = self.debug_patterns.get(session.debugger_type.value, {})
            cmd_template = patterns.get('breakpoint_cmd', 'b {file}:{line}')

            if session.debugger_type == DebuggerType.PDB:
                command = cmd_template.format(line=line)
            else:
                command = cmd_template.format(file=file_path, line=line)

            self.tmux_cli.send(command, session.pane_id, enter=True)

            # Wait for confirmation
            time.sleep(0.5)
            session.breakpoints.append(f"{file_path}:{line}")
            session.last_activity = time.time()

            return True

        except Exception as e:
            raise DebuggingError(f"Failed to set breakpoint: {e}")

            logger.error(f"Error: {e}")
    def continue_execution(self, session: DebugSession) -> DebugState:
        """
        Continue execution from current breakpoint.

        Args:
            session: Debug session

        Returns:
            New debug state
        """
        try:
            patterns = self.debug_patterns.get(session.debugger_type.value, {})
            continue_cmd = patterns.get('continue_cmd', 'c')

            self.tmux_cli.send(continue_cmd, session.pane_id, enter=True)

            # Update state
            session.state = DebugState.RUNNING
            session.last_activity = time.time()

            return session.state

        except Exception as e:
            raise DebuggingError(f"Failed to continue execution: {e}")

            logger.error(f"Error: {e}")
    def step_execution(self, session: DebugSession, step_type: str = 'step') -> DebugState:
        """
        Step through execution (step into, step over).

        Args:
            session: Debug session
            step_type: 'step' (into) or 'next' (over)

        Returns:
            New debug state
        """
        try:
            patterns = self.debug_patterns.get(session.debugger_type.value, {})

            if step_type == 'step':
                step_cmd = patterns.get('step_cmd', 's')
            elif step_type == 'next':
                step_cmd = patterns.get('next_cmd', 'n')
            else:
                step_cmd = 's'  # Default to step

            self.tmux_cli.send(step_cmd, session.pane_id, enter=True)

            # Check if we hit a breakpoint or finished
            time.sleep(0.5)
            output = self.tmux_cli.capture(session.pane_id, lines=3)

            if self._is_at_breakpoint(output, session.debugger_type):
                session.state = DebugState.BREAKPOINT
            elif self._is_finished(output, session.debugger_type):
                session.state = DebugState.FINISHED
            else:
                session.state = DebugState.RUNNING

            session.last_activity = time.time()
            return session.state

        except Exception as e:
            raise DebuggingError(f"Failed to step execution: {e}")

            logger.error(f"Error: {e}")
    def inspect_variable(self, session: DebugSession, variable_name: str) -> str:
        """
        Inspect a variable's value.

        Args:
            session: Debug session
            variable_name: Variable to inspect

        Returns:
            Variable value as string
        """
        try:
            patterns = self.debug_patterns.get(session.debugger_type.value, {})
            print_cmd = patterns.get('print_cmd', 'p {var}')
            command = print_cmd.format(var=variable_name)

            self.tmux_cli.send(command, session.pane_id, enter=True)

            # Wait for output
            time.sleep(0.5)
            output = self.tmux_cli.capture(session.pane_id, lines=5)

            # Extract variable value from output
            return self._extract_variable_value(output, variable_name)

        except Exception as e:
            raise DebuggingError(f"Failed to inspect variable {variable_name}: {e}")

            logger.error(f"Error: {e}")
    def get_stack_trace(self, session: DebugSession) -> List[str]:
        """
        Get current stack trace.

        Args:
            session: Debug session

        Returns:
            List of stack frames
        """
        try:
            patterns = self.debug_patterns.get(session.debugger_type.value, {})
            stack_cmd = patterns.get('stack_cmd', 'w')

            self.tmux_cli.send(stack_cmd, session.pane_id, enter=True)

            # Wait for output
            time.sleep(0.5)
            output = self.tmux_cli.capture(session.pane_id, lines=20)

            # Parse stack trace
            return self._parse_stack_trace(output, session.debugger_type)

        except Exception as e:
            raise DebuggingError(f"Failed to get stack trace: {e}")

            logger.error(f"Error: {e}")
    def get_local_variables(self, session: DebugSession) -> Dict[str, Any]:
        """
        Get local variables at current frame.

        Args:
            session: Debug session

        Returns:
            Dict of variable names to values
        """
        try:
            patterns = self.debug_patterns.get(session.debugger_type.value, {})
            locals_cmd = patterns.get('locals_cmd', 'locals()')

            self.tmux_cli.send(locals_cmd, session.pane_id, enter=True)

            # Wait for output
            time.sleep(0.5)
            output = self.tmux_cli.capture(session.pane_id, lines=50)

            # Parse locals output
            return self._parse_locals_output(output, session.debugger_type)

        except Exception as e:
            raise DebuggingError(f"Failed to get local variables: {e}")

            logger.error(f"Error: {e}")
    def quit_debugging(self, session: DebugSession) -> None:
        """
        Quit the debugging session.

        Args:
            session: Debug session
        """
        try:
            patterns = self.debug_patterns.get(session.debugger_type.value, {})
            quit_cmd = patterns.get('quit_cmd', 'q')

            self.tmux_cli.send(quit_cmd, session.pane_id, enter=True)
            session.state = DebugState.FINISHED
            session.last_activity = time.time()

        except Exception as e:
            # Force kill pane if quit fails
            try:
                self.tmux_cli.kill(session.pane_id)
            except Exception as e:
                pass  # Pane might already be dead

                logger.error(f"Error: {e}")
    def analyze_error(self, error_output: str) -> Dict[str, Any]:
        """
        Analyze error output to provide debugging insights.

        Args:
            error_output: Error message/output

        Returns:
            Analysis results
        """
        analysis = {
            'error_type': 'unknown',
            'likely_cause': 'unknown',
            'suggested_fixes': [],
            'severity': 'medium'
        }

        # Common error patterns
        if 'NameError' in error_output:
            analysis['error_type'] = 'NameError'
            analysis['likely_cause'] = 'Undefined variable or function'
            analysis['suggested_fixes'] = ['Check variable spelling', 'Import required modules']
        elif 'TypeError' in error_output:
            analysis['error_type'] = 'TypeError'
            analysis['likely_cause'] = 'Incorrect data type operation'
            analysis['suggested_fixes'] = ['Check data types', 'Add type conversions']
        elif 'ValueError' in error_output:
            analysis['error_type'] = 'ValueError'
            analysis['likely_cause'] = 'Invalid value for operation'
            analysis['suggested_fixes'] = ['Validate input values', 'Add error handling']
        elif 'ImportError' in error_output or 'ModuleNotFoundError' in error_output:
            analysis['error_type'] = 'ImportError'
            analysis['likely_cause'] = 'Missing module or incorrect import'
            analysis['suggested_fixes'] = ['Install required packages', 'Check import paths']

        return analysis

    # Helper methods
    def _is_at_breakpoint(self, output: str, debugger: DebuggerType) -> bool:
        """Check if debugger is at a breakpoint."""
        patterns = self.debug_patterns.get(debugger.value, {})
        prompt_pattern = patterns.get('prompt_pattern', r'> ')
        return bool(re.search(prompt_pattern, output, re.MULTILINE))

    def _is_finished(self, output: str, debugger: DebuggerType) -> bool:
        """Check if debugging session has finished."""
        # Look for exit patterns
        if debugger == DebuggerType.PDB:
            return 'The program finished' in output or 'Post mortem debugger' in output
        return False

    def _extract_variable_value(self, output: str, var_name: str) -> str:
        """Extract variable value from debugger output."""
        # Simple extraction - could be enhanced
        lines = output.split('\n')
        for line in lines:
            if var_name in line and ('=' in line or '->' in line):
                return line.strip()
        return f"Variable {var_name} not found or not accessible"

    def _parse_stack_trace(self, output: str, debugger: DebuggerType) -> List[str]:
        """Parse stack trace from debugger output."""
        frames = []
        lines = output.split('\n')

        if debugger == DebuggerType.PDB:
            # PDB stack trace format
            for line in lines:
                if '->' in line or '  ' in line:  # Indented frames
                    frames.append(line.strip())

        return frames

    def _parse_locals_output(self, output: str, debugger: DebuggerType) -> Dict[str, Any]:
        """Parse local variables from debugger output."""
        variables = {}

        # Simple parsing - could be enhanced based on debugger output format
        lines = output.split('\n')
        for line in lines:
            if '=' in line and not line.startswith(' '):
                try:
                    key, value = line.split('=', 1)
                    variables[key.strip()] = value.strip()
                except ValueError:
                    continue

        return variables

    def get_session(self, session_id: str) -> Optional[DebugSession]:
        """Get debug session by ID."""
        return self.active_sessions.get(session_id)

    def list_sessions(self) -> List[DebugSession]:
        """List all active debug sessions."""
        return list(self.active_sessions.values())

    def cleanup_session(self, session_id: str) -> None:
        """Clean up a debug session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.state != DebugState.FINISHED:
                self.quit_debugging(session)
            del self.active_sessions[session_id]