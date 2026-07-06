"""Tests for the dopecon-bridge promotable-event chronicle mirror.

The mirror copies promotable events (decision.logged, task.*, ...) from the
general bus stream onto the dope-memory input stream (activity.events.v1),
using a capture_client-compatible envelope.
"""

import importlib.util

import pytest
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "dopecon-bridge"
    / "dopecon_bridge"
    / "promotable_mirror.py"
)
MODULE_DIR = MODULE_PATH.parent

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

SPEC = importlib.util.spec_from_file_location("promotable_mirror_for_tests", MODULE_PATH)
MIRROR = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MIRROR)


class _FakeRedis:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = []

    async def xadd(self, stream, envelope):
        if self.fail:
            raise ConnectionError("redis down")
        self.calls.append((stream, envelope))
        return b"1-0"


def test_normalize_event_type():
    assert MIRROR.normalize_event_type("decision_logged") == "decision.logged"
    assert MIRROR.normalize_event_type("decision.logged") == "decision.logged"
    assert MIRROR.normalize_event_type("  Task_Completed ") == "task.completed"
    assert MIRROR.normalize_event_type("") == "unknown"
    assert MIRROR.normalize_event_type("work_untracked_detected") == "work.untracked.detected"


def test_envelope_promotable_underscore_type():
    envelope = MIRROR.build_mirror_envelope(
        "decision_logged",
        {"workspace_id": "/ws/repo", "summary": "picked X"},
        "conport",
    )
    assert envelope is not None
    assert envelope["type"] == "decision.logged"
    assert envelope["workspace_id"] == "/ws/repo"
    assert envelope["instance_id"] == "A"  # default when absent
    assert envelope["session_id"] == ""
    assert envelope["source"] == "conport"
    assert json.loads(envelope["data"])["summary"] == "picked X"


def test_envelope_non_promotable_returns_none():
    assert MIRROR.build_mirror_envelope("progress_updated", {}, "conport") is None
    assert MIRROR.build_mirror_envelope("session_started", {}, "bridge") is None



@pytest.mark.asyncio
async def test_mirror_writes_to_memory_stream():
    fake = _FakeRedis()
    written = await MIRROR.mirror_promotable_event(
        fake,
        stream="dopemux:events",
        event_type="decision.logged",
        data={"workspace_id": "/ws/repo", "instance_id": "B", "session_id": "s1"},
        source="conport",
    )
    assert written is True
    assert len(fake.calls) == 1
    stream, envelope = fake.calls[0]
    assert stream == MIRROR.MEMORY_INPUT_STREAM
    assert envelope["instance_id"] == "B"
    assert envelope["session_id"] == "s1"



@pytest.mark.asyncio
async def test_mirror_skips_when_already_on_memory_stream():
    fake = _FakeRedis()
    written = await MIRROR.mirror_promotable_event(
        fake,
        stream=MIRROR.MEMORY_INPUT_STREAM,
        event_type="decision.logged",
        data={"workspace_id": "/ws"},
        source="conport",
    )
    assert written is False
    assert fake.calls == []



@pytest.mark.asyncio
async def test_mirror_skips_non_promotable():
    fake = _FakeRedis()
    written = await MIRROR.mirror_promotable_event(
        fake,
        stream="dopemux:events",
        event_type="progress_updated",
        data={"workspace_id": "/ws"},
        source="conport",
    )
    assert written is False
    assert fake.calls == []



@pytest.mark.asyncio
async def test_mirror_never_raises_on_redis_failure():
    fake = _FakeRedis(fail=True)
    written = await MIRROR.mirror_promotable_event(
        fake,
        stream="dopemux:events",
        event_type="decision.logged",
        data={"workspace_id": "/ws"},
        source="conport",
    )
    assert written is False


def test_new_contract_types_are_promotable():
    """Phase 1.1 extension types mirror correctly."""
    for event_type in (
        "task.created",
        "blocker.cleared",
        "work.untracked_detected",
        "work.untracked_converted",
    ):
        envelope = MIRROR.build_mirror_envelope(
            event_type, {"workspace_id": "/ws"}, "test"
        )
        assert envelope is not None, event_type
        assert envelope["type"] == event_type
