# Implementation Plan: ADHD Engine Integration

**Task ID**: IP-001
**Priority**: 🔴 CRITICAL
**Duration**: 7 days (14 focus blocks @ 25min each)
**Complexity**: 0.65 (HIGH)
**Dependencies**: None (can start immediately)
**Risk Level**: MEDIUM (feature flags mitigate risk)

---

## Executive Summary

**Problem**: ADHD Engine is fully implemented but unused. Services hardcode 23+ ADHD thresholds, defeating personalization.

**Solution**: Create `ADHDConfigService` shared library that all services query for dynamic, user-specific ADHD accommodations.

**Impact**:
- ✅ Enables personalized ADHD support (currently broken)
- ✅ Centralizes 23+ scattered thresholds into single source of truth
- ✅ Allows runtime ADHD profile adjustments per user
- ✅ Unlocks full power of existing ADHD Engine

**Success Criteria**:
- [ ] All services query ADHD Engine for thresholds (not hardcoded)
- [ ] User ADHD profiles control behavior across all services
- [ ] Feature flags allow gradual rollout
- [ ] Zero regression in existing functionality

---

## Discovered Hardcoded Thresholds

### Serena v2 (services/serena/v2/adhd_features.py)

**ADHDCodeNavigator class** (lines 92-102):
```python
# HARDCODED - Should query ADHD Engine
self.max_initial_results = 10              # Line 93
self.complexity_threshold = 0.7            # Line 94
self.focus_mode_limit = 5                  # Line 95
self.max_context_depth = 3                 # Line 102
```

**CognitiveLoadManager class** (lines 457-462):
```python
# HARDCODED - Should query ADHD Engine
self.max_load_threshold = 0.8              # Line 460
self.break_suggestion_threshold = 0.9      # Line 461
```

### ConPort (services/conport/src/context_portal_mcp/)

**AttentionStateMonitor** (conport_kg/adhd_query_adapter.py):
```python
# DUPLICATE attention detector - ADHD Engine already does this!
class AttentionStateMonitor:
    def get_current_state(self, activity: UserActivity) -> str:
        # Detects: focused, scattered, transitioning
        # Should USE ADHD Engine's current_attention_states instead
```

### Dope-Context (services/dope-context/)

**Progressive Disclosure Limits** (src/mcp/server.py):
```python
# HARDCODED - Should query ADHD Engine
DEFAULT_TOP_K = 10        # Should vary by attention state
MAX_RESULTS = 50          # Should vary by cognitive capacity
```

### Integration Bridge (services/integration-bridge/)

**No ADHD Engine queries at all** - needs implementation

---

## Day-by-Day Implementation Plan

### Day 1: Create ADHDConfigService Foundation (2 focus blocks, 50min)

**Location**: `services/adhd_engine/adhd_config_service.py` (NEW FILE)

**Tasks**:
1. Create `ADHDConfigService` class with Redis client
2. Implement methods to query ADHD Engine state
3. Add caching layer (5-minute TTL)
4. Write unit tests

