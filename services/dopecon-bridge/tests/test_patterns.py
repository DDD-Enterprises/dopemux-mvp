"""
Tests for Pattern Detection Engine
Validates all 7 pattern detectors and orchestrator
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from patterns import (
    HighComplexityClusterPattern,
    RepeatedErrorPattern,
    KnowledgeGapPattern,
    DecisionChurnPattern,
    ADHDStatePattern,
    ContextSwitchFrequencyPattern,
    TaskAbandonmentPattern,
)
from pattern_detector import PatternDetector


class TestHighComplexityClusterPattern:
    """Test high complexity cluster pattern detection"""

    def test_detects_cluster_of_high_complexity_files(self):
        """Test detection of 3+ high-complexity files in same directory"""
        pattern = HighComplexityClusterPattern()

        events = [
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth/login.py", "complexity": 0.7},
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth/session.py", "complexity": 0.8},
                "timestamp": "2025-10-23T10:05:00Z"
            },
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth/permissions.py", "complexity": 0.75},
                "timestamp": "2025-10-23T10:10:00Z"
            },
        ]

        insights = pattern.detect(events)

        assert len(insights) == 1, "Should detect 1 cluster"
        assert insights[0].pattern_name == "high_complexity_cluster"
        assert insights[0].event_count == 3
        assert "/project/auth" in insights[0].details

    def test_no_detection_below_threshold(self):
        """Test that clusters below threshold are not detected"""
        pattern = HighComplexityClusterPattern()

        events = [
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth/login.py", "complexity": 0.7},
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth/session.py", "complexity": 0.8},
                "timestamp": "2025-10-23T10:05:00Z"
            },
        ]

        insights = pattern.detect(events)

        assert len(insights) == 0, "Should not detect cluster with only 2 files"


class TestRepeatedErrorPattern:
    """Test repeated errors pattern detection"""

    def test_detects_repeated_errors(self):
        """Test detection of same error from multiple agents"""
        pattern = RepeatedErrorPattern()

        events = [
            {
                "type": "agent.error",
                "data": {"error": "Connection refused to database on line 45"},
                "source": "serena",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "task.failed",
                "data": {"error": "Connection refused to database on line 67"},
                "source": "task-orchestrator",
                "timestamp": "2025-10-23T10:02:00Z"
            },
            {
                "type": "analysis.error",
                "data": {"message": "Connection refused to database on line 123"},
                "source": "zen",
                "timestamp": "2025-10-23T10:05:00Z"
            },
        ]

        insights = pattern.detect(events)

        assert len(insights) == 1, "Should detect repeated error pattern"
        assert insights[0].pattern_name == "repeated_errors"
        assert insights[0].event_count == 3
        assert len(insights[0].affected_resources) == 3  # 3 different agents


class TestKnowledgeGapPattern:
    """Test knowledge gaps pattern detection"""

    def test_detects_low_confidence_searches(self):
        """Test detection of repeated low-confidence searches"""
        pattern = KnowledgeGapPattern()

        events = [
            {
                "type": "search.completed",
                "data": {"query": "authentication flow implementation", "confidence": 0.2},
                "source": "dope-context",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "search.completed",
                "data": {"query": "how to implement authentication", "confidence": 0.3},
                "source": "dope-context",
                "timestamp": "2025-10-23T10:10:00Z"
            },
            {
                "type": "search.completed",
                "data": {"query": "authentication implementation guide", "confidence": 0.25},
                "source": "serena",
                "timestamp": "2025-10-23T10:15:00Z"
            },
        ]

        insights = pattern.detect(events)

        assert len(insights) == 1, "Should detect knowledge gap"
        assert insights[0].pattern_name == "knowledge_gaps"
        assert insights[0].event_count == 3


class TestDecisionChurnPattern:
    """Test decision churn pattern detection"""

    def test_detects_repeated_decisions_on_same_topic(self):
        """Test detection of multiple decisions on similar topics"""
        pattern = DecisionChurnPattern()

        events = [
            {
                "type": "decision.consensus.reached",
                "data": {"summary": "Use PostgreSQL for data storage"},
                "source": "zen",
                "timestamp": "2025-10-23T09:00:00Z"
            },
            {
                "type": "decision.logged",
                "data": {"summary": "Switch to MongoDB for data storage"},
                "source": "task-orchestrator",
                "timestamp": "2025-10-23T10:00:00Z"
            },
            {
                "type": "decision.consensus.reached",
                "data": {"summary": "Reconsider PostgreSQL vs MongoDB storage"},
                "source": "zen",
                "timestamp": "2025-10-23T11:00:00Z"
            },
        ]

        insights = pattern.detect(events)

        assert len(insights) == 1, "Should detect decision churn"
        assert insights[0].pattern_name == "decision_churn"
        assert insights[0].event_count == 3


class TestADHDStatePattern:
    """Test ADHD state patterns detection"""

    def test_detects_time_based_cognitive_load_patterns(self):
        """Test detection of cognitive load spikes at specific times"""
        pattern = ADHDStatePattern()

        # Create events with high load at same hour
        base_time = datetime(2025, 10, 23, 14, 0, 0)  # 2pm
        events = []

        for day in range(3):
            for minute in [0, 15, 30]:
                timestamp = base_time + timedelta(days=day, minutes=minute)
                events.append({
                    "type": "cognitive.state.changed",
                    "data": {
                        "cognitive_load": 0.85,  # High load
                        "attention_state": "scattered"
                    },
                    "timestamp": timestamp.isoformat() + "Z"
                })

        insights = pattern.detect(events)

        assert len(insights) >= 1, "Should detect time-based pattern"
        if insights:
            assert insights[0].pattern_name == "adhd_state_patterns"


class TestContextSwitchFrequencyPattern:
    """Test context switch frequency pattern detection"""

    def test_detects_excessive_workspace_switches(self):
        """Test detection of >10 workspace switches per hour"""
        pattern = ContextSwitchFrequencyPattern()

        # Create 12 workspace switches over 1 hour (12/hour rate)
        base_time = datetime.utcnow()
        events = []

        for i in range(12):
            timestamp = base_time + timedelta(minutes=i * 5)
            events.append({
                "type": "workspace.switched",
                "data": {
                    "from_workspace": f"/project{i % 3}",
                    "to_workspace": f"/project{(i + 1) % 3}"
                },
                "timestamp": timestamp.isoformat() + "Z"
            })

        insights = pattern.detect(events)

        assert len(insights) == 1, "Should detect excessive switching"
        assert insights[0].pattern_name == "context_switch_frequency"
        assert insights[0].event_count == 12


class TestTaskAbandonmentPattern:
    """Test task abandonment pattern detection"""

    def test_detects_abandoned_tasks(self):
        """Test detection of tasks started but not progressed"""
        pattern = TaskAbandonmentPattern()

        # Create tasks started 3+ hours ago with no completion
        old_time = datetime.utcnow() - timedelta(hours=3)

        events = []
        for i in range(3):
            task_id = f"task-{i}"

            # Task started
            events.append({
                "type": "task.progress.updated",
                "data": {
                    "task_id": task_id,
                    "status": "IN_PROGRESS",
                    "description": f"Implement feature {i}",
                    "complexity": 0.7
                },
                "timestamp": (old_time + timedelta(minutes=i * 10)).isoformat() + "Z"
            })

        insights = pattern.detect(events)

        assert len(insights) == 1, "Should detect abandoned tasks"
        assert insights[0].pattern_name == "task_abandonment"
        assert insights[0].event_count == 3


class TestPatternDetector:
    """Test PatternDetector orchestrator"""

    @pytest.fixture
    async def event_bus(self):
        """Create mock EventBus"""
        bus = Mock()
        bus.redis_client = Mock()
        return bus

    @pytest.fixture
    def pattern_detector(self, event_bus):
        """Create PatternDetector instance"""
        return PatternDetector(
            event_bus=event_bus,
            event_window_minutes=60,
            detection_interval_seconds=300
        )

    @pytest.mark.asyncio
    async def test_analyzes_events_with_all_patterns(self, pattern_detector):
        """Test that all patterns are run on events"""
        events = [
            {
                "type": "code.complexity.high",
                "data": {"file": "/project/auth/login.py", "complexity": 0.7},
                "timestamp": "2025-10-23T10:00:00Z"
            },
        ]

        insights = await pattern_detector.analyze_events(events, "/workspace")

        # Should run without errors (may or may not generate insights)
        assert isinstance(insights, list)

    def test_all_7_patterns_loaded(self, pattern_detector):
        """Test that all 7 pattern detectors are loaded"""
        assert len(pattern_detector.patterns) == 7, "Should have 7 pattern detectors"

        pattern_names = [p.get_pattern_name() for p in pattern_detector.patterns]

        expected_patterns = [
            "high_complexity_cluster",
            "repeated_errors",
            "knowledge_gaps",
            "decision_churn",
            "adhd_state_patterns",
            "context_switch_frequency",
            "task_abandonment",
        ]

        for expected in expected_patterns:
            assert expected in pattern_names, f"Missing pattern: {expected}"

    def test_get_metrics_returns_all_pattern_stats(self, pattern_detector):
        """Test that metrics include all pattern statistics"""
        metrics = pattern_detector.get_metrics()

        assert "total_runs" in metrics
        assert "total_insights_generated" in metrics
        assert "patterns" in metrics
        assert len(metrics["patterns"]) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
