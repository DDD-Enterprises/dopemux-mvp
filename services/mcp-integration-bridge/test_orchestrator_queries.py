#!/usr/bin/env python3
"""
Test Script for Component 5: Cross-Plane Query Endpoints
=========================================================

Tests all orchestrator query endpoints to ensure proper functionality.

Usage:
    python test_orchestrator_queries.py [--url http://localhost:3016]
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

# Default Integration Bridge URL
BRIDGE_URL = "http://localhost:3016"


async def test_endpoint(session: aiohttp.ClientSession, endpoint: str, name: str) -> bool:
    """Test a single endpoint."""
    url = f"{BRIDGE_URL}{endpoint}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ {name}: {response.status}")
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                return True
            else:
                print(f"❌ {name}: {response.status}")
                text = await response.text()
                print(f"   Error: {text[:200]}")
                return False
    except Exception as e:
        print(f"❌ {name}: Exception - {e}")
        return False


async def run_tests():
    """Run all Component 5 endpoint tests."""
    print("=" * 80)
    print("Component 5: Cross-Plane Query Endpoints - Test Suite")
    print("=" * 80)
    print()
    
    tests = [
        ("/orchestrator/tasks", "List all tasks"),
        ("/orchestrator/tasks?status=IN_PROGRESS", "List tasks by status"),
        ("/orchestrator/tasks/task-001", "Get task details"),
        ("/orchestrator/tasks/task-001/status", "Get task status"),
        ("/orchestrator/adhd-state", "Get ADHD state"),
        ("/orchestrator/recommendations", "Get task recommendations"),
        ("/orchestrator/session", "Get session status"),
        ("/orchestrator/active-sprint", "Get active sprint info"),
    ]
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for endpoint, name in tests:
            print(f"\nTesting: {name}")
            print(f"Endpoint: {endpoint}")
            result = await test_endpoint(session, endpoint, name)
            results.append((name, result))
            await asyncio.sleep(0.5)  # Rate limiting
    
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed ({100 * passed // total}%)")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BRIDGE_URL = sys.argv[1]
    
    print(f"Testing Integration Bridge at: {BRIDGE_URL}")
    print()
    
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
