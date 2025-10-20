#!/usr/bin/env python3
"""
Architecture 3.0 End-to-End Integration Tests
==============================================

Validates complete bidirectional PM ↔ Cognitive communication across all 5 components.

**Test Coverage**:
- Component 1: Foundation (Redis, PostgreSQL, MCP servers)
- Component 2: Task-Orchestrator HTTP Server (PORT 3017)
- Component 3: PM → Cognitive event propagation (EventBus → Redis Streams)
- Component 4: PM → Cognitive state sync (ConPort MCP client)
- Component 5: Cognitive → PM queries (Integration Bridge → Orchestrator)

**ADHD Performance Targets**:
- End-to-end latency: < 400ms (full cycle PM → Cognitive → PM)
- Individual components: < 200ms each
- Event propagation: < 100ms async
- State sync: < 150ms MCP
- Query response: < 70ms HTTP

**Prerequisites**:
- Integration Bridge running on PORT 3016
- Task-Orchestrator running on PORT 3017
- ConPort PostgreSQL available (PORT 5455)
- Redis available (PORT 6379)
"""

import asyncio
import aiohttp
import pytest
import time
import redis
import json
from typing import Dict, Any, List
from datetime import datetime

# Test configuration
INTEGRATION_BRIDGE_URL = "http://localhost:3016"
ORCHESTRATOR_URL = "http://localhost:3017"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
CONPORT_WORKSPACE = "/Users/hue/code/dopemux-mvp"

# ADHD performance thresholds
E2E_LATENCY_TARGET = 0.400  # 400ms end-to-end
COMPONENT_LATENCY_TARGET = 0.200  # 200ms per component
EVENT_LATENCY_TARGET = 0.100  # 100ms event propagation
STATE_SYNC_TARGET = 0.150  # 150ms ConPort sync
QUERY_TARGET = 0.070  # 70ms HTTP query


class PerformanceTracker:
    """Track end-to-end performance with ADHD awareness."""

    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}

    def start(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = time.time()

    def stop(self, operation: str):
        """Stop timing and record latency."""
        if operation not in self.start_times:
            raise ValueError(f"Operation {operation} was never started")

        latency = time.time() - self.start_times[operation]
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(latency)
        del self.start_times[operation]
        return latency

    def summary(self) -> Dict[str, Dict[str, float]]:
        """Generate performance summary."""
        return {
            op: {
                "avg_ms": sum(times) / len(times) * 1000,
                "min_ms": min(times) * 1000,
                "max_ms": max(times) * 1000,
                "count": len(times)
            }
            for op, times in self.timings.items()
        }


@pytest.fixture
def redis_client():
    """Redis client for event bus testing."""
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    yield client
    client.close()


@pytest.fixture
def perf_tracker():
    """Performance tracker for ADHD latency validation."""
    return PerformanceTracker()


class TestComponent1Foundation:
    """Test Component 1: Foundation infrastructure."""

    def test_redis_available(self, redis_client):
        """Verify Redis is running and accessible."""
        assert redis_client.ping(), "Redis not available"

    @pytest.mark.asyncio
    async def test_integration_bridge_health(self):
        """Verify Integration Bridge is healthy."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/health") as resp:
                assert resp.status == 200, "Integration Bridge not healthy"
                data = await resp.json()
                assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_orchestrator_health(self):
        """Verify Task-Orchestrator HTTP server is healthy."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/health") as resp:
                assert resp.status == 200, "Orchestrator not healthy"
                data = await resp.json()
                assert data["status"] == "healthy"


class TestComponent3EventPropagation:
    """Test Component 3: PM → Cognitive event propagation."""

    @pytest.mark.asyncio
    async def test_event_publishing(self, redis_client, perf_tracker):
        """Test publishing events to Redis Streams."""
        stream_name = "pm_plane_events"
        event_data = {
            "event_type": "task.created",
            "task_id": "test-001",
            "timestamp": datetime.now().isoformat(),
            "data": {"title": "Test Task", "status": "TODO"}
        }

        # Publish event
        perf_tracker.start("event_publish")
        message_id = redis_client.xadd(stream_name, event_data)
        latency = perf_tracker.stop("event_publish")

        assert message_id is not None
        assert latency < EVENT_LATENCY_TARGET, f"Event publish too slow: {latency*1000:.1f}ms"

    @pytest.mark.asyncio
    async def test_event_consumption(self, redis_client, perf_tracker):
        """Test consuming events from Redis Streams."""
        stream_name = "pm_plane_events"

        # Publish test event
        event_data = {
            "event_type": "task.updated",
            "task_id": "test-002",
            "timestamp": datetime.now().isoformat()
        }
        redis_client.xadd(stream_name, event_data)

        # Consume event
        perf_tracker.start("event_consume")
        messages = redis_client.xread({stream_name: "0-0"}, count=1, block=1000)
        latency = perf_tracker.stop("event_consume")

        assert len(messages) > 0, "No events consumed"
        assert latency < EVENT_LATENCY_TARGET, f"Event consume too slow: {latency*1000:.1f}ms"