**Code Template**:
```python
"""
ADHD Configuration Service - Shared Library
Provides centralized ADHD accommodations across all services.
"""
import redis.asyncio as redis
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ADHDConfigService:
    """
    Centralized ADHD configuration service.

    All services query this instead of hardcoding thresholds.
    Backed by ADHD Engine's real-time state tracking.
    """

    def __init__(self, redis_url: str, workspace_id: str):
        self.redis_url = redis_url
        self.workspace_id = workspace_id
        self.redis_client: Optional[redis.Redis] = None
        self._cache: Dict[str, tuple] = {}  # (timestamp, value)
        self._cache_ttl = 300  # 5 minutes

    async def initialize(self) -> None:
        """Initialize Redis connection to ADHD Engine."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        await self.redis_client.ping()
        logger.info("✅ ADHDConfigService connected to ADHD Engine")

    async def get_max_results(self, user_id: str) -> int:
        """
        Get maximum results to show based on user's attention state.

        Returns:
            scattered: 3-5 results
            transitioning: 10 results
            focused: 15-20 results
            hyperfocused: 40-50 results
        """
        attention_state = await self._get_attention_state(user_id)

        result_limits = {
            "scattered": 5,
            "transitioning": 10,
            "focused": 15,
            "hyperfocused": 40,
            "overwhelmed": 3
        }

        return result_limits.get(attention_state, 10)  # Default: 10

    async def get_complexity_threshold(self, user_id: str) -> float:
        """
        Get complexity threshold based on user's energy level.

        Returns:
            very_low: 0.3 (only simple tasks)
            low: 0.5
            medium: 0.7
            high: 0.9
            hyperfocus: 1.0 (no limits)
        """
        energy_level = await self._get_energy_level(user_id)

        thresholds = {
            "very_low": 0.3,
            "low": 0.5,
            "medium": 0.7,
            "high": 0.9,
            "hyperfocus": 1.0
        }

        return thresholds.get(energy_level, 0.7)  # Default: 0.7

    async def get_cognitive_load_threshold(self, user_id: str) -> float:
        """Get max cognitive load threshold for user."""
        profile = await self._get_user_profile(user_id)

        # Default thresholds if no profile
        if not profile:
            return 0.8

        # Adjust based on user's distraction sensitivity
        distraction_sensitivity = profile.get("distraction_sensitivity", 0.6)

        # Higher sensitivity = lower threshold (need breaks sooner)
        return max(0.5, 1.0 - (distraction_sensitivity * 0.5))

    async def get_context_depth(self, user_id: str) -> int:
        """
        Get max context depth based on working memory capacity.

        Returns:
            scattered/overwhelmed: 1-2 levels
            transitioning: 2-3 levels
            focused: 3-4 levels
            hyperfocused: 5-6 levels
        """
        attention_state = await self._get_attention_state(user_id)

        depth_limits = {
            "scattered": 1,
            "overwhelmed": 1,
            "transitioning": 2,
            "focused": 3,
            "hyperfocused": 5
        }

        return depth_limits.get(attention_state, 3)  # Default: 3

    async def should_suggest_break(self, user_id: str) -> tuple[bool, str]:
        """
        Check if user should take a break.

        Returns: (should_break: bool, reason: str)
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

            if minutes_since >= optimal_duration * 2:
                return (True, f"Working {minutes_since:.0f}min without break")

        # Check cognitive load
        energy = await self._get_energy_level(user_id)
        if energy == "very_low":
            return (True, "Low energy detected")

        return (False, "")

    # Internal helper methods

    async def _get_attention_state(self, user_id: str) -> str:
        """Get current attention state from ADHD Engine."""
        cache_key = f"attention:{user_id}"

        # Check cache
        if cache_key in self._cache:
            cached_time, cached_value = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._cache_ttl:
                return cached_value

        # Query ADHD Engine Redis
        redis_key = f"adhd:attention_state:{user_id}"
        state = await self.redis_client.get(redis_key)

        if not state:
            state = "focused"  # Safe default

        # Cache result
        self._cache[cache_key] = (datetime.now(), state)
        return state

    async def _get_energy_level(self, user_id: str) -> str:
        """Get current energy level from ADHD Engine."""
        cache_key = f"energy:{user_id}"

        # Check cache
        if cache_key in self._cache:
            cached_time, cached_value = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._cache_ttl:
                return cached_value

        # Query ADHD Engine Redis
        redis_key = f"adhd:energy_level:{user_id}"
        level = await self.redis_client.get(redis_key)

        if not level:
            level = "medium"  # Safe default

        # Cache result
        self._cache[cache_key] = (datetime.now(), level)
        return level

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user ADHD profile from ADHD Engine."""
        cache_key = f"profile:{user_id}"

        # Check cache
        if cache_key in self._cache:
            cached_time, cached_value = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._cache_ttl:
                return cached_value

        # Query ADHD Engine Redis
        redis_key = f"adhd:profile:{user_id}"
        profile_json = await self.redis_client.get(redis_key)

        if not profile_json:
            return None

        import json
        profile = json.loads(profile_json)

        # Cache result
        self._cache[cache_key] = (datetime.now(), profile)
        return profile


# Global singleton instance
_adhd_config_service: Optional[ADHDConfigService] = None

async def get_adhd_config_service(
    redis_url: str = "redis://localhost:6379/5",
    workspace_id: str = "/Users/hue/code/dopemux-mvp"
) -> ADHDConfigService:
    """Get or create global ADHDConfigService instance."""
    global _adhd_config_service

    if _adhd_config_service is None:
        _adhd_config_service = ADHDConfigService(redis_url, workspace_id)
        await _adhd_config_service.initialize()

    return _adhd_config_service
```

