import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

from dashboard.api_client import APIClient, APIConfig, CacheEntry

mock_httpx.AsyncClient.return_value.aclose = AsyncMock()  # Ensure aclose is awaitable
    def setUp(self):
        self.api_config = APIConfig(
            base_url="http://api.example.com",
            timeout=1.0,
            max_retries=3,
            retry_delay=0.1
        )
        self.api_client = APIClient(self.api_config)

    async def asyncTearDown(self):
        # We need to make sure the mock client's aclose is awaitable
        # The constructor of APIClient creates self.client = httpx.AsyncClient(...)
        # which returns a MagicMock since we mocked httpx.AsyncClient
        await self.api_client.close()

    async def test_api_client_initialization(self):
        client = APIClient(self.api_config)
        self.assertEqual(client.config, self.api_config)
        self.assertEqual(client._cache, {})
        self.assertEqual(client._in_flight, {})

    async def test_get_success_no_cache(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        with patch.object(self.api_client.client, 'get', AsyncMock(return_value=mock_response)) as mock_get:
            result = await self.api_client.get("/test")

            self.assertEqual(result, {"key": "value"})
            mock_get.assert_called_once_with("http://api.example.com/test", params=None)
            # Verify it's cached
            self.assertIn("/test", self.api_client._cache)
            self.assertEqual(self.api_client._cache["/test"].data, {"key": "value"})

    async def test_get_cache_hit(self):
        self.api_client._store_in_cache("test_key", {"cached": "data"})

        with patch.object(self.api_client.client, 'get', AsyncMock()) as mock_get:
            result = await self.api_client.get("/test", cache_key="test_key")

            self.assertEqual(result, {"cached": "data"})
            mock_get.assert_not_called()

    async def test_get_cache_expired(self):
        # Store expired entry
        expired_at = datetime.now() - timedelta(seconds=60)
        self.api_client._cache["test_key"] = CacheEntry(
            data={"old": "data"},
            cached_at=expired_at,
            ttl_seconds=30
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"new": "data"}

        with patch.object(self.api_client.client, 'get', AsyncMock(return_value=mock_response)) as mock_get:
            result = await self.api_client.get("/test", cache_key="test_key")

            self.assertEqual(result, {"new": "data"})
            mock_get.assert_called_once()
            self.assertEqual(self.api_client._cache["test_key"].data, {"new": "data"})

    async def test_get_deduplication(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"async": "data"}

        # Slow down the request to ensure it stays in flight
        async def slow_get(*args, **kwargs):
            await asyncio.sleep(0.1)
            return mock_response

        with patch.object(self.api_client.client, 'get', side_effect=slow_get) as mock_get:
            # Launch two concurrent requests
            results = await asyncio.gather(
                self.api_client.get("/test"),
                self.api_client.get("/test")
            )

            self.assertEqual(results[0], {"async": "data"})
            self.assertEqual(results[1], {"async": "data"})
            # Should only be called once
            self.assertEqual(mock_get.call_count, 1)

    async def test_get_retry_logic(self):
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {"success": True}

        # Fail twice, then succeed
        mock_get = AsyncMock()

        mock_get.side_effect = [
            mock_httpx.TimeoutException("timeout"),
            Exception("random error"),
            mock_response_ok
        ]

        self.api_client.client.get = mock_get

        with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
            result = await self.api_client.get("/retry-test")

            self.assertEqual(result, {"success": True})
            self.assertEqual(mock_get.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 2)

    async def test_get_all_retries_fail_with_fallback(self):
        self.api_client.client.get = AsyncMock(side_effect=mock_httpx.TimeoutException("timeout"))
        fallback = {"fallback": "data"}

        with patch('asyncio.sleep', AsyncMock()):
            result = await self.api_client.get("/fail", fallback_data=fallback)

            self.assertEqual(result, fallback)
            self.assertEqual(self.api_client.client.get.call_count, self.api_client.config.max_retries)

    async def test_post_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"posted": "ok"}

        with patch.object(self.api_client.client, 'post', AsyncMock(return_value=mock_response)) as mock_post:
            result = await self.api_client.post("/post-test", json_data={"data": 123})

            self.assertEqual(result, {"posted": "ok"})
            mock_post.assert_called_once_with(
                "http://api.example.com/post-test",
                json={"data": 123}
            )
            # Post should not be cached
            self.assertNotIn("/post-test", self.api_client._cache)

    async def test_post_retry_and_fallback(self):
        self.api_client.client.post = AsyncMock(side_effect=Exception("post failed"))
        fallback = {"post_fallback": True}

        with patch('asyncio.sleep', AsyncMock()):
            result = await self.api_client.post("/post-fail", fallback_data=fallback)

            self.assertEqual(result, fallback)
            self.assertEqual(self.api_client.client.post.call_count, self.api_client.config.max_retries)

    def test_invalidate_cache(self):
        self.api_client._store_in_cache("key1", "data1")
        self.api_client._store_in_cache("key2", "data2")

        self.api_client.invalidate_cache("key1")
        self.assertNotIn("key1", self.api_client._cache)
        self.assertIn("key2", self.api_client._cache)

        self.api_client.invalidate_cache()
        self.assertEqual(self.api_client._cache, {})

    async def test_close_client(self):
        with patch.object(self.api_client.client, 'aclose', AsyncMock()) as mock_aclose:
            await self.api_client.close()
            mock_aclose.assert_called_once()

if __name__ == '__main__':
    unittest.main()
