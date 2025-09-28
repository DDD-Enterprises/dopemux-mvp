"""
Unit tests for hybrid vector storage system.

Tests the HybridVectorStore and related storage components.
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from dopemux.embeddings.storage import (
    HybridVectorStore,
    HNSWIndex,
    BM25Index,
    HybridRanker,
    InMemoryDocumentStore
)
from dopemux.embeddings.core import AdvancedEmbeddingConfig, SearchResult
from dopemux.embeddings.providers import VoyageAPIClient


class TestInMemoryDocumentStore:
    """Test in-memory document storage."""

    @pytest.fixture
    def doc_store(self):
        """Create test document store."""
        return InMemoryDocumentStore()

    def test_store_initialization(self, doc_store):
        """Test document store initialization."""
        assert len(doc_store.documents) == 0
        assert len(doc_store._id_to_index) == 0

    async def test_add_documents(self, doc_store):
        """Test adding documents."""
        docs = [
            {"id": "doc1", "content": "First document", "metadata": {"type": "text"}},
            {"id": "doc2", "content": "Second document", "metadata": {"type": "code"}}
        ]

        await doc_store.add_documents(docs)

        assert len(doc_store.documents) == 2
        assert doc_store.documents[0]["id"] == "doc1"
        assert doc_store.documents[1]["id"] == "doc2"
        assert doc_store._id_to_index["doc1"] == 0
        assert doc_store._id_to_index["doc2"] == 1

    async def test_get_document_by_id(self, doc_store):
        """Test retrieving document by ID."""
        docs = [{"id": "test_doc", "content": "Test content"}]
        await doc_store.add_documents(docs)

        doc = await doc_store.get_document("test_doc")
        assert doc["id"] == "test_doc"
        assert doc["content"] == "Test content"

    async def test_get_nonexistent_document(self, doc_store):
        """Test retrieving non-existent document."""
        doc = await doc_store.get_document("nonexistent")
        assert doc is None

    async def test_get_documents_by_indices(self, doc_store):
        """Test retrieving documents by indices."""
        docs = [
            {"id": "doc1", "content": "First"},
            {"id": "doc2", "content": "Second"},
            {"id": "doc3", "content": "Third"}
        ]
        await doc_store.add_documents(docs)

        retrieved = await doc_store.get_documents_by_indices([0, 2])
        assert len(retrieved) == 2
        assert retrieved[0]["id"] == "doc1"
        assert retrieved[1]["id"] == "doc3"

    async def test_update_document(self, doc_store):
        """Test updating existing document."""
        docs = [{"id": "doc1", "content": "Original content"}]
        await doc_store.add_documents(docs)

        updated_doc = {"id": "doc1", "content": "Updated content", "version": 2}
        await doc_store.update_document("doc1", updated_doc)

        doc = await doc_store.get_document("doc1")
        assert doc["content"] == "Updated content"
        assert doc["version"] == 2

    async def test_delete_document(self, doc_store):
        """Test deleting document."""
        docs = [
            {"id": "doc1", "content": "Keep this"},
            {"id": "doc2", "content": "Delete this"}
        ]
        await doc_store.add_documents(docs)

        success = await doc_store.delete_document("doc2")
        assert success is True

        # Document should be None (soft delete)
        doc = await doc_store.get_document("doc2")
        assert doc is None

        # Index mapping should be updated
        assert "doc2" not in doc_store._id_to_index

    def test_get_stats(self, doc_store):
        """Test getting storage statistics."""
        stats = doc_store.get_stats()

        assert "document_count" in stats
        assert "storage_type" in stats
        assert stats["storage_type"] == "in_memory"


class TestHNSWIndex:
    """Test HNSW vector index."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(
            embedding_dimension=128,  # Smaller for testing
            hnsw_m=16,
            hnsw_ef=64
        )

    @pytest.fixture
    def hnsw_index(self, config):
        """Create test HNSW index."""
        return HNSWIndex(config)

    def test_index_initialization(self, hnsw_index, config):
        """Test HNSW index initialization."""
        assert hnsw_index.config == config
        assert hnsw_index.dimension == 128
        assert hnsw_index.index is not None
        assert hnsw_index.doc_ids == []

    async def test_add_vectors(self, hnsw_index):
        """Test adding vectors to index."""
        vectors = np.random.random((5, 128)).astype(np.float32)
        doc_ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]

        await hnsw_index.add_vectors(vectors, doc_ids)

        assert len(hnsw_index.doc_ids) == 5
        assert hnsw_index.index.get_current_count() == 5

    async def test_search_vectors(self, hnsw_index):
        """Test vector search."""
        # Add some vectors
        vectors = np.random.random((10, 128)).astype(np.float32)
        doc_ids = [f"doc{i}" for i in range(10)]
        await hnsw_index.add_vectors(vectors, doc_ids)

        # Search with first vector (should be very similar to itself)
        query_vector = vectors[0]
        results = await hnsw_index.search(query_vector, k=3)

        assert len(results) <= 3
        assert results[0]["doc_id"] == "doc0"  # Should find itself first
        assert results[0]["score"] > 0.9  # High similarity

    async def test_search_empty_index(self, hnsw_index):
        """Test searching empty index."""
        query_vector = np.random.random(128).astype(np.float32)
        results = await hnsw_index.search(query_vector, k=5)

        assert len(results) == 0

    async def test_update_vector(self, hnsw_index):
        """Test updating existing vector."""
        # Add initial vector
        vector = np.random.random(128).astype(np.float32)
        await hnsw_index.add_vectors(np.array([vector]), ["doc1"])

        # Update with new vector
        new_vector = np.random.random(128).astype(np.float32)
        await hnsw_index.update_vector("doc1", new_vector)

        # Search should find the updated vector
        results = await hnsw_index.search(new_vector, k=1)
        assert len(results) == 1
        assert results[0]["doc_id"] == "doc1"

    async def test_delete_vector(self, hnsw_index):
        """Test deleting vector."""
        vectors = np.random.random((3, 128)).astype(np.float32)
        doc_ids = ["doc1", "doc2", "doc3"]
        await hnsw_index.add_vectors(vectors, doc_ids)

        # Delete middle document
        await hnsw_index.delete_vector("doc2")

        # Should have 2 vectors remaining
        assert len([doc_id for doc_id in hnsw_index.doc_ids if doc_id is not None]) == 2

    async def test_save_and_load_index(self, hnsw_index, tmp_path):
        """Test saving and loading index."""
        # Add some data
        vectors = np.random.random((5, 128)).astype(np.float32)
        doc_ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        await hnsw_index.add_vectors(vectors, doc_ids)

        # Save index
        index_path = tmp_path / "test_index.bin"
        await hnsw_index.save(str(index_path))

        # Create new index and load
        new_index = HNSWIndex(hnsw_index.config)
        await new_index.load(str(index_path))

        # Should have same data
        assert len(new_index.doc_ids) == 5
        assert new_index.index.get_current_count() == 5

        # Search should work the same
        query_vector = vectors[0]
        results = await new_index.search(query_vector, k=1)
        assert results[0]["doc_id"] == "doc1"

    def test_get_stats(self, hnsw_index):
        """Test getting index statistics."""
        stats = hnsw_index.get_stats()

        assert "vector_count" in stats
        assert "index_type" in stats
        assert "dimension" in stats
        assert stats["index_type"] == "hnsw"


