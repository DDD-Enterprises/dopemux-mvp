"""
DocRAG service configuration.
"""

import os
from typing import List, Optional

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class MilvusConfig(BaseSettings):
    """Milvus database configuration."""
    host: str = Field(default="milvus", env="MILVUS_HOST")
    port: int = Field(default=19530, env="MILVUS_PORT")
    token: Optional[str] = Field(default=None, env="MILVUS_TOKEN")
    timeout: float = Field(default=10.0, env="MILVUS_TIMEOUT")

    @property
    def uri(self) -> str:
        """Get Milvus connection URI."""
        return f"http://{self.host}:{self.port}"


class VoyageConfig(BaseSettings):
    """Voyage AI configuration."""
    api_key: str = Field(env="VOYAGEAI_API_KEY")
    embed_model: str = Field(default="voyage-3", env="VOYAGE_EMBED_MODEL")
    rerank_model: str = Field(default="rerank-2.5", env="VOYAGE_RERANK_MODEL")
    timeout: float = Field(default=30.0, env="VOYAGE_TIMEOUT")
    max_retries: int = Field(default=3, env="VOYAGE_MAX_RETRIES")


class CollectionConfig(BaseSettings):
    """Milvus collection configuration."""
    docs_collection: str = Field(default="docs_index", env="DOCS_COLLECTION_NAME")
    dimension: int = Field(default=1024, env="EMBEDDING_DIMENSION")
    metric_type: str = Field(default="COSINE", env="METRIC_TYPE")

    # Index parameters
    index_type: str = Field(default="HNSW", env="INDEX_TYPE")
    hnsw_m: int = Field(default=16, env="HNSW_M")
    hnsw_ef_construction: int = Field(default=200, env="HNSW_EF_CONSTRUCTION")
    hnsw_ef_search: int = Field(default=64, env="HNSW_EF_SEARCH")

    @validator('metric_type')
    def validate_metric_type(cls, v):
        valid_metrics = ["COSINE", "IP", "L2"]
        if v not in valid_metrics:
            raise ValueError(f"Metric type must be one of {valid_metrics}")
        return v


class ChunkingConfig(BaseSettings):
    """Document chunking configuration."""
    default_chunk_size: int = Field(default=1000, env="DEFAULT_CHUNK_SIZE")
    default_chunk_overlap: int = Field(default=100, env="DEFAULT_CHUNK_OVERLAP")
    max_chunk_size: int = Field(default=2000, env="MAX_CHUNK_SIZE")
    min_chunk_size: int = Field(default=100, env="MIN_CHUNK_SIZE")

    @validator('default_chunk_overlap')
    def validate_overlap(cls, v, values):
        if 'default_chunk_size' in values and v >= values['default_chunk_size']:
            raise ValueError("Chunk overlap must be less than chunk size")
        return v


class SecurityConfig(BaseSettings):
    """Security and access control configuration."""
    allowed_extensions: List[str] = Field(
        default=[".pdf", ".md", ".html", ".txt", ".docx"],
        env="ALLOWED_EXTENSIONS"
    )
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    enable_acl: bool = Field(default=True, env="ENABLE_ACL")
    default_sensitivity: str = Field(default="internal", env="DEFAULT_SENSITIVITY")

    @validator('allowed_extensions')
    def validate_extensions(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string from environment
            return [ext.strip() for ext in v.split(",")]
        return v


class DocRAGConfig(BaseSettings):
    """Main DocRAG service configuration."""
    # Service settings
    host: str = Field(default="0.0.0.0", env="DOCRAG_HOST")
    port: int = Field(default=3009, env="DOCRAG_PORT")
    workers: int = Field(default=1, env="DOCRAG_WORKERS")

    # Feature flags
    enable_hybrid_search: bool = Field(default=True, env="ENABLE_HYBRID_SEARCH")
    enable_reranking: bool = Field(default=True, env="ENABLE_RERANKING")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")

    # Performance settings
    search_timeout: float = Field(default=10.0, env="SEARCH_TIMEOUT")
    ingest_timeout: float = Field(default=300.0, env="INGEST_TIMEOUT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    # Sub-configurations
    milvus: MilvusConfig = Field(default_factory=MilvusConfig)
    voyage: VoyageConfig = Field(default_factory=VoyageConfig)
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


def get_config() -> DocRAGConfig:
    """Get application configuration."""
    return DocRAGConfig()