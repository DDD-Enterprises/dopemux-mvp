"""
Backwards-compatible task tracker used by the CLI.

Refactored for PM-INT-24: CLI TaskRecord flow onto canonical PM plane.
Authority now resides in PM Plane (Orchestrator/ConPort).
Local file storage is kept as a local cache/mirror only.
"""

import json
import logging
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# PM Plane imports
from dopemux.pm.models import PMTask, PMTaskStatus, content_hash_task_id
from dopemux.pm.reads import pm_get_priority_queue
from dopemux.pm.write import pm_transition_work_item, pm_update_work_item, pm_log_progress
from dopemux.pm.store import InMemoryPMTaskStore

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Legacy task lifecycle statuses for CLI compatibility.
    
    Mapped to authoritative PMTaskStatus values.
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


def _now() -> str:
    """Helper to get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TaskRecord:
    """Legacy persisted representation of a task.
    
    This class is maintained for backwards compatibility with the CLI's 
    local JSON storage. In the current architecture, this data is treated 
    as a local mirror/cache, while the PM Plane holds the canonical truth.
    """
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
        """Convert the record to a JSON-serializable dictionary."""
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
    """Backwards-compatible task tracker used by the CLI.

    Refactored for PM-INT-24: Authority has moved to the PM Plane 
    (Task Orchestrator / ConPort). This class now serves as a thin 
    adapter that synchronizes legacy CLI commands with the authoritative 
    canonical tools.
    """

    def __init__(self, workspace: Path | str):
        """Initialize the decomposer and seed the local PM mirror.
        
        Args:
            workspace: The path to the project workspace.
        """
        self.workspace = Path(workspace).expanduser()
        try:
            self.workspace = self.workspace.resolve()
        except Exception:
            self.workspace = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))

        self.tasks_file = self.workspace / ".dopemux_tasks.json"
        self._tasks: Dict[str, TaskRecord] = {}
        self.pm_store = InMemoryPMTaskStore() # Local session mirror
        
        # Initial load from disk (legacy)
        self._load()

    async def add_task(
        self,
        description: str,
        estimated_duration: int = 25,
        priority: str = "medium",
    ) -> str:
        """Create a task and register it with the PM Plane.
        
        Orchestration Flow:
        1. Generates a deterministic canonical ID.
        2. Creates a `PMTask` in the local session mirror.
        3. Synchronizes the creation with the ConPort/Chronicle backends
           via `pm_log_progress`.
        4. Updates the legacy local JSON file.

        Args:
            description: The task summary.
            estimated_duration: Expected time in minutes.
            priority: Semantic priority level.

        Returns:
            The generated canonical task ID.
        """
        task_id = content_hash_task_id("cli", None, description)
        
        # 1. Create locally
        pm_task = PMTask(
            task_id=task_id,
            title=description,
            description=description,
            status=PMTaskStatus.TODO,
            source="cli",
            created_at_utc=datetime.now(timezone.utc),
            updated_at_utc=datetime.now(timezone.utc),
            meta={"estimated_duration": estimated_duration}
        )
        self.pm_store.create(pm_task)
        
        # 2. Record legacy representation
        record = TaskRecord(
            id=task_id,
            description=description,
            estimated_duration=estimated_duration,
            priority=priority,
        )
        self._tasks[task_id] = record
        
        # 3. Synchronize with PM Plane (ConPort/Chronicle)
        await pm_log_progress(
            workspace_id=str(self.workspace),
            task_id=task_id,
            status="PLANNED",
            summary=f"CLI Task added: {description}",
            idempotency_key=f"cli-add-{task_id}"
        )
        
        self._save()
        return task_id

    async def start_task(self, task_id: str) -> bool:
        """Transition a task to 'in_progress' using the authoritative PM Plane.
        
        Args:
            task_id: The canonical ID of the task.

        Returns:
            True if the transition was accepted by the PM Plane, False otherwise.
        """
        task = self._tasks.get(task_id)
        pm_task = self.pm_store.get(task_id)
        if not task or not pm_task:
            return False

        # Transition PM Plane
        await pm_transition_work_item(
            store=self.pm_store,
            task_id=task_id,
            project_id="default",
            workflow_id=task_id,
            new_status="IN_PROGRESS",
            expected_version=pm_task.version,
            idempotency_key=f"cli-start-{task_id}"
        )

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = _now()
        self._save()
        return True

    async def complete_task(self, task_id: str) -> bool:
        """Mark a task as 'done' using the authoritative PM Plane.
        
        Args:
            task_id: The canonical ID of the task.

        Returns:
            True if the transition was accepted, False otherwise.
        """
        task = self._tasks.get(task_id)
        pm_task = self.pm_store.get(task_id)
        if not task or not pm_task:
            return False

        # Transition PM Plane
        await pm_transition_work_item(
            store=self.pm_store,
            task_id=task_id,
            project_id="default",
            workflow_id=task_id,
            new_status="DONE",
            expected_version=pm_task.version,
            idempotency_key=f"cli-complete-{task_id}"
        )

        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = _now()
        self._save()
        return True

    def _load(self) -> None:
        """Load legacy JSON and seed the PM Plane mirror."""
        if not self.tasks_file.exists():
            return
        try:
            with self.tasks_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("tasks", []):
                record = TaskRecord.from_dict(entry)
                self._tasks[record.id] = record
                
                # Seed local PM store mirror
                self.pm_store.create(PMTask(
                    task_id=record.id,
                    title=record.description,
                    source="cli",
                    created_at_utc=datetime.now(timezone.utc),
                    updated_at_utc=datetime.now(timezone.utc)
                ))
        except Exception:
            pass

    def _save(self) -> None:
        """Persist the legacy JSON mirror to disk."""
        payload = {
            "version": 1,
            "tasks": [task.to_dict() for task in self._tasks.values()],
        }
        tmp_file = self.tasks_file.with_suffix(".tmp")
        with tmp_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        tmp_file.replace(self.tasks_file)

    def __iter__(self) -> Iterable[TaskRecord]:
        """Allow iteration over legacy task records."""
        return iter(self._tasks.values())
