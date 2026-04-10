from pathlib import Path
import sys

from fastapi.testclient import TestClient


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app

def test_health_endpoint():
    # Use context manager to trigger lifespan events (FastAPI 0.93+)
    with TestClient(app) as client:
        # The health endpoint in app.main is /health
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "task-orchestrator"
        # In testing without real Redis, it should still report ok/pass if handled gracefully
        assert data["status"] in ("ok", "pass")

def test_decompose_route_missing():
    """Verify that decompose route is currently missing (migration in progress)"""
    with TestClient(app) as client:
        response = client.post("/api/decompose", json={})
        # This confirms it's not currently implemented in app.main
        assert response.status_code == 404


def test_project_workflow_state_route_available():
    """Verify the canonical runtime mounts the project workflow state route."""
    with TestClient(app) as client:
        response = client.get("/api/projects/1/workflow/state")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "1"
