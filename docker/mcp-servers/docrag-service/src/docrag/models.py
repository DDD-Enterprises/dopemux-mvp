"""
DocRAG data models and schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    DOCX = "docx"
    UNKNOWN = "unknown"


class VisibilityLevel(str, Enum):
    """Document visibility levels for access control."""
    PRIVATE = "private"
    WORKSPACE = "workspace"
    PUBLIC = "public"


class SourceType(str, Enum):
    """Document source types for filtering."""
    UPLOAD = "upload"
    API = "api"
    AI_GENERATED = "ai"


class ModelAttribution(BaseModel):
    """Model attribution for document versions following ADR-0034."""
    name: str
    provider: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""
    # Source information
    source_path: str
    source_hash: str
    title: Optional[str] = None

    # Chunk information
    chunk_index: int
    chunk_id: str = Field(default_factory=lambda: str(uuid4()))

    # Document structure
    page_number: Optional[int] = None
    section: Optional[str] = None
    heading: Optional[str] = None

    # Content properties
    char_count: int
    token_count: int
    content_hash: str

    # Classification and access control
    document_type: DocumentType
    tags: List[str] = Field(default_factory=list)
    sensitivity: str = "internal"  # public, internal, confidential, restricted
    visibility: VisibilityLevel = VisibilityLevel.PRIVATE
    source_type: SourceType = SourceType.UPLOAD
    owner: Optional[str] = None
    team: Optional[str] = None

    # Versioning (ADR-0034)
    version_number: int = 1
    created_by_model: Optional[ModelAttribution] = None
    change_summary: Optional[str] = None

    # Processing timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Additional metadata
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class DocumentChunk(BaseModel):
    """A processed document chunk ready for indexing."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    embedding: Optional[List[float]] = None
    sparse_vector: Optional[Dict[str, float]] = None
    metadata: ChunkMetadata

    @validator('text')
    def validate_text_length(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Chunk text cannot be empty")
        if len(v) > 8000:  # Milvus VARCHAR limit
            raise ValueError("Chunk text too long for Milvus storage")
        return v


class SearchQuery(BaseModel):
    """Search query request."""
    query: str
    limit: int = Field(default=8, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = None
    rerank: bool = True
    hybrid: bool = False
    dense_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    sparse_weight: float = Field(default=0.4, ge=0.0, le=1.0)

    @validator('dense_weight', 'sparse_weight')
    def validate_weights(cls, v, values):
        if 'dense_weight' in values and 'sparse_weight' in values:
            if abs((values['dense_weight'] + values['sparse_weight']) - 1.0) > 0.01:
                raise ValueError("Dense and sparse weights must sum to 1.0")
        return v


class SearchResult(BaseModel):
    """Single search result."""
    chunk_id: str
    text: str
    score: float
    metadata: ChunkMetadata
    rerank_score: Optional[float] = None


class CodeSearchResult(BaseModel):
    """Search result for code search (specialized)."""
    id: str
    score: float
    file_path: str
    function_name: Optional[str] = None
    language: str
    content: str
    context_snippet: Optional[str] = None
    complexity: float = 0.0
    start_line: int = 0
    end_line: int = 0


class SearchResponse(BaseModel):
    """Search response with results and metadata."""
    results: List[SearchResult]
    query: str
    total_found: int
    search_time_ms: float
    rerank_time_ms: Optional[float] = None
    hybrid_search: bool = False


class IngestionRequest(BaseModel):
    """Document ingestion request."""
    source_path: str
    content: Optional[str] = None  # If not provided, will read from source_path
    document_type: Optional[DocumentType] = None  # Auto-detect if not provided
    metadata: Optional[Dict[str, Any]] = None
    chunk_size: int = Field(default=1000, ge=100, le=2000)
    chunk_overlap: int = Field(default=100, ge=0, le=500)
    force_reindex: bool = False


class IngestionResponse(BaseModel):
    """Document ingestion response."""
    success: bool
    message: str
    chunks_created: int
    source_path: str
    source_hash: str
    processing_time_ms: float


class CollectionStats(BaseModel):
    """Milvus collection statistics."""
    name: str
    entity_count: int
    index_type: str
    metric_type: str
    dimension: int
    created_at: Optional[datetime] = None


class HealthStatus(BaseModel):
    """Service health status."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    milvus_connected: bool
    voyage_api_available: bool
    collections: List[CollectionStats]
    version: str = "0.1.0"


class DocumentVersion(BaseModel):
    """Document version history entry (ADR-0034)."""
    version_number: int
    content_hash: str
    change_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_model: Optional[ModelAttribution] = None
    chunk_count: int = 0
    size_bytes: int = 0


class BulkOperationRequest(BaseModel):
    """Bulk operation request for multiple documents."""
    operation: str  # "upload" | "delete" | "update"
    documents: List[Union[str, Dict[str, Any]]]  # paths or document data
    options: Dict[str, Any] = Field(default_factory=dict)


class BulkOperationResponse(BaseModel):
    """Bulk operation response."""
    success: bool
    total_requested: int
    total_processed: int
    total_failed: int
    results: List[Dict[str, Any]]
    processing_time_ms: float
    errors: List[str] = Field(default_factory=list)


class AdvancedSearchFilters(BaseModel):
    """Advanced search filters following ADR-0034."""
    source_type: Optional[SourceType] = None
    visibility: Optional[VisibilityLevel] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    owner: Optional[str] = None
    team: Optional[str] = None
    min_version: Optional[int] = None
    content_type: Optional[DocumentType] = None


class SearchAnalytics(BaseModel):
    """Search analytics data."""
    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    results_count: int
    query_time_ms: int
    user_id: Optional[str] = None
    filters_used: Dict[str, Any] = Field(default_factory=dict)
    clicked_results: List[str] = Field(default_factory=list)