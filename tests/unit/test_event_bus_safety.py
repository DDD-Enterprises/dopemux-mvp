import asyncio
import pytest
from dopemux.event_bus import InMemoryAdapter, DopemuxEvent, Priority

@pytest.mark.asyncio
async def test_unsubscribe_during_publish():
    bus = InMemoryAdapter()

    sub_id = None

    async def callback(event):
        nonlocal sub_id
        # This modification of the subscribers dict during iteration should handle gracefully
        await bus.unsubscribe(sub_id)

    sub_id = await bus.subscribe("test.*", callback)

    event = DopemuxEvent.create("test", "test.event", {}, priority=Priority.NORMAL)

    # This should NOT raise RuntimeError
    await bus.publish(event)

@pytest.mark.asyncio
async def test_unsubscribe_other_during_publish():
    """Test unsubscribing a DIFFERENT subscriber during publish loop."""
    bus = InMemoryAdapter()

    sub_id_1 = None
    sub_id_2 = None

    async def callback_1(event):
        nonlocal sub_id_2
        # Unsubscribe the *other* callback
        await bus.unsubscribe(sub_id_2)

    async def callback_2(event):
        pass

    sub_id_1 = await bus.subscribe("test.*", callback_1)
    sub_id_2 = await bus.subscribe("test.*", callback_2)

    event = DopemuxEvent.create("test", "test.event", {}, priority=Priority.NORMAL)

    # This should NOT raise RuntimeError
    await bus.publish(event)
