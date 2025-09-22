"""
Core DocRAG service for document ingestion and search.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

import structlog

from .config import DocRAGConfig
from .database import MilvusDatabase
from .embeddings import SparseEncoder, VoyageEmbeddings
from .models import (
    DocumentChunk,
    HealthStatus,
    IngestionRequest,
    IngestionResponse,
    SearchQuery,
    SearchResponse,
)
from .processing import DocumentProcessor

logger = structlog.get_logger(__name__)


class DocRAGService:
    """Main DocRAG service orchestrating all components."""

    def __init__(self, config: DocRAGConfig):
        """Initialize DocRAG service."""
        self.config = config
        self.db = MilvusDatabase(config)
        self.embeddings = VoyageEmbeddings(config)
        self.processor = DocumentProcessor()
        self.sparse_encoder = SparseEncoder() if config.enable_hybrid_search else None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all service components."""
        try:
            # Connect to Milvus
            await self.db.connect()

            # Test Voyage AI connection
            if self.config.enable_reranking:
                await self.embeddings.health_check()

            self._initialized = True
            logger.info("DocRAG service initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize DocRAG service", error=str(e))
            raise

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        if self._initialized:
            await self.db.disconnect()
            await self.embeddings.close()
            self._initialized = False
            logger.info("DocRAG service shutdown complete")

    async def ingest_document(self, request: IngestionRequest) -> IngestionResponse:
        """Ingest a document into the search index."""
        start_time = time.time()

        if not self._initialized:
            raise RuntimeError("Service not initialized")

        try:
            # Validate file path
            file_path = Path(request.source_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {request.source_path}")

            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.security.max_file_size_mb:
                raise ValueError(
                    f"File too large: {file_size_mb:.1f}MB "
                    f"(max: {self.config.security.max_file_size_mb}MB)"
                )

            # Check file extension
            if file_path.suffix.lower() not in self.config.security.allowed_extensions:
                raise ValueError(f"File type not allowed: {file_path.suffix}")

            logger.info("Starting document ingestion", source=request.source_path)

            # Process document into chunks
            chunks = self.processor.process_document(
                file_path=request.source_path,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                metadata_override=request.metadata,
            )

            if not chunks:
                raise ValueError("No chunks generated from document")

            # Check if document already exists (unless force reindex)
            if not request.force_reindex:
                source_hash = chunks[0].metadata.source_hash
                if await self.db.check_document_exists(source_hash):
                    logger.info(
                        "Document already indexed, skipping",
                        source=request.source_path,
                        hash=source_hash,
                    )
                    return IngestionResponse(
                        success=True,
                        message="Document already indexed",
                        chunks_created=0,
                        source_path=request.source_path,
                        source_hash=source_hash,
                        processing_time_ms=(time.time() - start_time) * 1000,
                    )

            # Generate embeddings for all chunks
            texts = [chunk.text for chunk in chunks]
            embeddings = await self.embeddings.embed_texts(texts)

            # Generate sparse vectors if hybrid search enabled
            sparse_vectors = None
            if self.config.enable_hybrid_search and self.sparse_encoder:
                sparse_vectors = await self.sparse_encoder.encode_texts(texts)

            # Attach embeddings and sparse vectors to chunks
            for i, chunk in enumerate(chunks):
                chunk.embedding = embeddings[i]
                if sparse_vectors:
                    chunk.sparse_vector = sparse_vectors[i]

            # Delete existing chunks from same source if reindexing
            if request.force_reindex:
                await self.db.delete_by_source(request.source_path)

            # Insert chunks into database
            await self.db.insert_chunks(chunks)

            processing_time = (time.time() - start_time) * 1000
            source_hash = chunks[0].metadata.source_hash

            logger.info(
                "Document ingestion completed",
                source=request.source_path,
                chunks=len(chunks),
                processing_time_ms=processing_time,
            )

            return IngestionResponse(
                success=True,
                message=f"Successfully ingested {len(chunks)} chunks",
                chunks_created=len(chunks),
                source_path=request.source_path,
                source_hash=source_hash,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(
                "Document ingestion failed",
                source=request.source_path,
                error=str(e),
                processing_time_ms=processing_time,
            )

            return IngestionResponse(
                success=False,
                message=f"Ingestion failed: {str(e)}",
                chunks_created=0,
                source_path=request.source_path,
                source_hash="",
                processing_time_ms=processing_time,
            )

    async def search_documents(self, query: SearchQuery) -> SearchResponse:
        """Search for documents using semantic and/or hybrid search."""
        start_time = time.time()

        if not self._initialized:
            raise RuntimeError("Service not initialized")

        try:
            logger.debug("Starting document search", query=query.query, limit=query.limit)

            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(query.query)

            # Generate sparse query vector if hybrid search
            sparse_query = None
            if query.hybrid and self.config.enable_hybrid_search and self.sparse_encoder:
                sparse_query = self.sparse_encoder.encode(query.query)

            # Build filters expression
            filters = None
            if query.filters:
                # Convert filters to Milvus expression format
                filter_parts = []
                for key, value in query.filters.items():
                    if isinstance(value, str):
                        filter_parts.append(f'metadata["{key}"] == "{value}"')
                    elif isinstance(value, list):
                        values_str = '", "'.join(str(v) for v in value)
                        filter_parts.append(f'metadata["{key}"] in ["{values_str}"]')

                if filter_parts:
                    filters = " and ".join(filter_parts)

            # Perform search
            search_limit = query.limit * 4 if query.rerank else query.limit
            results = await self.db.search(
                query_embedding=query_embedding,
                limit=search_limit,
                filters=filters,
                sparse_vector=sparse_query,
                dense_weight=query.dense_weight,
                sparse_weight=query.sparse_weight,
            )

            search_time = (time.time() - start_time) * 1000

            # Apply reranking if enabled
            rerank_time = None
            if query.rerank and self.config.enable_reranking and results:
                rerank_start = time.time()
                results = await self.embeddings.rerank_search_results(
                    query=query.query,
                    results=results,
                    top_k=query.limit,
                )
                rerank_time = (time.time() - rerank_start) * 1000

            total_time = (time.time() - start_time) * 1000

            logger.debug(
                "Document search completed",
                results_count=len(results),
                search_time_ms=search_time,
                rerank_time_ms=rerank_time,
                total_time_ms=total_time,
            )

            return SearchResponse(
                results=results,
                query=query.query,
                total_found=len(results),
                search_time_ms=total_time,
                rerank_time_ms=rerank_time,
                hybrid_search=query.hybrid and sparse_query is not None,
            )

        except Exception as e:
            logger.error("Document search failed", query=query.query, error=str(e))
            raise

    async def get_health_status(self) -> HealthStatus:
        """Get service health status."""
        try:
            # Check Milvus connection
            milvus_healthy = await self.db.health_check()

            # Check Voyage AI availability
            voyage_healthy = False
            if self.config.enable_reranking:
                voyage_healthy = await self.embeddings.health_check()

            # Get collection stats
            collections = []
            if milvus_healthy:
                try:
                    stats = await self.db.get_collection_stats()
                    collections.append(stats)
                except Exception:
                    pass

            status = "healthy" if milvus_healthy else "unhealthy"
            if self.config.enable_reranking and not voyage_healthy:
                status = "degraded"

            return HealthStatus(
                status=status,
                milvus_connected=milvus_healthy,
                voyage_api_available=voyage_healthy,
                collections=collections,
            )

        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return HealthStatus(
                status="unhealthy",
                milvus_connected=False,
                voyage_api_available=False,
                collections=[],
            )