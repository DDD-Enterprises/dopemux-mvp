import asyncio
import json
import threading

from fastapi.testclient import TestClient

import backend


async def _idle_reader(*_args, **_kwargs):
    await asyncio.Event().wait()


class _FakePubSub:
    def __init__(self, payload, gate, channel="adhd:state_changes:default"):
        self._payload = payload
        self._gate = gate
        self._channel = channel
        self.subscribed_patterns = []

    async def psubscribe(self, *patterns, **_kwargs):
        self.subscribed_patterns.extend(patterns)
        return None

    async def listen(self):
        await asyncio.to_thread(self._gate.wait)
        yield {"type": "pmessage", "channel": self._channel, "data": json.dumps(self._payload)}

    async def unpsubscribe(self, *_args, **_kwargs):
        return None

    async def close(self):
        return None


class _FakeRedisClient:
    def __init__(self, payload, gate, channel="adhd:state_changes:default"):
        self._payload = payload
        self._gate = gate
        self._channel = channel
        self.last_pubsub = None

    def pubsub(self):
        self.last_pubsub = _FakePubSub(self._payload, self._gate, self._channel)
        return self.last_pubsub

    async def close(self):
        return None


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


def test_prefixed_synthetic_event_reaches_ws_state(monkeypatch):
    release_reader = threading.Event()
    monkeypatch.setattr(backend, "redis_stream_reader", _idle_reader)
    monkeypatch.setattr(backend, "ADHD_ENGINE_REDIS_PREFIX", "test-prefix")

    payload = {
        "type": "state_update",
        "data": {
            "energy_level": "high",
            "attention_state": "focused",
            "cognitive_load": 0.42,
            "recommendation": "Deep work session in progress.",
        },
    }

    fake_redis = _FakeRedisClient(payload, release_reader, channel="test-prefix:adhd:state_changes:default")
    monkeypatch.setattr(backend, "redis_client", fake_redis)
    backend.manager.active_connections.clear()

    try:
        with TestClient(backend.app) as client:
            with client.websocket_connect("/ws/state") as websocket:
                release_reader.set()
                assert websocket.receive_json() == payload
                assert "test-prefix:adhd:state_changes:*" in fake_redis.last_pubsub.subscribed_patterns
    finally:
        backend.manager.active_connections.clear()


def test_http_health_endpoint():
    with TestClient(backend.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "adhd-dashboard"
