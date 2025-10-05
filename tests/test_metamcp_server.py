#!/usr/bin/env python3
"""
Test MetaMCP Server functionality before integrating with Claude Code
"""

import asyncio
import json
import sys
import subprocess
import tempfile
import os
from pathlib import Path

# Test the MetaMCP server
async def test_metamcp_server():
    """Test the MetaMCP server with sample MCP requests"""

    print("🧪 Testing MetaMCP Server...")

    # Change to the correct directory
    original_dir = os.getcwd()
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    try:
        # Start the server process
        server_process = subprocess.Popen(
            [sys.executable, "metamcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=test_dir
        )

        # Wait a moment for startup
        await asyncio.sleep(2)

        # Test initialize request
        print("📡 Testing initialize request...")
        init_request = {
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

        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()

        # Read response
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"✅ Initialize response: {response.get('result', {}).get('serverInfo', {}).get('name')}")

        # Test tools list request
        print("🛠️  Testing tools/list request...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        server_process.stdin.write(json.dumps(tools_request) + "\n")
        server_process.stdin.flush()

        # Read response
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            tools = response.get('result', {}).get('tools', [])
            print(f"✅ Tools available: {[tool['name'] for tool in tools]}")

        # Test get_status tool call
        print("📊 Testing get_status tool call...")
        status_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_status",
                "arguments": {}
            }
        }

        server_process.stdin.write(json.dumps(status_request) + "\n")
        server_process.stdin.flush()

        # Read response
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            content = response.get('result', {}).get('content', [])
            if content:
                print(f"✅ Status response received")
                print(f"📋 Content preview: {content[0].get('text', '')[:100]}...")

        # Test role switch
        print("🔄 Testing role switch...")
        switch_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "switch_role",
                "arguments": {
                    "role": "researcher"
                }
            }
        }

        server_process.stdin.write(json.dumps(switch_request) + "\n")
        server_process.stdin.flush()

        # Read response
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            content = response.get('result', {}).get('content', [])
            if content:
                print(f"✅ Role switch response received")
                print(f"📋 Response: {content[0].get('text', '')[:100]}...")

        print("✅ MetaMCP Server test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        # Clean up
        if 'server_process' in locals():
            server_process.terminate()
            server_process.wait()
        os.chdir(original_dir)

if __name__ == "__main__":
    # Ensure we have the right dependencies
    if not os.path.exists("config/mcp/policy.yaml"):
        print("❌ Please run from dopemux-mvp directory with config files")
        sys.exit(1)

    # Run the test
    success = asyncio.run(test_metamcp_server())
    sys.exit(0 if success else 1)