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
from dataclasses import asdict, dataclass, field
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
        except Exception:
            self.workspace = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))

        self.tasks_file = self.workspace / ".dopemux_tasks.json"
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
        
        # Sync creation
        self._sync_to_pm_plane(record, is_creation=True)
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
        
        # Sync transition
        self._sync_to_pm_plane(task, is_transition=True)
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
