"""
Unit Tests for ConPort Insight Publisher

Tests AI decision logging, automatic linking, and event parsing
for Architecture 3.0 Component 2.

Created: 2025-10-19 (Task 2.3)
"""

import pytest
from datetime import datetime

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_orchestrator import AgentType
from adapters.conport_insight_publisher import (
    AIDecisionEvent,
    ConPortInsightPublisher,
    create_architecture_decision,
    create_code_review_decision
)


# ============================================================================
# AIDecisionEvent Tests
# ============================================================================

class TestAIDecisionEvent:
    """Test AIDecisionEvent dataclass and methods."""

    def test_decision_event_creation(self):
        """Test basic AIDecisionEvent creation."""
        event = AIDecisionEvent(
            summary="Use Redis Streams for event bus",
            rationale="Enables async communication between services",
            implementation_details="Implement xadd/xreadgroup pattern",
            agent_type=AgentType.ZEN,
            confidence=0.85,
            alternatives_considered=["Direct HTTP", "Shared database"]
        )

        assert event.summary == "Use Redis Streams for event bus"
        assert event.agent_type == AgentType.ZEN
        assert event.confidence == 0.85
        assert len(event.alternatives_considered) == 2

    def test_auto_tag_generation(self):
        """Test that tags are auto-generated from agent and confidence."""
        event = AIDecisionEvent(
            summary="Test decision",
            rationale="Test rationale",
            implementation_details="Test details",
            agent_type=AgentType.SERENA,
            confidence=0.75,
            alternatives_considered=[]
        )

        # Tags auto-generated in __post_init__
        assert "ai-generated" in event.tags
        assert "agent-serena" in event.tags
        assert "confidence-7" in event.tags  # 0.75 * 10 = 7

    def test_custom_tags_preserved(self):
        """Test that custom tags can be provided."""
        custom_tags = ["custom-tag", "architecture", "critical"]

        event = AIDecisionEvent(
            summary="Test",
            rationale="Test",
            implementation_details="Test",
            agent_type=AgentType.ZEN,
            confidence=0.9,
            alternatives_considered=[],
            tags=custom_tags
        )

        assert event.tags == custom_tags  # Custom tags preserved

    def test_to_conport_decision_format(self):
        """Test conversion to ConPort decision format."""
        event = AIDecisionEvent(
            summary="Architecture decision",
            rationale="Performance requirements",
            implementation_details="Use caching layer",
            agent_type=AgentType.ZEN,
            confidence=0.8,
            alternatives_considered=["No caching", "Redis only"]
        )

        conport_format = event.to_conport_decision()

        assert conport_format["summary"] == "Architecture decision"
        assert conport_format["rationale"] == "Performance requirements"
        assert conport_format["implementation_details"] == "Use caching layer"
        assert "tags" in conport_format
        assert "ai-generated" in conport_format["tags"]


# ============================================================================
# Convenience Function Tests
# ============================================================================

class TestConvenienceFunctions:
    """Test convenience functions for creating decision events."""

    def test_create_architecture_decision(self):
        """Test architecture decision creation."""
        event = create_architecture_decision(
            summary="Use microservices architecture",
            rationale="Scalability and team independence",
            implementation_details="Split into auth, api, worker services",
            confidence=0.9,
            task_id="task-200"
        )

        assert event.agent_type == AgentType.ZEN  # Default
        assert event.confidence == 0.9
        assert event.related_task_id == "task-200"
        assert "architecture" in event.tags

    def test_create_code_review_decision(self):
        """Test code review decision creation."""
        event = create_code_review_decision(
            summary="Security vulnerability found in auth module",
            findings="JWT tokens not properly validated",
            recommendations="Add token signature verification",
            severity="high",
            task_id="task-auth-fix"
        )

        assert event.agent_type == AgentType.SERENA  # Default
        assert "code-review" in event.tags
        assert "severity-high" in event.tags
        assert event.related_task_id == "task-auth-fix"


