"""
Unit tests for Load Alert Manager (Week 3).

Tests alert generation and management:
- Rate limiting (max 1/hour)
- Snooze functionality
- Priority classification
- User settings customization
"""

import pytest
from datetime import datetime, timedelta

from .cognitive_load_balancer import CognitiveLoad, LoadStatus, LoadFactors, UserLoadProfile
from .load_alert_manager import (
    LoadAlertManager,
    AlertSettings,
    AlertPriority,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def alert_manager():
    """Create LoadAlertManager instance."""
    return LoadAlertManager()


@pytest.fixture
def sample_load_calculation():
    """Create sample CognitiveLoad for testing."""
    return CognitiveLoad(
        load_value=0.9,
        load_level=LoadStatus.CRITICAL,
        factors=LoadFactors(
            task_complexity=0.9,
            active_decisions=10,
            context_switches=5,
            minutes_since_break=90,
            active_interruptions=5
        ),
        factor_contributions={},
        calculated_at=datetime.now(),
        user_profile=UserLoadProfile(user_id="test-user")
    )


# ============================================================================
# Alert Generation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_generates_alert_when_threshold_exceeded(alert_manager, sample_load_calculation):
    """Test that alert is generated when load exceeds threshold."""
    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )

    assert alert is not None
    assert alert.user_id == "test-user"
    assert alert.load_value == 0.9
    assert alert.load_level == LoadStatus.CRITICAL


@pytest.mark.asyncio
async def test_no_alert_when_below_threshold(alert_manager):
    """Test that no alert is generated when load is below threshold."""
    low_load = CognitiveLoad(
        load_value=0.4,  # Below all thresholds
        load_level=LoadStatus.OPTIMAL,
        factors=LoadFactors(0.4, 2, 1, 20, 0),
        factor_contributions={},
        calculated_at=datetime.now(),
        user_profile=UserLoadProfile(user_id="test-user")
    )

    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=low_load
    )

    assert alert is None


# ============================================================================
# Rate Limiting Tests
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limiting_prevents_multiple_alerts(alert_manager, sample_load_calculation):
    """Test that rate limiting prevents sending multiple alerts within time window."""
    # First alert should be sent
    alert1 = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )
    assert alert1 is not None

    # Second alert immediately after should be suppressed
    alert2 = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )
    assert alert2 is None


@pytest.mark.asyncio
async def test_different_users_independent_rate_limiting(alert_manager, sample_load_calculation):
    """Test that rate limiting is per-user."""
    # Alert for user 1
    alert1 = await alert_manager.check_and_generate_alert(
        user_id="user-1",
        load_calculation=sample_load_calculation
    )
    assert alert1 is not None

    # Alert for user 2 should still be sent
    alert2 = await alert_manager.check_and_generate_alert(
        user_id="user-2",
        load_calculation=sample_load_calculation
    )
    assert alert2 is not None


# ============================================================================
# Snooze Functionality Tests
# ============================================================================

@pytest.mark.asyncio
async def test_snooze_suppresses_alerts(alert_manager, sample_load_calculation):
    """Test that snoozing prevents alerts from being sent."""
    # Snooze for 30 minutes
    snooze_until = alert_manager.snooze_alerts("test-user", duration_minutes=30)

    assert snooze_until > datetime.now()

    # Alert should be suppressed
    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )

    assert alert is None


@pytest.mark.asyncio
async def test_unsnooze_resumes_alerts(alert_manager, sample_load_calculation):
    """Test that unsnoozing allows alerts to be sent again."""
    # Snooze
    alert_manager.snooze_alerts("test-user", duration_minutes=30)

    # Unsnooze
    alert_manager.unsnooze_alerts("test-user")

    # Alert should now be sent
    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )

    assert alert is not None


@pytest.mark.asyncio
async def test_snooze_duration_options(alert_manager):
    """Test different snooze duration options."""
    durations = [15, 30, 60]

    for duration in durations:
        snooze_until = alert_manager.snooze_alerts(
            f"user-{duration}",
            duration_minutes=duration
        )

        expected_until = datetime.now() + timedelta(minutes=duration)

        # Allow 1 second tolerance
        time_diff = abs((snooze_until - expected_until).total_seconds())
        assert time_diff < 1, f"Snooze duration {duration} not accurate"


# ============================================================================
# Priority Classification Tests
# ============================================================================

