"""Tests for PM event adapter functions."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dopemux.pm.adapters import (
    canonical_task_id,
    orchestrator_event_to_pm,
    pm_to_bus_event,
    taskmaster_event_to_pm,
)


def test_taskmaster_mapping_created_status_updated_completed() -> None:
    base = {
        "task_id": "tm-100",
        "title": "Build parser",
        "description": "Implement parser",
        "status": "IN_PROGRESS",
        "ts_utc": "2026-02-12T19:00:00Z",
        "idempotency_key": "idem-tm",
    }

    created = taskmaster_event_to_pm("taskmaster.task.created", dict(base))
    status_updated = taskmaster_event_to_pm("taskmaster.task.status_updated", dict(base))
    completed = taskmaster_event_to_pm("taskmaster.task.completed", dict(base))

    assert created["event_type"] == "pm.task.created"
    assert status_updated["event_type"] == "pm.task.status_changed"
    assert completed["event_type"] == "pm.task.completed"


def test_orchestrator_mapping_created_updated_completed() -> None:
    created = orchestrator_event_to_pm({"event_type": "task_created", "task_id": "orch-1"})
    updated = orchestrator_event_to_pm({"type": "task_updated", "payload": {"task_id": "orch-2"}})
    completed = orchestrator_event_to_pm({"event_type": "task_completed", "data": {"task_id": "orch-3"}})

    assert created["event_type"] == "pm.task.created"
    assert updated["event_type"] == "pm.task.updated"
    assert completed["event_type"] == "pm.task.completed"


def test_unknown_orchestrator_event_gracefully_maps_to_updated_with_reason() -> None:
    event = orchestrator_event_to_pm(
        {
            "event_type": "task_paused_unknown",
            "task_id": "orch-4",
            "status": "paused",
        }
    )
    assert event["event_type"] == "pm.task.updated"
    assert event["payload"]["mapping_reason"] == "unknown_orchestrator_event_type"
    assert event["payload"]["dialect_event_type"] == "task_paused_unknown"
    assert event["payload"]["dialect_status"] == "paused"


def test_dialect_breadcrumbs_present_for_taskmaster_mapping() -> None:
    event = taskmaster_event_to_pm(
        "taskmaster.task.status_updated",
        {
            "task_id": "tm-333",
            "status": "BLOCKED",
            "title": "Write docs",
            "description": "Long form",
        },
    )
    assert event["payload"]["dialect_event_type"] == "taskmaster.task.status_updated"
    assert event["payload"]["dialect_status"] == "BLOCKED"


def test_task_id_policy_source_task_id_precedence_and_fallback_normalization() -> None:
    # Source task ID path should ignore timestamp drift.
    event_a = taskmaster_event_to_pm(
        "taskmaster.task.created",
        {
            "source_task_id": "tm-stable",
            "title": "Title A",
            "description": "Desc A",
            "created_at_utc": "2026-02-12T10:00:00Z",
        },
    )
    event_b = taskmaster_event_to_pm(
        "taskmaster.task.created",
        {
            "source_task_id": "tm-stable",
            "title": "Title A",
            "description": "Desc A",
            "created_at_utc": "2030-01-01T00:00:00Z",
        },
    )
    assert event_a["task_id"] == event_b["task_id"]

    # Fallback path uses normalized title + description.
    id_1 = canonical_task_id("taskmaster", None, "  Fix   Bug  ", "  In   Auth ")
    id_2 = canonical_task_id("taskmaster", None, "fix bug", "in auth")
    assert id_1 == id_2


def test_pm_to_bus_event_namespace_starts_with_pm() -> None:
    envelope = taskmaster_event_to_pm(
        "taskmaster.task.created",
        {"task_id": "tm-999", "title": "Task", "description": "Desc"},
    )
    bus_event = pm_to_bus_event(envelope)
    assert bus_event["namespace"].startswith("pm.")
    assert bus_event["payload"]["envelope"] == envelope


def test_pm_to_bus_event_rejects_non_pm_namespace() -> None:
    with pytest.raises(ValueError):
        pm_to_bus_event({"event_type": "task.created"})


def test_pm_modules_respect_trinity_boundary_imports() -> None:
    forbidden = ("services.", "dopemux.mcp", "dopemux.event_bus")
    bad: list[tuple[str, str]] = []

    for path in Path("src/dopemux/pm").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if any(token in module for token in forbidden):
                    bad.append((str(path), module))
            if isinstance(node, ast.Import):
                for name in node.names:
                    module = name.name
                    if any(token in module for token in forbidden):
                        bad.append((str(path), module))

    assert bad == []
