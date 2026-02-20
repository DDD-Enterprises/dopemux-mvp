"""
Tests for ActivityTracker with ConPort integration.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from ..activity_tracker import ActivityTracker


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


class TestDailyStats:
    """Test daily statistics retrieval from ConPort."""

    @pytest.mark.asyncio
    async def test_get_daily_stats_with_mcp_client(self, mock_redis):
        """Should retrieve daily stats from MCP client when available."""
        mock_mcp = AsyncMock()
        mock_mcp.get_progress = AsyncMock(return_value=[
            {"id": 1, "status": "DONE", "description": "Task 1"},
            {"id": 2, "status": "DONE", "description": "Task 2"},
            {"id": 3, "status": "IN_PROGRESS", "description": "Task 3"},
            {"id": 4, "status": "TODO", "description": "Task 4"},
        ])

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db",
            conport_mcp_client=mock_mcp
        )

        result = await tracker.get_daily_stats("user1")

        assert result["completed"] == 2, "Should count 2 DONE tasks"
        assert result["total"] == 4, "Should count 4 total tasks"
        mock_mcp.get_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_stats_fallback_to_sqlite(self, mock_redis, mock_conport_client):
        """Should fallback to SQLite when MCP client is not available."""
        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db",
            conport_mcp_client=None
        )
        tracker.conport = mock_conport_client

        result = await tracker.get_daily_stats("user1")

        # Mock has 1 DONE out of 3 total (from conftest.py)
        assert result["completed"] == 1, "Should count 1 DONE task from SQLite"
        assert result["total"] == 3, "Should count 3 total tasks from SQLite"
        mock_conport_client.get_progress_entries.assert_called_once_with(
            limit=100,
            hours_ago=24
        )

    @pytest.mark.asyncio
    async def test_get_daily_stats_various_statuses(self, mock_redis):
        """Should correctly filter by DONE status among various status values."""
        mock_mcp = AsyncMock()
        mock_mcp.get_progress = AsyncMock(return_value=[
            {"id": 1, "status": "DONE", "description": "Task 1"},
            {"id": 2, "status": "COMPLETED", "description": "Task 2"},  # Not DONE
            {"id": 3, "status": "DONE", "description": "Task 3"},
            {"id": 4, "status": "IN_PROGRESS", "description": "Task 4"},
            {"id": 5, "status": "FAILED", "description": "Task 5"},
            {"id": 6, "status": "DONE", "description": "Task 6"},
        ])

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db",
            conport_mcp_client=mock_mcp
        )

        result = await tracker.get_daily_stats("user1")

        assert result["completed"] == 3, "Should only count tasks with status='DONE'"
        assert result["total"] == 6, "Should count all tasks"

    @pytest.mark.asyncio
    async def test_get_daily_stats_empty_data(self, mock_redis):
        """Should handle empty progress entries gracefully."""
        mock_mcp = AsyncMock()
        mock_mcp.get_progress = AsyncMock(return_value=[])

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db",
            conport_mcp_client=mock_mcp
        )

        result = await tracker.get_daily_stats("user1")

        assert result["completed"] == 0, "Should return 0 for empty data"
        assert result["total"] == 0, "Should return 0 for empty data"

    @pytest.mark.asyncio
    async def test_get_daily_stats_none_data(self, mock_redis):
        """Should handle None progress entries gracefully."""
        mock_mcp = AsyncMock()
        mock_mcp.get_progress = AsyncMock(return_value=None)

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db",
            conport_mcp_client=mock_mcp
        )

        result = await tracker.get_daily_stats("user1")

        assert result["completed"] == 0, "Should return 0 for None data"
        assert result["total"] == 0, "Should return 0 for None data"

    @pytest.mark.asyncio
    async def test_get_daily_stats_error_handling(self, mock_redis):
        """Should return default values when both data sources fail."""
        mock_mcp = AsyncMock()
        mock_mcp.get_progress = AsyncMock(side_effect=Exception("Connection failed"))

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db",
            conport_mcp_client=mock_mcp
        )

        result = await tracker.get_daily_stats("user1")

        assert result["completed"] == 0, "Should return 0 on error"
        assert result["total"] == 0, "Should return 0 on error"

    @pytest.mark.asyncio
    async def test_get_daily_stats_sqlite_error_handling(self, mock_redis, mock_conport_client):
        """Should return default values when SQLite fallback fails."""
        mock_conport_client.get_progress_entries = MagicMock(
            side_effect=Exception("SQLite error")
        )

        tracker = ActivityTracker(
            redis_client=mock_redis,
            conport_db_path="/fake/path.db",
            conport_mcp_client=None
        )
        tracker.conport = mock_conport_client

        result = await tracker.get_daily_stats("user1")

        assert result["completed"] == 0, "Should return 0 on SQLite error"
        assert result["total"] == 0, "Should return 0 on SQLite error"
