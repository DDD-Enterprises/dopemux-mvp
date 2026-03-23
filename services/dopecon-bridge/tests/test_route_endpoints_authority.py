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
