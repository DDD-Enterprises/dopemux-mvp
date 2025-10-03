"""
Tests for ActivityTracker with ConPort integration.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from adhd_engine.activity_tracker import ActivityTracker


class TestActivityTrackerCaching:
    """Test caching mechanism in ActivityTracker."""

    @pytest.mark.asyncio
    async def test_cache_hit_avoids_query(self, mock_redis, mock_conport_client):
        """Cached data should avoid repeated ConPort queries."""
        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db"
        )
        tracker.conport = mock_conport_client

        # First call - should query
        result1 = await tracker.get_recent_activity("user1")
        call_count_1 = mock_conport_client.get_progress_entries.call_count

        # Second call within cache TTL - should use cache
        result2 = await tracker.get_recent_activity("user1")
        call_count_2 = mock_conport_client.get_progress_entries.call_count

        assert call_count_2 == call_count_1, "Should not query again within cache TTL"
        assert result1 == result2, "Cached result should match original"


class TestActivityMetricsCalculation:
    """Test activity metrics calculation from ConPort data."""

    @pytest.mark.asyncio
    async def test_completion_rate_calculation(self, mock_redis, mock_conport_client):
        """Completion rate should be calculated from real progress data."""
        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db"
        )
        tracker.conport = mock_conport_client

        result = await tracker.get_recent_activity("user1")

        # Mock has 1 DONE out of 3 total = 33.3%
        assert 0.3 <= result["completion_rate"] <= 0.4, f"Expected ~33% completion, got {result['completion_rate']}"

    @pytest.mark.asyncio
    async def test_context_switches_from_custom_data(self, mock_redis, mock_conport_client):
        """Context switches should come from ConPort custom_data."""
        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db"
        )
        tracker.conport = mock_conport_client

        result = await tracker.get_recent_activity("user1")

        assert result["context_switches"] == 3, "Should get context switches from mock data"

    @pytest.mark.asyncio
    async def test_fallback_on_no_data(self, mock_redis, mock_conport_client):
        """Should handle missing ConPort data gracefully."""
        mock_conport_client.get_progress_entries = MagicMock(return_value=[])
        mock_conport_client.get_custom_data = MagicMock(return_value=None)

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db"
        )
        tracker.conport = mock_conport_client

        result = await tracker.get_recent_activity("user1")

        # Should return defaults, not crash
        assert "completion_rate" in result
        assert 0.0 <= result["completion_rate"] <= 1.0


class TestAttentionIndicators:
    """Test attention indicator extraction."""

    @pytest.mark.asyncio
    async def test_indicators_from_activity_log(self, mock_redis, mock_conport_client):
        """Should extract attention indicators from ConPort activity log."""
        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db"
        )
        tracker.conport = mock_conport_client

        result = await tracker.get_attention_indicators("user1")

        assert result["context_switches_per_hour"] == 5
        assert result["abandoned_tasks"] == 1
        assert result["average_focus_duration"] == 22
        assert result["distraction_events"] == 3

    @pytest.mark.asyncio
    async def test_defaults_when_no_activity_log(self, mock_redis, mock_conport_client):
        """Should provide sensible defaults when activity log missing."""
        mock_conport_client.get_custom_data = MagicMock(return_value=None)

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db"
        )
        tracker.conport = mock_conport_client

        result = await tracker.get_attention_indicators("user1")

        # Should have all required fields with defaults
        assert "context_switches_per_hour" in result
        assert "abandoned_tasks" in result
        assert "average_focus_duration" in result
        assert "distraction_events" in result
