from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "ui-dashboard-backend" / "app.py"
)


@pytest.fixture(scope="module")
def dashboard_backend_module():
    spec = importlib.util.spec_from_file_location("ui_dashboard_backend_app", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def client(dashboard_backend_module):
    return TestClient(dashboard_backend_module.app)


def test_health_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "Ultra UI Dashboard Backend"
    assert "timestamp" in payload
    assert "integrations" in payload


def test_cognitive_state_fallback_shape(client, dashboard_backend_module, monkeypatch):
    async def _fallback(*args, **kwargs):
        return None

    monkeypatch.setattr(dashboard_backend_module, "_load_live_cognitive_state", _fallback)

    response = client.get("/api/cognitive-state?user_id=hue")
    assert response.status_code == 200

    payload = response.json()
    assert payload["source"] == "fallback"
    assert "sampled_at" in payload

    state = payload["cognitive_state"]
    assert 0.0 <= state["energy"] <= 1.0
    assert 0.0 <= state["attention"] <= 1.0
    assert 0.0 <= state["load"] <= 1.0
    assert state["status"] in {"low", "optimal", "high", "critical"}


def test_cognitive_state_live_source(client, dashboard_backend_module, monkeypatch):
    live_state = dashboard_backend_module.CognitiveState(
        energy=0.82,
        attention=0.79,
        load=0.31,
        status="optimal",
        recommendation="Continue focused execution.",
        prediction=0.27,
    )

    async def _live(*args, **kwargs):
        return live_state

    monkeypatch.setattr(dashboard_backend_module, "_load_live_cognitive_state", _live)

    response = client.get("/api/cognitive-state")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "adhd-engine"
    assert payload["cognitive_state"]["prediction"] == 0.27


def test_tasks_fallback_contract(client, dashboard_backend_module, monkeypatch):
    async def _fallback(*args, **kwargs):
        return None

    monkeypatch.setattr(dashboard_backend_module, "_load_live_tasks", _fallback)

    response = client.get("/api/tasks?limit=2")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2
    assert tasks[0]["id"] == "task-1"
    assert tasks[0]["status"] in {"pending", "in_progress", "completed"}


def test_dashboard_snapshot_contract(client, dashboard_backend_module, monkeypatch):
    async def _fallback_state(*args, **kwargs):
        return None

    async def _fallback_tasks(*args, **kwargs):
        return None

    monkeypatch.setattr(dashboard_backend_module, "_load_live_cognitive_state", _fallback_state)
    monkeypatch.setattr(dashboard_backend_module, "_load_live_tasks", _fallback_tasks)

    response = client.get("/api/dashboard?user_id=hue&limit=3")
    assert response.status_code == 200
    payload = response.json()

    assert "cognitive_state" in payload
    assert "team_members" in payload
    assert "tasks" in payload
    assert "sources" in payload
    assert payload["sources"]["cognitive_state"] == "fallback"
    assert len(payload["tasks"]) == 3
