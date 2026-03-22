from pathlib import Path
import sys

from fastapi.testclient import TestClient


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from task_orchestrator.app import app


def test_decompose_route_exists_with_validation_error():
    client = TestClient(app)
    response = client.post("/api/decompose", json={})
    assert response.status_code == 422


def test_health_route_available():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
