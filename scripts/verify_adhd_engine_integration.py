#!/usr/bin/env python3
"""
Verification Script for ADHD Engine Integration

Tests that services correctly query ADHD Engine for dynamic accommodations.
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import redis.asyncio as redis
import json
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "adhd_engine"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "serena" / "v2"))

from adhd_config_service import get_adhd_config_service, reset_adhd_config_service
from feature_flags import ADHDFeatureFlags, FEATURE_ADHD_ENGINE_SERENA
from adhd_features import ADHDCodeNavigator, CognitiveLoadManager


async def setup_test_adhd_state():
    """Setup test ADHD state in Redis."""
    logger.info("🔧 Setting up test ADHD state in Redis...")

    client = redis.from_url("redis://localhost:6379/5", decode_responses=True)

    # Set test user to scattered attention + low energy
    await client.set("adhd:attention_state:test_user", "scattered")
    await client.set("adhd:energy_level:test_user", "low")

    # Set profile
    profile = {
        "user_id": "test_user",
        "optimal_task_duration": 25,
        "max_task_duration": 90,
        "distraction_sensitivity": 0.7,
        "hyperfocus_tendency": 0.6
    }
    await client.set("adhd:profile:test_user", json.dumps(profile))

    logger.info("✅ Test state configured:")
    logger.info(f"   Attention: scattered (should limit to 5 results)")
    logger.info(f"   Energy: low (should use 0.5 complexity threshold)")

    await client.aclose()


async def test_feature_flag_off():
    """Test with feature flag OFF (should use hardcoded defaults)."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Feature Flag OFF (Legacy Behavior)")
    logger.info("="*60)

    # Ensure flag is OFF
    client = redis.from_url("redis://localhost:6379/5", decode_responses=True)
    await client.delete("adhd:feature_flags:adhd_engine_integration_serena:global")
    await client.aclose()

    # Reset singleton to force re-initialization
    await reset_adhd_config_service()

    # Create navigator
    navigator = ADHDCodeNavigator(user_id="test_user")
    await navigator.initialize(Path("/test"))

    # Query values
    max_results = await navigator.get_max_initial_results()
    complexity = await navigator.get_complexity_threshold()
    context_depth = await navigator.get_max_context_depth()

    logger.info(f"\n📊 Results (Flag OFF):")
    logger.info(f"   max_results: {max_results} (expected: 10 - hardcoded default)")
    logger.info(f"   complexity_threshold: {complexity} (expected: 0.7 - hardcoded default)")
    logger.info(f"   context_depth: {context_depth} (expected: 3 - hardcoded default)")

    # Verify using defaults
    assert max_results == 10, "Should use hardcoded default when flag OFF"
    assert complexity == 0.7, "Should use hardcoded default when flag OFF"
    assert context_depth == 3, "Should use hardcoded default when flag OFF"

    logger.info("\n✅ PASS: Legacy behavior preserved (backward compatibility verified)")


