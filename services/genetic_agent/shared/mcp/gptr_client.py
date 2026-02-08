"""GPT-Researcher MCP Client."""

from typing import Dict, Any, List, Optional
from .base_client import MCPClient


class GPTRClient(MCPClient):
    """Client for GPT-Researcher MCP service."""

    def __init__(self, base_url: str, config: Any):
        super().__init__(base_url, config)
        self.service_name = "gptr-mcp"

    async def health_check(self) -> bool:
        """Check GPT-Researcher service health."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False

    async def deep_research(self, query: str) -> Dict[str, Any]:
        """Perform deep research on a query."""
        payload = {"query": query}
        return await self._make_request("deep_research", payload)

    async def quick_search(self, query: str) -> Dict[str, Any]:
        """Perform quick search."""
        payload = {"query": query}
        return await self._make_request("quick_search", payload)
