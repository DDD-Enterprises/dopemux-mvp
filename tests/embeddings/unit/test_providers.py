"""Unit tests for the current Voyage embedding provider."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from dopemux.embeddings.core import AdvancedEmbeddingConfig
from dopemux.embeddings.providers import VoyageAPIClient


class TestVoyageAPIClient:
    """Test VoyageAPIClient functionality against the current httpx API."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = AdvancedEmbeddingConfig(
            embedding_model="voyage-context-3",
            rerank_model="voyage-rerank-2.5",
            embedding_dimension=2048,
            batch_size=16,
            request_timeout=30.0,
        )
        config.voyage_api_key = "test-key"
        config.api_base_url = "https://api.voyageai.com/v1"
        return config

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return VoyageAPIClient(config)

    @staticmethod
    def _mock_response(payload, *, raise_error=None):
        response = MagicMock()
        response.json.return_value = payload
        response.raise_for_status = MagicMock()
        if raise_error is not None:
            response.raise_for_status.side_effect = raise_error
        return response

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = VoyageAPIClient(config)

        assert client.config == config
        assert client.api_key == "test-key"
        assert client.config.api_base_url == "https://api.voyageai.com/v1"
        assert client.get_embedding_dimension() == 2048
        assert client.total_requests == 0

    def test_client_initialization_with_custom_url(self, config):
        """Test client initialization with custom base URL."""
        config.api_base_url = "https://custom.api.com/v1"
        client = VoyageAPIClient(config)

        assert client.config.api_base_url == "https://custom.api.com/v1"

    @pytest.mark.asyncio
    async def test_context_manager_protocol(self, client):
        """Test async context manager protocol."""
        client.client = AsyncMock()
        client.client.aclose = AsyncMock()

        async with client as ctx:
            assert ctx is client

        client.client.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_embed_texts_single_text(self, client):
        """Test embedding a single text."""
        client.client.post = AsyncMock(
            return_value=self._mock_response(
                {
                    "data": [{"embedding": [0.1] * 2048, "index": 0}],
                    "usage": {"total_tokens": 10},
                }
            )
        )

        embeddings = await client.embed_texts(["Hello world"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 2048
        assert embeddings[0][0] == 0.1
        assert client.total_tokens == 10
        assert client.embedding_requests == 1

    @pytest.mark.asyncio
    async def test_embed_texts_multiple_texts(self, client):
        """Test embedding multiple texts."""
        client.client.post = AsyncMock(
            return_value=self._mock_response(
                {
                    "data": [
                        {"embedding": [0.1] * 2048, "index": 0},
                        {"embedding": [0.2] * 2048, "index": 1},
                        {"embedding": [0.3] * 2048, "index": 2},
                    ],
                    "usage": {"total_tokens": 30},
                }
            )
        )

        embeddings = await client.embed_texts(["First", "Second", "Third"])

        assert len(embeddings) == 3
        assert all(len(embedding) == 2048 for embedding in embeddings)
        assert embeddings[2][0] == 0.3
        assert client.total_requests == 1

    @pytest.mark.asyncio
    async def test_embed_texts_api_error(self, client):
        """Test handling of API errors."""
        request = httpx.Request("POST", f"{client.config.api_base_url}/embeddings")
        response = httpx.Response(400, request=request)
        error = httpx.HTTPStatusError("bad request", request=request, response=response)
        client.client.post = AsyncMock(
            return_value=self._mock_response({"error": {"message": "Invalid input"}}, raise_error=error)
        )

        with pytest.raises(Exception) as exc_info:
            await client.embed_texts(["Invalid text"])

        assert "Voyage API request failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_texts_network_error(self, client):
        """Test handling of network errors."""
        client.client.post = AsyncMock(
            side_effect=httpx.ConnectError("Network error", request=httpx.Request("POST", "https://example.com"))
        )

        with pytest.raises(Exception) as exc_info:
            await client.embed_texts(["Test text"])

        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_texts_timeout(self, client):
        """Test handling of request timeouts."""
        client.client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))

        with pytest.raises(Exception) as exc_info:
            await client.embed_texts(["Test text"])

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rerank_documents(self, client):
        """Test reranking documents."""
        client.client.post = AsyncMock(
            return_value=self._mock_response(
                {
                    "results": [
                        {"relevance_score": 0.9},
                        {"relevance_score": 0.7},
                        {"relevance_score": 0.4},
                    ]
                }
            )
        )

        scores = await client.rerank("query", ["doc1", "doc2", "doc3"])

        assert scores == [0.9, 0.7, 0.4]
        assert client.rerank_requests == 1

    @pytest.mark.asyncio
    async def test_validate_connection(self, client):
        """Test connection validation."""
        client.client.post = AsyncMock(
            return_value=self._mock_response(
                {
                    "data": [{"embedding": [0.1] * 2048, "index": 0}],
                    "usage": {"total_tokens": 1},
                }
            )
        )

        assert await client.validate_connection() is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, client):
        """Test connection validation failure."""
        client.client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed", request=httpx.Request("POST", "https://example.com"))
        )

        assert await client.validate_connection() is False

    @pytest.mark.asyncio
    async def test_get_health_metrics(self, client):
        """Test health metrics shape."""
        client.total_requests = 3
        client.total_tokens = 42
        client.embedding_requests = 2
        client.rerank_requests = 1

        metrics = await client.get_health_metrics()

        assert isinstance(metrics, SimpleNamespace)
        assert metrics.provider_name == "voyage"
        assert metrics.total_requests == 3
        assert metrics.total_tokens == 42

    def test_usage_tracking_helpers(self, client):
        """Test usage tracking helper methods."""
        client.total_tokens = 100
        client.total_requests = 4
        client.embedding_requests = 3
        client.rerank_requests = 1

        stats = client.get_usage_stats()
        cost = client.get_cost_estimate()

        assert stats["total_tokens"] == 100
        assert stats["total_requests"] == 4
        assert cost["total_cost"] >= 0

        client.reset_usage_tracking()
        assert client.get_usage_stats()["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_missing_api_key_raises(self, config):
        """Test missing API key handling."""
        config.voyage_api_key = None
        client = VoyageAPIClient(config)

        with pytest.raises(Exception) as exc_info:
            await client.embed_texts(["Test text"])

        assert "failed" in str(exc_info.value).lower()
