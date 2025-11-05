"""
Rate limiting middleware for ADHD Accommodation Engine.

Implements simple IP-based rate limiting to prevent abuse.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Any
import time
import os
from collections import defaultdict
from typing import Dict, Optional

# Simple in-memory rate limiter (use Redis in production)
class RateLimiter:
    """
    Simple IP-based rate limiter using in-memory storage.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if request from client IP is allowed.

        Args:
            client_ip: Client IP address

        Returns:
            True if request allowed, False if rate limited
        """
        now = time.time()

        # Remove old requests outside window
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if now - timestamp < self.window_seconds
        ]

        # Check if under limit
        if len(self.requests[client_ip]) < self.max_requests:
            self.requests[client_ip].append(now)
            return True

        return False

    def get_usage(self, client_ip: str) -> Dict[str, Any]:
        """
        Get current usage statistics for client IP.
        """
        now = time.time()
        recent_requests = len([
            ts for ts in self.requests[client_ip]
            if now - ts < self.window_seconds
        ])

        return {
            "current_usage": recent_requests,
            "max_allowed": self.max_requests,
            "window_seconds": self.window_seconds,
            "rate_limited": recent_requests >= self.max_requests
        }


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_MAX", "100")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60"))
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting requests.
    """

    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or ["/health", "/"]

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """
        Intercept requests and apply rate limiting.
        """
        # Skip rate limiting for exempt paths
        if any(path in request.url.path for path in self.exempt_paths):
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host

        # Check rate limit
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "usage": rate_limiter.get_usage(client_ip),
                    "retry_after": rate_limiter.window_seconds
                }
            )

        # Continue with request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            rate_limiter.max_requests - len(rate_limiter.requests[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + rate_limiter.window_seconds))

        return response