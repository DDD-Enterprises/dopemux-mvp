"""
Document Search - Docs Index
Multi-vector search for documents (PDFs, Markdown, HTML, DOCX) using Qdrant.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .dense_search import MultiVectorSearch, SearchProfile, SearchResult


logger = logging.getLogger(__name__)


class DocumentSearch:
    """
    Document search using Qdrant with multi-vector embeddings.

    Parallel to code search but optimized for documents:
    - voyage-context-3 embeddings
    - Document chunking (1000 chars with overlap)
    - Multi-vector: content, title, breadcrumb
    """

    def __init__(
        self,
        collection_name: str = "docs_index",
        url: str = "localhost",
        port: int = 6333,
        vector_size: int = 1024,
    ):
        """
        Initialize document search.

        Args:
            collection_name: Qdrant collection name for docs
            url: Qdrant server URL
            port: Qdrant server port
            vector_size: Embedding dimension (1024 for Voyage)
        """
        # Reuse MultiVectorSearch infrastructure
        self.search = MultiVectorSearch(
            collection_name=collection_name,
            url=url,
            port=port,
            vector_size=vector_size,
        )

    async def create_collection(self):
        """Create Qdrant collection for documents."""
        await self.search.create_collection()
        logger.info(f"Created docs collection: {self.search.collection_name}")

    async def index_document(
        self,
        doc_id: str,
        chunks: List[Dict],
        content_vectors: List[List[float]],
        title_vectors: List[List[float]],
        breadcrumb_vectors: List[List[float]],
    ) -> List[str]:
        """
        Index document chunks.

        Args:
            doc_id: Document ID
            chunks: List of chunk metadata
            content_vectors: Embeddings for chunk content
            title_vectors: Embeddings for chunk titles
            breadcrumb_vectors: Embeddings for breadcrumbs

        Returns:
            List of point IDs
        """
        points = []
        for i, (chunk, content_vec, title_vec, breadcrumb_vec) in enumerate(
            zip(chunks, content_vectors, title_vectors, breadcrumb_vectors)
        ):
            point_id = f"{doc_id}_chunk_{i}"
            payload = {
                "doc_id": doc_id,
                "chunk_index": i,
                "text": chunk["text"],
                "source_path": chunk.get("source_path", ""),
                "doc_type": chunk.get("doc_type", "unknown"),
                "page_number": chunk.get("page_number"),
                "workspace_id": chunk.get("workspace_id", "default"),
            }

            points.append((content_vec, title_vec, breadcrumb_vec, payload, point_id))

        point_ids = await self.search.insert_points_batch(points)
        return point_ids

    async def search_documents(
        self,
        query_vectors: Dict[str, List[float]],
        profile: Optional[SearchProfile] = None,
        filter_by: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """
        Search documents with multi-vector.

        Args:
            query_vectors: Dict with 'content', 'title', 'breadcrumb' vectors
            profile: Search profile
            filter_by: Optional filters

        Returns:
            List of SearchResult
        """
        return await self.search.search(
            query_content_vector=query_vectors.get("content", []),
            query_title_vector=query_vectors.get("title", []),
            query_breadcrumb_vector=query_vectors.get("breadcrumb", []),
            profile=profile,
            filter_by=filter_by,
        )
