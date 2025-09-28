#!/usr/bin/env python3
"""
Test script for GPT-Researcher MCP Server
Tests basic stdio communication and tool functionality
"""

import asyncio
import json
import subprocess
import sys


async def test_mcp_server():
    """Test the MCP server with basic requests"""

    # Start the server process
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        'server.py',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd='/Users/hue/code/dopemux-mvp/services/dopemux-gpt-researcher/mcp-server'
    )

    print("🚀 Testing GPT-Researcher MCP Server")
    print("-" * 40)

    try:
        # Test 1: Initialize
        print("\n1. Testing initialization...")
        request = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {
                'protocolVersion': '0.1.0',
                'capabilities': {},
                'clientInfo': {
                    'name': 'test-client',
                    'version': '1.0.0'
                }
            },
            'id': 1
        }

        response = await send_request(process, request)
        if response and 'result' in response:
            print("✅ Initialization successful")
            print(f"   Server: {response['result'].get('serverInfo', {}).get('name')}")
            print(f"   Version: {response['result'].get('serverInfo', {}).get('version')}")
        else:
            print("❌ Initialization failed")
            print(f"   Response: {response}")

        # Test 2: List tools
        print("\n2. Testing tools/list...")
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/list',
            'params': {},
            'id': 2
        }

        response = await send_request(process, request)
        if response and 'result' in response:
            tools = response['result'].get('tools', [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print("❌ Failed to list tools")
            print(f"   Response: {response}")

        # Test 3: List resources
        print("\n3. Testing resources/list...")
        request = {
            'jsonrpc': '2.0',
            'method': 'resources/list',
            'params': {},
            'id': 3
        }

        response = await send_request(process, request)
        if response and 'result' in response:
            resources = response['result'].get('resources', [])
            print(f"✅ Found {len(resources)} resources:")
            for resource in resources:
                print(f"   - {resource['name']}: {resource['uri']}")
        else:
            print("❌ Failed to list resources")
            print(f"   Response: {response}")

        # Test 4: Quick search (mock test without actual API keys)
        print("\n4. Testing quick_search tool...")
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': 'quick_search',
                'arguments': {
                    'query': 'Python MCP server implementation',
                    'max_results': 3
                }
            },
            'id': 4
        }

        response = await send_request(process, request)
        if response:
            if 'result' in response:
                print("✅ Quick search executed")
                # Parse the content
                content = response['result'].get('content', [])
                if content and content[0].get('type') == 'text':
                    result_data = json.loads(content[0].get('text', '{}'))
                    print(f"   Task ID: {result_data.get('task_id', 'N/A')}")
                    print(f"   Query: {result_data.get('query', 'N/A')}")
            elif 'error' in response:
                print("⚠️  Quick search returned error (expected without API keys)")
                print(f"   Error: {response['error'].get('message', 'Unknown error')}")
        else:
            print("❌ No response from quick search")

        print("\n" + "-" * 40)
        print("✅ All basic tests completed!")

    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Terminate the server
        process.terminate()
        await process.wait()


async def send_request(process, request):
    """Send a request to the server and get response"""
    try:
        # Send request
        request_str = json.dumps(request) + '\n'
        process.stdin.write(request_str.encode())
        await process.stdin.drain()

        # Read response (with timeout)
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )
            response = json.loads(response_line.decode())
            return response
        except asyncio.TimeoutError:
            print("   ⏱️  Timeout waiting for response")
            return None
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Invalid JSON response: {e}")
            return None

    except Exception as e:
        print(f"   ❌ Communication error: {e}")
        return None


if __name__ == '__main__':
    asyncio.run(test_mcp_server())