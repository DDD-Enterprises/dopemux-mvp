"""
Tests for Event Deduplication
Validates duplicate detection, TTL expiry, and performance
"""

import asyncio
import hashlib
import json
import pytest
import time
from datetime import datetime

import redis.asyncio as redis

from event_deduplication import EventDeduplicator
from event_bus import Event, EventBus


class TestEventDeduplicator:
    """Test suite for EventDeduplicator"""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        client = redis.from_url(
            "redis://localhost:6379",
            db=15,  # Use separate test database
            decode_responses=True
        )

        # Clear test database
        await client.flushdb()

        yield client

        # Cleanup
        await client.flushdb()
        await client.close()

    @pytest.fixture
    async def deduplicator(self, redis_client):
        """Create EventDeduplicator instance"""
        return EventDeduplicator(
            redis_client=redis_client,
            ttl_seconds=2,  # Short TTL for testing
            key_prefix="test_dedup"
        )

    @pytest.mark.asyncio
    async def test_duplicate_detection_within_window(self, deduplicator):
        """Test that duplicate events are detected within TTL window"""
        # Create event data
        event_data = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test"
        }

        # First check should return False (not a duplicate)
        is_dup_1 = await deduplicator.is_duplicate(event_data)
        assert is_dup_1 is False, "First event should not be detected as duplicate"

        # Mark as processed
        await deduplicator.mark_processed(event_data)

        # Second check should return True (is a duplicate)
        is_dup_2 = await deduplicator.is_duplicate(event_data)
        assert is_dup_2 is True, "Second event should be detected as duplicate"

    @pytest.mark.asyncio
    async def test_different_events_not_duplicates(self, deduplicator):
        """Test that different events are not detected as duplicates"""
        event_1 = {
            "type": "test.event",
            "data": {"key": "value1"},
            "source": "test"
        }

        event_2 = {
            "type": "test.event",
            "data": {"key": "value2"},  # Different data
            "source": "test"
        }

        # Mark first event
        await deduplicator.mark_processed(event_1)

        # Second event should not be duplicate (different content)
        is_dup = await deduplicator.is_duplicate(event_2)
        assert is_dup is False, "Events with different data should not be duplicates"

    @pytest.mark.asyncio
    async def test_ttl_expiry_allows_reprocessing(self, deduplicator):
        """Test that events can be reprocessed after TTL expires"""
        event_data = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test"
        }

        # Mark as processed
        await deduplicator.mark_processed(event_data)

        # Should be duplicate immediately
        is_dup_1 = await deduplicator.is_duplicate(event_data)
        assert is_dup_1 is True, "Should be duplicate within TTL"

        # Wait for TTL to expire (2 seconds + buffer)
        await asyncio.sleep(2.5)

        # Should no longer be duplicate after TTL
        is_dup_2 = await deduplicator.is_duplicate(event_data)
        assert is_dup_2 is False, "Should not be duplicate after TTL expiry"

    @pytest.mark.asyncio
    async def test_check_and_mark_combined_operation(self, deduplicator):
        """Test combined check_and_mark operation"""
        event_data = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test"
        }

        # First call should return True (new event) and mark it
        is_new_1 = await deduplicator.check_and_mark(event_data)
        assert is_new_1 is True, "First event should be new"

        # Second call should return False (duplicate)
        is_new_2 = await deduplicator.check_and_mark(event_data)
        assert is_new_2 is False, "Second event should be duplicate"

    @pytest.mark.asyncio
    async def test_content_hash_stability(self, deduplicator):
        """Test that content hash is stable across calls"""
        event_data = {
            "type": "test.event",
            "data": {"key1": "value1", "key2": "value2"},
            "source": "test"
        }

        # Compute hash twice
        hash_1 = deduplicator._compute_content_hash(event_data)
        hash_2 = deduplicator._compute_content_hash(event_data)

        assert hash_1 == hash_2, "Content hash should be stable"

        # Verify hash is SHA256 (64 hex characters)
        assert len(hash_1) == 64, "SHA256 hash should be 64 hex characters"

    @pytest.mark.asyncio
    async def test_timestamp_not_included_in_hash(self, deduplicator):
        """Test that timestamp differences don't affect hash"""
        event_1 = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test",
            "timestamp": "2025-01-01T00:00:00"
        }

        event_2 = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test",
            "timestamp": "2025-01-01T00:01:00"  # Different timestamp
        }

        hash_1 = deduplicator._compute_content_hash(event_1)
        hash_2 = deduplicator._compute_content_hash(event_2)

        assert hash_1 == hash_2, "Timestamps should not affect content hash"

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, deduplicator):
        """Test that deduplication metrics are tracked correctly"""
        # Reset metrics
        deduplicator.reset_metrics()

        event_data = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test"
        }

        # First event (not duplicate)
        await deduplicator.check_and_mark(event_data)

        # Second event (duplicate)
        await deduplicator.check_and_mark(event_data)

        # Third event (duplicate)
        await deduplicator.check_and_mark(event_data)

        metrics = deduplicator.get_metrics()

        assert metrics["total_checks"] == 3, "Should have 3 total checks"
        assert metrics["duplicates_found"] == 2, "Should have found 2 duplicates"
        assert metrics["dedup_rate_percent"] == 66.67, "Dedup rate should be 66.67%"
        assert metrics["errors"] == 0, "Should have no errors"

    @pytest.mark.asyncio
    async def test_performance_under_2ms(self, deduplicator):
        """Test that deduplication overhead is <2ms per event"""
        event_data = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test"
        }

        # Warm up
        await deduplicator.check_and_mark(event_data)

        # Measure 100 operations
        start_time = time.time()

        for i in range(100):
            event_data["data"]["iteration"] = i
            await deduplicator.check_and_mark(event_data)

        elapsed_ms = (time.time() - start_time) * 1000
        avg_ms_per_op = elapsed_ms / 100

        print(f"Average deduplication time: {avg_ms_per_op:.2f}ms")

        assert avg_ms_per_op < 2.0, f"Deduplication should be <2ms, got {avg_ms_per_op:.2f}ms"


