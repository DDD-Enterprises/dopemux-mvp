"""
Tests for Claude Context Generator - Task 3
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.context.claude_generator import (
    ClaudeContextGenerator,
    ContextRequest,
    ContextResponse,
    CostTracker,
)
from src.preprocessing.code_chunker import CodeChunk


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test-anthropic-api-key"


@pytest.fixture
def generator(mock_api_key):
    """Create ClaudeContextGenerator instance for testing."""
    # Mock the Anthropic client at import level
    with patch("anthropic.AsyncAnthropic") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        gen = ClaudeContextGenerator(
            api_key=mock_api_key,
            cache_ttl_hours=1,
            max_batch_size=5,
        )
        return gen


@pytest.fixture
def sample_chunk():
    """Create sample code chunk."""
    return CodeChunk(
        content="def calculate_total(items):\n    return sum(item.price for item in items)",
        start_line=10,
        end_line=11,
        chunk_type="function",
        language="python",
        symbol_name="calculate_total",
        parent_symbol=None,
        complexity=0.3,
        tokens_estimate=20,
    )


def test_context_request_cache_key(sample_chunk):
    """Test cache key generation."""
    req1 = ContextRequest(
        chunk=sample_chunk,
        file_path="src/billing.py",
        module_name="billing",
    )

    req2 = ContextRequest(
        chunk=sample_chunk,
        file_path="src/billing.py",
        module_name="billing",
    )

    # Same content = same key
    assert req1.cache_key() == req2.cache_key()


def test_cost_tracker():
    """Test cost tracking."""
    tracker = CostTracker()

    # Add requests
    cost1 = tracker.add_request(input_tokens=1000, output_tokens=100, cached=False)
    cost2 = tracker.add_request(input_tokens=500, output_tokens=50, cached=True)

    assert tracker.total_input_tokens == 1000  # Cached doesn't count
    assert tracker.total_output_tokens == 100
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
async def test_generate_context(generator, sample_chunk):
    """Test single context generation."""
    # Mock API response
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="This function from src/billing.py calculates the total price for a list of items. It sums the price attribute of each item.")]
    mock_message.usage = MagicMock(input_tokens=150, output_tokens=25)

    generator.client.messages.create = AsyncMock(return_value=mock_message)

    # Generate context
    response = await generator.generate_context(
        chunk=sample_chunk,
        file_path="src/billing.py",
        module_name="billing",
    )

    assert isinstance(response, ContextResponse)
    assert len(response.context) > 0
    assert "function" in response.context.lower()
    assert response.tokens_used == 175
    assert not response.cached
    assert response.cost_usd > 0


@pytest.mark.asyncio
async def test_context_caching(generator, sample_chunk):
    """Test context caching."""
    # Mock API response
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Test context")]
    mock_message.usage = MagicMock(input_tokens=100, output_tokens=20)

    generator.client.messages.create = AsyncMock(return_value=mock_message)

    # First call - not cached
    response1 = await generator.generate_context(
        chunk=sample_chunk,
        file_path="src/test.py",
    )
    assert not response1.cached

    # Second call - cached
    response2 = await generator.generate_context(
        chunk=sample_chunk,
        file_path="src/test.py",
    )
    assert response2.cached
    assert response2.cost_usd == 0.0

    # API should only be called once
    assert generator.client.messages.create.call_count == 1


@pytest.mark.asyncio
async def test_generate_contexts_batch(generator):
    """Test batch context generation."""
    # Create multiple chunks
    chunks = [
        CodeChunk(
            content=f"def func{i}(): pass",
            start_line=i * 10,
            end_line=i * 10 + 1,
            chunk_type="function",
            language="python",
            symbol_name=f"func{i}",
        )
        for i in range(3)
    ]

    file_paths = ["src/test.py"] * 3

    # Mock API response
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Test context")]
    mock_message.usage = MagicMock(input_tokens=100, output_tokens=20)

    generator.client.messages.create = AsyncMock(return_value=mock_message)

    # Generate contexts
    responses = await generator.generate_contexts_batch(
        chunks=chunks,
        file_paths=file_paths,
    )

    assert len(responses) == 3
    assert all(isinstance(r, ContextResponse) for r in responses)
    assert all(r.context == "Test context" for r in responses)


@pytest.mark.asyncio
async def test_batch_with_partial_cache(generator, sample_chunk):
    """Test batch with some contexts already cached."""
    chunks = [sample_chunk] * 3
    file_paths = ["src/test1.py", "src/test2.py", "src/test3.py"]

    # Mock API response
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Test context")]
    mock_message.usage = MagicMock(input_tokens=100, output_tokens=20)

    generator.client.messages.create = AsyncMock(return_value=mock_message)

    # First batch - all uncached
    responses1 = await generator.generate_contexts_batch(
        chunks=chunks,
        file_paths=file_paths,
    )
    assert all(not r.cached for r in responses1)

    # Second batch - first one cached, others not
    chunks2 = [sample_chunk] * 3
    file_paths2 = ["src/test1.py", "src/new1.py", "src/new2.py"]

    responses2 = await generator.generate_contexts_batch(
        chunks=chunks2,
        file_paths=file_paths2,
    )

    assert responses2[0].cached  # First one cached
    assert not responses2[1].cached
    assert not responses2[2].cached


@pytest.mark.asyncio
async def test_fallback_on_error(generator, sample_chunk):
    """Test fallback to simple context on API error."""
    # Mock API error
    generator.client.messages.create = AsyncMock(side_effect=Exception("API error"))

    # Should return fallback context
    response = await generator.generate_context(
        chunk=sample_chunk,
        file_path="src/test.py",
    )

    assert isinstance(response, ContextResponse)
    assert "src/test.py" in response.context
    assert response.tokens_used == 0
    assert response.cost_usd == 0.0


def test_build_context_prompt(generator, sample_chunk):
    """Test context prompt building."""
    prompt = generator._build_context_prompt(
        chunk=sample_chunk,
        file_path="src/billing.py",
        module_name="billing",
    )

    assert "function" in prompt.lower()
    assert "billing" in prompt
    # When module_name provided, uses module.symbol format
    assert "billing.calculate_total" in prompt
    assert sample_chunk.content in prompt
    assert "calculate_total" in prompt


def test_clear_cache(generator):
    """Test cache clearing."""
    # Add to cache manually
    generator.cache["test_key"] = (
        ContextResponse(
            context="Test context",
            tokens_used=50,
        ),
        generator.cache.get("test_key", (None, None))[1] or asyncio.get_event_loop().time(),
    )

    assert len(generator.cache) > 0

    generator.clear_cache()

    assert len(generator.cache) == 0


def test_cost_summary(generator):
    """Test cost summary."""
    generator.cost_tracker.add_request(1000, 100, cached=False)
    generator.cost_tracker.add_request(500, 50, cached=True)

    summary = generator.get_cost_summary()

    assert summary["total_requests"] == 2
    assert summary["total_input_tokens"] == 1000
    assert summary["total_output_tokens"] == 100
    assert summary["cache_hits"] == 1
    assert summary["total_cost_usd"] > 0


def test_context_response_defaults():
    """Test ContextResponse default values."""
    response = ContextResponse(
        context="Test context",
        tokens_used=100,
    )

    assert response.cached == False
    assert response.cost_usd == 0.0
