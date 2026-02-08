from pathlib import Path
import sys

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.http_server import app  # noqa: E402


client = TestClient(app)


def test_health_endpoint_contract():
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "serena"
    assert "timestamp" in payload


def test_metrics_endpoint_returns_payload():
    response = client.get("/api/metrics")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, dict)
    assert "timestamp" in payload


def test_top_patterns_respects_limit():
    response = client.get("/api/patterns/top", params={"limit": 2})
    assert response.status_code == 200

    payload = response.json()
    assert "patterns" in payload
    assert len(payload["patterns"]) <= 2
