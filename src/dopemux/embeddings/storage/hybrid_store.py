"""
Hybrid Vector Store - Production-grade BM25 + Vector Search Fusion

Orchestrates the complete hybrid search pipeline combining lexical (BM25)
and semantic (vector) search with learned fusion and optional reranking.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..core import (
    AdvancedEmbeddingConfig,
    EmbeddingHealthMetrics,
    SearchResult,
    VectorStoreError,
    SearchError,
    VectorStore
)
from ..providers import VoyageAPIClient
from .base import BaseDocumentStore
from .vector_indices import HNSWIndex, FAISSIndex
from .text_indices import BM25Index
from .ranking import HybridRanker, RRFFusion

logger = logging.getLogger(__name__)


class InMemoryDocumentStore(BaseDocumentStore):
    """
    Simple in-memory document store.

    Stores document content and metadata in memory for fast retrieval.
    For production use, consider database-backed implementations.
    """

    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}

    def store_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Store a document with metadata."""
        self.documents[doc_id] = {
            'content': content,
            'metadata': metadata,
            'added_at': time.time()
        }

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a document by ID."""
        if doc_id not in self.documents:
            raise VectorStoreError(f"Document not found: {doc_id}")
        return self.documents[doc_id]

    def get_documents(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve multiple documents by IDs."""
        results = []
        for doc_id in doc_ids:
            try:
                results.append(self.get_document(doc_id))
            except VectorStoreError:
                logger.warning(f"⚠️ Document not found: {doc_id}")
                continue
        return results

    def delete_document(self, doc_id: str) -> None:
        """Delete a document."""
        if doc_id in self.documents:
            del self.documents[doc_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get document store statistics."""
        return {
            "document_count": len(self.documents),
            "storage_type": "in_memory"
        }


class HybridVectorStore(VectorStore):
    """
    Production-grade hybrid search store.

    Combines BM25 lexical search with vector semantic search using
    learned fusion weights and optional cross-encoder reranking.
    """

    def __init__(self, config: AdvancedEmbeddingConfig, persist_directory: Optional[Path] = None):
        """
        Initialize hybrid vector store.

        Args:
            config: Advanced embedding configuration
            persist_directory: Optional directory for persistent storage

        Raises:
            VectorStoreError: When initialization fails
        """
        try:
            self.config = config
            self.persist_directory = persist_directory or Path(config.persist_directory)
            self.persist_directory.mkdir(parents=True, exist_ok=True)

            # Initialize components
            self.document_store = InMemoryDocumentStore()

            # Initialize vector index based on configuration
            if config.index_type.value == "hnsw":
                self.vector_index = HNSWIndex(config)
            elif config.index_type.value == "ivf_pq":
                self.vector_index = FAISSIndex(config)
            else:
                # Default to HNSW
                self.vector_index = HNSWIndex(config)

            self.bm25_index = BM25Index()

            # Initialize ranker
            if config.enable_learning_to_rank:
                self.ranker = HybridRanker(config)
            else:
                self.ranker = RRFFusion()

            # Initialize API client if not using on-premise
            self.api_client: Optional[VoyageAPIClient] = None
            if not config.use_on_premise and config.voyage_api_key:
                self.api_client = VoyageAPIClient(config)

            # Metrics tracking
            self.metrics = EmbeddingHealthMetrics()
            if self.metrics.processing_start_time is None:
                from datetime import datetime
                self.metrics.processing_start_time = datetime.now()

            logger.info(f"🚀 Hybrid vector store initialized with {config.index_type.value} + BM25")

        except Exception as e:
            logger.error(f"❌ Failed to initialize hybrid vector store: {e}")
            raise VectorStoreError(f"Initialization failed: {e}") from e

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the hybrid index.

        Args:
            documents: List of documents with id, content, and metadata

        Raises:
            VectorStoreError: When document addition fails
        """
        try:
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
                self.document_store.store_document(doc_id, content, metadata)

                doc_contents.append(content)
                doc_ids.append(doc_id)

            # Generate embeddings if using API
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

        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise VectorStoreError(f"Document addition failed: {e}") from e

    async def search(self, query_vector: List[float], k: int = 10) -> List[SearchResult]:
        """
        Search using query vector (implements VectorStore interface).

        Args:
            query_vector: Pre-computed query embedding
            k: Number of results to return

        Returns:
            List of search results

        Raises:
            SearchError: When search fails
        """
        try:
            # Convert to numpy array
            query_vector_np = np.array(query_vector, dtype=np.float32)

            # Vector search
            scores, indices = self.vector_index.search(query_vector_np, k * 2)

            # Convert to results format
            vector_results = []
            for score, idx in zip(scores, indices):
                if idx < len(self.vector_index.doc_ids):
                    doc_id = self.vector_index.doc_ids[idx]
                    vector_results.append((doc_id, score))

            # Create placeholder BM25 results (would need query text for real BM25)
            lexical_results = []

            # Fuse results
            fused_results = self.ranker.fuse_scores(lexical_results, vector_results)

            # Fill in document content
            for result in fused_results[:k]:
                try:
                    doc_data = self.document_store.get_document(result.doc_id)
                    result.content = doc_data['content']
                    result.metadata = doc_data['metadata']
                except VectorStoreError:
                    logger.warning(f"⚠️ Document content not found: {result.doc_id}")

            return fused_results[:k]

        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            raise SearchError(f"Search failed: {e}") from e

    async def hybrid_search(self, query: str, k: int = 10,
                           enable_reranking: bool = True) -> List[SearchResult]:
        """
        Hybrid search with BM25 + vector fusion and optional reranking.

        Args:
            query: Search query text
            k: Number of results to return
            enable_reranking: Whether to use cross-encoder reranking

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: When search fails
        """
        try:
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
            fused_results = self.ranker.fuse_scores(bm25_results, vector_results)

            # 4. Fill in document content
            for result in fused_results:
                try:
                    doc_data = self.document_store.get_document(result.doc_id)
                    result.content = doc_data['content']
                    result.metadata = doc_data['metadata']
                except VectorStoreError:
                    logger.warning(f"⚠️ Document content not found: {result.doc_id}")

            # 5. Optional reranking
            if enable_reranking and self.api_client:
                try:
                    # Take top candidates for reranking
                    rerank_candidates = fused_results[:self.config.rerank_batch_size * 2]
                    if rerank_candidates:
                        documents = [r.content for r in rerank_candidates]
                        rerank_scores = await self.api_client.rerank(query, documents)

                        # Update scores
                        for result, rerank_score in zip(rerank_candidates, rerank_scores):
                            result.rerank_score = rerank_score

                        # Re-sort by rerank score
                        rerank_candidates.sort(key=lambda x: x.rerank_score or 0, reverse=True)

                        # Combine reranked top results with remaining results
                        final_results = rerank_candidates + fused_results[len(rerank_candidates):]
                    else:
                        final_results = fused_results

                except Exception as e:
                    logger.warning(f"⚠️ Reranking failed: {e}")
                    final_results = fused_results
            else:
                final_results = fused_results

            # Update metrics
            search_time = (time.time() - search_start) * 1000
            if self.config.enable_progress_tracking and search_time > 1000:
                print(f"🔍 Search completed in {search_time:.0f}ms")

            return final_results[:k]

        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            raise SearchError(f"Hybrid search failed: {e}") from e

    async def delete_documents(self, doc_ids: List[str]) -> None:
        """
        Delete documents from the store.

        Args:
            doc_ids: List of document IDs to delete

        Raises:
            VectorStoreError: When deletion fails
        """
        try:
            for doc_id in doc_ids:
                # Remove from document store
                self.document_store.delete_document(doc_id)

                # Note: Vector and BM25 indices don't support individual deletion
                # In production, implement tombstone marking or periodic rebuild

            logger.info(f"🗑️ Marked {len(doc_ids)} documents for deletion")

        except Exception as e:
            logger.error(f"❌ Failed to delete documents: {e}")
            raise VectorStoreError(f"Document deletion failed: {e}") from e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the hybrid store.

        Returns:
            Dictionary with detailed statistics
        """
        try:
            return {
                "documents": self.document_store.get_stats(),
                "vector_index": self.vector_index.get_stats(),
                "bm25_index": self.bm25_index.get_stats(),
                "ranker": self.ranker.get_stats(),
                "metrics": self.metrics.get_summary(),
                "config": {
                    "index_type": self.config.index_type.value,
                    "embedding_model": self.config.embedding_model,
                    "dimension": self.config.embedding_dimension,
                    "enable_reranking": self.config.rerank_model is not None,
                    "use_on_premise": self.config.use_on_premise
                }
            }

        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {"error": str(e)}

    async def save(self, path: Optional[str] = None) -> None:
        """
        Save the hybrid store to disk.

        Args:
            path: Optional custom path (uses persist_directory if not provided)

        Raises:
            VectorStoreError: When saving fails
        """
        try:
            base_path = Path(path) if path else self.persist_directory

            # Save indices
            self.vector_index.save(str(base_path / "vector_index"))
            self.bm25_index.save(str(base_path / "bm25_index.pkl"))

            logger.info(f"💾 Hybrid store saved to {base_path}")

        except Exception as e:
            logger.error(f"❌ Failed to save hybrid store: {e}")
            raise VectorStoreError(f"Save failed: {e}") from e

    async def load(self, path: Optional[str] = None) -> None:
        """
        Load the hybrid store from disk.

        Args:
            path: Optional custom path (uses persist_directory if not provided)

        Raises:
            VectorStoreError: When loading fails
        """
        try:
            base_path = Path(path) if path else self.persist_directory

            # Load indices
            self.vector_index.load(str(base_path / "vector_index"))
            self.bm25_index.load(str(base_path / "bm25_index.pkl"))

            logger.info(f"📁 Hybrid store loaded from {base_path}")

        except Exception as e:
            logger.error(f"❌ Failed to load hybrid store: {e}")
            raise VectorStoreError(f"Load failed: {e}") from e