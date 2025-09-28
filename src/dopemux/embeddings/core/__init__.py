"""
Core abstractions for the advanced embedding system.

Provides provider-agnostic interfaces, configuration classes, and data types
that form the foundation of the embedding architecture.
"""

# Configuration and enums
from .config import (
    AdvancedEmbeddingConfig,
    IndexType,
    SecurityLevel
)

# Interfaces and protocols
from .interfaces import (
    EmbeddingProvider,
    RerankProvider,
    VectorStore,
    TextSearchIndex,
    HybridRanker,
    AsyncContextManager,
    # Exceptions
    EmbeddingError,
    RerankError,
    VectorStoreError,
    SearchError,
    FusionError,
    IndexError
)

# Data types and structures
from .types import (
    SearchResult,
    Document,
    EmbeddingRequest,
    EmbeddingResponse,
    RerankRequest,
    RerankResponse,
    IndexStats,
    HybridSearchRequest,
    HybridSearchResponse
)

# Metrics and monitoring
from .metrics import EmbeddingHealthMetrics

# Configuration presets
from .presets import (
    create_production_config,
    create_development_config,
    create_research_config,
    create_high_security_config,
    create_high_performance_config,
    create_adhd_optimized_config
)

__all__ = [
    # Configuration
    "AdvancedEmbeddingConfig",
    "IndexType",
    "SecurityLevel",

    # Interfaces
    "EmbeddingProvider",
    "RerankProvider",
    "VectorStore",
    "TextSearchIndex",
    "HybridRanker",
    "AsyncContextManager",

    # Data types
    "SearchResult",
    "Document",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "RerankRequest",
    "RerankResponse",
    "IndexStats",
    "HybridSearchRequest",
    "HybridSearchResponse",

    # Metrics
    "EmbeddingHealthMetrics",

    # Presets
    "create_production_config",
    "create_development_config",
    "create_research_config",
    "create_high_security_config",
    "create_high_performance_config",
    "create_adhd_optimized_config",

    # Exceptions
    "EmbeddingError",
    "RerankError",
    "VectorStoreError",
    "SearchError",
    "FusionError",
    "IndexError"
]