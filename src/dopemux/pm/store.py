"""
PM task store contract and in-memory implementation.

Implements idempotent transitions and stale-write protection
per ADR-PM-001 invariants.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any

from .models import PMTask, PMTransitionRequest, PMLinkedIDUpdateRequest


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


class IdempotencyMismatchError(Exception):
    """Raised when an idempotency key is reused with a different payload."""

    def __init__(self, task_id: str, idempotency_key: str) -> None:
        super().__init__(f"Idempotency mismatch for task {task_id} with key {idempotency_key}")


class LinkedIDConflictError(Exception):
    """Raised when a linked ID update conflicts with an existing value."""

    def __init__(self, task_id: str, system: str, existing_id: str, new_id: str) -> None:
        super().__init__(
            f"Linked ID conflict for task {task_id} on system {system}: "
            f"existing {existing_id}, new {new_id}"
        )


class PMTaskStore(ABC):
    """Abstract base class for PM task persistence.

    All implementations must honor:
    - Create idempotency by task_id
    - Transition idempotency by (task_id, idempotency_key) with fail-closed payload mismatch checks
    - Stale write protection via expected_version
    - Monotonic version increments
    - Stable linked IDs: reject silent overwrites
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
            IdempotencyMismatchError: idempotency key reused with different payload.

        Idempotency: duplicate (task_id, idempotency_key) returns
        the previously produced result without mutation.
        """
        ...

    @abstractmethod
    def update_linked_ids(self, task_id: str, req: PMLinkedIDUpdateRequest) -> PMTask:
        """Update linked IDs for a task.
        
        Raises:
            TaskNotFoundError: task_id does not exist.
            StaleWriteError: expected_version mismatch.
            LinkedIDConflictError: attempts to silently overwrite an existing linked ID.
            IdempotencyMismatchError: idempotency key reused with different payload.
        """
        ...


class InMemoryPMTaskStore(PMTaskStore):
    """In-memory PM task store for testing and bootstrapping.

    Not suitable for production persistence.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, PMTask] = {}
        # Maps (task_id, idempotency_key) -> (version that was produced, payload_hash)
        self._replay_log: Dict[Tuple[str, str], Tuple[int, int]] = {}

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

        req_hash = hash(f"transition:{req.new_status}:{req.reason}")

        # Idempotency check: if this (task_id, idempotency_key) was already
        # processed, return the current state without mutation, fail if payload differs.
        replay_key = (task_id, req.idempotency_key)
        if replay_key in self._replay_log:
            _, old_hash = self._replay_log[replay_key]
            if old_hash != req_hash:
                raise IdempotencyMismatchError(task_id, req.idempotency_key)
            return task.model_copy()

        # Stale write check
        if req.expected_version != task.version:
            raise StaleWriteError(task_id, req.expected_version, task.version)

        # Apply transition
        task.status = req.new_status
        task.version += 1
        task.updated_at_utc = req.ts_utc

        # Record replay key
        self._replay_log[replay_key] = (task.version, req_hash)

        return task.model_copy()

    def update_linked_ids(self, task_id: str, req: PMLinkedIDUpdateRequest) -> PMTask:
        """Update linked IDs with idempotency and overwrite protection."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        # Serialize dict for basic payload hash
        req_hash = hash("linked_ids:" + str(sorted(req.linked_ids.items())))

        replay_key = (task_id, req.idempotency_key)
        if replay_key in self._replay_log:
            _, old_hash = self._replay_log[replay_key]
            if old_hash != req_hash:
                raise IdempotencyMismatchError(task_id, req.idempotency_key)
            return task.model_copy()

        if req.expected_version != task.version:
            raise StaleWriteError(task_id, req.expected_version, task.version)

        # Validate linked IDs updates
        for system, new_id in req.linked_ids.items():
            if system in task.linked_ids:
                existing_id = task.linked_ids[system]
                if existing_id != new_id:
                    raise LinkedIDConflictError(task_id, system, existing_id, new_id)

        # Apply update
        for system, new_id in req.linked_ids.items():
            task.linked_ids[system] = new_id

        task.version += 1
        task.updated_at_utc = req.ts_utc
        self._replay_log[replay_key] = (task.version, req_hash)
        
        return task.model_copy()
