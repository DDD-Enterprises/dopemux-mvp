"""
PM task store contract and in-memory implementation.

Implements idempotent transitions and stale-write protection
per ADR-PM-001 invariants.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from .models import PMTask, PMTransitionRequest


class TaskNotFoundError(Exception):
    """Raised when a task_id does not exist in the store."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class StaleWriteError(Exception):
    """Raised when expected_version does not match current version."""

    def __init__(self, task_id: str, expected: int, actual: int) -> None:
        self.task_id = task_id
        self.expected_version = expected
        self.actual_version = actual
        super().__init__(
            f"Stale write for task {task_id}: "
            f"expected version {expected}, actual {actual}"
        )


class PMTaskStore(ABC):
    """Abstract base class for PM task persistence.

    All implementations must honor:
    - Create idempotency by task_id
    - Transition idempotency by (task_id, idempotency_key)
    - Stale write protection via expected_version
    - Monotonic version increments
    """

    @abstractmethod
    def create(self, task: PMTask) -> PMTask:
        """Store a new task. If task_id already exists, return existing."""
        ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[PMTask]:
        """Retrieve a task by ID. Returns None if not found."""
        ...

    @abstractmethod
    def transition(self, task_id: str, req: PMTransitionRequest) -> PMTask:
        """Apply a status transition.

        Raises:
            TaskNotFoundError: task_id does not exist.
            StaleWriteError: expected_version mismatch.

        Idempotency: duplicate (task_id, idempotency_key) returns
        the previously produced result without mutation.
        """
        ...


class InMemoryPMTaskStore(PMTaskStore):
    """In-memory PM task store for testing and bootstrapping.

    Not suitable for production persistence.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, PMTask] = {}
        # Maps (task_id, idempotency_key) -> version that was produced
        self._replay_log: Dict[Tuple[str, str], int] = {}

    def create(self, task: PMTask) -> PMTask:
        """Store a new task. Idempotent by task_id."""
        if task.task_id in self._tasks:
            return self._tasks[task.task_id].model_copy()
        self._tasks[task.task_id] = task.model_copy()
        return self._tasks[task.task_id].model_copy()

    def get(self, task_id: str) -> Optional[PMTask]:
        """Retrieve task by ID."""
        task = self._tasks.get(task_id)
        if task is not None:
            return task.model_copy()
        return None

    def transition(self, task_id: str, req: PMTransitionRequest) -> PMTask:
        """Apply status transition with idempotency and stale-write protection."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        # Idempotency check: if this (task_id, idempotency_key) was already
        # processed, return the current state without mutation.
        replay_key = (task_id, req.idempotency_key)
        if replay_key in self._replay_log:
            return task.model_copy()

        # Stale write check
        if req.expected_version != task.version:
            raise StaleWriteError(task_id, req.expected_version, task.version)

        # Apply transition
        task.status = req.new_status
        task.version += 1
        task.updated_at_utc = req.ts_utc

        # Record replay key
        self._replay_log[replay_key] = task.version

        return task.model_copy()
