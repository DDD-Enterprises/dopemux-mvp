"""
Rate Limiting Middleware for ADHD Engine

Implements token bucket algorithm for API rate limiting.
Configurable limits per endpoint to prevent abuse.
"""

import time
import asyncio
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Each bucket refills at a constant rate up to a maximum capacity.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.

    Configurable limits per endpoint with IP-based buckets.
    """

    def __init__(self, app, default_capacity: int = 100, default_refill_rate: float = 10.0):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI app
            default_capacity: Default bucket capacity
            default_refill_rate: Default refill rate (tokens/second)
        """
        super().__init__(app)
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate

        # Per-endpoint rate limits (path -> (capacity, refill_rate))
        self.endpoint_limits: Dict[str, Tuple[int, float]] = {
            "/api/v1/assess-task": (50, 5.0),  # 50 requests, 5 per second
            "/api/v1/user-profile": (20, 2.0),  # 20 requests, 2 per second
            "/api/v1/energy-level": (200, 20.0),  # 200 requests, 20 per second
            "/api/v1/attention-state": (200, 20.0),  # 200 requests, 20 per second
            "/api/v1/recommend-break": (100, 10.0),  # 100 requests, 10 per second
        }

        # IP-based token buckets (ip -> path -> bucket)
        self.buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.

        Checks X-Forwarded-For, X-Real-IP, then remote address.
        """
        # Check forwarded headers (for proxy/load balancer scenarios)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP if multiple
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to remote address
        client_host = getattr(request.client, 'host', None) if request.client else None
        return client_host or "unknown"

    def _get_bucket(self, client_ip: str, path: str) -> TokenBucket:
        """
        Get or create token bucket for client IP and path.

        Args:
            client_ip: Client IP address
            path: Request path

        Returns:
            TokenBucket instance
        """
        if path not in self.buckets[client_ip]:
            capacity, refill_rate = self.endpoint_limits.get(
                path, (self.default_capacity, self.default_refill_rate)
            )
            self.buckets[client_ip][path] = TokenBucket(capacity, refill_rate)

        return self.buckets[client_ip][path]

    async def dispatch(self, request: Request, call_next):
        """
        Middleware dispatch method.

        Checks rate limit before processing request.
        """
        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Skip rate limiting for health checks and docs
        if path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get appropriate bucket for this client and endpoint
        bucket = self._get_bucket(client_ip, path)

        # Check if request can proceed
        if not bucket.consume():
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")

            # Calculate retry-after time
            capacity, refill_rate = self.endpoint_limits.get(
                path, (self.default_capacity, self.default_refill_rate)
            )
            retry_after = int(capacity / refill_rate)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)}
            )

        # Proceed with request
        response = await call_next(request)
        return response


# Factory function for easy integration
def create_rate_limit_middleware(
    capacity: int = 100,
    refill_rate: float = 10.0
) -> RateLimitMiddleware:
    """
    Create rate limiting middleware with custom defaults.

    Args:
        capacity: Default bucket capacity
        refill_rate: Default refill rate (tokens/second)

    Returns:
        Configured RateLimitMiddleware instance
    """
    class ConfiguredRateLimitMiddleware(RateLimitMiddleware):
        def __init__(self, app):
            super().__init__(app, capacity, refill_rate)

    return ConfiguredRateLimitMiddleware