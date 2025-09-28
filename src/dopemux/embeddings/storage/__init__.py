"""
Storage implementations for the embedding system.

Provides vector indices, text indices, ranking algorithms, and the main
hybrid store that orchestrates all components for production-grade search.
"""

# Base abstractions
from .base import (
    BaseVectorIndex,
    BaseTextIndex,
    BaseRanker,
    BaseDocumentStore
)

# Vector index implementations
from .vector_indices import (
    HNSWIndex,
    FAISSIndex
)

# Text index implementations
from .text_indices import (
    BM25Index
)

# Ranking algorithms
from .ranking import (
    HybridRanker,
    RRFFusion
)

# Main hybrid store
from .hybrid_store import (
    HybridVectorStore,
    InMemoryDocumentStore
)

__all__ = [
    # Base abstractions
    "BaseVectorIndex",
    "BaseTextIndex",
    "BaseRanker",
    "BaseDocumentStore",

    # Vector indices
    "HNSWIndex",
    "FAISSIndex",

    # Text indices
    "BM25Index",

    # Ranking algorithms
    "HybridRanker",
    "RRFFusion",

    # Main store and document storage
    "HybridVectorStore",
    "InMemoryDocumentStore"
]