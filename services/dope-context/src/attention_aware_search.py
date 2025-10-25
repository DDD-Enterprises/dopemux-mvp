"""
F-NEW-4: Attention-Aware Search Integration

Makes dope-context search results dynamically adaptive to ADHD attention state.
Synergy between dope-context and ADHD Engine for optimal cognitive load management.

Attention State Mapping:
- scattered → 5 results (reduce overwhelm)
- transitioning → 7 results (moderate)
- focused → 10 results (standard)
- deep_focus → 15 results (high capacity)
- hyperfocus → 20 results (peak performance)

ADHD Benefits:
- Prevents overwhelm during scattered states
- Maximizes throughput during peak focus
- Personalized to individual attention patterns
- Real-time adaptation vs static limits
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AttentionAwareSearch:
    """
    Integrates ADHD Engine attention state with dope-context search.

    Dynamically adjusts result limits based on real-time cognitive capacity.
    """

    def __init__(self):
        """Initialize attention-aware search integration."""
        self._adhd_config = None
        self._adhd_feature_flags = None
        self._initialized = False

    async def _ensure_adhd_connection(self):
        """Lazy-load ADHD Engine connection."""
        if self._initialized:
            return

        try:
            import sys
            from pathlib import Path

            # Add ADHD Engine to path
            adhd_path = Path(__file__).parent.parent.parent / "adhd_engine"
            if str(adhd_path) not in sys.path:
                sys.path.insert(0, str(adhd_path))

            from adhd_config_service import get_adhd_config_service
            from feature_flags import ADHDFeatureFlags

            self._adhd_config = await get_adhd_config_service()
            self._adhd_feature_flags = ADHDFeatureFlags(self._adhd_config.redis_client)
            self._initialized = True

            logger.info("✅ Dope-Context connected to ADHD Engine for attention-aware search")

        except Exception as e:
            logger.warning(f"⚠️  ADHD Engine unavailable for attention-aware search: {e}")
            self._initialized = False

    async def get_adaptive_result_limit(
        self,
        user_id: str = "default",
        requested_limit: Optional[int] = None
    ) -> int:
        """
        Get adaptive result limit based on attention state.

        Args:
            user_id: User identifier for ADHD state lookup
            requested_limit: User-requested limit (overrides ADHD if provided)

        Returns:
            Adaptive result limit based on attention state:
            - scattered: 5 results
            - transitioning: 7 results
            - focused: 10 results
            - deep_focus: 15 results
            - hyperfocus: 20 results
            - fallback: requested_limit or 10
        """
        # User override takes precedence
        if requested_limit is not None:
            return requested_limit

        # Try ADHD Engine integration
        await self._ensure_adhd_connection()

        if self._adhd_config and self._adhd_feature_flags:
            try:
                # Check if feature is enabled
                is_enabled = await self._adhd_feature_flags.is_enabled(
                    "attention_aware_search",
                    user_id
                )

                if not is_enabled:
                    logger.debug(f"Attention-aware search disabled for user {user_id}")
                    return 10  # Default

                # Get attention state
                attention_state = await self._adhd_config.get_attention_state(user_id)

                # Map attention state to result limit
                attention_limits = {
                    'scattered': 5,
                    'transitioning': 7,
                    'focused': 10,
                    'deep_focus': 15,
                    'hyperfocus': 20
                }

                limit = attention_limits.get(attention_state, 10)
                logger.info(f"📊 Attention-aware limit: {attention_state} → {limit} results")
                return limit

            except Exception as e:
                logger.debug(f"ADHD Engine query failed: {e}")

        # Fallback to default
        return requested_limit if requested_limit is not None else 10

    async def get_attention_optimized_top_k(
        self,
        user_id: str = "default",
        base_top_k: int = 10
    ) -> int:
        """
        Backward-compatible method for getting adaptive top_k.

        Args:
            user_id: User identifier
            base_top_k: Base result limit

        Returns:
            Attention-optimized top_k value
        """
        return await self.get_adaptive_result_limit(user_id, base_top_k)


# Global singleton
_attention_aware_search = None


async def get_attention_aware_search() -> AttentionAwareSearch:
    """
    Get or create attention-aware search singleton.

    Returns:
        AttentionAwareSearch instance
    """
    global _attention_aware_search

    if _attention_aware_search is None:
        _attention_aware_search = AttentionAwareSearch()

    return _attention_aware_search


async def get_adaptive_search_limit(
    user_id: str = "default",
    requested: Optional[int] = None
) -> int:
    """
    Convenience function for getting adaptive search limit.

    Args:
        user_id: User identifier for ADHD state
        requested: Optional requested limit (overrides ADHD)

    Returns:
        Adaptive search limit based on attention state

    Example:
        >>> limit = await get_adaptive_search_limit(user_id="alice")
        >>> results = await search_code(query, top_k=limit)
    """
    search = await get_attention_aware_search()
    return await search.get_adaptive_result_limit(user_id, requested)