**Tests** (`tests/test_adhd_config_service.py`):
```python
import pytest
from adhd_config_service import ADHDConfigService

@pytest.mark.asyncio
async def test_get_max_results_scattered():
    """Scattered attention should limit results to 5."""
    service = ADHDConfigService("redis://localhost:6379/5", "/test")
    await service.initialize()

    # Mock attention state
    await service.redis_client.set("adhd:attention_state:user1", "scattered")

    max_results = await service.get_max_results("user1")
    assert max_results == 5

@pytest.mark.asyncio
async def test_get_complexity_threshold_low_energy():
    """Low energy should lower complexity threshold."""
    service = ADHDConfigService("redis://localhost:6379/5", "/test")
    await service.initialize()

    # Mock energy level
    await service.redis_client.set("adhd:energy_level:user1", "low")

    threshold = await service.get_complexity_threshold("user1")
    assert threshold == 0.5
```

**Deliverables**:
- [ ] `adhd_config_service.py` created and tested
- [ ] Unit tests passing
- [ ] Documentation added

---

### Day 2: Add Feature Flags System (2 focus blocks, 50min)

**Location**: `services/adhd_engine/feature_flags.py` (NEW FILE)

**Tasks**:
1. Create feature flag system for gradual rollout
2. Add per-service enable/disable flags
3. Add user-level override flags
4. Test flag evaluation logic

**Code Template**:
```python
"""
Feature Flags for ADHD Engine Integration Rollout
"""
import redis.asyncio as redis
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ADHDFeatureFlags:
    """
    Feature flag system for ADHD Engine integration rollout.

    Allows gradual migration with per-service and per-user control.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_enabled(
        self,
        feature: str,
        service: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if feature is enabled.

        Priority:
        1. User-level override (if user_id provided)
        2. Service-level flag
        3. Global flag
        """
        # Check user override
        if user_id:
            user_key = f"adhd:feature_flags:{feature}:user:{user_id}"
            user_flag = await self.redis.get(user_key)
            if user_flag is not None:
                return user_flag.lower() in ("true", "1", "yes")

        # Check service flag
        service_key = f"adhd:feature_flags:{feature}:service:{service}"
        service_flag = await self.redis.get(service_key)
        if service_flag is not None:
            return service_flag.lower() in ("true", "1", "yes")

        # Check global flag
        global_key = f"adhd:feature_flags:{feature}:global"
        global_flag = await self.redis.get(global_key)
        if global_flag is not None:
            return global_flag.lower() in ("true", "1", "yes")

        # Default: DISABLED (safe default during migration)
        return False

    async def enable_for_service(self, feature: str, service: str) -> None:
        """Enable feature for specific service."""
        key = f"adhd:feature_flags:{feature}:service:{service}"
        await self.redis.set(key, "true")
        logger.info(f"✅ Enabled {feature} for service {service}")

    async def enable_for_user(self, feature: str, user_id: str) -> None:
        """Enable feature for specific user (beta testing)."""
        key = f"adhd:feature_flags:{feature}:user:{user_id}"
        await self.redis.set(key, "true")
        logger.info(f"✅ Enabled {feature} for user {user_id}")

    async def enable_globally(self, feature: str) -> None:
        """Enable feature globally (full rollout)."""
        key = f"adhd:feature_flags:{feature}:global"
        await self.redis.set(key, "true")
        logger.info(f"✅ Enabled {feature} globally")


# Feature flag keys
FEATURE_ADHD_ENGINE_SERENA = "adhd_engine_integration_serena"
FEATURE_ADHD_ENGINE_CONPORT = "adhd_engine_integration_conport"
FEATURE_ADHD_ENGINE_DOPE_CONTEXT = "adhd_engine_integration_dope_context"
FEATURE_ADHD_ENGINE_INTEGRATION_BRIDGE = "adhd_engine_integration_bridge"
```

