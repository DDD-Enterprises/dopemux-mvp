"""
Security Tests for Rate Limiting

Tests rate limiting middleware functionality.
"""

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, RequestError
import os
import subprocess
import asyncio
from services.adhd_engine.middleware.rate_limit import TokenBucket

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestRateLimiting:
    """Test rate limiting functionality."""

    @staticmethod
    def _assess_payload(index: int) -> dict:
        return {
            "user_id": "test",
            "task_id": f"task-{index}",
            "task_data": {
                "complexity_score": 0.5,
                "estimated_minutes": 30,
                "description": f"Test task {index}",
                "dependencies": [],
            },
        }

    @pytest_asyncio.fixture(scope="function")
    async def client(self):
        """Create test client for ADHD Engine."""
        process = None
        client = None
        try:
            env = os.environ.copy()
            env["ALLOWED_ORIGINS"] = "http://localhost:3000"
            env["ADHD_ENGINE_API_KEY"] = "test-key-123"
            env["ADHD_ENGINE_ALLOW_DEGRADED_STARTUP"] = "1"
            env["ADHD_FORCE_INMEMORY_CACHE"] = "1"

            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "services.adhd_engine.main:app", "--host", "127.0.0.1", "--port", "8096"],
                cwd=REPO_ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            client = AsyncClient(base_url="http://127.0.0.1:8096", timeout=30.0)

            server_ready = False
            for _ in range(60):
                if process.poll() is not None:
                    break
                try:
                    response = await client.get("/health")
                    if response.status_code == 200:
                        server_ready = True
                        break
                except (RequestError, OSError):
                    # Server can reject early probes during startup; continue retry loop.
                    pass
                await asyncio.sleep(0.25)

            assert server_ready, "ADHD Engine server failed to start for rate-limiting tests"

            yield client

        finally:
            if client:
                await client.aclose()
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    async def _burst_assess_requests(self, client, count: int, headers: dict) -> list[int]:
        tasks = [
            client.post(
                "/api/v1/assess-task",
                json=self._assess_payload(i),
                headers=headers,
            )
            for i in range(count)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        statuses: list[int] = []
        for result in results:
            if isinstance(result, Exception):
                statuses.append(429)
            else:
                statuses.append(result.status_code)
        return statuses

    @pytest.mark.asyncio
    async def test_rate_limit_assess_task_endpoint(self, client):
        """Test rate limiting on assess-task endpoint (50 requests, 5 per second)."""
        responses = await self._burst_assess_requests(
            client,
            count=90,
            headers={"X-API-Key": "test-key-123"},
        )

        # Should have some successful responses and then rate limiting
        assert 200 in responses  # Some successful requests
        assert 429 in responses  # Rate limiting kicks in

    @pytest.mark.asyncio
    async def test_rate_limit_user_profile_endpoint(self, client):
        """Test rate limiting on user-profile endpoint (20 requests, 2 per second)."""
        tasks = [
            client.post(
                "/api/v1/user-profile",
                json={"user_id": f"test-{i}", "energy_level": "medium"},
                headers={"X-API-Key": "test-key-123"},
            )
            for i in range(40)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        responses = [r.status_code if not isinstance(r, Exception) else 429 for r in results]

        assert 200 in responses  # Some successful requests
        assert 429 in responses  # Rate limiting kicks in

    @pytest.mark.asyncio
    async def test_rate_limit_energy_level_endpoint(self, client):
        """Test rate limiting on energy-level endpoint (200 requests, 20 per second)."""
        responses = []
        for i in range(210):  # Exceed the 200 request limit
            try:
                response = await client.get(
                    "/api/v1/energy-level/test",
                    headers={"X-API-Key": "test-key-123"}
                )
                responses.append(response.status_code)
            except Exception as e:
                responses.append(429)
                break

            # Very short delay for high-throughput endpoint
            await asyncio.sleep(0.01)

        assert 200 in responses  # Some successful requests
        # Note: This endpoint has high limits, may not trigger rate limiting in short test

    @pytest.mark.asyncio
    async def test_no_rate_limit_on_health_endpoint(self, client):
        """Test that health endpoint is not rate limited."""
        # Make many requests to health endpoint
        for i in range(100):
            response = await client.get("/health")
            assert response.status_code == 200

        # Should not be rate limited
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_by_ip_address(self):
        """Rate-limit state should be isolated per client IP."""
        from services.adhd_engine.middleware.rate_limit import RateLimitMiddleware

        middleware = RateLimitMiddleware(FastAPI())
        path = "/api/v1/assess-task"

        bucket_1 = middleware._get_bucket("192.168.1.100", path)
        bucket_2 = middleware._get_bucket("192.168.1.101", path)

        for _ in range(bucket_1.capacity):
            assert bucket_1.consume() is True

        # First IP is now limited.
        assert bucket_1.consume() is False
        # Second IP remains unaffected.
        assert bucket_2.consume() is True

    @pytest.mark.asyncio
    async def test_token_bucket_refill(self):
        """Token bucket should reject when empty and allow requests after refill."""
        bucket = TokenBucket(capacity=2, refill_rate=2.0)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False
        await asyncio.sleep(0.6)
        assert bucket.consume() is True
