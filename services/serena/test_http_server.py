from pathlib import Path
import sys
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.http_server import app  # noqa: E402


client = TestClient(app)


class TestSerenaHttpServer:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "serena"
        assert "aggregator" in data

    @patch("services.serena.http_server.aggregator", new_callable=Mock)
    def test_get_metrics(self, mock_agg):
        mock_agg.aggregate_detections.return_value = {
            "total_detections": 10,
            "f1_f4_metrics": {"pass_rate": 0.9, "avg_confidence": 0.85},
            "adhd_insight": {"cognitive_load": "low"},
        }
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data

    def test_get_metrics_mock_fallback(self):
        with patch("services.serena.http_server.AGGREGATOR_AVAILABLE", False):
            response = client.get("/api/metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["source"] == "mock"

    def test_detections_summary_limit(self):
        response = client.get("/api/detections/summary?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["top_patterns"]) <= 3

    def test_pattern_detail_endpoint_returns_known_pattern(self):
        response = client.get("/api/patterns/top?limit=1")
        assert response.status_code == 200
        top_pattern = response.json()["patterns"][0]

        detail_response = client.get(f"/api/patterns/{top_pattern['id']}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == top_pattern["id"]
        assert "success_rate" in detail

    def test_top_patterns_adhd_limit(self):
        response = client.get("/api/patterns/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) <= 5
        assert "adhd_friendly" in data

    @pytest.mark.parametrize("limit", [1, 3, 5, 10])
    def test_limit_parameter_validation(self, limit):
        response = client.get(f"/api/detections/summary?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("top_patterns", [])) <= limit