**Migration Script** (`scripts/enable_adhd_integration.sh`):
```bash
#!/bin/bash
# Gradual rollout script for ADHD Engine integration

REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_DB=${REDIS_DB:-5}

echo "🚀 ADHD Engine Integration Rollout"
echo ""

# Phase 1: Enable for one user (beta test)
echo "Phase 1: Beta testing with user: developer1"
redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB SET "adhd:feature_flags:adhd_engine_integration_serena:user:developer1" "true"

# Phase 2: Enable for Serena service (after 2 days testing)
echo "Phase 2: Enable for Serena service"
read -p "Continue to Phase 2? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB SET "adhd:feature_flags:adhd_engine_integration_serena:global" "true"
fi

# Phase 3: Enable for ConPort service
echo "Phase 3: Enable for ConPort service"
read -p "Continue to Phase 3? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB SET "adhd:feature_flags:adhd_engine_integration_conport:global" "true"
fi

# Phase 4: Enable for all services (full rollout)
echo "Phase 4: Full rollout - Enable for all services"
read -p "Continue to Phase 4? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB SET "adhd:feature_flags:adhd_engine_integration_dope_context:global" "true"
    redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB SET "adhd:feature_flags:adhd_engine_integration_bridge:global" "true"
    echo "✅ Full rollout complete!"
fi
```

**Deliverables**:
- [ ] Feature flags system implemented
- [ ] Migration script created
- [ ] Rollout plan documented

---

### Day 3-4: Migrate Serena v2 (4 focus blocks, 100min)

**Location**: `services/serena/v2/adhd_features.py`

**Tasks**:
1. Inject ADHDConfigService into ADHDCodeNavigator
2. Replace hardcoded thresholds with dynamic queries
3. Add feature flag checks
4. Test migration with flags ON and OFF

**Before** (Current Code):
```python
# services/serena/v2/adhd_features.py, lines 92-102
class ADHDCodeNavigator:
    def __init__(self):
        self.max_initial_results = 10              # HARDCODED
        self.complexity_threshold = 0.7            # HARDCODED
        self.focus_mode_limit = 5                  # HARDCODED
        self.max_context_depth = 3                 # HARDCODED
```

