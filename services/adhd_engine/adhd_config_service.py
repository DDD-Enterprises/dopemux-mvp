"""
ADHD Configuration Service - Shared Library

Provides centralized ADHD accommodations across all Dopemux services.
All services query this instead of hardcoding thresholds.

Backed by ADHD Engine's real-time state tracking via Redis.

Usage:
    from adhd_config_service import get_adhd_config_service

    adhd_config = await get_adhd_config_service()
    max_results = await adhd_config.get_max_results(user_id)
    # Returns: 5 (scattered) or 15 (focused) or 40 (hyperfocused)

Features:
- Dynamic thresholds based on real-time ADHD state
- 5-minute caching to prevent excessive Redis queries
- Graceful degradation with safe defaults
- Singleton pattern for global reuse
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import redis.asyncio as redis
from redis.exceptions import RedisError

from .inmemory_redis import InMemoryRedis

logger = logging.getLogger(__name__)


class ADHDConfigService:
    """
    Centralized ADHD configuration service.

    All services query this instead of hardcoding thresholds.
    Backed by ADHD Engine's real-time state tracking.
    """

    def __init__(self, redis_url: str, workspace_id: str):
        """
        Initialize ADHD Config Service.

        Args:
            redis_url: Redis connection URL (should connect to ADHD Engine's Redis db=5)
            workspace_id: Workspace identifier for scoping
        """
        self.redis_url = redis_url
        self.workspace_id = workspace_id
        self.redis_client: Optional[redis.Redis] = None

        # In-memory cache (5min TTL) to prevent excessive Redis queries
        self._cache: Dict[str, tuple] = {}  # {key: (timestamp, value)}
        self._cache_ttl = 300  # 5 minutes in seconds

    async def initialize(self) -> None:
        """Initialize Redis connection to ADHD Engine."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ ADHDConfigService connected to ADHD Engine")
        except (RedisError, OSError, PermissionError) as exc:
            logger.warning("⚠️ Redis unavailable (%s); falling back to in-memory store", exc)
            self.redis_client = InMemoryRedis()

    # ============================================================================
    # Public API - Dynamic ADHD Accommodations
    # ============================================================================

    async def get_max_results(self, user_id: str) -> int:
        """
        Get maximum results to show based on user's attention state.

        Returns:
            scattered/overwhelmed: 3-5 results (reduce cognitive overload)
            transitioning: 10 results (standard)
            focused: 15-20 results (can handle more)
            hyperfocused: 40-50 results (deep dive mode)

        ADHD Benefit: Adapts result count to attention capacity, preventing
                      information overload during scattered states.
        """
        attention_state = await self._get_attention_state(user_id)

        result_limits = {
            "scattered": 5,
            "transitioning": 10,
            "focused": 15,
            "hyperfocused": 40,
            "overwhelmed": 3
        }

        limit = result_limits.get(attention_state, 10)  # Default: 10

        logger.debug(f"📊 max_results for {user_id}: {limit} (attention: {attention_state})")
        return limit

    async def get_complexity_threshold(self, user_id: str) -> float:
        """
        Get complexity threshold based on user's energy level.

        Returns:
            very_low: 0.3 (only simple tasks, avoid burnout)
            low: 0.5 (easy to moderate tasks)
            medium: 0.7 (standard tasks)
            high: 0.9 (can handle complex tasks)
            hyperfocus: 1.0 (no limits, peak performance)

        ADHD Benefit: Prevents complex tasks during low energy, reducing
                      frustration and protecting against burnout.
        """
        energy_level = await self._get_energy_level(user_id)

        thresholds = {
            "very_low": 0.3,
            "low": 0.5,
            "medium": 0.7,
            "high": 0.9,
            "hyperfocus": 1.0
        }

        threshold = thresholds.get(energy_level, 0.7)  # Default: 0.7

        logger.debug(f"⚡ complexity_threshold for {user_id}: {threshold} (energy: {energy_level})")
        return threshold

    async def get_cognitive_load_threshold(self, user_id: str) -> float:
        """
        Get max cognitive load threshold for user.

        Adjusts based on user's distraction sensitivity from ADHD profile.
        Higher sensitivity = lower threshold (need breaks sooner).

        Returns:
            float: 0.5-1.0 threshold for cognitive load
        """
        profile = await self._get_user_profile(user_id)

        # Default threshold if no profile
        if not profile:
            return 0.8

        # Adjust based on user's distraction sensitivity
        distraction_sensitivity = profile.get("distraction_sensitivity", 0.6)

        # Higher sensitivity = lower threshold (need breaks sooner)
        threshold = max(0.5, 1.0 - (distraction_sensitivity * 0.5))

        logger.debug(f"🧠 cognitive_load_threshold for {user_id}: {threshold:.2f}")
        return threshold

    async def get_context_depth(self, user_id: str) -> int:
        """
        Get max context depth based on working memory capacity.

        Returns:
            scattered/overwhelmed: 1-2 levels (minimal to prevent overload)
            transitioning: 2-3 levels (moderate)
            focused: 3-4 levels (standard navigation)
            hyperfocused: 5-6 levels (deep exploration)

        ADHD Benefit: Respects working memory limitations (ADHD: 3-5 items
                      vs neurotypical: 7±2 items). Prevents rabbit holes
                      during scattered states.
        """
        attention_state = await self._get_attention_state(user_id)

        depth_limits = {
            "scattered": 1,
            "overwhelmed": 1,
            "transitioning": 2,
            "focused": 3,
            "hyperfocused": 5
        }

        depth = depth_limits.get(attention_state, 3)  # Default: 3

        logger.debug(f"📏 context_depth for {user_id}: {depth} (attention: {attention_state})")
        return depth

    async def get_break_suggestion_threshold(self, user_id: str) -> float:
        """
        Get threshold for suggesting breaks based on cognitive load.

        Adjusts based on user's break resistance from ADHD profile.

        Returns:
            float: 0.7-0.95 threshold for break suggestions
        """
        profile = await self._get_user_profile(user_id)

        if not profile:
            return 0.9  # Default

        # Higher break resistance = higher threshold (suggest less frequently)
        break_resistance = profile.get("break_resistance", 0.3)
        threshold = 0.7 + (break_resistance * 0.25)  # 0.7-0.95 range

        return min(threshold, 0.95)

    async def should_suggest_break(self, user_id: str) -> tuple[bool, str]:
        """
        Check if user should take a break.

        Combines multiple signals:
        - Time since last break
        - Current energy level
        - Cognitive load
        - User's optimal task duration

        Returns:
            (should_break: bool, reason: str)

        ADHD Benefit: Proactive break recommendations prevent burnout
                      and maintain sustainable productivity.
        """
        # Check time since last break
        last_break_key = f"adhd:last_break:{user_id}"
        last_break_str = await self.redis_client.get(last_break_key)

        if last_break_str:
            last_break = datetime.fromisoformat(last_break_str)
            minutes_since = (datetime.now() - last_break).total_seconds() / 60

            # Get user's optimal task duration
            profile = await self._get_user_profile(user_id)
            optimal_duration = profile.get("optimal_task_duration", 25) if profile else 25
            max_duration = profile.get("max_task_duration", 90) if profile else 90

            # Check if maximum duration reached (mandatory break)
            if minutes_since >= max_duration:
                return (True, f"🛡️ Maximum duration reached ({minutes_since:.0f}min)")

            # Check if 2x optimal duration (strong recommendation)
            if minutes_since >= optimal_duration * 2:
                return (True, f"⏰ Extended work period ({minutes_since:.0f}min without break)")

        # Check current energy level
        energy = await self._get_energy_level(user_id)
        if energy == "very_low":
            return (True, "💙 Low energy detected - break recommended for recovery")

        # No break needed
        return (False, "")

    async def get_focus_mode_limit(self, user_id: str) -> int:
        """
        Get result limit for focus mode (reduced results).

        Focus mode shows fewer items for concentrated work.
        """
        attention_state = await self._get_attention_state(user_id)

        # Focus mode: half the normal limits
        normal_limit = await self.get_max_results(user_id)
        focus_limit = max(3, normal_limit // 2)

        return focus_limit

    # ============================================================================
    # Internal Helper Methods - Query ADHD Engine State
    # ============================================================================

    async def _get_attention_state(self, user_id: str) -> str:
        """
        Get current attention state from ADHD Engine.

        Queries Redis where ADHD Engine's _attention_state_monitor()
        writes state every 2 minutes (engine.py:614-664).

        Returns: scattered, transitioning, focused, hyperfocused, overwhelmed
        """
        cache_key = f"attention:{user_id}"

        # Check cache first
        cached_value = self._get_from_cache(cache_key)
        if cached_value is not None:
            return cached_value

        # Query ADHD Engine Redis
        redis_key = f"adhd:attention_state:{user_id}"
        state = await self.redis_client.get(redis_key)

        if not state:
            state = "transitioning"  # Safe default if ADHD Engine hasn't assessed yet

        # Cache result
        self._put_in_cache(cache_key, state)

        return state

    async def _get_energy_level(self, user_id: str) -> str:
        """
        Get current energy level from ADHD Engine.

        Queries Redis where ADHD Engine's _energy_level_monitor()
        writes level every 5 minutes (engine.py:538-612).

        Returns: very_low, low, medium, high, hyperfocus
        """
        cache_key = f"energy:{user_id}"

        # Check cache first
        cached_value = self._get_from_cache(cache_key)
        if cached_value is not None:
            return cached_value

        # Query ADHD Engine Redis
        redis_key = f"adhd:energy_level:{user_id}"
        level = await self.redis_client.get(redis_key)

        if not level:
            level = "medium"  # Safe default

        # Cache result
        self._put_in_cache(cache_key, level)

        return level

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user ADHD profile from ADHD Engine.

        Profile includes personalized characteristics:
        - hyperfocus_tendency (0.0-1.0)
        - distraction_sensitivity (0.0-1.0)
        - context_switch_penalty (0.0-1.0)
        - break_resistance (0.0-1.0)
        - optimal_task_duration (minutes)
        - max_task_duration (minutes)

        Returns: Profile dict or None if not found
        """
        cache_key = f"profile:{user_id}"

        # Check cache first
        cached_value = self._get_from_cache(cache_key)
        if cached_value is not None:
            return cached_value

        # Query ADHD Engine Redis
        redis_key = f"adhd:profile:{user_id}"
        profile_json = await self.redis_client.get(redis_key)

        if not profile_json:
            logger.debug(f"No ADHD profile found for {user_id}, using defaults")
            return None

        profile = json.loads(profile_json)

        # Cache result
        self._put_in_cache(cache_key, profile)

        return profile

    # ============================================================================
    # Cache Management - 5-Minute TTL
    # ============================================================================

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Returns None if cache miss or expired.
        """
        if key not in self._cache:
            return None

        cached_time, cached_value = self._cache[key]

        # Check if expired
        if (datetime.now() - cached_time).total_seconds() >= self._cache_ttl:
            # Expired - remove from cache
            del self._cache[key]
            return None

        return cached_value

    def _put_in_cache(self, key: str, value: Any) -> None:
        """Put value in cache with current timestamp."""
        self._cache[key] = (datetime.now(), value)

    async def clear_cache(self, user_id: Optional[str] = None) -> None:
        """
        Clear cache for specific user or all users.

        Use when ADHD state changes need immediate reflection.
        """
        if user_id:
            # Clear specific user's cached values
            keys_to_remove = [k for k in self._cache.keys() if user_id in k]
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"🗑️ Cleared cache for {user_id}")
        else:
            # Clear all cache
            self._cache.clear()
            logger.debug("🗑️ Cleared all cache")

    # ============================================================================
    # Utility Methods
    # ============================================================================

    async def get_current_state_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete current ADHD state summary for user.

        Useful for debugging and displaying current accommodations.

        Returns:
            {
                "energy_level": "medium",
                "attention_state": "focused",
                "max_results": 15,
                "complexity_threshold": 0.7,
                "context_depth": 3,
                "should_break": False,
                "profile": {...}
            }
        """
        energy = await self._get_energy_level(user_id)
        attention = await self._get_attention_state(user_id)
        profile = await self._get_user_profile(user_id)
        should_break, break_reason = await self.should_suggest_break(user_id)

        return {
            "user_id": user_id,
            "energy_level": energy,
            "attention_state": attention,
            "max_results": await self.get_max_results(user_id),
            "complexity_threshold": await self.get_complexity_threshold(user_id),
            "context_depth": await self.get_context_depth(user_id),
            "cognitive_load_threshold": await self.get_cognitive_load_threshold(user_id),
            "should_break": should_break,
            "break_reason": break_reason,
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for ADHDConfigService.

        Verifies connection to ADHD Engine's Redis.
        """
        try:
            if not self.redis_client:
                return {"status": "not_initialized", "healthy": False}

            # Ping Redis
            await self.redis_client.ping()

            # Check cache stats
            cache_size = len(self._cache)

            return {
                "status": "healthy",
                "healthy": True,
                "redis_connected": True,
                "cache_size": cache_size,
                "cache_ttl": self._cache_ttl,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }


