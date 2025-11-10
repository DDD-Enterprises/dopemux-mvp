#!/usr/bin/env python3
"""
Working Memory Assistant Service - Test Suite
Tests core functionality: snapshots, recovery, preferences
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

WMA_BASE_URL = "http://localhost:8096"

async def test_health_check():
    """Test service health endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{WMA_BASE_URL}/health")
            response.raise_for_status()
            data = response.json()
            print("✅ Health check passed:", data["status"])
            return True
        except Exception as e:
            print("❌ Health check failed:", str(e))
            return False

async def test_snapshot_creation():
    """Test context snapshot creation"""
    snapshot_data = {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "context_type": "work",
        "priority": 0.8,
        "emotional_weight": 0.6,
        "complexity_score": 0.7,
        "mental_model": {
            "project": "Working Memory Assistant",
            "workspace": "/Users/hue/code/dopemux-mvp",
            "goal": "Implement 20-30x faster interrupt recovery"
        },
        "active_focus": {
            "file": "services/working-memory-assistant/main.py",
            "cursor": {"line": 150, "column": 10},
            "visible_range": {"start": {"line": 140}, "end": {"line": 160}}
        },
        "current_task": {
            "description": "Building FastAPI endpoints for context snapshots",
            "progress": 0.7,
            "blockers": [],
            "nextSteps": ["Test recovery functionality", "Implement Redis caching"],
            "relatedFiles": ["main.py", "requirements.txt", "Dockerfile"]
        },
        "metadata": {
            "interrupt_type": "meeting",
            "energy_level": 0.8,
            "attention_state": "focused"
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{WMA_BASE_URL}/snapshot", json=snapshot_data)
            response.raise_for_status()
            data = response.json()
            snapshot_id = data["snapshot_id"]
            print(f"✅ Snapshot created: {snapshot_id}")
            return snapshot_id
        except Exception as e:
            print("❌ Snapshot creation failed:", str(e))
            return None

async def test_context_recovery(snapshot_id: str):
    """Test context recovery"""
    recovery_request = {
        "user_id": "test_user_123",
        "snapshot_id": snapshot_id,
        "recovery_stage": "essential"
    }

    async with httpx.AsyncClient() as client:
        try:
            start_time = time.time()
            response = await client.post(f"{WMA_BASE_URL}/recover", json=recovery_request)
            response.raise_for_status()
            data = response.json()
            duration = int((time.time() - start_time) * 1000)

            print(f"✅ Context recovered in {data['recovery_time_ms']}ms (actual: {duration}ms)")
            print(f"   Cache hit: {data['cache_hit']}")
            print(f"   Recovery stage: {data['recovery_stage']}")

            # Check essential context structure
            context = data['context_data']
            if 'task' in context and 'file' in context and 'line' in context:
                print("   ✅ Essential context structure correct")
            else:
                print("   ❌ Essential context structure incomplete")

            return True
        except Exception as e:
            print("❌ Context recovery failed:", str(e))
            return False

async def test_user_contexts():
    """Test retrieving user contexts"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{WMA_BASE_URL}/contexts/test_user_123")
            response.raise_for_status()
            data = response.json()
            contexts = data["contexts"]
            print(f"✅ Retrieved {len(contexts)} user contexts")
            return len(contexts) > 0
        except Exception as e:
            print("❌ User contexts retrieval failed:", str(e))
            return False

async def test_user_preferences():
    """Test user preferences management"""
    # Test getting preferences (should return defaults)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{WMA_BASE_URL}/preferences/test_user_123")
            response.raise_for_status()
            prefs = response.json()
            print("✅ Retrieved user preferences (defaults)")

            # Test updating preferences
            update_data = {
                "user_id": "test_user_123",
                "auto_snapshot_enabled": False,
                "privacy_level": "comprehensive",
                "retention_days": 60,
                "max_memory_mb": 100,
                "notification_style": "standard"
            }

            response = await client.post(f"{WMA_BASE_URL}/preferences", json=update_data)
            response.raise_for_status()
            print("✅ Updated user preferences")

            # Verify update
            response = await client.get(f"{WMA_BASE_URL}/preferences/test_user_123")
            response.raise_for_status()
            updated_prefs = response.json()

            if updated_prefs["privacy_level"] == "comprehensive":
                print("✅ Preferences update verified")
                return True
            else:
                print("❌ Preferences update not reflected")
                return False

        except Exception as e:
            print("❌ User preferences test failed:", str(e))
            return False

async def test_performance():
    """Test performance against targets"""
    print("\n📊 Performance Testing:")

    # Test snapshot creation time (target: <200ms)
    snapshot_data = {
        "user_id": "perf_test_user",
        "context_type": "work",
        "mental_model": {"project": "Performance Test"},
        "active_focus": {"file": "test.py", "cursor": {"line": 1, "column": 1}},
        "current_task": {"description": "Performance testing"}
    }

    async with httpx.AsyncClient() as client:
        # Create snapshot and measure time
        start_time = time.time()
        response = await client.post(f"{WMA_BASE_URL}/snapshot", json=snapshot_data)
        response.raise_for_status()
        data = response.json()
        snapshot_id = data["snapshot_id"]
        snapshot_time = int((time.time() - start_time) * 1000)

        print(f"   Snapshot creation: {snapshot_time}ms (target: <200ms) {'✅' if snapshot_time < 200 else '❌'}")

        # Test recovery time (target: <2000ms)
        recovery_data = {
            "user_id": "perf_test_user",
            "snapshot_id": snapshot_id,
            "recovery_stage": "complete"
        }

        start_time = time.time()
        response = await client.post(f"{WMA_BASE_URL}/recover", json=recovery_data)
        response.raise_for_status()
        data = response.json()
        recovery_time = data["recovery_time_ms"]

        print(f"   Context recovery: {recovery_time}ms (target: <2000ms) {'✅' if recovery_time < 2000 else '❌'}")

        # Test cache hit (should be fast)
        start_time = time.time()
        response = await client.post(f"{WMA_BASE_URL}/recover", json=recovery_data)
        response.raise_for_status()
        data = response.json()
        cache_recovery_time = data["recovery_time_ms"]

        print(f"   Cache hit recovery: {cache_recovery_time}ms (should be <100ms) {'✅' if cache_recovery_time < 100 else '❌'}")
        print(f"   Cache hit: {data['cache_hit']} {'✅' if data['cache_hit'] else '⚠️'}")

        return snapshot_time < 200 and recovery_time < 2000

async def run_tests():
    """Run all WMA service tests"""
    print("🧠 Working Memory Assistant Service - Test Suite")
    print("=" * 55)

    tests = [
        ("Health Check", test_health_check),
        ("Snapshot Creation", test_snapshot_creation),
        ("User Contexts", test_user_contexts),
        ("User Preferences", test_user_preferences),
        ("Performance", test_performance),
    ]

    results = []
    snapshot_id = None

    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_name == "Context Recovery":
            # Pass snapshot_id from previous test
            result = await test_func(snapshot_id) if snapshot_id else False
        elif test_name == "Snapshot Creation":
            snapshot_id = await test_func()
            result = snapshot_id is not None
        else:
            result = await test_func()
        results.append((test_name, result))

    # Add context recovery test after snapshot creation
    if snapshot_id:
        print(f"\n🔍 Testing: Context Recovery")
        recovery_result = await test_context_recovery(snapshot_id)
        results.append(("Context Recovery", recovery_result))

    # Summary
    print("\n📊 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n🏆 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! WMA service is ready for production.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    # Run async tests
    success = asyncio.run(run_tests())
    exit(0 if success else 1)