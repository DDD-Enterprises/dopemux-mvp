"""
Unit Tests for ADHDConfigService

Tests the centralized ADHD configuration service that all services
will query instead of hardcoding thresholds.
"""

import pytest
import pytest_asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from adhd_config_service import ADHDConfigService, get_adhd_config_service, reset_adhd_config_service


@pytest_asyncio.fixture
async def adhd_service(redis_client):
    """Create ADHDConfigService instance for testing."""
    service = ADHDConfigService(
        redis_url="redis://localhost:6379/5",
        workspace_id="/test"
    )
    service.redis_client = redis_client  # Inject test client
    return service


class TestMaxResults:
    """Test get_max_results() method."""

    @pytest.mark.asyncio
    async def test_scattered_attention_limits_results(self, adhd_service, redis_client):
        """Scattered attention should limit results to 5."""
        # Setup: User in scattered state
        await redis_client.set("adhd:attention_state:user1", "scattered")

        # Execute
        max_results = await adhd_service.get_max_results("user1")

        # Verify
        assert max_results == 5, "Scattered attention should limit to 5 results"

    @pytest.mark.asyncio
    async def test_focused_attention_allows_more_results(self, adhd_service, redis_client):
        """Focused attention should allow 15 results."""
        await redis_client.set("adhd:attention_state:user1", "focused")

        max_results = await adhd_service.get_max_results("user1")

        assert max_results == 15, "Focused attention should allow 15 results"

    @pytest.mark.asyncio
    async def test_hyperfocused_allows_maximum_results(self, adhd_service, redis_client):
        """Hyperfocused attention should allow 40 results."""
        await redis_client.set("adhd:attention_state:user1", "hyperfocused")

        max_results = await adhd_service.get_max_results("user1")

        assert max_results == 40, "Hyperfocused should allow 40 results"

    @pytest.mark.asyncio
    async def test_overwhelmed_minimizes_results(self, adhd_service, redis_client):
        """Overwhelmed state should minimize results to 3."""
        await redis_client.set("adhd:attention_state:user1", "overwhelmed")

        max_results = await adhd_service.get_max_results("user1")

        assert max_results == 3, "Overwhelmed should minimize to 3 results"

    @pytest.mark.asyncio
    async def test_default_when_no_state(self, adhd_service, redis_client):
        """Should default to 10 when no attention state set."""
        # No state set for user2
        max_results = await adhd_service.get_max_results("user2")

        assert max_results == 10, "Should default to 10 when no state"


class TestComplexityThreshold:
    """Test get_complexity_threshold() method."""

    @pytest.mark.asyncio
    async def test_very_low_energy_lowers_threshold(self, adhd_service, redis_client):
        """Very low energy should set threshold to 0.3 (only simple tasks)."""
        await redis_client.set("adhd:energy_level:user1", "very_low")

        threshold = await adhd_service.get_complexity_threshold("user1")

        assert threshold == 0.3, "Very low energy should lower threshold to 0.3"

    @pytest.mark.asyncio
    async def test_low_energy_moderate_threshold(self, adhd_service, redis_client):
        """Low energy should set threshold to 0.5."""
        await redis_client.set("adhd:energy_level:user1", "low")

        threshold = await adhd_service.get_complexity_threshold("user1")

        assert threshold == 0.5, "Low energy threshold should be 0.5"

    @pytest.mark.asyncio
    async def test_high_energy_allows_complex_tasks(self, adhd_service, redis_client):
        """High energy should allow complex tasks (0.9)."""
        await redis_client.set("adhd:energy_level:user1", "high")

        threshold = await adhd_service.get_complexity_threshold("user1")

        assert threshold == 0.9, "High energy should allow 0.9 complexity"

    @pytest.mark.asyncio
    async def test_hyperfocus_removes_limits(self, adhd_service, redis_client):
        """Hyperfocus should remove complexity limits (1.0)."""
        await redis_client.set("adhd:energy_level:user1", "hyperfocus")

        threshold = await adhd_service.get_complexity_threshold("user1")

        assert threshold == 1.0, "Hyperfocus should allow any complexity"


