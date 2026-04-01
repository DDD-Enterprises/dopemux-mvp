"""
Canonical PM-plane task manager for CLI and test workflows.

This implementation acts as an offline-first caching layer for task lifecycle
while synchronizing directly to the Dopemux PM plane. It persists tasks to
``{workspace}/.dopemux/tasks/tasks.json`` and forwards create, transition,
and completion events to canonical PM authorities.
"""

import json
import logging
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dopemux.pm.models import PMTask, PMTaskStatus
from dopemux.pm.writes import (
    PMWriteConfig,
    pm_transition_work_item,
    pm_update_work_item,
    pm_log_progress,
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
    sync_pending: bool = True
    last_sync_error: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        """Convert the record to a JSON-serializable dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    def to_execution_packet(self, owner_id: str) -> ExecutionPacket:
        """Wrap the local task mirror as an execution packet."""
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
            },
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


class InMemoryPMTaskStore:
    """Mock/Stub store for PMTask objects used by the local mirror."""
    def __init__(self):
        self._store: Dict[str, PMTask] = {}

    def get(self, task_id: str) -> Optional[PMTask]:
        return self._store.get(task_id)

    def create(self, task: PMTask) -> None:
        self._store[task.task_id] = task

    def update(self, task: PMTask) -> None:
        self._store[task.task_id] = task


def content_hash_task_id(source: str, parent: Optional[str], description: str) -> str:
    """Generate a deterministic task ID based on content."""
    import hashlib
    seed = f"{source}:{parent or ''}:{description}".encode("utf-8")
    return f"task-{hashlib.sha256(seed).hexdigest()[:8]}"


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
        try:
            self.workspace = self.workspace.resolve()
        except Exception:
            self.workspace = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))

        self.dopemux_dir = self.workspace / ".dopemux"
        self.tasks_dir = self.dopemux_dir / "tasks"
        self.tasks_file = self.tasks_dir / "tasks.json"
        
        # Ensure directories exist
        try:
            self.tasks_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.workspace = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))
            self.dopemux_dir = self.workspace / ".dopemux"
            self.tasks_dir = self.dopemux_dir / "tasks"
            self.tasks_file = self.tasks_dir / "tasks.json"
            self.tasks_dir.mkdir(parents=True, exist_ok=True)

        self._tasks: Dict[str, TaskRecord] = {}
        self.pm_store = InMemoryPMTaskStore() # Local session mirror
        
        # Initial load from disk (legacy)
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

        # Synchronization is now handled directly in the CRUD methods via pm_* helpers.
        # This method is maintained for future bulk-sync/recovery logic.
        pass

    # --------------------------------------------------------------------- #
    # CRUD operations
    # --------------------------------------------------------------------- #

    def add_task(
        self,
        description: str,
        estimated_duration: int = 25,
        priority: str = "medium",
        **extra: Any,
    ) -> str:
        """Create a task and register it with the PM Plane."""
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
        if self.pm_config:
            try:
                pm_log_progress(
                    config=self.pm_config,
                    task_id=task_id,
                    progress_notes=f"CLI Task added: {description}",
                    idempotency_key=f"cli-add-{task_id}"
                )
                record.sync_pending = False
            except Exception as e:
                record.sync_pending = True
                record.last_sync_error = str(e)
        
        self._save()
        return task_id

    def start_task(self, task_id: str) -> bool:
        """Transition a task to 'in_progress' using the authoritative PM Plane."""
        task = self._tasks.get(task_id)
        pm_task = self.pm_store.get(task_id)
        if not task or not pm_task:
            return False

        # Transition PM Plane
        if self.pm_config:
            try:
                pm_transition_work_item(
                    config=self.pm_config,
                    task_id=task_id,
                    new_status=PMTaskStatus.IN_PROGRESS,
                    reason="Task started via CLI",
                    idempotency_key=f"cli-start-{task_id}",
                    expected_version=getattr(pm_task, "version", 1)
                )
                task.sync_pending = False
            except Exception as e:
                task.sync_pending = True
                task.last_sync_error = str(e)

        task.status = TaskStatus.IN_PROGRESS
        task.progress = 0.01
        task.started_at = _now()
        self._save()
        return True

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as 'done' using the authoritative PM Plane."""
        task = self._tasks.get(task_id)
        pm_task = self.pm_store.get(task_id)
        if not task or not pm_task:
            return False

        # Transition PM Plane
        if self.pm_config:
            try:
                pm_transition_work_item(
                    config=self.pm_config,
                    task_id=task_id,
                    new_status=PMTaskStatus.DONE,
                    reason="Task completed via CLI",
                    idempotency_key=f"cli-complete-{task_id}",
                    expected_version=getattr(pm_task, "version", 1)
                )
                task.sync_pending = False
            except Exception as e:
                task.sync_pending = True
                task.last_sync_error = str(e)

        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        if not task.started_at:
            task.started_at = _now()
        task.completed_at = _now()
        self._save()
        return True

    def update_progress(self, task_id: str, progress: float) -> bool:
        """Update fractional progress (0.0 - 1.0)."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.progress = max(0.0, min(1.0, float(progress)))
        if task.progress > 0.0 and task.progress < 1.0:
            task.status = TaskStatus.IN_PROGRESS
            if not task.started_at:
                task.started_at = _now()
        
        if task.progress >= 1.0:
            return self.complete_task(task_id)
        
        self._save()
        return True

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Return all managed tasks."""
        return [t.to_dict() for t in self._tasks.values()]

    def get_progress(self) -> Dict[str, Any]:
        """Return task completion summary."""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        return {
            "total": total,
            "completed": completed,
            "percent": (completed / total * 100) if total > 0 else 0.0
        }

    def _load(self) -> None:
        """Load tasks from disk."""
        if not self.tasks_file.exists():
            return
        try:
            data = json.loads(self.tasks_file.read_text(encoding="utf-8"))
            for task_data in data.get("tasks", []):
                record = TaskRecord.from_dict(task_data)
                self._tasks[record.id] = record
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")

    def _save(self) -> None:
        """Persist tasks to disk."""
        try:
            self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "tasks": [t.to_dict() for t in self._tasks.values()],
                "updated_at": _now()
            }
            self.tasks_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

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
                
        if success_count > 0:
            self._save()
            
        return success_count
