"""
Task Decomposer for ADHD-optimized development.

Breaks complex tasks into manageable 25-minute chunks with visual progress
tracking and dependency management.
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(Enum):
    """Task status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """ADHD-optimized task structure."""

    id: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    estimated_duration: int  # minutes
    actual_duration: int = 0
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    subtasks: List[str] = None  # List of subtask IDs
    dependencies: List[str] = None  # List of task IDs this depends on
    blocked_by: List[str] = None  # What's blocking this task
    tags: List[str] = None
    notes: str = ""
    energy_required: str = "medium"  # low, medium, high
    context_switches_allowed: int = 2  # ADHD consideration
    break_reminders: bool = True

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()
        if self.subtasks is None:
            self.subtasks = []
        if self.dependencies is None:
            self.dependencies = []
        if self.blocked_by is None:
            self.blocked_by = []
        if self.tags is None:
            self.tags = []

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def is_in_progress(self) -> bool:
        return self.status == TaskStatus.IN_PROGRESS

    @property
    def is_blocked(self) -> bool:
        return self.status == TaskStatus.BLOCKED or bool(self.blocked_by)

    @property
    def can_start(self) -> bool:
        return (
            self.status == TaskStatus.PENDING
            and not self.is_blocked
            and not self.dependencies
        )


