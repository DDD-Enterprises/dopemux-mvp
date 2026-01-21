"""
Unit tests for Claude-Code-Tools tmux-cli integration.

Tests tmux automation capabilities for AI agents.
"""

import pytest
from unittest.mock import patch, MagicMock

from dopemux.claude_tools.tmux_cli import TmuxCli, TmuxCliError, PaneInfo


class TestTmuxCli:
    """Test TmuxCli functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmux_cli = TmuxCli()

    @patch('subprocess.run')
    def test_launch_command_success(self, mock_subprocess):
        """Test successful command launch."""
        # Mock successful tmux command execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "dopemux"
        mock_subprocess.return_value = mock_result

        result = self.tmux_cli.launch("echo hello", "test-session")

        assert isinstance(result, PaneInfo)
        assert result.session == "test-session"
        assert "claude-tool" in result.window
        assert result.command == "echo hello"

    @patch('subprocess.run')
    def test_launch_command_failure(self, mock_subprocess):
        """Test command launch failure."""
        # Mock failed tmux command
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "tmux error"
        mock_subprocess.return_value = mock_result

        with pytest.raises(TmuxCliError, match="Failed to launch command"):
            self.tmux_cli.launch("invalid command")

    @patch('subprocess.run')
    def test_send_text_success(self, mock_subprocess):
        """Test successful text sending."""
        # Mock successful tmux send-keys
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        self.tmux_cli.send("hello world", "session:0.0")

        # Should call tmux send-keys twice (text + enter)
        assert mock_subprocess.call_count == 2

    @patch('subprocess.run')
    def test_send_text_with_enter_disabled(self, mock_subprocess):
        """Test text sending without enter."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        self.tmux_cli.send("hello world", "session:0.0", enter=False)

        # Should call tmux send-keys only once (text only)
        assert mock_subprocess.call_count == 1

    @patch('subprocess.run')
    def test_capture_output_success(self, mock_subprocess):
        """Test successful output capture."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "captured output"
        mock_subprocess.return_value = mock_result

        result = self.tmux_cli.capture("session:0.0", lines=50)

        assert result == "captured output"

    @patch('subprocess.run')
    def test_interrupt_pane_success(self, mock_subprocess):
        """Test successful pane interrupt."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        self.tmux_cli.interrupt("session:0.0")

        # Verify tmux send-keys C-c was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "send-keys" in call_args
        assert "C-c" in call_args

    @patch('subprocess.run')
    def test_kill_pane_success(self, mock_subprocess):
        """Test successful pane killing."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        self.tmux_cli.kill("session:0.0")

        # Verify tmux kill-pane was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "kill-pane" in call_args

    @patch('subprocess.run')
    def test_list_panes_success(self, mock_subprocess):
        """Test successful pane listing."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "session1 0 0 1 bash\nsession1 0 1 0 python3"
        mock_subprocess.return_value = mock_result

        panes = self.tmux_cli.list_panes()

        assert len(panes) == 2
        assert panes[0].session == "session1"
        assert panes[0].window == "0"
        assert panes[0].pane == "0"
        assert panes[0].active == True
        assert panes[0].command == "bash"

        assert panes[1].session == "session1"
        assert panes[1].window == "0"
        assert panes[1].pane == "1"
        assert panes[1].active == False
        assert panes[1].command == "python3"

    @patch('subprocess.run')
    def test_status_success(self, mock_subprocess):
        """Test successful status retrieval."""
        # Mock current pane query
        mock_current = MagicMock()
        mock_current.returncode = 0
        mock_current.stdout = "session:0.0"

        # Mock list-panes query
        mock_list = MagicMock()
        mock_list.returncode = 0
        mock_list.stdout = "session 0 0 1 bash"

        mock_subprocess.side_effect = [mock_current, mock_list]

        status = self.tmux_cli.status()

        assert status["current_location"] == "session:0.0"
        assert len(status["panes"]) == 1
        assert status["panes"][0]["id"] == "session:0.0"
        assert status["panes"][0]["command"] == "bash"
        assert status["panes"][0]["active"] == True