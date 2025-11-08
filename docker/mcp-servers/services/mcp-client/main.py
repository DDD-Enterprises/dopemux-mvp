#!/usr/bin/env python3
"""
Custom MCP Client for Dopemux
Connects to MCP servers over stdio transport and provides tool execution capabilities
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Dict, List, Any, Optional
import aiohttp


class MCPClient:
    """MCP client for stdio-based MCP servers"""

    def __init__(self, server_name: str, command: str, args: List[str], env: Dict[str, str]):
        self.server_name = server_name
        self.command = command
        self.args = args
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self.session_id: Optional[str] = None

    async def connect_stdio(self):
        """Connect to stdio-based MCP server"""
        print(f"🔌 Connecting to MCP server: {self.server_name}")

        # Start the subprocess
        env = os.environ.copy()
        env.update(self.env)

        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        # Initialize the server
        await self.initialize()

        print(f"✅ Connected to MCP server: {self.server_name}")

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.process or not self.process.stdin:
            raise Exception("MCP server not connected")

        # Send the request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read the response
        if not self.process.stdout:
            raise Exception("MCP server stdout not available")

        response_line = self.process.stdout.readline().strip()
        if not response_line:
            raise Exception("No response from MCP server")

        return json.loads(response_line)

    async def initialize(self):
        """Initialize the MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "dopemux-mcp-client",
                    "version": "1.0.0"
                }
            }
        }

        response = await self.send_request(request)
        if "error" in response:
            raise Exception(f"MCP initialization failed: {response['error']}")

        print(f"Initialized MCP server {self.server_name}: {response}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        response = await self.send_request(request)
        if "error" in response:
            raise Exception(f"Failed to list tools: {response['error']}")

        return response.get("result", {}).get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        response = await self.send_request(request)
        if "error" in response:
            raise Exception(f"Failed to call tool {tool_name}: {response['error']}")

        return response.get("result")

    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.create_subprocess_shell(f"wait {self.process.pid}")
            except Exception as e:
                print(f"Warning: Failed to terminate process: {e}")

        print(f"🔌 Disconnected from MCP server: {self.server_name}")


class MCPClientManager:
    """Manages multiple MCP clients"""

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    def add_server(self, server_name: str, command: str, args: List[str], env: Dict[str, str]):
        """Add an MCP server configuration"""
        self.clients[server_name] = MCPClient(server_name, command, args, env)

    async def connect_all(self):
        """Connect to all MCP servers"""
        for client in self.clients.values():
            await client.connect_stdio()

    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List tools from all connected servers"""
        results = {}
        for server_name, client in self.clients.items():
            try:
                tools = await client.list_tools()
                results[server_name] = tools
            except Exception as e:
                print(f"Failed to list tools for {server_name}: {e}")
                results[server_name] = []

        return results

    async def call_tool_by_name(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool by name, searching across all servers"""
        for server_name, client in self.clients.items():
            try:
                tools = await client.list_tools()
                tool_names = [tool["name"] for tool in tools]

                if tool_name in tool_names:
                    return await client.call_tool(tool_name, arguments)
            except Exception as e:
                print(f"Failed to check tools for {server_name}: {e}")
                continue

        raise Exception(f"Tool '{tool_name}' not found on any server")

    async def disconnect_all(self):
        """Disconnect from all servers"""
        for client in self.clients.values():
            await client.disconnect()


# Server configurations
def create_server_configs():
    """Create MCP server configurations"""
    configs = {}

    # Task Master AI (stdio)
    configs['task-master-ai'] = {
        'command': 'docker',
        'args': ['exec', 'mcp-task-master-ai', 'node', '/app/dist/mcp-server.js'],
        'env': {
            'MCP_SERVER_PORT': '3005',
            'MCP_TRANSPORT': 'stdio'
        }
    }

    # Zen (stdio)
    configs['zen'] = {
        'command': 'docker',
        'args': ['exec', 'mcp-zen', 'bash', '-c', 'source /app/.venv/bin/activate && python zen-mcp-server/server.py'],
        'env': {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', 'REDACTED_GEMINI_KEY'),
            'XAI_API_KEY': os.getenv('XAI_API_KEY', 'REDACTED_XAI_KEY'),
            'DISABLED_TOOLS': 'refactor,testgen,secaudit,docgen,tracer',
            'DEFAULT_MODEL': 'auto',
            'ZEN_DEFAULT_PROVIDER': 'openrouter'
        }
    }

    # Exa (stdio)
    configs['exa'] = {
        'command': 'docker',
        'args': ['exec', 'mcp-exa', 'python', '/app/mcp_server.py'],
        'env': {
            'EXA_API_KEY': os.getenv('EXA_API_KEY', '')
        }
    }

    # Desktop Commander (stdio)
    configs['desktop-commander'] = {
        'command': 'docker',
        'args': ['exec', 'mcp-desktop-commander', 'python', '/app/mcp_server.py'],
        'env': {
            'DISPLAY': os.getenv('DISPLAY', ':0')
        }
    }

    return configs


async def main():
    print("🚀 Starting Dopemux MCP Client (Python)")

    manager = MCPClientManager()

    # Add server configurations
    configs = create_server_configs()
    for server_name, config in configs.items():
        manager.add_server(
            server_name,
            config['command'],
            config['args'],
            config['env']
        )

    try:
        # Connect to all servers
        await manager.connect_all()

        print(f"\n📋 Connected MCP Servers: {list(manager.clients.keys())}")

        # List all available tools
        print("\n🔧 Available Tools:")
        all_tools = await manager.list_all_tools()

        for server_name, tools in all_tools.items():
            print(f"\n{server_name}:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool.get('description', 'No description')}")

        # Test task-master-ai batch_tasks tool if available
        if 'task-master-ai' in manager.clients:
            print("\n🛠️  Testing task-master-ai batch_tasks tool...")
            try:
                result = await manager.call_tool_by_name(
                    'batch_tasks',
                    {'tasks': ['task1', 'task2', 'task3', 'task4', 'task5']}
                )
                print("Result:", json.dumps(result, indent=2))
            except Exception as e:
                print(f"Task not available or failed: {e}")

    except Exception as e:
        print(f"❌ MCP Client error: {e}")
        sys.exit(1)
    finally:
        await manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())