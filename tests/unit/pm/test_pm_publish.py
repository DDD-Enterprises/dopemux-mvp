"""Tests for PM publish bridge via EventBus."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dopemux.event_bus import InMemoryAdapter
from dopemux.pm.adapters import taskmaster_event_to_pm
from dopemux.pm_publish import pm_envelope_to_dopemux_event, publish_pm_envelope


def test_pm_envelope_to_dopemux_event_wraps_namespace_and_payload() -> None:
    envelope = taskmaster_event_to_pm(
        "taskmaster.task.created",
        {
            "source_task_id": "tm-200",
            "title": "Publish envelope",
            "description": "Bridge test",
            "ts_utc": "2026-02-12T20:00:00Z",
        },
    )

    event = pm_envelope_to_dopemux_event(envelope)

    assert event.envelope.namespace == envelope["event_type"]
    assert event.payload == {"envelope": envelope}


@pytest.mark.asyncio
async def test_publish_pm_envelope_emits_to_inmemory_bus_subscriber() -> None:
    bus = InMemoryAdapter()
    envelope = taskmaster_event_to_pm(
        "taskmaster.task.created",
        {
            "source_task_id": "tm-201",
            "title": "Publish to bus",
            "description": "In-memory subscriber",
            "ts_utc": "2026-02-12T20:01:00Z",
        },
    )

    received = []

    async def on_event(event):
        received.append(event)

    await bus.subscribe("pm.*", on_event)
    result = await publish_pm_envelope(envelope, bus)

    assert result is True
    assert len(received) == 1
    assert received[0].envelope.namespace == envelope["event_type"]
    assert received[0].payload == {"envelope": envelope}


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
