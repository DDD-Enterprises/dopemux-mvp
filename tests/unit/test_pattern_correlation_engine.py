from __future__ import annotations

import importlib.util
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "intelligence"
    / "pattern_correlation_engine.py"
)


@pytest.fixture(scope="module")
def pattern_module():
    spec = importlib.util.spec_from_file_location("pattern_correlation_engine", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_recent_events_handles_mixed_timezone_timestamps(pattern_module):
    engine = pattern_module.PatternCorrelationEngine(window_minutes=30)
    now_aware = datetime.now(timezone.utc)

    event_queue = deque(
        [
            {"id": "aware", "timestamp": now_aware.isoformat()},
            {"id": "naive", "timestamp": now_aware.replace(tzinfo=None).isoformat()},
            {"id": "bad", "timestamp": "not-a-timestamp"},
        ],
        maxlen=10,
    )

    recent = engine._get_recent_events(event_queue, minutes=5)
    ids = {event["id"] for event in recent}

    assert "aware" in ids
    assert "naive" in ids
    assert "bad" not in ids


@pytest.mark.asyncio
async def test_detects_cognitive_code_mismatch(pattern_module):
    engine = pattern_module.PatternCorrelationEngine(window_minutes=30)
    now = datetime.now(timezone.utc).isoformat()

    complexity_event = {
        "id": "c1",
        "type": "code.complexity.updated",
        "timestamp": now,
        "data": {"complexity": 0.82, "file": "src/core/module.py"},
    }
    cognitive_event = {
        "id": "c2",
        "type": "cognitive.state.changed",
        "timestamp": now,
        "data": {"energy": "low"},
    }

    assert await engine.on_event(complexity_event) is None
    insight = await engine.on_event(cognitive_event)

    assert insight is not None
    assert insight.insight_type == pattern_module.IntelligenceType.COGNITIVE_CODE
    assert insight.priority == "critical"


@pytest.mark.asyncio
async def test_detects_context_switch_risk(pattern_module):
    engine = pattern_module.PatternCorrelationEngine(window_minutes=30)
    now = datetime.now(timezone.utc).isoformat()

    first = {
        "id": "w1",
        "type": "workspace.switch.changed",
        "timestamp": now,
        "data": {
            "workspace": "/repo/one",
            "uncommitted_files": ["src/a.py", "src/b.py"],
        },
    }
    second = {
        "id": "w2",
        "type": "workspace.switch.changed",
        "timestamp": now,
        "data": {"workspace": "/repo/two", "uncommitted_files": []},
    }

    assert await engine.on_event(first) is None
    insight = await engine.on_event(second)

    assert insight is not None
    assert insight.insight_type == pattern_module.IntelligenceType.CONTEXT_SWITCH
    assert "Context switch" in insight.title
