"""
Search Engine Integration Layer - Multi-Engine Research

This module provides unified interfaces for multiple search engines optimized for ADHD research:
- Exa: Semantic search for technical documentation
- Tavily: Developer-focused search with code examples
- Perplexity: Real-time web search with citations
- Context7: Official documentation prioritization

Features:
- Intelligent search orchestration with strategy-based routing
- Parallel execution for performance
- ADHD-optimized result combination and ranking
- Automatic deduplication and relevance scoring
- Progressive disclosure and cognitive load management

All adapters implement the BaseSearchAdapter interface for consistent results.
"""

from .base_adapter import (
    BaseSearchAdapter,
    SearchResult,
    SearchResultType,
    SourceQuality,
    SearchMetadata
)
from .search_orchestrator import SearchOrchestrator, SearchStrategy, SearchConfig, EngineWeight
from .exa_adapter import ExaSearchAdapter
from .tavily_adapter import TavilySearchAdapter
from .perplexity_adapter import PerplexitySearchAdapter
from .context7_adapter import Context7SearchAdapter

__all__ = [
    # Base classes and types
    "BaseSearchAdapter",
    "SearchResult",
    "SearchResultType",
    "SourceQuality",
    "SearchMetadata",

    # Orchestration
    "SearchOrchestrator",
    "SearchStrategy",
    "SearchConfig",
    "EngineWeight",

    # Search adapters
    "ExaSearchAdapter",
    "TavilySearchAdapter",
    "PerplexitySearchAdapter",
    "Context7SearchAdapter"
]