class TestEventBusDeduplication:
    """Test EventBus integration with deduplication"""

    @pytest.fixture
    async def event_bus(self):
        """Create EventBus instance for testing"""
        bus = EventBus(
            redis_url="redis://localhost:6379",
            enable_deduplication=True
        )

        await bus.initialize()

        # Clear test stream
        if bus.redis_client:
            try:
                await bus.redis_client.delete("test:stream")
            except:
                pass

        yield bus

        # Cleanup
        if bus.redis_client:
            try:
                await bus.redis_client.delete("test:stream")
            except:
                pass
            await bus.redis_client.close()

    @pytest.mark.asyncio
    async def test_duplicate_events_not_published(self, event_bus):
        """Test that duplicate events are not published to stream"""
        event = Event(
            type="test.event",
            data={"key": "value"},
            source="test"
        )

        # Publish first time
        msg_id_1 = await event_bus.publish("test:stream", event)
        assert msg_id_1 is not None, "First event should be published"

        # Publish same event again
        msg_id_2 = await event_bus.publish("test:stream", event)
        assert msg_id_2 is None, "Duplicate event should not be published"

        # Verify only one event in stream
        if event_bus.redis_client:
            stream_length = await event_bus.redis_client.xlen("test:stream")
            assert stream_length == 1, "Stream should contain only one event"

    @pytest.mark.asyncio
    async def test_deduplication_can_be_disabled(self):
        """Test that deduplication can be disabled"""
        bus = EventBus(
            redis_url="redis://localhost:6379",
            enable_deduplication=False  # Disabled
        )

        await bus.initialize()

        event = Event(
            type="test.event",
            data={"key": "value"},
            source="test"
        )

        # Publish same event twice
        msg_id_1 = await bus.publish("test:stream", event)
        msg_id_2 = await bus.publish("test:stream", event)

        assert msg_id_1 is not None, "First event should be published"
        assert msg_id_2 is not None, "Second event should be published (dedup disabled)"

        # Cleanup
        if bus.redis_client:
            await bus.redis_client.delete("test:stream")
            await bus.redis_client.close()

    @pytest.mark.asyncio
    async def test_deduplication_metrics_accessible(self, event_bus):
        """Test that deduplication metrics can be retrieved"""
        event = Event(
            type="test.event",
            data={"key": "value"},
            source="test"
        )

        # Publish twice (second should be duplicate)
        await event_bus.publish("test:stream", event)
        await event_bus.publish("test:stream", event)

        # Get metrics
        if event_bus.deduplicator:
            metrics = event_bus.deduplicator.get_metrics()

            assert metrics["total_checks"] >= 1, "Should have at least 1 check"
            assert metrics["duplicates_found"] >= 1, "Should have found at least 1 duplicate"
            assert "dedup_rate_percent" in metrics, "Should include dedup rate"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
