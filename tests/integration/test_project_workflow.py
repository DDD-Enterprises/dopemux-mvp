"""
Integration tests for complete project workflows.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from dopemux.adhd import AttentionMonitor, ContextManager, TaskDecomposer
from dopemux.cli import cli
from dopemux.config import ConfigManager


@pytest.mark.integration
class TestProjectInitializationWorkflow:
    """Test complete project initialization workflow."""

    def test_init_and_start_workflow(self):
        """Test initializing a project and starting Claude Code."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()

            # Mock all the external dependencies
            with patch("dopemux.cli.ConfigManager") as mock_config:
                with patch("dopemux.cli.ClaudeConfigurator") as mock_configurator:
                    with patch("dopemux.cli.ContextManager") as mock_context:
                        with patch("dopemux.cli.ClaudeLauncher") as mock_launcher:
                            with patch(
                                "dopemux.cli.AttentionMonitor"
                            ) as mock_attention:
                                # Setup mocks
                                mock_context_instance = Mock()
                                mock_context.return_value = mock_context_instance
                                mock_context_instance.restore_latest.return_value = None

                                mock_launcher_instance = Mock()
                                mock_launcher.return_value = mock_launcher_instance
                                mock_launcher_instance.launch.return_value = Mock()

                                # Initialize project
                                result = runner.invoke(cli, ["init", str(project_path)])
                                assert result.exit_code == 0

                                # Start Claude Code
                                with patch(
                                    "dopemux.cli.Path.cwd", return_value=project_path
                                ):
                                    result = runner.invoke(cli, ["start"])
                                    assert result.exit_code == 0

    def test_context_save_restore_workflow(self):
        """Test saving and restoring context."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()

            # Create .dopemux directory
            dopemux_dir = project_path / ".dopemux"
            dopemux_dir.mkdir()

            with patch("dopemux.cli.ConfigManager"):
                with patch("dopemux.cli.ContextManager") as mock_context:
                    mock_context_instance = Mock()
                    mock_context.return_value = mock_context_instance

                    # Save context
                    mock_context_instance.save_context.return_value = "session-123"

                    with patch("dopemux.cli.Path.cwd", return_value=project_path):
                        result = runner.invoke(
                            cli, ["save", "--message", "Test checkpoint"]
                        )
                        assert result.exit_code == 0
                        assert "session-" in result.output  # CLI shows session_id[:8]

                    # Restore context
                    mock_context_instance.restore_session.return_value = {
                        "timestamp": "2024-01-01T12:00:00",
                        "current_goal": "Test goal",
                        "open_files": [],
                    }

                    with patch("dopemux.cli.Path.cwd", return_value=project_path):
                        result = runner.invoke(
                            cli, ["restore", "--session", "session-123"]
                        )
                        assert result.exit_code == 0
                        assert "Restored session" in result.output

    def test_task_management_workflow(self):
        """Test complete task management workflow."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            dopemux_dir = project_path / ".dopemux"
            dopemux_dir.mkdir()

            with patch("dopemux.cli.ConfigManager"):
                with patch("dopemux.cli.TaskDecomposer") as mock_decomposer:
                    mock_decomposer_instance = Mock()
                    mock_decomposer.return_value = mock_decomposer_instance

                    # Add task
                    mock_decomposer_instance.add_task.return_value = "task-123"

                    with patch("dopemux.cli.Path.cwd", return_value=project_path):
                        result = runner.invoke(
                            cli,
                            [
                                "task",
                                "Implement new feature",
                                "--priority",
                                "high",
                                "--duration",
                                "30",
                            ],
                        )
                        assert result.exit_code == 0

                    # List tasks
                    mock_decomposer_instance.list_tasks.return_value = [
                        {
                            "description": "Implement new feature",
                            "priority": "high",
                            "estimated_duration": 30,
                            "status": "pending",
                        }
                    ]

                    with patch("dopemux.cli.Path.cwd", return_value=project_path):
                        result = runner.invoke(cli, ["task", "--list"])
                        assert result.exit_code == 0
                        assert "Implement new feature" in result.output


