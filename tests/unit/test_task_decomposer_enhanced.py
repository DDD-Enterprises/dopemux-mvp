import json
import tempfile
import uuid
from pathlib import Path
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


class TestTaskDecomposerEnhanced:
    """Enhanced unit tests for TaskDecomposer.add_task."""

    def test_add_task_defaults(self, decomposer):
        """Test that add_task uses correct default values."""
        task_id = decomposer.add_task("Default Task")
        task = decomposer._tasks[task_id]

        assert task.description == "Default Task"
        assert task.estimated_duration == 25
        assert task.priority == "medium"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0

    def test_add_task_custom_values(self, decomposer):
        """Test that add_task accepts and stores custom values."""
        task_id = decomposer.add_task(
            description="Custom Task",
            duration=60,
            priority="high"
        )
        task = decomposer._tasks[task_id]

        assert task.description == "Custom Task"
        assert task.estimated_duration == 60
        assert task.priority == "high"

    def test_add_task_validation(self, decomposer):
        """Test input validation and sanitization."""
        # Test duration < 1 is coerced to 1
        task_id1 = decomposer.add_task("Zero Duration", duration=0)
        assert decomposer._tasks[task_id1].estimated_duration == 1

        task_id2 = decomposer.add_task("Negative Duration", duration=-10)
        assert decomposer._tasks[task_id2].estimated_duration == 1

        # Test priority is converted to string
        task_id3 = decomposer.add_task("Int Priority", priority=1)
        assert decomposer._tasks[task_id3].priority == "1"

    def test_add_task_persistence_check(self, decomposer):
        """Verify that the task is actually written to disk."""
        task_id = decomposer.add_task("Persisted Task")

        # Check if file exists
        assert decomposer.tasks_file.exists()

        # Read file content
        with open(decomposer.tasks_file, "r") as f:
            data = json.load(f)

        tasks = data.get("tasks", [])
        assert len(tasks) == 1
        saved_task = tasks[0]

        assert saved_task["id"] == task_id
        assert saved_task["description"] == "Persisted Task"
        assert saved_task["estimated_duration"] == 25
        assert saved_task["priority"] == "medium"

    def test_add_task_id_format(self, decomposer):
        """Verify the format of the generated task ID."""
        task_id = decomposer.add_task("ID Test")

        assert isinstance(task_id, str)
        assert task_id.startswith("task-")
        # task-{8 hex chars}
        parts = task_id.split("-")
        assert len(parts) == 2
        assert len(parts[1]) == 8
        # Verify hex
        try:
            int(parts[1], 16)
        except ValueError:
            pytest.fail("Task ID suffix is not valid hex")

    def test_add_task_extra_args(self, decomposer):
        """Verify that extra arguments are accepted gracefully."""
        # Should not raise TypeError
        task_id = decomposer.add_task(
            "Extra Args Task",
            some_legacy_param="ignored",
            another_param=123
        )

        task = decomposer._tasks[task_id]
        # Verify core fields are still correct
        assert task.description == "Extra Args Task"
        # Extra args are not stored on the record (based on implementation)
        # But we verify it didn't crash
