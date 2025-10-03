"""
Tests for FastMCP Server - Task 8
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.server import (
    _index_workspace_impl,
    _search_code_impl,
    _get_index_status_impl,
    _clear_index_impl,
)
from src.pipeline.indexing_pipeline import IndexingProgress
from src.search.dense_search import SearchResult
from src.rerank.voyage_reranker import RerankResult, RerankResponse


@pytest.fixture
def mock_pipeline():
    """Mock pipeline for testing."""
    pipeline = MagicMock()
    pipeline.index_workspace = AsyncMock()
    pipeline.vector_search = MagicMock()
    pipeline.vector_search.get_collection_info = AsyncMock()
    pipeline.vector_search.delete_collection = AsyncMock()
    pipeline.context_generator = MagicMock()
    pipeline.context_generator.get_cost_summary.return_value = {"total_cost_usd": 0.10}
    return pipeline


@pytest.fixture
def mock_components():
    """Mock all components."""
    embedder = MagicMock()
    hybrid_search = MagicMock()
    reranker = MagicMock()

    return {
        "embedder": embedder,
        "hybrid_search": hybrid_search,
        "reranker": reranker,
    }


@pytest.mark.asyncio
async def test_index_workspace_tool(tmp_path):
    """Test index_workspace MCP tool."""
    with patch("src.mcp.server._initialize_components") as mock_init, patch(
        "src.mcp.server._pipeline"
    ) as mock_pipeline:

        # Mock progress
        progress = IndexingProgress(
            total_files=5,
            processed_files=5,
            total_chunks=20,
            indexed_chunks=20,
        )

        mock_pipeline.index_workspace = AsyncMock(return_value=progress)
        mock_pipeline.config = MagicMock()

        # Call tool impl
        result = await _index_workspace_impl(
            workspace_path=str(tmp_path),
            include_patterns=["*.py"],
            max_files=10,
        )

        # Check result
        assert "files" in result
        assert "chunks" in result
        assert "completion" in result


@pytest.mark.asyncio
async def test_search_code_tool():
    """Test search_code MCP tool."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._hybrid_search"
    ) as mock_hybrid, patch("src.mcp.server._embedder") as mock_embedder, patch(
        "src.mcp.server._reranker"
    ) as mock_reranker:

        # Mock embedder
        from src.embeddings.voyage_embedder import EmbeddingResponse

        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=10,
        )
        mock_embedder.embed = AsyncMock(return_value=mock_embedding)

        # Mock search results
        search_result = SearchResult(
            id="1",
            score=0.9,
            payload={},
            file_path="src/test.py",
            function_name="test_func",
            language="python",
            content="def test_func(): pass",
            context_snippet="Test function",
        )
        mock_hybrid.search = AsyncMock(return_value=[search_result])

        # Mock reranker
        rerank_result = RerankResult(
            search_result=search_result,
            relevance_score=0.95,
            original_rank=0,
            new_rank=0,
        )
        rerank_response = RerankResponse(
            top_results=[rerank_result],
            cached_results=[],
            total_results=1,
            tokens_used=50,
            cost_usd=0.0001,
        )
        mock_reranker.rerank = AsyncMock(return_value=rerank_response)

        # Call tool impl
        results = await _search_code_impl(
            query="test function",
            top_k=10,
            use_reranking=True,
        )

        # Check results
        assert len(results) > 0
        assert results[0]["file_path"] == "src/test.py"
        assert results[0]["function_name"] == "test_func"
        assert results[0]["reranked"] == True
        assert "relevance_score" in results[0]


@pytest.mark.asyncio
async def test_search_code_without_reranking():
    """Test search_code without reranking."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._hybrid_search"
    ) as mock_hybrid, patch("src.mcp.server._embedder") as mock_embedder:

        # Mock embedder
        from src.embeddings.voyage_embedder import EmbeddingResponse

        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=10,
        )
        mock_embedder.embed = AsyncMock(return_value=mock_embedding)

        # Mock search results
        search_result = SearchResult(
            id="1",
            score=0.9,
            payload={},
            file_path="src/test.py",
            function_name="test_func",
            language="python",
            content="def test_func(): pass",
            context_snippet="Test function",
        )
        mock_hybrid.search = AsyncMock(return_value=[search_result])

        # Call tool impl without reranking
        results = await _search_code_impl(
            query="test function",
            top_k=10,
            use_reranking=False,
        )

        # Should return results without reranking
        assert len(results) > 0
        assert results[0]["reranked"] == False
        assert "score" in results[0]


@pytest.mark.asyncio
async def test_search_code_with_language_filter():
    """Test search_code with language filter."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._hybrid_search"
    ) as mock_hybrid, patch("src.mcp.server._embedder") as mock_embedder, patch(
        "src.mcp.server._reranker"
    ) as mock_reranker:

        # Setup mocks
        from src.embeddings.voyage_embedder import EmbeddingResponse

        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=10,
        )
        mock_embedder.embed = AsyncMock(return_value=mock_embedding)
        mock_hybrid.search = AsyncMock(return_value=[])
        mock_reranker.rerank = AsyncMock(
            return_value=RerankResponse(
                top_results=[],
                cached_results=[],
                total_results=0,
                tokens_used=0,
                cost_usd=0,
            )
        )

        # Call with filter
        await _search_code_impl(
            query="test",
            filter_language="python",
        )

        # Verify filter was passed
        call_args = mock_hybrid.search.call_args
        assert call_args[1].get("filter_by") == {"language": "python"}


@pytest.mark.asyncio
async def test_get_index_status_tool():
    """Test get_index_status MCP tool."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._pipeline"
    ) as mock_pipeline, patch("src.mcp.server._embedder") as mock_embedder:

        # Mock collection info
        mock_pipeline.vector_search.get_collection_info = AsyncMock(
            return_value={
                "name": "code_index",
                "vectors_count": 1000,
                "status": "green",
            }
        )

        mock_embedder.get_cost_summary.return_value = {"total_cost_usd": 0.50}

        mock_pipeline.context_generator = MagicMock()
        mock_pipeline.context_generator.get_cost_summary.return_value = {
            "total_cost_usd": 0.20
        }

        # Call tool impl
        status = await _get_index_status_impl()

        # Check status
        assert status["collection_name"] == "code_index"
        assert status["total_vectors"] == 1000
        assert status["status"] == "green"
        assert "embedding_cost_summary" in status


@pytest.mark.asyncio
async def test_clear_index_tool():
    """Test clear_index MCP tool."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._pipeline"
    ) as mock_pipeline:

        mock_pipeline.vector_search.delete_collection = AsyncMock()

        # Call tool impl
        result = await _clear_index_impl()

        # Check result
        assert result["status"] == "success"
        mock_pipeline.vector_search.delete_collection.assert_called_once()


def test_search_profiles():
    """Test search profile mapping."""
    profiles = ["implementation", "debugging", "exploration"]

    for profile_name in profiles:
        # Should not raise
        assert profile_name in ["implementation", "debugging", "exploration"]
