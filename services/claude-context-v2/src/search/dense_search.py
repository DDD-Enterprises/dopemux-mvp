"""
Multi-Vector Dense Search - Task 4
Qdrant-based vector search with multiple named vectors and weighted fusion.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    SearchRequest,
    NamedVector,
    Filter,
    FieldCondition,
    MatchValue,
)


logger = logging.getLogger(__name__)


@dataclass
class SearchProfile:
    """Search configuration profile for different use cases."""

    name: str
    top_k: int
    content_weight: float
    title_weight: float
    breadcrumb_weight: float
    ef: int  # HNSW search quality parameter

    @classmethod
    def implementation(cls) -> "SearchProfile":
        """Profile for finding implementation examples."""
        return cls(
            name="implementation",
            top_k=100,
            content_weight=0.7,
            title_weight=0.2,
            breadcrumb_weight=0.1,
            ef=150,
        )

    @classmethod
    def debugging(cls) -> "SearchProfile":
        """Profile for debugging (focus on function names)."""
        return cls(
            name="debugging",
            top_k=50,
            content_weight=0.5,
            title_weight=0.4,
            breadcrumb_weight=0.1,
            ef=120,
        )

    @classmethod
    def exploration(cls) -> "SearchProfile":
        """Profile for codebase exploration (broader context)."""
        return cls(
            name="exploration",
            top_k=200,
            content_weight=0.6,
            title_weight=0.2,
            breadcrumb_weight=0.2,
            ef=180,
        )


@dataclass
class SearchResult:
    """Single search result with metadata."""

    id: str
    score: float
    payload: Dict
    file_path: str
    function_name: Optional[str]
    language: str
    content: str
    context_snippet: Optional[str] = None


class MultiVectorSearch:
    """
    Multi-vector dense search using Qdrant.

    Features:
    - 3 named vectors (content, title, breadcrumb)
    - Weighted fusion with configurable profiles
    - HNSW index with high-recall tuning
    - Async operations for performance
    """

    def __init__(
        self,
        collection_name: str = "code_index",
        url: str = "localhost",
        port: int = 6333,
        vector_size: int = 1024,
    ):
        """
        Initialize multi-vector search.

        Args:
            collection_name: Qdrant collection name
            url: Qdrant server URL
            port: Qdrant server port
            vector_size: Embedding dimension (1024 for Voyage)
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = AsyncQdrantClient(url=url, port=port)

        # HNSW config for high-recall code search
        # ef_construct=200 (2x default) for better index quality
        # m=16 (default) balances accuracy and memory
        self.hnsw_config = models.HnswConfigDiff(
            m=16,
            ef_construct=200,
        )

    async def create_collection(self):
        """Create Qdrant collection with multi-vector schema."""
        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            if self.collection_name in [c.name for c in collections.collections]:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return

            # Create collection with 3 named vectors
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "content_vec": VectorParams(
                        size=self.vector_size,
                        distance=Distance.DOT,  # Voyage embeddings are normalized
                        hnsw_config=self.hnsw_config,
                    ),
                    "title_vec": VectorParams(
                        size=self.vector_size,
                        distance=Distance.DOT,
                    ),
                    "breadcrumb_vec": VectorParams(
                        size=self.vector_size,
                        distance=Distance.DOT,
                    ),
                },
            )

            # Create payload indexes for filtering
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="file_path",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="language",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="workspace_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            logger.info(f"Created collection '{self.collection_name}' with 3 named vectors")

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def delete_collection(self):
        """Delete the collection."""
        try:
            await self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

    async def insert_point(
        self,
        content_vector: List[float],
        title_vector: List[float],
        breadcrumb_vector: List[float],
        payload: Dict,
        point_id: Optional[str] = None,
    ) -> str:
        """
        Insert a single point with multi-vector embeddings.

        Args:
            content_vector: Embedding of contextualized content
            title_vector: Embedding of function/class name
            breadcrumb_vector: Embedding of file path + qualified name
            payload: Metadata (file_path, function_name, language, etc.)
            point_id: Optional custom ID (generates UUID if None)

        Returns:
            Point ID
        """
        if point_id is None:
            point_id = str(uuid4())

        point = PointStruct(
            id=point_id,
            vector={
                "content_vec": content_vector,
                "title_vec": title_vector,
                "breadcrumb_vec": breadcrumb_vector,
            },
            payload=payload,
        )

        await self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

        logger.debug(f"Inserted point {point_id}")
        return point_id

    async def insert_points_batch(
        self,
        points: List[Tuple[List[float], List[float], List[float], Dict, Optional[str]]],
    ) -> List[str]:
        """
        Insert multiple points in batch.

        Args:
            points: List of (content_vec, title_vec, breadcrumb_vec, payload, point_id)

        Returns:
            List of point IDs
        """
        point_structs = []
        point_ids = []

        for content_vec, title_vec, breadcrumb_vec, payload, point_id in points:
            if point_id is None:
                point_id = str(uuid4())

            point_ids.append(point_id)

            point_structs.append(
                PointStruct(
                    id=point_id,
                    vector={
                        "content_vec": content_vec,
                        "title_vec": title_vec,
                        "breadcrumb_vec": breadcrumb_vec,
                    },
                    payload=payload,
                )
            )

        await self.client.upsert(
            collection_name=self.collection_name,
            points=point_structs,
        )

        logger.info(f"Inserted {len(point_structs)} points in batch")
        return point_ids

    async def search(
        self,
        query_content_vector: List[float],
        query_title_vector: List[float],
        query_breadcrumb_vector: List[float],
        profile: SearchProfile = None,
        filter_by: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """
        Multi-vector search with weighted fusion.

        Args:
            query_content_vector: Query embedding for content
            query_title_vector: Query embedding for title
            query_breadcrumb_vector: Query embedding for breadcrumb
            profile: Search profile (defaults to implementation)
            filter_by: Optional filters (e.g., {"language": "python"})

        Returns:
            List of SearchResult sorted by score
        """
        if profile is None:
            profile = SearchProfile.implementation()

        # Build filter
        query_filter = None
        if filter_by:
            conditions = []
            for key, value in filter_by.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )

            if conditions:
                query_filter = Filter(must=conditions)

        # Search each vector with its weight
        # Qdrant doesn't support weighted multi-vector search directly,
        # so we search each vector separately and fuse results

        # Search content vector
        content_results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=NamedVector(
                name="content_vec",
                vector=query_content_vector,
            ),
            query_filter=query_filter,
            limit=profile.top_k,
            search_params=models.SearchParams(
                hnsw_ef=profile.ef,
            ),
        )

        # Search title vector
        title_results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=NamedVector(
                name="title_vec",
                vector=query_title_vector,
            ),
            query_filter=query_filter,
            limit=profile.top_k,
            search_params=models.SearchParams(
                hnsw_ef=profile.ef,
            ),
        )

        # Search breadcrumb vector
        breadcrumb_results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=NamedVector(
                name="breadcrumb_vec",
                vector=query_breadcrumb_vector,
            ),
            query_filter=query_filter,
            limit=profile.top_k,
            search_params=models.SearchParams(
                hnsw_ef=profile.ef,
            ),
        )

        # Fuse results with weighted scores
        score_map: Dict[str, float] = {}
        payload_map: Dict[str, Dict] = {}

        # Add content scores
        for result in content_results:
            score_map[str(result.id)] = result.score * profile.content_weight
            payload_map[str(result.id)] = result.payload

        # Add title scores
        for result in title_results:
            point_id = str(result.id)
            score_map[point_id] = score_map.get(point_id, 0.0) + (
                result.score * profile.title_weight
            )
            if point_id not in payload_map:
                payload_map[point_id] = result.payload

        # Add breadcrumb scores
        for result in breadcrumb_results:
            point_id = str(result.id)
            score_map[point_id] = score_map.get(point_id, 0.0) + (
                result.score * profile.breadcrumb_weight
            )
            if point_id not in payload_map:
                payload_map[point_id] = result.payload

        # Sort by fused score and create SearchResult objects
        sorted_ids = sorted(score_map.items(), key=lambda x: x[1], reverse=True)

        results = []
        for point_id, score in sorted_ids[:profile.top_k]:
            payload = payload_map[point_id]

            results.append(
                SearchResult(
                    id=point_id,
                    score=score,
                    payload=payload,
                    file_path=payload.get("file_path", ""),
                    function_name=payload.get("function_name"),
                    language=payload.get("language", ""),
                    content=payload.get("raw_code", ""),
                    context_snippet=payload.get("context_snippet"),
                )
            )

        logger.debug(
            f"Multi-vector search returned {len(results)} results "
            f"(profile: {profile.name})"
        )

        return results

    async def delete_points(self, point_ids: List[str]):
        """Delete points by IDs."""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=point_ids),
        )
        logger.info(f"Deleted {len(point_ids)} points")

    async def get_collection_info(self) -> Dict:
        """Get collection information."""
        info = await self.client.get_collection(collection_name=self.collection_name)
        return {
            "name": info.config.name if hasattr(info.config, 'name') else self.collection_name,
            "vectors_count": info.points_count,
            "status": info.status,
        }


