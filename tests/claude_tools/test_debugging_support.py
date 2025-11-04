"""
Unit tests for Claude-Code-Tools debugging support.

Tests interactive debugging workflows and debugger automation.
"""

import pytest
from unittest.mock import Mock, MagicMock

from dopemux.claude_tools.debugging_support import (
    InteractiveDebugger, DebugSession, DebuggerType, DebugState
)
from dopemux.claude_tools.tmux_cli import TmuxCli


class TestInteractiveDebugger:
    """Test InteractiveDebugger functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_tmux = Mock(spec=TmuxCli)
        self.mock_communicator = Mock()
        self.debugger = InteractiveDebugger(self.mock_tmux, self.mock_communicator)

    def test_start_debug_session_pdb(self):
        """Test starting PDB debug session."""
        # Mock pane creation and debugger prompt
        mock_pane = Mock()
        mock_pane.pane_id = "session:0.0"
        self.mock_tmux.launch.return_value = mock_pane
        self.mock_tmux.capture.return_value = "(Pdb) "

        session = self.debugger.start_debug_session("python test.py")

        assert session.debugger_type == DebuggerType.PDB
        assert session.pane_id == "session:0.0"
        assert session.state == DebugState.IDLE
        self.mock_tmux.launch.assert_called_once()

    def test_set_breakpoint(self):
        """Test setting breakpoints."""
        session = DebugSession(
            session_id="test_session",
            pane_id="session:0.0",
            debugger_type=DebuggerType.PDB,
            state=DebugState.IDLE,
            start_time=0,
            last_activity=0
        )
        self.debugger.active_sessions[session.session_id] = session

        success = self.debugger.set_breakpoint(session, "test.py", 10)

        assert success is True
        assert "test.py:10" in session.breakpoints
        self.mock_tmux.send.assert_called_with("b 10", "session:0.0", enter=True)

    def test_continue_execution(self):
        """Test continuing execution."""
        session = DebugSession(
            session_id="test_session",
            pane_id="session:0.0",
            debugger_type=DebuggerType.PDB,
            state=DebugState.IDLE,
            start_time=0,
            last_activity=0
        )
        self.debugger.active_sessions[session.session_id] = session

        new_state = self.debugger.continue_execution(session)

        assert new_state == DebugState.RUNNING
        self.mock_tmux.send.assert_called_with("c", "session:0.0", enter=True)

    def test_step_execution(self):
        """Test stepping through execution."""
        session = DebugSession(
            session_id="test_session",
            pane_id="session:0.0",
            debugger_type=DebuggerType.PDB,
            state=DebugState.IDLE,
            start_time=0,
            last_activity=0
        )
        self.debugger.active_sessions[session.session_id] = session
        self.mock_tmux.capture.return_value = "(Pdb) -> line = 5"

        new_state = self.debugger.step_execution(session, "step")

        assert new_state == DebugState.BREAKPOINT
        self.mock_tmux.send.assert_called_with("s", "session:0.0", enter=True)

    def test_inspect_variable(self):
        """Test variable inspection."""
        session = DebugSession(
            session_id="test_session",
            pane_id="session:0.0",
            debugger_type=DebuggerType.PDB,
            state=DebugState.IDLE,
            start_time=0,
            last_activity=0
        )
        self.debugger.active_sessions[session.session_id] = session
        self.mock_tmux.capture.return_value = "test_var = 42"

        value = self.debugger.inspect_variable(session, "test_var")

        assert "42" in value
        self.mock_tmux.send.assert_called_with("p test_var", "session:0.0", enter=True)

    def test_get_stack_trace_pdb(self):
        """Test getting stack trace from PDB."""
        session = DebugSession(
            session_id="test_session",
            pane_id="session:0.0",
            debugger_type=DebuggerType.PDB,
            state=DebugState.IDLE,
            start_time=0,
            last_activity=0
        )
        self.debugger.active_sessions[session.session_id] = session
        self.mock_tmux.capture.return_value = "-> main()\n  test.py(5)<module>()"

        stack = self.debugger.get_stack_trace(session)

        assert len(stack) >= 1
        self.mock_tmux.send.assert_called_with("w", "session:0.0", enter=True)

    def test_analyze_error_nameerror(self):
        """Test error analysis for NameError."""
        error_output = "NameError: name 'undefined_var' is not defined"

        analysis = self.debugger.analyze_error(error_output)

        assert analysis['error_type'] == 'NameError'
        assert 'undefined variable' in analysis['likely_cause'].lower()
        assert len(analysis['suggested_fixes']) > 0

    def test_analyze_error_typeerror(self):
        """Test error analysis for TypeError."""
        error_output = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"

        analysis = self.debugger.analyze_error(error_output)

        assert analysis['error_type'] == 'TypeError'
        assert 'incorrect data type' in analysis['likely_cause'].lower()

    def test_quit_debugging(self):
        """Test quitting debug session."""
        session = DebugSession(
            session_id="test_session",
            pane_id="session:0.0",
            debugger_type=DebuggerType.PDB,
            state=DebugState.IDLE,
            start_time=0,
            last_activity=0
        )
        self.debugger.active_sessions[session.session_id] = session

        self.debugger.quit_debugging(session)

        assert session.state == DebugState.FINISHED
        self.mock_tmux.send.assert_called_with("q", "session:0.0", enter=True)

    def test_list_sessions(self):
        """Test listing active debug sessions."""
        session1 = DebugSession(
            session_id="session1",
            pane_id="pane1",
            debugger_type=DebuggerType.PDB,
            state=DebugState.IDLE,
            start_time=0,
            last_activity=0
        )
        session2 = DebugSession(
            session_id="session2",
            pane_id="pane2",
            debugger_type=DebuggerType.GDB,
            state=DebugState.RUNNING,
            start_time=0,
            last_activity=0
        )

        self.debugger.active_sessions = {
            "session1": session1,
            "session2": session2
        }

        sessions = self.debugger.list_sessions()

        assert len(sessions) == 2
        assert sessions[0].session_id == "session1"
        assert sessions[1].session_id == "session2"