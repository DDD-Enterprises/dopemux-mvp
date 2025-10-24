"""
Complexity Coordinator - Unified Complexity Intelligence

Combines complexity signals from:
1. dope-context: AST-based structural complexity (Tree-sitter)
2. Serena v2: LSP-based usage complexity (references, callers)
3. ADHD Engine: User-specific adjustment multipliers

Produces single unified complexity score shared across all systems.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class ComplexityResult:
    """Unified complexity result with component breakdown."""

    unified_score: float  # 0.0-1.0 final score
    ast_complexity: float  # Structural complexity
    usage_complexity: float  # Reference/caller patterns
    user_multiplier: float  # ADHD adjustment
    metadata: Dict[str, Any]  # Additional context


class ComplexityCoordinator:
    """
    Coordinates complexity calculation across multiple systems.

    Algorithm:
        unified_score = (
            ast_complexity * 0.50 +      # Structural (most objective)
            usage_complexity * 0.30      # Impact (widely used code)
        ) * user_multiplier * 0.20       # Personalization (ADHD patterns)
    """

    def __init__(
        self,
        dope_context_client=None,
        serena_client=None,
        adhd_engine_client=None,
    ):
        """
        Initialize complexity coordinator.

        Args:
            dope_context_client: Optional dope-context MCP client
            serena_client: Optional Serena v2 MCP client
            adhd_engine_client: Optional ADHD Engine client
        """
        self.dope = dope_context_client
        self.serena = serena_client
        self.adhd = adhd_engine_client

        # LRU cache (max 1000 entries)
        self._cache = {}
        self._cache_max_size = 1000

    @lru_cache(maxsize=1000)
    def _get_cached_complexity(
        self, file_path: str, symbol: str, user_id: str
    ) -> ComplexityResult:
        """Cache wrapper for complexity calculation."""
        cache_key = f"{file_path}:{symbol}:{user_id}"
        return self._cache.get(cache_key)

    async def get_unified_complexity(
        self,
        file_path: str,
        symbol: str,
        user_id: str = "default",
    ) -> ComplexityResult:
        """
        Get unified complexity score combining all sources.

        Args:
            file_path: Absolute or relative file path
            symbol: Function/class/method name
            user_id: User identifier for ADHD personalization

        Returns:
            ComplexityResult with unified score and breakdown
        """
        # Check cache
        cache_key = f"{file_path}:{symbol}:{user_id}"
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]

        # 1. Get AST complexity from dope-context (50% weight)
        ast_score = await self._get_ast_complexity(file_path, symbol)

        # 2. Get LSP usage complexity from Serena (30% weight)
        usage_score = await self._get_usage_complexity(file_path, symbol)

        # 3. Get ADHD adjustment multiplier (20% weight)
        user_multiplier = await self._get_adhd_adjustment(user_id, ast_score)

        # 4. Calculate unified score
        unified = (ast_score * 0.50 + usage_score * 0.30) * (
            1.0 + (user_multiplier - 1.0) * 0.20
        )

        # Ensure 0.0-1.0 range
        unified = max(0.0, min(1.0, unified))

        # Build result
        result = ComplexityResult(
            unified_score=round(unified, 3),
            ast_complexity=round(ast_score, 3),
            usage_complexity=round(usage_score, 3),
            user_multiplier=round(user_multiplier, 3),
            metadata={
                "file_path": file_path,
                "symbol": symbol,
                "user_id": user_id,
                "sources": {
                    "ast": "dope-context" if self.dope else "fallback",
                    "usage": "serena" if self.serena else "fallback",
                    "adhd": "adhd-engine" if self.adhd else "fallback",
                },
            },
        )

        # Cache result
        if len(self._cache) >= self._cache_max_size:
            # Evict oldest entry (simple FIFO for now)
            self._cache.pop(next(iter(self._cache)))

        self._cache[cache_key] = result

        logger.debug(
            f"Calculated unified complexity for {symbol}: {unified:.3f} "
            f"(AST: {ast_score:.3f}, Usage: {usage_score:.3f}, ADHD: {user_multiplier:.3f})"
        )

        return result

    async def _get_ast_complexity(
        self, file_path: str, symbol: str
    ) -> float:
        """
        Get AST-based structural complexity from dope-context.

        Returns:
            Complexity score 0.0-1.0
        """
        if not self.dope:
            # Fallback: Use moderate complexity
            logger.debug("dope-context unavailable, using fallback AST complexity")
            return 0.5

        try:
            # Query dope-context for chunk complexity
            # TODO: Implement get_chunk_complexity MCP tool in dope-context
            complexity_data = await self.dope.get_chunk_complexity(
                file_path, symbol
            )
            return complexity_data.get("complexity", 0.5)

        except Exception as e:
            logger.warning(
                f"Failed to get AST complexity from dope-context: {e}"
            )
            return 0.5  # Fallback

    async def _get_usage_complexity(
        self, file_path: str, symbol: str
    ) -> float:
        """
        Get usage-based complexity from Serena LSP metadata.

        Factors:
        - Reference count (how widely used)
        - Caller count (how many depend on it)
        - Import frequency

        Returns:
            Complexity score 0.0-1.0
        """
        if not self.serena:
            # Fallback: Use moderate complexity
            logger.debug("Serena unavailable, using fallback usage complexity")
            return 0.5

        try:
            # Query Serena for symbol metadata
            # TODO: Implement get_symbol_metadata in Serena
            metadata = await self.serena.get_symbol_metadata(file_path, symbol)

            ref_count = metadata.get("references_count", 0)
            caller_count = metadata.get("callers_count", 0)

            # Normalize to 0.0-1.0
            # ref_count/100 + caller_count/50, capped at 1.0
            usage_score = min(
                1.0, (ref_count / 100.0 + caller_count / 50.0) / 2.0
            )

            return usage_score

        except Exception as e:
            logger.warning(
                f"Failed to get usage complexity from Serena: {e}"
            )
            return 0.5  # Fallback

    async def _get_adhd_adjustment(
        self, user_id: str, base_complexity: float
    ) -> float:
        """
        Get ADHD-specific complexity adjustment multiplier.

        Based on user's historical patterns with similar complexity.

        Returns:
            Multiplier (typically 0.8-1.5, where >1.0 = harder for this user)
        """
        if not self.adhd:
            # Fallback: No adjustment
            logger.debug("ADHD Engine unavailable, using fallback multiplier")
            return 1.0

        try:
            # Query ADHD Engine for complexity adjustment
            # TODO: Implement get_complexity_adjustment endpoint
            adjustment = await self.adhd.get_complexity_adjustment(
                user_id=user_id, base_complexity=base_complexity
            )

            multiplier = adjustment.get("multiplier", 1.0)

            # Sanity check: Keep within reasonable bounds
            return max(0.5, min(2.0, multiplier))

        except Exception as e:
            logger.warning(
                f"Failed to get ADHD adjustment from ADHD Engine: {e}"
            )
            return 1.0  # Fallback

    def clear_cache(self):
        """Clear complexity cache."""
        self._cache.clear()
        logger.info("Complexity cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._cache_max_size,
            "hit_rate": "not_tracked",  # Could add hit tracking
        }
