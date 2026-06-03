import asyncio

from fastapi.testclient import TestClient

import backend


async def _idle_reader(*_args, **_kwargs):
    await asyncio.Event().wait()


def test_synthetic_state_update_reaches_ws_state(monkeypatch):
    monkeypatch.setattr(backend, "redis_pubsub_reader", _idle_reader)
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

    backend.manager.active_connections.clear()
    try:
        with TestClient(backend.app) as client:
            with client.websocket_connect("/ws/state") as websocket:
                client.portal.call(backend.manager.broadcast, payload)

                assert websocket.receive_json() == payload
    finally:
        backend.manager.active_connections.clear()
