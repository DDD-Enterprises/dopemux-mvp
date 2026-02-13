"""Tests for canonical PM event envelope utilities."""

from datetime import datetime, timedelta, timezone

from dopemux.pm.events import (
    PM_EVENT_TYPES,
    PMEventType,
    canonical_json,
    create_pm_event,
)


EXPECTED_PM_EVENT_TYPES = [
    "pm.task.created",
    "pm.task.updated",
    "pm.task.status_changed",
    "pm.task.blocked",
    "pm.task.completed",
    "pm.decision.linked",
    "pm.sync.requested",
    "pm.sync.succeeded",
    "pm.sync.failed",
]


def test_pm_event_types_exactly_expected_values() -> None:
    assert PM_EVENT_TYPES == EXPECTED_PM_EVENT_TYPES
    assert [item.value for item in PMEventType] == EXPECTED_PM_EVENT_TYPES
    assert len(PM_EVENT_TYPES) == 9


def test_canonical_json_is_stable_for_dict_key_order() -> None:
    obj_a = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
    obj_b = {"nested": {"y": 8, "z": 9}, "a": 1, "b": 2}
    assert canonical_json(obj_a) == canonical_json(obj_b)


def test_create_pm_event_is_deterministic_for_same_inputs() -> None:
    args = {
        "event_type": PMEventType.TASK_CREATED.value,
        "ts_utc": datetime(2026, 2, 12, 18, 30, tzinfo=timezone.utc),
        "idempotency_key": "idem-001",
        "source": "taskmaster",
        "task_id": "task-123",
        "payload": {"x": 1, "y": [3, 2, 1]},
    }
    event_1 = create_pm_event(**args)
    event_2 = create_pm_event(**args)
    assert event_1["event_id"] == event_2["event_id"]


def test_event_id_changes_when_payload_changes() -> None:
    common = {
        "event_type": PMEventType.TASK_UPDATED.value,
        "ts_utc": "2026-02-12T18:30:00Z",
        "idempotency_key": "idem-002",
        "source": "taskmaster",
        "task_id": "task-123",
    }
    event_1 = create_pm_event(payload={"status": "a"}, **common)
    event_2 = create_pm_event(payload={"status": "b"}, **common)
    assert event_1["event_id"] != event_2["event_id"]


def test_datetime_is_normalized_to_utc_with_z_suffix() -> None:
    offset = timezone(timedelta(hours=-5))
    dt = datetime(2026, 2, 12, 13, 0, 0, tzinfo=offset)

    serialized = canonical_json({"ts_utc": dt})
    assert '"ts_utc":"2026-02-12T18:00:00Z"' in serialized

    event = create_pm_event(
        event_type=PMEventType.TASK_COMPLETED.value,
        ts_utc=dt,
        idempotency_key="idem-003",
        source="taskmaster",
        task_id="task-xyz",
        payload={},
    )
    assert event["ts_utc"].endswith("Z")
