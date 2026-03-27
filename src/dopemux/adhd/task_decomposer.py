"""
Canonical PM-plane task manager for CLI and test workflows.

This implementation acts as an offline-first caching layer for task lifecycle
while synchronizing directly to the Dopemux PM plane. It persists tasks to
``{workspace}/.dopemux/tasks/tasks.json`` and forwards create, transition,
and completion events to canonical PM authorities.
"""

from __future__ import annotations
import logging


import json
import uuid
import tempfile
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dopemux.pm.models import PMTaskStatus
from dopemux.pm.writes import (
    PMWriteConfig,
    pm_transition_work_item,
    pm_update_work_item,
)
from dopemux.execution.models import ExecutionPacket, PacketState


logger = logging.getLogger(__name__)

def _now() -> str:
    """Return current timestamp in ISO-8601 format (UTC)."""
    return datetime.now(timezone.utc).isoformat()

class TaskStatus(Enum):
    """Simple task lifecycle states mapping to Canonical PM status."""

    PENDING = PMTaskStatus.TODO.value
    IN_PROGRESS = PMTaskStatus.IN_PROGRESS.value
    COMPLETED = PMTaskStatus.DONE.value


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
    sync_pending: bool = True
    last_sync_error: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        """Convert to JSON-friendly dict."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    def to_execution_packet(self, owner_id: str) -> ExecutionPacket:
        """Wrap the task record into an ExecutionPacket."""
        state_map = {
            TaskStatus.PENDING: PacketState.READY,
            TaskStatus.IN_PROGRESS: PacketState.EXECUTING,
            TaskStatus.COMPLETED: PacketState.PROOF_GENERATED,
        }
        return ExecutionPacket(
            packet_id=self.id,
            owner_id=owner_id,
            state=state_map.get(self.status, PacketState.READY),
            metadata={
                "description": self.description,
                "priority": self.priority,
                "estimated_duration": self.estimated_duration,
            }
        )

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
            sync_pending=bool(data.get("sync_pending", True)),
            last_sync_error=data.get("last_sync_error"),
        )


class TaskDecomposer:
    """
    Canonical PM-plane-backed task tracker used by the CLI.

    The original TaskDecomposer class persisted exclusively to local disk.
    Now, it acts as a queue/offline cache while delegating real authority to 
    the PM Plane's normalized transition paths (Leantime, Task Orchestrator, ConPort).
    """

    def __init__(self, workspace: Path | str, pm_config: Optional[PMWriteConfig] = None):
        self.workspace = Path(workspace).expanduser()
        self.pm_config = pm_config
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
    # PM Plane Canonical Synchronization
    # --------------------------------------------------------------------- #

    def _sync_to_pm_plane(self, task: TaskRecord, is_transition: bool = False, is_creation: bool = False) -> None:
        """Attempt to synchronize a task update to the canonical PM plane."""
        if not self.pm_config:
            # If no PM config, mark task as needing sync and bail.
            # Local disk remains offline queue.
            task.sync_pending = True
            task.last_sync_error = "No PM config available"
            return

        idempotency_key = f"{task.id}-{task.status.value}-{task.progress}"
        
        # Translate to Canonical Status
        new_status = PMTaskStatus(task.status.value)
        
        try:
            if is_creation:
                pm_update_work_item(
                    config=self.pm_config,
                    task_id=task.id,
                    updates={"title": task.description, "description": task.description},
                    idempotency_key=f"create-{idempotency_key}",
                )
                
            if is_transition or is_creation:
                pm_transition_work_item(
                    config=self.pm_config,
                    task_id=task.id,
                    new_status=new_status,
                    reason="cli_task_update",
                    idempotency_key=f"transition-{idempotency_key}",
                    expected_version=1, # CLI cache uses version 1 as naive stub
                )
            
            # Record explicit sync success
            task.sync_pending = False
            task.last_sync_error = None
        except Exception as e:
            # Explicit fail-closed offline queue behavior: record the failure on the record.
            # Avoids shadow authority by explicitly marking state pending.
            task.sync_pending = True
            task.last_sync_error = str(e)
            logger.debug(f"PM sync failed, queued offline: {e}")
            
        self._save()


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
        
        # Sync creation
        self._sync_to_pm_plane(record, is_creation=True)
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
        
        # Sync transition
        self._sync_to_pm_plane(task, is_transition=True)
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
        
        # Sync transition
        self._sync_to_pm_plane(task, is_transition=True)
        return True

    def update_progress(self, task_id: str, progress: float) -> bool:
        """Update fractional progress (0.0 - 1.0)."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        normalized = max(0.0, min(1.0, float(progress)))
        task.progress = normalized
        
        status_changed = False

        if normalized >= 1.0:
            if task.status != TaskStatus.COMPLETED:
                status_changed = True
            task.status = TaskStatus.COMPLETED
            task.completed_at = task.completed_at or _now()
        elif normalized > 0 and task.status is TaskStatus.PENDING:
            status_changed = True
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = task.started_at or _now()

        self._save()
        
        # Sync progress/transition
        self._sync_to_pm_plane(task, is_transition=status_changed)
        return True

    # --------------------------------------------------------------------- #
    # Importer / Backfill
    # --------------------------------------------------------------------- #

    def backfill_to_pm_plane(self) -> int:
        """
        Backfill all currently local tasks to the PM plane.
        Useful when transitioning an existing workspace to the PM-plane architecture,
        or recovering after being offline.
        
        Returns the number of tasks successfully synced.
        """
        if not self.pm_config:
            return 0
            
        success_count = 0
        for task in self._tasks.values():
            if not task.sync_pending:
                continue
                
            try:
                # We do both a metadata update and a status transition to ensure fully synced
                self._sync_to_pm_plane(task, is_creation=True)
                if not task.sync_pending:
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to backfill task {task.id}: {e}")
                
        return success_count


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
