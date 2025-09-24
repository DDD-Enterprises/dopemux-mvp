"""
Tests for the attention monitor module.
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from dopemux.adhd.attention_monitor import (
    AttentionMetrics,
    AttentionState,
)


class TestAttentionMetrics:
    """Test AttentionMetrics dataclass."""

    def test_creation(self):
        """Test creating AttentionMetrics."""
        now = datetime.now()
        metrics = AttentionMetrics(
            timestamp=now,
            keystroke_rate=30.0,
            error_rate=2.0,
            context_switches=1,
            pause_duration=5.0,
            focus_score=0.8,
            attention_state=AttentionState.FOCUSED,
        )

        assert metrics.timestamp == now
        assert metrics.keystroke_rate == 30.0
        assert metrics.error_rate == 2.0
        assert metrics.context_switches == 1
        assert metrics.pause_duration == 5.0
        assert metrics.focus_score == 0.8
        assert metrics.attention_state == AttentionState.FOCUSED


class TestAttentionState:
    """Test AttentionState enum."""

    def test_states(self):
        """Test attention state constants."""
        assert AttentionState.FOCUSED == "focused"
        assert AttentionState.NORMAL == "normal"
        assert AttentionState.SCATTERED == "scattered"
        assert AttentionState.HYPERFOCUS == "hyperfocus"
        assert AttentionState.DISTRACTED == "distracted"


class TestAttentionMonitor:
    """Test AttentionMonitor class."""

    def test_initialization(self, attention_monitor, temp_project_dir):
        """Test AttentionMonitor initialization."""
        assert attention_monitor.project_path == temp_project_dir
        assert attention_monitor.data_dir == temp_project_dir / ".dopemux" / "attention"
        assert attention_monitor.data_dir.exists()

        # Check default configuration
        assert attention_monitor.sample_interval == 5
        assert attention_monitor.keystroke_threshold == 2.0
        assert attention_monitor.context_switch_threshold == 3
        assert attention_monitor.focus_threshold == 0.7
        assert attention_monitor.hyperfocus_duration == 45

        # Check initial state
        assert attention_monitor._monitoring is False
        assert attention_monitor._current_state == AttentionState.NORMAL
        assert len(attention_monitor._metrics_history) == 0

    def test_start_stop_monitoring(self, attention_monitor):
        """Test starting and stopping monitoring."""
        # Start monitoring
        attention_monitor.start_monitoring()
        assert attention_monitor._monitoring is True
        assert attention_monitor._monitor_thread is not None
        assert attention_monitor._monitor_thread.is_alive()

        # Stop monitoring
        attention_monitor.stop_monitoring()
        assert attention_monitor._monitoring is False

    def test_get_current_metrics_no_data(self, attention_monitor):
        """Test getting current metrics when no data available."""
        metrics = attention_monitor.get_current_metrics()

        assert metrics["attention_state"] == AttentionState.NORMAL
        assert metrics["focus_score"] == 0.5
        assert metrics["session_duration"] == 0
        assert metrics["monitoring_active"] is False

    def test_get_current_metrics_with_data(self, attention_monitor):
        """Test getting current metrics with data."""
        # Add some sample metrics
        now = datetime.now()
        sample_metrics = AttentionMetrics(
            timestamp=now,
            keystroke_rate=25.0,
            error_rate=1.0,
            context_switches=2,
            pause_duration=10.0,
            focus_score=0.75,
            attention_state=AttentionState.FOCUSED,
        )

        attention_monitor._metrics_history.append(sample_metrics)

        metrics = attention_monitor.get_current_metrics()

        assert metrics["attention_state"] == AttentionState.FOCUSED
        assert metrics["focus_score"] == 0.75
        assert metrics["keystroke_rate"] == 25.0
        assert metrics["error_rate"] == 1.0

    def test_simulate_activity_keystroke(self, attention_monitor):
        """Test simulating keystroke activity."""
        initial_count = len(attention_monitor._keystroke_buffer)

        attention_monitor.simulate_activity("keystroke")

        assert len(attention_monitor._keystroke_buffer) == initial_count + 1

    def test_simulate_activity_error(self, attention_monitor):
        """Test simulating error activity."""
        initial_count = len(attention_monitor._error_buffer)

        attention_monitor.simulate_activity("error")

        assert len(attention_monitor._error_buffer) == initial_count + 1

    def test_simulate_activity_file_switch(self, attention_monitor):
        """Test simulating file switch activity."""
        initial_count = len(attention_monitor._context_switch_buffer)

        attention_monitor.simulate_activity("file_switch", file="test.py")

        assert len(attention_monitor._context_switch_buffer) == initial_count + 1
        assert attention_monitor._current_file == "test.py"

    def test_calculate_keystroke_rate(self, attention_monitor):
        """Test keystroke rate calculation."""
        now = datetime.now()

        # Add keystrokes in last minute
        for i in range(30):
            attention_monitor._keystroke_buffer.append(now - timedelta(seconds=i))

        rate = attention_monitor._calculate_keystroke_rate()
        assert rate == 30  # 30 keystrokes in last minute

    def test_calculate_error_rate(self, attention_monitor):
        """Test error rate calculation."""
        now = datetime.now()

        # Add errors in last minute
        for i in range(5):
            attention_monitor._error_buffer.append(now - timedelta(seconds=i * 10))

        rate = attention_monitor._calculate_error_rate()
        assert rate == 5  # 5 errors in last minute

    def test_calculate_context_switches(self, attention_monitor):
        """Test context switch calculation."""
        now = datetime.now()

        # Add context switches in current sample period
        for i in range(3):
            attention_monitor._context_switch_buffer.append(now - timedelta(seconds=i))

        switches = attention_monitor._calculate_context_switches()
        assert switches == 3

    def test_calculate_focus_score(self, attention_monitor):
        """Test focus score calculation."""
        # Test perfect focus conditions
        score = attention_monitor._calculate_focus_score(
            keystroke_rate=60,  # High activity
            error_rate=0,  # No errors
            context_switches=0,  # No switches
            pause_duration=0,  # No pause
        )
        assert score == 1.0

        # Test poor focus conditions
        score = attention_monitor._calculate_focus_score(
            keystroke_rate=0,  # No activity
            error_rate=10,  # Many errors
            context_switches=5,  # Many switches
            pause_duration=300,  # Long pause
        )
        assert score == 0.0  # Should be clamped to 0

    def test_classify_attention_state_distracted(self, attention_monitor):
        """Test classifying distracted state."""
        state = attention_monitor._classify_attention_state(
            keystroke_rate=0,
            error_rate=0,
            context_switches=0,
            pause_duration=700,  # > 10 minutes
            focus_score=0.5,
        )
        assert state == AttentionState.DISTRACTED

    def test_classify_attention_state_scattered(self, attention_monitor):
        """Test classifying scattered state."""
        state = attention_monitor._classify_attention_state(
            keystroke_rate=20,
            error_rate=2,
            context_switches=5,  # > threshold
            pause_duration=0,
            focus_score=0.5,
        )
        assert state == AttentionState.SCATTERED

    def test_classify_attention_state_focused(self, attention_monitor):
        """Test classifying focused state."""
        state = attention_monitor._classify_attention_state(
            keystroke_rate=30,
            error_rate=1,  # < 2
            context_switches=1,
            pause_duration=5,
            focus_score=0.8,  # > threshold
        )
        assert state == AttentionState.FOCUSED

    def test_classify_attention_state_hyperfocus(self, attention_monitor):
        """Test classifying hyperfocus state."""
        # Set up sustained high activity
        attention_monitor._state_duration = 50 * 60  # 50 minutes

        state = attention_monitor._classify_attention_state(
            keystroke_rate=40,  # High activity
            error_rate=1,
            context_switches=0,
            pause_duration=0,
            focus_score=0.9,  # Very high focus
        )
        assert state == AttentionState.HYPERFOCUS

    def test_update_state_tracking_no_change(self, attention_monitor):
        """Test state tracking when state doesn't change."""
        initial_duration = attention_monitor._state_duration
        initial_state = attention_monitor._current_state

        attention_monitor._update_state_tracking(AttentionState.NORMAL, datetime.now())

        assert attention_monitor._current_state == initial_state
        assert (
            attention_monitor._state_duration
            == initial_duration + attention_monitor.sample_interval
        )

    def test_update_state_tracking_state_change(self, attention_monitor):
        """Test state tracking when state changes."""
        attention_monitor._update_state_tracking(AttentionState.FOCUSED, datetime.now())

        assert attention_monitor._current_state == AttentionState.FOCUSED
        assert attention_monitor._state_duration == 0
        assert attention_monitor._focus_session_start is not None

    def test_collect_metrics(self, attention_monitor):
        """Test metrics collection."""
        # Add some activity
        attention_monitor.simulate_activity("keystroke")
        attention_monitor.simulate_activity("keystroke")

        # Collect metrics
        attention_monitor._collect_metrics()

        assert len(attention_monitor._metrics_history) == 1

        metrics = attention_monitor._metrics_history[0]
        assert isinstance(metrics, AttentionMetrics)
        assert metrics.keystroke_rate >= 0
        assert metrics.focus_score >= 0

    def test_add_callback(self, attention_monitor):
        """Test adding callbacks for state changes."""
        callback_called = False
        received_metrics = None

        def test_callback(metrics):
            nonlocal callback_called, received_metrics
            callback_called = True
            received_metrics = metrics

        attention_monitor.add_callback(test_callback)

        # Trigger metrics collection
        attention_monitor._collect_metrics()

        assert callback_called is True
        assert received_metrics is not None
        assert isinstance(received_metrics, AttentionMetrics)

    def test_get_session_summary_no_data(self, attention_monitor):
        """Test session summary with no data."""
        summary = attention_monitor.get_session_summary()
        assert summary == {}

    def test_get_session_summary_with_data(self, attention_monitor):
        """Test session summary with data."""
        # Add sample metrics
        now = datetime.now()
        for i in range(10):
            metrics = AttentionMetrics(
                timestamp=now - timedelta(minutes=i),
                keystroke_rate=20 + i,
                error_rate=1,
                context_switches=0,
                pause_duration=0,
                focus_score=0.7 + (i * 0.01),
                attention_state=(
                    AttentionState.FOCUSED if i % 2 == 0 else AttentionState.NORMAL
                ),
            )
            attention_monitor._metrics_history.append(metrics)

        summary = attention_monitor.get_session_summary()

        assert "session_duration_minutes" in summary
        assert "average_focus_score" in summary
        assert "total_context_switches" in summary
        assert "state_distribution" in summary
        assert "productivity_score" in summary
        assert "recommendations" in summary

        # Check state distribution
        state_dist = summary["state_distribution"]
        assert AttentionState.FOCUSED in state_dist
        assert AttentionState.NORMAL in state_dist

    def test_calculate_productivity_score(self, attention_monitor):
        """Test productivity score calculation."""
        # Add high-quality metrics
        now = datetime.now()
        for i in range(5):
            metrics = AttentionMetrics(
                timestamp=now - timedelta(minutes=i),
                keystroke_rate=30,
                error_rate=1,  # Low error rate
                context_switches=0,
                pause_duration=0,
                focus_score=0.8,  # High focus
                attention_state=AttentionState.FOCUSED,
            )
            attention_monitor._metrics_history.append(metrics)

        score = attention_monitor._calculate_productivity_score()
        assert score > 0.5  # Should be high for good metrics

    def test_generate_recommendations_scattered(self, attention_monitor):
        """Test recommendations for scattered attention."""
        # Set up scattered state
        attention_monitor._current_state = AttentionState.SCATTERED

        with patch.object(attention_monitor, "get_current_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "attention_state": AttentionState.SCATTERED,
                "focus_score": 0.6,
                "session_duration": 30,
            }

            recommendations = attention_monitor._generate_recommendations()

            assert len(recommendations) > 0
            assert any("break" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_hyperfocus(self, attention_monitor):
        """Test recommendations for hyperfocus state."""
        with patch.object(attention_monitor, "get_current_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "attention_state": AttentionState.HYPERFOCUS,
                "focus_score": 0.9,
                "session_duration": 30,
            }

            recommendations = attention_monitor._generate_recommendations()

            assert len(recommendations) > 0
            assert any("break" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_low_focus(self, attention_monitor):
        """Test recommendations for low focus."""
        with patch.object(attention_monitor, "get_current_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "attention_state": AttentionState.NORMAL,
                "focus_score": 0.3,  # Low focus
                "session_duration": 30,
            }

            recommendations = attention_monitor._generate_recommendations()

            assert len(recommendations) > 0
            assert any("pomodoro" in rec.lower() for rec in recommendations)

    def test_save_session_metrics(self, attention_monitor):
        """Test saving session metrics to file."""
        # Add some metrics
        now = datetime.now()
        metrics = AttentionMetrics(
            timestamp=now,
            keystroke_rate=25,
            error_rate=1,
            context_switches=2,
            pause_duration=0,
            focus_score=0.7,
            attention_state=AttentionState.FOCUSED,
        )
        attention_monitor._metrics_history.append(metrics)

        attention_monitor._save_session_metrics()

        # Check that file was created
        session_files = list(attention_monitor.data_dir.glob("session_*.json"))
        assert len(session_files) > 0

        # Verify content
        with open(session_files[0]) as f:
            data = json.load(f)
            assert "session_start" in data
            assert "session_end" in data
            assert "summary" in data

    def test_log_focus_session(self, attention_monitor):
        """Test logging focus sessions."""
        # Mock session quality calculation
        with patch.object(
            attention_monitor, "_calculate_session_quality", return_value=0.8
        ):
            attention_monitor._log_focus_session(30.0)  # 30 minute session

        log_file = attention_monitor.data_dir / "focus_sessions.jsonl"
        assert log_file.exists()

        # Verify content
        with open(log_file) as f:
            lines = f.readlines()
            assert len(lines) > 0

            last_session = json.loads(lines[-1])
            assert last_session["duration_minutes"] == 30.0
            assert last_session["quality_score"] == 0.8

    def test_log_focus_session_too_short(self, attention_monitor):
        """Test that short focus sessions are not logged."""
        log_file = attention_monitor.data_dir / "focus_sessions.jsonl"

        # Remove existing log file if it exists
        if log_file.exists():
            log_file.unlink()

        attention_monitor._log_focus_session(3.0)  # 3 minute session (too short)

        # Should not create log file for short sessions
        assert not log_file.exists()

    def test_calculate_session_quality(self, attention_monitor):
        """Test session quality calculation."""
        # Add metrics with varying focus scores
        now = datetime.now()
        focus_scores = [0.8, 0.7, 0.9, 0.6, 0.8]

        for score in focus_scores:
            metrics = AttentionMetrics(
                timestamp=now,
                keystroke_rate=25,
                error_rate=1,
                context_switches=1,
                pause_duration=0,
                focus_score=score,
                attention_state=AttentionState.FOCUSED,
            )
            attention_monitor._metrics_history.append(metrics)

        quality = attention_monitor._calculate_session_quality()
        expected_avg = sum(focus_scores) / len(focus_scores)
        assert abs(quality - expected_avg) < 0.01

    def test_monitoring_thread_integration(self, attention_monitor):
        """Test monitoring thread runs without errors."""
        # Reduce sample interval for faster test
        attention_monitor.sample_interval = 0.1

        attention_monitor.start_monitoring()
        time.sleep(0.3)  # Let it run for a bit
        attention_monitor.stop_monitoring()

        # Should have collected some metrics
        assert len(attention_monitor._metrics_history) > 0

    def test_error_handling_in_callback(self, attention_monitor):
        """Test error handling when callback fails."""

        def failing_callback(metrics):
            raise ValueError("Test error")

        def working_callback(metrics):
            working_callback.called = True

        working_callback.called = False

        attention_monitor.add_callback(failing_callback)
        attention_monitor.add_callback(working_callback)

        # Should not crash when callback fails
        attention_monitor._collect_metrics()

        # Working callback should still be called
        assert working_callback.called is True
