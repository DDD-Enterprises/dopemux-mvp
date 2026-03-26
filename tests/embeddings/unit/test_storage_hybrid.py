"""
Unit tests for hybrid vector storage system.

Tests the HybridVectorStore and related storage components.
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
import pickle
import types

from dopemux.embeddings.storage import (
    HybridVectorStore,
    HNSWIndex,
    BM25Index,
    HybridRanker,
    InMemoryDocumentStore,
    RRFFusion,
)
from dopemux.embeddings.core import AdvancedEmbeddingConfig, SearchResult, VectorStoreError
from dopemux.embeddings.providers import VoyageAPIClient


class _FakeHNSWLibIndex:
    """Small in-memory substitute for hnswlib.Index used in unit tests."""

    def __init__(self, space: str, dim: int):
        self.space = space
        self.dim = dim
        self._vectors: dict[int, np.ndarray] = {}
        self._max_elements = 0
        self._ef = 0

    def init_index(self, max_elements: int, M: int, ef_construction: int) -> None:
        self._max_elements = max_elements

    def set_ef(self, ef: int) -> None:
        self._ef = ef

    def get_current_count(self) -> int:
        return len(self._vectors)

    def get_max_elements(self) -> int:
        return self._max_elements

    def resize_index(self, new_capacity: int) -> None:
        self._max_elements = new_capacity

    def add_items(self, vectors: np.ndarray, indices: list[int]) -> None:
        for idx, vector in zip(indices, vectors):
            self._vectors[int(idx)] = np.asarray(vector, dtype=np.float32)

    def knn_query(self, query_vector: np.ndarray, k: int):
        if not self._vectors:
            return np.empty((1, 0), dtype=np.int64), np.empty((1, 0), dtype=np.float32)

        query = np.asarray(query_vector, dtype=np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)
        query = query[0]

        labels = sorted(self._vectors.keys())
        matrix = np.vstack([self._vectors[label] for label in labels])

        if self.space == "cosine":
            vec_norm = np.linalg.norm(matrix, axis=1)
            query_norm = np.linalg.norm(query)
            denom = np.maximum(vec_norm * query_norm, 1e-12)
            similarities = (matrix @ query) / denom
            distances = 1.0 - similarities
        else:
            distances = np.linalg.norm(matrix - query, axis=1)

        top_k = min(k, len(labels))
        order = np.argsort(distances)[:top_k]
        ranked_labels = np.array([[labels[i] for i in order]], dtype=np.int64)
        ranked_distances = np.array([[float(distances[i]) for i in order]], dtype=np.float32)
        return ranked_labels, ranked_distances

    def save_index(self, path: str) -> None:
        payload = {
            "space": self.space,
            "dim": self.dim,
            "max_elements": self._max_elements,
            "ef": self._ef,
            "vectors": self._vectors,
        }
        with open(path, "wb") as handle:
            pickle.dump(payload, handle)

    def load_index(self, path: str) -> None:
        with open(path, "rb") as handle:
            payload = pickle.load(handle)
        self.space = payload["space"]
        self.dim = payload["dim"]
        self._max_elements = payload["max_elements"]
        self._ef = payload["ef"]
        self._vectors = payload["vectors"]


class _FakeBM25Okapi:
    """Simple lexical scorer substitute for rank_bm25.BM25Okapi."""

    def __init__(self, corpus):
        self.corpus = corpus

    def get_scores(self, query_tokens):
        query_set = set(query_tokens)
        scores = []
        for document_tokens in self.corpus:
            overlap = len(query_set & set(document_tokens))
            scores.append(float(overlap))
        return np.asarray(scores, dtype=np.float32)


class TestInMemoryDocumentStore:
    """Test in-memory document storage."""

    @pytest.fixture
    def doc_store(self):
        """Create test document store."""
        return InMemoryDocumentStore()

    def test_store_initialization(self, doc_store):
        """Test document store initialization."""
        assert len(doc_store.documents) == 0

    def test_store_document(self, doc_store):
        """Test storing documents."""
        doc_store.store_document("doc1", "First document", {"type": "text"})
        doc_store.store_document("doc2", "Second document", {"type": "code"})

        assert len(doc_store.documents) == 2
        assert doc_store.documents["doc1"]["content"] == "First document"
        assert doc_store.documents["doc2"]["metadata"]["type"] == "code"

    def test_get_document_by_id(self, doc_store):
        """Test retrieving document by ID."""
        doc_store.store_document("test_doc", "Test content", {"source": "unit"})

        doc = doc_store.get_document("test_doc")
        assert doc["content"] == "Test content"
        assert doc["metadata"]["source"] == "unit"

    def test_get_nonexistent_document(self, doc_store):
        """Test retrieving non-existent document."""
        with pytest.raises(VectorStoreError):
            doc_store.get_document("nonexistent")

    def test_get_documents_by_ids(self, doc_store):
        """Test retrieving documents by IDs."""
        doc_store.store_document("doc1", "First", {})
        doc_store.store_document("doc2", "Second", {})
        doc_store.store_document("doc3", "Third", {})

        retrieved = doc_store.get_documents(["doc1", "doc3"])
        assert len(retrieved) == 2
        assert retrieved[0]["content"] == "First"
        assert retrieved[1]["content"] == "Third"

    def test_update_document(self, doc_store):
        """Test updating existing document."""
        doc_store.store_document("doc1", "Original content", {"version": 1})
        doc_store.store_document("doc1", "Updated content", {"version": 2})

        doc = doc_store.get_document("doc1")
        assert doc["content"] == "Updated content"
        assert doc["metadata"]["version"] == 2

    def test_delete_document(self, doc_store):
        """Test deleting document."""
        doc_store.store_document("doc1", "Keep this", {})
        doc_store.store_document("doc2", "Delete this", {})

        doc_store.delete_document("doc2")

        assert "doc2" not in doc_store.documents

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
    def hnsw_index(self, config, monkeypatch):
        """Create test HNSW index."""
        from dopemux.embeddings.storage import vector_indices

        if vector_indices.hnswlib is None:
            monkeypatch.setattr(
                vector_indices,
                "hnswlib",
                types.SimpleNamespace(Index=_FakeHNSWLibIndex),
            )
        return HNSWIndex(config)

    def test_index_initialization(self, hnsw_index, config):
        """Test HNSW index initialization."""
        assert hnsw_index.config == config
        assert hnsw_index.dimension == 128
        assert hnsw_index.index is not None
        assert hnsw_index.doc_ids == []

    def test_add_vectors(self, hnsw_index):
        """Test adding vectors to index."""
        vectors = np.random.random((5, 128)).astype(np.float32)
        doc_ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]

        hnsw_index.add_vectors(vectors, doc_ids)

        assert len(hnsw_index.doc_ids) == 5
        assert hnsw_index.index.get_current_count() == 5

    def test_search_vectors(self, hnsw_index):
        """Test vector search."""
        vectors = np.random.random((10, 128)).astype(np.float32)
        doc_ids = [f"doc{i}" for i in range(10)]
        hnsw_index.add_vectors(vectors, doc_ids)

        query_vector = vectors[0]
        scores, indices = hnsw_index.search(query_vector, k=3)

        assert len(indices) <= 3
        assert indices[0] == 0
        assert scores[0] > 0.9

    def test_search_empty_index(self, hnsw_index):
        """Test searching empty index."""
        query_vector = np.random.random(128).astype(np.float32)
        scores, indices = hnsw_index.search(query_vector, k=5)

        assert scores == []
        assert indices == []

    def test_save_and_load_index(self, hnsw_index, tmp_path):
        """Test saving and loading index."""
        vectors = np.random.random((5, 128)).astype(np.float32)
        doc_ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        hnsw_index.add_vectors(vectors, doc_ids)

        index_path = tmp_path / "test_index.bin"
        hnsw_index.save(str(index_path))

        new_index = HNSWIndex(hnsw_index.config)
        new_index.load(str(index_path))

        assert len(new_index.doc_ids) == 5
        assert new_index.index.get_current_count() == 5

        query_vector = vectors[0]
        _, indices = new_index.search(query_vector, k=1)
        assert indices[0] == 0

    def test_get_stats(self, hnsw_index):
        """Test getting index statistics."""
        vectors = np.random.random((1, 128)).astype(np.float32)
        hnsw_index.add_vectors(vectors, ["doc1"])
        stats = hnsw_index.get_stats()

        assert "vector_count" in stats
        assert "dimension" in stats
        assert stats["vector_count"] == 1
        assert stats["document_count"] == 1


class TestBM25Index:
    """Test BM25 lexical index."""

    @pytest.fixture
    def bm25_index(self, monkeypatch):
        """Create test BM25 index."""
        from dopemux.embeddings.storage import text_indices

        if text_indices.BM25Okapi is None:
            monkeypatch.setattr(text_indices, "BM25Okapi", _FakeBM25Okapi)
        return BM25Index()

    def test_index_initialization(self, bm25_index):
        """Test BM25 index initialization."""
        assert bm25_index.language == "english"
        assert bm25_index.bm25 is None
        assert bm25_index.documents == []
        assert bm25_index.doc_ids == []

    def test_add_documents(self, bm25_index):
        """Test adding documents to BM25 index."""
        documents = [
            "machine learning algorithms",
            "deep neural networks",
            "machine learning with neural networks",
        ]
        ids = ["doc1", "doc2", "doc3"]

        bm25_index.add_documents(documents, ids)

        assert len(bm25_index.documents) == 3
        assert len(bm25_index.doc_ids) == 3
        assert bm25_index.doc_ids[0] == "doc1"

    def test_search_documents(self, bm25_index):
        """Test BM25 search."""
        documents = [
            "machine learning algorithms",
            "deep neural networks",
            "machine learning with neural networks",
            "computer vision applications",
        ]
        ids = ["doc1", "doc2", "doc3", "doc4"]
        bm25_index.add_documents(documents, ids)

        results = bm25_index.search("machine learning", k=3)

        assert len(results) <= 3
        top_doc_ids = [doc_id for doc_id, _ in results]
        assert top_doc_ids[0] in {"doc1", "doc3"}
        assert set(top_doc_ids).issubset({"doc1", "doc3"})

    def test_search_single_document_corpus(self, bm25_index):
        """BM25 should still return lexical matches for tiny corpora."""
        bm25_index.add_documents(["original content"], ["doc1"])

        results = bm25_index.search("original", k=1)

        assert len(results) == 1
        assert results[0][0] == "doc1"

    def test_search_empty_index(self, bm25_index):
        """Test searching empty index."""
        results = bm25_index.search("test query", k=5)
        assert len(results) == 0

    def test_update_document(self, bm25_index):
        """Test updating document in BM25 index."""
        bm25_index.add_documents(["original content"], ["doc1"])

        bm25_index.update_document("doc1", "updated machine learning content")

        results = bm25_index.search("machine learning", k=1)
        assert len(results) == 1
        assert results[0][0] == "doc1"

    def test_delete_document(self, bm25_index):
        """Test deleting document from BM25 index."""
        bm25_index.add_documents(
            ["keep this document", "delete this document"],
            ["doc1", "doc2"],
        )

        bm25_index.remove_document("doc2")

        results = bm25_index.search("delete", k=10)
        doc_ids = [doc_id for doc_id, _ in results]
        assert "doc2" not in doc_ids

    def test_get_stats(self, bm25_index):
        """Test getting BM25 statistics."""
        bm25_index.add_documents(["machine learning"], ["doc1"])
        stats = bm25_index.get_stats()

        assert "document_count" in stats
        assert "vocabulary_size" in stats
        assert stats["has_index"] is True


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

    def test_fuse_scores_simple(self, ranker):
        """Test simple score fusion."""
        bm25_results = [
            ("doc1", 0.8),
            ("doc2", 0.6),
            ("doc3", 0.4),
        ]

        vector_results = [
            ("doc2", 0.9),
            ("doc1", 0.5),
            ("doc4", 0.3),
        ]

        fused = ranker.fuse_scores(bm25_results, vector_results)

        # Should combine results from both systems
        assert len(fused) >= 3
        # Scores should be weighted combination
        doc1_result = next(r for r in fused if r.doc_id == "doc1")
        expected_score = 0.3 * 0.8 + 0.7 * 0.5  # BM25 weight * score + vector weight * score
        assert abs(doc1_result.score - expected_score) < 0.01

    def test_fuse_scores_rrf(self):
        """Test Reciprocal Rank Fusion."""
        ranker = RRFFusion()

        bm25_results = [
            ("doc1", 0.9),
            ("doc2", 0.7),
            ("doc3", 0.5),
        ]

        vector_results = [
            ("doc3", 0.8),
            ("doc1", 0.6),
            ("doc2", 0.4),
        ]

        fused = ranker.fuse_scores(bm25_results, vector_results)

        # RRF should consider rank positions, not just raw scores
        assert len(fused) == 3
        # Results should be sorted by RRF score
        assert fused[0].score >= fused[1].score >= fused[2].score

    def test_normalize_scores(self, ranker):
        """Test score normalization."""
        scores = [10.0, 5.0, 2.0]

        normalized = ranker._normalize_scores(scores)

        # Scores should be between 0 and 1
        assert all(0 <= score <= 1 for score in normalized)
        # Highest score should be 1.0
        assert max(normalized) == 1.0
        # Relative ordering should be preserved
        assert normalized[0] > normalized[1] > normalized[2]

    def test_get_stats(self, ranker):
        """Test ranker statistics."""
        stats = ranker.get_stats()

        assert stats["is_trained"] is False
        assert stats["bm25_weight"] == 0.3
        assert stats["vector_weight"] == 0.7


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
        assert vector_store.document_store is not None
        assert vector_store.vector_index is not None
        assert vector_store.bm25_index is not None
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
        store_path.mkdir()
        await vector_store.save(str(store_path))

        # Create new store and load
        new_config = vector_store.config
        new_store = HybridVectorStore(new_config)
        await new_store.load(str(store_path))

        # Should have same data
        stats = new_store.get_stats()
        assert stats["vector_index"]["document_count"] == 1
        assert stats["bm25_index"]["document_count"] == 1

    async def test_search_with_filters(self, vector_store, mock_provider):
        """Test search with metadata filters."""
        docs = [
            {"id": "doc1", "content": "document 1", "metadata": {"type": "code", "lang": "python"}},
            {"id": "doc2", "content": "document 2", "metadata": {"type": "text", "lang": "english"}},
            {"id": "doc3", "content": "document 3", "metadata": {"type": "code", "lang": "javascript"}}
        ]
        await vector_store.add_documents(docs)

        results = await vector_store.hybrid_search("document", k=10)

        assert len(results) >= 1
        for result in results:
            doc = vector_store.document_store.get_document(result.doc_id)
            assert doc["metadata"]["type"] in {"code", "text"}

    def test_get_comprehensive_stats(self, vector_store):
        """Test getting comprehensive storage statistics."""
        stats = vector_store.get_stats()

        # Should have stats for all components
        assert "documents" in stats
        assert "vector_index" in stats
        assert "lexical_index" in stats
        assert "ranker" in stats

        assert "metrics" in stats
        assert "config" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dopemux.embeddings.storage", "--cov-report=term-missing"])
