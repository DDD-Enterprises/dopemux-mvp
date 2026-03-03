#!/usr/bin/env python3
"""
Test script to verify desktop-commander HTTP transport works
"""

import asyncio
import aiohttp
import json

async def test_desktop_commander():
    """Test desktop-commander MCP server via HTTP"""

    base_url = "http://localhost:3012"

    try:
        async with aiohttp.ClientSession() as session:
            print("🔌 Testing desktop-commander HTTP transport...")

            # Test 1: Health check
            print("📊 Testing health endpoint...")
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ Health check passed: {health}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return

            # Test 2: MCP tools/list
            print("🔧 Testing tools/list...")
            request_data = {"method": "tools/list", "params": {}}
            async with session.post(f"{base_url}/mcp", json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("error"):
                        print(f"❌ Tools list failed: {result['error']}")
                        return
                    tools = result.get("result", {}).get("tools", [])
                    print(f"✅ Tools list successful: {len(tools)} tools found")
                    for tool in tools:
                        print(f"  - {tool['name']}: {tool['description']}")
                else:
                    print(f"❌ Tools list failed: HTTP {response.status}")
                    return

            # Test 3: MCP tools/call (window_list)
            print("🖥️  Testing window_list tool...")
            request_data = {"method": "tools/call", "params": {"name": "window_list", "arguments": {}}}
            async with session.post(f"{base_url}/mcp", json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("error"):
                        print(f"❌ Window list failed: {result['error']}")
                        return
                    print(f"✅ Window list successful: {result.get('result', {})}")
                else:
                    print(f"❌ Window list failed: HTTP {response.status}")
                    return

            print("🎉 All tests passed! Desktop-commander HTTP transport is working.")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_desktop_commander())