class TestBM25Index:
    """Test BM25 lexical index."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig()

    @pytest.fixture
    def bm25_index(self, config):
        """Create test BM25 index."""
        return BM25Index(config)

    def test_index_initialization(self, bm25_index):
        """Test BM25 index initialization."""
        assert bm25_index.k1 == 1.5  # BM25 parameter
        assert bm25_index.b == 0.75   # BM25 parameter
        assert bm25_index.documents == []
        assert bm25_index.doc_ids == []

    async def test_add_documents(self, bm25_index):
        """Test adding documents to BM25 index."""
        docs = [
            {"id": "doc1", "content": "machine learning algorithms"},
            {"id": "doc2", "content": "deep neural networks"},
            {"id": "doc3", "content": "machine learning with neural networks"}
        ]

        await bm25_index.add_documents(docs)

        assert len(bm25_index.documents) == 3
        assert len(bm25_index.doc_ids) == 3
        assert bm25_index.doc_ids[0] == "doc1"

    async def test_search_documents(self, bm25_index):
        """Test BM25 search."""
        docs = [
            {"id": "doc1", "content": "machine learning algorithms"},
            {"id": "doc2", "content": "deep neural networks"},
            {"id": "doc3", "content": "machine learning with neural networks"},
            {"id": "doc4", "content": "computer vision applications"}
        ]
        await bm25_index.add_documents(docs)

        # Search for "machine learning"
        results = await bm25_index.search("machine learning", k=3)

        assert len(results) <= 3
        # Documents with "machine learning" should rank higher
        assert results[0]["doc_id"] in ["doc1", "doc3"]
        assert all(result["score"] > 0 for result in results)

    async def test_search_empty_index(self, bm25_index):
        """Test searching empty index."""
        results = await bm25_index.search("test query", k=5)
        assert len(results) == 0

    async def test_update_document(self, bm25_index):
        """Test updating document in BM25 index."""
        docs = [{"id": "doc1", "content": "original content"}]
        await bm25_index.add_documents(docs)

        # Update document
        updated_doc = {"id": "doc1", "content": "updated machine learning content"}
        await bm25_index.update_document("doc1", updated_doc)

        # Search should find updated content
        results = await bm25_index.search("machine learning", k=1)
        assert len(results) == 1
        assert results[0]["doc_id"] == "doc1"

    async def test_delete_document(self, bm25_index):
        """Test deleting document from BM25 index."""
        docs = [
            {"id": "doc1", "content": "keep this document"},
            {"id": "doc2", "content": "delete this document"}
        ]
        await bm25_index.add_documents(docs)

        await bm25_index.delete_document("doc2")

        # Search should not find deleted document
        results = await bm25_index.search("delete", k=10)
        doc_ids = [r["doc_id"] for r in results]
        assert "doc2" not in doc_ids

    def test_get_stats(self, bm25_index):
        """Test getting BM25 statistics."""
        stats = bm25_index.get_stats()

        assert "document_count" in stats
        assert "index_type" in stats
        assert stats["index_type"] == "bm25"


class TestHybridRanker:
    """Test hybrid ranking system."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(
            bm25_weight=0.3,
            vector_weight=0.7,
            enable_learning_to_rank=True
        )

    @pytest.fixture
    def ranker(self, config):
        """Create test hybrid ranker."""
        return HybridRanker(config)

    def test_ranker_initialization(self, ranker, config):
        """Test ranker initialization."""
        assert ranker.config == config
        assert ranker.bm25_weight == 0.3
        assert ranker.vector_weight == 0.7

    async def test_fuse_scores_simple(self, ranker):
        """Test simple score fusion."""
        bm25_results = [
            {"doc_id": "doc1", "score": 0.8},
            {"doc_id": "doc2", "score": 0.6},
            {"doc_id": "doc3", "score": 0.4}
        ]

        vector_results = [
            {"doc_id": "doc2", "score": 0.9},
            {"doc_id": "doc1", "score": 0.5},
            {"doc_id": "doc4", "score": 0.3}
        ]

        fused = await ranker.fuse_scores(bm25_results, vector_results)

        # Should combine results from both systems
        assert len(fused) >= 3
        # Scores should be weighted combination
        doc1_result = next(r for r in fused if r["doc_id"] == "doc1")
        expected_score = 0.3 * 0.8 + 0.7 * 0.5  # BM25 weight * score + vector weight * score
        assert abs(doc1_result["score"] - expected_score) < 0.01

    async def test_fuse_scores_rrf(self, config):
        """Test Reciprocal Rank Fusion."""
        config.fusion_method = "rrf"
        ranker = HybridRanker(config)

        bm25_results = [
            {"doc_id": "doc1", "score": 0.9},
            {"doc_id": "doc2", "score": 0.7},
            {"doc_id": "doc3", "score": 0.5}
        ]

        vector_results = [
            {"doc_id": "doc3", "score": 0.8},
            {"doc_id": "doc1", "score": 0.6},
            {"doc_id": "doc2", "score": 0.4}
        ]

        fused = await ranker.fuse_scores(bm25_results, vector_results)

        # RRF should consider rank positions, not just raw scores
        assert len(fused) == 3
        # Results should be sorted by RRF score
        assert fused[0]["score"] >= fused[1]["score"] >= fused[2]["score"]

    async def test_normalize_scores(self, ranker):
        """Test score normalization."""
        results = [
            {"doc_id": "doc1", "score": 10.0},
            {"doc_id": "doc2", "score": 5.0},
            {"doc_id": "doc3", "score": 2.0}
        ]

        normalized = await ranker._normalize_scores(results)

        # Scores should be between 0 and 1
        assert all(0 <= r["score"] <= 1 for r in normalized)
        # Highest score should be 1.0
        assert max(r["score"] for r in normalized) == 1.0
        # Relative ordering should be preserved
        assert normalized[0]["doc_id"] == "doc1"

    async def test_rerank_with_cross_encoder(self, ranker):
        """Test reranking with cross-encoder."""
        # Mock cross-encoder reranking
        with patch.object(ranker, '_cross_encoder_rerank') as mock_rerank:
            mock_rerank.return_value = [
                {"doc_id": "doc2", "score": 0.95},
                {"doc_id": "doc1", "score": 0.85},
                {"doc_id": "doc3", "score": 0.75}
            ]

            query = "test query"
            candidates = [
                {"doc_id": "doc1", "score": 0.8, "content": "content1"},
                {"doc_id": "doc2", "score": 0.6, "content": "content2"},
                {"doc_id": "doc3", "score": 0.4, "content": "content3"}
            ]

            reranked = await ranker.rerank(query, candidates)

            assert len(reranked) == 3
            assert reranked[0]["doc_id"] == "doc2"  # Reordered by cross-encoder
            mock_rerank.assert_called_once_with(query, candidates)


