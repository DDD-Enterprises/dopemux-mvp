"""Dope-Context MCP client for semantic code search."""

from typing import Dict, Any
from .base_client import MCPClient


class DopeContextClient(MCPClient):
    """Client for Dope-Context semantic search and documentation."""

    async def health_check(self) -> bool:
        """Check Dope-Context service health."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            return False

            logger.error(f"Error: {e}")
    async def search_code(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Search code semantically."""
        data = {
            "query": query,
            "top_k": top_k
        }
        return await self._make_request("search_code", data)

    async def search_docs(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Search documentation semantically."""
        data = {
            "query": query,
            "top_k": top_k
        }
        return await self._make_request("search_docs", data)

    async def search_all(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Search both code and docs."""
        data = {
            "query": query,
            "top_k": top_k
        }
        return await self._make_request("search_all", data)