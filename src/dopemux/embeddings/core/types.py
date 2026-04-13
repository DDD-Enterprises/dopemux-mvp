"""
Common data types and structures for the embedding system.

Defines result types, document formats, and other shared data structures
used across the embedding pipeline.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """Enhanced search result with hybrid scoring details."""

    doc_id: str
    score: float
    content: str
    metadata: Dict[str, Any]

    # Hybrid search details
    bm25_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: Optional[float] = None
    consensus_score: Optional[float] = None

    # Source information
    source_file: Optional[str] = None
    chunk_index: Optional[int] = None
    confidence: float = 1.0


@dataclass
class Document:
    """
    Document representation for embedding and storage.

    Standardized format for documents flowing through the embedding pipeline.
    """

    id: str
    content: str
    metadata: Dict[str, Any]

    # Optional preprocessing results
    embedding: Optional[List[float]] = None
    chunks: Optional[List[str]] = None

    # Source tracking
    source_path: Optional[str] = None
    last_modified: Optional[str] = None
    content_hash: Optional[str] = None


@dataclass
class EmbeddingRequest:
    """
    Request structure for embedding generation.

    Encapsulates all information needed to generate embeddings for documents.
    """

    texts: List[str]
    model: str
    batch_size: int = 8

    # Optional parameters
    encoding_format: str = "float"
    truncate: bool = True

    # Metadata
    request_id: Optional[str] = None
    priority: int = 0  # 0 = normal, higher = higher priority


@dataclass
class EmbeddingResponse:
    """
    Response structure from embedding generation.

    Contains embeddings and usage information for cost tracking.
    """

    embeddings: List[List[float]]
    model: str

    # Usage tracking
    total_tokens: int
    prompt_tokens: int

    # Performance metrics
    processing_time_ms: float
    request_id: Optional[str] = None

    # Cost information
    estimated_cost_usd: float = 0.0


@dataclass
class RerankRequest:
    """
    Request structure for document reranking.

    Encapsulates query and documents for relevance reranking.
    """

    query: str
    documents: List[str]
    model: str

    # Optional parameters
    top_k: Optional[int] = None
    return_documents: bool = False

    # Metadata
    request_id: Optional[str] = None


@dataclass
class RerankResponse:
    """
    Response structure from reranking.

    Contains relevance scores and optional reranked documents.
    """

    scores: List[float]
    model: str

    # Optional reranked documents
    documents: Optional[List[str]] = None

    # Performance metrics
    processing_time_ms: float
    request_id: Optional[str] = None

    # Cost information
    estimated_cost_usd: float = 0.0


@dataclass
class IndexStats:
    """
    Statistics about a search index.

    Provides insights into index size, performance, and usage.
    """

    total_documents: int
    total_vectors: int
    index_size_mb: float

    # Performance metrics
    avg_search_time_ms: float
    total_searches: int

    # Memory usage
    memory_usage_mb: float
    cache_hit_rate: float = 0.0

    # Last updated
    last_update: Optional[str] = None


@dataclass
class HybridSearchRequest:
    """
    Request structure for hybrid search combining lexical and vector search.

    Encapsulates all parameters needed for sophisticated search operations.
    """

    query: str
    k: int = 10

    # Search mode weights
    bm25_weight: float = 0.3
    vector_weight: float = 0.7

    # Optional filters
    metadata_filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None

    # Reranking options
    enable_reranking: bool = False
    rerank_top_k: int = 25

    # Performance options
    timeout_ms: int = 5000
    explain_scores: bool = False


@dataclass
class HybridSearchResponse:
    """
    Response from hybrid search with detailed scoring information.

    Provides comprehensive results with score breakdowns for analysis.
    """

    results: List[SearchResult]
    total_found: int

    # Search performance
    search_time_ms: float
    rerank_time_ms: float = 0.0

    # Score analysis
    fusion_method: str = "weighted_sum"
    score_stats: Optional[Dict[str, float]] = None

    # Debug information
    explain: Optional[Dict[str, Any]] = None