"""
Tests for the TaskDecomposer class.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from dopemux.adhd.task_decomposer import TaskDecomposer, TaskStatus

class TestTaskDecomposer:
    """Test suite for TaskDecomposer."""

    def test_initialization_creates_directories(self, tmp_path):
        """Test that initialization creates the necessary directory structure."""
        decomposer = TaskDecomposer(tmp_path)

        expected_dir = tmp_path / ".dopemux" / "tasks"

        assert (tmp_path / ".dopemux").exists()
        assert expected_dir.exists()
        assert expected_dir.is_dir()

    def test_fallback_initialization(self, tmp_path):
        """Test fallback to temp directory if permission error occurs."""
        # We need to simulate the permission error correctly.
        # TaskDecomposer calls self.dopemux_dir.mkdir(parents=True, exist_ok=True)
        # We will mock Path.mkdir to fail only for the specific directory we are testing.

        original_mkdir = Path.mkdir

        def side_effect(self, *args, **kwargs):
            if str(tmp_path) in str(self):
                 raise PermissionError("Mocked permission error")
            return original_mkdir(self, *args, **kwargs)

        with patch("pathlib.Path.mkdir", side_effect=side_effect, autospec=True):
            decomposer = TaskDecomposer(tmp_path)

            # The workspace should have changed to a temp dir
            # The code uses tempfile.mkdtemp(prefix="dopemux-tasks-")
            assert "dopemux-tasks-" in str(decomposer.workspace)
            assert decomposer.workspace != tmp_path

    def test_add_task(self, tmp_path):
        """Test adding a task."""
        decomposer = TaskDecomposer(tmp_path)
        task_id = decomposer.add_task(
            description="Test Task",
            duration=30,
            priority="high"
        )

        assert task_id is not None
        assert task_id in decomposer._tasks

        task = decomposer._tasks[task_id]
        assert task.description == "Test Task"
        assert task.estimated_duration == 30
        assert task.priority == "high"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0

        # Verify persistence
        with open(decomposer.tasks_file, "r") as f:
            data = json.load(f)
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["id"] == task_id

    def test_list_tasks(self, tmp_path):
        """Test listing tasks."""
        decomposer = TaskDecomposer(tmp_path)
        decomposer.add_task("Task 1", priority="high")
        decomposer.add_task("Task 2", priority="low")

        tasks = decomposer.list_tasks()
        assert len(tasks) == 2

        descriptions = {t["description"] for t in tasks}
        assert "Task 1" in descriptions
        assert "Task 2" in descriptions

    def test_get_progress(self, tmp_path):
        """Test get_progress summary."""
        decomposer = TaskDecomposer(tmp_path)
        t1 = decomposer.add_task("Task 1")
        t2 = decomposer.add_task("Task 2")

        decomposer.complete_task(t1)
        decomposer.start_task(t2)

        progress = decomposer.get_progress()
        summary = progress["summary"]

        assert summary["total"] == 2
        assert summary["completed"] == 1
        assert summary["in_progress"] == 1

    def test_start_task(self, tmp_path):
        """Test starting a task."""
        decomposer = TaskDecomposer(tmp_path)
        task_id = decomposer.add_task("Task 1")

        assert decomposer.start_task(task_id) is True

        task = decomposer._tasks[task_id]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        assert task.progress == 0.01

    def test_complete_task(self, tmp_path):
        """Test completing a task."""
        decomposer = TaskDecomposer(tmp_path)
        task_id = decomposer.add_task("Task 1")

        assert decomposer.complete_task(task_id) is True

        task = decomposer._tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 1.0
        assert task.completed_at is not None
        # started_at should be set if it wasn't
        assert task.started_at is not None

    def test_update_progress(self, tmp_path):
        """Test updating progress."""
        decomposer = TaskDecomposer(tmp_path)
        task_id = decomposer.add_task("Task 1")

        # Update to 0.5
        decomposer.update_progress(task_id, 0.5)
        task = decomposer._tasks[task_id]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.progress == 0.5

        # Update to 1.0
        decomposer.update_progress(task_id, 1.0)
        task = decomposer._tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 1.0

    def test_persistence(self, tmp_path):
        """Test that tasks persist across instances."""
        decomposer1 = TaskDecomposer(tmp_path)
        task_id = decomposer1.add_task("Persistent Task")

        decomposer2 = TaskDecomposer(tmp_path)
        assert task_id in decomposer2._tasks
        assert decomposer2._tasks[task_id].description == "Persistent Task"

    def test_load_corrupted_file(self, tmp_path):
        """Test loading from a corrupted tasks.json."""
        decomposer = TaskDecomposer(tmp_path)

        # Write garbage
        # Ensure directory exists first (it should)
        assert decomposer.tasks_dir.exists()

        with open(decomposer.tasks_file, "w") as f:
            f.write("This is not JSON")

        decomposer2 = TaskDecomposer(tmp_path)
        assert len(decomposer2._tasks) == 0

    def test_missing_task_operations(self, tmp_path):
        """Test operations on non-existent tasks."""
        decomposer = TaskDecomposer(tmp_path)
        assert decomposer.start_task("fake-id") is False
        assert decomposer.complete_task("fake-id") is False
        assert decomposer.update_progress("fake-id", 0.5) is False
