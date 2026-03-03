import asyncio
import pytest
from dopemux.event_bus import InMemoryAdapter, DopemuxEvent, Priority

@pytest.mark.asyncio
async def test_unsubscribe_during_publish():
    bus = InMemoryAdapter()

    sub_id = None
    callback_called = 0

    async def callback(event):
        nonlocal sub_id, callback_called
        callback_called += 1
        # This modification of the subscribers dict during iteration should handle gracefully
        await bus.unsubscribe(sub_id)

    sub_id = await bus.subscribe("test.*", callback)

    event = DopemuxEvent.create("test", "test.event", {}, priority=Priority.NORMAL)

    # This should NOT raise RuntimeError
    await bus.publish(event)
    assert callback_called == 1

    # Verify unsubscription worked
    await bus.publish(event)
    assert callback_called == 1

@pytest.mark.asyncio
async def test_unsubscribe_other_during_publish():
    """Test unsubscribing a DIFFERENT subscriber during publish loop."""
    bus = InMemoryAdapter()

    sub_id_1 = None
    sub_id_2 = None
    callback_1_called = 0
    callback_2_called = 0

    async def callback_1(event):
        nonlocal sub_id_2, callback_1_called
        callback_1_called += 1
        # Unsubscribe the *other* callback
        await bus.unsubscribe(sub_id_2)

    async def callback_2(event):
        nonlocal callback_2_called
        callback_2_called += 1

    sub_id_1 = await bus.subscribe("test.*", callback_1)
    sub_id_2 = await bus.subscribe("test.*", callback_2)

    event = DopemuxEvent.create("test", "test.event", {}, priority=Priority.NORMAL)

    # This should NOT raise RuntimeError
    await bus.publish(event)
    assert callback_1_called == 1
    
    # Verify unsubscription worked for callback_2
    # Note: callback_2 might or might not have been called in the first publish depending on order
    # but it definitely shouldn't be called in the second.
    initial_c2_calls = callback_2_called
    await bus.publish(event)
    assert callback_1_called == 2
    assert callback_2_called == initial_c2_calls
