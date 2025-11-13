"""
Tests for Zen Integration
Validates event emission for consensus decisions and architecture choices
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from event_bus import Event, EventBus
from integrations.zen import ZenEventEmitter, ZenIntegrationManager


class TestZenEventEmitter:
    """Test ZenEventEmitter"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def emitter(self, event_bus_mock):
        """Create ZenEventEmitter"""
        return ZenEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

    @pytest.mark.asyncio
    async def test_emits_consensus_reached_event(self, emitter, event_bus_mock):
        """Test consensus event emission"""
        result = await emitter.emit_consensus_reached(
            decision_summary="Use PostgreSQL for data storage",
            models_consulted=["gpt-5", "claude-sonnet-4.5", "gemini-2.5-pro"],
            final_recommendation="PostgreSQL is recommended",
            confidence=0.85,
            stances={"gpt-5": "for", "claude-sonnet-4.5": "for", "gemini-2.5-pro": "neutral"}
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "decision.consensus.reached"
        assert event.data["decision_summary"] == "Use PostgreSQL for data storage"
        assert event.data["model_count"] == 3
        assert event.data["confidence"] == 0.85
        assert event.source == "zen"

    @pytest.mark.asyncio
    async def test_emits_architecture_choice(self, emitter, event_bus_mock):
        """Test architecture choice event"""
        result = await emitter.emit_architecture_choice(
            choice_summary="Microservices architecture",
            rationale="Better scalability and team autonomy",
            alternatives=["Monolith", "Modular monolith"],
            trade_offs={"complexity": "high", "scalability": "excellent"},
            priority="high"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "architecture.choice.made"
        assert event.data["priority"] == "high"
        assert len(event.data["alternatives"]) == 2

    @pytest.mark.asyncio
    async def test_emits_analysis_completed(self, emitter, event_bus_mock):
        """Test analysis completion event"""
        # Enable tracking
        emitter.track_all_analyses = True

        result = await emitter.emit_analysis_completed(
            analysis_type="thinkdeep",
            summary="Root cause identified",
            confidence=0.9,
            findings=["Finding 1", "Finding 2"],
            recommendations=["Recommendation 1"]
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "analysis.completed"
        assert event.data["analysis_type"] == "thinkdeep"
        assert event.data["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_analysis_events_disabled_by_default(self, emitter, event_bus_mock):
        """Test that analysis events are disabled by default"""
        result = await emitter.emit_analysis_completed(
            analysis_type="debug",
            summary="Bug found",
            confidence=0.8
        )

        assert result is False
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_events_can_be_disabled(self, event_bus_mock):
        """Test that all events can be disabled"""
        emitter = ZenEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_events=False
        )

        result = await emitter.emit_consensus_reached(
            decision_summary="Test",
            models_consulted=["model1"],
            final_recommendation="Recommendation",
            confidence=0.8
        )

        assert result is False
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, emitter):
        """Test metrics tracking"""
        emitter.reset_metrics()

        await emitter.emit_consensus_reached(
            "Decision 1", ["model1"], "Rec 1", 0.8
        )
        await emitter.emit_consensus_reached(
            "Decision 2", ["model1"], "Rec 2", 0.7
        )
        await emitter.emit_architecture_choice(
            "Choice 1", "Rationale", ["Alt"], {}, "medium"
        )

        metrics = emitter.get_metrics()

        assert metrics["agent"] == "zen"
        assert metrics["events_emitted"] == 3
        assert metrics["consensus_events"] == 2
        assert metrics["architecture_events"] == 1

    @pytest.mark.asyncio
    async def test_handles_publish_errors_gracefully(self, event_bus_mock):
        """Test graceful error handling"""
        event_bus_mock.publish = AsyncMock(side_effect=Exception("EventBus down"))

        emitter = ZenEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

        result = await emitter.emit_consensus_reached(
            "Decision", ["model1"], "Recommendation", 0.8
        )

        assert result is False
        assert emitter.emission_errors == 1


class TestZenIntegrationManager:
    """Test ZenIntegrationManager"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def manager(self, event_bus_mock):
        """Create ZenIntegrationManager"""
        return ZenIntegrationManager(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

    @pytest.mark.asyncio
    async def test_handles_consensus_result(self, manager, event_bus_mock):
        """Test handling consensus result"""
        await manager.handle_consensus_result(
            decision_summary="Use TypeScript",
            models_consulted=["gpt-5", "claude"],
            final_recommendation="TypeScript recommended for type safety",
            confidence=0.9,
            stances={"gpt-5": "for", "claude": "for"}
        )

        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "decision.consensus.reached"
        assert event.data["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_handles_architecture_decision(self, manager, event_bus_mock):
        """Test handling architecture decision"""
        await manager.handle_architecture_decision(
            choice="Event-driven architecture",
            rationale="Better scalability and decoupling",
            alternatives=["Request-response", "Batch processing"],
            trade_offs={"complexity": "medium", "scalability": "high"},
            priority="high"
        )

        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "architecture.choice.made"
        assert event.data["priority"] == "high"

    def test_get_metrics_returns_emitter_metrics(self, manager):
        """Test that manager returns emitter metrics"""
        metrics = manager.get_metrics()

        assert metrics["agent"] == "zen"
        assert "events_emitted" in metrics
        assert "consensus_events" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
