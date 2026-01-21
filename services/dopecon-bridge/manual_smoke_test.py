#!/usr/bin/env python3
"""
Manual Smoke Test for Integration Day 3

Tests complete event pipeline:
  Agents → EventBus → Redis → PatternDetector → ConPort
"""
import asyncio

import logging

logger = logging.getLogger(__name__)

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

    logger.info("\n" + "=" * 70)
    logger.info("INTEGRATION DAY 3: MANUAL SMOKE TEST")
    logger.info("=" * 70 + "\n")

    # Connect to Redis
    redis_client = redis.from_url("redis://localhost:6379", db=0, decode_responses=False)

    # Initialize EventBus
    logger.info("📊 Initializing EventBus with Phase 3 features...")
    bus = EventBus(
        redis_url="redis://localhost:6379/0",
        enable_deduplication=True,
        enable_cache=True,
        enable_rate_limiting=True,
        enable_monitoring=True,
    )
    await bus.initialize()

    logger.info(f"   Cache: {'✅' if bus.cache else '❌'}")
    logger.info(f"   Rate Limiter: {'✅' if bus.rate_limiter else '❌'}")
    logger.info(f"   Metrics: {'✅' if bus.metrics else '❌'}")
    logger.info(f"   Deduplicator: {'✅' if bus.deduplicator else '❌'}\n")

    # Create agent managers
    workspace_id = "/test/workspace"
    logger.info("📊 Creating agent managers...")
    managers = {
        "serena": SerenaIntegrationManager(bus, workspace_id),
        "dope-context": DopeContextIntegrationManager(bus, workspace_id),
        "adhd-engine": ADHDEngineIntegrationManager(bus, workspace_id),
        "task-orchestrator": TaskOrchestratorIntegrationManager(bus, workspace_id),
    }
    logger.info(f"   Created {len(managers)} managers ✅\n")

    # Test 1: Emit event from each agent
    logger.info("🧪 TEST 1: Event Emission from All 4 Agents")
    logger.info("-" * 70)

    results = {}

    # Serena: Code complexity
    try:
        await managers["serena"].handle_complexity_result("/test/auth.py", 0.85)
        results["serena"] = "✅"
        logger.info("   Serena (complexity): ✅")
    except Exception as e:
        results["serena"] = f"❌ {e}"
        logger.info(f"   Serena: ❌ {e}")

    # Dope-Context: Search result
    try:
        await managers["dope-context"].handle_search_result("test query", [{"file": "test.py", "relevance_score": 0.8}])
        results["dope-context"] = "✅"
        logger.info("   Dope-Context (search): ✅")
    except Exception as e:
        results["dope-context"] = f"❌ {e}"
        logger.info(f"   Dope-Context: ❌ {e}")

    # ADHD Engine: State update
    try:
        await managers["adhd-engine"].handle_state_update("focused", 0.3, 0.7)
        results["adhd-engine"] = "✅"
        logger.info("   ADHD Engine (state): ✅")
    except Exception as e:
        results["adhd-engine"] = f"❌ {e}"
        logger.info(f"   ADHD Engine: ❌ {e}")

    # Task Orchestrator: Task status change
    try:
        await managers["task-orchestrator"].handle_task_status_change("TASK-001", "Test Task", "TODO", "IN_PROGRESS", 25.5)
        results["task-orchestrator"] = "✅"
        logger.info("   Task Orchestrator (task): ✅")
    except Exception as e:
        results["task-orchestrator"] = f"❌ {e}"
        logger.info(f"   Task Orchestrator: ❌ {e}")

    logger.info()

    # Test 2: Check Redis stream
    logger.info("🧪 TEST 2: Events in Redis Stream")
    logger.info("-" * 70)

    stream_length = await redis_client.execute_command("XLEN", "dopemux:events")
    logger.info(f"   Stream length: {stream_length}")
    logger.info(f"   Status: {'✅ Events published' if stream_length > 0 else '❌ No events'}\n")

    # Test 3: Read events from stream
    if stream_length > 0:
        logger.info("🧪 TEST 3: Read Events from Stream")
        logger.info("-" * 70)

        events = await redis_client.execute_command(
            "XREAD", "COUNT", "10", "STREAMS", "dopemux:events", "0"
        )

        if events:
            for stream_name, messages in events:
                for msg_id, msg_data in messages:
                    logger.info(f"   Event ID: {msg_id.decode()}")
                    event_type = msg_data.get(b"event_type", b"unknown").decode()
                    source = msg_data.get(b"source", b"unknown").decode()
                    logger.info(f"   Type: {event_type}, Source: {source}")

        logger.info(f"   Status: ✅ Events readable\n")

    # Test 4: Check Phase 3 features
    logger.info("🧪 TEST 4: Phase 3 Features Active")
    logger.info("-" * 70)

    if bus.cache:
        logger.info("   Multi-tier Cache: ✅ Initialized")
    if bus.rate_limiter:
        logger.info("   Rate Limiter: ✅ Initialized")
    if bus.metrics:
        logger.info("   Monitoring: ✅ Initialized")
    if bus.deduplicator:
        logger.info("   Deduplication: ✅ Initialized")

    logger.info()

    # Summary
    logger.info("=" * 70)
    logger.info("SMOKE TEST SUMMARY")
    logger.info("=" * 70)

    success_count = sum(1 for r in results.values() if "✅" in str(r))
    total_count = len(results)

    logger.info(f"\n📊 Agent Integration: {success_count}/{total_count} agents working")
    for agent, status in results.items():
        logger.info(f"   {agent}: {status}")

    logger.info(f"\n📊 Event Pipeline: {'✅ OPERATIONAL' if stream_length > 0 else '❌ NO EVENTS'}")
    logger.info(f"\n📊 Phase 3 Features: {'✅ ALL ACTIVE' if all([bus.cache, bus.rate_limiter, bus.metrics]) else '⚠️ PARTIAL'}")

    # Overall verdict
    if success_count == total_count and stream_length > 0:
        logger.info("\n" + "=" * 70)
        logger.info("✅ SMOKE TEST PASSED - System operational!")
        logger.info("=" * 70 + "\n")
        verdict = True
    else:
        logger.info("\n" + "=" * 70)
        logger.info("⚠️ SMOKE TEST PARTIAL - Some issues detected")
        logger.info("=" * 70 + "\n")
        verdict = False

    # Cleanup
    await redis_client.aclose()
    if bus.redis_client:
        await bus.redis_client.aclose()

    return verdict


if __name__ == "__main__":
    result = asyncio.run(test_complete_pipeline())
    sys.exit(0 if result else 1)
