"""
Tests for VoyageAI Embedder - Task 1
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.embeddings.voyage_embedder import (
    CostTracker,
    EmbeddingRequest,
    EmbeddingResponse,
    VoyageEmbedder,
)


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test-voyage-api-key"


@pytest.fixture
def embedder(mock_api_key):
    """Create VoyageEmbedder instance for testing."""
    with patch("src.embeddings.voyage_embedder.AsyncClient"):
        return VoyageEmbedder(
            api_key=mock_api_key,
            cache_ttl_hours=1,
            max_batch_size=10,
            rate_limit_rpm=60,
        )


def test_embedding_request_cache_key():
    """Test cache key generation."""
    req1 = EmbeddingRequest(
        text="def foo():",
        model="voyage-code-3",
        input_type="document",
    )

    req2 = EmbeddingRequest(
        text="def foo():",
        model="voyage-code-3",
        input_type="document",
    )

    req3 = EmbeddingRequest(
        text="def bar():",
        model="voyage-code-3",
        input_type="document",
    )

    # Same text = same key
    assert req1.cache_key() == req2.cache_key()

    # Different text = different key
    assert req1.cache_key() != req3.cache_key()


def test_cost_tracker():
    """Test cost tracking."""
    tracker = CostTracker()

    # Add requests
    cost1 = tracker.add_request("voyage-code-3", tokens=1000, cached=False)
    cost2 = tracker.add_request("voyage-code-3", tokens=500, cached=True)

    assert tracker.total_tokens == 1000  # Cached doesn't count
    assert tracker.cache_hits == 1
    assert tracker.total_requests == 2
    assert cost1 > 0
    assert cost2 == 0.0

    # Summary
    summary = tracker.summary()
    assert summary["total_requests"] == 2
    assert summary["cache_hits"] == 1
    assert summary["cache_rate"] == 0.5


@pytest.mark.asyncio
async def test_embed_single(embedder):
    """Test single text embedding."""
    # Mock API response
    mock_result = MagicMock()
    mock_result.embeddings = [[0.1, 0.2, 0.3] * 341]  # 1024d
    mock_result.total_tokens = 50

    embedder.client.embed = AsyncMock(return_value=mock_result)

    # Embed
    response = await embedder.embed(
        text="async def process():",
        model="voyage-code-3",
        input_type="document",
    )

    assert isinstance(response, EmbeddingResponse)
    assert len(response.embedding) == 1023
    assert response.model == "voyage-code-3"
    assert response.tokens == 50
    assert not response.cached
    assert response.cost_usd > 0


@pytest.mark.asyncio
async def test_embed_with_cache(embedder):
    """Test embedding with caching."""
    # Mock API response
    mock_result = MagicMock()
    mock_result.embeddings = [[0.1] * 1024]
    mock_result.total_tokens = 50

    embedder.client.embed = AsyncMock(return_value=mock_result)

    text = "def foo():"

    # First call - not cached
    response1 = await embedder.embed(text, model="voyage-code-3")
    assert not response1.cached

    # Second call - cached
    response2 = await embedder.embed(text, model="voyage-code-3")
    assert response2.cached
    assert response2.cost_usd == 0.0

    # API should only be called once
    assert embedder.client.embed.call_count == 1


@pytest.mark.asyncio
async def test_embed_batch(embedder):
    """Test batch embedding."""
    # Mock API response
    mock_result = MagicMock()
    mock_result.embeddings = [
        [0.1] * 1024,
        [0.2] * 1024,
        [0.3] * 1024,
    ]
    mock_result.total_tokens = 150

    embedder.client.embed = AsyncMock(return_value=mock_result)

    texts = [
        "def foo():",
        "class Bar:",
        "async with session:",
    ]

    responses = await embedder.embed_batch(
        texts=texts,
        model="voyage-code-3",
    )

    assert len(responses) == 3
    assert all(isinstance(r, EmbeddingResponse) for r in responses)
    assert all(len(r.embedding) == 1024 for r in responses)


@pytest.mark.asyncio
async def test_batch_with_partial_cache(embedder):
    """Test batch with some texts already cached."""
    # Mock API response for first call
    mock_result = MagicMock()
    mock_result.embeddings = [
        [0.1] * 1024,
        [0.2] * 1024,
        [0.3] * 1024,
    ]
    mock_result.total_tokens = 150

    embedder.client.embed = AsyncMock(return_value=mock_result)

    texts = [
        "def foo():",  # Will be cached after first call
        "class Bar:",
        "async with session:",
    ]

    # First batch
    responses1 = await embedder.embed_batch(texts, model="voyage-code-3")
    assert all(not r.cached for r in responses1)

    # Second batch - first text cached, others not
    texts2 = ["def foo():", "new code", "more code"]

    mock_result2 = MagicMock()
    mock_result2.embeddings = [
        [0.4] * 1024,
        [0.5] * 1024,
    ]
    mock_result2.total_tokens = 80
    embedder.client.embed.return_value = mock_result2

    responses2 = await embedder.embed_batch(texts2, model="voyage-code-3")

    assert responses2[0].cached  # First one cached
    assert not responses2[1].cached
    assert not responses2[2].cached


def test_clear_cache(embedder):
    """Test cache clearing."""
    # Add to cache manually
    embedder.cache["test_key"] = (
        EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=50,
        ),
        embedder.cache.get("test_key", (None, None))[1]
        or asyncio.get_event_loop().time(),
    )

    assert len(embedder.cache) > 0

    embedder.clear_cache()

    assert len(embedder.cache) == 0


def test_cost_summary(embedder):
    """Test cost summary."""
    embedder.cost_tracker.add_request("voyage-code-3", 1000, cached=False)
    embedder.cost_tracker.add_request("voyage-3-lite", 500, cached=True)

    summary = embedder.get_cost_summary()

    assert summary["total_requests"] == 2
    assert summary["total_tokens"] == 1000
    assert summary["cache_hits"] == 1
    assert summary["total_cost_usd"] > 0