# ============================================================================
# Global Singleton Instance
# ============================================================================

_adhd_config_service: Optional[ADHDConfigService] = None


async def get_adhd_config_service(
    redis_url: str = "redis://localhost:6379/5",
    workspace_id: str = "/Users/hue/code/dopemux-mvp"
) -> ADHDConfigService:
    """
    Get or create global ADHDConfigService singleton instance.

    Args:
        redis_url: Redis URL (default: localhost:6379/5 - ADHD Engine's db)
        workspace_id: Workspace path

    Returns:
        Initialized ADHDConfigService instance

    Usage:
        adhd_config = await get_adhd_config_service()
        max_results = await adhd_config.get_max_results("user1")
    """
    global _adhd_config_service

    if _adhd_config_service is None:
        _adhd_config_service = ADHDConfigService(redis_url, workspace_id)
        await _adhd_config_service.initialize()
        logger.info("✅ Global ADHDConfigService initialized")

    return _adhd_config_service


async def reset_adhd_config_service() -> None:
    """
    Reset global singleton (useful for testing).

    Forces re-initialization on next get_adhd_config_service() call.
    """
    global _adhd_config_service

    if _adhd_config_service and _adhd_config_service.redis_client:
        await _adhd_config_service.redis_client.close()

    _adhd_config_service = None
    logger.info("🔄 ADHDConfigService reset")