**After** (Migrated Code):
```python
# services/serena/v2/adhd_features.py
from adhd_config_service import get_adhd_config_service
from feature_flags import ADHDFeatureFlags, FEATURE_ADHD_ENGINE_SERENA

class ADHDCodeNavigator:
    def __init__(self, redis_client, user_id: str = "default"):
        self.redis_client = redis_client
        self.user_id = user_id

        # Legacy hardcoded values (fallback)
        self._default_max_results = 10
        self._default_complexity_threshold = 0.7
        self._default_focus_mode_limit = 5
        self._default_max_context_depth = 3

        # ADHD Engine integration
        self.adhd_config = None
        self.feature_flags = ADHDFeatureFlags(redis_client)

    async def initialize(self, workspace_path: Path) -> None:
        """Initialize with ADHD Engine connection."""
        self.workspace_path = workspace_path

        # Connect to ADHD Engine
        try:
            self.adhd_config = await get_adhd_config_service()
            logger.info("✅ ADHD Code Navigator connected to ADHD Engine")
        except Exception as e:
            logger.warning(f"⚠️ ADHD Engine unavailable, using defaults: {e}")

        logger.info("🧠 ADHD Code Navigator initialized")

    async def get_max_results(self) -> int:
        """Get max results dynamically from ADHD Engine."""
        # Check feature flag
        if await self.feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_SERENA,
            "serena",
            self.user_id
        ):
            if self.adhd_config:
                try:
                    return await self.adhd_config.get_max_results(self.user_id)
                except Exception as e:
                    logger.error(f"ADHD Engine query failed: {e}")

        # Fallback to hardcoded default
        return self._default_max_results

    async def get_complexity_threshold(self) -> float:
        """Get complexity threshold dynamically from ADHD Engine."""
        if await self.feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_SERENA,
            "serena",
            self.user_id
        ):
            if self.adhd_config:
                try:
                    return await self.adhd_config.get_complexity_threshold(self.user_id)
                except Exception as e:
                    logger.error(f"ADHD Engine query failed: {e}")

        return self._default_complexity_threshold

    async def get_context_depth(self) -> int:
        """Get context depth dynamically from ADHD Engine."""
        if await self.feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_SERENA,
            "serena",
            self.user_id
        ):
            if self.adhd_config:
                try:
                    return await self.adhd_config.get_context_depth(self.user_id)
                except Exception as e:
                    logger.error(f"ADHD Engine query failed: {e}")

        return self._default_max_context_depth

    async def apply_progressive_disclosure(
        self,
        results: List[Dict[str, Any]],
        max_initial_items: int = None
    ) -> List[Dict[str, Any]]:
        """Apply progressive disclosure with dynamic limits."""
        # Get dynamic max from ADHD Engine
        if max_initial_items is None:
            max_initial_items = await self.get_max_results()

        # Rest of existing logic unchanged...
```

**CognitiveLoadManager Migration**:
```python
# services/serena/v2/adhd_features.py, lines 454+
class CognitiveLoadManager:
    def __init__(self, redis_client, user_id: str = "default"):
        self.redis_client = redis_client
        self.user_id = user_id
        self.current_load = 0.0
        self.load_history = []

        # Legacy defaults (fallback)
        self._default_max_load_threshold = 0.8
        self._default_break_threshold = 0.9

        # ADHD Engine integration
        self.adhd_config = None
        self.feature_flags = ADHDFeatureFlags(redis_client)

    async def initialize(self) -> None:
        """Connect to ADHD Engine."""
        try:
            self.adhd_config = await get_adhd_config_service()
        except Exception as e:
            logger.warning(f"ADHD Engine unavailable: {e}")

    async def get_max_load_threshold(self) -> float:
        """Get max load threshold dynamically."""
        if await self.feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_SERENA,
            "serena",
            self.user_id
        ):
            if self.adhd_config:
                try:
                    return await self.adhd_config.get_cognitive_load_threshold(self.user_id)
                except Exception as e:
                    logger.error(f"ADHD Engine query failed: {e}")

        return self._default_max_load_threshold

    async def assess_navigation_load(
        self,
        action: str,
        result_complexity: float,
        result_count: int,
        file_path: str = None
    ) -> Dict[str, Any]:
        """Assess cognitive load with dynamic thresholds."""
        # Calculate load (existing logic)
        # ...

        # Get dynamic thresholds
        max_threshold = await self.get_max_load_threshold()

        # Check if break recommended
        should_break, reason = await self.adhd_config.should_suggest_break(self.user_id) if self.adhd_config else (False, "")

        recommendations = []
        if should_break:
            recommendations.append(f"☕ {reason} - break recommended")
        elif self.current_load > max_threshold:
            recommendations.append("🎯 Focus mode recommended")

        # Rest of existing logic...
```

**Testing Strategy**:
```bash
# Test with feature flag OFF (should use hardcoded defaults)
redis-cli -n 5 DEL "adhd:feature_flags:adhd_engine_integration_serena:global"
pytest tests/serena/test_adhd_features.py -v

# Test with feature flag ON (should query ADHD Engine)
redis-cli -n 5 SET "adhd:feature_flags:adhd_engine_integration_serena:global" "true"
redis-cli -n 5 SET "adhd:attention_state:developer1" "scattered"
redis-cli -n 5 SET "adhd:energy_level:developer1" "low"
pytest tests/serena/test_adhd_integration.py -v

# Verify dynamic behavior
# Scattered attention should give max_results = 5 (not 10)
# Low energy should give complexity_threshold = 0.5 (not 0.7)
```