class TestHybridVectorStore:
    """Test complete hybrid vector store."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(
            embedding_dimension=128,  # Smaller for testing
            batch_size=4
        )

    @pytest.fixture
    def mock_provider(self):
        """Create mock embedding provider."""
        provider = AsyncMock(spec=VoyageAPIClient)
        provider.embed_texts.return_value = [
            np.random.random(128).astype(np.float32).tolist()
            for _ in range(4)
        ]
        return provider

    @pytest.fixture
    async def vector_store(self, config, mock_provider):
        """Create test hybrid vector store."""
        store = HybridVectorStore(config, api_client=mock_provider)
        await store.initialize()
        return store

    async def test_store_initialization(self, vector_store, config):
        """Test vector store initialization."""
        assert vector_store.config == config
        assert vector_store.doc_store is not None
        assert vector_store.vector_index is not None
        assert vector_store.lexical_index is not None
        assert vector_store.ranker is not None

    async def test_add_documents(self, vector_store, mock_provider):
        """Test adding documents to hybrid store."""
        docs = [
            {"id": "doc1", "content": "machine learning algorithms"},
            {"id": "doc2", "content": "deep neural networks"},
            {"id": "doc3", "content": "natural language processing"}
        ]

        await vector_store.add_documents(docs)

        # Should have called embedding provider
        mock_provider.embed_texts.assert_called_once()

        # Should have 3 documents in all indexes
        stats = vector_store.get_stats()
        assert stats["documents"]["document_count"] == 3

    async def test_hybrid_search(self, vector_store, mock_provider):
        """Test hybrid search functionality."""
        # Add test documents first
        docs = [
            {"id": "doc1", "content": "machine learning algorithms and models"},
            {"id": "doc2", "content": "deep neural network architectures"},
            {"id": "doc3", "content": "machine learning with deep networks"}
        ]
        await vector_store.add_documents(docs)

        # Mock query embedding
        mock_provider.embed_texts.return_value = [np.random.random(128).tolist()]

        # Perform hybrid search
        results = await vector_store.hybrid_search("machine learning", k=2)

        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(hasattr(r, 'doc_id') and hasattr(r, 'score') for r in results)

    async def test_vector_search_only(self, vector_store, mock_provider):
        """Test vector-only search."""
        docs = [{"id": "doc1", "content": "test document"}]
        await vector_store.add_documents(docs)

        query_vector = np.random.random(128)
        results = await vector_store.vector_search(query_vector, k=1)

        assert len(results) <= 1
        if results:
            assert isinstance(results[0], SearchResult)

    async def test_lexical_search_only(self, vector_store):
        """Test lexical-only search."""
        docs = [
            {"id": "doc1", "content": "machine learning tutorial"},
            {"id": "doc2", "content": "deep learning guide"}
        ]
        await vector_store.add_documents(docs)

        results = await vector_store.lexical_search("machine learning", k=1)

        assert len(results) <= 1
        if results:
            assert isinstance(results[0], SearchResult)
            assert results[0].doc_id == "doc1"

    async def test_update_document(self, vector_store, mock_provider):
        """Test updating existing document."""
        # Add initial document
        docs = [{"id": "doc1", "content": "original content"}]
        await vector_store.add_documents(docs)

        # Update document
        updated_doc = {"id": "doc1", "content": "updated machine learning content"}
        await vector_store.update_document("doc1", updated_doc)

        # Search should find updated content
        results = await vector_store.lexical_search("machine learning", k=1)
        assert len(results) == 1
        assert results[0].doc_id == "doc1"

    async def test_delete_document(self, vector_store, mock_provider):
        """Test deleting document."""
        docs = [
            {"id": "doc1", "content": "keep this"},
            {"id": "doc2", "content": "delete this"}
        ]
        await vector_store.add_documents(docs)

        await vector_store.delete_document("doc2")

        # Document should be deleted from all indexes
        stats = vector_store.get_stats()
        assert stats["documents"]["document_count"] == 1

    async def test_save_and_load(self, vector_store, tmp_path):
        """Test saving and loading vector store."""
        # Add some data
        docs = [{"id": "doc1", "content": "test document"}]
        await vector_store.add_documents(docs)

        # Save store
        store_path = tmp_path / "test_store"
        await vector_store.save(str(store_path))

        # Create new store and load
        new_config = vector_store.config
        new_store = HybridVectorStore(new_config)
        await new_store.load(str(store_path))

        # Should have same data
        stats = new_store.get_stats()
        assert stats["documents"]["document_count"] == 1

    async def test_search_with_filters(self, vector_store, mock_provider):
        """Test search with metadata filters."""
        docs = [
            {"id": "doc1", "content": "document 1", "metadata": {"type": "code", "lang": "python"}},
            {"id": "doc2", "content": "document 2", "metadata": {"type": "text", "lang": "english"}},
            {"id": "doc3", "content": "document 3", "metadata": {"type": "code", "lang": "javascript"}}
        ]
        await vector_store.add_documents(docs)

        # Search with metadata filter
        filters = {"type": "code"}
        results = await vector_store.hybrid_search("document", k=10, filters=filters)

        # Should only return code documents
        assert len(results) == 2
        for result in results:
            doc = await vector_store.get_document(result.doc_id)
            assert doc["metadata"]["type"] == "code"

    def test_get_comprehensive_stats(self, vector_store):
        """Test getting comprehensive storage statistics."""
        stats = vector_store.get_stats()

        # Should have stats for all components
        assert "documents" in stats
        assert "vector_index" in stats
        assert "lexical_index" in stats
        assert "ranker" in stats

        # Should include health metrics
        assert "storage_health" in stats
        assert "last_updated" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dopemux.embeddings.storage", "--cov-report=term-missing"])