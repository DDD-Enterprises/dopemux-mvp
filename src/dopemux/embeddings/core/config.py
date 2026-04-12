"""
Core configuration and enums for the advanced embedding system.

Provides production-grade configuration with expert-validated defaults,
ADHD-optimized settings, and security policy enforcement.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    """Supported vector index types."""
    HNSW = "hnsw"              # Hierarchical Navigable Small World
    IVF_PQ = "ivf_pq"          # Inverted File with Product Quantization
    SCANN = "scann"            # Scalable Nearest Neighbors


class SecurityLevel(str, Enum):
    """Security levels for document processing."""
    PUBLIC = "public"          # No restrictions
    INTERNAL = "internal"      # Company-internal documents
    CONFIDENTIAL = "confidential"  # Requires PII redaction
    RESTRICTED = "restricted"  # On-premise only, no cloud APIs


@dataclass
class AdvancedEmbeddingConfig:
    """
    Production-grade embedding configuration.

    Implements expert recommendations for voyage-context-3 + hybrid search architecture.
    Includes ADHD-optimized defaults and automatic security policy enforcement.
    """

    # === Core Model Configuration ===
    embedding_model: str = "voyage-context-3"
    rerank_model: str = "voyage-rerank-2.5"
    embedding_dimension: int = 2048
    max_seq_length: int = 4000  # voyage-context-3 supports up to 32k

    # === Hybrid Search Configuration ===
    # Initial static weights (will be optimized via learning-to-rank)
    bm25_weight: float = 0.3
    vector_weight: float = 0.7
    enable_learning_to_rank: bool = False  # Requires training data

    # === Vector Index Configuration ===
    index_type: IndexType = IndexType.HNSW
    enable_quantization: bool = True       # 8-bit PQ for 4x memory reduction
    distance_metric: str = "cosine"        # cosine, l2, ip

    # HNSW-specific parameters (expert-recommended)
    hnsw_m: int = 32                      # Connections per node
    hnsw_ef: int = 128                    # Search parameter
    hnsw_ef_construction: int = 200       # Build parameter

    # IVF-PQ parameters
    ivf_nlist: int = 2048                 # Number of clusters
    pq_m: int = 64                        # Product quantization subspaces

    # === Performance Configuration ===
    batch_size: int = 8                   # Embedding batch size (GPU optimized)
    top_k_candidates: int = 25            # Candidates for reranking (vs 100)
    rerank_batch_size: int = 4            # Reranker batch size
    max_concurrent_requests: int = 10     # API concurrency limit

    # === Storage Configuration ===
    persist_directory: str = "./.advanced_vectors"
    cache_embeddings: bool = True         # Cache by (doc_sha256, model_version)
    enable_compression: bool = True       # Additional storage compression

    # === Security & Privacy ===
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    enable_pii_redaction: bool = False    # Auto-enabled for CONFIDENTIAL+
    use_on_premise: bool = False          # Use local models vs APIs
    redaction_patterns: List[str] = field(default_factory=list)

    # === API Configuration ===
    voyage_api_key: Optional[str] = None  # Set via environment
    api_base_url: str = "https://api.voyageai.com/v1"
    request_timeout: int = 30             # API timeout in seconds
    retry_attempts: int = 3               # Failed request retries

    # === ADHD Optimization ===
    enable_progress_tracking: bool = True
    progress_update_interval: int = 100   # Update every N documents
    visual_progress_indicators: bool = True
    gentle_error_messages: bool = True

    # === Multi-Model Consensus ===
    enable_consensus: bool = False        # Expensive, use selectively
    consensus_models: List[str] = field(default_factory=lambda: [
        "text-embedding-3-large",         # OpenAI comparison
        "embed-english-v3.0"              # Cohere comparison
    ])
    consensus_threshold: float = 0.9      # Cosine similarity threshold

    # === Cost Management ===
    monthly_budget_usd: Optional[float] = None
    enable_cost_tracking: bool = True
    cost_alert_threshold: float = 0.8     # Alert at 80% budget

    def __post_init__(self):
        """Validate configuration and apply security policies."""
        # Auto-enable PII redaction for sensitive data
        if self.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
            self.enable_pii_redaction = True

        # Force on-premise for restricted data
        if self.security_level == SecurityLevel.RESTRICTED:
            self.use_on_premise = True
            logger.warning("🔒 Restricted data detected - forcing on-premise processing")

        # Validate dimensions
        if self.embedding_dimension not in [1024, 2048]:
            logger.warning(f"⚠️ Unusual embedding dimension: {self.embedding_dimension}")

        # Validate weights
        if abs(self.bm25_weight + self.vector_weight - 1.0) > 0.01:
            raise ValueError("BM25 and vector weights must sum to 1.0")

        # Set default redaction patterns for PII
        if self.enable_pii_redaction and not self.redaction_patterns:
            self.redaction_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',        # SSN
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                r'\b\(\d{3}\)\s?\d{3}-\d{4}\b',  # Phone numbers
            ]