**Deliverables**:
- [ ] Serena ADHDCodeNavigator migrated
- [ ] Serena CognitiveLoadManager migrated
- [ ] Feature flag checks added
- [ ] Tests passing with flags ON/OFF
- [ ] Backward compatibility verified

---

### Day 5: Migrate ConPort (2 focus blocks, 50min)

**Location**: `services/conport/src/context_portal_mcp/conport_kg/adhd_query_adapter.py`

**Tasks**:
1. Remove duplicate AttentionStateMonitor class
2. Replace with ADHDConfigService queries
3. Add feature flag checks
4. Test migration

**Before** (Current Code):
```python
# Duplicate attention detector - REMOVE THIS!
class AttentionStateMonitor:
    def get_current_state(self, activity: UserActivity) -> str:
        # Detects: focused, scattered, transitioning
        # This duplicates ADHD Engine's functionality!
```

**After** (Migrated Code):
```python
# services/conport/src/context_portal_mcp/conport_kg/adhd_query_adapter.py
from adhd_config_service import get_adhd_config_service
from feature_flags import ADHDFeatureFlags, FEATURE_ADHD_ENGINE_CONPORT

class ADHDQueryAdapter:
    """
    ADHD-optimized query adapter for ConPort.

    NOW USES ADHD ENGINE instead of duplicating functionality!
    """

    def __init__(self, redis_client, user_id: str = "default"):
        self.redis_client = redis_client
        self.user_id = user_id
        self.adhd_config = None
        self.feature_flags = ADHDFeatureFlags(redis_client)

    async def initialize(self) -> None:
        """Connect to ADHD Engine."""
        try:
            self.adhd_config = await get_adhd_config_service()
            logger.info("✅ ConPort connected to ADHD Engine")
        except Exception as e:
            logger.warning(f"⚠️ ADHD Engine unavailable: {e}")

    async def get_attention_state(self) -> str:
        """
        Get attention state from ADHD Engine (not local detection).
        """
        if await self.feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_CONPORT,
            "conport",
            self.user_id
        ):
            if self.adhd_config:
                try:
                    return await self.adhd_config._get_attention_state(self.user_id)
                except Exception as e:
                    logger.error(f"ADHD Engine query failed: {e}")

        # Fallback
        return "focused"

    async def get_result_limit(self) -> int:
        """Get dynamic result limit from ADHD Engine."""
        if await self.feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_CONPORT,
            "conport",
            self.user_id
        ):
            if self.adhd_config:
                try:
                    return await self.adhd_config.get_max_results(self.user_id)
                except Exception as e:
                    logger.error(f"ADHD Engine query failed: {e}")

        return 10  # Fallback
```

**Deliverables**:
- [ ] AttentionStateMonitor removed (duplicate deleted)
- [ ] ConPort queries ADHD Engine for state
- [ ] Feature flags implemented
- [ ] Tests passing

---

### Day 6: Migrate Dope-Context + Integration Bridge (2 focus blocks, 50min)

**Dope-Context Location**: `services/dope-context/src/mcp/server.py`

**Before**:
```python
DEFAULT_TOP_K = 10        # HARDCODED
MAX_RESULTS = 50          # HARDCODED
```

**After**:
```python
from adhd_config_service import get_adhd_config_service
from feature_flags import ADHDFeatureFlags, FEATURE_ADHD_ENGINE_DOPE_CONTEXT

class DopeContextServer:
    def __init__(self):
        self.adhd_config = None
        self.feature_flags = None
        self.user_id = "default"

    async def initialize(self):
        """Connect to ADHD Engine."""
        try:
            self.adhd_config = await get_adhd_config_service()
            self.feature_flags = ADHDFeatureFlags(self.adhd_config.redis_client)
        except Exception as e:
            logger.warning(f"ADHD Engine unavailable: {e}")

    async def get_top_k(self, user_id: str = None) -> int:
        """Get dynamic top_k from ADHD Engine."""
        uid = user_id or self.user_id

        if await self.feature_flags.is_enabled(
            FEATURE_ADHD_ENGINE_DOPE_CONTEXT,
            "dope-context",
            uid
        ):
            if self.adhd_config:
                try:
                    return await self.adhd_config.get_max_results(uid)
                except Exception:
                    pass

        return 10  # Fallback
```

