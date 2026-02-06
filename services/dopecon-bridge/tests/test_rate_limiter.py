"""
Tests for Rate Limiting System
Validates sliding window algorithm and dual-level limits
"""

import asyncio
import pytest
import time

redis = pytest.importorskip("redis.asyncio", reason="redis package not installed")

from rate_limiter import RateLimiter, RateLimitExceeded


class TestRateLimiter:
    """Test RateLimiter sliding window algorithm"""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        client = redis.from_url(
            "redis://localhost:6379",
            db=12,  # Rate limit test database
            decode_responses=True
        )

        # Clear test database
        await client.flushdb()

        yield client

        # Cleanup
        await client.flushdb()
        await client.aclose()

    @pytest.fixture
    def limiter(self, redis_client):
        """Create RateLimiter with low limits for testing"""
        return RateLimiter(
            redis_client=redis_client,
            user_limit_per_minute=5,  # Low limit for testing
            workspace_limit_per_minute=10,
            window_seconds=60
        )

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self, limiter):
        """Test that requests under limit are allowed"""
        # Make 3 requests (under limit of 5)
        for i in range(3):
            allowed, retry_after = await limiter.check_limit(user_id="user1")
            assert allowed is True, f"Request {i+1} should be allowed"
            assert retry_after == 0

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self, limiter):
        """Test that requests over limit are blocked"""
        # Make 5 requests (at limit)
        for i in range(5):
            await limiter.check_limit(user_id="user1")

        # 6th request should be blocked
        allowed, retry_after = await limiter.check_limit(user_id="user1")

        assert allowed is False, "Request over limit should be blocked"
        assert retry_after > 0, "Should provide retry_after value"

    @pytest.mark.asyncio
    async def test_different_users_have_separate_limits(self, limiter):
        """Test that different users have independent limits"""
        # User 1: Use up their limit
        for _ in range(5):
            await limiter.check_limit(user_id="user1")

        # User 1: Should be blocked
        allowed1, _ = await limiter.check_limit(user_id="user1")
        assert allowed1 is False

        # User 2: Should still be allowed
        allowed2, _ = await limiter.check_limit(user_id="user2")
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_workspace_limit_independent_of_user(self, limiter):
        """Test workspace limits enforced separately"""
        # Multiple users in same workspace
        for i in range(10):  # Workspace limit is 10
            await limiter.check_limit(
                user_id=f"user{i}",
                workspace_id="workspace1"
            )

        # 11th request should hit workspace limit
        allowed, retry_after = await limiter.check_limit(
            user_id="user99",  # Different user
            workspace_id="workspace1"  # Same workspace
        )

        assert allowed is False, "Workspace limit should be exceeded"

    @pytest.mark.asyncio
    async def test_sliding_window_allows_new_requests(self, limiter):
        """Test that old requests slide out of window"""
        # Create limiter with 2-second window for faster testing
        short_limiter = RateLimiter(
            redis_client=limiter.redis_client,
            user_limit_per_minute=3,
            window_seconds=2
        )

        # Make 3 requests (at limit)
        for _ in range(3):
            await short_limiter.check_limit(user_id="user1")

        # 4th should be blocked
        allowed, _ = await short_limiter.check_limit(user_id="user1")
        assert allowed is False

        # Wait for window to slide
        await asyncio.sleep(2.1)

        # Should be allowed now (old requests expired)
        allowed, retry_after = await short_limiter.check_limit(user_id="user1")
        assert allowed is True
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_get_current_usage(self, limiter):
        """Test getting current usage stats"""
        # Make some requests
        for _ in range(3):
            await limiter.check_limit(user_id="user1", workspace_id="workspace1")

        usage = await limiter.get_current_usage(
            user_id="user1",
            workspace_id="workspace1"
        )

        assert usage["user"] == 3
        assert usage["user_limit"] == 5
        assert usage["user_remaining"] == 2
        assert usage["workspace"] == 3
        assert usage["workspace_limit"] == 10
        assert usage["workspace_remaining"] == 7

    @pytest.mark.asyncio
    async def test_retry_after_accurate(self, limiter):
        """Test that retry_after value is accurate"""
        # Use short window for testing
        short_limiter = RateLimiter(
            redis_client=limiter.redis_client,
            user_limit_per_minute=2,
            window_seconds=5  # 5 second window
        )

        # Fill limit
        await short_limiter.check_limit(user_id="user1")
        await short_limiter.check_limit(user_id="user1")

        # Should be blocked
        allowed, retry_after = await short_limiter.check_limit(user_id="user1")

        assert allowed is False
        assert 1 <= retry_after <= 6, f"retry_after should be 1-6 seconds, got {retry_after}"

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, limiter):
        """Test rate limiter metrics"""
        limiter.reset_metrics()

        # Make allowed requests
        for _ in range(3):
            await limiter.check_limit(user_id="user1")

        # Make requests that exceed limit
        for _ in range(5):
            await limiter.check_limit(user_id="user1")  # 3-7 will exceed

        metrics = limiter.get_metrics()

        assert metrics["checks_performed"] == 8
        assert metrics["user_limits_exceeded"] == 3  # Requests 6, 7, 8
        assert metrics["user_limit_per_minute"] == 5

    @pytest.mark.asyncio
    async def test_handles_redis_errors_gracefully(self):
        """Test graceful failure when Redis unavailable"""
        # Create limiter with bad Redis client
        bad_client = redis.from_url("redis://localhost:9999", decode_responses=True)

        limiter = RateLimiter(bad_client)

        # Should fail open (allow request) when Redis unavailable
        allowed, retry_after = await limiter.check_limit(user_id="user1")

        assert allowed is True, "Should fail open when Redis unavailable"

        await bad_client.aclose()

    @pytest.mark.asyncio
    async def test_record_request_without_check(self, limiter):
        """Test recording request without prior check"""
        await limiter.record_request(user_id="user1", workspace_id="workspace1")

        usage = await limiter.get_current_usage(user_id="user1", workspace_id="workspace1")

        assert usage["user"] == 1
        assert usage["workspace"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
