"""Unit tests for the Context Integration Framework."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from genetic_agent.intelligent.context_integrator import (
    ContextIntegrator,
    ContextSource,
    EnhancedContext
)
from genetic_agent.core.config import AgentConfig


@pytest.fixture
def agent_config():
    """Fixture for agent configuration."""
    return AgentConfig()


@pytest.fixture
def context_integrator(agent_config):
    """Fixture for context integrator."""
    return ContextIntegrator(agent_config)


@pytest.fixture
def sample_issue_context():
    """Sample issue context for testing."""
    return {
        "description": "null pointer exception in user validation",
        "file_path": "user_service.py",
        "function_name": "validate_user",
        "error_type": "null_pointer",
        "line_number": 45
    }


class TestContextIntegrator:
    """Test suite for ContextIntegrator."""

    @pytest.mark.asyncio
    async def test_gather_context_basic(self, context_integrator, sample_issue_context):
        """Test basic context gathering functionality."""
        with patch.object(context_integrator, '_collect_all_sources', new_callable=AsyncMock) as mock_collect:
            # Mock collected sources
            mock_sources = [
                ContextSource("code_complexity", {"score": 0.7}, 0.8, 150, "static"),
                ContextSource("test_patterns", {"failing_tests": ["test_user"]}, 0.6, 100, "dynamic")
            ]
            mock_collect.return_value = mock_sources

            context = await context_integrator.gather_context(sample_issue_context)

            assert isinstance(context, EnhancedContext)
            assert context.total_sources == 2
            assert len(context.essential_context) > 0
            assert "quality_score" in context.__dict__

    def test_score_sources(self, context_integrator, sample_issue_context):
        """Test source scoring functionality."""
        sources = [
            ContextSource("code_complexity", {"score": 0.7}, 0.0, 150, "static"),
            ContextSource("test_patterns", {"failing_tests": ["test_user"]}, 0.0, 100, "dynamic"),
            ContextSource("similar_patterns", {"results": []}, 0.0, 200, "semantic")
        ]

        scored_sources = context_integrator._score_sources(sources, sample_issue_context)

        # All sources should have relevance scores
        for source in scored_sources:
            assert source.relevance_score > 0

        # Should be sorted by relevance (highest first)
        assert scored_sources[0].relevance_score >= scored_sources[1].relevance_score

    def test_assess_content_relevance(self, context_integrator, sample_issue_context):
        """Test content relevance assessment."""
        # High relevance for complexity with complexity-related issue
        complexity_source = ContextSource("code_complexity", {"score": 0.8}, 0.0, 100, "static")
        relevance = context_integrator._assess_content_relevance(complexity_source, {
            **sample_issue_context,
            "description": "high complexity in validation"
        })
        assert relevance > 1.0  # Boosted relevance

        # High relevance for test patterns with test-related issue
        test_source = ContextSource("test_failure_patterns", {"failing_tests": ["test_validate"]}, 0.0, 100, "dynamic")
        relevance = context_integrator._assess_content_relevance(test_source, {
            **sample_issue_context,
            "description": "test failure in validation"
        })
        assert relevance > 1.5  # Significantly boosted

    def test_estimate_token_usage(self, context_integrator):
        """Test token usage estimation."""
        # Test different source types
        static_source = ContextSource("complexity", {"large": "content" * 100}, 0.0, 0, "static")
        dynamic_source = ContextSource("traces", {"large": "content" * 100}, 0.0, 0, "dynamic")
        semantic_source = ContextSource("patterns", {"large": "content" * 100}, 0.0, 0, "semantic")

        static_tokens = context_integrator._estimate_token_usage(static_source)
        dynamic_tokens = context_integrator._estimate_token_usage(dynamic_source)
        semantic_tokens = context_integrator._estimate_token_usage(semantic_source)

        # All should have reasonable estimates
        assert static_tokens > 0
        assert dynamic_tokens > 0
        assert semantic_tokens > 0

        # Static should be slightly lower (more structured)
        assert static_tokens <= dynamic_tokens

    def test_apply_progressive_disclosure(self, context_integrator, sample_issue_context):
        """Test progressive disclosure functionality."""
        sources = [
            ContextSource("high_relevance", {"data": "valuable"}, 0.9, 100, "static"),
            ContextSource("medium_relevance", {"data": "useful"}, 0.6, 200, "dynamic"),
            ContextSource("low_relevance", {"data": "minimal"}, 0.2, 50, "semantic"),
            ContextSource("too_large", {"data": "huge" * 1000}, 0.8, 2500, "static")  # Over budget
        ]

        context = context_integrator._apply_progressive_disclosure(sources, sample_issue_context)

        # Should include high and medium relevance sources
        assert "high_relevance" in context.essential_context
        assert "medium_relevance" in context.essential_context
        assert "low_relevance" not in context.essential_context  # Below threshold
        assert "too_large" not in context.essential_context  # Over budget

        # Should respect token budget
        assert context.token_budget_used <= context.max_token_budget

        # Full context should include all sources
        assert len(context.full_context) == 4

    def test_calculate_context_quality(self, context_integrator):
        """Test context quality calculation."""
        # High quality context
        high_quality = {
            "static": {"complexity": 0.7},
            "dynamic": {"traces": []},
            "semantic": {"patterns": []}
        }

        sources = [
            ContextSource("static", {}, 0.8, 100, "static"),
            ContextSource("dynamic", {}, 0.7, 100, "dynamic"),
            ContextSource("semantic", {}, 0.6, 100, "semantic")
        ]

        quality = context_integrator._calculate_context_quality(high_quality, sources)
        assert 0.7 <= quality <= 1.0  # High quality score

        # Low quality context
        low_quality = {}
        quality = context_integrator._calculate_context_quality(low_quality, sources)
        assert quality == 0.0

    def test_get_context_statistics(self, context_integrator):
        """Test context statistics generation."""
        context = EnhancedContext(
            essential_context={"static": {}, "dynamic": {}},
            full_context={
                "static": {"type": "static", "relevance": 0.8, "tokens": 100},
                "dynamic": {"type": "dynamic", "relevance": 0.7, "tokens": 150},
                "semantic": {"type": "semantic", "relevance": 0.5, "tokens": 200}
            },
            total_sources=3,
            prioritized_sources=["static", "dynamic"],
            token_budget_used=250,
            max_token_budget=2000
        )

        stats = context_integrator.get_context_statistics(context)

        assert stats["total_sources"] == 3
        assert stats["prioritized_sources"] == 2
        assert stats["token_budget_used"] == 250
        assert stats["token_budget_remaining"] == 1750
        assert "quality_score" in stats
        assert "source_type_breakdown" in stats
        assert stats["context_coverage"] == 2/3

    @pytest.mark.asyncio
    async def test_gather_static_context(self, context_integrator, sample_issue_context):
        """Test static context gathering."""
        with patch.object(context_integrator.serena_client, 'analyze_complexity', new_callable=AsyncMock) as mock_complexity:
            mock_complexity.return_value = {"score": 0.7, "functions": 5}

            async with context_integrator.serena_client:
                sources = await context_integrator._gather_static_context(sample_issue_context)

            assert len(sources) > 0
            assert sources[0].source_type == "static"
            assert "code_complexity" in sources[0].name

    @pytest.mark.asyncio
    async def test_gather_semantic_context(self, context_integrator, sample_issue_context):
        """Test semantic context gathering."""
        with patch.object(context_integrator.dope_client, 'search_code', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"results": ["pattern1", "pattern2"]}

            async with context_integrator.dope_client:
                sources = await context_integrator._gather_semantic_context(sample_issue_context)

            assert len(sources) > 0
            assert sources[0].source_type == "semantic"
            assert "similar_repair_patterns" in sources[0].name

    @pytest.mark.asyncio
    async def test_context_collection_error_handling(self, context_integrator, sample_issue_context):
        """Test error handling in context collection."""
        with patch.object(context_integrator.serena_client, 'analyze_complexity', side_effect=Exception("Service unavailable")):
            async with context_integrator.serena_client:
                sources = await context_integrator._gather_static_context(sample_issue_context)

            # Should still return sources, but with error information
            assert len(sources) > 0
            error_source = next((s for s in sources if "error" in s.name), None)
            assert error_source is not None
            assert error_source.content["available"] is False

    def test_context_source_data_integrity(self, context_integrator):
        """Test that ContextSource objects maintain data integrity."""
        source = ContextSource(
            name="test_source",
            content={"key": "value"},
            relevance_score=0.8,
            token_estimate=150,
            source_type="static"
        )

        assert source.name == "test_source"
        assert source.content == {"key": "value"}
        assert source.relevance_score == 0.8
        assert source.token_estimate == 150
        assert source.source_type == "static"
        assert source.timestamp is not None

    def test_enhanced_context_initialization(self):
        """Test EnhancedContext proper initialization."""
        context = EnhancedContext(
            essential_context={"key": "value"},
            full_context={"full": "data"},
            total_sources=5,
            token_budget_used=300,
            max_token_budget=2000
        )

        assert context.essential_context == {"key": "value"}
        assert context.full_context == {"full": "data"}
        assert context.total_sources == 5
        assert context.token_budget_used == 300
        assert context.max_token_budget == 2000
        assert context.quality_score == 0.0  # Default
        assert context.prioritized_sources == []  # Default