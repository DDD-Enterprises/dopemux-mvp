import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dopemux.adhd.task_decomposer import TaskDecomposer, TaskStatus


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def decomposer(temp_workspace):
    """Create a TaskDecomposer instance with a temporary workspace."""
    return TaskDecomposer(temp_workspace)


class TestTaskDecomposer:
    """Unit tests for TaskDecomposer."""

    def test_init_creates_directories(self, temp_workspace):
        """Test that __init__ creates the necessary directories."""
        decomposer = TaskDecomposer(temp_workspace)
        assert (temp_workspace / ".dopemux").exists()
        assert (temp_workspace / ".dopemux" / "tasks").exists()
        assert decomposer.tasks_file == temp_workspace / ".dopemux" / "tasks" / "tasks.json"

    def test_init_permission_error_fallback(self, temp_workspace):
        """Test that __init__ falls back to a temp directory on permission error."""
        original_mkdir = Path.mkdir

        def mocked_mkdir(self, *args, **kwargs):
            if ".dopemux" in str(self) and "dopemux-tasks-" not in str(self):
                raise PermissionError("Mocked permission error")
            return original_mkdir(self, *args, **kwargs)

        with patch.object(Path, "mkdir", autospec=True, side_effect=mocked_mkdir):
            decomposer = TaskDecomposer(temp_workspace)
            # Should have fallback workspace in /tmp
            assert "dopemux-tasks-" in str(decomposer.workspace)
            assert decomposer.workspace != temp_workspace

    def test_add_task_persistence(self, decomposer):
        """Test that add_task creates a task and persists it."""
        task_id = decomposer.add_task("Test task", duration=30, priority="high")
        assert task_id in decomposer._tasks

        task = decomposer._tasks[task_id]
        assert task.description == "Test task"
        assert task.estimated_duration == 30
        assert task.priority == "high"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0

        # Verify file persistence
        assert decomposer.tasks_file.exists()
        with open(decomposer.tasks_file, "r") as f:
            data = json.load(f)
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["id"] == task_id

    def test_add_task_defaults(self, decomposer):
        """Test add_task with default values."""
        task_id = decomposer.add_task("Default task")
        task = decomposer._tasks[task_id]
        assert task.estimated_duration == 25
        assert task.priority == "medium"

    def test_start_task(self, decomposer):
        """Test starting a task."""
        task_id = decomposer.add_task("Start me")
        success = decomposer.start_task(task_id)

        assert success is True
        task = decomposer._tasks[task_id]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        assert task.progress == 0.01

    def test_complete_task(self, decomposer):
        """Test completing a task."""
        task_id = decomposer.add_task("Complete me")
        success = decomposer.complete_task(task_id)

        assert success is True
        task = decomposer._tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 1.0
        assert task.completed_at is not None
        assert task.started_at == task.completed_at # Started at completion if not started before

    def test_update_progress_basic(self, decomposer):
        """Test basic progress update."""
        task_id = decomposer.add_task("Progressive task")
        success = decomposer.update_progress(task_id, 0.5)

        assert success is True
        task = decomposer._tasks[task_id]
        assert task.progress == 0.5
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None

    def test_update_progress_auto_complete(self, decomposer):
        """Test auto-completion via progress update."""
        task_id = decomposer.add_task("Finish me")
        success = decomposer.update_progress(task_id, 1.0)

        assert success is True
        task = decomposer._tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 1.0
        assert task.completed_at is not None

    def test_update_progress_normalization(self, decomposer):
        """Test normalization of progress values."""
        task_id = decomposer.add_task("Normalize me")

        decomposer.update_progress(task_id, -0.5)
        assert decomposer._tasks[task_id].progress == 0.0

        decomposer.update_progress(task_id, 1.5)
        assert decomposer._tasks[task_id].progress == 1.0
        assert decomposer._tasks[task_id].status == TaskStatus.COMPLETED

    def test_update_progress_non_existent(self, decomposer):
        """Test update_progress for non-existent task."""
        success = decomposer.update_progress("invalid-id", 0.5)
        assert success is False

    def test_list_tasks(self, decomposer):
        """Test listing tasks."""
        decomposer.add_task("Task 1")
        decomposer.add_task("Task 2")

        tasks = decomposer.list_tasks()
        assert len(tasks) == 2
        assert any(t["description"] == "Task 1" for t in tasks)
        assert any(t["description"] == "Task 2" for t in tasks)

        # Check keys
        task = tasks[0]
        for key in ["id", "description", "priority", "estimated_duration", "status", "progress"]:
            assert key in task

    def test_get_progress(self, decomposer):
        """Test getting progress summary."""
        t1 = decomposer.add_task("Task 1")
        t2 = decomposer.add_task("Task 2")
        decomposer.complete_task(t1)
        decomposer.start_task(t2)

        progress = decomposer.get_progress()
        assert "tasks" in progress
        assert "summary" in progress

        summary = progress["summary"]
        assert summary["total"] == 2
        assert summary["completed"] == 1
        assert summary["in_progress"] == 1

    def test_persistence_loading(self, temp_workspace):
        """Test that tasks are correctly loaded from disk."""
        decomposer1 = TaskDecomposer(temp_workspace)
        task_id = decomposer1.add_task("Persisted task")
        decomposer1.start_task(task_id)

        # Create a new instance pointing to the same workspace
        decomposer2 = TaskDecomposer(temp_workspace)
        assert task_id in decomposer2._tasks
        assert decomposer2._tasks[task_id].description == "Persisted task"
        assert decomposer2._tasks[task_id].status == TaskStatus.IN_PROGRESS

    def test_iter(self, decomposer):
        """Test iteration over tasks."""
        decomposer.add_task("Task 1")
        decomposer.add_task("Task 2")

        task_list = list(decomposer)
        assert len(task_list) == 2
        assert all(hasattr(t, "id") for t in task_list)