# ============================================================================
# ConPortInsightPublisher Tests
# ============================================================================

class TestConPortInsightPublisher:
    """Test ConPortInsightPublisher class methods."""

    def test_publisher_initialization(self):
        """Test publisher initialization."""
        publisher = ConPortInsightPublisher(
            workspace_id="/test/workspace",
            conport_client=None
        )

        assert publisher.workspace_id == "/test/workspace"
        assert publisher.conport_client is None
        assert len(publisher.decision_cache) == 0

    @pytest.mark.asyncio
    async def test_log_ai_decision_no_client(self):
        """Test decision logging when ConPort client not available."""
        publisher = ConPortInsightPublisher("/test", conport_client=None)

        event = AIDecisionEvent(
            summary="Test decision",
            rationale="Test rationale",
            implementation_details="Test details",
            agent_type=AgentType.ZEN,
            confidence=0.8,
            alternatives_considered=[]
        )

        decision_id = await publisher.log_ai_decision(event)

        # Should return None when no client
        assert decision_id is None
        # Should cache locally
        assert "Test decision" in publisher.decision_cache

    def test_parse_zen_result(self):
        """Test parsing Zen MCP agent results."""
        publisher = ConPortInsightPublisher("/test")

        zen_result = {
            "summary": "Zen analysis complete",
            "findings": "Found optimal solution",
            "recommendations": "Implement pattern X",
            "confidence": 0.9,
            "tool": "thinkdeep",
            "alternatives": ["Pattern Y", "Pattern Z"]
        }

        event = publisher.parse_zen_result(zen_result, task_id="task-999")

        assert event.summary == "Zen analysis complete"
        assert event.rationale == "Found optimal solution"
        assert event.implementation_details == "Implement pattern X"
        assert event.agent_type == AgentType.ZEN
        assert event.confidence == 0.9
        assert event.related_task_id == "task-999"
        assert "thinkdeep" in event.tags

    def test_parse_serena_result(self):
        """Test parsing Serena MCP agent results."""
        publisher = ConPortInsightPublisher("/test")

        serena_result = {
            "summary": "Code complexity analysis",
            "analysis": "Function has high cyclomatic complexity",
            "recommendations": "Refactor into smaller functions",
            "confidence": 0.85
        }

        event = publisher.parse_serena_result(serena_result, task_id="refactor-123")

        assert event.agent_type == AgentType.SERENA
        assert "code-analysis" in event.tags
        assert event.related_task_id == "refactor-123"

    def test_cache_stats(self):
        """Test cache statistics reporting."""
        publisher = ConPortInsightPublisher("/test")

        # Add some cached decisions
        event1 = AIDecisionEvent(
            summary="Decision 1",
            rationale="Rationale 1",
            implementation_details="Details 1",
            agent_type=AgentType.ZEN,
            confidence=0.8,
            alternatives_considered=[]
        )
        publisher.decision_cache["Decision 1"] = event1

        stats = publisher.get_cache_stats()

        assert stats["cached_decisions"] == 1
        assert stats["cache_size_bytes"] > 0


# ============================================================================
# Integration Tests (placeholder for Task 2.6)
# ============================================================================

class TestInsightPublisherIntegration:
    """Integration tests with actual ConPort (placeholder for Task 2.6)."""

    @pytest.mark.skip(reason="Requires ConPort MCP client - implement in Task 2.6")
    @pytest.mark.asyncio
    async def test_log_and_link_decision(self):
        """Test end-to-end decision logging and linking."""
        pass

    @pytest.mark.skip(reason="Requires ConPort MCP client - implement in Task 2.6")
    @pytest.mark.asyncio
    async def test_batch_decision_logging(self):
        """Test batch decision logging."""
        pass

    @pytest.mark.skip(reason="Requires ConPort MCP client - implement in Task 2.6")
    @pytest.mark.asyncio
    async def test_cache_flush_to_conport(self):
        """Test flushing cached decisions to ConPort."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
