import asyncio
import logging
from src.dopemux.event_bus import InMemoryAdapter, DopemuxEvent, Priority

async def test_unsubscribe_during_publish():
    bus = InMemoryAdapter()

    sub_id = None

    async def callback(event):
        nonlocal sub_id
        print(f"Callback called, unsubscribing {sub_id}")
        await bus.unsubscribe(sub_id)

    sub_id = await bus.subscribe("test.*", callback)

    event = DopemuxEvent.create("test", "test.event", {}, priority=Priority.NORMAL)

    try:
        await bus.publish(event)
        print("Publish successful")
    except RuntimeError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_unsubscribe_during_publish())
