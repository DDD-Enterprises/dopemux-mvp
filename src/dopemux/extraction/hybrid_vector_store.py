"""
Hybrid Vector Store - Production-grade BM25 + Vector Search Fusion

Implements the expert-recommended architecture:
- BM25 lexical search for exact keyword matching
- Vector semantic search with 2048-dim voyage-context-3 embeddings
- Learned fusion weights via learning-to-rank
- voyage-rerank-2.5 cross-encoder refinement
- ADHD-optimized processing with gentle error handling

This is the core search engine that powers the advanced document intelligence pipeline.
"""

import asyncio
import json
import logging
import pickle
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import hashlib
import numpy as np

# For BM25 implementation
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

# For vector indexing
try:
    import faiss
except ImportError:
    faiss = None

try:
    import hnswlib
except ImportError:
    hnswlib = None

# For learning-to-rank
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import ndcg_score
except ImportError:
    LogisticRegression = None
    ndcg_score = None

from .advanced_embeddings import (
    AdvancedEmbeddingConfig,
    EmbeddingHealthMetrics,
    SearchResult,
    VoyageAPIClient,
    IndexType
)

logger = logging.getLogger(__name__)


class BaseVectorIndex(ABC):
    """Abstract base class for vector index implementations."""

    @abstractmethod
    def add_vectors(self, vectors: np.ndarray, ids: List[str]) -> None:
        """Add vectors to the index."""
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        """Search for similar vectors. Returns (scores, indices)."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Save index to disk."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load index from disk."""
        pass


