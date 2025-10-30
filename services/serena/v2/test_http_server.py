import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add v2 to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from http_server import app  # Assuming the server module
from metrics_dashboard import MetricsAggregator

client = TestClient(app)

class TestSerenaHttpServer:
    @pytest.fixture
    def mock_aggregator(self):
        mock = Mock(spec=MetricsAggregator)
        mock.aggregate_detections.return_value = {
            "total_detections": 5,
            "f1_f4_metrics": {"pass_rate": 0.8, "avg_confidence": 0.75},
            "f5_metrics": {"boost_rate": 0.6},
            "f6_metrics": {"total_abandoned": 0}
        }
        return mock

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "aggregator" in data  # Should be "available" or "mock_mode"

    @patch("http_server.aggregator", new_callable=Mock)
    def test_get_metrics(self, mock_agg):
        mock_agg.aggregate_detections.return_value = {
            "total_detections": 10,
            "f1_f4_metrics": {"pass_rate": 0.9, "avg_confidence": 0.85},
            "adhd_insight": {"cognitive_load": "low"}
        }
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_detections"] == 10
        assert "adhd_insight" in data
        assert data["adhd_insight"]["cognitive_load"] == "low"

    def test_get_metrics_mock_fallback(self):
        # Test fallback to mocks when aggregator fails
        with patch("http_server.AGGREGATOR_AVAILABLE", False):
            response = client.get("/api/metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["source"] == "mock"  # From MOCK_METRICS

    def test_detections_summary_limit(self):
        response = client.get("/api/detections/summary?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["top_patterns"]) <= 3  # ADHD limit enforcement

    @pytest.mark.asyncio
    async def test_mcp_find_symbol_endpoint(self):
        # Mock LSP integration
        mock_lsp_result = {
            "symbols": [{"name": "test_func", "uri": "file:///test.py", "range": {}}],
            "cached": True
        }
        with patch("http_server.enhanced_lsp") as mock_lsp:  # Assume import
            mock_lsp.find_symbols.return_value = mock_lsp_result

        response = client.post("/mcp/find_symbol", json={"query": "test", "file_path": "/test.py"})
        assert response.status_code == 200
        data = response.json()
        assert "symbols" in data
        assert data["cached"] == True  # From mock

    def test_top_patterns_adhd_limit(self):
        response = client.get("/api/patterns/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) <= 5  # Enforces cognitive load limit
        assert "adhd_friendly" in data  # ADHD metadata

    @pytest.mark.parametrize("limit", [1, 3, 5, 10])  # Test ADHD limits
    def test_limit_parameter_validation(self, limit):
        response = client.get(f"/api/detections/summary?limit={limit}")
        assert response.status_code == 200  # Accepts 1-10
        if limit > 10:
            # Should still work but cap internally
            data = response.json()
            assert len(data.get("top_patterns", [])) <= 5  # Hard ADHD cap

# Run with: pytest services/serena/v2/test_http_server.py -v
