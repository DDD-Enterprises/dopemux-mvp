"""Tests for PM task store contract and InMemoryPMTaskStore."""

from datetime import datetime, timezone, timedelta

import pytest

from dopemux.pm.models import PMTask, PMTaskStatus, PMTransitionRequest
from dopemux.pm.store import InMemoryPMTaskStore, StaleWriteError, TaskNotFoundError


@pytest.fixture
def store():
    return InMemoryPMTaskStore()


@pytest.fixture
def sample_task():
    now = datetime.now(timezone.utc)
    return PMTask(
        task_id="task-001",
        title="Test task",
        description="A test task",
        source="test",
        created_at_utc=now,
        updated_at_utc=now,
        version=1,
    )


class TestCreate:
    """create() is idempotent by task_id."""

    def test_create_returns_task(self, store, sample_task):
        result = store.create(sample_task)
        assert result.task_id == "task-001"
        assert result.title == "Test task"

    def test_create_idempotent_by_task_id(self, store, sample_task):
        """Creating same task_id twice returns original without mutation."""
        result1 = store.create(sample_task)

        modified = sample_task.model_copy()
        modified.title = "Modified title"
        modified.task_id = "task-001"  # same ID
        result2 = store.create(modified)

        assert result2.title == "Test task"  # original, not modified
        assert result2.version == result1.version

    def test_create_returns_copy(self, store, sample_task):
        """Returned task is a copy, not a reference."""
        result = store.create(sample_task)
        result.title = "mutated"
        stored = store.get("task-001")
        assert stored.title == "Test task"


class TestGet:
    """get() returns task or None."""

    def test_get_existing(self, store, sample_task):
        store.create(sample_task)
        result = store.get("task-001")
        assert result is not None
        assert result.task_id == "task-001"

    def test_get_nonexistent(self, store):
        assert store.get("does-not-exist") is None

    def test_get_returns_copy(self, store, sample_task):
        store.create(sample_task)
        result = store.get("task-001")
        result.title = "mutated"
        fresh = store.get("task-001")
        assert fresh.title == "Test task"


class TestTransition:
    """transition() with idempotency and stale-write protection."""

    def test_successful_transition(self, store, sample_task):
        store.create(sample_task)
        ts = datetime.now(timezone.utc)
        req = PMTransitionRequest(
            idempotency_key="tx-1",
            expected_version=1,
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=ts,
            source="test",
        )
        result = store.transition("task-001", req)
        assert result.status == PMTaskStatus.IN_PROGRESS
        assert result.version == 2
        assert result.updated_at_utc == ts

    def test_version_increments(self, store, sample_task):
        store.create(sample_task)
        ts = datetime.now(timezone.utc)

        req1 = PMTransitionRequest(
            idempotency_key="tx-1",
            expected_version=1,
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=ts,
            source="test",
        )
        result1 = store.transition("task-001", req1)
        assert result1.version == 2

        req2 = PMTransitionRequest(
            idempotency_key="tx-2",
            expected_version=2,
            new_status=PMTaskStatus.DONE,
            ts_utc=ts + timedelta(minutes=1),
            source="test",
        )
        result2 = store.transition("task-001", req2)
        assert result2.version == 3

    def test_idempotency_by_key(self, store, sample_task):
        """Duplicate (task_id, idempotency_key) returns prior state, no version bump."""
        store.create(sample_task)
        ts = datetime.now(timezone.utc)
        req = PMTransitionRequest(
            idempotency_key="tx-1",
            expected_version=1,
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=ts,
            source="test",
        )

        result1 = store.transition("task-001", req)
        assert result1.version == 2

        # Replay same idempotency key
        result2 = store.transition("task-001", req)
        assert result2.version == 2  # No additional bump
        assert result2.status == PMTaskStatus.IN_PROGRESS

    def test_stale_write_raises(self, store, sample_task):
        store.create(sample_task)
        req = PMTransitionRequest(
            idempotency_key="tx-1",
            expected_version=99,  # Wrong version
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=datetime.now(timezone.utc),
            source="test",
        )
        with pytest.raises(StaleWriteError) as exc_info:
            store.transition("task-001", req)
        assert exc_info.value.expected_version == 99
        assert exc_info.value.actual_version == 1

    def test_not_found_raises(self, store):
        req = PMTransitionRequest(
            idempotency_key="tx-1",
            expected_version=1,
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=datetime.now(timezone.utc),
            source="test",
        )
        with pytest.raises(TaskNotFoundError) as exc_info:
            store.transition("ghost", req)
        assert exc_info.value.task_id == "ghost"

    def test_updated_at_advances(self, store, sample_task):
        """updated_at_utc is set to req.ts_utc on successful transition."""
        store.create(sample_task)
        future = datetime(2030, 1, 1, tzinfo=timezone.utc)
        req = PMTransitionRequest(
            idempotency_key="tx-1",
            expected_version=1,
            new_status=PMTaskStatus.BLOCKED,
            ts_utc=future,
            source="test",
        )
        result = store.transition("task-001", req)
        assert result.updated_at_utc == future

    def test_transition_returns_copy(self, store, sample_task):
        """Returned task is a copy — mutations don't affect store."""
        store.create(sample_task)
        req = PMTransitionRequest(
            idempotency_key="tx-1",
            expected_version=1,
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=datetime.now(timezone.utc),
            source="test",
        )
        result = store.transition("task-001", req)
        result.title = "mutated"
        stored = store.get("task-001")
        assert stored.title == "Test task"
