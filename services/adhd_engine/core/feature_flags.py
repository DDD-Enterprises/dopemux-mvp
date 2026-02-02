"""
Feature Flags for ADHD Engine Integration Rollout

Enables gradual migration with per-service and per-user control.
Prevents "big bang" deployments and allows safe rollback.

Usage:
    from feature_flags import ADHDFeatureFlags, FEATURE_ADHD_ENGINE_SERENA

    flags = ADHDFeatureFlags(redis_client)

    if await flags.is_enabled(FEATURE_ADHD_ENGINE_SERENA, "serena", user_id):
        # Use new ADHD Engine integration
        max_results = await adhd_config.get_max_results(user_id)
    else:
        # Use legacy hardcoded values
        max_results = 10

Priority:
    1. User-level override (highest priority - for beta testing)
    2. Service-level flag (per-service rollout)
    3. Global flag (full rollout)
"""

import logging
from typing import Optional, Dict, Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ADHDFeatureFlags:
    """
    Feature flag system for ADHD Engine integration rollout.

    Allows gradual migration with per-service and per-user control.
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize feature flags with Redis client.

        Args:
            redis_client: Redis client (should use ADHD Engine's db=5)
        """
        self.redis = redis_client

    async def is_enabled(
        self,
        feature: str,
        service: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if feature is enabled.

        Priority hierarchy (highest to lowest):
        1. User-level override (if user_id provided)
        2. Service-level flag
        3. Global flag
        4. Default: DISABLED (safe default during migration)

        Args:
            feature: Feature flag name (e.g., FEATURE_ADHD_ENGINE_SERENA)
            service: Service name (e.g., "serena", "conport")
            user_id: Optional user ID for user-specific override

        Returns:
            True if feature enabled, False otherwise

        Example:
            is_enabled("adhd_engine_serena", "serena", "developer1")
            → Checks: user override → service flag → global flag → default (false)
        """
        # Priority 1: Check user override
        if user_id:
            user_key = f"adhd:feature_flags:{feature}:user:{user_id}"
            user_flag = await self.redis.get(user_key)
            if user_flag is not None:
                enabled = user_flag.lower() in ("true", "1", "yes")
                logger.debug(f"🎯 Feature {feature} user override for {user_id}: {enabled}")
                return enabled

        # Priority 2: Check service flag
        service_key = f"adhd:feature_flags:{feature}:service:{service}"
        service_flag = await self.redis.get(service_key)
        if service_flag is not None:
            enabled = service_flag.lower() in ("true", "1", "yes")
            logger.debug(f"🔧 Feature {feature} service flag for {service}: {enabled}")
            return enabled

        # Priority 3: Check global flag
        global_key = f"adhd:feature_flags:{feature}:global"
        global_flag = await self.redis.get(global_key)
        if global_flag is not None:
            enabled = global_flag.lower() in ("true", "1", "yes")
            logger.debug(f"🌐 Feature {feature} global flag: {enabled}")
            return enabled

        # Priority 4: Default DISABLED (safe during migration)
        logger.debug(f"⚪ Feature {feature} not enabled (using default: false)")
        return False

    async def enable_for_service(self, feature: str, service: str) -> None:
        """
        Enable feature for specific service.

        Use for gradual rollout (e.g., enable Serena first, then ConPort).

        Args:
            feature: Feature flag name
            service: Service name to enable for
        """
        key = f"adhd:feature_flags:{feature}:service:{service}"
        await self.redis.set(key, "true")
        logger.info(f"✅ Enabled {feature} for service {service}")

    async def disable_for_service(self, feature: str, service: str) -> None:
        """Disable feature for specific service."""
        key = f"adhd:feature_flags:{feature}:service:{service}"
        await self.redis.delete(key)
        logger.info(f"❌ Disabled {feature} for service {service}")

    async def enable_for_user(self, feature: str, user_id: str) -> None:
        """
        Enable feature for specific user (beta testing).

        Use for testing with one user before broader rollout.

        Args:
            feature: Feature flag name
            user_id: User ID to enable for
        """
        key = f"adhd:feature_flags:{feature}:user:{user_id}"
        await self.redis.set(key, "true")
        logger.info(f"✅ Enabled {feature} for user {user_id}")

    async def disable_for_user(self, feature: str, user_id: str) -> None:
        """Disable feature for specific user."""
        key = f"adhd:feature_flags:{feature}:user:{user_id}"
        await self.redis.delete(key)
        logger.info(f"❌ Disabled {feature} for user {user_id}")

    async def enable_globally(self, feature: str) -> None:
        """
        Enable feature globally (full rollout).

        Use after successful beta testing and service-level rollouts.

        Args:
            feature: Feature flag name
        """
        key = f"adhd:feature_flags:{feature}:global"
        await self.redis.set(key, "true")
        logger.info(f"🌐 Enabled {feature} globally")

    async def disable_globally(self, feature: str) -> None:
        """
        Disable feature globally (emergency rollback).

        All services immediately revert to legacy behavior.
        """
        key = f"adhd:feature_flags:{feature}:global"
        await self.redis.delete(key)
        logger.info(f"🚨 Disabled {feature} globally (rollback)")

    async def get_flag_status(self, feature: str) -> Dict[str, Any]:
        """
        Get current status of feature flag at all levels.

        Useful for debugging and monitoring rollout progress.

        Returns:
            {
                "global": True/False,
                "services": {"serena": True, "conport": False},
                "users": {"user1": True}
            }
        """
        status = {
            "global": False,
            "services": {},
            "users": {}
        }

        # Check global
        global_key = f"adhd:feature_flags:{feature}:global"
        global_flag = await self.redis.get(global_key)
        status["global"] = bool(global_flag and global_flag.lower() in ("true", "1", "yes"))

        # Get all service flags
        pattern = f"adhd:feature_flags:{feature}:service:*"
        service_keys = await self.redis.keys(pattern)
        for key in service_keys:
            service_name = key.split(":")[-1]
            flag_value = await self.redis.get(key)
            status["services"][service_name] = flag_value.lower() in ("true", "1", "yes")

        # Get all user flags
        pattern = f"adhd:feature_flags:{feature}:user:*"
        user_keys = await self.redis.keys(pattern)
        for key in user_keys:
            user_id = key.split(":")[-1]
            flag_value = await self.redis.get(key)
            status["users"][user_id] = flag_value.lower() in ("true", "1", "yes")

        return status


# ============================================================================
# Feature Flag Constants
# ============================================================================

# ADHD Engine integration feature flags
FEATURE_ADHD_ENGINE_SERENA = "adhd_engine_integration_serena"
FEATURE_ADHD_ENGINE_CONPORT = "adhd_engine_integration_conport"
FEATURE_ADHD_ENGINE_DOPE_CONTEXT = "adhd_engine_integration_dope_context"
FEATURE_ADHD_ENGINE_DOPECON_BRIDGE = "adhd_engine_dopecon_bridge"

# Future feature flags (placeholders)
FEATURE_DOPECON_BRIDGE_EVENTS = "dopecon_bridge_events"
FEATURE_CONPORT_SEARCH_DELEGATION = "conport_search_delegation"
