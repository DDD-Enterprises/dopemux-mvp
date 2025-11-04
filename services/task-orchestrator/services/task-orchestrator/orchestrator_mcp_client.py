"""
MCP Client for Task Orchestrator
Provides access to MCP servers (ConPort, Serena, etc.) for the orchestrator
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]

class MCPClient:
    """
    MCP Client that connects to MCP servers and provides tools to orchestrator
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.tools: Dict[str, MCPTool] = {}
        self.conport_url = "http://localhost:3010"  # ConPort MCP server
        self.serena_url = "http://localhost:3012"   # Serena MCP server
        self.zen_url = "http://localhost:3013"      # Zen MCP server

    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def connect_conport(self) -> Dict[str, Any]:
        """
        Connect to ConPort MCP server and get available tools
        Returns a mock tools object that can be used by the orchestrator
        """
        try:
            # For now, return a mock tools object with ConPort methods
            # In production, this would connect to actual MCP server via HTTP/SSE

            class MockConPortTools:
                async def mcp__conport__log_progress(self, **kwargs):
                    """Mock ConPort log_progress tool"""
                    logger.info(f"Mock ConPort log_progress: {kwargs}")
                    return {"id": 999, "status": "success"}

                async def mcp__conport__update_progress(self, **kwargs):
                    """Mock ConPort update_progress tool"""
                    logger.info(f"Mock ConPort update_progress: {kwargs}")
                    return {"status": "success"}

                async def mcp__conport__get_decisions(self, **kwargs):
                    """Mock ConPort get_decisions tool"""
                    logger.info(f"Mock ConPort get_decisions: {kwargs}")
                    return {"decisions": [], "status": "success"}

                async def mcp__conport__semantic_search(self, **kwargs):
                    """Mock ConPort semantic_search tool"""
                    logger.info(f"Mock ConPort semantic_search: {kwargs}")
                    return {"results": [], "status": "success"}

            return MockConPortTools()

        except Exception as e:
            logger.error(f"Failed to connect to ConPort MCP server: {e}")
            return None

    async def get_mcp_tools(self) -> Optional[Any]:
        """
        Get MCP tools object for the orchestrator
        This provides the mcp_tools parameter needed by EnhancedTaskOrchestrator
        """
        try:
            # Get ConPort tools (primary focus for sync)
            conport_tools = await self.connect_conport()

            if conport_tools:
                # Return tools object that orchestrator can use
                return conport_tools
            else:
                logger.warning("No MCP tools available")
                return None

        except Exception as e:
            logger.error(f"Failed to get MCP tools: {e}")
            return None

# Global MCP client instance
_mcp_client: Optional[MCPClient] = None

async def get_mcp_client() -> MCPClient:
    """Get or create global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
        await _mcp_client.initialize()
    return _mcp_client

async def get_mcp_tools() -> Optional[Any]:
    """Get MCP tools for orchestrator initialization"""
    client = await get_mcp_client()
    return await client.get_mcp_tools()