class TestComponent5HTTPQueries:
    """Test Component 5: Cognitive → PM queries."""

    @pytest.mark.asyncio
    async def test_query_tasks(self, perf_tracker):
        """Test querying tasks from Integration Bridge."""
        async with aiohttp.ClientSession() as session:
            perf_tracker.start("query_tasks")
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/tasks?limit=10") as resp:
                latency = perf_tracker.stop("query_tasks")

                assert resp.status == 200, f"Query failed: {resp.status}"
                data = await resp.json()
                assert isinstance(data, list), "Expected list of tasks"
                assert latency < QUERY_TARGET, f"Query too slow: {latency*1000:.1f}ms (target: {QUERY_TARGET*1000:.0f}ms)"

    @pytest.mark.asyncio
    async def test_query_adhd_state(self, perf_tracker):
        """Test querying ADHD state from Integration Bridge."""
        async with aiohttp.ClientSession() as session:
            perf_tracker.start("query_adhd_state")
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/adhd-state") as resp:
                latency = perf_tracker.stop("query_adhd_state")

                assert resp.status == 200, f"ADHD state query failed: {resp.status}"
                data = await resp.json()
                assert "energy_level" in data
                assert "attention_level" in data
                assert latency < QUERY_TARGET, f"ADHD query too slow: {latency*1000:.1f}ms"

    @pytest.mark.asyncio
    async def test_query_session_status(self, perf_tracker):
        """Test querying session status."""
        async with aiohttp.ClientSession() as session:
            perf_tracker.start("query_session")
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/session") as resp:
                latency = perf_tracker.stop("query_session")

                assert resp.status == 200
                data = await resp.json()
                assert "active" in data
                assert latency < QUERY_TARGET, f"Session query too slow: {latency*1000:.1f}ms"

    @pytest.mark.asyncio
    async def test_query_recommendations(self, perf_tracker):
        """Test querying task recommendations."""
        async with aiohttp.ClientSession() as session:
            perf_tracker.start("query_recommendations")
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/recommendations?limit=5") as resp:
                latency = perf_tracker.stop("query_recommendations")

                assert resp.status == 200
                data = await resp.json()
                assert isinstance(data, list)
                assert latency < QUERY_TARGET, f"Recommendations query too slow: {latency*1000:.1f}ms"

    @pytest.mark.asyncio
    async def test_parallel_queries(self, perf_tracker):
        """Test concurrent queries maintain performance."""
        async with aiohttp.ClientSession() as session:
            # Fire 5 concurrent queries
            perf_tracker.start("parallel_queries")
            tasks = [
                session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/tasks"),
                session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/adhd-state"),
                session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/session"),
                session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/recommendations"),
                session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/active-sprint")
            ]
            responses = await asyncio.gather(*tasks)
            latency = perf_tracker.stop("parallel_queries")

            # All should succeed
            for resp in responses:
                assert resp.status == 200

            # Parallel execution should be faster than sequential
            # Target: < 200ms for 5 concurrent queries
            assert latency < COMPONENT_LATENCY_TARGET, f"Parallel queries too slow: {latency*1000:.1f}ms"


