#!/usr/bin/env python3
"""
Custom MCP Client for Dopemux in Python
Connects to MCP servers over stdio and SSE transports
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import stdio_client
from mcp.types import ClientConfiguration, ServerConfiguration, StdioServerParameters

class MCPClient:
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.session: Optional[Any] = None

    async def connect_sse(self, url: str):
        """Connect to SSE-based MCP server"""
        config = ClientConfiguration(
            client_name=self.name,
            client_version=self.version
        )
        server_config = ServerConfiguration(url=url)

        self.session = await streamable_http_client(config, server_config)
        await self.session.initialize()
        print(f"✅ Connected to SSE MCP server at {url}")

    async def connect_stdio(self, command: List[str]):
        """Connect to stdio-based MCP server"""
        config = ClientConfiguration(
            client_name=self.name,
            client_version=self.version
        )
        server_params = StdioServerParameters(command=command)

        self.session = await stdio_client(config, server_params)
        await self.session.initialize()
        print(f"✅ Connected to stdio MCP server: {' '.join(command)}")

    async def list_tools(self) -> List[Any]:
        """List available tools"""
        if not self.session:
            raise Exception("Not connected to MCP server")

        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool"""
        if not self.session:
            raise Exception("Not connected to MCP server")

        result = await self.session.call_tool(tool_name, arguments)
        return result.content

    async def close(self):
        """Close the connection"""
        if self.session:
            await self.session.close()
            print("🔌 Disconnected from MCP server")


async def main():
    """Main entry point for the MCP client"""
    print("🚀 Starting Dopemux MCP Client (Python)")

    # Create client
    client = MCPClient("dopemux-mcp-client", "1.0.0")

    # Connect to servers
    servers = [
        {
            "type": "sse",
            "url": "http://localhost:3015/sse"  # Leantime bridge
        },
        {
            "type": "sse",
            "url": "http://localhost:3009/sse"  # GPT Researcher
        },
        {
            "type": "stdio",
            "command": ["python", "/Users/hue/code/dopemux-mvp/services/task-orchestrator/server.py"]
        }
    ]

    try:
        # Connect to each server
        for server in servers:
            if server["type"] == "sse":
                await client.connect_sse(server["url"])
            elif server["type"] == "stdio":
                await client.connect_stdio(server["command"])

            # List tools
            tools = await client.list_tools()
            print(f"\n📋 Tools for {server['type']} server:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")

            # Test a tool if connected
            if server["type"] == "sse" and server["url"].endswith("3015/sse"):
                try:
                    result = await client.call_tool("list_projects")
                    print(f"Projects: {result}")
                except Exception as e:
                    print(f"Tool call failed: {e}")

            await client.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print("🎉 MCP Client test completed!")


if __name__ == "__main__":
    asyncio.run(main())