**Integration Bridge**: Similar pattern, add ADHD Engine queries for task routing decisions.

**Deliverables**:
- [ ] Dope-context migrated
- [ ] Integration Bridge migrated
- [ ] All 4 services using ADHD Engine
- [ ] Feature flags operational

---

### Day 7: Testing, Documentation, Rollout (2 focus blocks, 50min)

**Tasks**:
1. End-to-end integration testing
2. Update documentation
3. Create rollout runbook
4. Monitor initial rollout

**Integration Tests** (`tests/integration/test_adhd_engine_integration.py`):
```python
import pytest
import redis.asyncio as redis

@pytest.mark.asyncio
async def test_adhd_engine_integration_e2e():
    """
    Test complete ADHD Engine integration across all services.
    """
    # Setup: Create test user with specific ADHD profile
    r = redis.from_url("redis://localhost:6379/5", decode_responses=True)

    # Set user to scattered attention + low energy
    await r.set("adhd:attention_state:test_user", "scattered")
    await r.set("adhd:energy_level:test_user", "low")

    # Enable feature flags for all services
    await r.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")
    await r.set("adhd:feature_flags:adhd_engine_integration_conport:global", "true")

    # Test Serena: Should limit results to 5 (scattered) instead of 10
    from serena.adhd_features import ADHDCodeNavigator
    nav = ADHDCodeNavigator(r, "test_user")
    await nav.initialize(Path("/test"))

    max_results = await nav.get_max_results()
    assert max_results == 5, "Serena should use ADHD Engine limits"

    complexity_threshold = await nav.get_complexity_threshold()
    assert complexity_threshold == 0.5, "Low energy should lower threshold"

    # Test ConPort: Should get state from ADHD Engine
    from conport.adhd_query_adapter import ADHDQueryAdapter
    adapter = ADHDQueryAdapter(r, "test_user")
    await adapter.initialize()

    attention = await adapter.get_attention_state()
    assert attention == "scattered", "ConPort should use ADHD Engine state"

    # Verify no duplicate attention detection
    # (AttentionStateMonitor class should be deleted)

    print("✅ All services successfully integrated with ADHD Engine!")
```

**Documentation Updates**:
- [ ] Update `.claude/claude.md` with ADHD Engine integration
- [ ] Update service READMEs
- [ ] Add troubleshooting guide
- [ ] Document feature flag usage

**Rollout Runbook** (`docs/operations/adhd-engine-rollout.md`):
```markdown
# ADHD Engine Integration Rollout

## Pre-Rollout Checklist
- [ ] ADHD Engine service is running
- [ ] Redis db=5 is accessible
- [ ] All services have ADHDConfigService dependency
- [ ] Feature flags are OFF (default)
- [ ] Monitoring alerts configured

## Phase 1: Beta Test (Day 1-2)
1. Enable for one developer:
   ```bash
   ./scripts/enable_adhd_integration.sh
   # Select Phase 1 only
   ```
2. Monitor for 48 hours
3. Collect feedback
4. Verify metrics: response times, error rates

## Phase 2: Serena Rollout (Day 3-4)
1. Enable Serena globally:
   ```bash
   redis-cli -n 5 SET "adhd:feature_flags:adhd_engine_integration_serena:global" "true"
   ```
2. Monitor Serena MCP for 24 hours
3. Check: max_results adapting to attention state?
4. Rollback if issues:
   ```bash
   redis-cli -n 5 DEL "adhd:feature_flags:adhd_engine_integration_serena:global"
   ```

## Phase 3: ConPort Rollout (Day 5)
1. Enable ConPort globally
2. Verify duplicate AttentionStateMonitor removed
3. Monitor for 24 hours

## Phase 4: Full Rollout (Day 6-7)
1. Enable all services
2. Remove feature flag checks (optional, for cleaner code)
3. Update documentation
4. Celebrate! 🎉

## Rollback Procedure
```bash
# Emergency rollback - disable all flags
redis-cli -n 5 KEYS "adhd:feature_flags:*" | xargs redis-cli -n 5 DEL
```

Services automatically fallback to hardcoded defaults.

## Success Metrics
- [ ] All services query ADHD Engine (check logs)
- [ ] max_results varies by attention state
- [ ] complexity_threshold varies by energy level
- [ ] No duplicate attention state detection
- [ ] Response times unchanged (<5ms overhead)
- [ ] Zero regressions in functionality
```

