"""
Tests for the CLI module.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from dopemux.cli import cli


class TestCLI:
    """Test CLI commands."""

    def test_show_version(self):
        """Test version callback function."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "Dopemux" in result.output

    def test_cli_group_help(self):
        """Test CLI group help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "ADHD-optimized development platform" in result.output
        assert "init" in result.output
        assert "start" in result.output
        assert "save" in result.output
        assert "restore" in result.output
        assert "status" in result.output
        assert "task" in result.output

    def test_cli_verbose_flag(self):
        """Test verbose flag is passed to context."""
        runner = CliRunner()

        # Mock the init command to access context
        with patch("dopemux.cli.ConfigManager"):
            with patch("dopemux.cli.Path.exists", return_value=True):
                with patch("dopemux.cli.Path.resolve", return_value=Path("/test")):
                    with patch("dopemux.cli.ClaudeConfigurator"):
                        with patch("dopemux.cli.ContextManager"):
                            result = runner.invoke(cli, ["-v", "init", "."])

        # Should not fail with verbose flag
        assert result.exit_code == 0

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.Path.exists")
    @patch("dopemux.cli.ClaudeConfigurator")
    @patch("dopemux.cli.ContextManager")
    def test_init_command_success(
        self, mock_context, mock_configurator, mock_exists, mock_config
    ):
        """Test successful project initialization."""
        mock_exists.return_value = True

        runner = CliRunner()
        with patch("dopemux.cli.Path.resolve", return_value=Path("/test/project")):
            result = runner.invoke(cli, ["init", "."])

        assert result.exit_code == 0
        assert "Project Initialized" in result.output

    def test_init_command_nonexistent_directory(self):
        """Test init command with non-existent directory."""
        runner = CliRunner()

        with patch("dopemux.cli.Path.exists", return_value=False):
            result = runner.invoke(cli, ["init", "/nonexistent"])

        assert result.exit_code == 1
        assert "does not exist" in result.output

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.Path.exists")
    def test_init_command_already_initialized(self, mock_exists, mock_config):
        """Test init command when project is already initialized."""

        # Mock that .dopemux directory exists
        def side_effect(self):
            if ".dopemux" in str(self):
                return True
            return False

        mock_exists.side_effect = side_effect

        runner = CliRunner()
        with patch("dopemux.cli.Path.resolve", return_value=Path("/test/project")):
            result = runner.invoke(cli, ["init", "."])

        assert result.exit_code == 1
        assert "already initialized" in result.output

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.Path.exists")
    @patch("dopemux.cli.ClaudeConfigurator")
    @patch("dopemux.cli.ContextManager")
    def test_init_command_force_overwrite(
        self, mock_context, mock_configurator, mock_exists, mock_config
    ):
        """Test init command with force flag."""

        # Mock that project is already initialized
        def side_effect(self):
            if ".dopemux" in str(self):
                return True
            if "project" in str(self):
                return True
            return False

        mock_exists.side_effect = side_effect

        runner = CliRunner()
        with patch("dopemux.cli.Path.resolve", return_value=Path("/test/project")):
            result = runner.invoke(cli, ["init", "--force", "."])

        assert result.exit_code == 0
        assert "Project Initialized" in result.output

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.Path.cwd")
    @patch("dopemux.cli.ContextManager")
    @patch("dopemux.cli.ClaudeLauncher")
    @patch("dopemux.cli.AttentionMonitor")
    def test_start_command_success(
        self, mock_attention, mock_launcher, mock_context, mock_cwd, mock_config
    ):
        """Test successful start command."""
        mock_cwd.return_value = Path("/test/project")

        # Mock that project is initialized
        mock_project_path = Mock()
        mock_project_path.__truediv__ = Mock(return_value=Mock())
        mock_project_path.__truediv__.return_value.exists.return_value = True

        mock_context_manager = Mock()
        mock_context_manager.restore_latest.return_value = {"current_goal": "Test goal"}
        mock_context.return_value = mock_context_manager

        mock_claude_launcher = Mock()
        mock_claude_launcher.launch.return_value = Mock()
        mock_launcher.return_value = mock_claude_launcher

        runner = CliRunner()
        with patch("dopemux.cli.Path", return_value=mock_project_path):
            result = runner.invoke(cli, ["start"])

        assert result.exit_code == 0

    @patch("dopemux.cli.ConfigManager")
    def test_start_command_not_initialized(self, mock_config):
        """Test start command when project is not initialized."""
        runner = CliRunner()

        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=False):
                # Don't confirm initialization
                result = runner.invoke(cli, ["start"], input="n\n")

        assert result.exit_code == 1

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.ContextManager")
    def test_save_command_success(self, mock_context, mock_config):
        """Test successful save command."""
        mock_context_manager = Mock()
        mock_context_manager.save_context.return_value = "session-123"
        mock_context.return_value = mock_context_manager

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(cli, ["save", "--message", "Test save"])

        assert result.exit_code == 0
        assert "Context saved" in result.output

    @patch("dopemux.cli.ConfigManager")
    def test_save_command_not_initialized(self, mock_config):
        """Test save command when project is not initialized."""
        runner = CliRunner()

        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=False):
                result = runner.invoke(cli, ["save"])

        assert result.exit_code == 1
        assert "No Dopemux project found" in result.output

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.ContextManager")
    def test_restore_command_success(self, mock_context, mock_config):
        """Test successful restore command."""
        mock_context_manager = Mock()
        mock_context_manager.restore_session.return_value = {
            "timestamp": "2024-01-01T12:00:00",
            "current_goal": "Test goal",
            "open_files": ["file1.py", "file2.py"],
        }
        mock_context.return_value = mock_context_manager

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(cli, ["restore", "--session", "session-123"])

        assert result.exit_code == 0
        assert "Restored session" in result.output

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.ContextManager")
    def test_restore_command_list_sessions(self, mock_context, mock_config):
        """Test restore command with list flag."""
        mock_context_manager = Mock()
        mock_context_manager.list_sessions.return_value = [
            {
                "id": "session-1",
                "timestamp": "2024-01-01T12:00:00",
                "current_goal": "Goal 1",
                "open_files": ["file1.py"],
            },
            {
                "id": "session-2",
                "timestamp": "2024-01-01T13:00:00",
                "current_goal": "Goal 2",
                "open_files": ["file2.py"],
            },
        ]
        mock_context.return_value = mock_context_manager

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(cli, ["restore", "--list"])

        assert result.exit_code == 0
        assert "Available Sessions" in result.output
        assert "session-1" in result.output
        assert "session-2" in result.output

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.AttentionMonitor")
    @patch("dopemux.cli.ContextManager")
    @patch("dopemux.cli.TaskDecomposer")
    def test_status_command_all_metrics(
        self, mock_decomposer, mock_context, mock_attention, mock_config
    ):
        """Test status command showing all metrics."""
        # Mock attention monitor
        mock_attention_monitor = Mock()
        mock_attention_monitor.get_current_metrics.return_value = {
            "attention_state": "focused",
            "session_duration": 30.5,
            "focus_score": 0.8,
            "context_switches": 2,
        }
        mock_attention.return_value = mock_attention_monitor

        # Mock context manager
        mock_context_manager = Mock()
        mock_context_manager.get_current_context.return_value = {
            "current_goal": "Test goal",
            "open_files": ["file1.py"],
            "last_save": "10 minutes ago",
            "git_branch": "main",
        }
        mock_context.return_value = mock_context_manager

        # Mock task decomposer
        mock_task_decomposer = Mock()
        mock_task_decomposer.get_progress.return_value = {
            "tasks": [
                {
                    "name": "Task 1",
                    "completed": True,
                    "in_progress": False,
                    "progress": 1.0,
                },
                {
                    "name": "Task 2",
                    "completed": False,
                    "in_progress": True,
                    "progress": 0.5,
                },
            ]
        }
        mock_decomposer.return_value = mock_task_decomposer

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "Attention Metrics" in result.output
        assert "Context Information" in result.output
        assert "Task Progress" in result.output

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.TaskDecomposer")
    def test_task_command_add_task(self, mock_decomposer, mock_config):
        """Test adding a task via task command."""
        mock_task_decomposer = Mock()
        mock_task_decomposer.add_task.return_value = "task-123"
        mock_decomposer.return_value = mock_task_decomposer

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(
                    cli,
                    [
                        "task",
                        "Implement new feature",
                        "--duration",
                        "30",
                        "--priority",
                        "high",
                    ],
                )

        assert result.exit_code == 0
        assert "Task added" in result.output
        mock_task_decomposer.add_task.assert_called_once_with(
            description="Implement new feature", duration=30, priority="high"
        )

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.TaskDecomposer")
    def test_task_command_list_tasks(self, mock_decomposer, mock_config):
        """Test listing tasks via task command."""
        mock_task_decomposer = Mock()
        mock_task_decomposer.list_tasks.return_value = [
            {
                "description": "Task 1",
                "priority": "high",
                "estimated_duration": 25,
                "status": "completed",
            },
            {
                "description": "Task 2",
                "priority": "medium",
                "estimated_duration": 15,
                "status": "in_progress",
            },
        ]
        mock_decomposer.return_value = mock_task_decomposer

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(cli, ["task", "--list"])

        assert result.exit_code == 0
        assert "Current Tasks" in result.output
        assert "Task 1" in result.output
        assert "Task 2" in result.output

    def test_task_command_missing_description(self):
        """Test task command with missing description."""
        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(cli, ["task"])

        assert result.exit_code == 1
        assert "Description required" in result.output

    def test_attention_emoji_mapping(self):
        """Test _get_attention_emoji function."""
        from dopemux.cli import _get_attention_emoji

        assert _get_attention_emoji("focused") == "🎯"
        assert _get_attention_emoji("scattered") == "🌪️"
        assert _get_attention_emoji("hyperfocus") == "🔥"
        assert _get_attention_emoji("normal") == "😊"
        assert _get_attention_emoji("distracted") == "😵‍💫"
        assert _get_attention_emoji("unknown") == "❓"
        assert _get_attention_emoji(None) == "❓"

    @patch("dopemux.cli.console")
    def test_main_function_keyboard_interrupt(self, mock_console):
        """Test main function handling keyboard interrupt."""
        from dopemux.cli import main

        with patch("dopemux.cli.cli", side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_console.print.assert_called_with(
                "\n[yellow]⏸️ Interrupted by user[/yellow]"
            )

    @patch("dopemux.cli.console")
    def test_main_function_general_exception(self, mock_console):
        """Test main function handling general exception."""
        from dopemux.cli import main

        with patch("dopemux.cli.cli", side_effect=Exception("Test error")):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]❌ Error: Test error[/red]")

    @patch("dopemux.cli.console")
    def test_main_function_debug_mode(self, mock_console):
        """Test main function in debug mode."""
        from dopemux.cli import main

        with patch("sys.argv", ["dopemux", "--debug"]):
            with patch("dopemux.cli.cli", side_effect=Exception("Test error")):
                with pytest.raises(Exception):  # Should re-raise in debug mode
                    main()

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.ContextManager")
    def test_start_command_with_context_restore(self, mock_context, mock_config):
        """Test start command that restores context."""
        mock_context_manager = Mock()
        mock_context_manager.restore_session.return_value = {
            "timestamp": "2024-01-01T12:00:00",
            "current_goal": "Continue feature development",
        }
        mock_context.return_value = mock_context_manager

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                with patch("dopemux.cli.ClaudeLauncher") as mock_launcher:
                    with patch("dopemux.cli.AttentionMonitor"):
                        result = runner.invoke(
                            cli, ["start", "--session", "session-123"]
                        )

        assert result.exit_code == 0
        mock_context_manager.restore_session.assert_called_with("session-123")

    @patch("dopemux.cli.ConfigManager")
    @patch("dopemux.cli.ContextManager")
    def test_save_command_force_flag(self, mock_context, mock_config):
        """Test save command with force flag."""
        mock_context_manager = Mock()
        mock_context_manager.save_context.return_value = "session-456"
        mock_context.return_value = mock_context_manager

        runner = CliRunner()
        with patch("dopemux.cli.Path.cwd", return_value=Path("/test")):
            with patch("dopemux.cli.Path.exists", return_value=True):
                result = runner.invoke(cli, ["save", "--force"])

        assert result.exit_code == 0
        mock_context_manager.save_context.assert_called_with(message=None, force=True)

    def test_init_command_custom_template(self):
        """Test init command with custom template."""
        runner = CliRunner()

        with patch("dopemux.cli.ConfigManager"):
            with patch("dopemux.cli.Path.exists", return_value=True):
                with patch("dopemux.cli.Path.resolve", return_value=Path("/test")):
                    with patch("dopemux.cli.ClaudeConfigurator") as mock_configurator:
                        with patch("dopemux.cli.ContextManager"):
                            result = runner.invoke(
                                cli, ["init", "--template", "rust", "."]
                            )

        assert result.exit_code == 0
        # Verify template was passed to configurator
        mock_configurator.return_value.setup_project_config.assert_called_once()
        call_args = mock_configurator.return_value.setup_project_config.call_args
        assert call_args[0][1] == "rust"  # template argument
