"""
Vector index implementations for semantic search.

Provides HNSW and other vector index implementations optimized for
2048-dimensional embeddings with expert-tuned parameters.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import hnswlib
except ImportError:
    hnswlib = None

try:
    import faiss
except ImportError:
    faiss = None

from ..core import AdvancedEmbeddingConfig, VectorStoreError
from .base import BaseVectorIndex

logger = logging.getLogger(__name__)


class HNSWIndex(BaseVectorIndex):
    """
    HNSW vector index optimized for 2048-dimensional embeddings.

    Implements Hierarchical Navigable Small World graph algorithm
    with expert-recommended parameters for voyage-context-3 embeddings.
    Provides excellent recall with fast search times.
    """

    def __init__(self, config: AdvancedEmbeddingConfig):
        """
        Initialize HNSW index.

        Args:
            config: Embedding configuration with HNSW parameters

        Raises:
            ImportError: If hnswlib is not available
        """
        if hnswlib is None:
            raise ImportError("hnswlib not available. Install with: pip install hnswlib")

        self.config = config
        self.dimension = config.embedding_dimension

        # Expert-recommended HNSW parameters for 2048-dim
        self.index = hnswlib.Index(
            space='cosine' if config.distance_metric == 'cosine' else 'l2',
            dim=self.dimension
        )

        self.doc_ids: List[str] = []
        self.is_initialized = False

    def _init_index(self, max_elements: int = 10000):
        """
        Initialize the HNSW index with capacity.

        Args:
            max_elements: Maximum number of elements the index can hold
        """
        self.index.init_index(
            max_elements=max_elements,
            M=self.config.hnsw_m,              # 32 connections per node
            ef_construction=self.config.hnsw_ef_construction  # 200 for build
        )
        self.index.set_ef(self.config.hnsw_ef)  # 128 for search
        self.is_initialized = True

        logger.info(f"🔧 HNSW index initialized: {max_elements:,} capacity, M={self.config.hnsw_m}")

    def add_vectors(self, vectors: np.ndarray, ids: List[str]) -> None:
        """
        Add vectors to HNSW index.

        Args:
            vectors: Array of embedding vectors to add
            ids: Corresponding document IDs

        Raises:
            VectorStoreError: When vector addition fails
        """
        try:
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

        except Exception as e:
            logger.error(f"❌ Failed to add vectors to HNSW index: {e}")
            raise VectorStoreError(f"HNSW vector addition failed: {e}") from e

    def search(self, query_vector: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        """
        Search HNSW index for similar vectors.

        Args:
            query_vector: Query embedding vector
            k: Number of nearest neighbors to return

        Returns:
            Tuple of (similarity_scores, doc_indices)

        Raises:
            VectorStoreError: When search fails
        """
        try:
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

        except Exception as e:
            logger.error(f"❌ HNSW search failed: {e}")
            raise VectorStoreError(f"HNSW search failed: {e}") from e

    def save(self, path: str) -> None:
        """
        Save HNSW index and metadata.

        Args:
            path: File path to save the index

        Raises:
            VectorStoreError: When saving fails
        """
        try:
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

        except Exception as e:
            logger.error(f"❌ Failed to save HNSW index: {e}")
            raise VectorStoreError(f"HNSW save failed: {e}") from e

    def load(self, path: str) -> None:
        """
        Load HNSW index and metadata.

        Args:
            path: File path to load the index from

        Raises:
            VectorStoreError: When loading fails
        """
        try:
            index_path = Path(path)
            if not index_path.exists():
                raise FileNotFoundError(f"HNSW index not found: {path}")

            # Load metadata
            with open(f"{path}.meta", 'r') as f:
                metadata = json.load(f)

            self.doc_ids = metadata["doc_ids"]

            # Load index
            self.index.load_index(str(index_path))
            self.index.set_ef(self.config.hnsw_ef)
            self.is_initialized = True

            logger.info(f"📁 HNSW index loaded from {path} ({len(self.doc_ids):,} documents)")

        except Exception as e:
            logger.error(f"❌ Failed to load HNSW index: {e}")
            raise VectorStoreError(f"HNSW load failed: {e}") from e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get HNSW index statistics.

        Returns:
            Dictionary with index statistics
        """
        if not self.is_initialized:
            return {"initialized": False}

        try:
            current_count = self.index.get_current_count()
            max_elements = self.index.get_max_elements()

            return {
                "initialized": True,
                "document_count": len(self.doc_ids),
                "vector_count": current_count,
                "max_capacity": max_elements,
                "dimension": self.dimension,
                "utilization": current_count / max_elements if max_elements > 0 else 0,
                "distance_metric": self.config.distance_metric,
                "hnsw_m": self.config.hnsw_m,
                "hnsw_ef": self.config.hnsw_ef
            }

        except Exception as e:
            logger.error(f"❌ Failed to get HNSW stats: {e}")
            return {"error": str(e)}


