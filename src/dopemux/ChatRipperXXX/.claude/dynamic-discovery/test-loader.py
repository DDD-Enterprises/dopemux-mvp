#!/usr/bin/env python3
"""
Test script for dynamic tool discovery
"""

import asyncio
import sys
import os

# Add the loader to path
sys.path.append('.claude/dynamic-discovery')

try:
    from loader import ConstrainedDynamicLoader

    async def test_dynamic_discovery():
        print("🚀 Testing Dynamic Tool Discovery")
        print("=" * 40)

        loader = ConstrainedDynamicLoader()

        # Test requests
        test_requests = [
            "I need to search for API documentation about authentication",
            "Analyze this Python code for potential bugs",
            "Store this decision in the project memory"
        ]

        for request in test_requests:
            print(f"\\nTest Request: {request}")
            try:
                activated_tools = await loader.discover_tools(request)
                print(f"Activated {len(activated_tools)} tools")
            except Exception as e:
                print(f"Error: {e}")

        print("\\n✅ Dynamic tool discovery test completed")

    if __name__ == '__main__':
        asyncio.run(test_dynamic_discovery())

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure the dynamic-discovery directory exists")
except Exception as e:
    print(f"❌ Test error: {e}")