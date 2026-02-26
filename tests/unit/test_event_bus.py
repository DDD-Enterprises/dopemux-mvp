import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from dopemux.event_bus import InMemoryAdapter, RedisStreamsAdapter, DopemuxEvent, Priority, Envelope

class TestInMemoryAdapter:
    @pytest.mark.asyncio
    async def test_publish_direct_match(self):
        adapter = InMemoryAdapter()
        callback = AsyncMock()
        await adapter.subscribe("test.namespace", callback)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_multiple_subscribers(self):
        adapter = InMemoryAdapter()
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        await adapter.subscribe("test.namespace", callback1)
        await adapter.subscribe("test.namespace", callback2)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_wildcard_match_all(self):
        adapter = InMemoryAdapter()
        callback = AsyncMock()
        await adapter.subscribe("*", callback)

        event = DopemuxEvent.create("test", "any.namespace", {"data": "value"})
        await adapter.publish(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_wildcard_match_prefix(self):
        adapter = InMemoryAdapter()
        callback = AsyncMock()
        await adapter.subscribe("test.*", callback)

        event1 = DopemuxEvent.create("test", "test.one", {"data": "1"})
        event2 = DopemuxEvent.create("test", "test.two", {"data": "2"})
        event3 = DopemuxEvent.create("test", "other.one", {"data": "3"})

        await adapter.publish(event1)
        await adapter.publish(event2)
        await adapter.publish(event3)

        assert callback.call_count == 2
        callback.assert_any_call(event1)
        callback.assert_any_call(event2)

    @pytest.mark.asyncio
    async def test_publish_no_match(self):
        adapter = InMemoryAdapter()
        callback = AsyncMock()
        await adapter.subscribe("other.namespace", callback)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_sync_callback(self):
        adapter = InMemoryAdapter()
        callback = MagicMock()
        await adapter.subscribe("test.namespace", callback)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_error_handling(self):
        adapter = InMemoryAdapter()

        callback1 = AsyncMock(side_effect=Exception("Failed"))
        callback2 = AsyncMock()

        await adapter.subscribe("test.namespace", callback1)
        await adapter.subscribe("test.namespace", callback2)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})

        # Should not raise exception
        result = await adapter.publish(event)

        assert result is True
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)

    def test_matches_missing_namespace(self):
        adapter = InMemoryAdapter()
        # Create an event without envelope/namespace if possible, or just mock it
        event = MagicMock()
        del event.envelope

        # InMemoryAdapter._matches returns True if event doesn't have envelope.namespace
        assert adapter._matches("any.pattern", event) is True

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        adapter = InMemoryAdapter()
        callback = AsyncMock()
        sub_id = await adapter.subscribe("test.namespace", callback)

        await adapter.unsubscribe(sub_id)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        callback.assert_not_called()

class TestRedisStreamsAdapter:
    @pytest.mark.asyncio
    async def test_publish_local_dispatch_when_disconnected(self):
        adapter = RedisStreamsAdapter(redis_url="redis://localhost")
        assert adapter.connected is False

        callback = AsyncMock()
        await adapter.subscribe("test.namespace", callback)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_local_dispatch_when_connected(self):
        adapter = RedisStreamsAdapter(redis_url="redis://localhost")
        await adapter.connect()
        assert adapter.connected is True

        callback = AsyncMock()
        await adapter.subscribe("test.namespace", callback)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        # In current implementation, it still does local dispatch
        callback.assert_called_once_with(event)

    def test_matches_behavior(self):
        adapter = RedisStreamsAdapter(redis_url="redis://localhost")

        # Test * match
        event = DopemuxEvent.create("test", "any", {})
        assert adapter._matches("*", event) is True

        # Test prefix match
        assert adapter._matches("test.*", event) is False
        event2 = DopemuxEvent.create("test", "test.foo", {})
        assert adapter._matches("test.*", event2) is True

        # Test direct match
        assert adapter._matches("test.foo", event2) is True
        assert adapter._matches("test.bar", event2) is False

    def test_matches_missing_namespace(self):
        adapter = RedisStreamsAdapter(redis_url="redis://localhost")
        event = MagicMock()
        event.envelope = MagicMock()
        del event.envelope.namespace # Make it missing

        # RedisStreamsAdapter uses getattr(event.envelope, "namespace", "")
        # So it defaults to ""
        assert adapter._matches("test.*", event) is False
        assert adapter._matches("*", event) is True

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        adapter = RedisStreamsAdapter(redis_url="redis://localhost")
        callback = AsyncMock()
        sub_id = await adapter.subscribe("test.namespace", callback)

        await adapter.unsubscribe(sub_id)

        event = DopemuxEvent.create("test", "test.namespace", {"data": "value"})
        await adapter.publish(event)

        callback.assert_not_called()
