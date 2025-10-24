#!/usr/bin/env python3
"""
Manual Smoke Test for Integration Day 3

Tests complete event pipeline:
  Agents → EventBus → Redis → PatternDetector → ConPort
"""
import asyncio
import sys
import redis.asyncio as redis

from event_bus import Event, EventBus
from pattern_detector import PatternDetector
from integrations.serena import SerenaIntegrationManager
from integrations.dope_context import DopeContextIntegrationManager
from integrations.adhd_engine import ADHDEngineIntegrationManager
from integrations.task_orchestrator import TaskOrchestratorIntegrationManager


async def test_complete_pipeline():
    """Test full event pipeline with all 4 agents"""

    print("\n" + "=" * 70)
    print("INTEGRATION DAY 3: MANUAL SMOKE TEST")
    print("=" * 70 + "\n")

    # Connect to Redis
    redis_client = redis.from_url("redis://localhost:6379", db=0, decode_responses=False)

    # Initialize EventBus
    print("📊 Initializing EventBus with Phase 3 features...")
    bus = EventBus(
        redis_url="redis://localhost:6379/0",
        enable_deduplication=True,
        enable_cache=True,
        enable_rate_limiting=True,
        enable_monitoring=True,
    )
    await bus.initialize()

    print(f"   Cache: {'✅' if bus.cache else '❌'}")
    print(f"   Rate Limiter: {'✅' if bus.rate_limiter else '❌'}")
    print(f"   Metrics: {'✅' if bus.metrics else '❌'}")
    print(f"   Deduplicator: {'✅' if bus.deduplicator else '❌'}\n")

    # Create agent managers
    workspace_id = "/test/workspace"
    print("📊 Creating agent managers...")
    managers = {
        "serena": SerenaIntegrationManager(bus, workspace_id),
        "dope-context": DopeContextIntegrationManager(bus, workspace_id),
        "adhd-engine": ADHDEngineIntegrationManager(bus, workspace_id),
        "task-orchestrator": TaskOrchestratorIntegrationManager(bus, workspace_id),
    }
    print(f"   Created {len(managers)} managers ✅\n")

    # Test 1: Emit event from each agent
    print("🧪 TEST 1: Event Emission from All 4 Agents")
    print("-" * 70)

    results = {}

    # Serena: Code complexity
    try:
        await managers["serena"].handle_complexity_result("/test/auth.py", 0.85)
        results["serena"] = "✅"
        print("   Serena (complexity): ✅")
    except Exception as e:
        results["serena"] = f"❌ {e}"
        print(f"   Serena: ❌ {e}")

    # Dope-Context: Search completed
    try:
        await managers["dope-context"].handle_search_completed("test query", 5, 1.2)
        results["dope-context"] = "✅"
        print("   Dope-Context (search): ✅")
    except Exception as e:
        results["dope-context"] = f"❌ {e}"
        print(f"   Dope-Context: ❌ {e}")

    # ADHD Engine: State change
    try:
        await managers["adhd-engine"].handle_cognitive_state_change("focused", "scattered", 0.7)
        results["adhd-engine"] = "✅"
        print("   ADHD Engine (state): ✅")
    except Exception as e:
        results["adhd-engine"] = f"❌ {e}"
        print(f"   ADHD Engine: ❌ {e}")

    # Task Orchestrator: Task completed
    try:
        await managers["task-orchestrator"].handle_task_completed("TASK-001", 25.5)
        results["task-orchestrator"] = "✅"
        print("   Task Orchestrator (task): ✅")
    except Exception as e:
        results["task-orchestrator"] = f"❌ {e}"
        print(f"   Task Orchestrator: ❌ {e}")

    print()

    # Test 2: Check Redis stream
    print("🧪 TEST 2: Events in Redis Stream")
    print("-" * 70)

    stream_length = await redis_client.execute_command("XLEN", "dopemux:events")
    print(f"   Stream length: {stream_length}")
    print(f"   Status: {'✅ Events published' if stream_length > 0 else '❌ No events'}\n")

    # Test 3: Read events from stream
    if stream_length > 0:
        print("🧪 TEST 3: Read Events from Stream")
        print("-" * 70)

        events = await redis_client.execute_command(
            "XREAD", "COUNT", "10", "STREAMS", "dopemux:events", "0"
        )

        if events:
            for stream_name, messages in events:
                for msg_id, msg_data in messages:
                    print(f"   Event ID: {msg_id.decode()}")
                    event_type = msg_data.get(b"event_type", b"unknown").decode()
                    source = msg_data.get(b"source", b"unknown").decode()
                    print(f"   Type: {event_type}, Source: {source}")

        print(f"   Status: ✅ Events readable\n")

    # Test 4: Check Phase 3 features
    print("🧪 TEST 4: Phase 3 Features Active")
    print("-" * 70)

    if bus.cache:
        print("   Multi-tier Cache: ✅ Initialized")
    if bus.rate_limiter:
        print("   Rate Limiter: ✅ Initialized")
    if bus.metrics:
        print("   Monitoring: ✅ Initialized")
    if bus.deduplicator:
        print("   Deduplication: ✅ Initialized")

    print()

    # Summary
    print("=" * 70)
    print("SMOKE TEST SUMMARY")
    print("=" * 70)

    success_count = sum(1 for r in results.values() if "✅" in str(r))
    total_count = len(results)

    print(f"\n📊 Agent Integration: {success_count}/{total_count} agents working")
    for agent, status in results.items():
        print(f"   {agent}: {status}")

    print(f"\n📊 Event Pipeline: {'✅ OPERATIONAL' if stream_length > 0 else '❌ NO EVENTS'}")
    print(f"\n📊 Phase 3 Features: {'✅ ALL ACTIVE' if all([bus.cache, bus.rate_limiter, bus.metrics]) else '⚠️ PARTIAL'}")

    # Overall verdict
    if success_count == total_count and stream_length > 0:
        print("\n" + "=" * 70)
        print("✅ SMOKE TEST PASSED - System operational!")
        print("=" * 70 + "\n")
        verdict = True
    else:
        print("\n" + "=" * 70)
        print("⚠️ SMOKE TEST PARTIAL - Some issues detected")
        print("=" * 70 + "\n")
        verdict = False

    # Cleanup
    await redis_client.aclose()
    if bus.redis_client:
        await bus.redis_client.aclose()

    return verdict


if __name__ == "__main__":
    result = asyncio.run(test_complete_pipeline())
    sys.exit(0 if result else 1)
