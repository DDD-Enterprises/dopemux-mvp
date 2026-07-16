import asyncio
import json
import threading
from datetime import datetime

from fastapi.testclient import TestClient

import backend


async def _idle_reader(*_args, **_kwargs):
    await asyncio.Event().wait()


class _FakePubSub:
    def __init__(self, payload, gate):
        self._payload = payload
        self._gate = gate

    async def psubscribe(self, *_args, **_kwargs):
        return None

    async def listen(self):
        await asyncio.to_thread(self._gate.wait)
        yield {"type": "pmessage", "data": json.dumps(self._payload)}

    async def unpsubscribe(self, *_args, **_kwargs):
        return None

    async def close(self):
        return None


class _FakeRedisClient:
    def __init__(self, payload, gate):
        self._payload = payload
        self._gate = gate

    def pubsub(self):
        return _FakePubSub(self._payload, self._gate)

    async def close(self):
        return None


class _FailingSession:
    def get(self, _url):
        raise OSError("upstream offline")


def test_synthetic_state_update_reaches_ws_state(monkeypatch):
    release_reader = threading.Event()
    monkeypatch.setattr(backend, "redis_stream_reader", _idle_reader)

    payload = {
        "type": "state_update",
        "data": {
            "energy_level": "low",
            "attention_state": "scattered",
            "cognitive_load": 0.84,
            "predicted_load_15min": 0.91,
            "recommendation": "Pause and take a recovery break.",
        },
    }

    monkeypatch.setattr(backend, "redis_client", _FakeRedisClient(payload, release_reader))
    backend.manager.active_connections.clear()
    try:
        with TestClient(backend.app) as client:
            with client.websocket_connect("/ws/state") as websocket:
                release_reader.set()
                assert websocket.receive_json() == payload
    finally:
        backend.manager.active_connections.clear()


def test_health_payload_matches_registry_runtime_shape():
    payload = asyncio.run(backend.health_check())

    assert payload["status"] == "healthy"
    assert payload["service"] == "adhd-dashboard"
    assert datetime.fromisoformat(payload["ts"])


def test_upstream_failure_returns_error_payload():
    payload = asyncio.run(
        backend._get_json(_FailingSession(), "http://adhd-engine:8095/health")
    )

    assert payload == {"error": "upstream offline"}


def test_state_change_pattern_matches_engine_prefix_contract():
    assert (
        backend._state_changes_pattern("worktree-a")
        == "worktree-a:adhd:state_changes:*"
    )
    assert backend._state_changes_pattern("") == "adhd:state_changes:*"
    assert backend._state_changes_pattern("worktree-a:") == (
        "worktree-a:adhd:state_changes:*"
    )
