"""
Legacy task decomposer with a local JSON mirror and optional PM-plane sync.

The CLI and test suite still rely on a synchronous task tracker rooted at
``{workspace}/.dopemux/tasks/tasks.json``. This module preserves that contract
while treating PM-plane writes as best-effort mirrors behind ``PMWriteConfig``.
"""

from __future__ import annotations

import json
import logging
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from dopemux.execution.models import ExecutionPacket, PacketState
from dopemux.pm.models import PMTask, PMTaskStatus
from dopemux.pm.store import InMemoryPMTaskStore
from dopemux.pm.writes import PMWriteConfig, pm_transition_work_item, pm_update_work_item

logger = logging.getLogger(__name__)


def _now() -> str:
    """Return the current timestamp in ISO-8601 UTC format."""

    return datetime.now(timezone.utc).isoformat()


class TaskStatus(Enum):
    """Local task lifecycle states mirrored into canonical PM statuses."""

    PENDING = PMTaskStatus.TODO.value
    IN_PROGRESS = PMTaskStatus.IN_PROGRESS.value
    COMPLETED = PMTaskStatus.DONE.value


_TASK_STATUS_TO_PM_STATUS = {
    TaskStatus.PENDING: PMTaskStatus.TODO,
    TaskStatus.IN_PROGRESS: PMTaskStatus.IN_PROGRESS,
    TaskStatus.COMPLETED: PMTaskStatus.DONE,
}

_TASK_STATUS_TO_LIST_STATUS = {
    TaskStatus.PENDING: "pending",
    TaskStatus.IN_PROGRESS: "in_progress",
    TaskStatus.COMPLETED: "completed",
}

_LEGACY_FILE_NAME = ".dopemux_tasks.json"


def _status_from_value(value: object) -> TaskStatus:
    """Parse persisted task status from old or new representations."""

    if isinstance(value, TaskStatus):
        return value
    text = str(value or TaskStatus.PENDING.value).strip()
    if text in {status.value for status in TaskStatus}:
        return TaskStatus(text)
    normalized = text.lower()
    if normalized == "pending":
        return TaskStatus.PENDING
    if normalized == "in_progress":
        return TaskStatus.IN_PROGRESS
    if normalized == "completed":
        return TaskStatus.COMPLETED
    return TaskStatus.PENDING


@dataclass
class TaskRecord:
    """Persisted local mirror of a CLI task."""

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
    pm_version: int = 1

    def to_dict(self) -> Dict[str, object]:
        """Convert the record to a JSON-serializable dictionary."""

        data = asdict(self)
        data["status"] = self.status.value
        data.pop("pm_version", None)
        return data

    def to_execution_packet(self, owner_id: str) -> ExecutionPacket:
        """Wrap the task mirror as an execution packet."""

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
        """Create a task record from persisted JSON."""

        return cls(
            id=str(data["id"]),
            description=str(data["description"]),
            estimated_duration=max(1, int(data.get("estimated_duration", 25))),
            priority=str(data.get("priority", "medium")),
            status=_status_from_value(data.get("status")),
            progress=float(data.get("progress", 0.0)),
            created_at=str(data.get("created_at", _now())),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            sync_pending=bool(data.get("sync_pending", True)),
            last_sync_error=data.get("last_sync_error"),
            pm_version=int(data.get("pm_version", 1)),
        )


