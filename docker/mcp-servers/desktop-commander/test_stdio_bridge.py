#!/usr/bin/env python3
"""
Test Desktop-Commander Stdio Bridge

Validates that the stdio bridge correctly forwards MCP requests
from stdio to the HTTP server and back.
"""

import subprocess
import json
import sys
import time

def test_stdio_bridge():
    """Test the stdio bridge with a tools/list request"""
    print("=" * 60)
    print("Testing Desktop-Commander Stdio Bridge")
    print("=" * 60)
    print()

    # Start the stdio bridge
    print("1. Starting stdio bridge...")
    process = subprocess.Popen(
        ['python3', '/Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander/stdio_bridge.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )

    # Give it a moment to start
    time.sleep(1)

    try:
        # Send tools/list request
        print("2. Sending tools/list request...")
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/list',
            'params': {}
        }

        request_json = json.dumps(request) + '\n'
        print(f"   Request: {request_json.strip()}")

        process.stdin.write(request_json)
        process.stdin.flush()

        # Read response (with timeout)
        print("3. Waiting for response...")
        response_line = process.stdout.readline()

        if not response_line:
            stderr_output = process.stderr.read()
            print(f"❌ ERROR: No response received")
            print(f"   Stderr: {stderr_output}")
            return False

        print(f"   Response received: {len(response_line)} bytes")

        # Parse response
        try:
            response = json.loads(response_line)
            print("4. Parsing response...")

            # Validate response structure
            assert 'jsonrpc' in response, "Missing jsonrpc field"
            assert 'id' in response, "Missing id field"
            assert response['id'] == 1, f"Wrong id: {response['id']}"

            if 'error' in response:
                print(f"❌ ERROR in response: {response['error']}")
                return False

            # Validate tools in result
            assert 'result' in response, "Missing result field"
            result = response['result']
            assert 'tools' in result, "Missing tools in result"

            tools = result['tools']
            print(f"   Tools found: {len(tools)}")

            # Validate expected tools
            tool_names = [tool['name'] for tool in tools]
            expected_tools = ['screenshot', 'window_list', 'focus_window', 'type_text']

            print("5. Validating tools:")
            for expected in expected_tools:
                if expected in tool_names:
                    print(f"   ✅ {expected}")
                else:
                    print(f"   ❌ Missing: {expected}")
                    return False

            print()
            print("=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("Desktop-Commander stdio bridge is working correctly.")
            print("=" * 60)
            return True

        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON response: {e}")
            print(f"   Raw response: {response_line}")
            return False

    except Exception as e:
        print(f"❌ ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        print("\n6. Cleaning up...")
        process.terminate()
        process.wait(timeout=5)
        print("   Bridge process terminated")

if __name__ == '__main__':
    success = test_stdio_bridge()
    sys.exit(0 if success else 1)
