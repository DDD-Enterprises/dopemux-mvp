"""
Unit tests for SessionTracker logic (Phase 2 hardening).

Tests cover:
- Idle detection edge cases
- Activity resets
- Pulse emission scheduling
- Reflection window boundaries
- Duplicate prevention behavior
- Environment variable configuration overrides
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

# Import SessionTracker from eventbus_consumer
from eventbus_consumer import SessionTracker, HIGH_SIGNAL_EVENTS, HEARTBEAT_EVENTS


pytestmark = pytest.mark.phase2  # Mark all tests in this module as phase2


# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def test_context():
    """Test context tuple (workspace_id, instance_id, session_id)."""
    return ("ws_test", "inst_test", "session_test")


# ═══════════════════════════════════════════════════════════════════════════════
# Test 1: Idle Detection Marks Session Idle After Threshold
# ═══════════════════════════════════════════════════════════════════════════════


def test_idle_detection_marks_session_idle_after_threshold(test_context):
    """Test that session is marked idle after IDLE_MINUTES threshold."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Record activity
    tracker.update_activity(workspace_id, instance_id, session_id)
    
    # Initially not idle
    assert not tracker.is_idle(workspace_id, instance_id, session_id)
    
    # Advance time past idle threshold
    idle_threshold_seconds = int(os.getenv("DOPE_MEMORY_IDLE_MINUTES", "20")) * 60
    current_time = base_time + timedelta(seconds=idle_threshold_seconds + 60)
    
    # Now should be idle
    assert tracker.is_idle(workspace_id, instance_id, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 2: Activity Resets Idle Timer for High-Signal Events
# ═══════════════════════════════════════════════════════════════════════════════


def test_activity_resets_idle_timer_for_high_signal_events(test_context):
    """Test that new activity resets the idle timer."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Initial activity
    tracker.update_activity(workspace_id, instance_id, session_id)
    first_activity_time = tracker._sessions[tracker._session_key(*test_context)]["last_activity_at"]
    
    # Advance time and update activity again
    current_time = base_time + timedelta(seconds=10)
    tracker.update_activity(workspace_id, instance_id, session_id)
    second_activity_time = tracker._sessions[tracker._session_key(*test_context)]["last_activity_at"]
    
    # Second activity time should be later than first
    assert second_activity_time > first_activity_time


# ═══════════════════════════════════════════════════════════════════════════════
# Test 3: should_emit_pulse Respects Interval and Jitter Bounds
# ═══════════════════════════════════════════════════════════════════════════════


def test_should_emit_pulse_respects_interval_and_jitter_bounds(test_context):
    """Test pulse emission respects interval timing."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Initialize session
    tracker.update_activity(workspace_id, instance_id, session_id)
    
    # Mark initial pulse
    tracker.mark_pulse(workspace_id, instance_id, session_id)
    
    # Verify last_pulse_at is set
    key = tracker._session_key(*test_context)
    assert tracker._sessions[key]["last_pulse_at"] is not None
    assert tracker._sessions[key]["last_pulse_at"] == base_time


# ═══════════════════════════════════════════════════════════════════════════════
# Test 4: should_generate_reflection Respects Min Window
# ═══════════════════════════════════════════════════════════════════════════════


def test_should_generate_reflection_respects_min_window(test_context):
    """Test that reflections respect minimum window duration."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Initialize session
    tracker.update_activity(workspace_id, instance_id, session_id)
    
    # Mark first reflection
    tracker.mark_reflection(workspace_id, instance_id, session_id)
    
    # Immediately after, should not generate another reflection
    assert not tracker.should_generate_reflection(workspace_id, instance_id, session_id)
    
    # Advance time past min window + idle threshold
    min_window_minutes = int(os.getenv("DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES", "30"))
    idle_threshold = int(os.getenv("DOPE_MEMORY_IDLE_MINUTES", "20")) * 60
    
    # Advance past both min window and idle threshold
    current_time = base_time + timedelta(minutes=min_window_minutes + 1, seconds=idle_threshold)
    
    # Should generate reflection now (min window passed AND idle)
    assert tracker.should_generate_reflection(workspace_id, instance_id, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 5: should_generate_reflection Respects Max Window
# ═══════════════════════════════════════════════════════════════════════════════


def test_should_generate_reflection_respects_max_window(test_context):
    """Test that reflections are triggered after max window duration."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Initialize session
    tracker.update_activity(workspace_id, instance_id, session_id)
    
    # Mark first reflection
    tracker.mark_reflection(workspace_id, instance_id, session_id)
    
    # Fast-forward past max window
    max_window_hours = int(os.getenv("DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS", "2"))
    current_time = base_time + timedelta(hours=max_window_hours + 1)
    
    # Should generate reflection (max window exceeded, even if not idle)
    assert tracker.should_generate_reflection(workspace_id, instance_id, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 6: Reflection Duplicate Prevention Cooldown
# ═══════════════════════════════════════════════════════════════════════════════


def test_reflection_duplicate_prevention_cooldown(test_context):
    """Test that reflection cooldown prevents duplicates."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Initialize session
    tracker.update_activity(workspace_id, instance_id, session_id)
    
    # Mark first reflection
    tracker.mark_reflection(workspace_id, instance_id, session_id)
    
    # Immediately after, should not allow another reflection
    assert not tracker.should_generate_reflection(workspace_id, instance_id, session_id)
    
    # Just before min window expires
    min_window_minutes = int(os.getenv("DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES", "30"))
    current_time = base_time + timedelta(minutes=min_window_minutes - 1)
    
    # Should still not allow reflection (within cooldown)
    assert not tracker.should_generate_reflection(workspace_id, instance_id, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 7: Explicit Session Ended is Authoritative
# ═══════════════════════════════════════════════════════════════════════════════


def test_explicit_session_ended_is_authoritative(test_context):
    """Test that explicit session.ended event is authoritative."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Initialize session
    tracker.update_activity(workspace_id, instance_id, session_id)
    
    # Mark session as ended
    tracker.mark_ended(workspace_id, instance_id, session_id)
    
    # Session should be considered idle (ended)
    assert tracker.is_idle(workspace_id, instance_id, session_id)
    
    # Should generate reflection on explicit end
    assert tracker.should_generate_reflection(workspace_id, instance_id, session_id)
    
    # Even with new activity, session remains ended
    current_time = base_time + timedelta(minutes=5)
    tracker.update_activity(workspace_id, instance_id, session_id, is_heartbeat=False)
    assert tracker.is_idle(workspace_id, instance_id, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 8: Environment Variable Override - Idle Minutes
# ═══════════════════════════════════════════════════════════════════════════════


def test_env_var_override_idle_minutes(test_context, monkeypatch):
    """Test that DOPE_MEMORY_IDLE_MINUTES env var overrides default."""
    workspace_id, instance_id, session_id = test_context
    
    # Set custom idle threshold
    monkeypatch.setenv("DOPE_MEMORY_IDLE_MINUTES", "10")
    
    # Reload module to pick up new env var
    import importlib
    import eventbus_consumer
    importlib.reload(eventbus_consumer)
    from eventbus_consumer import SessionTracker, DOPE_MEMORY_IDLE_MINUTES
    
    # Verify env var was read
    assert DOPE_MEMORY_IDLE_MINUTES == 10
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    tracker.update_activity(workspace_id, instance_id, session_id)
    
    # Not idle initially
    assert not tracker.is_idle(workspace_id, instance_id, session_id)
    
    # Advance 11 minutes (past custom 10-minute threshold)
    current_time = base_time + timedelta(minutes=11)
    
    # Should be idle with custom threshold
    assert tracker.is_idle(workspace_id, instance_id, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 9: Environment Variable Override - Reflection Window
# ═══════════════════════════════════════════════════════════════════════════════


def test_env_var_override_reflection_window(test_context, monkeypatch):
    """Test that reflection window env vars can be overridden."""
    workspace_id, instance_id, session_id = test_context
    
    # Set custom reflection windows
    monkeypatch.setenv("DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES", "15")
    monkeypatch.setenv("DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS", "1")
    
    # Reload module
    import importlib
    import eventbus_consumer
    importlib.reload(eventbus_consumer)
    from eventbus_consumer import (
        SessionTracker,
        DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES,
        DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS
    )
    
    # Verify env vars were read
    assert DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES == 15
    assert DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS == 1
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    tracker.update_activity(workspace_id, instance_id, session_id)
    tracker.mark_reflection(workspace_id, instance_id, session_id)
    
    # Immediately after, should not generate reflection (min window)
    assert not tracker.should_generate_reflection(workspace_id, instance_id, session_id)
    
    # After 16 minutes and past idle threshold, should allow
    current_time = base_time + timedelta(minutes=16, seconds=15*60)  # 16 min + idle threshold
    assert tracker.should_generate_reflection(workspace_id, instance_id, session_id)

# ═══════════════════════════════════════════════════════════════════════════════
# Test 10: Heartbeat Prevents Idle False Positive
# ═══════════════════════════════════════════════════════════════════════════════


def test_heartbeat_prevents_idle_false_positive(test_context):
    """Test that heartbeat events reset idle timer without triggering reflection."""
    workspace_id, instance_id, session_id = test_context
    
    # Mock clock
    base_time = datetime.now(timezone.utc)
    current_time = base_time
    
    def mock_clock():
        return current_time
    
    tracker = SessionTracker(clock=mock_clock)
    
    # Initial high-signal activity
    tracker.update_activity(workspace_id, instance_id, session_id, is_heartbeat=False)
    
    # Advance time to just before idle threshold
    idle_threshold_seconds = int(os.getenv("DOPE_MEMORY_IDLE_MINUTES", "20")) * 60
    current_time = base_time + timedelta(seconds=idle_threshold_seconds - 60)
    
    # Not idle yet
    assert not tracker.is_idle(workspace_id, instance_id, session_id)
    
    # Send heartbeat event (e.g., message.sent)
    current_time = base_time + timedelta(seconds=idle_threshold_seconds - 30)
    tracker.update_activity(workspace_id, instance_id, session_id, is_heartbeat=True)
    
    # Advance past original idle threshold (but not past heartbeat's threshold)
    current_time = base_time + timedelta(seconds=idle_threshold_seconds + 120)
    
    # Should NOT be idle because heartbeat reset the timer
    assert not tracker.is_idle(workspace_id, instance_id, session_id)
    
    # Should NOT generate reflection (heartbeat doesn't trigger reflection)
    assert not tracker.should_generate_reflection(workspace_id, instance_id, session_id)
    
    # Verify that is_heartbeat_only flag was set
    key = tracker._session_key(workspace_id, instance_id, session_id)
    assert tracker._sessions[key]["is_heartbeat_only"] is True
    
    # Now send a high-signal event
    tracker.update_activity(workspace_id, instance_id, session_id, is_heartbeat=False)
    
    # is_heartbeat_only should now be False
    assert tracker._sessions[key]["is_heartbeat_only"] is False
