"""
Graph Enrichment - Code Relationship Intelligence

Enriches semantic search results with code graph data from Serena v2.
Provides relationship context: callers, callees, imports, impact analysis.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentConfig:
    """Configuration for graph enrichment."""

    enabled: bool = True
    max_results_to_enrich: int = 10  # Only enrich top N
    cache_ttl_seconds: int = 300  # 5 minutes
    include_top_callers: int = 3  # Show top N callers
    include_impact_analysis: bool = True


class GraphEnrichment:
    """
    Enriches semantic search results with code graph relationship data.

    Queries Serena v2 code graph to add:
    - Relationship counts (called_by, calls, imported_by, imports)
    - Top callers (most common usage sites)
    - Impact analysis (change risk assessment)
    """

    def __init__(
        self,
        serena_client=None,
        config: Optional[EnrichmentConfig] = None,
    ):
        """
        Initialize graph enrichment.

        Args:
            serena_client: Serena v2 MCP client (optional, graceful degradation)
            config: Enrichment configuration
        """
        self.serena = serena_client
        self.config = config or EnrichmentConfig()
        self._cache: Dict[str, Dict] = {}

    async def enrich_results(
        self, search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich search results with relationship data.

        Args:
            search_results: Results from semantic search

        Returns:
            Enhanced results with relationship metadata
        """
        if not self.config.enabled or not self.serena:
            # Return unchanged if disabled or Serena unavailable
            if not self.serena:
                logger.debug(
                    "Serena client unavailable, skipping graph enrichment"
                )
            return search_results

        enriched = []
        max_enrich = self.config.max_results_to_enrich

        for idx, result in enumerate(search_results):
            if idx >= max_enrich:
                # Don't enrich beyond limit (performance optimization)
                enriched.append(result)
                continue

            # Get graph data from Serena
            graph_data = await self._get_graph_data(
                result.get("file_path", ""),
                result.get("function_name", ""),
            )

            if graph_data:
                # Add relationship metadata
                result["relationships"] = {
                    "called_by": len(graph_data.get("callers", [])),
                    "calls": len(graph_data.get("callees", [])),
                    "imported_by": len(graph_data.get("importers", [])),
                    "imports": len(graph_data.get("imports", [])),
                    "top_callers": graph_data.get("callers", [])[
                        : self.config.include_top_callers
                    ],
                }

                # Add impact analysis if enabled
                if self.config.include_impact_analysis:
                    result["impact_analysis"] = self._calculate_impact(
                        graph_data
                    )

            enriched.append(result)

        logger.debug(
            f"Enriched {min(len(search_results), max_enrich)} results with graph data"
        )

        return enriched

    async def _get_graph_data(
        self, file_path: str, symbol: str
    ) -> Optional[Dict]:
        """
        Get code graph data from Serena with caching.

        Args:
            file_path: File path
            symbol: Symbol name (function/class)

        Returns:
            Graph data dict or None
        """
        if not file_path or not symbol:
            return None

        # Check cache
        cache_key = f"{file_path}:{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Query Serena MCP for code graph
            # TODO: Implement get_code_graph() in Serena MCP
            graph_data = await self.serena.get_code_graph(
                file_path=file_path, symbol=symbol
            )

            # Cache for TTL
            self._cache[cache_key] = graph_data

            # Simple cache size management
            if len(self._cache) > 1000:
                # Evict oldest (FIFO)
                self._cache.pop(next(iter(self._cache)))

            return graph_data

        except Exception as e:
            logger.warning(f"Failed to get graph data from Serena: {e}")
            return None

    def _calculate_impact(self, graph_data: Dict) -> Dict[str, Any]:
        """
        Calculate change impact based on graph relationships.

        Args:
            graph_data: Graph data from Serena

        Returns:
            Impact analysis dict
        """
        callers = graph_data.get("callers", [])
        importers = graph_data.get("importers", [])

        total_affected = len(callers) + len(importers)

        # Risk categories
        if total_affected > 20:
            risk = "high"
        elif total_affected > 5:
            risk = "medium"
        else:
            risk = "low"

        return {
            "change_risk": risk,
            "affected_files": total_affected,
            "direct_callers": len(callers),
            "direct_importers": len(importers),
        }

    def clear_cache(self):
        """Clear relationship cache."""
        self._cache.clear()
        logger.info("Graph enrichment cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics."""
        return {
            "enabled": self.config.enabled,
            "cache_size": len(self._cache),
            "cache_max": 1000,
            "serena_available": self.serena is not None,
        }
