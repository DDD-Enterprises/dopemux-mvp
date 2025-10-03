"""
Qdrant Vector Store Abstraction
Provides multi-vector collection management with HNSW indexing
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    HnswConfigDiff,
    PointStruct,
    NamedVector,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
)

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreConfig:
    """Configuration for Qdrant vector store"""

    mode: str = "memory"  # 'memory' or 'disk'
    path: Optional[str] = "./data/qdrant"
    hnsw_m: int = 16
    hnsw_ef_construct: int = 200
    hnsw_ef: int = 150  # Search-time parameter


class QdrantVectorStore:
    """
    Multi-vector Qdrant collection manager

    Supports:
    - Multi-vector per point (content, title, breadcrumb)
    - HNSW indexing with tunable parameters
    - Filtered search by workspace, doc_type, language
    - Batch operations with payload
    """

    def __init__(self, config: VectorStoreConfig):
        self.config = config

        # Initialize client
        if config.mode == "memory":
            self.client = QdrantClient(":memory:")
            logger.info("Initialized Qdrant in-memory mode")
        else:
            self.client = QdrantClient(path=config.path)
            logger.info(f"Initialized Qdrant at {config.path}")

    def create_code_collection(self, collection_name: str = "code_index"):
        """
        Create multi-vector collection for code with HNSW indexing

        Vectors:
        - content_vec: Contextualized code (1024d)
        - title_vec: Function/class name (1024d)
        - breadcrumb_vec: Qualified path (1024d)
        """
        vectors_config = {
            "content_vec": VectorParams(
                size=1024,
                distance=Distance.DOT,  # Voyage vectors are normalized
                hnsw_config=HnswConfigDiff(
                    m=self.config.hnsw_m, ef_construct=self.config.hnsw_ef_construct
                ),
            ),
            "title_vec": VectorParams(
                size=1024,
                distance=Distance.DOT,
                hnsw_config=HnswConfigDiff(
                    m=self.config.hnsw_m, ef_construct=self.config.hnsw_ef_construct
                ),
            ),
            "breadcrumb_vec": VectorParams(
                size=1024,
                distance=Distance.DOT,
                hnsw_config=HnswConfigDiff(
                    m=self.config.hnsw_m, ef_construct=self.config.hnsw_ef_construct
                ),
            ),
        }

        self.client.create_collection(
            collection_name=collection_name, vectors_config=vectors_config
        )

        logger.info(
            f"Created code collection '{collection_name}' with multi-vector HNSW"
        )
        return collection_name

    def create_docs_collection(self, collection_name: str = "docs_index"):
        """
        Create single-vector collection for docs with voyage-context-3

        Vectors:
        - content_vec: Contextualized document chunks (1024d)
        """
        vectors_config = {
            "content_vec": VectorParams(
                size=1024,
                distance=Distance.DOT,
                hnsw_config=HnswConfigDiff(
                    m=self.config.hnsw_m, ef_construct=self.config.hnsw_ef_construct
                ),
            )
        }

        self.client.create_collection(
            collection_name=collection_name, vectors_config=vectors_config
        )

        logger.info(f"Created docs collection '{collection_name}'")
        return collection_name

    async def upsert_code_chunks(
        self, collection_name: str, chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Insert code chunks with multi-vector embeddings

        Args:
            collection_name: Target collection
            chunks: List of dicts with:
                - id: Unique identifier
                - vectors: Dict with content_vec, title_vec, breadcrumb_vec
                - payload: Metadata (file_path, function_name, language, etc.)

        Returns:
            Number of chunks inserted
        """
        points = []

        for chunk in chunks:
            # Create named vectors
            vectors = {
                "content_vec": chunk["vectors"]["content_vec"],
                "title_vec": chunk["vectors"]["title_vec"],
                "breadcrumb_vec": chunk["vectors"]["breadcrumb_vec"],
            }

            point = PointStruct(
                id=chunk["id"], vector=vectors, payload=chunk["payload"]
            )
            points.append(point)

        # Batch upsert
        self.client.upsert(collection_name=collection_name, points=points)

        logger.info(f"Upserted {len(points)} code chunks to {collection_name}")
        return len(points)

    async def search_code(
        self,
        collection_name: str,
        query_vectors: Dict[str, List[float]],
        top_k: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Multi-vector search with weighted fusion

        Args:
            collection_name: Collection to search
            query_vectors: Dict with content_vec, title_vec, breadcrumb_vec
            top_k: Number of results
            filters: Payload filters (workspace_id, language, etc.)
            weights: Vector weights (default: content=0.7, title=0.2, breadcrumb=0.1)

        Returns:
            List of search results with scores and payloads
        """
        if weights is None:
            weights = {"content_vec": 0.7, "title_vec": 0.2, "breadcrumb_vec": 0.1}

        # Build filter
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            if conditions:
                query_filter = Filter(must=conditions)

        # Search each vector field separately
        results_by_vector = {}

        for vector_name, query_vec in query_vectors.items():
            if query_vec is None:
                continue

            search_results = self.client.query_points(
                collection_name=collection_name,
                query=query_vec,
                using=vector_name,
                limit=top_k,
                query_filter=query_filter,
                search_params=SearchParams(hnsw_ef=self.config.hnsw_ef),
            ).points

            results_by_vector[vector_name] = search_results

        # Weighted fusion of multi-vector results
        fused_results = self._weighted_fusion(results_by_vector, weights, top_k)

        return fused_results

    def _weighted_fusion(
        self, results_by_vector: Dict[str, List], weights: Dict[str, float], top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Fuse multi-vector search results with weights

        Uses score-based weighted fusion:
        final_score = Σ(weight_i × score_i)
        """
        # Collect all unique IDs
        all_ids = set()
        for results in results_by_vector.values():
            for result in results:
                all_ids.add(result.id)

        # Calculate weighted scores
        id_scores = {}
        id_payloads = {}

        for point_id in all_ids:
            weighted_score = 0.0
            payload = None

            for vector_name, results in results_by_vector.items():
                weight = weights.get(vector_name, 0.0)

                # Find this ID in results
                for result in results:
                    if result.id == point_id:
                        weighted_score += weight * result.score
                        if payload is None:
                            payload = result.payload
                        break

            id_scores[point_id] = weighted_score
            id_payloads[point_id] = payload

        # Sort by weighted score
        sorted_ids = sorted(id_scores.keys(), key=lambda x: id_scores[x], reverse=True)[
            :top_k
        ]

        # Format results
        fused_results = []
        for point_id in sorted_ids:
            fused_results.append(
                {
                    "id": point_id,
                    "score": id_scores[point_id],
                    "payload": id_payloads[point_id],
                }
            )

        return fused_results

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics and configuration"""
        collection = self.client.get_collection(collection_name)

        return {
            "name": collection_name,
            "vectors_count": collection.points_count,
            "indexed_vectors_count": collection.indexed_vectors_count,
            "config": {
                "hnsw_m": self.config.hnsw_m,
                "hnsw_ef_construct": self.config.hnsw_ef_construct,
                "hnsw_ef": self.config.hnsw_ef,
            },
        }

    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        self.client.delete_collection(collection_name)
        logger.info(f"Deleted collection '{collection_name}'")