class FAISSIndex(BaseVectorIndex):
    """
    FAISS vector index for large-scale vector search.

    Implements Facebook AI Similarity Search with IVF-PQ indexing
    for memory-efficient large-scale vector retrieval.
    """

    def __init__(self, config: AdvancedEmbeddingConfig):
        """
        Initialize FAISS index.

        Args:
            config: Embedding configuration with FAISS parameters

        Raises:
            ImportError: If FAISS is not available
        """
        if faiss is None:
            raise ImportError("FAISS not available. Install with: pip install faiss-cpu")

        self.config = config
        self.dimension = config.embedding_dimension
        self.doc_ids: List[str] = []

        # Create IVF-PQ index for memory efficiency
        if config.enable_quantization:
            # Product quantization for memory reduction
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFPQ(
                quantizer,
                self.dimension,
                config.ivf_nlist,  # Number of clusters
                config.pq_m,       # Product quantization subspaces
                8                  # 8-bit quantization
            )
        else:
            # Standard IVF index
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(
                quantizer,
                self.dimension,
                config.ivf_nlist
            )

        self.is_trained = False

    def add_vectors(self, vectors: np.ndarray, ids: List[str]) -> None:
        """
        Add vectors to FAISS index.

        Args:
            vectors: Array of embedding vectors to add
            ids: Corresponding document IDs

        Raises:
            VectorStoreError: When vector addition fails
        """
        try:
            vectors = vectors.astype(np.float32)

            # Train index if not already trained
            if not self.is_trained and len(vectors) >= self.config.ivf_nlist:
                logger.info(f"🔧 Training FAISS index with {len(vectors)} vectors...")
                self.index.train(vectors)
                self.is_trained = True

            if self.is_trained:
                self.index.add(vectors)
                self.doc_ids.extend(ids)
                logger.debug(f"➕ Added {len(ids)} vectors to FAISS index")
            else:
                logger.warning(f"⚠️ Not enough vectors to train FAISS index (need {self.config.ivf_nlist})")

        except Exception as e:
            logger.error(f"❌ Failed to add vectors to FAISS index: {e}")
            raise VectorStoreError(f"FAISS vector addition failed: {e}") from e

    def search(self, query_vector: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        """
        Search FAISS index for similar vectors.

        Args:
            query_vector: Query embedding vector
            k: Number of nearest neighbors to return

        Returns:
            Tuple of (similarity_scores, doc_indices)

        Raises:
            VectorStoreError: When search fails
        """
        try:
            if not self.is_trained or len(self.doc_ids) == 0:
                return [], []

            query_vector = query_vector.astype(np.float32).reshape(1, -1)
            k = min(k, len(self.doc_ids))

            distances, indices = self.index.search(query_vector, k)

            # Convert to similarity scores and handle single query
            distances = distances[0]
            indices = indices[0]

            # Filter out -1 indices (not found)
            valid_mask = indices >= 0
            distances = distances[valid_mask]
            indices = indices[valid_mask]

            # Convert L2 distances to similarity scores
            scores = 1.0 / (1.0 + distances)

            return scores.tolist(), indices.tolist()

        except Exception as e:
            logger.error(f"❌ FAISS search failed: {e}")
            raise VectorStoreError(f"FAISS search failed: {e}") from e

    def save(self, path: str) -> None:
        """
        Save FAISS index and metadata.

        Args:
            path: File path to save the index

        Raises:
            VectorStoreError: When saving fails
        """
        try:
            if not self.is_trained:
                logger.warning("⚠️ Cannot save untrained FAISS index")
                return

            index_path = Path(path)
            index_path.parent.mkdir(parents=True, exist_ok=True)

            # Save index
            faiss.write_index(self.index, str(index_path))

            # Save metadata
            metadata = {
                "doc_ids": self.doc_ids,
                "dimension": self.dimension,
                "is_trained": self.is_trained,
                "config": {
                    "ivf_nlist": self.config.ivf_nlist,
                    "enable_quantization": self.config.enable_quantization
                }
            }

            with open(f"{path}.meta", 'w') as f:
                json.dump(metadata, f)

            logger.info(f"💾 FAISS index saved to {path}")

        except Exception as e:
            logger.error(f"❌ Failed to save FAISS index: {e}")
            raise VectorStoreError(f"FAISS save failed: {e}") from e

    def load(self, path: str) -> None:
        """
        Load FAISS index and metadata.

        Args:
            path: File path to load the index from

        Raises:
            VectorStoreError: When loading fails
        """
        try:
            index_path = Path(path)
            if not index_path.exists():
                raise FileNotFoundError(f"FAISS index not found: {path}")

            # Load metadata
            with open(f"{path}.meta", 'r') as f:
                metadata = json.load(f)

            self.doc_ids = metadata["doc_ids"]
            self.is_trained = metadata["is_trained"]

            # Load index
            self.index = faiss.read_index(str(index_path))

            logger.info(f"📁 FAISS index loaded from {path} ({len(self.doc_ids):,} documents)")

        except Exception as e:
            logger.error(f"❌ Failed to load FAISS index: {e}")
            raise VectorStoreError(f"FAISS load failed: {e}") from e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get FAISS index statistics.

        Returns:
            Dictionary with index statistics
        """
        try:
            return {
                "initialized": True,
                "trained": self.is_trained,
                "document_count": len(self.doc_ids),
                "vector_count": self.index.ntotal if hasattr(self.index, 'ntotal') else 0,
                "dimension": self.dimension,
                "quantization_enabled": self.config.enable_quantization,
                "ivf_nlist": self.config.ivf_nlist
            }

        except Exception as e:
            logger.error(f"❌ Failed to get FAISS stats: {e}")
            return {"error": str(e)}