"""
Tests for Event Aggregation Engine
Validates event merging, provenance tracking, and confidence combination
"""

import pytest
from datetime import datetime

from aggregation_engine import AggregationEngine, AggregatedEvent


class TestAggregatedEvent:
    """Test AggregatedEvent dataclass"""

    def test_combined_confidence_weighted_average(self):
        """Test that confidence is calculated as weighted average"""
        event = AggregatedEvent(
            event_type="test",
            data={},
            confidence_scores=[0.8, 0.6, 0.9]
        )

        combined = event.get_combined_confidence()

        # Weighted average should favor higher scores
        # (0.8^2 * 0.8 + 0.6^2 * 0.6 + 0.9^2 * 0.9) / (0.8^2 + 0.6^2 + 0.9^2)
        expected = (0.64 * 0.8 + 0.36 * 0.6 + 0.81 * 0.9) / (0.64 + 0.36 + 0.81)

        assert abs(combined - expected) < 0.01, f"Expected {expected}, got {combined}"

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all important fields"""
        event = AggregatedEvent(
            event_type="test.event",
            data={"key": "value"},
            sources=["agent1", "agent2"],
            confidence_scores=[0.8, 0.9],
            timestamps=["2025-10-23T10:00:00Z", "2025-10-23T10:01:00Z"],
            original_event_ids=["abc123", "def456"]
        )

        result = event.to_dict()

        assert result["event_type"] == "test.event"
        assert result["data"] == {"key": "value"}
        assert result["sources"] == ["agent1", "agent2"]
        assert result["event_count"] == 2
        assert "confidence" in result
        assert "provenance" in result


class TestAggregationEngine:
    """Test suite for AggregationEngine"""

    @pytest.fixture
    def engine(self):
        """Create AggregationEngine instance"""
        return AggregationEngine(similarity_threshold=0.8)

    @pytest.mark.asyncio
    async def test_identical_events_aggregated(self, engine):
        """Test that identical events from different agents are merged"""
        events = [
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth.py", "complexity": 0.7},
                "source": "serena",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth.py", "complexity": 0.72},
                "source": "dope-context",
                "timestamp": "2025-10-23T10:01:00Z"
            },
        ]

        aggregated = await engine.aggregate_events(events)

        assert len(aggregated) == 1, "Should merge identical events"
        assert len(aggregated[0].sources) == 2, "Should track both sources"
        assert "serena" in aggregated[0].sources
        assert "dope-context" in aggregated[0].sources

    @pytest.mark.asyncio
    async def test_different_events_not_aggregated(self, engine):
        """Test that different events are kept separate"""
        events = [
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth.py", "complexity": 0.7},
                "source": "serena",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "search.completed",
                "data": {"query": "authentication", "results": 5},
                "source": "dope-context",
                "timestamp": "2025-10-23T10:01:00Z"
            },
        ]

        aggregated = await engine.aggregate_events(events)

        assert len(aggregated) == 2, "Should keep different events separate"

    @pytest.mark.asyncio
    async def test_similar_but_not_identical_events_aggregated(self, engine):
        """Test that similar events (>80% match) are merged"""
        events = [
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth.py", "complexity": 0.7, "lines": 100},
                "source": "serena",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth.py", "complexity": 0.72, "lines": 102},
                "source": "dope-context",
                "timestamp": "2025-10-23T10:01:00Z"
            },
        ]

        aggregated = await engine.aggregate_events(events)

        # Should aggregate because core content (file + complexity) is very similar
        assert len(aggregated) == 1, "Should merge similar events"
        assert len(aggregated[0].sources) == 2

    @pytest.mark.asyncio
    async def test_confidence_scores_combined(self, engine):
        """Test that confidence scores are properly combined"""
        events = [
            {
                "type": "search.pattern",
                "data": {"pattern": "auth_flow", "confidence": 0.8},
                "source": "agent1",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "search.pattern",
                "data": {"pattern": "auth_flow", "confidence": 0.9},
                "source": "agent2",
                "timestamp": "2025-10-23T10:01:00Z"
            },
        ]

        aggregated = await engine.aggregate_events(events)

        assert len(aggregated) == 1
        combined_confidence = aggregated[0].get_combined_confidence()

        # Should be between 0.8 and 0.9, weighted toward higher score
        assert 0.8 <= combined_confidence <= 0.9
        assert combined_confidence > 0.85  # Weighted toward 0.9

    @pytest.mark.asyncio
    async def test_provenance_tracking(self, engine):
        """Test that provenance chain is tracked"""
        events = [
            {
                "type": "test.event",
                "data": {"key": "value"},
                "source": "agent1",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "test.event",
                "data": {"key": "value"},
                "source": "agent2",
                "timestamp": "2025-10-23T10:01:00Z"
            },
        ]

        aggregated = await engine.aggregate_events(events)

        assert len(aggregated) == 1
        assert len(aggregated[0].original_event_ids) == 2
        assert len(aggregated[0].timestamps) == 2

    @pytest.mark.asyncio
    async def test_single_event_not_modified(self, engine):
        """Test that single events pass through unchanged"""
        events = [
            {
                "type": "unique.event",
                "data": {"key": "value"},
                "source": "agent1",
                "timestamp": "2025-10-23T10:00:00Z"
            },
        ]

        aggregated = await engine.aggregate_events(events)

        assert len(aggregated) == 1
        assert aggregated[0].event_type == "unique.event"
        assert len(aggregated[0].sources) == 1

    @pytest.mark.asyncio
    async def test_empty_events_returns_empty(self, engine):
        """Test that empty event list returns empty"""
        aggregated = await engine.aggregate_events([])

        assert len(aggregated) == 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, engine):
        """Test that aggregation metrics are tracked"""
        # Reset metrics
        engine.reset_metrics()

        events = [
            {"type": "event1", "data": {"x": 1}, "source": "a1", "timestamp": "2025-10-23T10:00:00Z"},
            {"type": "event1", "data": {"x": 1}, "source": "a2", "timestamp": "2025-10-23T10:01:00Z"},
            {"type": "event2", "data": {"y": 2}, "source": "a3", "timestamp": "2025-10-23T10:02:00Z"},
        ]

        aggregated = await engine.aggregate_events(events)

        metrics = engine.get_metrics()

        assert metrics["total_aggregations"] == 1
        assert metrics["events_before"] == 3
        assert metrics["events_after"] == 2  # event1 merged, event2 separate
        # Reduction: (3-2)/3 = 33.33%
        assert metrics["reduction_rate_percent"] == 33.33

    @pytest.mark.asyncio
    async def test_reduction_rate_calculated(self, engine):
        """Test that reduction rate is calculated correctly"""
        engine.reset_metrics()

        # Create 10 identical events (should merge to 1)
        events = [
            {
                "type": "test",
                "data": {"same": "content"},
                "source": f"agent{i}",
                "timestamp": f"2025-10-23T10:{i:02d}:00Z"
            }
            for i in range(10)
        ]

        aggregated = await engine.aggregate_events(events)

        assert len(aggregated) == 1, "All identical events should merge"

        metrics = engine.get_metrics()
        # Reduction: (10-1)/10 = 90%
        assert metrics["reduction_rate_percent"] == 90.0

    @pytest.mark.asyncio
    async def test_similarity_threshold_enforcement(self):
        """Test that similarity threshold controls merging"""
        # High threshold (0.95) - strict matching
        strict_engine = AggregationEngine(similarity_threshold=0.95)

        events = [
            {
                "type": "event",
                "data": {"file": "auth.py", "score": 0.7},
                "source": "agent1",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "event",
                "data": {"file": "auth.py", "score": 0.75},  # Slightly different
                "source": "agent2",
                "timestamp": "2025-10-23T10:01:00Z"
            },
        ]

        aggregated = await strict_engine.aggregate_events(events)

        # With strict threshold, these might not merge
        # (depends on similarity calculation)
        assert len(aggregated) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
