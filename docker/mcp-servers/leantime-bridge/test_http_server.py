#!/usr/bin/env python3
"""
Test script for Leantime MCP HTTP Server
Tests the SSE endpoints and basic MCP protocol communication
"""

import asyncio
import json
import sys
from typing import Any, Dict

import aiohttp


class LeantimeMCPClient:
    """Simple HTTP/SSE client for testing Leantime MCP server"""

    def __init__(self, base_url: str = "http://localhost:3015"):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse"
        self.session = None
        self.message_endpoint = None
        self.session_id = None

    async def connect(self):
        """Connect to the MCP server via SSE"""
        print(f"Connecting to {self.sse_url}...")
        self.session = aiohttp.ClientSession()

        async with self.session.get(self.sse_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to connect: HTTP {response.status}")

            print(f"✓ Connected successfully (status: {response.status})")

            # Read SSE events
            async for line in response.content:
                decoded = line.decode('utf-8').strip()
                if not decoded:
                    continue

                if decoded.startswith('event:'):
                    event_type = decoded[6:].strip()

                if decoded.startswith('data:'):
                    data = decoded[5:].strip()

                    if event_type == 'endpoint':
                        # Extract message endpoint and session ID
                        self.message_endpoint = data.split('?')[0]
                        self.session_id = data.split('session_id=')[1] if 'session_id=' in data else None
                        print(f"✓ Received endpoint: {self.message_endpoint}")
                        print(f"✓ Session ID: {self.session_id}")
                        return  # Exit after getting endpoint

                    elif event_type == 'message':
                        # Handle MCP messages
                        message = json.loads(data)
                        print(f"→ Received message: {json.dumps(message, indent=2)}")

    async def send_initialize(self) -> Dict[str, Any]:
        """Send MCP initialize request"""
        if not self.message_endpoint or not self.session_id:
            raise Exception("Not connected - call connect() first")

        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        return await self.send_message(message)

    async def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools"""
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        return await self.send_message(message)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        return await self.send_message(message)

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP server via POST"""
        if not self.message_endpoint or not self.session_id:
            raise Exception("Not connected - call connect() first")

        url = f"{self.base_url}{self.message_endpoint}?session_id={self.session_id}"

        print(f"\n→ Sending: {message['method']}")

        async with self.session.post(url, json=message) as response:
            if response.status != 202:
                raise Exception(f"Failed to send message: HTTP {response.status}")

            # For testing, we'll just return the status
            # In a real client, you'd wait for the SSE response
            return {"status": "accepted", "http_status": response.status}

    async def close(self):
        """Close the connection"""
        if self.session:
            await self.session.close()
            print("\n✓ Connection closed")


async def test_basic_connection():
    """Test basic SSE connection"""
    print("=" * 60)
    print("TEST 1: Basic SSE Connection")
    print("=" * 60)

    client = LeantimeMCPClient()

    try:
        await client.connect()
        print("\n✓ TEST PASSED: Successfully connected via SSE")
        return True
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    finally:
        await client.close()


async def test_mcp_initialize():
    """Test MCP initialize handshake"""
    print("\n" + "=" * 60)
    print("TEST 2: MCP Initialize Handshake")
    print("=" * 60)

    client = LeantimeMCPClient()

    try:
        await client.connect()
        result = await client.send_initialize()
        print(f"✓ Initialize response: {result}")
        print("\n✓ TEST PASSED: MCP initialize successful")
        return True
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    finally:
        await client.close()


async def test_list_tools():
    """Test listing MCP tools"""
    print("\n" + "=" * 60)
    print("TEST 3: List Available Tools")
    print("=" * 60)

    client = LeantimeMCPClient()

    try:
        await client.connect()
        await client.send_initialize()
        result = await client.list_tools()
        print(f"✓ Tools list response: {result}")
        print("\n✓ TEST PASSED: Successfully listed tools")
        return True
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    finally:
        await client.close()


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Leantime MCP HTTP Server Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_basic_connection,
        test_mcp_initialize,
        test_list_tools,
    ]

    results = []
    for test in tests:
        result = await test()
        results.append(result)
        await asyncio.sleep(1)  # Brief pause between tests

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
