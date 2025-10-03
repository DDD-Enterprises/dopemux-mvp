"""
Tests for Voyage Reranking Layer - Task 6
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.rerank.voyage_reranker import (
    VoyageReranker,
    RerankResult,
    RerankResponse,
    CostTracker,
)
from src.search.dense_search import SearchResult


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test-voyage-api-key"


@pytest.fixture
def reranker(mock_api_key):
    """Create VoyageReranker instance for testing."""
    with patch("src.rerank.voyage_reranker.AsyncClient"):
        return VoyageReranker(
            api_key=mock_api_key,
            top_n_display=10,
            max_cache=40,
        )


@pytest.fixture
def sample_search_results():
    """Create sample search results."""
    return [
        SearchResult(
            id="1",
            score=0.9,
            payload={},
            file_path="src/auth.py",
            function_name="validate_user",
            language="python",
            content="def validate_user(token): pass",
            context_snippet="Validates user token",
        ),
        SearchResult(
            id="2",
            score=0.8,
            payload={},
            file_path="src/utils.py",
            function_name="calculate",
            language="python",
            content="def calculate(x): return x * 2",
            context_snippet="Calculates value",
        ),
        SearchResult(
            id="3",
            score=0.7,
            payload={},
            file_path="src/data.py",
            function_name="fetch_data",
            language="python",
            content="def fetch_data(id): pass",
            context_snippet="Fetches data by ID",
        ),
    ]


def test_cost_tracker():
    """Test cost tracking."""
    tracker = CostTracker()

    # Add requests
    cost1 = tracker.add_request(num_documents=10, tokens=500)
    cost2 = tracker.add_request(num_documents=5, tokens=250)

    assert tracker.total_requests == 2
    assert tracker.total_documents == 15
    assert cost1 > 0
    assert cost2 > 0

    # Summary
    summary = tracker.summary()
    assert summary["total_requests"] == 2
    assert summary["total_documents"] == 15
    assert summary["avg_docs_per_request"] == 7.5


@pytest.mark.asyncio
async def test_rerank_basic(reranker, sample_search_results):
    """Test basic reranking."""
    # Mock API response
    mock_reranking = MagicMock()
    mock_reranking.results = [
        MagicMock(index=2, relevance_score=0.95),  # fetch_data now top
        MagicMock(index=0, relevance_score=0.90),  # validate_user second
        MagicMock(index=1, relevance_score=0.85),  # calculate third
    ]
    mock_reranking.total_tokens = 150

    reranker.client.rerank = AsyncMock(return_value=mock_reranking)

    # Rerank
    response = await reranker.rerank(
        query="fetch data from database",
        results=sample_search_results,
    )

    assert isinstance(response, RerankResponse)
    assert response.total_results == 3
    assert len(response.top_results) == 3  # All fit in top-10
    assert len(response.cached_results) == 0
    assert response.tokens_used == 150
    assert response.cost_usd > 0

    # Check reordering
    assert response.top_results[0].search_result.id == "3"  # fetch_data
    assert response.top_results[1].search_result.id == "1"  # validate_user
    assert response.top_results[2].search_result.id == "2"  # calculate


@pytest.mark.asyncio
async def test_rerank_progressive_disclosure(reranker):
    """Test progressive disclosure with many results."""
    # Create 50 results
    many_results = [
        SearchResult(
            id=str(i),
            score=1.0 - (i * 0.01),
            payload={},
            file_path=f"file{i}.py",
            function_name=f"func{i}",
            language="python",
            content=f"def func{i}(): pass",
        )
        for i in range(50)
    ]

    # Mock API response
    mock_reranking = MagicMock()
    mock_reranking.results = [
        MagicMock(index=i, relevance_score=1.0 - (i * 0.01))
        for i in range(50)
    ]
    mock_reranking.total_tokens = 500

    reranker.client.rerank = AsyncMock(return_value=mock_reranking)

    # Rerank
    response = await reranker.rerank(
        query="test query",
        results=many_results,
    )

    # ADHD progressive disclosure
    assert len(response.top_results) == 10  # Top-10 displayed
    assert len(response.cached_results) == 40  # 40 cached (max_cache)
    assert response.total_results == 50


@pytest.mark.asyncio
async def test_rerank_empty_results(reranker):
    """Test reranking with empty results."""
    response = await reranker.rerank(
        query="test query",
        results=[],
    )

    assert response.total_results == 0
    assert len(response.top_results) == 0
    assert len(response.cached_results) == 0
    assert response.tokens_used == 0
    assert response.cost_usd == 0.0


@pytest.mark.asyncio
async def test_rerank_fallback_on_error(reranker, sample_search_results):
    """Test fallback to original ranking on API error."""
    # Mock API error
    reranker.client.rerank = AsyncMock(side_effect=Exception("API error"))

    # Should return fallback results
    response = await reranker.rerank(
        query="test query",
        results=sample_search_results,
    )

    # Should return results in original order
    assert len(response.top_results) == 3
    assert response.top_results[0].search_result.id == "1"  # Original order
    assert response.tokens_used == 0
    assert response.cost_usd == 0.0


@pytest.mark.asyncio
async def test_rerank_updates_ranks(reranker, sample_search_results):
    """Test that reranking updates rank positions."""
    # Mock reranking that reverses order
    mock_reranking = MagicMock()
    mock_reranking.results = [
        MagicMock(index=2, relevance_score=0.95),
        MagicMock(index=1, relevance_score=0.90),
        MagicMock(index=0, relevance_score=0.85),
    ]
    mock_reranking.total_tokens = 100

    reranker.client.rerank = AsyncMock(return_value=mock_reranking)

    response = await reranker.rerank(
        query="test",
        results=sample_search_results,
    )

    # Check rank updates
    assert response.top_results[0].original_rank == 2
    assert response.top_results[0].new_rank == 0

    assert response.top_results[1].original_rank == 1
    assert response.top_results[1].new_rank == 1

    assert response.top_results[2].original_rank == 0
    assert response.top_results[2].new_rank == 2


@pytest.mark.asyncio
async def test_rerank_with_context_snippets(reranker, sample_search_results):
    """Test that reranking uses context snippets."""
    mock_reranking = MagicMock()
    mock_reranking.results = [
        MagicMock(index=i, relevance_score=0.9 - i * 0.1)
        for i in range(3)
    ]
    mock_reranking.total_tokens = 100

    reranker.client.rerank = AsyncMock(return_value=mock_reranking)

    await reranker.rerank(
        query="test",
        results=sample_search_results,
    )

    # Check that documents sent to API include context
    call_args = reranker.client.rerank.call_args[1]
    documents = call_args['documents']

    # First document should have context + content
    assert "Validates user token" in documents[0]
    assert "def validate_user" in documents[0]


def test_rerank_result_creation():
    """Test RerankResult dataclass."""
    search_result = SearchResult(
        id="test",
        score=0.8,
        payload={},
        file_path="test.py",
        function_name="test_func",
        language="python",
        content="code",
    )

    rerank_result = RerankResult(
        search_result=search_result,
        relevance_score=0.95,
        original_rank=5,
        new_rank=1,
    )

    assert rerank_result.search_result.id == "test"
    assert rerank_result.relevance_score == 0.95
    assert rerank_result.original_rank == 5
    assert rerank_result.new_rank == 1


def test_rerank_response_get_all_results():
    """Test getting all results from response."""
    top = [MagicMock() for _ in range(5)]
    cached = [MagicMock() for _ in range(10)]

    response = RerankResponse(
        top_results=top,
        cached_results=cached,
        total_results=15,
        tokens_used=100,
        cost_usd=0.0001,
    )

    all_results = response.get_all_results()
    assert len(all_results) == 15
    assert all_results[:5] == top
    assert all_results[5:] == cached


def test_cost_summary(reranker):
    """Test cost summary."""
    reranker.cost_tracker.add_request(10, 100)
    reranker.cost_tracker.add_request(20, 200)

    summary = reranker.get_cost_summary()

    assert summary["total_requests"] == 2
    assert summary["total_documents"] == 30
    assert summary["avg_docs_per_request"] == 15.0
    assert summary["total_cost_usd"] > 0
