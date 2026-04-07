import pytest
from fastapi.testclient import TestClient
import sys

from dopecon_bridge.app import app
from dopecon_bridge.services.task_integration import task_service
def test_ddg_decisions_enforces_plane():
    response = client.get("/ddg/decisions", headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]

def test_ddg_search_enforces_plane():
    response = client.get("/ddg/search", params={"q": "test"}, headers={"X-Source-Plane": "invalid_plane"})
    assert response.status_code == 403
    assert "Invalid source plane" in response.json()["detail"]
