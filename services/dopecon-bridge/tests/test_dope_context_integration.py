"""
Tests for Dope-Context Integration
Validates event emission for search patterns and knowledge gaps
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from event_bus import Event, EventBus
from integrations.dope_context import DopeContextEventEmitter, DopeContextIntegrationManager


class TestDopeContextEventEmitter:
    """Test DopeContextEventEmitter"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def emitter(self, event_bus_mock):
        """Create DopeContextEventEmitter"""
        return DopeContextEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            confidence_threshold=0.4
        )

    @pytest.mark.asyncio
    async def test_emits_knowledge_gap_event(self, emitter, event_bus_mock):
        """Test that knowledge gap events are emitted for low confidence"""
        result = await emitter.emit_knowledge_gap(
            query="authentication flow",
            results_count=3,
            avg_confidence=0.25  # Below 0.4 threshold
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "knowledge.gap.detected"
        assert event.data["query"] == "authentication flow"
        assert event.data["confidence"] == 0.25
        assert event.source == "dope-context"

    @pytest.mark.asyncio
    async def test_no_gap_event_above_threshold(self, emitter, event_bus_mock):
        """Test that gap events not emitted above threshold"""
        result = await emitter.emit_knowledge_gap(
            query="test query",
            results_count=5,
            avg_confidence=0.7  # Above 0.4 threshold
        )

        assert result is False
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_emits_pattern_discovered(self, emitter, event_bus_mock):
        """Test pattern discovery event emission"""
        result = await emitter.emit_pattern_discovered(
            queries=["auth flow", "authentication impl", "how auth works"],
            frequency=3,
            topic_keywords="authentication"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "search.pattern.discovered"
        assert event.data["frequency"] == 3
        assert event.data["topic_keywords"] == "authentication"

    @pytest.mark.asyncio
    async def test_search_completed_requires_analytics_enabled(self, event_bus_mock):
        """Test that search.completed requires analytics flag"""
        emitter = DopeContextEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_search_analytics=False  # Disabled
        )

        result = await emitter.emit_search_completed(
            query="test",
            results_count=5,
            avg_confidence=0.7
        )

        assert result is False
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_search_completed_emits_when_enabled(self, event_bus_mock):
        """Test search.completed emits when analytics enabled"""
        emitter = DopeContextEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_search_analytics=True  # Enabled
        )

        result = await emitter.emit_search_completed(
            query="test query",
            results_count=5,
            avg_confidence=0.7
        )

        assert result is True
        assert event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, emitter):
        """Test that emission metrics are tracked"""
        emitter.reset_metrics()

        await emitter.emit_knowledge_gap("query1", 3, 0.2)
        await emitter.emit_knowledge_gap("query2", 2, 0.3)
        await emitter.emit_pattern_discovered(["q1", "q2", "q3"], 3, "topic")

        metrics = emitter.get_metrics()

        assert metrics["agent"] == "dope-context"
        assert metrics["events_emitted"] == 3
        assert metrics["knowledge_gap_events"] == 2
        assert metrics["pattern_events"] == 1


class TestDopeContextIntegrationManager:
    """Test DopeContextIntegrationManager"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def manager(self, event_bus_mock):
        """Create DopeContextIntegrationManager"""
        return DopeContextIntegrationManager(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_knowledge_gap_events=True,
            enable_pattern_events=True
        )

    @pytest.mark.asyncio
    async def test_handles_search_result_with_low_confidence(self, manager, event_bus_mock):
        """Test handling low confidence search result"""
        results = [
            {"relevance_score": 0.2},
            {"relevance_score": 0.3},
            {"relevance_score": 0.25}
        ]

        await manager.handle_search_result("authentication", results)

        # Should emit knowledge gap event
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "knowledge.gap.detected"

    @pytest.mark.asyncio
    async def test_tracks_query_history(self, manager):
        """Test that query history is tracked"""
        results = [{"relevance_score": 0.7}]

        await manager.handle_search_result("query1", results)
        await manager.handle_search_result("query2", results)
        await manager.handle_search_result("query3", results)

        assert len(manager.query_history) == 3

    @pytest.mark.asyncio
    async def test_detects_search_pattern(self, manager, event_bus_mock):
        """Test that repeated similar searches trigger pattern event"""
        results = [{"relevance_score": 0.7}]

        # Search for similar topics 4 times
        await manager.handle_search_result("authentication flow", results)
        await manager.handle_search_result("how to authenticate", results)
        await manager.handle_search_result("authentication implementation", results)
        await manager.handle_search_result("authentication guide", results)

        # Check if pattern event was emitted
        calls = event_bus_mock.publish.call_args_list
        pattern_events = [
            call for call in calls
            if call[0][1].type == "search.pattern.discovered"
        ]

        assert len(pattern_events) >= 1, "Should detect pattern after 3+ similar searches"

    @pytest.mark.asyncio
    async def test_history_limit_enforced(self, manager):
        """Test that query history respects size limit"""
        results = [{"relevance_score": 0.7}]

        # Add more than history_size (100) queries
        for i in range(150):
            await manager.handle_search_result(f"query{i}", results)

        # Should be capped at 100
        assert len(manager.query_history) == 100

    def test_get_metrics_includes_history_size(self, manager):
        """Test that metrics include query history size"""
        metrics = manager.get_metrics()

        assert "agent" in metrics
        assert metrics["agent"] == "dope-context"
        assert "query_history_size" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
