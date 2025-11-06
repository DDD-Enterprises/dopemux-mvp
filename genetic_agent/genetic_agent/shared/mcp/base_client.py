"""Base MCP client with common functionality."""

from abc import ABC, abstractmethod
import asyncio
import aiohttp
from typing import Dict, Any, Optional
import backoff
from datetime import datetime, timedelta

from ...core.config import MCPConfig


class MCPClient(ABC):
    """Base class for MCP service clients with async operations and error handling."""

    def __init__(self, base_url: str, config: MCPConfig):
        self.base_url = base_url.rstrip('/')
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_health_check = datetime.min
        self.health_status = False

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the MCP service is healthy and responding."""
        pass

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientError,
        max_tries=3,
        max_time=30
    )
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an HTTP request to the MCP service with retry logic."""
        if not await self._ensure_healthy():
            raise Exception(f"MCP service {self.base_url} is unhealthy")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def _ensure_healthy(self) -> bool:
        """Ensure service is healthy, checking periodically."""
        now = datetime.now()
        if now - self.last_health_check > timedelta(seconds=self.config.health_check_interval):
            self.health_status = await self.health_check()
            self.last_health_check = now
        return self.health_status