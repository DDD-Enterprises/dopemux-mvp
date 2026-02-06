"""Document search wrapper for docs collections."""

import logging
from typing import Dict, List, Optional

from qdrant_client.http import models

from .dense_search import MultiVectorSearch, SearchProfile, SearchResult


logger = logging.getLogger(__name__)


class DocumentSearch(MultiVectorSearch):
    """
    Qdrant-backed document search using the existing multi-vector engine.

    Docs use the same 3-vector schema as code collections:
    - content_vec
    - title_vec
    - breadcrumb_vec
    """

    async def create_collection(self):
        """Create the docs collection and docs-specific payload indexes."""
        await super().create_collection()

        for field_name in ("doc_type", "source_path", "title"):
            try:
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception as exc:
                # Index creation can fail if the index already exists.
                logger.debug(
                    "Payload index '%s' create skipped for '%s': %s",
                    field_name,
                    self.collection_name,
                    exc,
                )

    async def search_documents(
        self,
        query_vectors: Dict[str, List[float]],
        top_k: int = 100,
        filter_by: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """
        Search docs with defaults tuned for natural-language documentation queries.
        """
        content = query_vectors.get("content")
        if not content:
            raise ValueError("query_vectors.content is required")

        title = query_vectors.get("title") or content
        breadcrumb = query_vectors.get("breadcrumb") or content

        profile = SearchProfile(
            name="docs",
            top_k=top_k,
            content_weight=0.85,
            title_weight=0.1,
            breadcrumb_weight=0.05,
            ef=150,
        )

        return await self.search(
            query_content_vector=content,
            query_title_vector=title,
            query_breadcrumb_vector=breadcrumb,
            profile=profile,
            filter_by=filter_by,
        )