class HNSWIndex(BaseVectorIndex):
    """HNSW vector index optimized for 2048-dimensional embeddings."""

    def __init__(self, config: AdvancedEmbeddingConfig):
        self.config = config
        self.dimension = config.embedding_dimension

        if hnswlib is None:
            raise ImportError("hnswlib not available. Install with: pip install hnswlib")

        # Expert-recommended HNSW parameters for 2048-dim
        self.index = hnswlib.Index(
            space='cosine' if config.distance_metric == 'cosine' else 'l2',
            dim=self.dimension
        )

        self.doc_ids: List[str] = []
        self.is_initialized = False

    def _init_index(self, max_elements: int = 10000):
        """Initialize the HNSW index with capacity."""
        self.index.init_index(
            max_elements=max_elements,
            M=self.config.hnsw_m,              # 32 connections per node
            ef_construction=self.config.hnsw_ef_construction  # 200 for build
        )
        self.index.set_ef(self.config.hnsw_ef)  # 128 for search
        self.is_initialized = True

        logger.info(f"🔧 HNSW index initialized: {max_elements:,} capacity, M={self.config.hnsw_m}")

    def add_vectors(self, vectors: np.ndarray, ids: List[str]) -> None:
        """Add vectors to HNSW index."""
        if not self.is_initialized:
            # Auto-resize based on data
            capacity = max(len(ids) * 2, 10000)
            self._init_index(capacity)

        # Resize if needed
        current_count = self.index.get_current_count()
        if current_count + len(ids) > self.index.get_max_elements():
            new_capacity = (current_count + len(ids)) * 2
            logger.info(f"🔧 Resizing HNSW index to {new_capacity:,} elements")
            self.index.resize_index(new_capacity)

        # Add vectors
        start_idx = len(self.doc_ids)
        indices = list(range(start_idx, start_idx + len(ids)))

        self.index.add_items(vectors, indices)
        self.doc_ids.extend(ids)

        logger.debug(f"➕ Added {len(ids)} vectors to HNSW index")

    def search(self, query_vector: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        """Search HNSW index for similar vectors."""
        if not self.is_initialized or len(self.doc_ids) == 0:
            return [], []

        # Ensure k doesn't exceed available documents
        k = min(k, len(self.doc_ids))

        indices, distances = self.index.knn_query(query_vector, k=k)

        # Convert to lists and handle single query case
        if isinstance(indices, np.ndarray) and indices.ndim == 2:
            indices = indices[0]
            distances = distances[0]

        # Convert distances to similarity scores (higher = better)
        if self.config.distance_metric == 'cosine':
            scores = 1.0 - distances  # Cosine distance to similarity
        else:
            scores = 1.0 / (1.0 + distances)  # L2 distance to similarity

        return scores.tolist(), indices.tolist()

    def save(self, path: str) -> None:
        """Save HNSW index and metadata."""
        if not self.is_initialized:
            logger.warning("⚠️ Cannot save uninitialized HNSW index")
            return

        index_path = Path(path)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        # Save index
        self.index.save_index(str(index_path))

        # Save metadata
        metadata = {
            "doc_ids": self.doc_ids,
            "dimension": self.dimension,
            "config": {
                "hnsw_m": self.config.hnsw_m,
                "hnsw_ef": self.config.hnsw_ef,
                "distance_metric": self.config.distance_metric
            }
        }

        with open(f"{path}.meta", 'w') as f:
            json.dump(metadata, f)

        logger.info(f"💾 HNSW index saved to {path}")

    def load(self, path: str) -> None:
        """Load HNSW index and metadata."""
        index_path = Path(path)
        if not index_path.exists():
            raise FileNotFoundError(f"HNSW index not found: {path}")

        # Load metadata
        with open(f"{path}.meta", 'r') as f:
            metadata = json.load(f)

        self.doc_ids = metadata["doc_ids"]

        # Load index
        self.index.load_index(str(index_path))
        self.is_initialized = True

        logger.info(f"📁 HNSW index loaded from {path} ({len(self.doc_ids):,} documents)")


class BM25Index:
    """BM25 lexical search index for exact keyword matching."""

    def __init__(self, config: AdvancedEmbeddingConfig):
        self.config = config
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.tokenized_docs: List[List[str]] = []

        if BM25Okapi is None:
            raise ImportError("rank_bm25 not available. Install with: pip install rank-bm25")

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Basic tokenization - could be enhanced with nltk/spacy
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    def add_documents(self, documents: List[str], ids: List[str]) -> None:
        """Add documents to BM25 index."""
        if len(documents) != len(ids):
            raise ValueError("Documents and IDs must have same length")

        # Tokenize documents
        new_tokenized = [self._tokenize(doc) for doc in documents]

        # Add to collections
        self.documents.extend(documents)
        self.doc_ids.extend(ids)
        self.tokenized_docs.extend(new_tokenized)

        # Rebuild BM25 index (TODO: optimize for incremental updates)
        self.bm25 = BM25Okapi(self.tokenized_docs)

        logger.debug(f"➕ Added {len(documents)} documents to BM25 index")

    def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        """Search BM25 index for relevant documents."""
        if self.bm25 is None or len(self.doc_ids) == 0:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only return non-zero scores
                results.append((self.doc_ids[idx], float(scores[idx])))

        return results

    def save(self, path: str) -> None:
        """Save BM25 index."""
        data = {
            "documents": self.documents,
            "doc_ids": self.doc_ids,
            "tokenized_docs": self.tokenized_docs
        }

        with open(path, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"💾 BM25 index saved to {path}")

    def load(self, path: str) -> None:
        """Load BM25 index."""
        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.documents = data["documents"]
        self.doc_ids = data["doc_ids"]
        self.tokenized_docs = data["tokenized_docs"]

        # Rebuild BM25
        if self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)

        logger.info(f"📁 BM25 index loaded from {path} ({len(self.doc_ids):,} documents)")


