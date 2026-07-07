"""Tests for ConPort's direct chronicle emit envelope (corrected P0 fix).

The bridge HTTP publish path is dead (401, empty user store), so ConPort emits
decision.logged straight to the dope-memory input stream. This validates the
envelope shape + the summary->title mapping the promotion handler requires.
"""

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docker"
    / "mcp-servers-source"
    / "conport"
    / "integration_bridge_client.py"
)

if str(MODULE_PATH.parent) not in sys.path:
    sys.path.insert(0, str(MODULE_PATH.parent))

SPEC = importlib.util.spec_from_file_location("conport_bridge_client_for_tests", MODULE_PATH)
BC = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BC)


def test_envelope_shape_matches_capture_contract():
    env = BC.build_chronicle_envelope(
        event_type="decision.logged",
        data={"decision_id": "d1", "title": "Pick X", "rationale": "because"},
        workspace_id="/ws/repo",
        instance_id="B",
        session_id="s1",
    )
    # Top-level identity fields the dope-memory consumer reads directly.
    assert env["type"] == "decision.logged"
    assert env["workspace_id"] == "/ws/repo"
    assert env["instance_id"] == "B"
    assert env["session_id"] == "s1"
    assert env["source"] == "conport"
    assert env["id"] and env["ts"]
    # data is a JSON string (consumer json.loads it).
    payload = json.loads(env["data"])
    assert payload["title"] == "Pick X"


def test_envelope_defaults_when_identity_absent():
    env = BC.build_chronicle_envelope(
        event_type="decision.logged",
        data={"decision_id": "d1", "title": "t"},
        workspace_id=None,
    )
    assert env["workspace_id"] == "default"
    assert env["instance_id"] == "A"
    assert env["session_id"] == ""


def test_stream_and_redis_url_defaults():
    # Chronicle must target the events Redis + input stream dope-memory reads.
    assert BC.CHRONICLE_STREAM == "activity.events.v1"
    assert "redis-events" in BC.CHRONICLE_REDIS_URL


async def test_emit_maps_summary_to_title_and_is_fail_open():
    """emit_decision_to_chronicle maps ConPort 'summary' -> promotion 'title'
    and never raises when Redis is unavailable."""
    captured = {}

    class _FakeRedis:
        async def xadd(self, stream, envelope):
            captured["stream"] = stream
            captured["envelope"] = envelope
            return "1-0"

        async def aclose(self):
            pass

    class _FakeFactory:
        @staticmethod
        def from_url(*a, **k):
            return _FakeRedis()

    orig = BC._chronicle_redis
    BC._chronicle_redis = _FakeFactory
    try:
        ok = await BC.emit_decision_to_chronicle(
            decision_id="d9",
            summary="Adopt corrected fix",
            rationale="bridge auth dead",
            workspace_id="/ws",
            tags=["proof"],
        )
    finally:
        BC._chronicle_redis = orig

    assert ok is True
    assert captured["stream"] == "activity.events.v1"
    payload = json.loads(captured["envelope"]["data"])
    assert payload["title"] == "Adopt corrected fix"  # summary -> title
    assert payload["rationale"] == "bridge auth dead"


async def test_emit_skips_without_summary():
    ok = await BC.emit_decision_to_chronicle(
        decision_id="d0", summary=None, rationale="x", workspace_id="/ws"
    )
    assert ok is False
