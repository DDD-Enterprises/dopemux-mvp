"""
Legacy-compatible task manager for CLI and test workflows.

This lightweight implementation keeps the original Dopemux task CLI working
while the new ConPort-first flow rolls out. It persists tasks to
``{workspace}/.dopemux/tasks/tasks.json`` and exposes the handful of methods
that existing tests exercise.
"""

from __future__ import annotations

import json
import uuid
import tempfile
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _now() -> str:
    """Return current timestamp in ISO-8601 format (UTC)."""
    return datetime.now(timezone.utc).isoformat()


class TaskStatus(Enum):
    """Simple task lifecycle states."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class TaskRecord:
    """Persisted representation of a task."""

    id: str
    description: str
    estimated_duration: int
    priority: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    created_at: str = field(default_factory=_now)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        """Convert to JSON-friendly dict."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "TaskRecord":
        """Create a record from persisted JSON."""
        status_value = data.get("status", TaskStatus.PENDING.value)
        try:
            status = TaskStatus(status_value)
        except ValueError:
            status = TaskStatus.PENDING

        return cls(
            id=str(data["id"]),
            description=str(data["description"]),
            estimated_duration=int(data.get("estimated_duration", 25)),
            priority=str(data.get("priority", "medium")),
            status=status,
            progress=float(data.get("progress", 0.0)),
            created_at=str(data.get("created_at", _now())),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )


class TaskDecomposer:
    """
    Backwards-compatible task tracker used by the CLI.

    The original TaskDecomposer class lived under ``dopemux.adhd`` and stored
    JSON next to project metadata. The newer architecture has moved that logic
    into ConPort and MetaMCP, but the CLI (and associated tests) still rely on
    a thin synchronous manager. This implementation keeps that interface alive.
    """

    def __init__(self, workspace: Path | str):
        self.workspace = Path(workspace).expanduser()
        fallback = None
        try:
            self.workspace = self.workspace.resolve()
        except Exception as e:
            fallback = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))
            self.workspace = fallback

            logger.error(f"Error: {e}")
        self.dopemux_dir = self.workspace / ".dopemux"
        self.tasks_dir = self.dopemux_dir / "tasks"
        self.tasks_file = self.tasks_dir / "tasks.json"

        try:
            self.dopemux_dir.mkdir(parents=True, exist_ok=True)
            self.tasks_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))
            self.workspace = fallback
            self.dopemux_dir = self.workspace / ".dopemux"
            self.tasks_dir = self.dopemux_dir / "tasks"
            self.tasks_file = self.tasks_dir / "tasks.json"
            self.dopemux_dir.mkdir(parents=True, exist_ok=True)
            self.tasks_dir.mkdir(parents=True, exist_ok=True)

        self._tasks: Dict[str, TaskRecord] = {}
        self._load()

    # --------------------------------------------------------------------- #
    # CRUD operations
    # --------------------------------------------------------------------- #

    def add_task(
        self,
        description: str,
        duration: int = 25,
        priority: str = "medium",
        **extra: object,
    ) -> str:
        """
        Add a new task and persist immediately.

        Args:
            description: Human-readable description.
            duration: Estimated minutes to complete.
            priority: Task priority label.
            extra: Unused legacy parameters (accepted for compatibility).
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        record = TaskRecord(
            id=task_id,
            description=description,
            estimated_duration=max(1, int(duration)),
            priority=str(priority),
        )
        self._tasks[task_id] = record
        self._save()
        return task_id

    def list_tasks(self) -> List[Dict[str, object]]:
        """Return basic task details for CLI rendering."""
        return [
            {
                "id": task.id,
                "description": task.description,
                "priority": task.priority,
                "estimated_duration": task.estimated_duration,
                "status": task.status.value,
                "progress": round(task.progress, 2),
            }
            for task in self._tasks.values()
        ]

    def get_progress(self) -> Dict[str, object]:
        """Return summary used by `dopemux status`."""
        tasks = [
            {
                "id": task.id,
                "name": task.description,
                "completed": task.status is TaskStatus.COMPLETED,
                "in_progress": task.status is TaskStatus.IN_PROGRESS,
                "progress": round(task.progress, 2),
            }
            for task in self._tasks.values()
        ]

        return {
            "tasks": tasks,
            "summary": {
                "total": len(tasks),
                "completed": sum(1 for t in tasks if t["completed"]),
                "in_progress": sum(1 for t in tasks if t["in_progress"]),
            },
        }

    # --------------------------------------------------------------------- #
    # State transitions
    # --------------------------------------------------------------------- #

    def start_task(self, task_id: str) -> bool:
        """Mark a task as in progress."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = _now()
        if task.progress <= 0.0:
            task.progress = 0.01
        self._save()
        return True

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = _now()
        if task.started_at is None:
            task.started_at = task.completed_at
        self._save()
        return True

    def update_progress(self, task_id: str, progress: float) -> bool:
        """Update fractional progress (0.0 - 1.0)."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        normalized = max(0.0, min(1.0, float(progress)))
        task.progress = normalized

        if normalized >= 1.0:
            task.status = TaskStatus.COMPLETED
            task.completed_at = task.completed_at or _now()
        elif normalized > 0 and task.status is TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = task.started_at or _now()

        self._save()
        return True

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _load(self) -> None:
        """Load tasks from disk if available."""
        if not self.tasks_file.exists():
            return

        try:
            with self.tasks_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}

        tasks = data.get("tasks", [])
        for entry in tasks:
            try:
                record = TaskRecord.from_dict(entry)
                self._tasks[record.id] = record
            except Exception as e:
                continue

                logger.error(f"Error: {e}")
    def _save(self) -> None:
        """Persist tasks to disk."""
        payload = {
            "version": 1,
            "tasks": [task.to_dict() for task in self._tasks.values()],
        }
        tmp_file = self.tasks_file.with_suffix(".tmp")
        with tmp_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        tmp_file.replace(self.tasks_file)

    # --------------------------------------------------------------------- #
    # Legacy compatibility helpers
    # --------------------------------------------------------------------- #

    def __iter__(self) -> Iterable[TaskRecord]:
        return iter(self._tasks.values())
