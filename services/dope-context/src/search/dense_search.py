"""
Multi-Vector Dense Search - Task 4
Qdrant-based vector search with multiple named vectors and weighted fusion.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from uuid import NAMESPACE_URL, uuid4, uuid5

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from ..embeddings.model_registry import (
    COLLECTION_MANIFEST_KEY,
    CollectionCompatibilityError,
    compare_collection_manifests,
)

logger = logging.getLogger(__name__)


def manifest_point_id(collection_name: str) -> str:
    """Reserved, deterministic id for a collection's manifest sentinel."""

    return str(uuid5(NAMESPACE_URL, f"dope-context:manifest:{collection_name}"))


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
        manifest: Optional[Dict] = None,
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
        # Active compatibility record. Reads do not need it; writes refuse
        # without it, which is what makes the gate fail closed.
        self.manifest = manifest
        self._compatibility_checked = False
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
                # Idempotent by design: index runs call this twice (server.py
                # and again in IndexingPipeline.index_workspace), so a matching
                # manifest must return quietly rather than raise.
                await self._assert_compatible()
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

            await self._write_manifest()

            logger.info(
                f"Created collection '{self.collection_name}' with 3 named vectors"
            )

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def _write_manifest(self) -> None:
        """Persist the active manifest as a reserved zero-vector point.

        Stored inside the collection deliberately: a sidecar would have a
        lifecycle independent of the Qdrant volume and could outlive or be
        outlived by the data it describes.
        """

        if not self.manifest:
            logger.warning(
                "No manifest supplied for '%s'; collection is unguarded and "
                "writes will be refused until one is provided",
                self.collection_name,
            )
            return

        zero = [0.0] * self.vector_size
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=manifest_point_id(self.collection_name),
                    vector={
                        "content_vec": zero,
                        "title_vec": zero,
                        "breadcrumb_vec": zero,
                    },
                    payload=dict(self.manifest),
                )
            ],
        )
        logger.info("Wrote compatibility manifest for '%s'", self.collection_name)

    async def read_manifest(self) -> Optional[Dict]:
        """Return the stored manifest, or None if the collection has none."""

        records = await self.client.retrieve(
            collection_name=self.collection_name,
            ids=[manifest_point_id(self.collection_name)],
            with_payload=True,
            with_vectors=False,
        )
        if not records:
            return None
        return dict(records[0].payload or {})

    async def _is_empty(self) -> bool:
        info = await self.client.get_collection(collection_name=self.collection_name)
        return not getattr(info, "points_count", 0)

    async def _assert_compatible(self) -> None:
        """Fail closed unless the stored manifest matches the active one.

        An empty collection with no manifest is adopted; a populated one is
        refused, because its vectors were produced by an unknown configuration.
        """

        if self._compatibility_checked:
            return
        if not self.manifest:
            raise CollectionCompatibilityError(
                f"Refusing to write to '{self.collection_name}': no active "
                "manifest was supplied, so compatibility cannot be established."
            )

        stored = await self.read_manifest()
        if stored is None and await self._is_empty():
            await self._write_manifest()
            self._compatibility_checked = True
            return

        compare_collection_manifests(
            stored, self.manifest, collection_name=self.collection_name
        )
        self._compatibility_checked = True

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
        await self._assert_compatible()

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
        await self._assert_compatible()

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

    async def _query_named_vector(
        self,
        vector_name: str,
        query_vector: List[float],
        query_filter: Optional[Filter],
        profile: "SearchProfile",
    ) -> List:
        """Query one named vector.

        Uses ``query_points``: ``AsyncQdrantClient.search`` was removed from
        qdrant-client and calling it raises AttributeError on every installed
        version here (1.17.1 locally, 1.18.0 in the image and the running
        container). The returned ``.points`` are ScoredPoint, the same shape
        the old call produced, so fusion downstream is unchanged.
        """

        response = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using=vector_name,
            query_filter=query_filter,
            limit=profile.top_k,
            search_params=models.SearchParams(hnsw_ef=profile.ef),
            with_payload=True,
        )
        return response.points

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

        # Build filter. The manifest sentinel is excluded unconditionally:
        # it is a real point with zero vectors, so without this it comes back
        # at score 0.0 and consumes a slot in top_k.
        conditions = []
        if filter_by:
            for key, value in filter_by.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )

        query_filter = Filter(
            must=conditions or None,
            must_not=[
                FieldCondition(
                    key=COLLECTION_MANIFEST_KEY,
                    match=MatchValue(value=True),
                )
            ],
        )

        # Search each vector separately and fuse: Qdrant has no weighted
        # multi-vector query.
        content_results = await self._query_named_vector(
            "content_vec", query_content_vector, query_filter, profile
        )
        title_results = await self._query_named_vector(
            "title_vec", query_title_vector, query_filter, profile
        )
        breadcrumb_results = await self._query_named_vector(
            "breadcrumb_vec", query_breadcrumb_vector, query_filter, profile
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
        for point_id, score in sorted_ids[: profile.top_k]:
            payload = payload_map[point_id]

            # Support both code and docs payloads
            file_path = payload.get("file_path") or payload.get("source_path", "")
            content = payload.get("raw_code") or payload.get("text", "")
            language = payload.get("language") or payload.get("doc_type", "")

            results.append(
                SearchResult(
                    id=point_id,
                    score=score,
                    payload=payload,
                    file_path=file_path,
                    function_name=payload.get("function_name"),
                    language=language,
                    content=content,
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
            "name": (
                info.config.name
                if hasattr(info.config, "name")
                else self.collection_name
            ),
            "vectors_count": info.points_count,
            "status": info.status,
        }

    async def get_all_payloads(self, batch_size: int = 100) -> List[Dict]:
        """
        Retrieve all document payloads from collection (for BM25 index building).

        Uses Qdrant scroll API for efficient batch retrieval.

        Args:
            batch_size: Number of documents per batch (default: 100)

        Returns:
            List of payload dictionaries with 'id', 'raw_code', 'function_name', etc.
        """
        all_payloads = []
        offset = None

        try:
            while True:
                # Scroll through collection
                records, next_offset = await self.client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,  # Don't need vectors, just payloads
                )

                if not records:
                    break

                # Extract payloads and add IDs
                for record in records:
                    payload = dict(record.payload) if record.payload else {}
                    # Never leak the manifest sentinel: this feeds the BM25
                    # index, docs stale reconciliation and sync, any of which
                    # would treat it as a real document.
                    if payload.get(COLLECTION_MANIFEST_KEY):
                        continue
                    payload["id"] = str(record.id)  # Add ID for BM25 doc_id mapping
                    all_payloads.append(payload)

                # Check if more results available
                if next_offset is None:
                    break

                offset = next_offset

            logger.info(
                f"Retrieved {len(all_payloads)} payloads from '{self.collection_name}'"
            )
            return all_payloads

        except Exception as e:
            logger.error(f"Failed to retrieve payloads: {e}")
            raise


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

    logger.info(f"Inserted point: {point_id}")

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

    logger.info(f"\nFound {len(results)} results:")
    for r in results[:5]:
        logger.info(f"  {r.file_path}:{r.function_name} (score: {r.score:.4f})")

    # Collection info
    info = await search.get_collection_info()
    logger.info(f"\nCollection info: {info}")


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
