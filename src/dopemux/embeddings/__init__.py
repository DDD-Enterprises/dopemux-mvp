"""
Advanced Embedding System for dopemux-mvp

Production-grade semantic search with voyage-context-3, hybrid BM25+vector fusion,
multi-model consensus validation, and ADHD-optimized interfaces.

Quick Start:
    >>> from dopemux.embeddings import HybridVectorStore, AdvancedEmbeddingConfig
    >>> config = AdvancedEmbeddingConfig(embedding_model="voyage-context-3")
    >>> store = HybridVectorStore(config)
    >>> await store.add_documents([{"id": "1", "content": "Hello world"}])
    >>> results = await store.search("greeting", k=5)

Architecture Overview:
    - core/: Provider-agnostic abstractions and interfaces
    - providers/: Voyage AI, OpenAI, Cohere implementations
    - storage/: HNSW vector indices and BM25 lexical search
    - enhancers/: Consensus validation and ADHD health metrics
    - integrations/: ConPort, Serena, and CLAUDE.md adapters
    - pipelines/: Document processing and search workflows
"""

# Core abstractions
from .core import (
    AdvancedEmbeddingConfig,
    EmbeddingHealthMetrics,
    SearchResult,
    IndexType,
    SecurityLevel,
    create_production_config,
    create_development_config,
    create_research_config,
    create_high_security_config,
    create_high_performance_config,
    create_adhd_optimized_config
)

# Provider implementations
from .providers import VoyageAPIClient

# Storage implementations
from .storage import (
    HybridVectorStore,
    HNSWIndex,
    BM25Index,
    HybridRanker,
    FAISSIndex,
    RRFFusion,
    InMemoryDocumentStore
)

# Enhancement layers
from .enhancers import (
    ConsensusValidator,
    ConsensusConfig,
    ConsensusResult,
    ModelProvider,
    create_consensus_config
)

# Integration adapters
from .integrations import (
    ConPortAdapter,
    SerenaAdapter
)

# Pipeline orchestrators
from .pipelines import (
    DocumentPipeline,
    SearchPipeline,
    SyncPipeline
)

__version__ = "1.0.0"
__author__ = "Dopemux Development Team"

# Public API exports
__all__ = [
    # Core configuration and types
    "AdvancedEmbeddingConfig",
    "EmbeddingHealthMetrics",
    "SearchResult",
    "IndexType",
    "SecurityLevel",

    # Configuration presets
    "create_production_config",
    "create_development_config",
    "create_research_config",
    "create_high_security_config",
    "create_high_performance_config",
    "create_adhd_optimized_config",

    # Provider implementations
    "VoyageAPIClient",

    # Storage systems
    "HybridVectorStore",
    "HNSWIndex",
    "BM25Index",
    "HybridRanker",
    "FAISSIndex",
    "RRFFusion",
    "InMemoryDocumentStore",

    # Enhancement layers
    "ConsensusValidator",
    "ConsensusConfig",
    "ConsensusResult",
    "ModelProvider",
    "create_consensus_config",

    # Integration adapters
    "ConPortAdapter",
    "SerenaAdapter",

    # Pipeline orchestrators
    "DocumentPipeline",
    "SearchPipeline",
    "SyncPipeline",
]