# Example usage
async def main():
    """Example usage of MultiVectorSearch."""
    search = MultiVectorSearch()

    # Create collection
    await search.create_collection()

    # Example: Insert a code chunk
    # (In production, these would come from VoyageEmbedder)
    content_vec = [0.1] * 1024
    title_vec = [0.2] * 1024
    breadcrumb_vec = [0.3] * 1024

    payload = {
        "file_path": "src/utils/math.py",
        "function_name": "calculate_sum",
        "language": "python",
        "raw_code": "def calculate_sum(a, b):\n    return a + b",
        "context_snippet": "This function from src/utils/math.py calculates the sum of two numbers.",
        "workspace_id": "my-project",
    }

    point_id = await search.insert_point(
        content_vector=content_vec,
        title_vector=title_vec,
        breadcrumb_vector=breadcrumb_vec,
        payload=payload,
    )

    print(f"Inserted point: {point_id}")

    # Search
    query_content = [0.15] * 1024
    query_title = [0.25] * 1024
    query_breadcrumb = [0.35] * 1024

    results = await search.search(
        query_content_vector=query_content,
        query_title_vector=query_title,
        query_breadcrumb_vector=query_breadcrumb,
        profile=SearchProfile.implementation(),
    )

    print(f"\nFound {len(results)} results:")
    for r in results[:5]:
        print(f"  {r.file_path}:{r.function_name} (score: {r.score:.4f})")

    # Collection info
    info = await search.get_collection_info()
    print(f"\nCollection info: {info}")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