class TaskDecomposer:
    """
    ADHD-optimized task management and decomposition.

    Features:
    - Automatic task chunking into 25-minute segments
    - Visual progress tracking
    - Dependency management
    - Energy level considerations
    - Break reminders
    - Context switch minimization
    """

    def __init__(self, project_path: Path):
        """Initialize task decomposer."""
        self.project_path = project_path
        self.data_dir = project_path / ".dopemux" / "tasks"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.data_dir / "tasks.json"
        self.sessions_file = self.data_dir / "task_sessions.json"

        self._tasks: Dict[str, Task] = {}
        self._load_tasks()

        # ADHD-specific settings
        self.max_task_duration = 25  # minutes
        self.optimal_task_duration = 20  # minutes
        self.break_duration = 5  # minutes
        self.energy_levels = ["low", "medium", "high"]

    def add_task(
        self,
        description: str,
        priority: str = "medium",
        duration: int = 25,
        energy_required: str = "medium",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Add a new task with automatic decomposition if needed.

        Args:
            description: Task description
            priority: Task priority (low, medium, high, urgent)
            duration: Estimated duration in minutes
            energy_required: Energy level required
            tags: Optional tags

        Returns:
            Task ID
        """
        # Create main task
        task_id = str(uuid.uuid4())[:8]

        task = Task(
            id=task_id,
            description=description,
            priority=TaskPriority(priority),
            status=TaskStatus.PENDING,
            estimated_duration=duration,
            energy_required=energy_required,
            tags=tags or [],
        )

        # Decompose if task is too large
        if duration > self.max_task_duration:
            subtasks = self._decompose_task(task)
            task.subtasks = [subtask.id for subtask in subtasks]

            # Store subtasks
            for subtask in subtasks:
                self._tasks[subtask.id] = subtask

        self._tasks[task_id] = task
        self._save_tasks()

        console.print(f"[green]✅ Task added: {description} ({duration}m)[/green]")
        if task.subtasks:
            console.print(
                f"[blue]🔍 Decomposed into {len(task.subtasks)} subtasks[/blue]"
            )

        return task_id

    def start_task(self, task_id: str) -> bool:
        """
        Start working on a task.

        Args:
            task_id: Task ID to start

        Returns:
            True if task was started successfully
        """
        if task_id not in self._tasks:
            console.print(f"[red]Task {task_id} not found[/red]")
            return False

        task = self._tasks[task_id]

        if not task.can_start:
            console.print(
                f"[yellow]Task {task_id} cannot be started (blocked or has dependencies)[/yellow]"
            )
            return False

        # Check if another task is in progress
        active_tasks = [t for t in self._tasks.values() if t.is_in_progress]
        if active_tasks:
            console.print(
                "[yellow]Another task is already in progress. Complete it first or use 'dopemux task switch'[/yellow]"
            )
            return False

        # Start the task
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().isoformat()
        self._save_tasks()

        # Log task session
        self._log_task_session(task_id, "started")

        console.print(f"[green]🚀 Started task: {task.description}[/green]")
        console.print(
            f"[blue]⏱️ Estimated duration: {task.estimated_duration} minutes[/blue]"
        )

        # Show progress if task has subtasks
        if task.subtasks:
            self._show_task_progress(task_id)

        return True

    def complete_task(self, task_id: str, notes: str = "") -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID to complete
            notes: Optional completion notes

        Returns:
            True if task was completed successfully
        """
        if task_id not in self._tasks:
            console.print(f"[red]Task {task_id} not found[/red]")
            return False

        task = self._tasks[task_id]

        # Calculate actual duration
        if task.started_at:
            start_time = datetime.fromisoformat(task.started_at)
            actual_duration = (datetime.now() - start_time).total_seconds() / 60
            task.actual_duration = int(actual_duration)

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        task.progress = 1.0
        if notes:
            task.notes += f"\nCompleted: {notes}"

        # Complete all subtasks if this is a parent task
        if task.subtasks:
            for subtask_id in task.subtasks:
                if subtask_id in self._tasks:
                    subtask = self._tasks[subtask_id]
                    if subtask.status != TaskStatus.COMPLETED:
                        subtask.status = TaskStatus.COMPLETED
                        subtask.progress = 1.0

        self._save_tasks()
        self._log_task_session(task_id, "completed", notes)

        console.print(f"[green]✅ Completed task: {task.description}[/green]")
        if task.actual_duration:
            estimated = task.estimated_duration
            actual = task.actual_duration
            accuracy = (
                "on time"
                if abs(actual - estimated) <= 5
                else "over" if actual > estimated else "under"
            )
            console.print(
                f"[blue]⏱️ Duration: {actual}m (estimated {estimated}m) - {accuracy}[/blue]"
            )

        # Check for newly available tasks
        self._check_unblocked_tasks()

        return True

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List tasks with optional status filter.

        Args:
            status: Optional status filter

        Returns:
            List of task dictionaries
        """
        tasks = []

        for task in self._tasks.values():
            if status and task.status.value != status:
                continue

            # Skip subtasks in main list (they'll be shown under parent)
            is_subtask = any(
                task.id in parent.subtasks for parent in self._tasks.values()
            )
            if is_subtask:
                continue

            task_dict = asdict(task)
            task_dict["priority"] = task.priority.value
            task_dict["status"] = task.status.value

            # Add subtask info
            if task.subtasks:
                subtask_data = []
                for subtask_id in task.subtasks:
                    if subtask_id in self._tasks:
                        subtask = self._tasks[subtask_id]
                        subtask_data.append(
                            {
                                "id": subtask.id,
                                "description": subtask.description,
                                "status": subtask.status.value,
                                "progress": subtask.progress,
                            }
                        )
                task_dict["subtask_data"] = subtask_data

            tasks.append(task_dict)

        # Sort by priority and creation time
        priority_order = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }

        tasks.sort(
            key=lambda t: (priority_order[TaskPriority(t["priority"])], t["created_at"])
        )
        return tasks

    def get_progress(self) -> Dict[str, Any]:
        """Get overall task progress information."""
        all_tasks = list(self._tasks.values())

        if not all_tasks:
            return {}

        total_tasks = len(
            [
                t
                for t in all_tasks
                if not any(t.id in parent.subtasks for parent in all_tasks)
            ]
        )
        completed_tasks = len(
            [
                t
                for t in all_tasks
                if t.is_completed
                and not any(t.id in parent.subtasks for parent in all_tasks)
            ]
        )
        in_progress_tasks = len([t for t in all_tasks if t.is_in_progress])

        # Calculate overall progress
        total_progress = sum(t.progress for t in all_tasks)
        overall_progress = total_progress / len(all_tasks) if all_tasks else 0

        # Get current task
        current_task = None
        for task in all_tasks:
            if task.is_in_progress:
                current_task = {
                    "id": task.id,
                    "description": task.description,
                    "duration": task.estimated_duration,
                    "started_at": task.started_at,
                }
                break

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overall_progress": overall_progress,
            "current_task": current_task,
            "tasks": [
                asdict(t)
                for t in all_tasks
                if not any(t.id in parent.subtasks for parent in all_tasks)
            ],
        }

    def get_recommended_task(
        self, energy_level: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        """
        Get AI-recommended next task based on ADHD considerations.

        Args:
            energy_level: Current energy level (low, medium, high)

        Returns:
            Recommended task or None
        """
        available_tasks = [t for t in self._tasks.values() if t.can_start]

        if not available_tasks:
            return None

        # Score tasks based on ADHD factors
        scored_tasks = []
        for task in available_tasks:
            score = self._calculate_task_score(task, energy_level)
            scored_tasks.append((score, task))

        # Sort by score (highest first)
        scored_tasks.sort(key=lambda x: x[0], reverse=True)

        best_task = scored_tasks[0][1]
        return asdict(best_task)

    def update_progress(self, task_id: str, progress: float) -> bool:
        """
        Update task progress.

        Args:
            task_id: Task ID
            progress: Progress value (0.0 to 1.0)

        Returns:
            True if updated successfully
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        task.progress = max(0.0, min(1.0, progress))

        # Auto-complete if progress reaches 100%
        if task.progress >= 1.0 and task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()

        self._save_tasks()
        return True

    def _decompose_task(self, main_task: Task) -> List[Task]:
        """
        Decompose a large task into smaller subtasks.

        Args:
            main_task: Task to decompose

        Returns:
            List of subtasks
        """
        subtasks = []
        total_duration = main_task.estimated_duration

        # Calculate number of subtasks needed
        num_subtasks = max(
            2,
            (total_duration + self.optimal_task_duration - 1)
            // self.optimal_task_duration,
        )
        subtask_duration = total_duration // num_subtasks

        # Create subtasks
        for i in range(num_subtasks):
            subtask_id = str(uuid.uuid4())[:8]

            subtask = Task(
                id=subtask_id,
                description=f"{main_task.description} (part {i+1}/{num_subtasks})",
                priority=main_task.priority,
                status=TaskStatus.PENDING,
                estimated_duration=subtask_duration,
                energy_required=main_task.energy_required,
                tags=main_task.tags + [f"subtask-{i+1}"],
            )

            # Set dependencies (each subtask depends on previous)
            if i > 0:
                subtask.dependencies = [subtasks[i - 1].id]

            subtasks.append(subtask)

        return subtasks

    def _calculate_task_score(self, task: Task, energy_level: str) -> float:
        """
        Calculate task recommendation score based on ADHD factors.

        Args:
            task: Task to score
            energy_level: Current energy level

        Returns:
            Task score (higher is better)
        """
        score = 0.0

        # Priority score (0-4)
        priority_scores = {
            TaskPriority.URGENT: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1,
        }
        score += priority_scores[task.priority]

        # Energy match score (0-2)
        energy_scores = {"low": 1, "medium": 2, "high": 3}
        user_energy = energy_scores[energy_level]
        task_energy = energy_scores[task.energy_required]

        if user_energy >= task_energy:
            score += 2  # Can handle this task
        else:
            score -= 1  # Task might be too demanding

        # Duration preference (shorter tasks preferred for ADHD)
        if task.estimated_duration <= self.optimal_task_duration:
            score += 1
        elif task.estimated_duration > self.max_task_duration:
            score -= 1

        # Age penalty (older tasks get higher priority)
        created = datetime.fromisoformat(task.created_at)
        age_days = (datetime.now() - created).days
        score += min(age_days * 0.1, 1.0)  # Max 1 point for age

        return score

    def _show_task_progress(self, task_id: str) -> None:
        """Show visual progress for a task."""
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]

        if task.subtasks:
            completed_subtasks = sum(
                1
                for st_id in task.subtasks
                if st_id in self._tasks and self._tasks[st_id].is_completed
            )
            total_subtasks = len(task.subtasks)

            # Create progress bar
            progress_chars = "█" * (completed_subtasks * 10 // total_subtasks)
            remaining_chars = "░" * (10 - len(progress_chars))
            progress_bar = f"[{progress_chars}{remaining_chars}]"

            console.print(
                f"Progress: {progress_bar} {completed_subtasks}/{total_subtasks} subtasks ✅"
            )

    def _check_unblocked_tasks(self) -> None:
        """Check for tasks that became available after completion."""
        newly_available = []

        for task in self._tasks.values():
            if (
                task.status == TaskStatus.PENDING
                and task.dependencies
                and all(
                    self._tasks.get(dep_id, {}).status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if dep_id in self._tasks
                )
            ):

                # Clear dependencies since they're complete
                task.dependencies = []
                newly_available.append(task)

        if newly_available:
            console.print(
                f"[green]🚀 {len(newly_available)} task(s) now available![/green]"
            )
            for task in newly_available:
                console.print(f"  • {task.description}")

    def _log_task_session(self, task_id: str, action: str, notes: str = "") -> None:
        """Log task session for analytics."""
        session_entry = {
            "task_id": task_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
        }

        sessions = []
        if self.sessions_file.exists():
            with open(self.sessions_file, "r") as f:
                sessions = json.load(f)

        sessions.append(session_entry)

        # Keep only last 1000 entries
        sessions = sessions[-1000:]

        with open(self.sessions_file, "w") as f:
            json.dump(sessions, f, indent=2)

    def _load_tasks(self) -> None:
        """Load tasks from storage."""
        if not self.tasks_file.exists():
            return

        try:
            with open(self.tasks_file, "r") as f:
                data = json.load(f)

            for task_data in data:
                task = Task(**task_data)
                # Convert string enums back
                task.priority = TaskPriority(task.priority)
                task.status = TaskStatus(task.status)
                self._tasks[task.id] = task

        except Exception as e:
            console.print(f"[red]Error loading tasks: {e}[/red]")

    def _save_tasks(self) -> None:
        """Save tasks to storage."""
        try:
            data = []
            for task in self._tasks.values():
                task_dict = asdict(task)
                task_dict["priority"] = task.priority.value
                task_dict["status"] = task.status.value
                data.append(task_dict)

            with open(self.tasks_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            console.print(f"[red]Error saving tasks: {e}[/red]")
