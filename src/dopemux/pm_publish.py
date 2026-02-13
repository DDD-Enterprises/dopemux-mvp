"""Trinity-safe PM envelope publish bridge."""

from __future__ import annotations

from typing import Any

from dopemux.event_bus import DopemuxEvent, Priority
from dopemux.pm.adapters import pm_to_bus_event


def pm_envelope_to_dopemux_event(envelope: dict[str, Any]) -> DopemuxEvent:
    """Convert a canonical PM envelope into a DopemuxEvent."""
    bus_event = pm_to_bus_event(envelope)
    namespace = str(bus_event["namespace"])
    if not namespace.startswith("pm."):
        raise ValueError(f"PM namespace must start with 'pm.': {namespace}")

    payload = bus_event["payload"]
    return DopemuxEvent.create(
        event_type="pm",
        namespace=namespace,
        payload=payload,
        priority=Priority.NORMAL,
    )


async def publish_pm_envelope(envelope: dict[str, Any], bus: Any) -> bool:
    """Publish PM envelope through an injected EventBus-compatible instance."""
    if bus is None:
        raise ValueError("bus is required")

    event = pm_envelope_to_dopemux_event(envelope)
    return await bus.publish(event)
