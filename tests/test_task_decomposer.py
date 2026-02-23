"""
Tests for the TaskDecomposer module.
"""

from pathlib import Path
from dopemux.adhd.task_decomposer import TaskDecomposer, TaskStatus


class TestTaskDecomposer:
    """Test TaskDecomposer class."""

    def test_add_task_basic(self, task_decomposer):
        """Test adding a task with basic description."""
        task_id = task_decomposer.add_task("Test basic task")

        assert task_id.startswith("task-")
        tasks = task_decomposer.list_tasks()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert tasks[0]["description"] == "Test basic task"
        assert tasks[0]["estimated_duration"] == 25
        assert tasks[0]["priority"] == "medium"
        assert tasks[0]["status"] == TaskStatus.PENDING.value

    def test_add_task_full(self, task_decomposer):
        """Test adding a task with all parameters."""
        task_id = task_decomposer.add_task(
            description="Test full task",
            duration=45,
            priority="high"
        )

        tasks = task_decomposer.list_tasks()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert tasks[0]["description"] == "Test full task"
        assert tasks[0]["estimated_duration"] == 45
        assert tasks[0]["priority"] == "high"

    def test_add_task_duration_normalization(self, task_decomposer):
        """Test that duration is normalized to at least 1."""
        # Test zero duration
        id1 = task_decomposer.add_task("Zero duration", duration=0)
        # Test negative duration
        id2 = task_decomposer.add_task("Negative duration", duration=-10)

        tasks = {t["id"]: t for t in task_decomposer.list_tasks()}
        assert tasks[id1]["estimated_duration"] == 1
        assert tasks[id2]["estimated_duration"] == 1

    def test_add_task_persistence(self, temp_project_dir):
        """Test that added tasks are persisted to disk."""
        # Create first instance and add a task
        decomposer1 = TaskDecomposer(temp_project_dir)
        task_id = decomposer1.add_task("Persistent task")

        # Verify file exists
        tasks_file = temp_project_dir / ".dopemux" / "tasks" / "tasks.json"
        assert tasks_file.exists()

        # Create second instance pointing to same workspace
        decomposer2 = TaskDecomposer(temp_project_dir)
        tasks = decomposer2.list_tasks()

        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert tasks[0]["description"] == "Persistent task"

    def test_add_task_extra_args(self, task_decomposer):
        """Test adding a task with extra arguments (legacy compatibility)."""
        # Should not raise any error
        task_id = task_decomposer.add_task(
            "Extra args task",
            unknown_arg="value",
            another_arg=123
        )

        assert task_id.startswith("task-")
        tasks = task_decomposer.list_tasks()
        assert any(t["id"] == task_id for t in tasks)