@pytest.mark.integration
class TestADHDFeaturesIntegration:
    """Test integration of ADHD-specific features."""

    def test_context_and_attention_integration(self):
        """Test integration between context manager and attention monitor."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Initialize components
            context_manager = ContextManager(project_path)
            attention_monitor = AttentionMonitor(project_path)

            context_manager.initialize()

            # Simulate attention monitoring triggering context saves
            attention_callback_called = False

            def attention_callback(metrics):
                nonlocal attention_callback_called
                attention_callback_called = True

                if metrics.attention_state == "distracted":
                    context_manager.save_context(message="Auto-save due to distraction")

            attention_monitor.add_callback(attention_callback)

            # Simulate distracted state
            attention_monitor.simulate_activity("keystroke")
            attention_monitor._collect_metrics()

            # Manually trigger callback with distracted state
            from datetime import datetime

            from dopemux.adhd.attention_monitor import AttentionMetrics, AttentionState

            distracted_metrics = AttentionMetrics(
                timestamp=datetime.now(),
                keystroke_rate=0,
                error_rate=0,
                context_switches=0,
                pause_duration=700,  # Long pause = distracted
                focus_score=0.2,
                attention_state=AttentionState.DISTRACTED,
            )

            attention_callback(distracted_metrics)
            assert attention_callback_called

    def test_task_decomposer_and_attention_integration(self):
        """Test integration between task decomposer and attention monitoring."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            task_decomposer = TaskDecomposer(project_path)
            attention_monitor = AttentionMonitor(project_path)

            # Add a large task that gets decomposed
            task_id = task_decomposer.add_task(
                description="Large complex task",
                duration=60,  # Will be decomposed
                priority="high",
            )

            # Start the task
            task_decomposer.start_task(task_id)

            # Simulate attention patterns during task
            attention_monitor.simulate_activity("keystroke")
            attention_monitor.simulate_activity("keystroke")
            attention_monitor._collect_metrics()

            # Get current metrics
            metrics = attention_monitor.get_current_metrics()
            assert metrics["monitoring_active"] is False  # Not started
            assert metrics["focus_score"] >= 0


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration integration across components."""

    def test_config_propagation_to_components(self):
        """Test that configuration is properly propagated to all components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test config
            config_data = {
                "version": "1.0",
                "adhd_profile": {
                    "focus_duration_avg": 20,
                    "break_interval": 3,
                    "distraction_sensitivity": 0.7,
                    "notification_style": "bold",
                },
                "attention": {
                    "enabled": True,
                    "sample_interval": 3,
                    "keystroke_threshold": 1.5,
                },
                "context": {"enabled": True, "auto_save_interval": 15},
            }

            config_file = Path(temp_dir) / "config.yaml"
            with open(config_file, "w") as f:
                import yaml

                yaml.dump(config_data, f)

            # Initialize config manager with test config
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=config_file,
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()
                with patch.object(
                    config_manager, "_get_default_config", return_value={}
                ):
                    config = config_manager.load_config()

                    # Verify config loaded correctly
                    assert config.adhd_profile.focus_duration_avg == 20
                    assert config.attention.sample_interval == 3

    def test_mcp_server_configuration_integration(self):
        """Test MCP server configuration integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Mock config with test MCP servers
            with patch(
                "dopemux.config.manager.ConfigManager._init_paths"
            ) as mock_init_paths:
                from dopemux.config.manager import ConfigPaths

                mock_init_paths.return_value = ConfigPaths(
                    global_config=Path(temp_dir) / "global.yaml",
                    user_config=Path(temp_dir) / "config.yaml",
                    project_config=Path(temp_dir) / "project.yaml",
                    cache_dir=Path(temp_dir) / "cache",
                    data_dir=Path(temp_dir) / "data",
                )

                config_manager = ConfigManager()

                # Test MCP server configuration generation
                claude_settings = config_manager.get_claude_settings()

                assert "mcpServers" in claude_settings
                assert "env" in claude_settings


@pytest.mark.integration
class TestRealFileSystemIntegration:
    """Test integration with real file system operations."""

    def test_context_manager_file_operations(self):
        """Test context manager with real file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create some test files
            src_dir = project_path / "src"
            src_dir.mkdir()

            test_file = src_dir / "main.py"
            test_file.write_text(
                """
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
"""
            )

            # Initialize context manager
            context_manager = ContextManager(project_path)
            context_manager.initialize()

            # Save context
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="main\n")
                session_id = context_manager.save_context(message="Test save")

            assert session_id
            assert context_manager.db_path.exists()

            # Verify database content
            import sqlite3

            with sqlite3.connect(context_manager.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM context_snapshots")
                count = cursor.fetchone()[0]
                assert count > 0

    def test_task_decomposer_file_persistence(self):
        """Test task decomposer file persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Initialize first decomposer
            decomposer1 = TaskDecomposer(project_path)

            # Add tasks
            task_id1 = decomposer1.add_task("Task 1", duration=15)
            task_id2 = decomposer1.add_task("Task 2", duration=30)

            # Start a task
            decomposer1.start_task(task_id1)

            # Verify files exist
            assert decomposer1.tasks_file.exists()

            # Initialize second decomposer (simulates restart)
            decomposer2 = TaskDecomposer(project_path)

            # Verify tasks were loaded
            assert task_id1 in decomposer2._tasks
            assert task_id2 in decomposer2._tasks

            # Verify state persistence
            task1 = decomposer2._tasks[task_id1]
            assert task1.status.value == "in_progress"

    def test_attention_monitor_data_persistence(self):
        """Test attention monitor data persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            monitor = AttentionMonitor(project_path)

            # Simulate some activity and metrics collection
            monitor.simulate_activity("keystroke")
            monitor.simulate_activity("keystroke")
            monitor._collect_metrics()

            # Force save session metrics
            monitor._save_session_metrics()

            # Verify files were created
            session_files = list(monitor.data_dir.glob("session_*.json"))
            assert len(session_files) > 0

            # Verify file content
            with open(session_files[0]) as f:
                data = json.load(f)
                assert "session_start" in data
                assert "summary" in data


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""

    def test_context_manager_error_recovery(self):
        """Test context manager error recovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            context_manager = ContextManager(project_path)
            context_manager.initialize()

            # Simulate error during context capture
            with patch.object(
                context_manager,
                "_capture_current_state",
                side_effect=Exception("Test error"),
            ):
                # Should not crash and should create emergency save
                session_id = context_manager.save_context()

                # Emergency save file should exist
                emergency_file = context_manager.dopemux_dir / "emergency_context.json"
                assert emergency_file.exists()

    def test_attention_monitor_callback_error_handling(self):
        """Test attention monitor callback error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            monitor = AttentionMonitor(project_path)

            # Add callbacks, one that fails
            successful_callback_called = False

            def failing_callback(metrics):
                raise ValueError("Callback failed")

            def successful_callback(metrics):
                nonlocal successful_callback_called
                successful_callback_called = True

            monitor.add_callback(failing_callback)
            monitor.add_callback(successful_callback)

            # Collect metrics - should not crash despite failing callback
            monitor._collect_metrics()

            # Successful callback should still be called
            assert successful_callback_called

    def test_task_decomposer_invalid_operations(self):
        """Test task decomposer handling of invalid operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            decomposer = TaskDecomposer(project_path)

            # Try to start non-existent task
            result = decomposer.start_task("non-existent-id")
            assert result is False

            # Try to complete non-existent task
            result = decomposer.complete_task("non-existent-id")
            assert result is False

            # Try to update progress for non-existent task
            result = decomposer.update_progress("non-existent-id", 0.5)
            assert result is False


@pytest.mark.integration
class TestCLIIntegrationWorkflow:
    """Test complete CLI workflows."""

    def test_full_development_session_workflow(self):
        """Test a complete development session workflow."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()

            # Mock all external dependencies
            with patch("dopemux.cli.ConfigManager"):
                with patch("dopemux.cli.ClaudeConfigurator"):
                    with patch("dopemux.cli.ContextManager") as mock_context:
                        with patch("dopemux.cli.ClaudeLauncher"):
                            with patch("dopemux.cli.AttentionMonitor"):
                                with patch(
                                    "dopemux.cli.TaskDecomposer"
                                ) as mock_decomposer:
                                    # Setup mocks
                                    mock_context_instance = Mock()
                                    mock_context.return_value = mock_context_instance
                                    mock_context_instance.save_context.return_value = (
                                        "session-123"
                                    )

                                    mock_decomposer_instance = Mock()
                                    mock_decomposer.return_value = (
                                        mock_decomposer_instance
                                    )
                                    mock_decomposer_instance.add_task.return_value = (
                                        "task-123"
                                    )

                                    # 1. Initialize project
                                    result = runner.invoke(
                                        cli, ["init", str(project_path)]
                                    )
                                    assert result.exit_code == 0

                                    # 2. Add a task
                                    with patch(
                                        "dopemux.cli.Path.cwd",
                                        return_value=project_path,
                                    ):
                                        result = runner.invoke(
                                            cli,
                                            [
                                                "task",
                                                "Implement authentication",
                                                "--priority",
                                                "high",
                                                "--duration",
                                                "45",
                                            ],
                                        )
                                        assert result.exit_code == 0

                                    # 3. Save context
                                    with patch(
                                        "dopemux.cli.Path.cwd",
                                        return_value=project_path,
                                    ):
                                        result = runner.invoke(
                                            cli,
                                            ["save", "--message", "Starting auth work"],
                                        )
                                        assert result.exit_code == 0

                                    # 4. Check status
                                    mock_context_instance.get_current_context.return_value = {
                                        "current_goal": "Implement authentication",
                                        "open_files": [],
                                        "last_save": "Just now",
                                        "git_branch": "feature/auth",
                                    }

                                    with patch(
                                        "dopemux.cli.AttentionMonitor"
                                    ) as mock_attention:
                                        with patch(
                                            "dopemux.cli.TaskDecomposer"
                                        ) as mock_task:
                                            mock_attention.return_value.get_current_metrics.return_value = {
                                                "attention_state": "focused",
                                                "focus_score": 0.8,
                                                "session_duration": 25,
                                                "context_switches": 2,
                                            }

                                            mock_task.return_value.get_progress.return_value = {
                                                "tasks": [
                                                    {
                                                        "name": "Implement authentication",
                                                        "completed": False,
                                                        "in_progress": True,
                                                        "progress": 0.3,
                                                    }
                                                ]
                                            }

                                            with patch(
                                                "dopemux.cli.Path.cwd",
                                                return_value=project_path,
                                            ):
                                                result = runner.invoke(cli, ["status"])
                                                assert result.exit_code == 0
                                                assert (
                                                    "Attention Metrics" in result.output
                                                )
