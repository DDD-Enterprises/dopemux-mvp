"""
DocRAG - Document Retrieval and Generation service for Dopemux.

A semantic search service that combines Milvus vector database with Voyage AI
embeddings and reranking for high-quality document retrieval.
"""

from .config import DocRAGConfig, get_config
from .models import (
    DocumentChunk,
    DocumentType,
    HealthStatus,
    IngestionRequest,
    IngestionResponse,
    SearchQuery,
    SearchResponse,
)
from .service import DocRAGService

__version__ = "0.1.0"
__all__ = [
    "DocRAGConfig",
    "get_config",
    "DocRAGService",
    "DocumentChunk",
    "DocumentType",
    "HealthStatus",
    "IngestionRequest",
    "IngestionResponse",
    "SearchQuery",
    "SearchResponse",
]