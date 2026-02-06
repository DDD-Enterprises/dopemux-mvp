"""
Tests for Query Complexity Budgets
Validates complexity scoring and budget enforcement
"""

import asyncio
import pytest
import time

redis = pytest.importorskip("redis.asyncio", reason="redis package not installed")

from complexity_scorer import ComplexityScorer, ComplexityBudgetExceeded


class TestComplexityScorer:
    """Test ComplexityScorer budget system"""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        client = redis.from_url(
            "redis://localhost:6379",
            db=11,  # Complexity test database
            decode_responses=True
        )

        # Clear test database
        await client.flushdb()

        yield client

        # Cleanup
        await client.flushdb()
        await client.aclose()

    @pytest.fixture
    def scorer(self, redis_client):
        """Create ComplexityScorer with low budget for testing"""
        return ComplexityScorer(
            redis_client=redis_client,
            budget_per_minute=100,  # Low budget for testing
            window_seconds=60
        )

    def test_scores_simple_query_correctly(self, scorer):
        """Test complexity scoring for simple query"""
        # 1 pattern, 100 events
        score = scorer.score_pattern_query(pattern_count=1, event_count=100)

        # Expected: 10 (pattern) + 10 (100/10 events) = 20
        assert score == 20

    def test_scores_complex_query_correctly(self, scorer):
        """Test complexity scoring for complex query"""
        # 7 patterns, 1000 events, depth 3
        score = scorer.score_pattern_query(
            pattern_count=7,
            event_count=1000,
            graph_depth=3
        )

        # Expected: 70 (patterns) + 100 (1000/10 events) + 15 (3*5 graph) = 185
        assert score == 185

    @pytest.mark.asyncio
    async def test_allows_query_under_budget(self, scorer):
        """Test that queries under budget are allowed"""
        allowed, usage, retry_after = await scorer.check_budget("user1", 50)

        assert allowed is True
        assert usage == 50  # Points used
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_blocks_query_over_budget(self, scorer):
        """Test that queries over budget are blocked"""
        # Use up most of budget
        await scorer.check_budget("user1", 80)

        # Try to use 50 more (would exceed 100)
        allowed, usage, retry_after = await scorer.check_budget("user1", 50)

        assert allowed is False
        assert usage == 80  # Current usage
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_different_users_have_separate_budgets(self, scorer):
        """Test that different users have independent budgets"""
        # User 1: Use up budget
        await scorer.check_budget("user1", 100)

        # User 1: Should be blocked
        allowed1, _, _ = await scorer.check_budget("user1", 10)
        assert allowed1 is False

        # User 2: Should still have full budget
        allowed2, _, _ = await scorer.check_budget("user2", 10)
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_budget_resets_after_window(self, scorer):
        """Test that budget resets after window expires"""
        # Create scorer with short window
        short_scorer = ComplexityScorer(
            redis_client=scorer.redis_client,
            budget_per_minute=100,
            window_seconds=2  # 2 second window
        )

        # Use up budget
        await short_scorer.check_budget("user1", 100)

        # Should be blocked
        allowed, _, _ = await short_scorer.check_budget("user1", 10)
        assert allowed is False

        # Wait for window to expire
        await asyncio.sleep(2.1)

        # Should be allowed now
        allowed, usage, _ = await short_scorer.check_budget("user1", 10)
        assert allowed is True
        assert usage == 10  # Fresh budget

    @pytest.mark.asyncio
    async def test_get_current_budget_usage(self, scorer):
        """Test getting current budget usage"""
        # Use some budget
        await scorer.check_budget("user1", 30)
        await scorer.check_budget("user1", 25)

        usage = await scorer.get_current_budget_usage("user1")

        assert usage["used"] == 55
        assert usage["budget"] == 100
        assert usage["remaining"] == 45

    def test_suggests_simpler_queries(self, scorer):
        """Test suggestion generation for expensive queries"""
        # High complexity query
        suggestions = scorer.suggest_simpler_query(complexity_points=600)

        assert len(suggestions) > 0
        assert any("event window" in s.lower() for s in suggestions)
        assert any("pattern" in s.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, scorer):
        """Test complexity scorer metrics"""
        scorer.reset_metrics()

        scorer.score_pattern_query(1, 100)
        scorer.score_pattern_query(3, 500)
        scorer.score_pattern_query(7, 1000)

        await scorer.check_budget("user1", 50)
        await scorer.check_budget("user1", 60)  # Would exceed

        metrics = scorer.get_metrics()

        assert metrics["queries_scored"] == 3
        assert metrics["budgets_exceeded"] == 1
        assert metrics["average_complexity"] > 0
        assert metrics["budget_per_minute"] == 100

    @pytest.mark.asyncio
    async def test_handles_redis_errors_gracefully(self):
        """Test graceful failure when Redis unavailable"""
        bad_client = redis.from_url("redis://localhost:9999", decode_responses=True)

        scorer = ComplexityScorer(bad_client)

        # Should fail open (allow query) when Redis unavailable
        allowed, usage, retry_after = await scorer.check_budget("user1", 100)

        assert allowed is True, "Should fail open when Redis unavailable"
        assert usage == 0
        assert retry_after == 0

        await bad_client.aclose()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
