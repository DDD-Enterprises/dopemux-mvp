from pathlib import Path
import sys

from fastapi.testclient import TestClient


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app

def test_health_route_available():
    client = TestClient(app)
    # The health endpoint in app.main is /health
    response = client.get("/health")
    assert response.status_code == 200