class TestContextDepth:
    """Test get_context_depth() method."""

    @pytest.mark.asyncio
    async def test_scattered_minimizes_depth(self, adhd_service, redis_client):
        """Scattered attention should minimize context depth to 1."""
        await redis_client.set("adhd:attention_state:user1", "scattered")

        depth = await adhd_service.get_context_depth("user1")

        assert depth == 1, "Scattered should limit depth to 1 level"

    @pytest.mark.asyncio
    async def test_focused_allows_standard_depth(self, adhd_service, redis_client):
        """Focused attention should allow 3 levels."""
        await redis_client.set("adhd:attention_state:user1", "focused")

        depth = await adhd_service.get_context_depth("user1")

        assert depth == 3, "Focused should allow 3 levels"

    @pytest.mark.asyncio
    async def test_hyperfocused_allows_deep_exploration(self, adhd_service, redis_client):
        """Hyperfocused should allow 5 levels for deep dives."""
        await redis_client.set("adhd:attention_state:user1", "hyperfocused")

        depth = await adhd_service.get_context_depth("user1")

        assert depth == 5, "Hyperfocused should allow 5 levels"


class TestBreakSuggestions:
    """Test should_suggest_break() method."""

    @pytest.mark.asyncio
    async def test_suggests_break_after_max_duration(self, adhd_service, redis_client):
        """Should suggest break after max task duration."""
        # Setup: User profile with 90min max duration
        profile = {
            "user_id": "user1",
            "optimal_task_duration": 25,
            "max_task_duration": 90
        }
        await redis_client.set("adhd:profile:user1", json.dumps(profile))

        # Set last break to 95 minutes ago (exceeds max)
        last_break = (datetime.now() - timedelta(minutes=95)).isoformat()
        await redis_client.set("adhd:last_break:user1", last_break)

        # Execute
        should_break, reason = await adhd_service.should_suggest_break("user1")

        # Verify
        assert should_break is True, "Should suggest break after max duration"
        assert "Maximum duration" in reason or "95" in reason

    @pytest.mark.asyncio
    async def test_suggests_break_for_very_low_energy(self, adhd_service, redis_client):
        """Should suggest break when energy is very low."""
        await redis_client.set("adhd:energy_level:user1", "very_low")

        should_break, reason = await adhd_service.should_suggest_break("user1")

        assert should_break is True, "Should suggest break for very low energy"
        assert "Low energy" in reason

    @pytest.mark.asyncio
    async def test_no_break_needed_when_recent(self, adhd_service, redis_client):
        """Should not suggest break if recent break taken."""
        # Setup: Break taken 10 minutes ago
        last_break = (datetime.now() - timedelta(minutes=10)).isoformat()
        await redis_client.set("adhd:last_break:user1", last_break)
        await redis_client.set("adhd:energy_level:user1", "medium")

        should_break, reason = await adhd_service.should_suggest_break("user1")

        assert should_break is False, "Should not suggest break when recent"
        assert reason == ""


class TestCaching:
    """Test 5-minute cache functionality."""

    @pytest.mark.asyncio
    async def test_caching_reduces_redis_queries(self, adhd_service, redis_client):
        """Verify caching works and reduces Redis queries."""
        await redis_client.set("adhd:attention_state:user1", "focused")

        # First call - should query Redis
        result1 = await adhd_service._get_attention_state("user1")
        assert result1 == "focused"

        # Change value in Redis
        await redis_client.set("adhd:attention_state:user1", "scattered")

        # Second call - should use cache (returns old value)
        result2 = await adhd_service._get_attention_state("user1")
        assert result2 == "focused", "Should return cached value"

        # Verify cache was used
        assert "attention:user1" in adhd_service._cache

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, adhd_service, redis_client):
        """Verify cache expires after 5-minute TTL."""
        await redis_client.set("adhd:attention_state:user1", "focused")

        # First call
        result1 = await adhd_service._get_attention_state("user1")
        assert result1 == "focused"

        # Manually expire cache by setting old timestamp
        cache_key = "attention:user1"
        old_time = datetime.now() - timedelta(minutes=6)  # 6 minutes ago
        adhd_service._cache[cache_key] = (old_time, "focused")

        # Change Redis value
        await redis_client.set("adhd:attention_state:user1", "scattered")

        # Next call should query Redis (cache expired)
        result2 = await adhd_service._get_attention_state("user1")
        assert result2 == "scattered", "Should query Redis after cache expiry"

    @pytest.mark.asyncio
    async def test_clear_cache_for_user(self, adhd_service, redis_client):
        """Test clearing cache for specific user."""
        # Setup cache for two users
        adhd_service._cache["attention:user1"] = (datetime.now(), "focused")
        adhd_service._cache["energy:user1"] = (datetime.now(), "high")
        adhd_service._cache["attention:user2"] = (datetime.now(), "scattered")

        # Clear cache for user1
        await adhd_service.clear_cache("user1")

        # Verify user1 cache cleared, user2 intact
        assert "attention:user1" not in adhd_service._cache
        assert "energy:user1" not in adhd_service._cache
        assert "attention:user2" in adhd_service._cache