class TaskDecomposer:
    """Synchronous task tracker used by the CLI and local tests."""

    def __init__(self, workspace: Path | str, pm_config: Optional[PMWriteConfig] = None):
        self.pm_config = pm_config
        self.pm_store = InMemoryPMTaskStore()
        self._tasks: Dict[str, TaskRecord] = {}

        self.workspace = Path(workspace).expanduser()
        try:
            self.workspace = self.workspace.resolve()
            self._configure_paths(self.workspace)
            self._ensure_storage()
        except Exception:
            fallback = Path(tempfile.mkdtemp(prefix="dopemux-tasks-"))
            self.workspace = fallback
            self._configure_paths(fallback)
            self._ensure_storage()

        self._load()

    def _configure_paths(self, workspace: Path) -> None:
        """Derive all persisted paths from the active workspace."""

        self.workspace = workspace
        self.dopemux_dir = workspace / ".dopemux"
        self.tasks_dir = self.dopemux_dir / "tasks"
        self.tasks_file = self.tasks_dir / "tasks.json"
        self.legacy_tasks_file = workspace / _LEGACY_FILE_NAME

    def _ensure_storage(self) -> None:
        """Create the on-disk task mirror structure."""

        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _next_task_id(self) -> str:
        """Generate the legacy ``task-<8 hex>`` identifier format."""

        while True:
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            if task_id not in self._tasks:
                return task_id

    def _upsert_pm_mirror(self, task: TaskRecord) -> None:
        """Keep the local PM task mirror aligned with the JSON cache."""

        existing = self.pm_store.get(task.id)
        created_at_utc = existing.created_at_utc if existing else datetime.now(timezone.utc)
        self.pm_store._tasks[task.id] = PMTask(
            task_id=task.id,
            title=task.description,
            description=task.description,
            status=_TASK_STATUS_TO_PM_STATUS[task.status],
            source="cli",
            created_at_utc=created_at_utc,
            updated_at_utc=datetime.now(timezone.utc),
            version=max(1, task.pm_version),
            meta={"estimated_duration": task.estimated_duration, "priority": task.priority},
        )

    def _sync_to_pm_plane(self, task: TaskRecord, *, is_creation: bool = False, is_transition: bool = False) -> None:
        """Best-effort mirror writes into the PM plane."""

        if self.pm_config is None:
            task.sync_pending = True
            task.last_sync_error = "No PM config available"
            return

        pm_status = _TASK_STATUS_TO_PM_STATUS[task.status]
        expected_version = max(1, task.pm_version)
        try:
            if is_creation:
                pm_update_work_item(
                    config=self.pm_config,
                    task_id=task.id,
                    updates={"title": task.description, "description": task.description},
                    idempotency_key=f"cli-create-meta-{task.id}",
                )

            if is_creation or is_transition:
                pm_transition_work_item(
                    config=self.pm_config,
                    task_id=task.id,
                    new_status=pm_status,
                    reason="cli_task_update",
                    idempotency_key=f"cli-status-{task.id}-{pm_status.value.lower()}-{expected_version}",
                    expected_version=expected_version,
                )
                task.pm_version = expected_version + 1

            task.sync_pending = False
            task.last_sync_error = None
        except Exception as exc:
            task.sync_pending = True
            task.last_sync_error = str(exc)
            logger.debug("PM sync failed for %s: %s", task.id, exc)
        finally:
            self._upsert_pm_mirror(task)
            self._save()

    def add_task(
        self,
        description: str,
        duration: int = 25,
        priority: Any = "medium",
        **_: Any,
    ) -> str:
        """Create a task in the local mirror and optionally sync it."""

        task = TaskRecord(
            id=self._next_task_id(),
            description=str(description),
            estimated_duration=max(1, int(duration)),
            priority=str(priority),
        )
        self._tasks[task.id] = task
        self._upsert_pm_mirror(task)
        self._save()
        self._sync_to_pm_plane(task, is_creation=True)
        return task.id

    def start_task(self, task_id: str) -> bool:
        """Mark a task as in progress."""

        task = self._tasks.get(task_id)
        if task is None:
            return False

        if task.started_at is None:
            task.started_at = _now()
        task.status = TaskStatus.IN_PROGRESS
        task.progress = max(task.progress, 0.01)
        self._upsert_pm_mirror(task)
        self._save()
        self._sync_to_pm_plane(task, is_transition=True)
        return True

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""

        task = self._tasks.get(task_id)
        if task is None:
            return False

        completion_ts = _now()
        if task.started_at is None:
            task.started_at = completion_ts
        task.completed_at = completion_ts
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        self._upsert_pm_mirror(task)
        self._save()
        self._sync_to_pm_plane(task, is_transition=True)
        return True

    def update_progress(self, task_id: str, progress: float) -> bool:
        """Update task progress and transition state when thresholds are crossed."""

        task = self._tasks.get(task_id)
        if task is None:
            return False

        normalized = max(0.0, min(1.0, float(progress)))
        task.progress = normalized
        status_changed = False

        if normalized >= 1.0:
            completion_ts = _now()
            if task.started_at is None:
                task.started_at = completion_ts
            if task.status is not TaskStatus.COMPLETED:
                status_changed = True
            task.status = TaskStatus.COMPLETED
            task.completed_at = completion_ts
        elif normalized > 0.0 and task.status is TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = task.started_at or _now()
            status_changed = True

        self._upsert_pm_mirror(task)
        self._save()
        self._sync_to_pm_plane(task, is_transition=status_changed)
        return True

    def list_tasks(self) -> list[dict[str, object]]:
        """Return task rows for the CLI table view."""

        return [
            {
                "id": task.id,
                "description": task.description,
                "priority": task.priority,
                "estimated_duration": task.estimated_duration,
                "status": _TASK_STATUS_TO_LIST_STATUS[task.status],
                "progress": task.progress,
            }
            for task in self._tasks.values()
        ]

    def get_progress(self) -> dict[str, object]:
        """Return task and summary progress data for ``dopemux status --tasks``."""

        tasks = [
            {
                "id": task.id,
                "name": task.description,
                "description": task.description,
                "completed": task.status is TaskStatus.COMPLETED,
                "in_progress": task.status is TaskStatus.IN_PROGRESS,
                "progress": task.progress,
                "priority": task.priority,
                "estimated_duration": task.estimated_duration,
            }
            for task in self._tasks.values()
        ]
        summary = {
            "total": len(tasks),
            "completed": sum(1 for task in self._tasks.values() if task.status is TaskStatus.COMPLETED),
            "in_progress": sum(1 for task in self._tasks.values() if task.status is TaskStatus.IN_PROGRESS),
            "pending": sum(1 for task in self._tasks.values() if task.status is TaskStatus.PENDING),
        }
        return {"tasks": tasks, "summary": summary}

    def backfill_to_pm_plane(self) -> int:
        """Sync any locally queued tasks to the PM plane."""

        if self.pm_config is None:
            return 0

        success_count = 0
        for task in self._tasks.values():
            if not task.sync_pending:
                continue
            try:
                self._sync_to_pm_plane(task, is_creation=True)
            except Exception as exc:
                logger.error("Failed to backfill task %s: %s", task.id, exc)
            else:
                if not task.sync_pending:
                    success_count += 1
        return success_count

    def _load(self) -> None:
        """Load persisted tasks from the current or legacy on-disk location."""

        source = self.tasks_file if self.tasks_file.exists() else self.legacy_tasks_file
        if not source.exists():
            return

        try:
            with source.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            logger.debug("Ignoring unreadable task cache at %s", source)
            return

        for raw_task in payload.get("tasks", []):
            try:
                task = TaskRecord.from_dict(raw_task)
            except Exception:
                logger.debug("Skipping malformed task row from %s", source)
                continue
            self._tasks[task.id] = task
            self._upsert_pm_mirror(task)

        if source == self.legacy_tasks_file and self._tasks:
            self._save()

    def _save(self) -> None:
        """Persist the local task mirror atomically."""

        payload = {"version": 1, "tasks": [task.to_dict() for task in self._tasks.values()]}
        tmp_file = self.tasks_file.with_suffix(".tmp")
        with tmp_file.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        tmp_file.replace(self.tasks_file)

    def __iter__(self) -> Iterable[TaskRecord]:
        """Allow iteration over task records."""

        return iter(self._tasks.values())
