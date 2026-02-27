import asyncio
import pytest
from dopemux.event_bus import InMemoryAdapter, DopemuxEvent, Priority

@pytest.mark.asyncio
async def test_unsubscribe_during_publish():
    bus = InMemoryAdapter()

    sub_id = None
    callback_called = False

    async def callback(event):
        nonlocal sub_id, callback_called
        callback_called = True
        # This modification of the subscribers dict during iteration should handle gracefully
        await bus.unsubscribe(sub_id)

    sub_id = await bus.subscribe("test.*", callback)

    event = DopemuxEvent.create("test", "test.event", {}, priority=Priority.NORMAL)

    # This should NOT raise RuntimeError
    await bus.publish(event)

    # Verify the callback was actually executed
    assert callback_called is True
    # Verify the unsubscription was successful
    assert sub_id not in bus._patterns

@pytest.mark.asyncio
async def test_unsubscribe_other_during_publish():
    """Test unsubscribing a DIFFERENT subscriber during publish loop."""
    bus = InMemoryAdapter()

    sub_id_1 = None
    sub_id_2 = None
    callback_1_called = False
    callback_2_called = False

    async def callback_1(event):
        nonlocal sub_id_2, callback_1_called
        callback_1_called = True
        # Unsubscribe the *other* callback
        await bus.unsubscribe(sub_id_2)

    async def callback_2(event):
        nonlocal callback_2_called
        callback_2_called = True

    sub_id_1 = await bus.subscribe("test.*", callback_1)
    sub_id_2 = await bus.subscribe("test.*", callback_2)

    event = DopemuxEvent.create("test", "test.event", {}, priority=Priority.NORMAL)

    # This should NOT raise RuntimeError
    await bus.publish(event)

    # Verify at least the first callback was executed
    assert callback_1_called is True

    # Depending on iteration order, callback_2 might or might not have been called
    # BEFORE it was unsubscribed.
    # If callback_1 ran first, callback_2 should NOT be called (because we added a check `if sub_id not in self._patterns: continue`)
    # However, since dict iteration order is insertion order in recent Python, callback_1 (subscribed first) runs first.
    # So callback_2 should be removed before it gets a chance to run.

    # Verify unsubscription happened
    assert sub_id_2 not in bus._patterns

    # Verify safety: The loop completed without error
