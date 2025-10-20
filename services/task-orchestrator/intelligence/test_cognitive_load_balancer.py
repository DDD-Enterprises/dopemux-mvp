"""
Unit tests for Cognitive Load Balancer (Week 3).

Tests real-time load calculation:
- Formula accuracy
- Factor normalization
- Caching behavior
- User profile management
"""

import pytest
from datetime import datetime, timedelta

from .cognitive_load_balancer import (
    CognitiveLoadBalancer,
    LoadFactors,
    LoadStatus,
    UserLoadProfile,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def balancer():
    """Create CognitiveLoadBalancer instance."""
    return CognitiveLoadBalancer()


@pytest.fixture
def default_factors():
    """Create default load factors."""
    return LoadFactors(
        task_complexity=0.5,
        active_decisions=5,
        context_switches=2,
        minutes_since_break=30,
        active_interruptions=1
    )


# ============================================================================
# Load Calculation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_basic_load_calculation(balancer, default_factors):
    """Test basic load calculation with default weights."""
    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=default_factors,
        use_cache=False
    )

    # Load should be calculated
    assert 0.0 <= calculation.load_value <= 1.0
    assert calculation.load_level in list(LoadStatus)
    assert calculation.factors == default_factors
    assert isinstance(calculation.factor_contributions, dict)


@pytest.mark.asyncio
async def test_formula_accuracy(balancer):
    """Test that formula calculates correctly with known values."""
    # Known values: all factors at 0.5 normalized
    factors = LoadFactors(
        task_complexity=0.5,    # Already normalized
        active_decisions=5,     # 5/10 = 0.5
        context_switches=2.5,   # 2.5/5 = 0.5 (will round)
        minutes_since_break=45, # 45/90 = 0.5
        active_interruptions=2.5  # 2.5/5 = 0.5 (will round)
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=factors,
        use_cache=False
    )

    # Expected: 0.4*0.5 + 0.2*0.5 + 0.2*0.5 + 0.1*0.5 + 0.1*0.5 = 0.5
    assert 0.45 <= calculation.load_value <= 0.55, \
        f"Expected ~0.5, got {calculation.load_value}"


@pytest.mark.asyncio
async def test_zero_load(balancer):
    """Test load calculation with all zero factors."""
    zero_factors = LoadFactors(
        task_complexity=0.0,
        active_decisions=0,
        context_switches=0,
        minutes_since_break=0,
        active_interruptions=0
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=zero_factors,
        use_cache=False
    )

    assert calculation.load_value == 0.0
    assert calculation.load_level == LoadStatus.LOW


@pytest.mark.asyncio
async def test_max_load(balancer):
    """Test load calculation with maximum factors."""
    max_factors = LoadFactors(
        task_complexity=1.0,
        active_decisions=20,  # > 10, will cap at 1.0
        context_switches=10,  # > 5, will cap at 1.0
        minutes_since_break=180,  # > 90, will cap at 1.0
        active_interruptions=10  # > 5, will cap at 1.0
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=max_factors,
        use_cache=False
    )

    assert calculation.load_value == 1.0
    assert calculation.load_level == LoadStatus.CRITICAL


# ============================================================================
# Load Classification Tests
# ============================================================================

@pytest.mark.asyncio
async def test_low_load_classification(balancer):
    """Test that low load values are classified correctly."""
    low_factors = LoadFactors(
        task_complexity=0.2,
        active_decisions=1,
        context_switches=0,
        minutes_since_break=10,
        active_interruptions=0
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=low_factors,
        use_cache=False
    )

    assert calculation.load_level == LoadStatus.LOW


@pytest.mark.asyncio
async def test_optimal_load_classification(balancer):
    """Test that optimal load values are classified correctly."""
    optimal_factors = LoadFactors(
        task_complexity=0.6,
        active_decisions=3,
        context_switches=2,
        minutes_since_break=30,
        active_interruptions=1
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=optimal_factors,
        use_cache=False
    )

    assert calculation.load_level == LoadStatus.OPTIMAL


@pytest.mark.asyncio
async def test_critical_load_classification(balancer):
    """Test that critical load values are classified correctly."""
    critical_factors = LoadFactors(
        task_complexity=0.9,
        active_decisions=10,
        context_switches=5,
        minutes_since_break=90,
        active_interruptions=5
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=critical_factors,
        use_cache=False
    )

    assert calculation.load_level == LoadStatus.CRITICAL


# ============================================================================
# Caching Tests
# ============================================================================

