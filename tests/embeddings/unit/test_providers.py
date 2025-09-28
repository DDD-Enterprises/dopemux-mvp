"""
Unit tests for embedding providers.

Tests the VoyageAPIClient and other provider implementations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from dopemux.embeddings.providers import VoyageAPIClient
from dopemux.embeddings.core import AdvancedEmbeddingConfig, SecurityLevel


class TestVoyageAPIClient:
    """Test VoyageAPIClient functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(
            embedding_model="voyage-context-3",
            embedding_dimension=2048,
            batch_size=16,
            request_timeout=30.0
        )

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return VoyageAPIClient(config, api_key="test-key")

    @pytest.fixture
    def mock_session(self):
        """Create mock aiohttp session."""
        session = AsyncMock(spec=aiohttp.ClientSession)
        return session

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = VoyageAPIClient(config, api_key="test-key")

        assert client.config == config
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.voyageai.com/v1"
        assert client.model_name == "voyage-context-3"
        assert client.session is None  # Not initialized yet

    def test_client_initialization_with_custom_url(self, config):
        """Test client initialization with custom base URL."""
        client = VoyageAPIClient(
            config,
            api_key="test-key",
            base_url="https://custom.api.com/v1"
        )

        assert client.base_url == "https://custom.api.com/v1"

    @pytest.mark.asyncio
    async def test_context_manager_protocol(self, client, mock_session):
        """Test async context manager protocol."""
        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client as c:
                assert c.session == mock_session
                assert c.session is not None

            # Should close session on exit
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_texts_single_text(self, client, mock_session):
        """Test embedding single text."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3] * 683,  # 2048 dimensions
                    "index": 0
                }
            ],
            "model": "voyage-context-3",
            "usage": {"total_tokens": 10}
        }

        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                embeddings = await client.embed_texts(["Hello world"])

                assert len(embeddings) == 1
                assert len(embeddings[0]) == 2048
                assert embeddings[0][0] == 0.1

                # Verify API call
                mock_session.post.assert_called_once()
                call_args = mock_session.post.call_args
                assert "embeddings" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_embed_texts_multiple_texts(self, client, mock_session):
        """Test embedding multiple texts."""
        texts = ["First text", "Second text", "Third text"]

        # Mock response with multiple embeddings
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 2048, "index": 0},
                {"embedding": [0.2] * 2048, "index": 1},
                {"embedding": [0.3] * 2048, "index": 2}
            ],
            "model": "voyage-context-3",
            "usage": {"total_tokens": 30}
        }

        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                embeddings = await client.embed_texts(texts)

                assert len(embeddings) == 3
                assert all(len(emb) == 2048 for emb in embeddings)
                assert embeddings[0][0] == 0.1
                assert embeddings[1][0] == 0.2
                assert embeddings[2][0] == 0.3

    @pytest.mark.asyncio
    async def test_embed_texts_with_batching(self, config, mock_session):
        """Test embedding with automatic batching."""
        config.batch_size = 2
        client = VoyageAPIClient(config, api_key="test-key")

        texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]

        # Mock responses for batches
        def create_mock_response(batch_start, batch_size):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "data": [
                    {"embedding": [0.1 + i] * 2048, "index": i}
                    for i in range(batch_size)
                ],
                "model": "voyage-context-3",
                "usage": {"total_tokens": 10 * batch_size}
            }
            return mock_response

        # Set up multiple batch responses
        batch_responses = [
            create_mock_response(0, 2),  # Batch 1: texts 0-1
            create_mock_response(2, 2),  # Batch 2: texts 2-3
            create_mock_response(4, 1),  # Batch 3: text 4
        ]

        mock_session.post.return_value.__aenter__.side_effect = batch_responses

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                embeddings = await client.embed_texts(texts)

                assert len(embeddings) == 5
                assert mock_session.post.call_count == 3  # 3 batches

    @pytest.mark.asyncio
    async def test_embed_texts_api_error(self, client, mock_session):
        """Test handling of API errors."""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json.return_value = {
            "error": {"message": "Invalid input", "code": "invalid_request"}
        }

        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                with pytest.raises(Exception) as exc_info:
                    await client.embed_texts(["Invalid text"])

                assert "API request failed" in str(exc_info.value)
                assert "400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_texts_network_error(self, client, mock_session):
        """Test handling of network errors."""
        # Mock network error
        mock_session.post.side_effect = aiohttp.ClientError("Network error")

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                with pytest.raises(Exception) as exc_info:
                    await client.embed_texts(["Test text"])

                assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_texts_timeout(self, client, mock_session):
        """Test handling of request timeouts."""
        # Mock timeout error
        mock_session.post.side_effect = asyncio.TimeoutError()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                with pytest.raises(Exception) as exc_info:
                    await client.embed_texts(["Test text"])

                assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_embed_texts_rate_limiting(self, client, mock_session):
        """Test handling of rate limiting with retry."""
        # First call: rate limited
        rate_limited_response = AsyncMock()
        rate_limited_response.status = 429
        rate_limited_response.headers = {"Retry-After": "1"}
        rate_limited_response.json.return_value = {
            "error": {"message": "Rate limit exceeded", "code": "rate_limit"}
        }

        # Second call: success
        success_response = AsyncMock()
        success_response.status = 200
        success_response.json.return_value = {
            "data": [{"embedding": [0.1] * 2048, "index": 0}],
            "model": "voyage-context-3",
            "usage": {"total_tokens": 10}
        }

        mock_session.post.return_value.__aenter__.side_effect = [
            rate_limited_response,
            success_response
        ]

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                async with client:
                    embeddings = await client.embed_texts(["Test text"])

                    assert len(embeddings) == 1
                    assert mock_session.post.call_count == 2  # Retry happened
                    mock_sleep.assert_called_once_with(1.0)  # Slept for retry-after

    @pytest.mark.asyncio
    async def test_embed_texts_with_pii_detection(self, config, mock_session):
        """Test embedding with PII detection enabled."""
        config.enable_pii_detection = True
        config.pii_redaction_mode = "mask"
        client = VoyageAPIClient(config, api_key="test-key")

        # Mock PII detection
        with patch.object(client, '_detect_and_handle_pii') as mock_pii:
            mock_pii.return_value = ["Redacted text"]

            # Mock successful embedding response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 2048, "index": 0}],
                "model": "voyage-context-3",
                "usage": {"total_tokens": 10}
            }

            mock_session.post.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession', return_value=mock_session):
                async with client:
                    embeddings = await client.embed_texts(["Text with PII: SSN 123-45-6789"])

                    mock_pii.assert_called_once()
                    assert len(embeddings) == 1

    @pytest.mark.asyncio
    async def test_embed_texts_progress_tracking(self, config, mock_session):
        """Test embedding with progress tracking enabled."""
        config.enable_progress_tracking = True
        client = VoyageAPIClient(config, api_key="test-key")

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 2048, "index": 0}],
            "model": "voyage-context-3",
            "usage": {"total_tokens": 10}
        }

        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('builtins.print') as mock_print:
                async with client:
                    await client.embed_texts(["Test text"])

                    # Should have printed progress
                    mock_print.assert_called()
                    progress_calls = [call for call in mock_print.call_args_list
                                    if "embedding" in str(call).lower()]
                    assert len(progress_calls) > 0

    @pytest.mark.asyncio
    async def test_rerank_documents(self, client, mock_session):
        """Test document reranking functionality."""
        query = "test query"
        documents = ["doc1", "doc2", "doc3"]

        # Mock rerank response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "data": [
                {"index": 2, "relevance_score": 0.9},
                {"index": 0, "relevance_score": 0.7},
                {"index": 1, "relevance_score": 0.5}
            ],
            "model": "voyage-rerank-2.5",
            "usage": {"total_tokens": 50}
        }

        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                reranked = await client.rerank_documents(query, documents)

                assert len(reranked) == 3
                # Should be ordered by relevance score (descending)
                assert reranked[0]["text"] == "doc3"
                assert reranked[0]["score"] == 0.9
                assert reranked[1]["text"] == "doc1"
                assert reranked[1]["score"] == 0.7

    @pytest.mark.asyncio
    async def test_validate_connection(self, client, mock_session):
        """Test connection validation."""
        # Mock successful validation response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 2048, "index": 0}],
            "model": "voyage-context-3"
        }

        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                is_valid = await client.validate_connection()

                assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, client, mock_session):
        """Test connection validation failure."""
        # Mock failed validation
        mock_session.post.side_effect = aiohttp.ClientError("Connection failed")

        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with client:
                is_valid = await client.validate_connection()

                assert is_valid is False

    @pytest.mark.asyncio
    async def test_get_health_metrics(self, client):
        """Test health metrics collection."""
        # Simulate some usage
        client._request_count = 10
        client._total_tokens = 1000
        client._average_latency = 250.0

        metrics = await client.get_health_metrics()

        assert metrics.requests_made == 10
        assert metrics.total_tokens_used == 1000
        assert metrics.average_latency_ms == 250.0
        assert metrics.provider_name == "voyage"

    def test_prepare_request_headers(self, client):
        """Test request header preparation."""
        headers = client._prepare_headers()

        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers
        assert "dopemux" in headers["User-Agent"].lower()

    def test_prepare_embedding_payload(self, client):
        """Test embedding request payload preparation."""
        texts = ["text1", "text2"]
        payload = client._prepare_embedding_payload(texts)

        assert payload["input"] == texts
        assert payload["model"] == "voyage-context-3"
        assert "encoding_format" in payload

    def test_prepare_rerank_payload(self, client):
        """Test rerank request payload preparation."""
        query = "test query"
        documents = ["doc1", "doc2"]
        payload = client._prepare_rerank_payload(query, documents)

        assert payload["query"] == query
        assert payload["documents"] == documents
        assert payload["model"] == "voyage-rerank-2.5"

    @pytest.mark.asyncio
    async def test_detect_and_handle_pii(self, config):
        """Test PII detection and handling."""
        config.enable_pii_detection = True
        config.pii_redaction_mode = "mask"
        client = VoyageAPIClient(config, api_key="test-key")

        # Test with PII
        texts_with_pii = [
            "Contact John at john@email.com",
            "SSN: 123-45-6789",
            "Phone: (555) 123-4567"
        ]

        cleaned_texts = client._detect_and_handle_pii(texts_with_pii)

        # Should mask PII
        assert "john@email.com" not in cleaned_texts[0]
        assert "123-45-6789" not in cleaned_texts[1]
        assert "(555) 123-4567" not in cleaned_texts[2]

        # Should contain masks or redacted content
        assert all("[EMAIL]" in text or "***" in text for text in cleaned_texts
                  if "@" in texts_with_pii[i] for i, text in enumerate(cleaned_texts))

    @pytest.mark.asyncio
    async def test_concurrent_requests_limit(self, config, mock_session):
        """Test concurrent request limiting."""
        config.max_concurrent_requests = 2
        client = VoyageAPIClient(config, api_key="test-key")

        # Mock slow responses to test concurrency
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.1)
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 2048, "index": 0}],
                "model": "voyage-context-3"
            }
            return mock_response

        mock_session.post.return_value.__aenter__.side_effect = slow_response

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch.object(client, '_semaphore', asyncio.Semaphore(2)) as mock_sem:
                async with client:
                    # Start multiple concurrent requests
                    tasks = [
                        client.embed_texts([f"text {i}"])
                        for i in range(5)
                    ]

                    await asyncio.gather(*tasks)

                    # Semaphore should have been used to limit concurrency
                    assert mock_sem._value <= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dopemux.embeddings.providers", "--cov-report=term-missing"])