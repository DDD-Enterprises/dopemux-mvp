"""
Rate Limiting for DopeconBridge

Implements sliding window rate limiting to prevent abuse:
- Per-user limits: 100 requests/minute
- Per-workspace limits: 1000 requests/minute
- Redis-backed for distributed rate limiting
- Returns retry-after for 429 responses

Features:
- Sliding window algorithm (precise)
- Redis sorted sets for efficient cleanup
- Dual-level limits (user + workspace)
- Configurable limits per use case
- ADHD-friendly: Clear feedback on rate limits
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, limit_type: str, retry_after_seconds: int):
        self.limit_type = limit_type
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Rate limit exceeded ({limit_type}). Retry after {retry_after_seconds} seconds."
        )


class RateLimiter:
    """
    Sliding window rate limiter using Redis sorted sets.

    Uses Redis ZSET with timestamps as scores for precise sliding window.
    Automatically cleans up old entries to prevent memory growth.

    Example:
        limiter = RateLimiter(redis_client)

        allowed, retry_after = await limiter.check_limit(
            user_id="user-123",
            workspace_id="workspace-abc"
        )

        if not allowed:
            raise RateLimitExceeded("user", retry_after)
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        user_limit_per_minute: int = 100,
        workspace_limit_per_minute: int = 1000,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiter.

        Args:
            redis_client: Async Redis client
            user_limit_per_minute: Max requests per user per minute (default: 100)
            workspace_limit_per_minute: Max requests per workspace per minute (default: 1000)
            window_seconds: Sliding window size in seconds (default: 60)
        """
        self.redis_client = redis_client
        self.user_limit = user_limit_per_minute
        self.workspace_limit = workspace_limit_per_minute
        self.window_seconds = window_seconds

        # Metrics
        self.checks_performed = 0
        self.user_limits_exceeded = 0
        self.workspace_limits_exceeded = 0

    async def check_limit(
        self,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limits.

        Checks both user and workspace limits (if provided).

        Args:
            user_id: Optional user identifier
            workspace_id: Optional workspace identifier

        Returns:
            Tuple of (allowed: bool, retry_after_seconds: int)
            - If allowed=True, retry_after=0
            - If allowed=False, retry_after indicates seconds to wait
        """
        self.checks_performed += 1

        current_time = time.time()
        window_start = current_time - self.window_seconds

        # Check user limit
        if user_id:
            user_allowed, user_retry = await self._check_single_limit(
                key=f"ratelimit:user:{user_id}",
                limit=self.user_limit,
                window_start=window_start,
                current_time=current_time
            )

            if not user_allowed:
                self.user_limits_exceeded += 1
                return False, user_retry

        # Check workspace limit
        if workspace_id:
            workspace_allowed, workspace_retry = await self._check_single_limit(
                key=f"ratelimit:workspace:{workspace_id}",
                limit=self.workspace_limit,
                window_start=window_start,
                current_time=current_time
            )

            if not workspace_allowed:
                self.workspace_limits_exceeded += 1
                return False, workspace_retry

        return True, 0

    async def _check_single_limit(
        self,
        key: str,
        limit: int,
        window_start: float,
        current_time: float
    ) -> Tuple[bool, int]:
        """
        Check single rate limit using Redis sorted set.

        Args:
            key: Redis key for this limit
            limit: Maximum requests in window
            window_start: Start of sliding window (timestamp)
            current_time: Current timestamp

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        try:
            # Remove old entries outside window
            await self.redis_client.zremrangebyscore(
                key,
                '-inf',
                window_start
            )

            # Count requests in current window
            count = await self.redis_client.zcard(key)

            if count >= limit:
                # Rate limit exceeded
                # Calculate retry_after based on oldest entry in window
                oldest_entries = await self.redis_client.zrange(
                    key,
                    0,
                    0,
                    withscores=True
                )

                if oldest_entries:
                    oldest_timestamp = oldest_entries[0][1]
                    retry_after = int(oldest_timestamp + self.window_seconds - current_time) + 1
                else:
                    retry_after = self.window_seconds

                return False, max(1, retry_after)

            # Add current request to window
            await self.redis_client.zadd(
                key,
                {str(current_time): current_time}
            )

            # Set expiry to window size + buffer
            await self.redis_client.expire(key, self.window_seconds + 10)

            return True, 0

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis unavailable
            return True, 0

    async def record_request(self, user_id: Optional[str] = None, workspace_id: Optional[str] = None):
        """
        Record a request (increments counters without checking).

        Use for recording after check_limit() has already passed.

        Args:
            user_id: Optional user identifier
            workspace_id: Optional workspace identifier
        """
        current_time = time.time()

        if user_id:
            key = f"ratelimit:user:{user_id}"
            try:
                await self.redis_client.zadd(key, {str(current_time): current_time})
                await self.redis_client.expire(key, self.window_seconds + 10)
            except Exception as e:
                logger.error(f"Failed to record user request: {e}")

        if workspace_id:
            key = f"ratelimit:workspace:{workspace_id}"
            try:
                await self.redis_client.zadd(key, {str(current_time): current_time})
                await self.redis_client.expire(key, self.window_seconds + 10)
            except Exception as e:
                logger.error(f"Failed to record workspace request: {e}")

    async def get_current_usage(
        self,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get current usage for user and/or workspace.

        Args:
            user_id: Optional user identifier
            workspace_id: Optional workspace identifier

        Returns:
            Dictionary with current request counts
        """
        window_start = time.time() - self.window_seconds
        usage = {}

        if user_id:
            key = f"ratelimit:user:{user_id}"
            try:
                await self.redis_client.zremrangebyscore(key, '-inf', window_start)
                count = await self.redis_client.zcard(key)
                usage["user"] = count
                usage["user_limit"] = self.user_limit
                usage["user_remaining"] = max(0, self.user_limit - count)
            except Exception as e:
                logger.error(f"Failed to get user usage: {e}")

        if workspace_id:
            key = f"ratelimit:workspace:{workspace_id}"
            try:
                await self.redis_client.zremrangebyscore(key, '-inf', window_start)
                count = await self.redis_client.zcard(key)
                usage["workspace"] = count
                usage["workspace_limit"] = self.workspace_limit
                usage["workspace_remaining"] = max(0, self.workspace_limit - count)
            except Exception as e:
                logger.error(f"Failed to get workspace usage: {e}")

        return usage

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiter metrics"""
        total_exceeded = self.user_limits_exceeded + self.workspace_limits_exceeded
        exceeded_rate = (
            (total_exceeded / self.checks_performed * 100)
            if self.checks_performed > 0
            else 0.0
        )

        return {
            "checks_performed": self.checks_performed,
            "user_limits_exceeded": self.user_limits_exceeded,
            "workspace_limits_exceeded": self.workspace_limits_exceeded,
            "total_limits_exceeded": total_exceeded,
            "exceeded_rate_percent": round(exceeded_rate, 2),
            "user_limit_per_minute": self.user_limit,
            "workspace_limit_per_minute": self.workspace_limit,
            "window_seconds": self.window_seconds
        }

    def reset_metrics(self):
        """Reset metrics counters"""
        self.checks_performed = 0
        self.user_limits_exceeded = 0
        self.workspace_limits_exceeded = 0