class TestStateSummary:
    """Test get_current_state_summary() method."""

    @pytest.mark.asyncio
    async def test_complete_state_summary(self, adhd_service, redis_client):
        """Should return complete state summary with all fields."""
        # Setup state
        await redis_client.set("adhd:energy_level:user1", "medium")
        await redis_client.set("adhd:attention_state:user1", "focused")

        profile = {
            "user_id": "user1",
            "optimal_task_duration": 25,
            "distraction_sensitivity": 0.6
        }
        await redis_client.set("adhd:profile:user1", json.dumps(profile))

        # Execute
        summary = await adhd_service.get_current_state_summary("user1")

        # Verify all fields present
        assert summary["user_id"] == "user1"
        assert summary["energy_level"] == "medium"
        assert summary["attention_state"] == "focused"
        assert summary["max_results"] == 15  # Focused = 15
        assert summary["complexity_threshold"] == 0.7  # Medium energy = 0.7
        assert summary["context_depth"] == 3  # Focused = 3
        assert "timestamp" in summary
        assert "profile" in summary


class TestHealthCheck:
    """Test health_check() method."""

    @pytest.mark.asyncio
    async def test_health_check_when_healthy(self, adhd_service, redis_client):
        """Health check should return healthy when Redis connected."""
        health = await adhd_service.health_check()

        assert health["healthy"] is True
        assert health["status"] == "healthy"
        assert health["redis_connected"] is True
        assert "cache_size" in health
        assert "timestamp" in health

    @pytest.mark.asyncio
    async def test_health_check_when_not_initialized(self):
        """Health check should return not_initialized when Redis not connected."""
        service = ADHDConfigService("redis://localhost:6379/5", "/test")
        # Don't initialize - no Redis connection

        health = await service.health_check()

        assert health["healthy"] is False
        assert health["status"] == "not_initialized"


class TestSingletonPattern:
    """Test global singleton instance."""

    @pytest.mark.asyncio
    async def test_get_adhd_config_service_returns_singleton(self):
        """Should return same instance on multiple calls."""
        # Reset first
        await reset_adhd_config_service()

        # Get service twice
        service1 = await get_adhd_config_service()
        service2 = await get_adhd_config_service()

        # Verify same instance
        assert service1 is service2, "Should return singleton instance"

        # Cleanup
        await reset_adhd_config_service()

    @pytest.mark.asyncio
    async def test_reset_clears_singleton(self):
        """reset_adhd_config_service() should clear singleton."""
        service1 = await get_adhd_config_service()

        await reset_adhd_config_service()

        service2 = await get_adhd_config_service()

        # Should be different instances after reset
        assert service1 is not service2, "Reset should clear singleton"

        # Cleanup
        await reset_adhd_config_service()


class TestGracefulDegradation:
    """Test behavior when ADHD Engine unavailable."""

    @pytest.mark.asyncio
    async def test_defaults_when_no_attention_state(self, adhd_service, redis_client):
        """Should use safe defaults when ADHD Engine hasn't set state."""
        # No state set in Redis
        max_results = await adhd_service.get_max_results("user_unknown")

        # Should return default
        assert max_results == 10, "Should default to 10 when no state"

    @pytest.mark.asyncio
    async def test_defaults_when_no_energy_level(self, adhd_service, redis_client):
        """Should use safe defaults when no energy level."""
        threshold = await adhd_service.get_complexity_threshold("user_unknown")

        assert threshold == 0.7, "Should default to 0.7 when no energy"

    @pytest.mark.asyncio
    async def test_defaults_when_no_profile(self, adhd_service, redis_client):
        """Should work without user profile."""
        cognitive_threshold = await adhd_service.get_cognitive_load_threshold("user_unknown")

        assert cognitive_threshold == 0.8, "Should default to 0.8 when no profile"


