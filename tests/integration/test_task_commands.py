import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import MagicMock, patch

from dopemux.cli import cli


@pytest.mark.integration
class TestTaskIntegration:
    """Integration tests for task commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_task_decomposer(self):
        with patch("dopemux.cli.TaskDecomposer") as mock:
            instance = mock.return_value
            # Setup default behaviors
            instance.list_tasks.return_value = []
            instance.add_task.return_value = "task-uuid-123"
            instance.get_progress.return_value = {"tasks": [], "summary": {}}
            yield instance

    def test_task_lifecycle(self, runner, mock_task_decomposer, tmp_path):
        """Test full task lifecycle via CLI."""

        # Setup valid environment
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".dopemux").mkdir()

        with patch("dopemux.cli.Path.cwd", return_value=project_root):
            # 1. List tasks (empty)
            result = runner.invoke(cli, ["task", "--list"])
            assert result.exit_code == 0
            # Command is deprecated, so check for empty state message
            assert "No tasks found" in result.output
            mock_task_decomposer.list_tasks.assert_called()

            # 2. Add a task
            result = runner.invoke(cli, ["task", "Implement features", "--priority", "high", "--duration", "45"])
            assert result.exit_code == 0
            assert "Task added" in result.output
            assert "Implement features" in result.output

            mock_task_decomposer.add_task.assert_called_with(
                description="Implement features",
                duration=45,
                priority="high",
            )

    def test_task_list_populated(self, runner, mock_task_decomposer, tmp_path):
        """Test listing tasks when populated."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".dopemux").mkdir()

        mock_task_decomposer.list_tasks.return_value = [
            {
                "description": "Existing Task",
                "priority": "medium",
                "estimated_duration": 30,
                "status": "pending",
            }
        ]

        with patch("dopemux.cli.Path.cwd", return_value=project_root):
            result = runner.invoke(cli, ["task", "--list"])
            assert result.exit_code == 0
            assert "Current Tasks" in result.output
            assert "Existing Task" in result.output

    def test_status_integration(self, runner, mock_task_decomposer):
        """Test status command integration with tasks."""
        # Setup mock data
        mock_task_decomposer.get_progress.return_value = {
            "tasks": [
                {
                    "name": "Integration Test Task",
                    "completed": False,
                    "in_progress": True,
                    "progress": 0.5,
                }
            ],
            "summary": {"total": 1, "completed": 0, "in_progress": 1},
        }

        # Mock other dependencies required for status
        with patch("dopemux.cli.AttentionMonitor") as mock_attn, \
             patch("dopemux.cli.ContextManager") as mock_ctx, \
             patch("dopemux.cli.Path.exists", return_value=True):

            mock_attn.return_value.get_current_metrics.return_value = {}
            mock_ctx.return_value.get_current_context.return_value = {}

            result = runner.invoke(cli, ["status", "--tasks"])

            assert result.exit_code == 0
            assert "Task Progress" in result.output
            assert "Integration Test Task" in result.output
            assert "50%" in result.output  # 0.5 progress

    def test_task_persistence_check(self, runner, tmp_path):
        """Verify task commands interact with filesystem (using real TaskDecomposer with tmp path)."""
        # We want to test the actual TaskDecomposer interaction with files,
        # but we need to inject the tmp_path into the CLI's resolution logic

        # Create a fake project root
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".dopemux").mkdir()

        with patch("dopemux.cli.Path.cwd", return_value=project_root):
            # 1. Add task
            result = runner.invoke(cli, ["task", "Real persistence task"])
            assert result.exit_code == 0

            # 2. List tasks to verify persistence
            result = runner.invoke(cli, ["task", "--list"])
            assert result.exit_code == 0
            assert "Real persistence task" in result.output

            # Verify file creation
            tasks_file = project_root / ".dopemux" / "tasks" / "tasks.json"
            assert tasks_file.exists()
            content = tasks_file.read_text()
            assert "Real persistence task" in content
