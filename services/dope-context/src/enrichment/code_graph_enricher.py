"""
F-NEW-5: Code Graph + Semantic Search Enrichment

Enriches dope-context search results with Serena code graph relationship metadata.
Adds context about how code is used: callers, callees, imports, imported_by.

ADHD Benefits:
- See impact before making changes (reduces anxiety)
- Better understanding of code relationships
- Gentle warnings for high-impact code (>20 references)
- Progressive disclosure (expand for details)

Performance:
- Enrichment target: <200ms for top 5 results
- Parallel API calls via asyncio.gather()
- Redis caching (TTL: 30min)
- Graceful degradation if Serena unavailable
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)


class CodeGraphEnricher:
    """
    Enriches semantic search results with code graph relationship metadata.

    Integrates with Serena v2 to add:
    - Caller count (how many functions call this)
    - Callee count (how many functions this calls)
    - Import count (how many files import this)
    - Imported by count (how many files this imports)
    """

    def __init__(self, redis_client=None, cache_ttl: int = 1800):
        """
        Initialize code graph enricher.

        Args:
            redis_client: Optional Redis client for caching
            cache_ttl: Cache TTL in seconds (default: 30 min)
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self._serena_available = None  # Lazy check

    async def _check_serena_availability(self) -> bool:
        """
        Check if Serena MCP is available.

        Returns:
            True if Serena is accessible, False otherwise
        """
        if self._serena_available is not None:
            return self._serena_available

        try:
            # Try to import Serena client or make test call
            # For now, assume available if we can import
            import sys
            serena_path = Path(__file__).parent.parent.parent.parent / "serena" / "v2"
            if str(serena_path) not in sys.path:
                sys.path.insert(0, str(serena_path))

            # Test import
            from mcp_server import SerenaV2Server

            self._serena_available = True
            logger.info("Serena v2 available for code graph enrichment")

        except Exception as e:
            self._serena_available = False
            logger.warning(f"Serena v2 unavailable: {e}")

        return self._serena_available

    async def _get_cached_relationships(self, cache_key: str) -> Optional[Dict]:
        """
        Get cached relationship data from Redis.

        Args:
            cache_key: Redis cache key

        Returns:
            Cached relationship dict or None if not found
        """
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")

        return None

    async def _cache_relationships(self, cache_key: str, data: Dict):
        """
        Cache relationship data in Redis.

        Args:
            cache_key: Redis cache key
            data: Relationship data to cache
        """
        if not self.redis_client:
            return

        try:
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.debug(f"Cache write failed: {e}")

    async def _get_references_count(
        self,
        file_path: str,
        symbol: Optional[str],
        start_line: int
    ) -> int:
        """
        Get reference count from Serena MCP.

        Args:
            file_path: File path
            symbol: Function/class name
            start_line: Line number where symbol is defined

        Returns:
            Number of references found
        """
        try:
            # Cache key
            cache_key = f"serena:refs:{file_path}:{start_line}"

            # Check cache
            cached = await self._get_cached_relationships(cache_key)
            if cached:
                return cached.get('count', 0)

            # Call Serena MCP find_references tool
            # Note: In production, this would be an MCP client call
            # For now, we'll use a placeholder that can be wired later

            # TODO: Wire to actual Serena MCP client
            # serena_result = await serena_mcp.call_tool(
            #     "find_references",
            #     file_path=file_path,
            #     line=start_line,
            #     column=0,
            #     max_results=100  # Count all references
            # )
            # count = serena_result.get('found', 0)

            count = 0  # Placeholder until MCP client wired

            # Cache result
            await self._cache_relationships(cache_key, {'count': count})

            logger.debug(f"References for {file_path}:{symbol} at line {start_line}: {count}")
            return count

        except Exception as e:
            logger.debug(f"Failed to get references for {file_path}:{symbol}: {e}")
            return 0

    async def _get_code_graph_data(
        self,
        file_path: str,
        symbol: Optional[str]
    ) -> Dict[str, int]:
        """
        Get code graph metadata from Serena.

        Args:
            file_path: File path
            symbol: Function/class name

        Returns:
            Dict with callees, imports counts
        """
        try:
            # In production, query Serena code graph
            # For now, return mock data

            # Cache key
            cache_key = f"serena:graph:{file_path}:{symbol}"

            # Check cache
            cached = await self._get_cached_relationships(cache_key)
            if cached:
                return cached

            # Mock response
            graph_data = {
                'callees': 0,
                'imports': 0
            }

            # Cache result
            await self._cache_relationships(cache_key, graph_data)

            return graph_data

        except Exception as e:
            logger.debug(f"Failed to get code graph for {file_path}:{symbol}: {e}")
            return {'callees': 0, 'imports': 0}

    async def _enrich_single_result(self, result: Dict) -> Dict:
        """
        Enrich a single search result with code graph data.

        Args:
            result: Search result dict from dope-context
                   Must include: file_path, function_name, start_line

        Returns:
            Enhanced result with relationship metadata
        """
        start_time = time.time()

        try:
            file_path = result.get('file_path', '')
            symbol = result.get('function_name')
            start_line = result.get('start_line')

            # Skip if no symbol or no line number
            if not symbol or start_line is None:
                result['relationships'] = None
                result['enrichment_skipped'] = 'missing_symbol_or_line'
                return result

            # Parallel fetch: references + code graph
            refs_task = self._get_references_count(file_path, symbol, start_line)
            graph_task = self._get_code_graph_data(file_path, symbol)

            # Wait with timeout (200ms max per result)
            try:
                callers_count, graph_data = await asyncio.wait_for(
                    asyncio.gather(refs_task, graph_task),
                    timeout=0.2  # 200ms ADHD target
                )
            except asyncio.TimeoutError:
                logger.warning(f"Enrichment timeout for {file_path}:{symbol}")
                callers_count = 0
                graph_data = {'callees': 0, 'imports': 0}

            # Build relationship metadata
            relationships = {
                'callers': callers_count,
                'callees': graph_data.get('callees', 0),
                'imports': graph_data.get('imports', 0),
                'impact_score': self._calculate_impact_score(callers_count),
                'impact_level': self._get_impact_level(callers_count),
                'impact_message': self._get_impact_message(callers_count)
            }

            result['relationships'] = relationships
            result['enrichment_status'] = 'success'

            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"Enriched {symbol} in {elapsed_ms:.1f}ms")

            return result

        except Exception as e:
            logger.warning(f"Enrichment failed for result: {e}")
            result['relationships'] = None
            result['enrichment_status'] = f'error: {str(e)}'
            return result

    def _calculate_impact_score(self, callers_count: int) -> float:
        """
        Calculate impact score based on caller count.

        Args:
            callers_count: Number of callers

        Returns:
            Impact score 0.0-1.0 (ADHD cognitive load scale)
        """
        # Logarithmic scaling: 1 caller = 0.1, 10 = 0.3, 100 = 0.5, 1000+ = 1.0
        if callers_count == 0:
            return 0.0

        import math
        score = min(1.0, math.log10(callers_count + 1) / 3.0)
        return round(score, 2)

    def _get_impact_level(self, callers_count: int) -> str:
        """
        Get human-readable impact level.

        Args:
            callers_count: Number of callers

        Returns:
            Impact level: none, low, medium, high, critical
        """
        if callers_count == 0:
            return "none"
        elif callers_count < 5:
            return "low"
        elif callers_count < 20:
            return "medium"
        elif callers_count < 50:
            return "high"
        else:
            return "critical"

    def _get_impact_message(self, callers_count: int) -> str:
        """
        Get gentle ADHD-friendly impact message.

        Args:
            callers_count: Number of callers

        Returns:
            Human-readable impact message
        """
        if callers_count == 0:
            return "No callers - safe to modify"
        elif callers_count < 5:
            return f"Low impact - {callers_count} caller(s)"
        elif callers_count < 20:
            return f"Medium impact - {callers_count} callers"
        elif callers_count < 50:
            return f"High impact - affects {callers_count} functions"
        else:
            return f"CRITICAL IMPACT - {callers_count}+ callers (review carefully!)"

    async def enrich_results(
        self,
        results: List[Dict],
        max_enrich: int = 5,
        timeout_per_result: float = 0.2
    ) -> List[Dict]:
        """
        Enrich search results with code graph relationships.

        Args:
            results: Search results from dope-context
            max_enrich: Maximum results to enrich (default: 5, ADHD limit)
            timeout_per_result: Timeout in seconds per result (default: 200ms)

        Returns:
            Enriched results with relationship metadata

        ADHD Optimization:
        - Only enriches top N results (prevents overwhelm)
        - Parallel processing for speed
        - Graceful degradation if data unavailable
        - Clear impact indicators (low/medium/high/critical)
        """
        if not results:
            return results

        # Check Serena availability
        serena_available = await self._check_serena_availability()
        if not serena_available:
            logger.info("Serena unavailable - returning results without enrichment")
            for result in results:
                result['relationships'] = None
            return results

        # Enrich only top N results
        to_enrich = results[:max_enrich]
        remaining = results[max_enrich:]

        logger.info(f"Enriching top {len(to_enrich)} results with code graph data")

        start_time = time.time()

        # Parallel enrichment
        try:
            enriched = await asyncio.gather(
                *[self._enrich_single_result(result) for result in to_enrich],
                return_exceptions=True
            )

            # Filter out exceptions
            enriched_results = []
            for item in enriched:
                if isinstance(item, Exception):
                    logger.error(f"Enrichment error: {item}")
                else:
                    enriched_results.append(item)

            # Add unenriched results
            for result in remaining:
                result['relationships'] = None
                enriched_results.append(result)

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"Enrichment complete in {elapsed_ms:.1f}ms")

            return enriched_results

        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            # Return original results without enrichment
            for result in results:
                result['relationships'] = None
            return results


# Global singleton
_code_graph_enricher = None


async def get_code_graph_enricher(redis_client=None) -> CodeGraphEnricher:
    """
    Get or create code graph enricher singleton.

    Args:
        redis_client: Optional Redis client for caching

    Returns:
        CodeGraphEnricher instance
    """
    global _code_graph_enricher

    if _code_graph_enricher is None:
        _code_graph_enricher = CodeGraphEnricher(redis_client=redis_client)

    return _code_graph_enricher
