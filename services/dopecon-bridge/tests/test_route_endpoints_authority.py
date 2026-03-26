import pytest
from fastapi.testclient import TestClient
import sys

from dopecon_bridge.app import app
from dopecon_bridge.services.task_integration import task_service

client = TestClient(app)

def test_parse_prd_requires_cognitive_plane():
    response = client.post("/tasks/parse-prd", json={"content": "test prd", "project_id": "1"})
    assert response.status_code == 403
    assert "cognitive_plane authority" in response.json()["detail"]

def test_get_next_tasks_enforces_plane():
    response = client.get("/tasks/next/project-123", headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_next_tasks_returns_canonical_queue_items(monkeypatch):
    async def _mock_queue(project_id):
        assert project_id == "project-123"
        return {
            "queue_items": [
                {"workflow_id": "epic_1", "title": "First"},
                {"workflow_id": "epic_2", "title": "Second"},
            ]
        }

    monkeypatch.setattr(task_service, "get_priority_queue", _mock_queue)
    response = client.get("/tasks/next/project-123?limit=1", headers={"X-Source-Plane": "pm_plane"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["tasks"] == [{"workflow_id": "epic_1", "title": "First"}]

def test_ddg_decisions_enforces_plane():
    response = client.get("/ddg/decisions", headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]

def test_ddg_search_enforces_plane():
    response = client.get("/ddg/search", params={"q": "test"}, headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]
