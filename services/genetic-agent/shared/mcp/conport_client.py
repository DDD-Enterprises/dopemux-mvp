"""ConPort MCP client for decision logging and context management."""

from typing import Dict, Any
from .base_client import MCPClient


class ConPortClient(MCPClient):
    """Client for ConPort decision logging and context management."""

    async def health_check(self) -> bool:
        """Check ConPort service health."""
        try:
            # Simple health check - in production, call actual health endpoint
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False

    async def log_decision(self, summary: str, rationale: str, **kwargs) -> Dict[str, Any]:
        """Log an architectural or implementation decision."""
        data = {
            "summary": summary,
            "rationale": rationale,
            **kwargs
        }
        return await self._make_request("log_decision", data)

    async def get_active_context(self, workspace_id: str) -> Dict[str, Any]:
        """Get current active context for workspace."""
        return await self._make_request("get_active_context", {"workspace_id": workspace_id})

    async def log_progress(self, status: str, description: str, **kwargs) -> Dict[str, Any]:
        """Log progress entry."""
        data = {
            "status": status,
            "description": description,
            **kwargs
        }
        return await self._make_request("log_progress", data)