class TestUserProfile:
    """Test user profile integration."""

    @pytest.mark.asyncio
    async def test_cognitive_load_adjusts_for_distraction_sensitivity(self, adhd_service, redis_client):
        """High distraction sensitivity should lower cognitive load threshold."""
        # High sensitivity profile
        profile = {
            "user_id": "user1",
            "distraction_sensitivity": 0.9  # Very high sensitivity
        }
        await redis_client.set("adhd:profile:user1", json.dumps(profile))

        threshold = await adhd_service.get_cognitive_load_threshold("user1")

        # Higher sensitivity = lower threshold
        # Formula: max(0.5, 1.0 - (0.9 * 0.5)) = max(0.5, 0.55) = 0.55
        assert 0.5 <= threshold <= 0.6, "High sensitivity should lower threshold"

    @pytest.mark.asyncio
    async def test_profile_caching_works(self, adhd_service, redis_client):
        """Profile should be cached for 5 minutes."""
        profile = {"user_id": "user1", "optimal_task_duration": 30}
        await redis_client.set("adhd:profile:user1", json.dumps(profile))

        # First call - loads from Redis
        profile1 = await adhd_service._get_user_profile("user1")
        assert profile1["optimal_task_duration"] == 30

        # Change in Redis
        profile["optimal_task_duration"] = 45
        await redis_client.set("adhd:profile:user1", json.dumps(profile))

        # Second call - should return cached value
        profile2 = await adhd_service._get_user_profile("user1")
        assert profile2["optimal_task_duration"] == 30, "Should use cached profile"


class TestIntegration:
    """Integration tests with ADHD Engine."""

    @pytest.mark.asyncio
    async def test_end_to_end_state_query(self, adhd_service, redis_client):
        """
        Test complete workflow:
        1. ADHD Engine sets state in Redis
        2. ADHDConfigService queries state
        3. Returns appropriate accommodations
        """
        # Simulate ADHD Engine setting state
        await redis_client.set("adhd:attention_state:developer1", "scattered")
        await redis_client.set("adhd:energy_level:developer1", "low")

        profile = {
            "user_id": "developer1",
            "optimal_task_duration": 25,
            "max_task_duration": 90,
            "distraction_sensitivity": 0.7
        }
        await redis_client.set("adhd:profile:developer1", json.dumps(profile))

        # Query accommodations
        summary = await adhd_service.get_current_state_summary("developer1")

        # Verify appropriate accommodations
        assert summary["energy_level"] == "low"
        assert summary["attention_state"] == "scattered"
        assert summary["max_results"] == 5, "Scattered should limit results"
        assert summary["complexity_threshold"] == 0.5, "Low energy should lower threshold"
        assert summary["context_depth"] == 1, "Scattered should minimize depth"

        print("✅ End-to-end ADHD accommodation workflow successful!")


class TestFocusModeLimit:
    """Test get_focus_mode_limit() method."""

    @pytest.mark.asyncio
    async def test_focus_mode_halves_results(self, adhd_service, redis_client):
        """Focus mode should show half the normal results."""
        await redis_client.set("adhd:attention_state:user1", "focused")

        # Normal: 15 results
        normal_limit = await adhd_service.get_max_results("user1")
        assert normal_limit == 15

        # Focus mode: 7-8 results (half of 15)
        focus_limit = await adhd_service.get_focus_mode_limit("user1")
        assert focus_limit == 7, "Focus mode should halve results"

    @pytest.mark.asyncio
    async def test_focus_mode_minimum_three(self, adhd_service, redis_client):
        """Focus mode should never go below 3 results."""
        # Overwhelmed normally gives 3 results
        await redis_client.set("adhd:attention_state:user1", "overwhelmed")

        focus_limit = await adhd_service.get_focus_mode_limit("user1")

        # Even halved, should be minimum 3
        assert focus_limit >= 3, "Focus mode should have minimum 3 results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
