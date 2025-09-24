"""
Tests for the task decomposer module.
"""

import json
from datetime import datetime, timedelta

from dopemux.adhd.task_decomposer import Task, TaskDecomposer, TaskPriority, TaskStatus


class TestTaskPriority:
    """Test TaskPriority enum."""

    def test_priority_values(self):
        """Test priority enum values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTask:
    """Test Task dataclass."""

    def test_default_creation(self):
        """Test creating task with minimal parameters."""
        task = Task(
            id="test-123",
            description="Test task",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            estimated_duration=25,
        )

        assert task.id == "test-123"
        assert task.description == "Test task"
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.PENDING
        assert task.estimated_duration == 25
        assert task.actual_duration == 0
        assert task.progress == 0.0
        assert task.subtasks == []
        assert task.dependencies == []
        assert task.blocked_by == []
        assert task.tags == []
        assert task.energy_required == "medium"
        assert task.context_switches_allowed == 2
        assert task.break_reminders is True

    def test_post_init_sets_defaults(self):
        """Test that __post_init__ sets up defaults."""
        task = Task(
            id="test-123",
            description="Test task",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            estimated_duration=30,
        )

        assert task.created_at  # Should be set
        assert isinstance(task.subtasks, list)
        assert isinstance(task.dependencies, list)
        assert isinstance(task.blocked_by, list)
        assert isinstance(task.tags, list)

    def test_property_is_completed(self):
        """Test is_completed property."""
        task = Task(
            id="test",
            description="Test",
            priority=TaskPriority.LOW,
            status=TaskStatus.COMPLETED,
            estimated_duration=10,
        )
        assert task.is_completed is True

        task.status = TaskStatus.PENDING
        assert task.is_completed is False

    def test_property_is_in_progress(self):
        """Test is_in_progress property."""
        task = Task(
            id="test",
            description="Test",
            priority=TaskPriority.LOW,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=10,
        )
        assert task.is_in_progress is True

        task.status = TaskStatus.PENDING
        assert task.is_in_progress is False

    def test_property_is_blocked(self):
        """Test is_blocked property."""
        task = Task(
            id="test",
            description="Test",
            priority=TaskPriority.LOW,
            status=TaskStatus.BLOCKED,
            estimated_duration=10,
        )
        assert task.is_blocked is True

        task.status = TaskStatus.PENDING
        task.blocked_by = ["blocker-id"]
        assert task.is_blocked is True

        task.blocked_by = []
        assert task.is_blocked is False

    def test_property_can_start(self):
        """Test can_start property."""
        task = Task(
            id="test",
            description="Test",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            estimated_duration=10,
        )
        assert task.can_start is True

        task.status = TaskStatus.COMPLETED
        assert task.can_start is False

        task.status = TaskStatus.PENDING
        task.blocked_by = ["blocker"]
        assert task.can_start is False

        task.blocked_by = []
        task.dependencies = ["dep"]
        assert task.can_start is False


class TestTaskDecomposer:
    """Test TaskDecomposer class."""

    def test_initialization(self, task_decomposer, temp_project_dir):
        """Test TaskDecomposer initialization."""
        assert task_decomposer.project_path == temp_project_dir
        assert task_decomposer.data_dir == temp_project_dir / ".dopemux" / "tasks"
        assert task_decomposer.data_dir.exists()

        # Check ADHD-specific settings
        assert task_decomposer.max_task_duration == 25
        assert task_decomposer.optimal_task_duration == 20
        assert task_decomposer.break_duration == 5

        # Check initial state
        assert isinstance(task_decomposer._tasks, dict)

    def test_add_simple_task(self, task_decomposer):
        """Test adding a simple task that doesn't need decomposition."""
        task_id = task_decomposer.add_task(
            description="Simple task",
            priority="high",
            duration=20,
            energy_required="low",
            tags=["test"],
        )

        assert task_id in task_decomposer._tasks
        task = task_decomposer._tasks[task_id]

        assert task.description == "Simple task"
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_duration == 20
        assert task.energy_required == "low"
        assert "test" in task.tags
        assert len(task.subtasks) == 0  # No decomposition needed

    def test_add_large_task_with_decomposition(self, task_decomposer):
        """Test adding a large task that gets decomposed."""
        task_id = task_decomposer.add_task(
            description="Large task",
            priority="medium",
            duration=60,  # > max_task_duration (25)
            energy_required="high",
        )

        assert task_id in task_decomposer._tasks
        main_task = task_decomposer._tasks[task_id]

        assert main_task.description == "Large task"
        assert len(main_task.subtasks) > 0  # Should be decomposed

        # Check subtasks exist
        for subtask_id in main_task.subtasks:
            assert subtask_id in task_decomposer._tasks
            subtask = task_decomposer._tasks[subtask_id]
            assert subtask.estimated_duration <= task_decomposer.optimal_task_duration

    def test_start_task_success(self, task_decomposer):
        """Test successfully starting a task."""
        task_id = task_decomposer.add_task("Test task", duration=15)

        result = task_decomposer.start_task(task_id)
        assert result is True

        task = task_decomposer._tasks[task_id]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None

    def test_start_task_not_found(self, task_decomposer):
        """Test starting a non-existent task."""
        result = task_decomposer.start_task("nonexistent-id")
        assert result is False

    def test_start_task_cannot_start(self, task_decomposer):
        """Test starting a task that cannot be started."""
        # Create blocked task
        task_id = task_decomposer.add_task("Blocked task", duration=15)
        task = task_decomposer._tasks[task_id]
        task.blocked_by = ["some-blocker"]

        result = task_decomposer.start_task(task_id)
        assert result is False

    def test_start_task_another_in_progress(self, task_decomposer):
        """Test starting a task when another is already in progress."""
        # Start first task
        task_id1 = task_decomposer.add_task("Task 1", duration=15)
        task_decomposer.start_task(task_id1)

        # Try to start second task
        task_id2 = task_decomposer.add_task("Task 2", duration=15)
        result = task_decomposer.start_task(task_id2)

        assert result is False

    def test_complete_task_success(self, task_decomposer):
        """Test successfully completing a task."""
        task_id = task_decomposer.add_task("Test task", duration=15)
        task_decomposer.start_task(task_id)

        # Mock started time to calculate duration
        task = task_decomposer._tasks[task_id]
        start_time = datetime.now() - timedelta(minutes=10)
        task.started_at = start_time.isoformat()

        result = task_decomposer.complete_task(task_id, "Task completed successfully")
        assert result is True

        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.progress == 1.0
        assert task.actual_duration > 0
        assert "Task completed successfully" in task.notes

    def test_complete_task_not_found(self, task_decomposer):
        """Test completing a non-existent task."""
        result = task_decomposer.complete_task("nonexistent-id")
        assert result is False

    def test_complete_task_with_subtasks(self, task_decomposer):
        """Test completing a task with subtasks."""
        # Create large task that gets decomposed
        task_id = task_decomposer.add_task("Large task", duration=60)
        main_task = task_decomposer._tasks[task_id]

        # Start and complete the main task
        task_decomposer.start_task(task_id)
        result = task_decomposer.complete_task(task_id)

        assert result is True
        assert main_task.status == TaskStatus.COMPLETED

        # All subtasks should also be completed
        for subtask_id in main_task.subtasks:
            subtask = task_decomposer._tasks[subtask_id]
            assert subtask.status == TaskStatus.COMPLETED
            assert subtask.progress == 1.0

    def test_list_tasks_all(self, task_decomposer):
        """Test listing all tasks."""
        # Add various tasks
        task_decomposer.add_task("Task 1", priority="high", duration=15)
        task_decomposer.add_task("Task 2", priority="low", duration=10)
        task_decomposer.add_task("Task 3", priority="urgent", duration=20)

        tasks = task_decomposer.list_tasks()

        assert len(tasks) == 3

        # Should be sorted by priority (urgent first, then high, etc.)
        priorities = [t["priority"] for t in tasks]
        assert priorities[0] == "urgent"  # Task 3
        assert priorities[1] == "high"  # Task 1
        assert priorities[2] == "low"  # Task 2

    def test_list_tasks_filtered_by_status(self, task_decomposer):
        """Test listing tasks filtered by status."""
        # Add and start some tasks
        task_id1 = task_decomposer.add_task("Task 1", duration=15)
        task_id2 = task_decomposer.add_task("Task 2", duration=15)

        task_decomposer.start_task(task_id1)
        task_decomposer.complete_task(task_id1)

        # Filter by completed status
        completed_tasks = task_decomposer.list_tasks(status="completed")
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["description"] == "Task 1"

        # Filter by pending status
        pending_tasks = task_decomposer.list_tasks(status="pending")
        assert len(pending_tasks) == 1
        assert pending_tasks[0]["description"] == "Task 2"

    def test_get_progress_no_tasks(self, task_decomposer):
        """Test getting progress when no tasks exist."""
        progress = task_decomposer.get_progress()
        assert progress == {}

    def test_get_progress_with_tasks(self, task_decomposer):
        """Test getting progress with tasks."""
        # Add and partially complete tasks
        task_id1 = task_decomposer.add_task("Task 1", duration=15)
        task_id2 = task_decomposer.add_task("Task 2", duration=15)

        task_decomposer.start_task(task_id1)
        task_decomposer.complete_task(task_id1)

        task_decomposer.start_task(task_id2)

        progress = task_decomposer.get_progress()

        assert progress["total_tasks"] == 2
        assert progress["completed_tasks"] == 1
        assert progress["in_progress_tasks"] == 1
        assert progress["overall_progress"] > 0
        assert progress["current_task"] is not None
        assert progress["current_task"]["description"] == "Task 2"

    def test_get_recommended_task(self, task_decomposer):
        """Test getting recommended task."""
        # Add tasks with different characteristics
        task_decomposer.add_task(
            "Low energy task", energy_required="low", priority="high", duration=15
        )
        task_decomposer.add_task(
            "High energy task", energy_required="high", priority="medium", duration=30
        )
        task_decomposer.add_task(
            "Medium energy task", energy_required="medium", priority="low", duration=20
        )

        # Get recommendation for low energy user
        recommended = task_decomposer.get_recommended_task(energy_level="low")

        assert recommended is not None
        assert (
            recommended["description"] == "Low energy task"
        )  # Should match energy level

    def test_get_recommended_task_no_available(self, task_decomposer):
        """Test getting recommended task when none available."""
        # Add a task but make it unavailable
        task_id = task_decomposer.add_task("Task", duration=15)
        task = task_decomposer._tasks[task_id]
        task.blocked_by = ["blocker"]

        recommended = task_decomposer.get_recommended_task()
        assert recommended is None

    def test_update_progress(self, task_decomposer):
        """Test updating task progress."""
        task_id = task_decomposer.add_task("Test task", duration=15)

        # Update progress
        result = task_decomposer.update_progress(task_id, 0.5)
        assert result is True

        task = task_decomposer._tasks[task_id]
        assert task.progress == 0.5

    def test_update_progress_auto_complete(self, task_decomposer):
        """Test that task auto-completes when progress reaches 100%."""
        task_id = task_decomposer.add_task("Test task", duration=15)

        # Update to 100% progress
        result = task_decomposer.update_progress(task_id, 1.0)
        assert result is True

        task = task_decomposer._tasks[task_id]
        assert task.progress == 1.0
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_update_progress_invalid_task(self, task_decomposer):
        """Test updating progress for non-existent task."""
        result = task_decomposer.update_progress("nonexistent", 0.5)
        assert result is False

    def test_decompose_task(self, task_decomposer):
        """Test task decomposition algorithm."""
        main_task = Task(
            id="main",
            description="Large task",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            estimated_duration=50,
            energy_required="medium",
        )

        subtasks = task_decomposer._decompose_task(main_task)

        assert len(subtasks) >= 2  # Should be broken down

        # Check total duration is preserved
        total_duration = sum(st.estimated_duration for st in subtasks)
        assert total_duration == 50

        # Check dependencies (each subtask depends on previous)
        for i, subtask in enumerate(subtasks):
            if i == 0:
                assert len(subtask.dependencies) == 0
            else:
                assert len(subtask.dependencies) == 1
                assert subtask.dependencies[0] == subtasks[i - 1].id

    def test_calculate_task_score(self, task_decomposer):
        """Test task scoring algorithm."""
        urgent_task = Task(
            id="urgent",
            description="Urgent",
            priority=TaskPriority.URGENT,
            status=TaskStatus.PENDING,
            estimated_duration=15,
            energy_required="low",
        )

        low_task = Task(
            id="low",
            description="Low",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            estimated_duration=15,
            energy_required="high",
        )

        urgent_score = task_decomposer._calculate_task_score(urgent_task, "low")
        low_score = task_decomposer._calculate_task_score(low_task, "low")

        # Urgent task should score higher
        assert urgent_score > low_score

        # Task with matching energy level should score higher
        low_energy_score = task_decomposer._calculate_task_score(urgent_task, "low")
        high_energy_score = task_decomposer._calculate_task_score(urgent_task, "high")
        assert (
            low_energy_score >= high_energy_score
        )  # low energy task for low energy user

    def test_check_unblocked_tasks(self, task_decomposer):
        """Test checking for newly unblocked tasks."""
        # Create dependency chain
        task_id1 = task_decomposer.add_task("Task 1", duration=15)
        task_id2 = task_decomposer.add_task("Task 2", duration=15)

        # Make task 2 depend on task 1
        task2 = task_decomposer._tasks[task_id2]
        task2.dependencies = [task_id1]

        # Complete task 1
        task_decomposer.start_task(task_id1)
        task_decomposer.complete_task(task_id1)

        # Task 2 should now be available
        task2_after = task_decomposer._tasks[task_id2]
        assert len(task2_after.dependencies) == 0  # Should be cleared

    def test_save_and_load_tasks(self, task_decomposer):
        """Test saving and loading tasks from storage."""
        # Add some tasks
        task_id1 = task_decomposer.add_task("Task 1", priority="high", duration=15)
        task_id2 = task_decomposer.add_task("Task 2", priority="low", duration=20)

        # Modify task state
        task_decomposer.start_task(task_id1)

        # Force save
        task_decomposer._save_tasks()

        # Create new decomposer (simulates restart)
        new_decomposer = TaskDecomposer(task_decomposer.project_path)

        # Should load existing tasks
        assert task_id1 in new_decomposer._tasks
        assert task_id2 in new_decomposer._tasks

        # Check state is preserved
        loaded_task = new_decomposer._tasks[task_id1]
        assert loaded_task.status == TaskStatus.IN_PROGRESS

    def test_task_session_logging(self, task_decomposer):
        """Test task session logging."""
        task_id = task_decomposer.add_task("Test task", duration=15)

        # Start and complete task
        task_decomposer.start_task(task_id)
        task_decomposer.complete_task(task_id, "Finished successfully")

        # Check session log exists
        assert task_decomposer.sessions_file.exists()

        # Verify log content
        with open(task_decomposer.sessions_file) as f:
            sessions = json.load(f)

        assert len(sessions) >= 2  # Start and complete events
        assert any(s["action"] == "started" for s in sessions)
        assert any(s["action"] == "completed" for s in sessions)

    def test_show_task_progress(self, task_decomposer, capsys):
        """Test visual progress display."""
        # Create task with subtasks
        task_id = task_decomposer.add_task("Large task", duration=60)
        task = task_decomposer._tasks[task_id]

        # Complete some subtasks
        for i, subtask_id in enumerate(task.subtasks[:2]):
            subtask = task_decomposer._tasks[subtask_id]
            subtask.status = TaskStatus.COMPLETED

        # Show progress
        task_decomposer._show_task_progress(task_id)

        # Check that progress was displayed
        captured = capsys.readouterr()
        assert "Progress:" in captured.out
        assert "█" in captured.out  # Progress bar characters

    def test_energy_level_matching(self, task_decomposer):
        """Test that energy levels are properly matched in recommendations."""
        # Add tasks with different energy requirements
        low_task_id = task_decomposer.add_task(
            "Low energy", energy_required="low", priority="medium"
        )
        high_task_id = task_decomposer.add_task(
            "High energy", energy_required="high", priority="medium"
        )

        # For low energy user, low energy task should be preferred
        low_rec = task_decomposer.get_recommended_task(energy_level="low")
        assert low_rec["description"] == "Low energy"

        # For high energy user, either should be acceptable
        high_rec = task_decomposer.get_recommended_task(energy_level="high")
        assert high_rec is not None  # Should get a recommendation

    def test_task_age_in_scoring(self, task_decomposer):
        """Test that older tasks get priority boost in scoring."""
        # Create task and mock it as older
        task = Task(
            id="old",
            description="Old task",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            estimated_duration=15,
            energy_required="medium",
        )

        # Mock creation time as 5 days ago
        old_time = datetime.now() - timedelta(days=5)
        task.created_at = old_time.isoformat()

        score = task_decomposer._calculate_task_score(task, "medium")

        # Create identical new task
        new_task = Task(
            id="new",
            description="New task",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            estimated_duration=15,
            energy_required="medium",
        )

        new_score = task_decomposer._calculate_task_score(new_task, "medium")

        # Old task should score higher due to age
        assert score > new_score
