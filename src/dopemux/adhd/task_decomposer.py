"""
Task Decomposer for ADHD-optimized development.

Breaks complex tasks into manageable 25-minute chunks with visual progress
tracking and dependency management.
"""

import json
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from rich.console import Console
from dopemux.pm.models import PMTaskStatus
from dopemux.pm.writes import pm_transition_work_item

console = Console()


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().upper()
            for member in cls:
                if member.value == normalized:
                    return member
        return None


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


@dataclass
class TaskRecord:
    """Compatibility adapter for execution-plane handoff tests and callers."""

    id: str
    description: str
    estimated_duration: int
    priority: str = "medium"
    status: TaskStatus = TaskStatus.PENDING

    def to_execution_packet(self, owner_id: str):
        """Project a task record into the execution packet contract."""
        from dopemux.execution.models import ExecutionPacket, PacketState

        state_map = {
            TaskStatus.PENDING: PacketState.READY,
            TaskStatus.IN_PROGRESS: PacketState.EXECUTING,
            TaskStatus.COMPLETED: PacketState.PROOF_GENERATED,
            TaskStatus.BLOCKED: PacketState.PENDING,
            TaskStatus.CANCELLED: PacketState.CANCELLED,
        }
        task_status = (
            self.status if isinstance(self.status, TaskStatus) else TaskStatus(self.status)
        )
        return ExecutionPacket(
            packet_id=self.id,
            owner_id=owner_id,
            task_id=self.id,
            state=state_map[task_status],
            metadata={
                "description": self.description,
                "priority": self.priority,
                "estimated_duration": self.estimated_duration,
            },
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

    def __init__(
        self,
        project_path: Optional[Path] = None,
        *,
        workspace: Optional[Path] = None,
        pm_config: Any = None,
    ):
        """Initialize task decomposer."""
        requested_workspace = workspace if workspace is not None else project_path
        if requested_workspace is None:
            raise TypeError("TaskDecomposer requires project_path or workspace")

        self.project_path = Path(requested_workspace)
        self.pm_config = pm_config
        self.workspace = self._resolve_workspace(self.project_path)
        self.data_dir = self.workspace / ".dopemux" / "tasks"
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self._fallback_workspace()

        self.tasks_dir = self.data_dir
        self.tasks_file = self.data_dir / "tasks.json"
        self.sessions_file = self.data_dir / "task_sessions.json"

        self._tasks: Dict[str, Task] = {}
        self._load_tasks()

        # ADHD-specific settings
        self.max_task_duration = 60  # minutes
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
        **_: Any,
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
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        duration = max(1, int(duration))
        priority_text = str(priority)

        task = Task(
            id=task_id,
            description=description,
            priority=self._normalize_priority(priority_text),
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
        self._sync_to_pm_plane(task_id, PMTaskStatus.TODO, "task created")

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
        task.progress = max(task.progress, 0.01)
        self._save_tasks()
        self._sync_to_pm_plane(task_id, PMTaskStatus.IN_PROGRESS, "task started")

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
        completion_time = datetime.now().isoformat()
        if task.started_at:
            start_time = datetime.fromisoformat(task.started_at)
            actual_duration = (datetime.now() - start_time).total_seconds() / 60
            task.actual_duration = int(actual_duration)
        else:
            task.started_at = completion_time

        task.status = TaskStatus.COMPLETED
        task.completed_at = completion_time
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
        self._sync_to_pm_plane(task_id, PMTaskStatus.DONE, "task completed")

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
            if status and task.status.value.lower() != status.lower():
                continue

            # Skip subtasks in main list (they'll be shown under parent)
            is_subtask = any(
                task.id in parent.subtasks for parent in self._tasks.values()
            )
            if is_subtask:
                continue

            task_dict = asdict(task)
            task_dict["priority"] = task.priority.value
            task_dict["status"] = task.status.value.lower()

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
            key=lambda t: (
                priority_order.get(
                    self._normalize_priority(t["priority"]), len(priority_order)
                ),
                t["created_at"],
            )
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

        task_items = [
            self._task_to_dict(t)
            for t in all_tasks
            if not any(t.id in parent.subtasks for parent in all_tasks)
        ]

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overall_progress": overall_progress,
            "current_task": current_task,
            "tasks": task_items,
            "summary": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
            },
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
            if not task.started_at:
                task.started_at = datetime.now().isoformat()
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            self._sync_to_pm_plane(task_id, PMTaskStatus.DONE, "task progress completed")
        elif task.progress > 0.0:
            task.status = TaskStatus.IN_PROGRESS
            if not task.started_at:
                task.started_at = datetime.now().isoformat()
            self._sync_to_pm_plane(task_id, PMTaskStatus.IN_PROGRESS, "task progress updated")

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

            task_rows = data.get("tasks", data) if isinstance(data, dict) else data

            for task_data in task_rows:
                task = Task(**task_data)
                # Convert string enums back
                task.priority = self._normalize_priority(task.priority)
                task.status = TaskStatus(task.status)
                self._tasks[task.id] = task

        except Exception as e:
            console.print(f"[red]Error loading tasks: {e}[/red]")

    def _save_tasks(self) -> None:
        """Save tasks to storage."""
        try:
            data = []
            for task in self._tasks.values():
                data.append(self._task_to_dict(task))

            with open(self.tasks_file, "w") as f:
                json.dump({"tasks": data}, f, indent=2)

        except Exception as e:
            console.print(f"[red]Error saving tasks: {e}[/red]")

    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Normalize task serialization for stable persistence and CLI output."""
        task_dict = asdict(task)
        task_dict["priority"] = task.priority.value
        task_dict["status"] = task.status.value.lower()
        return task_dict

    def __iter__(self) -> Iterator[Task]:
        """Allow iteration over tracked tasks."""
        return iter(self._tasks.values())

    def _resolve_workspace(self, workspace: Path) -> Path:
        """Resolve the workspace path, falling back if resolution is unavailable."""
        try:
            return workspace.resolve()
        except (PermissionError, OSError):
            return Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))

    def _fallback_workspace(self) -> None:
        """Move persistence into a writable temporary workspace."""
        self.workspace = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))
        self.data_dir = self.workspace / ".dopemux" / "tasks"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_priority(self, priority: str) -> TaskPriority:
        """Convert known priorities to enum values while preserving legacy strings."""
        try:
            return TaskPriority(priority)
        except ValueError:
            class LegacyPriority(str):
                @property
                def value(self) -> str:
                    return str(self)

            return LegacyPriority(priority)

    def _sync_to_pm_plane(
        self, task_id: str, new_status: PMTaskStatus, reason: str
    ) -> bool:
        """Best-effort PM plane synchronization for task lifecycle changes."""
        if self.pm_config is None:
            return False

        try:
            pm_transition_work_item(
                config=self.pm_config,
                task_id=task_id,
                new_status=new_status,
                reason=reason,
                idempotency_key=f"task-decomposer:{task_id}:{new_status.value}",
                expected_version=1,
            )
            return True
        except Exception as exc:
            console.print(f"[yellow]PM sync skipped for {task_id}: {exc}[/yellow]")
            return False

    def backfill_to_pm_plane(self) -> int:
        """Replay current local task state into the PM plane."""
        count = 0
        status_map = {
            TaskStatus.PENDING: PMTaskStatus.TODO,
            TaskStatus.IN_PROGRESS: PMTaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED: PMTaskStatus.DONE,
            TaskStatus.BLOCKED: PMTaskStatus.BLOCKED,
            TaskStatus.CANCELLED: PMTaskStatus.CANCELED,
        }
        for task in self._tasks.values():
            try:
                if self._sync_to_pm_plane(
                    task.id,
                    status_map[task.status],
                    "task backfill",
                ):
                    count += 1
            except Exception:
                return count
        return count