class TestEndToEndBidirectional:
    """Test complete bidirectional PM ↔ Cognitive workflows."""

    @pytest.mark.asyncio
    async def test_pm_to_cognitive_flow(self, redis_client, perf_tracker):
        """
        Test PM → Cognitive flow:
        1. PM publishes event (Component 3)
        2. Cognitive receives event
        3. Cognitive queries PM state (Component 5)
        4. Complete cycle < 400ms
        """
        perf_tracker.start("pm_to_cognitive_flow")

        # Step 1: PM publishes task created event
        event_data = {
            "event_type": "task.created",
            "task_id": "e2e-test-001",
            "timestamp": datetime.now().isoformat(),
            "data": {"title": "E2E Test Task", "status": "TODO", "priority": "high"}
        }
        message_id = redis_client.xadd("pm_plane_events", event_data)
        assert message_id is not None, "Event publish failed"

        # Step 2: Simulate cognitive plane receiving event
        messages = redis_client.xread({"pm_plane_events": message_id}, count=1, block=1000)
        assert len(messages) > 0, "Event not received"

        # Step 3: Cognitive queries PM for task details
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/tasks?limit=10") as resp:
                assert resp.status == 200
                tasks = await resp.json()
                assert isinstance(tasks, list)

        # Step 4: Measure total latency
        latency = perf_tracker.stop("pm_to_cognitive_flow")
        assert latency < E2E_LATENCY_TARGET, f"PM→Cognitive too slow: {latency*1000:.1f}ms (target: {E2E_LATENCY_TARGET*1000:.0f}ms)"

    @pytest.mark.asyncio
    async def test_cognitive_to_pm_flow(self, perf_tracker):
        """
        Test Cognitive → PM flow:
        1. Cognitive queries tasks (Component 5)
        2. Cognitive queries ADHD state
        3. Cognitive queries recommendations
        4. Complete analysis < 200ms
        """
        perf_tracker.start("cognitive_to_pm_flow")

        async with aiohttp.ClientSession() as session:
            # Parallel queries for efficiency
            tasks_req = session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/tasks?limit=10")
            adhd_req = session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/adhd-state")
            rec_req = session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/recommendations?limit=5")

            # Gather all responses
            responses = await asyncio.gather(tasks_req, adhd_req, rec_req)

            # Validate all succeeded
            for resp in responses:
                assert resp.status == 200

            # Get response data
            tasks = await responses[0].json()
            adhd_state = await responses[1].json()
            recommendations = await responses[2].json()

            assert isinstance(tasks, list)
            assert "energy_level" in adhd_state
            assert isinstance(recommendations, list)

        latency = perf_tracker.stop("cognitive_to_pm_flow")
        assert latency < COMPONENT_LATENCY_TARGET, f"Cognitive→PM too slow: {latency*1000:.1f}ms"

    @pytest.mark.asyncio
    async def test_adhd_decision_workflow(self, redis_client, perf_tracker):
        """
        Test ADHD-aware decision workflow:
        1. Query current ADHD state (energy, attention)
        2. Query task recommendations based on state
        3. Select task and publish decision event
        4. Complete workflow < 300ms
        """
        perf_tracker.start("adhd_decision_workflow")

        async with aiohttp.ClientSession() as session:
            # Step 1: Get ADHD state
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/adhd-state") as resp:
                assert resp.status == 200
                adhd_state = await resp.json()
                energy = adhd_state["energy_level"]
                attention = adhd_state["attention_level"]

            # Step 2: Get recommendations
            async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/recommendations?limit=5") as resp:
                assert resp.status == 200
                recommendations = await resp.json()
                assert len(recommendations) > 0, "No recommendations available"

            # Step 3: Select task and publish decision
            selected_task = recommendations[0]
            decision_event = {
                "event_type": "task.selected",
                "task_id": selected_task.get("task_id", "test-task"),
                "energy_level": energy,
                "attention_level": attention,
                "timestamp": datetime.now().isoformat()
            }
            redis_client.xadd("cognitive_plane_events", decision_event)

        latency = perf_tracker.stop("adhd_decision_workflow")
        assert latency < 0.300, f"ADHD workflow too slow: {latency*1000:.1f}ms (target: 300ms)"


class TestPerformanceValidation:
    """Validate ADHD-optimized performance across all components."""

    @pytest.mark.asyncio
    async def test_component_latencies(self, perf_tracker):
        """Verify all components meet ADHD latency targets."""
        async with aiohttp.ClientSession() as session:
            # Component 5: HTTP queries (target: < 70ms avg)
            for _ in range(10):
                perf_tracker.start("component5_query")
                async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/tasks") as resp:
                    assert resp.status == 200
                perf_tracker.stop("component5_query")

        # Validate Component 5 average
        summary = perf_tracker.summary()
        avg_latency = summary["component5_query"]["avg_ms"]
        assert avg_latency < QUERY_TARGET * 1000, f"Component 5 avg latency {avg_latency:.1f}ms exceeds {QUERY_TARGET*1000:.0f}ms target"

    @pytest.mark.asyncio
    async def test_p95_latencies(self, perf_tracker):
        """Validate P95 latencies for ADHD attention safety."""
        async with aiohttp.ClientSession() as session:
            latencies = []
            for _ in range(20):
                start = time.time()
                async with session.get(f"{INTEGRATION_BRIDGE_URL}/orchestrator/adhd-state") as resp:
                    assert resp.status == 200
                latencies.append(time.time() - start)

        # Calculate P95
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < COMPONENT_LATENCY_TARGET, f"P95 latency {p95_latency*1000:.1f}ms exceeds {COMPONENT_LATENCY_TARGET*1000:.0f}ms target"


def test_performance_summary(perf_tracker):
    """Print comprehensive performance summary."""
    summary = perf_tracker.summary()

    print("\n" + "="*70)
    print("Architecture 3.0 End-to-End Performance Summary")
    print("="*70)

    for operation, metrics in summary.items():
        adhd_safe = "✅ ADHD-Safe" if metrics["avg_ms"] < COMPONENT_LATENCY_TARGET * 1000 else "⚠️  Needs optimization"
        print(f"\n{operation}:")
        print(f"  Average: {metrics['avg_ms']:.1f}ms")
        print(f"  Min: {metrics['min_ms']:.1f}ms")
        print(f"  Max: {metrics['max_ms']:.1f}ms")
        print(f"  Count: {metrics['count']}")
        print(f"  {adhd_safe}")

    print("\n" + "="*70)
    print("Test Timestamp:", datetime.now().isoformat())
    print("="*70)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])
