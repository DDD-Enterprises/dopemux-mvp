#!/usr/bin/env python3
"""
Custom MCP Client for Dopemux
Connects to MCP servers over stdio transport and SSE transport
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Dict, List, Any, Optional
import aiohttp
import threading
import queue
import time


class MCPStdioClient:
    """MCP client for stdio-based MCP servers"""

    def __init__(self, server_name: str, command: List[str], env: Dict[str, str]):
        self.server_name = server_name
        self.command = command
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        self.session_id: Optional[str] = None

    def _read_stdout(self):
        """Thread to read from stdout"""
        for line in iter(self.process.stdout.readline, ''):
            if line:
                try:
                    self.stdout_queue.put(json.loads(line.strip()))
                except json.JSONDecodeError:
                    pass  # Skip non-JSON lines
            else:
                break

    def _read_stderr(self):
        """Thread to read from stderr"""
        for line in iter(self.process.stderr.readline, ''):
            if line:
                print(f"[STDERR {self.server_name}] {line.strip()}")
            else:
                break

    def start_process(self):
        """Start the MCP server process"""
        env = os.environ.copy()
        env.update(self.env)

        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )

        # Start reading threads
        stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        print(f"🔌 Started MCP server process: {self.server_name} (PID: {self.process.pid})")

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.process or self.process.poll() is not None:
            raise Exception("MCP server process not running")

        # Send the request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Wait for response
        timeout = 10
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.stdout_queue.get(timeout=1)
                return response
            except queue.Empty:
                continue

        raise Exception("Timeout waiting for MCP server response")

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

        print(f"✅ Initialized MCP server {self.server_name}: {response.get('result', 'OK')}")

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

    def stop_process(self):
        """Stop the MCP server process"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        print(f"🔌 Stopped MCP server process: {self.server_name}")


class MCPHttpClient:
    """MCP client for HTTP/SSE-based MCP servers"""

    def __init__(self, server_name: str, base_url: str):
        self.server_name = server_name
        self.base_url = base_url.rstrip('/')
        self.session_id: Optional[str] = None

    async def connect(self):
        """Connect to HTTP/SSE MCP server"""
        # Establish SSE connection to get session ID
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/sse") as response:
                # Read the SSE stream until we get an endpoint event
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        try:
                            event_data = json.loads(data)
                            if 'session_id' in event_data:
                                self.session_id = event_data['session_id']
                                print(f"✅ Connected to HTTP MCP server: {self.server_name} (session: {self.session_id})")
                                return
                        except json.JSONDecodeError:
                            continue

        raise Exception("Failed to establish SSE connection and get session ID")

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.session_id:
            raise Exception("Not connected to MCP server")

        url = f"{self.base_url}/messages/?session_id={self.session_id}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error {response.status}")
                return await response.json()

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

        print(f"✅ Initialized MCP server {self.server_name}: {response.get('result', 'OK')}")

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


class MCPClientManager:
    """Manages multiple MCP clients"""

    def __init__(self):
        self.clients: Dict[str, Any] = {}

    def add_server(self, server_name: str, config: Dict[str, Any]):
        """Add an MCP server configuration"""
        if config.get('type') == 'stdio':
            self.clients[server_name] = MCPStdioClient(
                server_name,
                config['command'],
                config.get('env', {})
            )
        elif config.get('type') == 'http':
            self.clients[server_name] = MCPHttpClient(
                server_name,
                config['url']
            )

    async def connect_all(self):
        """Connect to all MCP servers"""
        for client in self.clients.values():
            if isinstance(client, MCPStdioClient):
                client.start_process()
                await client.initialize()
            elif isinstance(client, MCPHttpClient):
                await client.connect()
                await client.initialize()

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

    def stop_all(self):
        """Stop all MCP servers"""
        for client in self.clients.values():
            if isinstance(client, MCPStdioClient):
                client.stop_process()


def cli():
    """Command line interface"""
    asyncio.run(main())


async def main():
    """Main entry point for the MCP client"""
    print("🚀 Starting Dopemux MCP Client (Python)")

    manager = MCPClientManager()

    # Add server configurations
    configs = {
        'leantime-bridge': {
            'type': 'http',
            'url': 'http://localhost:3015'
        },
        'gpt-researcher': {
            'type': 'http',
            'url': 'http://localhost:3009'
        },
        'task-orchestrator': {
            'type': 'stdio',
            'command': ['python', '/Users/hue/code/dopemux-mvp/services/task-orchestrator/server.py'],
            'env': {}
        }
    }

    try:
        # Add servers
        for server_name, config in configs.items():
            manager.add_server(server_name, config)

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

        # Test a tool call
        try:
            print("\n🛠️  Testing list_projects tool...")
            result = await manager.call_tool_by_name('list_projects')
            print("Result:", json.dumps(result, indent=2))
        except Exception as e:
            print(f"Tool test failed: {e}")

    except Exception as e:
        print(f"❌ MCP Client error: {e}")
        sys.exit(1)
    finally:
        manager.stop_all()


if __name__ == "__main__":
    asyncio.run(main())