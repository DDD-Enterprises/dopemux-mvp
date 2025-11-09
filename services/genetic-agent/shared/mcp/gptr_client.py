"""GPT-Researcher MCP Client."""

import aiohttp
from typing import Dict, Any, List, Optional
from ..base_client import MCPClientBase

class GPTRClient(MCPClientBase):
    """Client for GPT-Researcher MCP service."""

    def __init__(self, base_url: str, config: Any):
        super().__init__(base_url, config)
        self.service_name = "gptr-mcp"

    async def deep_research(self, query: str) -> Dict[str, Any]:
        """Perform deep research on a query."""
        payload = {"query": query}
        return await self._post("deep_research", payload)

    async def quick_search(self, query: str) -> Dict[str, Any]:
        """Perform quick search."""
        payload = {"query": query}
        return await self._post("quick_search", payload)