@pytest.mark.asyncio
async def test_critical_priority_classification(alert_manager):
    """Test that load >= 0.85 is classified as CRITICAL."""
    critical_load = CognitiveLoad(
        load_value=0.9,
        load_level=LoadStatus.CRITICAL,
        factors=LoadFactors(0.9, 10, 5, 90, 5),
        factor_contributions={},
        calculated_at=datetime.now(),
        user_profile=UserLoadProfile(user_id="test-user")
    )

    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=critical_load
    )

    assert alert is not None
    assert "critical" in alert.message.lower() or "🚨" in alert.message


@pytest.mark.asyncio
async def test_warning_priority_classification(alert_manager):
    """Test that load in warning range is classified appropriately."""
    warning_load = CognitiveLoad(
        load_value=0.75,
        load_level=LoadStatus.HIGH,
        factors=LoadFactors(0.7, 5, 3, 60, 2),
        factor_contributions={},
        calculated_at=datetime.now(),
        user_profile=UserLoadProfile(user_id="test-user")
    )

    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=warning_load
    )

    assert alert is not None
    assert "warning" in alert.message.lower() or "⚠️" in alert.message or "💡" in alert.message


# ============================================================================
# Custom Settings Tests
# ============================================================================

@pytest.mark.asyncio
async def test_custom_alert_threshold(alert_manager):
    """Test that custom alert threshold is respected."""
    # Set lower threshold (0.75 instead of default 0.85)
    alert_manager.update_settings(
        "test-user",
        critical_threshold=0.75
    )

    # Load of 0.77 should trigger with custom threshold
    moderate_load = CognitiveLoad(
        load_value=0.77,
        load_level=LoadStatus.HIGH,
        factors=LoadFactors(0.7, 5, 3, 50, 2),
        factor_contributions={},
        calculated_at=datetime.now(),
        user_profile=UserLoadProfile(user_id="test-user")
    )

    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=moderate_load
    )

    assert alert is not None


@pytest.mark.asyncio
async def test_custom_rate_limit(alert_manager, sample_load_calculation):
    """Test that custom rate limit is respected."""
    # Allow 2 alerts per hour instead of 1
    alert_manager.update_settings(
        "test-user",
        max_alerts_per_hour=2,
        min_minutes_between_alerts=30  # 30 minutes between
    )

    # First alert
    alert1 = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )
    assert alert1 is not None

    # Second alert immediately - should be suppressed (min 30 min between)
    alert2 = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )
    assert alert2 is None


@pytest.mark.asyncio
async def test_disable_alerts(alert_manager, sample_load_calculation):
    """Test that alerts can be completely disabled."""
    alert_manager.update_settings(
        "test-user",
        alerts_enabled=False
    )

    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )

    assert alert is None


# ============================================================================
# Alert Acknowledgment Tests
# ============================================================================

@pytest.mark.asyncio
async def test_alert_acknowledgment_tracking(alert_manager, sample_load_calculation):
    """Test that alert acknowledgment is tracked."""
    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )

    assert alert is not None

    # Acknowledge alert
    success = alert_manager.acknowledge_alert("test-user", alert.alert_id)
    assert success is True

    # Check history
    history = alert_manager.get_history("test-user")
    assert history.total_alerts_acknowledged == 1


# ============================================================================
# Alert Message Tests
# ============================================================================

@pytest.mark.asyncio
async def test_alert_contains_recommendations(alert_manager, sample_load_calculation):
    """Test that alerts contain actionable recommendations."""
    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )

    assert alert is not None
    assert len(alert.recommendation) > 0
    assert "break" in alert.recommendation.lower() or "task" in alert.recommendation.lower()


@pytest.mark.asyncio
async def test_alert_message_includes_load_value(alert_manager, sample_load_calculation):
    """Test that alert message includes current load value."""
    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=sample_load_calculation
    )

    assert alert is not None
    # Should contain percentage or decimal representation
    assert "0.9" in alert.message or "90" in alert.message


# ============================================================================
# Statistics Tests
# ============================================================================

@pytest.mark.asyncio
async def test_statistics_tracking(alert_manager, sample_load_calculation):
    """Test that statistics are tracked correctly."""
    # Generate one alert
    await alert_manager.check_and_generate_alert(
        user_id="user-1",
        load_calculation=sample_load_calculation
    )

    # Try to generate second (will be suppressed)
    await alert_manager.check_and_generate_alert(
        user_id="user-1",
        load_calculation=sample_load_calculation
    )

    stats = alert_manager.get_statistics()

    assert stats["total_alerts_generated"] == 1
    assert stats["total_alerts_suppressed"] == 1
    assert stats["users_tracked"] == 1


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