**Deliverables**:
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] Rollout runbook ready
- [ ] Monitoring configured
- [ ] Ready for production rollout!

---

## Risk Assessment & Mitigation

### Risk 1: ADHD Engine Unavailable
**Probability**: LOW
**Impact**: MEDIUM
**Mitigation**: All services have hardcoded fallback defaults
**Rollback**: Feature flags allow instant disable

### Risk 2: Performance Degradation
**Probability**: LOW
**Impact**: MEDIUM
**Mitigation**: 5-minute caching reduces Redis queries to <0.2/sec
**Monitoring**: Track p95 latency, alert if >10ms overhead

### Risk 3: Incorrect ADHD State
**Probability**: MEDIUM (initially)
**Impact**: LOW
**Mitigation**: ADHD Engine already tested, defaults are safe
**Validation**: Beta test with real users for 48 hours

### Risk 4: Feature Flag Bugs
**Probability**: LOW
**Impact**: HIGH (could disable for all users)
**Mitigation**: Extensive testing, gradual rollout
**Recovery**: Redis-based flags can be fixed immediately

---

## Success Metrics

**Technical Metrics**:
- [ ] 23 hardcoded thresholds reduced to 0
- [ ] All services query ADHD Engine successfully
- [ ] Response time overhead <5ms (with caching)
- [ ] Cache hit rate >95%
- [ ] Zero functional regressions

**User Experience Metrics**:
- [ ] max_results adapts to attention state (5 vs 10 vs 15)
- [ ] complexity_threshold adapts to energy level (0.3 vs 0.7 vs 1.0)
- [ ] Break suggestions personalized per user
- [ ] Context depth adapts to cognitive capacity

**Business Metrics**:
- [ ] ADHD developers report improved experience
- [ ] Reduced cognitive overload incidents
- [ ] Increased task completion rates
- [ ] Positive feedback on personalization

---

## Rollback Plan

**Immediate Rollback** (if critical issues):
```bash
# Disable all feature flags instantly
redis-cli -n 5 KEYS "adhd:feature_flags:*" | xargs redis-cli -n 5 DEL

# Verify services using fallback defaults
tail -f /var/log/serena/mcp.log | grep "ADHD Engine"
# Should see: "ADHD Engine unavailable, using defaults"
```

**Partial Rollback** (if service-specific issues):
```bash
# Disable just Serena
redis-cli -n 5 DEL "adhd:feature_flags:adhd_engine_integration_serena:global"

# Other services unaffected
```

**Code Rollback** (if ADHDConfigService has bugs):
1. Revert commits
2. Redeploy services
3. Feature flags already OFF, so no user impact

---

## Next Steps After Completion

1. **Monitor for 1 week**: Collect metrics, user feedback
2. **Optimize**: Tune cache TTL, adjust thresholds if needed
3. **Enhance**: Add more ADHD accommodations
4. **Document**: Write case study on integration approach
5. **Celebrate**: Share success with team! 🎉

---

**Estimated Total Effort**: 7 days (14 focus blocks @ 25 minutes each)
**Risk Level**: MEDIUM (mitigated by feature flags)
**Impact**: EXTREME (unlocks fully-built ADHD Engine)
**ROI**: 🔥 Highest of all integration tasks
