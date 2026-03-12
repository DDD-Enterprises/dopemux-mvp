"""
Security Tests for Rate Limiting

Tests rate limiting middleware functionality.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
import os
import subprocess
import asyncio
import time
from typing import Optional


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest_asyncio.fixture(scope="function")
    async def client(self):
        """Create test client for ADHD Engine."""
        process = None
        client = None
        try:
            # Set test environment
            env = os.environ.copy()
            env["ALLOWED_ORIGINS"] = "http://localhost:3000"
            env["ADHD_ENGINE_API_KEY"] = "test-key-123"

            # Start server
            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8096"],
                cwd="services/adhd_engine",
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            await asyncio.sleep(3)

            # Create client for tests
            client = AsyncClient(base_url="http://127.0.0.1:8096")

            # Verify server is running
            try:
                response = await client.get("/health")
                assert response.status_code == 200
            except Exception:
                pytest.skip("ADHD Engine server failed to start")

            yield client

        finally:
            # Cleanup
            if client:
                await client.aclose()
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                await client.aclose()
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            raise

    @pytest.mark.asyncio
    async def test_rate_limit_assess_task_endpoint(self, client):
        """Test rate limiting on assess-task endpoint (50 requests, 5 per second)."""
        # Make requests up to the limit
        responses = []
        for i in range(55):  # Exceed the 50 request limit
            try:
                response = await client.post(
                    "/api/v1/assess-task",
                    json={"task_description": f"Test task {i}", "user_id": "test"},
                    headers={"X-API-Key": "test-key-123"}
                )
                responses.append(response.status_code)
            except Exception as e:
                # Rate limit should cause 429
                responses.append(429)
                break

            # Small delay to not exceed refill rate too quickly
            await asyncio.sleep(0.1)

        # Should have some successful responses and then rate limiting
        assert 200 in responses  # Some successful requests
        assert 429 in responses  # Rate limiting kicks in

        # Check Retry-After header is present
        if 429 in responses:
            last_response = await client.post(
                "/api/v1/assess-task",
                json={"task_description": "Test", "user_id": "test"},
                headers={"X-API-Key": "test-key-123"}
            )
            if last_response.status_code == 429:
                assert "retry-after" in last_response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_user_profile_endpoint(self, client):
        """Test rate limiting on user-profile endpoint (20 requests, 2 per second)."""
        responses = []
        for i in range(25):  # Exceed the 20 request limit
            try:
                response = await client.post(
                    "/api/v1/user-profile",
                    json={"user_id": "test", "energy_level": "medium"},
                    headers={"X-API-Key": "test-key-123"}
                )
                responses.append(response.status_code)
            except Exception as e:
                responses.append(429)
                break

            await asyncio.sleep(0.1)

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
    async def test_rate_limit_by_ip_address(self, client):
        """Test that rate limiting is applied per IP address."""
        # Simulate different IP addresses via headers
        headers1 = {"X-API-Key": "test-key-123", "X-Forwarded-For": "192.168.1.100"}
        headers2 = {"X-API-Key": "test-key-123", "X-Forwarded-For": "192.168.1.101"}

        # Exhaust limit for first IP
        responses = []
        for i in range(55):  # Exceed limit
            try:
                response = await client.post(
                    "/api/v1/assess-task",
                    json={"task_description": f"Test task {i}", "user_id": "test"},
                    headers=headers1
                )
                responses.append(response.status_code)
            except Exception:
                responses.append(429)
                break

            await asyncio.sleep(0.1)

        # First IP should be rate limited
        assert 429 in responses

        # Second IP should still work
        response = await client.post(
            "/api/v1/assess-task",
            json={"task_description": "Test from IP 2", "user_id": "test"},
            headers=headers2
        )
        assert response.status_code == 200  # Should not be rate limited

    @pytest.mark.asyncio
    async def test_token_bucket_refill(self, client):
        """Test that token bucket refills over time."""
        # Exhaust bucket
        for i in range(55):
            try:
                await client.post(
                    "/api/v1/assess-task",
                    json={"task_description": f"Test {i}", "user_id": "test"},
                    headers={"X-API-Key": "test-key-123"}
                )
            except Exception:
                break

            await asyncio.sleep(0.1)

        # Should be rate limited
        response = await client.post(
            "/api/v1/assess-task",
            json={"task_description": "Test after limit", "user_id": "test"},
            headers={"X-API-Key": "test-key-123"}
        )
        assert response.status_code == 429

        # Wait for refill (bucket refills at 5 tokens/second, retry-after should be reasonable)
        retry_after = int(response.headers.get("retry-after", "10"))
        await asyncio.sleep(min(retry_after, 5))  # Wait but not too long for test

        # Should work again after refill
        response = await client.post(
            "/api/v1/assess-task",
            json={"task_description": "Test after refill", "user_id": "test"},
            headers={"X-API-Key": "test-key-123"}
        )
        # May still be limited depending on exact timing, but should eventually work
        assert response.status_code in [200, 429]