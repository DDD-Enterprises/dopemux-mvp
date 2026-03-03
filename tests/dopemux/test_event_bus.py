import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.dopemux.event_bus import (
    DopemuxEvent,
    InMemoryAdapter,
    RedisStreamsAdapter,
    Priority,
    CognitiveLoad,
    ADHDMetadata,
    Envelope
)

# --- DopemuxEvent Tests ---

def test_dopemux_event_create():
    """Test creating a DopemuxEvent via the create factory method."""
    payload = {"key": "value"}
    event = DopemuxEvent.create(
        event_type="test.type",
        namespace="test.namespace",
        payload=payload,
        priority=Priority.HIGH,
        cognitive_load=CognitiveLoad.MEDIUM,
        source="test_source",
        instance_id="inst-1"
    )

    assert isinstance(event, DopemuxEvent)
    assert isinstance(event.envelope, Envelope)
    assert event.envelope.type == "test.type"
    assert event.envelope.namespace == "test.namespace"
    assert event.envelope.priority == Priority.HIGH
    assert event.payload == payload
    assert event.source == "test_source"
    assert event.instance_id == "inst-1"

def test_dopemux_event_adhd_metadata():
    """Test DopemuxEvent with ADHD metadata."""
    metadata = ADHDMetadata(interruption_allowed=False, focus_required=True)
    event = DopemuxEvent.create(
        event_type="test.adhd",
        namespace="test.ns",
        payload={},
        adhd_metadata=metadata
    )
    assert event.adhd_metadata == metadata
    assert event.adhd_metadata.interruption_allowed is False
    assert event.adhd_metadata.focus_required is True


# --- InMemoryAdapter Tests ---

@pytest.mark.asyncio
async def test_in_memory_subscribe_publish_async():
    """Test subscribing and publishing with an async callback."""
    bus = InMemoryAdapter()
    callback = AsyncMock()

    await bus.subscribe("test.event", callback)

    event = DopemuxEvent.create("test.event", "test.event", {})
    await bus.publish(event)

    callback.assert_awaited_once_with(event)

@pytest.mark.asyncio
async def test_in_memory_subscribe_publish_sync():
    """Test subscribing and publishing with a sync callback."""
    bus = InMemoryAdapter()
    callback = Mock()

    await bus.subscribe("test.event", callback)

    event = DopemuxEvent.create("test.event", "test.event", {})
    await bus.publish(event)

    callback.assert_called_once_with(event)

@pytest.mark.asyncio
async def test_in_memory_unsubscribe():
    """Test unsubscribing removes the callback."""
    bus = InMemoryAdapter()
    callback = Mock()

    sub_id = await bus.subscribe("test.event", callback)
    await bus.unsubscribe(sub_id)

    event = DopemuxEvent.create("test.event", "test.event", {})
    await bus.publish(event)

    callback.assert_not_called()

@pytest.mark.asyncio
async def test_in_memory_pattern_matching_exact():
    """Test exact pattern matching."""
    bus = InMemoryAdapter()
    callback = Mock()
    await bus.subscribe("a.b.c", callback)

    # Match
    event_match = DopemuxEvent.create("type", "a.b.c", {})
    await bus.publish(event_match)
    callback.assert_called_once_with(event_match)
    callback.reset_mock()

    # No match
    event_no_match = DopemuxEvent.create("type", "a.b.x", {})
    await bus.publish(event_no_match)
    callback.assert_not_called()

@pytest.mark.asyncio
async def test_in_memory_pattern_matching_wildcard_suffix():
    """Test wildcard matching with suffix (e.g. 'prefix.*')."""
    bus = InMemoryAdapter()
    callback = Mock()
    await bus.subscribe("a.b.*", callback)

    # Match
    event_match = DopemuxEvent.create("type", "a.b.c", {})
    await bus.publish(event_match)
    callback.assert_called_once_with(event_match)
    callback.reset_mock()

    # No match
    event_no_match = DopemuxEvent.create("type", "a.x.c", {})
    await bus.publish(event_no_match)
    callback.assert_not_called()

@pytest.mark.asyncio
async def test_in_memory_pattern_matching_wildcard_all():
    """Test wildcard matching for all events ('*')."""
    bus = InMemoryAdapter()
    callback = Mock()
    await bus.subscribe("*", callback)

    event = DopemuxEvent.create("type", "any.thing", {})
    await bus.publish(event)
    callback.assert_called_once_with(event)

@pytest.mark.asyncio
async def test_in_memory_callback_error_handling():
    """Test that an error in one subscriber doesn't block others."""
    bus = InMemoryAdapter()

    # Faulty callback
    fail_callback = Mock(side_effect=Exception("Boom"))
    await bus.subscribe("test.event", fail_callback)

    # Good callback
    success_callback = Mock()
    await bus.subscribe("test.event", success_callback)

    event = DopemuxEvent.create("type", "test.event", {})
    await bus.publish(event)

    fail_callback.assert_called_once()
    success_callback.assert_called_once()


# --- RedisStreamsAdapter Tests ---

@pytest.mark.asyncio
async def test_redis_adapter_connect_disconnect():
    """Test connection state changes without real Redis."""
    # Since RedisStreamsAdapter.connect just logs currently (based on read_file),
    # checking the flag is sufficient. If it did real connection logic,
    # we would mock the redis client here.
    bus = RedisStreamsAdapter("redis://localhost")
    assert not bus.connected

    # Mocking any potential side effect if implementation changes
    # For now, it just sets self.connected = True
    await bus.connect()
    assert bus.connected

    await bus.disconnect()
    assert not bus.connected

@pytest.mark.asyncio
async def test_redis_adapter_local_fallback():
    """Test that it uses local subscribers even when disconnected (fallback)."""
    bus = RedisStreamsAdapter("redis://localhost")
    # Not connecting, so self.connected is False

    callback = Mock()
    await bus.subscribe("test.event", callback)

    event = DopemuxEvent.create("type", "test.event", {})
    await bus.publish(event)

    callback.assert_called_once_with(event)

@pytest.mark.asyncio
async def test_redis_adapter_pattern_matching():
    """Test pattern matching in Redis adapter (local simulation)."""
    bus = RedisStreamsAdapter("redis://localhost")
    callback = Mock()
    await bus.subscribe("user.*", callback)

    # Match
    event = DopemuxEvent.create("type", "user.created", {})
    await bus.publish(event)
    callback.assert_called_once_with(event)
    callback.reset_mock()

    # No match
    event = DopemuxEvent.create("type", "system.error", {})
    await bus.publish(event)
    callback.assert_not_called()