async def test_feature_flag_on():
    """Test with feature flag ON (should use ADHD Engine)."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Feature Flag ON (ADHD Engine Integration)")
    logger.info("="*60)

    # Enable flag
    client = redis.from_url("redis://localhost:6379/5", decode_responses=True)
    await client.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")
    await client.aclose()

    # Reset singleton
    await reset_adhd_config_service()

    # Create navigator
    navigator = ADHDCodeNavigator(user_id="test_user")
    await navigator.initialize(Path("/test"))

    # Query values
    max_results = await navigator.get_max_initial_results()
    complexity = await navigator.get_complexity_threshold()
    context_depth = await navigator.get_max_context_depth()

    logger.info(f"\n📊 Results (Flag ON, User: scattered + low energy):")
    logger.info(f"   max_results: {max_results} (expected: 5 - scattered attention)")
    logger.info(f"   complexity_threshold: {complexity} (expected: 0.5 - low energy)")
    logger.info(f"   context_depth: {context_depth} (expected: 1 - scattered attention)")

    # Verify using ADHD Engine
    assert max_results == 5, "Scattered attention should limit to 5 results"
    assert complexity == 0.5, "Low energy should lower threshold to 0.5"
    assert context_depth == 1, "Scattered should limit depth to 1"

    logger.info("\n✅ PASS: ADHD Engine integration working! Accommodations adapt to user state!")


async def test_cognitive_load_manager():
    """Test CognitiveLoadManager integration."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: CognitiveLoadManager Integration")
    logger.info("="*60)

    # Ensure flag ON
    client = redis.from_url("redis://localhost:6379/5", decode_responses=True)
    await client.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")
    await client.aclose()

    # Reset singleton
    await reset_adhd_config_service()

    # Create manager
    manager = CognitiveLoadManager(user_id="test_user")
    await manager.initialize()

    # Get dynamic thresholds
    max_threshold = await manager.get_max_load_threshold()
    break_threshold = await manager.get_break_suggestion_threshold()

    logger.info(f"\n📊 Cognitive Load Thresholds:")
    logger.info(f"   max_load_threshold: {max_threshold:.2f}")
    logger.info(f"   break_suggestion_threshold: {break_threshold:.2f}")
    logger.info(f"   (Personalized based on user's distraction_sensitivity: 0.7)")

    # Assess navigation load
    assessment = await manager.assess_navigation_load(
        action="workspace_symbols",
        result_complexity=0.6,
        result_count=15
    )

    logger.info(f"\n📊 Load Assessment:")
    logger.info(f"   current_load: {assessment['current_load']:.2f}")
    logger.info(f"   recommendations: {assessment['recommendations']}")
    logger.info(f"   adhd_engine_active: {assessment.get('adhd_engine_active', False)}")

    assert assessment['adhd_engine_active'] is True, "Should show ADHD Engine is active"

    logger.info("\n✅ PASS: CognitiveLoadManager using ADHD Engine!")


async def test_state_adaptation():
    """Test that accommodations adapt when user state changes."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: State Adaptation (Dynamic Behavior)")
    logger.info("="*60)

    # Enable flag
    client = redis.from_url("redis://localhost:6379/5", decode_responses=True)
    await client.set("adhd:feature_flags:adhd_engine_integration_serena:global", "true")

    # Reset singleton to clear cache
    await reset_adhd_config_service()

    # Test 1: Scattered state
    await client.set("adhd:attention_state:test_user", "scattered")
    navigator = ADHDCodeNavigator(user_id="test_user")
    await navigator.initialize(Path("/test"))
    max_scattered = await navigator.get_max_initial_results()

    logger.info(f"\n📊 Scattered attention: max_results = {max_scattered}")

    # Test 2: Change to focused state
    await client.set("adhd:attention_state:test_user", "focused")
    # Clear cache to force fresh query
    if navigator.adhd_config:
        await navigator.adhd_config.clear_cache("test_user")

    max_focused = await navigator.get_max_initial_results()

    logger.info(f"📊 Focused attention: max_results = {max_focused}")

    # Test 3: Change to hyperfocused
    await client.set("adhd:attention_state:test_user", "hyperfocused")
    if navigator.adhd_config:
        await navigator.adhd_config.clear_cache("test_user")

    max_hyperfocused = await navigator.get_max_initial_results()

    logger.info(f"📊 Hyperfocused: max_results = {max_hyperfocused}")

    await client.aclose()

    # Verify progression
    assert max_scattered < max_focused < max_hyperfocused, "Results should increase with attention capacity"
    assert max_scattered == 5, "Scattered = 5"
    assert max_focused == 15, "Focused = 15"
    assert max_hyperfocused == 40, "Hyperfocused = 40"

    logger.info("\n✅ PASS: Accommodations dynamically adapt to user state changes!")


async def main():
    """Run all verification tests."""
    logger.info("\n🚀 ADHD Engine Integration Verification")
    logger.info("="*60)

    try:
        # Setup test state
        await setup_test_adhd_state()

        # Run tests
        await test_feature_flag_off()
        await test_feature_flag_on()
        await test_cognitive_load_manager()
        await test_state_adaptation()

        logger.info("\n" + "="*60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("="*60)
        logger.info("\n✅ Serena successfully integrated with ADHD Engine")
        logger.info("✅ Feature flags working correctly")
        logger.info("✅ Backward compatibility maintained")
        logger.info("✅ Dynamic accommodations operational")
        logger.info("\n🎯 Ready for rollout!")

    except AssertionError as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
