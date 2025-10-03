"""
Tests for Hybrid Search + BM25 Fusion - Task 5
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.search.hybrid_search import (
    code_aware_tokenizer,
    reciprocal_rank_fusion,
    BM25Index,
    HybridSearch,
)
from src.search.dense_search import SearchResult, SearchProfile


def test_code_aware_tokenizer_camel_case():
    """Test camelCase tokenization."""
    tokens = code_aware_tokenizer("getUserData")
    assert tokens == ["get", "user", "data"]


def test_code_aware_tokenizer_snake_case():
    """Test snake_case tokenization."""
    tokens = code_aware_tokenizer("get_user_data")
    assert tokens == ["get", "user", "data"]


def test_code_aware_tokenizer_mixed():
    """Test mixed case and punctuation."""
    tokens = code_aware_tokenizer("user.calculateScore")
    assert "user" in tokens
    assert "calculate" in tokens
    assert "score" in tokens


def test_code_aware_tokenizer_with_numbers():
    """Test tokenization with numbers."""
    tokens = code_aware_tokenizer("user123_data456")
    assert "user" in tokens
    assert "123" in tokens
    assert "data" in tokens
    assert "456" in tokens


def test_reciprocal_rank_fusion_basic():
    """Test basic RRF fusion."""
    rankings = [
        [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)],
        [("doc2", 0.95), ("doc1", 0.85), ("doc4", 0.75)],
    ]

    fused = reciprocal_rank_fusion(rankings, k=60)

    # doc1 and doc2 should have highest scores (appear in both)
    assert len(fused) == 4
    assert fused[0][0] in ["doc1", "doc2"]  # Top result
    assert all(isinstance(score, float) for _, score in fused)


def test_reciprocal_rank_fusion_single_ranking():
    """Test RRF with single ranking."""
    rankings = [[("doc1", 0.9), ("doc2", 0.8)]]

    fused = reciprocal_rank_fusion(rankings, k=60)

    assert len(fused) == 2
    assert fused[0][0] == "doc1"  # Original order preserved


def test_reciprocal_rank_fusion_empty():
    """Test RRF with empty rankings."""
    fused = reciprocal_rank_fusion([], k=60)
    assert fused == []


def test_bm25_index_build():
    """Test BM25 index building."""
    index = BM25Index()

    docs = [
        {
            'id': '1',
            'raw_code': 'def calculate_sum(a, b): return a + b',
            'function_name': 'calculate_sum',
        },
        {
            'id': '2',
            'raw_code': 'def get_user_data(user_id): return data',
            'function_name': 'get_user_data',
        },
    ]

    index.build_index(docs)

    assert index.bm25 is not None
    assert len(index.documents) == 2
    assert len(index.doc_ids) == 2


def test_bm25_index_search():
    """Test BM25 search."""
    index = BM25Index()

    docs = [
        {
            'id': '1',
            'raw_code': 'def calculate_sum(a, b): return a + b',
            'function_name': 'calculate_sum',
        },
        {
            'id': '2',
            'raw_code': 'def get_user_data(user_id): return data',
            'function_name': 'get_user_data',
        },
    ]

    index.build_index(docs)

    # Search for "calculate"
    results = index.search("calculate sum", top_k=10)

    assert len(results) > 0
    # First result should be doc1 (contains "calculate" and "sum")
    assert results[0][0] == '1'
    # BM25 scores can be negative (ranking matters, not absolute value)
    assert isinstance(results[0][1], float)


def test_bm25_index_search_no_matches():
    """Test BM25 search with no matches."""
    index = BM25Index()

    docs = [
        {'id': '1', 'raw_code': 'def foo(): pass', 'function_name': 'foo'},
    ]

    index.build_index(docs)

    results = index.search("nonexistent query xyz", top_k=10)

    # Should return empty or very low scores
    assert len(results) == 0 or all(score < 0.01 for _, score in results)


def test_bm25_index_get_document():
    """Test getting document by ID."""
    index = BM25Index()

    docs = [
        {'id': '1', 'raw_code': 'def foo(): pass', 'function_name': 'foo'},
        {'id': '2', 'raw_code': 'def bar(): pass', 'function_name': 'bar'},
    ]

    index.build_index(docs)

    doc = index.get_document('1')
    assert doc is not None
    assert doc['function_name'] == 'foo'

    doc = index.get_document('nonexistent')
    assert doc is None


@pytest.mark.asyncio
async def test_hybrid_search_initialization():
    """Test HybridSearch initialization."""
    dense_search = MagicMock()
    bm25_index = BM25Index()

    hybrid = HybridSearch(
        dense_search=dense_search,
        bm25_index=bm25_index,
    )

    assert hybrid.dense_search == dense_search
    assert hybrid.bm25_index == bm25_index
    assert hybrid.rrf_k == 60


@pytest.mark.asyncio
async def test_hybrid_search_basic():
    """Test basic hybrid search."""
    # Mock dense search
    dense_search = MagicMock()
    dense_search.search = AsyncMock(return_value=[
        SearchResult(
            id='1',
            score=0.9,
            payload={'raw_code': 'code1'},
            file_path='file1.py',
            function_name='func1',
            language='python',
            content='def func1(): pass',
        ),
        SearchResult(
            id='2',
            score=0.8,
            payload={'raw_code': 'code2'},
            file_path='file2.py',
            function_name='func2',
            language='python',
            content='def func2(): pass',
        ),
    ])

    # Create BM25 index
    bm25_index = BM25Index()
    bm25_index.build_index([
        {'id': '1', 'raw_code': 'def func1(): pass', 'function_name': 'func1', 'file_path': 'file1.py'},
        {'id': '2', 'raw_code': 'def func2(): pass', 'function_name': 'func2', 'file_path': 'file2.py'},
    ])

    # Create hybrid search
    hybrid = HybridSearch(dense_search, bm25_index)

    # Search
    query_vectors = {
        'content': [0.1] * 1024,
        'title': [0.2] * 1024,
        'breadcrumb': [0.3] * 1024,
    }

    results = await hybrid.search(
        query_vectors=query_vectors,
        query_text="func",
        top_k=10,
    )

    # Should return results
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)
    # Results should be sorted by score
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_hybrid_search_with_weights():
    """Test hybrid search with different weights."""
    dense_search = MagicMock()
    dense_search.search = AsyncMock(return_value=[
        SearchResult(
            id='1',
            score=0.9,
            payload={'raw_code': 'code1'},
            file_path='file1.py',
            function_name='func1',
            language='python',
            content='def func1(): pass',
        ),
    ])

    bm25_index = BM25Index()
    bm25_index.build_index([
        {'id': '1', 'raw_code': 'def func1(): pass', 'function_name': 'func1', 'file_path': 'file1.py'},
    ])

    hybrid = HybridSearch(dense_search, bm25_index)

    query_vectors = {
        'content': [0.1] * 1024,
        'title': [0.2] * 1024,
        'breadcrumb': [0.3] * 1024,
    }

    # Dense-heavy search
    results_dense = await hybrid.search(
        query_vectors=query_vectors,
        query_text="func",
        dense_weight=0.9,
        sparse_weight=0.1,
    )

    # Sparse-heavy search
    results_sparse = await hybrid.search(
        query_vectors=query_vectors,
        query_text="func",
        dense_weight=0.1,
        sparse_weight=0.9,
    )

    # Both should return results (may have different scores)
    assert len(results_dense) > 0
    assert len(results_sparse) > 0


@pytest.mark.asyncio
async def test_hybrid_search_empty_results():
    """Test hybrid search with no results."""
    dense_search = MagicMock()
    dense_search.search = AsyncMock(return_value=[])

    bm25_index = BM25Index()
    bm25_index.build_index([
        {'id': '1', 'raw_code': 'def foo(): pass', 'function_name': 'foo'},
    ])

    hybrid = HybridSearch(dense_search, bm25_index)

    query_vectors = {
        'content': [0.1] * 1024,
        'title': [0.2] * 1024,
        'breadcrumb': [0.3] * 1024,
    }

    results = await hybrid.search(
        query_vectors=query_vectors,
        query_text="nonexistent xyz abc",
        top_k=10,
    )

    # May have empty results or very low scores
    assert isinstance(results, list)


def test_bm25_code_search_specific():
    """Test BM25 with code-specific queries."""
    index = BM25Index()

    docs = [
        {
            'id': '1',
            'raw_code': 'async def getUserData(userId): return await db.fetch(userId)',
            'function_name': 'getUserData',
            'context_snippet': 'Fetches user data from database',
        },
        {
            'id': '2',
            'raw_code': 'def calculate_user_score(user): return user.score * 2',
            'function_name': 'calculate_user_score',
            'context_snippet': 'Calculates user engagement score',
        },
    ]

    index.build_index(docs)

    # Search with camelCase
    results = index.search("getUserData", top_k=5)
    assert len(results) > 0
    assert results[0][0] == '1'  # Should match doc1

    # Search with description
    results = index.search("user score", top_k=5)
    assert len(results) > 0
    # Should find doc2 (has "user" and "score")
    doc_ids = [doc_id for doc_id, _ in results]
    assert '2' in doc_ids
