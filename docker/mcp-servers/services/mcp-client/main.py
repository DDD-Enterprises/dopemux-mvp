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
import re
from typing import Dict, List, Any, Optional
import aiohttp


class MCPClient:
    """MCP client supporting both stdio and HTTP transports"""

    def __init__(self, server_name: str, transport: str, config: Dict[str, Any]):
        self.server_name = server_name
        self.transport = transport  # 'stdio' or 'http'
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.session_id: Optional[str] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        if transport == 'http':
            self.base_url = config.get('base_url', f'http://localhost:{config.get("port", 3000)}')
            self._validate_base_url(self.base_url)

    def _validate_base_url(self, base_url: str) -> None:
        """Validate base URL to prevent SSRF attacks"""
        # Allow only localhost, 127.0.0.1, and docker container names
        allowed_patterns = [
            r'^http://localhost(:\d+)?/?$',  # localhost
            r'^http://127\.0\.0\.1(:\d+)?/?$',  # 127.0.0.1
            r'^http://[a-zA-Z0-9_-]+(:\d+)?/?$',  # docker container names (no dots)
        ]

        for pattern in allowed_patterns:
            if re.match(pattern, base_url):
                return

        raise ValueError(f"Invalid base URL '{base_url}': only localhost, 127.0.0.1, and docker container names are allowed for security")

    async def connect_stdio(self):
        """Connect to stdio-based MCP server"""
        print(f"🔌 Connecting to MCP server: {self.server_name} (stdio)")

        # Start the subprocess
        env = os.environ.copy()
        env.update(self.config.get('env', {}))

        self.process = subprocess.Popen(
            [self.config['command']] + self.config['args'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        # Initialize the server
        await self.initialize()

        print(f"✅ Connected to MCP server: {self.server_name} (stdio)")

    async def connect_http(self):
        """Connect to HTTP-based MCP server"""
        print(f"🔌 Connecting to MCP server: {self.server_name} (http)")

        self.http_session = aiohttp.ClientSession()

        # Initialize the server
        await self.initialize()

        print(f"✅ Connected to MCP server: {self.server_name} (http)")

    async def connect(self):
        """Connect using the appropriate transport"""
        if self.transport == 'http':
            await self.connect_http()
        else:
            await self.connect_stdio()

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if self.transport == 'http':
            return await self._send_http_request(request)
        else:
            return await self._send_stdio_request(request)

    async def _send_stdio_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send stdio request"""
        if not self.process or not self.process.stdin:
            raise Exception("MCP server not connected (stdio)")

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

    async def _send_http_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send HTTP request"""
        if not self.http_session:
            raise Exception("MCP server not connected (http)")

        try:
            async with self.http_session.post(
                f"{self.base_url}/mcp",
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")

                result = await response.json()
                return result
        except aiohttp.ClientError as e:
            raise Exception(f"HTTP request failed: {e}")

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
        if self.transport == 'http':
            if self.http_session:
                await self.http_session.close()
                self.http_session = None
        else:
            if self.process:
                try:
                    self.process.terminate()
                    await asyncio.create_subprocess_shell(f"wait {self.process.pid}")
                except Exception as e:
                    print(f"Warning: Failed to terminate process: {e}")

        print(f"🔌 Disconnected from MCP server: {self.server_name} ({self.transport})")


class MCPClientManager:
    """Manages multiple MCP clients"""

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    def add_server(self, server_name: str, transport: str, config: Dict[str, Any]):
        """Add an MCP server configuration"""
        self.clients[server_name] = MCPClient(server_name, transport, config)

    async def connect_all(self):
        """Connect to all MCP servers"""
        for client in self.clients.values():
            await client.connect()

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
        'transport': 'stdio',
        'command': 'docker',
        'args': ['exec', 'mcp-task-master-ai', 'node', '/app/dist/mcp-server.js'],
        'env': {
            'MCP_SERVER_PORT': '3005',
            'MCP_TRANSPORT': 'stdio'
        }
    }

    # Zen (stdio - direct host process)
    configs['zen'] = {
        'transport': 'stdio',
        'command': '/Users/hue/code/dopemux-mvp/docker/mcp-servers/zen/zen-mcp-server/.venv/bin/python',
        'args': ['/Users/hue/code/dopemux-mvp/docker/mcp-servers/zen/zen-mcp-server/server.py'],
        'env': {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', '<REDACTED_GEMINI_KEY>'),
            'XAI_API_KEY': os.getenv('XAI_API_KEY', '<REDACTED_XAI_KEY>'),
            'DISABLED_TOOLS': 'refactor,testgen,secaudit,docgen,tracer',
            'DEFAULT_MODEL': 'auto',
            'ZEN_DEFAULT_PROVIDER': 'openrouter'
        }
    }

    # Exa (http)
    configs['exa'] = {
        'transport': 'http',
        'port': 3008,
        'env': {
            'EXA_API_KEY': os.getenv('EXA_API_KEY', '')
        }
    }

    # Desktop Commander (http)
    configs['desktop-commander'] = {
        'transport': 'http',
        'port': 3012,
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
        transport = config.get('transport', 'stdio')
        print(f"🔧 Configuring {server_name} with transport: {transport}")
        manager.add_server(
            server_name,
            transport,
            config
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