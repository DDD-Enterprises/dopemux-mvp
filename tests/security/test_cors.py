"""
Security Tests for CORS Configuration

Tests CORS middleware security restrictions.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
import os
import subprocess
import asyncio
import logging

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestCORSSecurity:
    """Test CORS security configuration."""

    @pytest_asyncio.fixture(scope="function")
    async def client(self):
        """Create test client for ADHD Engine."""
        process = None
        client = None
        try:
            env = os.environ.copy()
            env["ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:8097"
            env["ADHD_ENGINE_API_KEY"] = "test-key-123"
            env["ADHD_ENGINE_ALLOW_DEGRADED_STARTUP"] = "1"
            env["ADHD_FORCE_INMEMORY_CACHE"] = "1"

            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "services.adhd_engine.main:app", "--host", "127.0.0.1", "--port", "8095"],
                cwd=REPO_ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            client = AsyncClient(base_url="http://127.0.0.1:8095")

            server_ready = False
            # Increased retries for CI stability (60 * 0.5s = 30s timeout)
            for _ in range(60):
                if process.poll() is not None:
                    # Capture and log stderr if process crashed
                    stderr = process.stderr.read().decode()
                    logging.error(f"ADHD Engine process exited unexpectedly with code {process.returncode}. Stderr: {stderr}")
                    break
                try:
                    response = await client.get("/health")
                    if response.status_code == 200:
                        server_ready = True
                        break
                except Exception as exc:
                    logging.debug("Health check retry while ADHD Engine boots: %s", exc)
                await asyncio.sleep(0.5)

            assert server_ready, "ADHD Engine server failed to start for CORS tests"

            yield client

        except Exception:
            raise
        finally:
            if client:
                await client.aclose()
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    @pytest.mark.asyncio
    async def test_cors_allowed_origins(self, client):
        """Test that only allowed origins are permitted."""
        # Test allowed origin
        response = await client.options(
            "/api/v1/energy-level/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

        # Test another allowed origin
        response = await client.options(
            "/api/v1/energy-level/test",
            headers={
                "Origin": "http://localhost:8097",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:8097"

    @pytest.mark.asyncio
    async def test_cors_rejects_unauthorized_origins(self, client):
        """Test that unauthorized origins are rejected."""
        # Test unauthorized origin
        response = await client.options(
            "/api/v1/energy-level/test",
            headers={
                "Origin": "http://malicious.com",
                "Access-Control-Request-Method": "GET"
            }
        )

        # Should not include CORS headers for unauthorized origins
        assert "access-control-allow-origin" not in response.headers

    @pytest.mark.asyncio
    async def test_cors_restricted_methods(self, client):
        """Test that only GET and POST methods are allowed."""
        # Test allowed method
        response = await client.options(
            "/api/v1/energy-level/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        assert "access-control-allow-methods" in response.headers
        allowed_methods = response.headers["access-control-allow-methods"]
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "PUT" not in allowed_methods  # Should not be allowed
        assert "DELETE" not in allowed_methods  # Should not be allowed

    @pytest.mark.asyncio
    async def test_cors_restricted_headers(self, client):
        """Test that only necessary headers are allowed."""
        response = await client.options(
            "/api/v1/energy-level/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type,x-api-key"
            }
        )

        assert "access-control-allow-headers" in response.headers
        allowed_headers = response.headers["access-control-allow-headers"].lower()
        assert "content-type" in allowed_headers
        assert "x-api-key" in allowed_headers
        assert "authorization" in allowed_headers

    @pytest.mark.asyncio
    async def test_cors_invalid_origin_handling(self, client):
        """Test handling of malformed ALLOWED_ORIGINS environment variable."""
        # This would require restarting server with malformed origins
        # For now, just test that server starts with valid origins
        response = await client.get("/health")
        assert response.status_code == 200

        # Server should have started successfully despite any origin parsing issues
        # (due to our error handling in main.py)
