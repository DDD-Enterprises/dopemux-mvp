"""
Milvus database interface for document storage and retrieval.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import structlog
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
    connections,
    utility,
)
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import DocRAGConfig
from .models import CollectionStats, DocumentChunk, SearchResult

logger = structlog.get_logger(__name__)


class MilvusDatabase:
    """Interface to Milvus vector database."""

    def __init__(self, config: DocRAGConfig):
        """Initialize Milvus database connection."""
        self.config = config
        self.client: Optional[MilvusClient] = None
        self.collection: Optional[Collection] = None
        self._connected = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def connect(self) -> None:
        """Connect to Milvus database."""
        try:
            # Connect using pymilvus
            connections.connect(
                alias="default",
                host=self.config.milvus.host,
                port=self.config.milvus.port,
                token=self.config.milvus.token,
            )

            # Initialize client
            self.client = MilvusClient(uri=self.config.milvus.uri)

            # Create collection if it doesn't exist
            await self._ensure_collection_exists()

            self._connected = True
            logger.info("Connected to Milvus", host=self.config.milvus.host)

        except Exception as e:
            logger.error("Failed to connect to Milvus", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from Milvus."""
        if self._connected:
            connections.disconnect("default")
            self._connected = False
            logger.info("Disconnected from Milvus")

    async def _ensure_collection_exists(self) -> None:
        """Ensure the docs collection exists with proper schema."""
        collection_name = self.config.collection.docs_collection

        if utility.has_collection(collection_name):
            self.collection = Collection(collection_name)
            logger.info("Using existing collection", name=collection_name)
        else:
            await self._create_collection()
            logger.info("Created new collection", name=collection_name)

    async def _create_collection(self) -> None:
        """Create the docs collection with schema."""
        collection_name = self.config.collection.docs_collection

        # Define schema
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=100,
                is_primary=True,
                auto_id=False,
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.config.collection.dimension,
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=8000,
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON,
            ),
        ]

        # Add sparse vector field if hybrid search is enabled
        if self.config.enable_hybrid_search:
            fields.append(
                FieldSchema(
                    name="sparse_vector",
                    dtype=DataType.SPARSE_FLOAT_VECTOR,
                )
            )

        schema = CollectionSchema(
            fields=fields,
            description="DocRAG document chunks collection",
        )

        # Create collection
        self.collection = Collection(
            name=collection_name,
            schema=schema,
        )

        # Create index
        await self._create_indexes()

    async def _create_indexes(self) -> None:
        """Create indexes on the collection."""
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        # Dense vector index
        dense_index_params = {
            "metric_type": self.config.collection.metric_type,
            "index_type": self.config.collection.index_type,
            "params": {
                "M": self.config.collection.hnsw_m,
                "efConstruction": self.config.collection.hnsw_ef_construction,
            },
        }

        self.collection.create_index(
            field_name="embedding",
            index_params=dense_index_params,
        )

        # Sparse vector index for hybrid search
        if self.config.enable_hybrid_search:
            sparse_index_params = {
                "index_type": "SPARSE_INVERTED_INDEX",
                "metric_type": "IP",
            }
            self.collection.create_index(
                field_name="sparse_vector",
                index_params=sparse_index_params,
            )

        logger.info("Created indexes", collection=self.collection.name)

    async def insert_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Insert document chunks into the collection."""
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        if not chunks:
            return

        # Prepare data for insertion
        data = []
        for chunk in chunks:
            if not chunk.embedding:
                raise ValueError(f"Chunk {chunk.id} missing embedding")

            chunk_data = {
                "id": chunk.id,
                "embedding": chunk.embedding,
                "text": chunk.text,
                "metadata": chunk.metadata.dict(),
            }

            # Add sparse vector if available
            if self.config.enable_hybrid_search and chunk.sparse_vector:
                chunk_data["sparse_vector"] = chunk.sparse_vector

            data.append(chunk_data)

        # Insert data
        self.collection.insert(data)
        await self.collection.flush()

        logger.info(
            "Inserted chunks",
            count=len(chunks),
            collection=self.collection.name,
        )

    async def search(
        self,
        query_embedding: List[float],
        limit: int = 8,
        filters: Optional[str] = None,
        sparse_vector: Optional[Dict[str, float]] = None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        # Load collection
        self.collection.load()

        search_params = {
            "metric_type": self.config.collection.metric_type,
            "params": {"ef": self.config.collection.hnsw_ef_search},
        }

        try:
            if self.config.enable_hybrid_search and sparse_vector:
                # Hybrid search
                results = self.collection.hybrid_search(
                    reqs=[
                        {
                            "data": [query_embedding],
                            "anns_field": "embedding",
                            "param": search_params,
                            "limit": limit * 2,  # Get more for reranking
                            "expr": filters,
                        },
                        {
                            "data": [sparse_vector],
                            "anns_field": "sparse_vector",
                            "param": {"metric_type": "IP"},
                            "limit": limit * 2,
                            "expr": filters,
                        },
                    ],
                    rerank={
                        "strategy": "weighted",
                        "params": {"weights": [dense_weight, sparse_weight]},
                    },
                    limit=limit,
                    output_fields=["text", "metadata"],
                )
            else:
                # Dense search only
                results = self.collection.search(
                    data=[query_embedding],
                    anns_field="embedding",
                    param=search_params,
                    limit=limit,
                    expr=filters,
                    output_fields=["text", "metadata"],
                )

            # Convert results to SearchResult objects
            search_results = []
            for hits in results:
                for hit in hits:
                    search_result = SearchResult(
                        chunk_id=hit.id,
                        text=hit.entity.get("text"),
                        score=hit.distance,
                        metadata=hit.entity.get("metadata"),
                    )
                    search_results.append(search_result)

            return search_results

        except Exception as e:
            logger.error("Search failed", error=str(e))
            raise

    async def delete_by_source(self, source_path: str) -> int:
        """Delete all chunks from a specific source document."""
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        # Build filter expression
        expr = f'metadata["source_path"] == "{source_path}"'

        # Get IDs to delete
        results = self.collection.query(
            expr=expr,
            output_fields=["id"],
        )

        if not results:
            return 0

        # Delete by IDs
        ids = [result["id"] for result in results]
        self.collection.delete(expr=f"id in {ids}")

        logger.info(
            "Deleted chunks by source",
            source=source_path,
            count=len(ids),
        )

        return len(ids)

    async def check_document_exists(self, source_hash: str) -> bool:
        """Check if a document with the given hash already exists."""
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        expr = f'metadata["source_hash"] == "{source_hash}"'

        results = self.collection.query(
            expr=expr,
            output_fields=["id"],
            limit=1,
        )

        return len(results) > 0

    async def get_collection_stats(self) -> CollectionStats:
        """Get collection statistics."""
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        # Get basic stats
        stats = self.collection.get_stats()
        entity_count = int(stats["row_count"])

        # Get index info
        indexes = self.collection.indexes
        index_info = indexes[0] if indexes else None

        return CollectionStats(
            name=self.collection.name,
            entity_count=entity_count,
            index_type=index_info.params.get("index_type", "UNKNOWN") if index_info else "NONE",
            metric_type=index_info.params.get("metric_type", "UNKNOWN") if index_info else "NONE",
            dimension=self.config.collection.dimension,
        )

    async def health_check(self) -> bool:
        """Check if Milvus connection is healthy."""
        try:
            if not self._connected:
                return False

            # Try a simple operation
            collections = utility.list_collections()
            return True

        except Exception as e:
            logger.error("Milvus health check failed", error=str(e))
            return False