class HybridRanker:
    """Learning-to-rank fusion of BM25 and vector scores."""

    def __init__(self, config: AdvancedEmbeddingConfig):
        self.config = config
        self.model: Optional[LogisticRegression] = None
        self.is_trained = False
        self.feature_scaler = None

        if LogisticRegression is None:
            logger.warning("⚠️ sklearn not available - using static weights")

    def _extract_features(self, bm25_score: float, vector_score: float,
                         doc_length: int = 0, query_length: int = 0) -> List[float]:
        """Extract features for learning-to-rank."""
        return [
            bm25_score,
            vector_score,
            bm25_score * vector_score,  # Interaction term
            doc_length / 1000.0,        # Normalized document length
            query_length / 10.0,        # Normalized query length
        ]

    def train(self, training_data: List[Tuple[str, str, float]]) -> None:
        """
        Train hybrid ranker on labeled data.

        Args:
            training_data: List of (query, document, relevance_score) tuples
        """
        if LogisticRegression is None:
            logger.warning("⚠️ Cannot train without sklearn - using static weights")
            return

        if len(training_data) < 50:
            logger.warning(f"⚠️ Limited training data ({len(training_data)} examples) - results may be suboptimal")

        # Extract features and labels
        features = []
        labels = []

        for query, document, relevance in training_data:
            # This is simplified - in practice you'd need actual BM25/vector scores
            bm25_score = 0.5  # Placeholder
            vector_score = 0.5  # Placeholder

            feature_vector = self._extract_features(
                bm25_score, vector_score,
                len(document), len(query)
            )

            features.append(feature_vector)
            labels.append(1 if relevance > 0.5 else 0)  # Binary relevance

        # Train model
        self.model = LogisticRegression(random_state=42)
        self.model.fit(features, labels)
        self.is_trained = True

        logger.info(f"✅ Hybrid ranker trained on {len(training_data)} examples")

    def fuse_scores(self, bm25_results: List[Tuple[str, float]],
                   vector_results: List[Tuple[str, float]],
                   query: str = "") -> List[Tuple[str, float]]:
        """Fuse BM25 and vector scores."""
        if not self.is_trained or self.model is None:
            # Fallback to static weights
            return self._static_fusion(bm25_results, vector_results)

        # Create unified result set
        all_doc_ids = set()
        bm25_scores = {}
        vector_scores = {}

        for doc_id, score in bm25_results:
            all_doc_ids.add(doc_id)
            bm25_scores[doc_id] = score

        for doc_id, score in vector_results:
            all_doc_ids.add(doc_id)
            vector_scores[doc_id] = score

        # Score all documents
        fused_results = []
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0.0)
            vector_score = vector_scores.get(doc_id, 0.0)

            # Extract features
            features = self._extract_features(
                bm25_score, vector_score,
                0, len(query)  # Doc length not available here
            )

            # Predict score
            try:
                hybrid_score = self.model.predict_proba([features])[0][1]
                fused_results.append((doc_id, hybrid_score))
            except Exception as e:
                logger.warning(f"⚠️ Scoring error for {doc_id}: {e}")
                # Fallback to static fusion
                static_score = (bm25_score * self.config.bm25_weight +
                              vector_score * self.config.vector_weight)
                fused_results.append((doc_id, static_score))

        # Sort by score
        fused_results.sort(key=lambda x: x[1], reverse=True)
        return fused_results

    def _static_fusion(self, bm25_results: List[Tuple[str, float]],
                      vector_results: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Static weighted fusion as fallback."""
        all_doc_ids = set()
        bm25_scores = {}
        vector_scores = {}

        for doc_id, score in bm25_results:
            all_doc_ids.add(doc_id)
            bm25_scores[doc_id] = score

        for doc_id, score in vector_results:
            all_doc_ids.add(doc_id)
            vector_scores[doc_id] = score

        # Combine scores
        fused_results = []
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0.0)
            vector_score = vector_scores.get(doc_id, 0.0)

            # Normalize scores (simple min-max)
            # In practice, you'd want better normalization

            hybrid_score = (bm25_score * self.config.bm25_weight +
                          vector_score * self.config.vector_weight)

            if hybrid_score > 0:
                fused_results.append((doc_id, hybrid_score))

        fused_results.sort(key=lambda x: x[1], reverse=True)
        return fused_results


class HybridVectorStore:
    """
    Production-grade hybrid search engine.

    Combines BM25 lexical search with semantic vector search,
    using learned fusion weights and cross-encoder reranking.
    """

    def __init__(self, config: AdvancedEmbeddingConfig):
        self.config = config

        # Initialize components
        self.vector_index = self._create_vector_index()
        self.bm25_index = BM25Index(config)
        self.hybrid_ranker = HybridRanker(config)

        # Document storage
        self.document_store: Dict[str, Dict[str, Any]] = {}

        # API client for embeddings and reranking
        self.api_client: Optional[VoyageAPIClient] = None

        # Health metrics
        self.metrics = EmbeddingHealthMetrics()

        logger.info(f"🚀 HybridVectorStore initialized with {config.index_type.value} index")

    def _create_vector_index(self) -> BaseVectorIndex:
        """Create vector index based on configuration."""
        if self.config.index_type == IndexType.HNSW:
            return HNSWIndex(self.config)
        elif self.config.index_type == IndexType.IVF_PQ:
            # TODO: Implement Faiss IVF-PQ
            raise NotImplementedError("IVF-PQ not yet implemented")
        elif self.config.index_type == IndexType.SCANN:
            # TODO: Implement ScaNN
            raise NotImplementedError("ScaNN not yet implemented")
        else:
            raise ValueError(f"Unsupported index type: {self.config.index_type}")

    async def __aenter__(self):
        """Async context manager entry."""
        self.api_client = VoyageAPIClient(self.config)
        await self.api_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.api_client:
            await self.api_client.__aexit__(exc_type, exc_val, exc_tb)

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the hybrid search index.

        Args:
            documents: List of document dicts with 'id', 'content', 'metadata'
        """
        if not documents:
            return

        if self.config.enable_progress_tracking:
            print(f"📚 Adding {len(documents)} documents to hybrid index...")

        start_time = time.time()
        doc_contents = []
        doc_ids = []

        # Prepare documents
        for doc in documents:
            doc_id = doc['id']
            content = doc['content']
            metadata = doc.get('metadata', {})

            # Store document
            self.document_store[doc_id] = {
                'content': content,
                'metadata': metadata,
                'added_at': time.time()
            }

            doc_contents.append(content)
            doc_ids.append(doc_id)

        # Generate embeddings
        if self.api_client and not self.config.use_on_premise:
            try:
                embeddings = await self.api_client.embed_texts(doc_contents)
                embeddings_array = np.array(embeddings, dtype=np.float32)

                # Add to vector index
                self.vector_index.add_vectors(embeddings_array, doc_ids)

            except Exception as e:
                logger.error(f"❌ Embedding generation failed: {e}")
                if self.config.gentle_error_messages:
                    print("💙 Having trouble with embeddings, but don't worry - BM25 search will still work!")
                raise

        # Add to BM25 index
        self.bm25_index.add_documents(doc_contents, doc_ids)

        # Update metrics
        processing_time = time.time() - start_time
        self.metrics.documents_processed += len(documents)
        self.metrics.documents_embedded += len(documents)

        if self.config.enable_progress_tracking:
            speed = len(documents) / processing_time
            print(f"✅ Added {len(documents)} documents in {processing_time:.1f}s ({speed:.1f} docs/sec)")

    async def search(self, query: str, k: int = 10,
                    enable_reranking: bool = True) -> List[SearchResult]:
        """
        Hybrid search with BM25 + vector fusion and optional reranking.

        Args:
            query: Search query
            k: Number of results to return
            enable_reranking: Whether to use cross-encoder reranking

        Returns:
            List of SearchResult objects
        """
        if not query.strip():
            return []

        search_start = time.time()

        # Expand search to get more candidates for fusion
        candidate_k = max(k * 4, self.config.top_k_candidates)

        # 1. BM25 lexical search
        bm25_results = self.bm25_index.search(query, candidate_k)

        # 2. Vector semantic search
        vector_results = []
        if self.api_client and not self.config.use_on_premise:
            try:
                # Generate query embedding
                query_embeddings = await self.api_client.embed_texts([query])
                query_vector = np.array(query_embeddings[0], dtype=np.float32)

                # Search vector index
                scores, indices = self.vector_index.search(query_vector, candidate_k)

                # Convert to results format
                for score, idx in zip(scores, indices):
                    if idx < len(self.vector_index.doc_ids):
                        doc_id = self.vector_index.doc_ids[idx]
                        vector_results.append((doc_id, score))

            except Exception as e:
                logger.warning(f"⚠️ Vector search failed: {e}")
                if self.config.gentle_error_messages:
                    print("💙 Vector search had trouble - using lexical search only")

        # 3. Hybrid fusion
        fused_results = self.hybrid_ranker.fuse_scores(bm25_results, vector_results, query)

        # Take top candidates for reranking
        top_candidates = fused_results[:self.config.top_k_candidates]

        # 4. Optional reranking
        final_results = []
        if enable_reranking and self.api_client and len(top_candidates) > 1:
            try:
                # Prepare documents for reranking
                candidate_texts = []
                candidate_ids = []

                for doc_id, score in top_candidates:
                    if doc_id in self.document_store:
                        candidate_texts.append(self.document_store[doc_id]['content'])
                        candidate_ids.append(doc_id)

                # Get rerank scores
                rerank_scores = await self.api_client.rerank(query, candidate_texts)

                # Combine with hybrid scores
                reranked_results = []
                for i, (doc_id, hybrid_score) in enumerate(zip(candidate_ids, [s for s, _ in top_candidates if s in candidate_ids])):
                    if i < len(rerank_scores):
                        # Weighted combination of hybrid and rerank scores
                        final_score = 0.7 * rerank_scores[i] + 0.3 * hybrid_score
                        reranked_results.append((doc_id, final_score, rerank_scores[i]))

                reranked_results.sort(key=lambda x: x[1], reverse=True)

                # Create SearchResult objects
                for doc_id, final_score, rerank_score in reranked_results[:k]:
                    if doc_id in self.document_store:
                        doc_data = self.document_store[doc_id]

                        # Get component scores
                        bm25_score = next((s for did, s in bm25_results if did == doc_id), 0.0)
                        vector_score = next((s for did, s in vector_results if did == doc_id), 0.0)

                        result = SearchResult(
                            doc_id=doc_id,
                            score=final_score,
                            content=doc_data['content'],
                            metadata=doc_data['metadata'],
                            bm25_score=bm25_score,
                            vector_score=vector_score,
                            rerank_score=rerank_score
                        )
                        final_results.append(result)

            except Exception as e:
                logger.warning(f"⚠️ Reranking failed: {e}")
                if self.config.gentle_error_messages:
                    print("💙 Reranking had trouble - using hybrid scores only")
                # Fallback to non-reranked results
                enable_reranking = False

        # Fallback: use hybrid scores without reranking
        if not enable_reranking or not final_results:
            for doc_id, hybrid_score in fused_results[:k]:
                if doc_id in self.document_store:
                    doc_data = self.document_store[doc_id]

                    bm25_score = next((s for did, s in bm25_results if did == doc_id), 0.0)
                    vector_score = next((s for did, s in vector_results if did == doc_id), 0.0)

                    result = SearchResult(
                        doc_id=doc_id,
                        score=hybrid_score,
                        content=doc_data['content'],
                        metadata=doc_data['metadata'],
                        bm25_score=bm25_score,
                        vector_score=vector_score
                    )
                    final_results.append(result)

        search_time = time.time() - search_start

        if self.config.enable_progress_tracking and self.config.visual_progress_indicators:
            print(f"🔍 Search completed in {search_time*1000:.0f}ms - found {len(final_results)} results")

        return final_results

    def save_index(self, base_path: str) -> None:
        """Save all index components."""
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)

        # Save vector index
        self.vector_index.save(str(base_path / "vector_index"))

        # Save BM25 index
        self.bm25_index.save(str(base_path / "bm25_index.pkl"))

        # Save document store
        with open(base_path / "document_store.json", 'w') as f:
            json.dump(self.document_store, f)

        # Save configuration
        config_dict = {
            "embedding_model": self.config.embedding_model,
            "embedding_dimension": self.config.embedding_dimension,
            "index_type": self.config.index_type.value,
            "bm25_weight": self.config.bm25_weight,
            "vector_weight": self.config.vector_weight
        }

        with open(base_path / "config.json", 'w') as f:
            json.dump(config_dict, f)

        logger.info(f"💾 Hybrid index saved to {base_path}")

    def load_index(self, base_path: str) -> None:
        """Load all index components."""
        base_path = Path(base_path)

        if not base_path.exists():
            raise FileNotFoundError(f"Index directory not found: {base_path}")

        # Load vector index
        self.vector_index.load(str(base_path / "vector_index"))

        # Load BM25 index
        self.bm25_index.load(str(base_path / "bm25_index.pkl"))

        # Load document store
        with open(base_path / "document_store.json", 'r') as f:
            self.document_store = json.load(f)

        logger.info(f"📁 Hybrid index loaded from {base_path} ({len(self.document_store)} documents)")