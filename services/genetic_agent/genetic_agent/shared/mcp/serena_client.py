"""Serena MCP client for code analysis and navigation."""

from typing import Dict, Any
from .base_client import MCPClient


class SerenaClient(MCPClient):
    """Client for Serena code intelligence and analysis."""

    async def health_check(self) -> bool:
        """Check Serena service health."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False

    async def analyze_complexity(self, file_path: str, symbol: str = "") -> Dict[str, Any]:
        """Analyze code complexity for ADHD-safe reading."""
        data = {
            "file_path": file_path,
            "symbol": symbol
        }
        return await self._make_request("analyze_complexity", data)

    async def find_symbol(self, query: str, symbol_type: str = "") -> Dict[str, Any]:
        """Find symbols by name or pattern."""
        data = {
            "query": query,
            "symbol_type": symbol_type
        }
        return await self._make_request("find_symbol", data)

    async def goto_definition(self, file_path: str, line: int, column: int) -> Dict[str, Any]:
        """Navigate to symbol definition."""
        data = {
            "file_path": file_path,
            "line": line,
            "column": column
        }
        return await self._make_request("goto_definition", data)