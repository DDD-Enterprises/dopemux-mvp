"""Tests for PM event adapter functions."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dopemux.pm.adapters import (
    orchestrator_event_to_pm,
    pm_to_bus_event,
)
from dopemux.pm.models import content_hash_task_id


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


def test_dialect_breadcrumbs_present_for_orchestrator_mapping() -> None:
    event = orchestrator_event_to_pm(
        {
            "event_type": "task_updated",
            "task_id": "orch-333",
            "status": "blocked",
            "title": "Write docs",
            "description": "Long form",
        },
    )
    assert event["payload"]["dialect_event_type"] == "task_updated"
    assert event["payload"]["dialect_status"] == "blocked"


def test_task_id_matches_packet_a_policy() -> None:
    event = orchestrator_event_to_pm(
        {"task_id": "orch-stable", "title": "A", "description": "B"},
    )
    assert event["task_id"] == content_hash_task_id("task-orchestrator", "orch-stable", "A", "B")


def test_empty_string_source_task_id_is_treated_as_present_per_packet_a() -> None:
    event = orchestrator_event_to_pm(
        {"task_id": "", "title": "T", "description": "D"},
    )
    assert event["task_id"] == content_hash_task_id("task-orchestrator", "", "T", "D")


def test_task_id_fallback_matches_packet_a_policy() -> None:
    event = orchestrator_event_to_pm(
        {
            "title": "  Fix   Bug  ",
            "description": "  In   Auth ",
        },
    )
    assert event["task_id"] == content_hash_task_id(
        "task-orchestrator",
        None,
        "  Fix   Bug  ",
        "  In   Auth ",
    )


def test_source_task_id_path_ignores_created_at_drift() -> None:
    event_a = orchestrator_event_to_pm(
        {
            "task_id": "orch-stable",
            "title": "Title A",
            "description": "Desc A",
            "created_at_utc": "2026-02-12T10:00:00Z",
        },
    )
    event_b = orchestrator_event_to_pm(
        {
            "task_id": "orch-stable",
            "title": "Title A",
            "description": "Desc A",
            "created_at_utc": "2030-01-01T00:00:00Z",
        },
    )
    assert event_a["task_id"] == event_b["task_id"]


def test_pm_to_bus_event_namespace_starts_with_pm() -> None:
    envelope = orchestrator_event_to_pm(
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
