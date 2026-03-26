import pytest
from fastapi.testclient import TestClient
import sys

from dopecon_bridge.app import app

client = TestClient(app)

def test_parse_prd_requires_cognitive_plane():
    response = client.post("/tasks/parse-prd", json={"content": "test prd", "project_id": "1"})
    assert response.status_code == 403
    assert "cognitive_plane authority" in response.json()["detail"]

def test_get_next_tasks_enforces_plane():
    response = client.get("/tasks/next/project-123", headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]

def test_ddg_decisions_enforces_plane():
    response = client.get("/ddg/decisions", headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]

def test_ddg_search_enforces_plane():
    response = client.get("/ddg/search", params={"q": "test"}, headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]

def test_publish_event_canonicalizes_taskmaster_events(monkeypatch):
    captured = {}

    class DummyBus:
        async def initialize(self):
            return None

        async def publish(self, stream, event):
            captured["stream"] = stream
            captured["event"] = event
            return "1-0"

    monkeypatch.setattr("dopecon_bridge.event_bus.EventBus", DummyBus)

    response = client.post(
        "/events",
        json={
            "stream": "dopemux:events",
            "event_type": "taskmaster.task.created",
            "data": {
                "source_task_id": "tm-1",
                "title": "Canonical route event",
                "description": "Bridge route canonicalization",
                "ts_utc": "2026-03-26T12:00:00Z",
            },
            "source": "taskmaster",
        },
    )

    assert response.status_code == 200
    assert response.json()["event_type"] == "pm.task.created"
    assert captured["stream"] == "dopemux:events"
    assert captured["event"].type == "pm.task.created"
    assert captured["event"].data["event_type"] == "pm.task.created"
    assert captured["event"].data["idempotency_key"]
