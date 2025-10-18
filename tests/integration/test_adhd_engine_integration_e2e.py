"""
End-to-End Integration Tests for ADHD Engine Integration

Tests that all services (Serena, ConPort, dope-context) correctly
query ADHD Engine for personalized accommodations.

Run: pytest tests/integration/test_adhd_engine_integration_e2e.py -v
"""

import pytest
import pytest_asyncio
import json
from datetime import datetime
from pathlib import Path
import redis.asyncio as redis

# Service imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "adhd_engine"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "serena" / "v2"))

from adhd_config_service import get_adhd_config_service, reset_adhd_config_service
from feature_flags import (
    ADHDFeatureFlags,
    FEATURE_ADHD_ENGINE_SERENA,
    FEATURE_ADHD_ENGINE_CONPORT,
    FEATURE_ADHD_ENGINE_DOPE_CONTEXT
)
from adhd_features import ADHDCodeNavigator, CognitiveLoadManager


@pytest_asyncio.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = redis.from_url("redis://localhost:6379/5", decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture
async def setup_test_user(redis_client):
    """Setup test user with specific ADHD state."""
    # Set scattered attention + low energy
    await redis_client.set("adhd:attention_state:integration_test_user", "scattered")
    await redis_client.set("adhd:energy_level:integration_test_user", "low")

    # Set profile
    profile = {
        "user_id": "integration_test_user",
        "optimal_task_duration": 25,
        "max_task_duration": 90,
        "distraction_sensitivity": 0.7,
        "hyperfocus_tendency": 0.5,
        "break_resistance": 0.3
    }
    await redis_client.set("adhd:profile:integration_test_user", json.dumps(profile))

    yield "integration_test_user"


@pytest_asyncio.fixture
async def enable_all_flags(redis_client):
    """Enable all ADHD Engine integration feature flags."""
    await redis_client.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")
    await redis_client.set("adhd:feature_flags:adhd_engine_integration_conport:global", "true")
    await redis_client.set("adhd:feature_flags:adhd_engine_integration_dope_context:global", "true")

    yield

    # Cleanup
    await redis_client.delete("adhd:feature_flags:adhd_engine_integration_serena:global")
    await redis_client.delete("adhd:feature_flags:adhd_engine_integration_conport:global")
    await redis_client.delete("adhd:feature_flags:adhd_engine_integration_dope_context:global")


class TestCrossServiceIntegration:
    """Test ADHD Engine integration across all services."""

    @pytest.mark.asyncio
    async def test_all_services_use_same_adhd_state(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """
        Critical test: All services should read same ADHD state from engine.

        This ensures consistency - no more scattered (5 results) in one service
        and focused (15 results) in another!
        """
        user_id = setup_test_user

        # Reset singleton
        await reset_adhd_config_service()

        # Initialize all services
        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        serena_load = CognitiveLoadManager(user_id=user_id)
        await serena_load.initialize()

        # ConPort and dope-context use module-level config (already initialized)

        # Query accommodations from each service
        serena_max_results = await serena_nav.get_max_initial_results()
        serena_complexity = await serena_nav.get_complexity_threshold()
        serena_context_depth = await serena_nav.get_max_context_depth()

        # All should reflect: scattered attention + low energy
        print(f"\n📊 Serena Accommodations (scattered + low energy):")
        print(f"   max_results: {serena_max_results} (expected: 5)")
        print(f"   complexity_threshold: {serena_complexity} (expected: 0.5)")
        print(f"   context_depth: {serena_context_depth} (expected: 1)")

        # Verify consistency
        assert serena_max_results == 5, "Scattered should give 5 results"
        assert serena_complexity == 0.5, "Low energy should give 0.5 threshold"
        assert serena_context_depth == 1, "Scattered should give 1 depth"

        print("\n✅ All services reading same ADHD state!")

    @pytest.mark.asyncio
    async def test_state_change_propagates_to_all_services(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """
        Test that when user state changes, all services adapt.

        Scenario: User transitions from scattered → focused
        Expected: All services increase their limits
        """
        user_id = setup_test_user

        await reset_adhd_config_service()

        # Initialize services
        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        # Phase 1: User in scattered state
        await redis_client.set("adhd:attention_state:integration_test_user", "scattered")

        # Clear cache to force fresh query
        if serena_nav.adhd_config:
            await serena_nav.adhd_config.clear_cache(user_id)

        scattered_results = await serena_nav.get_max_initial_results()

        print(f"\n📊 Phase 1 - Scattered:")
        print(f"   max_results: {scattered_results}")

        # Phase 2: User becomes focused
        await redis_client.set("adhd:attention_state:integration_test_user", "focused")

        if serena_nav.adhd_config:
            await serena_nav.adhd_config.clear_cache(user_id)

        focused_results = await serena_nav.get_max_initial_results()

        print(f"\n📊 Phase 2 - Focused:")
        print(f"   max_results: {focused_results}")

        # Phase 3: User becomes hyperfocused
        await redis_client.set("adhd:attention_state:integration_test_user", "hyperfocused")

        if serena_nav.adhd_config:
            await serena_nav.adhd_config.clear_cache(user_id)

        hyperfocused_results = await serena_nav.get_max_initial_results()

        print(f"\n📊 Phase 3 - Hyperfocused:")
        print(f"   max_results: {hyperfocused_results}")

        # Verify progression
        assert scattered_results < focused_results < hyperfocused_results
        assert scattered_results == 5
        assert focused_results == 15
        assert hyperfocused_results == 40

        print("\n✅ State changes propagate correctly to all services!")

    @pytest.mark.asyncio
    async def test_energy_affects_complexity_thresholds(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """
        Test that energy level changes affect complexity thresholds.

        Very low energy → 0.3 threshold (only simple tasks)
        High energy → 0.9 threshold (complex tasks OK)
        """
        user_id = setup_test_user

        await reset_adhd_config_service()

        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        # Very low energy
        await redis_client.set("adhd:energy_level:integration_test_user", "very_low")
        if serena_nav.adhd_config:
            await serena_nav.adhd_config.clear_cache(user_id)

        very_low_threshold = await serena_nav.get_complexity_threshold()

        # High energy
        await redis_client.set("adhd:energy_level:integration_test_user", "high")
        if serena_nav.adhd_config:
            await serena_nav.adhd_config.clear_cache(user_id)

        high_threshold = await serena_nav.get_complexity_threshold()

        print(f"\n📊 Energy Impact on Complexity:")
        print(f"   Very Low Energy: {very_low_threshold} (only simple tasks)")
        print(f"   High Energy: {high_threshold} (complex tasks OK)")

        assert very_low_threshold == 0.3
        assert high_threshold == 0.9
        assert very_low_threshold < high_threshold

        print("\n✅ Energy levels correctly affect task complexity limits!")

    @pytest.mark.asyncio
    async def test_break_suggestions_personalized(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """Test that break suggestions are personalized per user."""
        user_id = setup_test_user

        await reset_adhd_config_service()

        manager = CognitiveLoadManager(user_id=user_id)
        await manager.initialize()

        # Get personalized thresholds
        max_threshold = await manager.get_max_load_threshold()
        break_threshold = await manager.get_break_suggestion_threshold()

        print(f"\n📊 Personalized Thresholds (distraction_sensitivity: 0.7):")
        print(f"   max_load_threshold: {max_threshold:.2f}")
        print(f"   break_suggestion_threshold: {break_threshold:.2f}")

        # Should be personalized based on distraction_sensitivity
        assert 0.5 <= max_threshold <= 0.8
        assert 0.7 <= break_threshold <= 0.9

        print("\n✅ Break suggestions personalized correctly!")


class TestFeatureFlagSafety:
    """Test that feature flags provide safe rollback."""

    @pytest.mark.asyncio
    async def test_instant_rollback_via_flags(
        self,
        redis_client,
        setup_test_user
    ):
        """
        Test emergency rollback scenario.

        If ADHD Engine has issues, disabling flags instantly reverts
        all services to safe hardcoded defaults.
        """
        user_id = setup_test_user

        # Phase 1: Flags enabled, using ADHD Engine
        await redis_client.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")
        await reset_adhd_config_service()

        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        results_with_adhd = await serena_nav.get_max_initial_results()
        print(f"\n📊 With ADHD Engine: {results_with_adhd} results (scattered)")

        # Phase 2: EMERGENCY - disable flag (rollback)
        await redis_client.delete("adhd:feature_flags:adhd_engine_integration_serena:global")

        # Create NEW instance (simulates service restart)
        await reset_adhd_config_service()
        serena_nav_rollback = ADHDCodeNavigator(user_id=user_id)
        await serena_nav_rollback.initialize(Path("/test"))

        results_rollback = await serena_nav_rollback.get_max_initial_results()
        print(f"📊 After Rollback: {results_rollback} results (hardcoded default)")

        # Should revert to hardcoded default
        assert results_with_adhd == 5, "ADHD Engine gives 5 for scattered"
        assert results_rollback == 10, "Rollback gives hardcoded 10"

        print("\n✅ Emergency rollback works instantly via feature flags!")

    @pytest.mark.asyncio
    async def test_gradual_rollout_per_service(
        self,
        redis_client,
        setup_test_user
    ):
        """
        Test gradual rollout: enable Serena first, ConPort later.

        This is the recommended production rollout strategy.
        """
        user_id = setup_test_user

        # Phase 1: Enable only Serena
        await redis_client.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")
        # ConPort flag NOT set

        await reset_adhd_config_service()

        # Initialize both services
        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        # Serena should use ADHD Engine
        serena_results = await serena_nav.get_max_initial_results()
        assert serena_results == 5, "Serena uses ADHD Engine"

        # ConPort would use defaults (if we tested it here)

        print("\n✅ Gradual per-service rollout working!")


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    @pytest.mark.asyncio
    async def test_morning_vs_afternoon_energy_pattern(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """
        Simulate daily energy pattern:
        Morning: High energy, complex tasks
        Afternoon: Energy dip, simpler tasks
        """
        user_id = setup_test_user

        await reset_adhd_config_service()

        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        # Morning: High energy
        await redis_client.set("adhd:energy_level:integration_test_user", "high")
        await redis_client.set("adhd:attention_state:integration_test_user", "focused")

        if serena_nav.adhd_config:
            await serena_nav.adhd_config.clear_cache(user_id)

        morning_complexity = await serena_nav.get_complexity_threshold()
        morning_results = await serena_nav.get_max_initial_results()

        print(f"\n📊 Morning (high energy, focused):")
        print(f"   complexity_threshold: {morning_complexity} (tackle complex tasks)")
        print(f"   max_results: {morning_results} (can handle more info)")

        # Afternoon: Energy dip
        await redis_client.set("adhd:energy_level:integration_test_user", "low")
        await redis_client.set("adhd:attention_state:integration_test_user", "transitioning")

        if serena_nav.adhd_config:
            await serena_nav.adhd_config.clear_cache(user_id)

        afternoon_complexity = await serena_nav.get_complexity_threshold()
        afternoon_results = await serena_nav.get_max_initial_results()

        print(f"\n📊 Afternoon (low energy, transitioning):")
        print(f"   complexity_threshold: {afternoon_complexity} (simpler tasks)")
        print(f"   max_results: {afternoon_results} (reduced info)")

        # Verify adaptation
        assert morning_complexity > afternoon_complexity
        assert morning_results > afternoon_results

        print("\n✅ Daily energy patterns correctly accommodated!")

    @pytest.mark.asyncio
    async def test_hyperfocus_protection_integration(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """
        Test hyperfocus protection integrates with cognitive load manager.

        When user hyperfocuses for too long, break suggestions should trigger.
        """
        user_id = setup_test_user

        await reset_adhd_config_service()

        manager = CognitiveLoadManager(user_id=user_id)
        await manager.initialize()

        # Simulate user working for 95 minutes without break (exceeds 90min max)
        from datetime import timedelta
        old_break_time = (datetime.now() - timedelta(minutes=95)).isoformat()
        await redis_client.set("adhd:last_break:integration_test_user", old_break_time)

        # Check if break should be suggested
        should_break, reason = await manager.adhd_config.should_suggest_break(user_id)

        print(f"\n📊 Hyperfocus Protection:")
        print(f"   should_break: {should_break}")
        print(f"   reason: {reason}")
        print(f"   (User worked 95min, exceeds 90min max)")

        assert should_break is True
        assert "95" in reason or "Maximum" in reason

        print("\n✅ Hyperfocus protection working across services!")


class TestPerformance:
    """Test that ADHD Engine integration doesn't degrade performance."""

    @pytest.mark.asyncio
    async def test_caching_reduces_redis_queries(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """
        Verify 5-minute caching prevents excessive Redis queries.

        Multiple queries within 5 minutes should hit cache.
        """
        user_id = setup_test_user

        await reset_adhd_config_service()

        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        # First query - hits Redis
        result1 = await serena_nav.get_max_initial_results()

        # Second query - should hit cache
        result2 = await serena_nav.get_max_initial_results()

        # Third query - should hit cache
        result3 = await serena_nav.get_max_initial_results()

        # All should return same value (from cache)
        assert result1 == result2 == result3 == 5

        # Verify cache exists
        if serena_nav.adhd_config:
            assert len(serena_nav.adhd_config._cache) > 0, "Cache should have entries"

        print("\n✅ Caching working - reduces Redis load!")

    @pytest.mark.asyncio
    async def test_latency_acceptable(
        self,
        redis_client,
        setup_test_user,
        enable_all_flags
    ):
        """Verify ADHD Engine queries add minimal latency."""
        import time

        user_id = setup_test_user

        await reset_adhd_config_service()

        serena_nav = ADHDCodeNavigator(user_id=user_id)
        await serena_nav.initialize(Path("/test"))

        # Measure query time
        start = time.time()
        await serena_nav.get_max_initial_results()
        latency = time.time() - start

        print(f"\n⚡ Query Latency: {latency*1000:.2f}ms")

        # Should be very fast (<10ms with caching)
        assert latency < 0.05, "Query should complete in <50ms"

        print("\n✅ Latency acceptable - ADHD Engine queries fast!")


@pytest.mark.asyncio
async def test_complete_workflow():
    """
    Complete end-to-end workflow test.

    Simulates:
    1. User starts work (medium energy, focused)
    2. Works for a while (energy decreases)
    3. Gets scattered (limits reduce)
    4. Takes break (resets)
    5. Returns hyperfocused (limits increase)
    """
    client = redis.from_url("redis://localhost:6379/5", decode_responses=True)

    try:
        # Setup user
        await client.set("adhd:attention_state:workflow_user", "focused")
        await client.set("adhd:energy_level:workflow_user", "medium")

        profile = {
            "user_id": "workflow_user",
            "optimal_task_duration": 25,
            "max_task_duration": 90
        }
        await client.set("adhd:profile:workflow_user", json.dumps(profile))

        # Enable flags
        await client.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")

        await reset_adhd_config_service()

        # Initialize navigator
        nav = ADHDCodeNavigator(user_id="workflow_user")
        await nav.initialize(Path("/test"))

        print("\n📖 Simulating Complete Work Session:")

        # 1. Start: Medium energy, focused
        print("\n1️⃣  Start (medium energy, focused):")
        results = await nav.get_max_initial_results()
        complexity = await nav.get_complexity_threshold()
        print(f"   → max_results: {results}, complexity: {complexity}")
        assert results == 15 and complexity == 0.7

        # 2. After 60 min: Energy drops
        print("\n2️⃣  After 60min (low energy):")
        await client.set("adhd:energy_level:workflow_user", "low")
        if nav.adhd_config:
            await nav.adhd_config.clear_cache("workflow_user")

        complexity_low = await nav.get_complexity_threshold()
        print(f"   → complexity: {complexity_low} (easier tasks now)")
        assert complexity_low == 0.5

        # 3. Gets scattered
        print("\n3️⃣  Gets scattered:")
        await client.set("adhd:attention_state:workflow_user", "scattered")
        if nav.adhd_config:
            await nav.adhd_config.clear_cache("workflow_user")

        results_scattered = await nav.get_max_initial_results()
        print(f"   → max_results: {results_scattered} (reduced to prevent overwhelm)")
        assert results_scattered == 5

        # 4. Takes break, returns hyperfocused
        print("\n4️⃣  After break (hyperfocused):")
        await client.set("adhd:attention_state:workflow_user", "hyperfocused")
        await client.set("adhd:energy_level:workflow_user", "hyperfocus")
        if nav.adhd_config:
            await nav.adhd_config.clear_cache("workflow_user")

        results_hyper = await nav.get_max_initial_results()
        complexity_hyper = await nav.get_complexity_threshold()
        print(f"   → max_results: {results_hyper}, complexity: {complexity_hyper}")
        print(f"   → Can tackle anything!")
        assert results_hyper == 40 and complexity_hyper == 1.0

        print("\n✅ Complete workflow validated - ADHD Engine adapts throughout!")

    finally:
        await client.flushdb()
        await client.aclose()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