@pytest.mark.asyncio
async def test_caching_returns_same_result(balancer, default_factors):
    """Test that caching returns the same calculation within TTL."""
    # First calculation
    calc1 = await balancer.calculate_load(
        user_id="test-user",
        factors=default_factors,
        use_cache=True
    )

    # Second calculation (should use cache)
    calc2 = await balancer.calculate_load(
        user_id="test-user",
        factors=default_factors,
        use_cache=True
    )

    # Should return the exact same object from cache
    assert calc1.calculated_at == calc2.calculated_at


@pytest.mark.asyncio
async def test_cache_bypass(balancer, default_factors):
    """Test that use_cache=False forces recalculation."""
    # First calculation
    calc1 = await balancer.calculate_load(
        user_id="test-user",
        factors=default_factors,
        use_cache=True
    )

    # Wait a moment
    await asyncio.sleep(0.01)

    # Second calculation with cache disabled
    calc2 = await balancer.calculate_load(
        user_id="test-user",
        factors=default_factors,
        use_cache=False
    )

    # Should be different calculation times
    assert calc1.calculated_at != calc2.calculated_at


# ============================================================================
# User Profile Tests
# ============================================================================

@pytest.mark.asyncio
async def test_default_profile_creation(balancer, default_factors):
    """Test that default profile is created for new users."""
    calculation = await balancer.calculate_load(
        user_id="new-user",
        factors=default_factors,
        use_cache=False
    )

    profile = calculation.user_profile

    # Check default weights
    assert profile.weight_task_complexity == 0.4
    assert profile.weight_decision_count == 0.2
    assert profile.weight_context_switches == 0.2
    assert profile.weight_time_pressure == 0.1
    assert profile.weight_interruptions == 0.1

    # Check default thresholds
    assert profile.optimal_load_min == 0.4
    assert profile.optimal_load_max == 0.7
    assert profile.alert_threshold == 0.85


@pytest.mark.asyncio
async def test_custom_profile_weights(balancer, default_factors):
    """Test that custom weights are applied correctly."""
    # Update profile to emphasize task complexity
    balancer.update_user_profile(
        "test-user",
        weight_task_complexity=0.6,
        weight_decision_count=0.1,
        weight_context_switches=0.1,
        weight_time_pressure=0.1,
        weight_interruptions=0.1
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=default_factors,
        use_cache=False
    )

    # Load should be different with custom weights
    profile = calculation.user_profile
    assert profile.weight_task_complexity == 0.6


@pytest.mark.asyncio
async def test_profile_persistence(balancer):
    """Test that profile persists across calculations."""
    # Create custom profile
    balancer.update_user_profile(
        "test-user",
        alert_threshold=0.75  # Lower threshold
    )

    # Get profile
    profile = balancer.get_user_profile("test-user")
    assert profile.alert_threshold == 0.75

    # Should persist
    profile2 = balancer.get_user_profile("test-user")
    assert profile2.alert_threshold == 0.75


# ============================================================================
# Recommendation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_critical_load_recommendation(balancer):
    """Test that critical load provides appropriate recommendation."""
    critical_factors = LoadFactors(
        task_complexity=0.9,
        active_decisions=10,
        context_switches=5,
        minutes_since_break=90,
        active_interruptions=5
    )

    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=critical_factors,
        use_cache=False
    )

    recommendation = balancer.get_load_recommendation(calculation)

    assert "overload" in recommendation.lower() or "critical" in recommendation.lower()
    assert "break" in recommendation.lower()


@pytest.mark.asyncio
async def test_optimal_load_recommendation(balancer, default_factors):
    """Test that optimal load provides appropriate recommendation."""
    calculation = await balancer.calculate_load(
        user_id="test-user",
        factors=default_factors,
        use_cache=False
    )

    # Adjust factors to be in optimal range
    if calculation.load_level != LoadStatus.OPTIMAL:
        optimal_factors = LoadFactors(
            task_complexity=0.6,
            active_decisions=3,
            context_switches=2,
            minutes_since_break=30,
            active_interruptions=1
        )
        calculation = await balancer.calculate_load(
            user_id="test-user",
            factors=optimal_factors,
            use_cache=False
        )

    recommendation = balancer.get_load_recommendation(calculation)

    assert "optimal" in recommendation.lower() or "zone" in recommendation.lower()


# ============================================================================
# Statistics Tests
# ============================================================================

@pytest.mark.asyncio
async def test_statistics_tracking(balancer, default_factors):
    """Test that statistics are tracked correctly."""
    # Perform several calculations
    for i in range(3):
        await balancer.calculate_load(
            user_id=f"user-{i}",
            factors=default_factors,
            use_cache=False
        )

    stats = balancer.get_statistics()

    assert stats["calculation_count"] == 3
    assert stats["user_profiles"] == 3
    assert stats["cache_size"] == 3


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    import asyncio
    pytest.main([__file__, "-v"])
