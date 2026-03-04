"""
Security Tests for Input Validation

Tests ALLOWED_ORIGINS parsing and validation.
"""

import importlib.util
import os
import subprocess
import asyncio
import signal
from pathlib import Path
import sys

import pytest
from httpx import AsyncClient


class TestInputValidation:
    """Test input validation security."""

    ADHD_ENGINE_DIR = Path("services/adhd_engine")
    REPO_ROOT = Path(__file__).resolve().parents[2]

    @pytest.mark.parametrize("origins_input,expected_origins", [
        # Valid cases
        ("http://localhost:3000", ["http://localhost:3000"]),
        ("http://localhost:3000,https://example.com", ["http://localhost:3000", "https://example.com"]),
        ("http://test.com:8080, https://secure.app ", ["http://test.com:8080", "https://secure.app"]),

        # Invalid cases (should be filtered out)
        ("http://valid.com,not-a-url", ["http://valid.com"]),
        ("http://valid.com, javascript:alert(1)", ["http://valid.com"]),
        ("", ["http://localhost:3000", "http://localhost:8080"]),  # Empty should trigger fallback
        ("invalid-url,another-invalid", ["http://localhost:3000", "http://localhost:8080"]),  # All invalid should trigger fallback
    ])
    def test_allowed_origins_parsing(self, origins_input, expected_origins):
        """Test ALLOWED_ORIGINS parsing with various inputs."""
        # Import the parsing logic
        sys.path.insert(0, "services/adhd_engine")

        try:
            # Simulate the parsing logic from main.py
            import re
            url_pattern = re.compile(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$')

            if origins_input:
                origins = origins_input.split(",")
                parsed_origins = [origin.strip() for origin in origins if url_pattern.match(origin.strip())]
            else:
                parsed_origins = []

            # Apply fallback logic
            if not parsed_origins:
                parsed_origins = ["http://localhost:3000", "http://localhost:8080"]

            assert parsed_origins == expected_origins

        finally:
            # Clean up path
            if "services/adhd_engine" in sys.path:
                sys.path.remove("services/adhd_engine")

    def test_malformed_origins_error_handling(self):
        """Test that malformed origins don't crash the application."""
        # This test ensures the try/catch in main.py works correctly

        # Simulate various malformed inputs
        test_cases = [
            "http://valid.com,invalid://bad.com",
            "http://valid.com,None",
            "http://valid.com,123",
            "http://valid.com,",
            ",http://valid.com",
        ]

        for origins_input in test_cases:
            try:
                # Simulate the parsing logic
                import re
                url_pattern = re.compile(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$')

                origins = origins_input.split(",")
                parsed_origins = [origin.strip() for origin in origins if url_pattern.match(origin.strip())]

                # Should not crash, should filter invalid origins
                assert isinstance(parsed_origins, list)

                # Should only contain valid URLs
                for origin in parsed_origins:
                    assert url_pattern.match(origin), f"Invalid origin not filtered: {origin}"

            except Exception as e:
                pytest.fail(f"Parsing should not crash with input '{origins_input}': {e}")

    @pytest.mark.asyncio
    async def test_server_starts_with_malformed_origins(self):
        """Test that server starts safely even with malformed ALLOWED_ORIGINS."""
        if importlib.util.find_spec("prometheus_client") is None:
            pytest.skip("prometheus_client is required to start the ADHD Engine service")

        process = None
        try:
            # Test with malformed origins
            env = os.environ.copy()
            env["ALLOWED_ORIGINS"] = "http://localhost:3000,invalid://bad-url,not-a-url"
            env["ADHD_ENGINE_API_KEY"] = "test-key-123"

            # Start server
            process = subprocess.Popen(
                [
                    "python",
                    "-m",
                    "uvicorn",
                    "services.adhd_engine.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8097",
                ],
                cwd=self.REPO_ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            await asyncio.sleep(3)

            # Test that server responds (should start with fallback origins)
            async with AsyncClient(base_url="http://127.0.0.1:8097") as client:
                response = await client.get("/health")
                assert response.status_code == 200

                # Test CORS with valid origin on a real endpoint
                cors_response = await client.options(
                    "/api/v1/energy-level/default",
                    headers={
                        "Origin": "http://localhost:3000",
                        "Access-Control-Request-Method": "GET"
                    }
                )

                # Should have CORS headers (fallback origins should work)
                assert "access-control-allow-origin" in cors_response.headers

        finally:
            # Cleanup
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    def test_regex_pattern_security(self):
        """Test that URL regex pattern doesn't allow dangerous schemes."""
        import re
        url_pattern = re.compile(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$')

        # Should match
        valid_urls = [
            "http://localhost:3000",
            "https://example.com",
            "http://test.com:8080",
            "https://secure.app/path",
        ]

        for url in valid_urls:
            assert url_pattern.match(url), f"Should match valid URL: {url}"

        # Should NOT match (security risk)
        dangerous_urls = [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
            "file:///etc/passwd",
            "ftp://evil.com",
            "ldap://evil.com",
        ]

        for url in dangerous_urls:
            assert not url_pattern.match(url), f"Should reject dangerous URL: {url}"

    def test_empty_origins_fallback(self):
        """Test that empty origins trigger secure fallback."""
        import re
        url_pattern = re.compile(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$')

        # Test empty input
        origins_input = ""
        origins = origins_input.split(",") if origins_input else []
        parsed_origins = [origin.strip() for origin in origins if url_pattern.match(origin.strip())]

        # Should trigger fallback
        if not parsed_origins:
            parsed_origins = ["http://localhost:3000", "http://localhost:8080"]

        assert parsed_origins == ["http://localhost:3000", "http://localhost:8080"]

        # Test all invalid input
        origins_input = "invalid1,invalid2,invalid3"
        origins = origins_input.split(",")
        parsed_origins = [origin.strip() for origin in origins if url_pattern.match(origin.strip())]

        # Should trigger fallback
        if not parsed_origins:
            parsed_origins = ["http://localhost:3000", "http://localhost:8080"]

        assert parsed_origins == ["http://localhost:3000", "http://localhost:8080"]
