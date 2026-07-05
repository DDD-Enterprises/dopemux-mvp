"""
Best-effort mirror of promotable events onto the dope-memory input stream.

The dope-memory EventBusConsumer subscribes only to MEMORY_INPUT_STREAM
(activity.events.v1, see services/working-memory-assistant/eventbus_consumer.py),
while the bridge's general event traffic flows on other streams (typically
dopemux:events, which has its own consumers: DDG pattern detection, ADHD engine
listener, dashboards). Without this mirror, promotable events published through
the bridge never reach the chronicle promotion pipeline.

Standalone module (no package-relative imports) so it is unit-testable from the
root test tree.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Promotable event types accepted by dope-memory's promotion engine
# (services/working-memory-assistant/promotion/promotion.py PROMOTABLE_EVENT_TYPES).
PROMOTABLE_EVENT_TYPES = frozenset(
    {
        "decision.logged",
        "task.completed",
        "task.failed",
        "task.blocked",
        "error.encountered",
        "workflow.phase_changed",
        "manual.memory_store",
    }
)

MEMORY_INPUT_STREAM = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")


def normalize_event_type(event_type: str) -> str:
    """Canonical dotted form, mirroring dope-memory's normalize_event_type."""
    t = (event_type or "").strip().lower()
    if not t:
        return "unknown"
    return t if "." in t else t.replace("_", ".")


def build_mirror_envelope(
    event_type: str,
    data: Dict[str, Any],
    source: str,
) -> Optional[Dict[str, str]]:
    """Build a capture-style envelope for a promotable event, or None.

    Envelope shape matches capture_client._emit_to_event_stream: top-level
    workspace/instance/session identity fields plus JSON-encoded "data", so the
    dope-memory consumer attributes the entry to the right ledger.
    """
    normalized = normalize_event_type(event_type)
    if normalized not in PROMOTABLE_EVENT_TYPES:
        return None
    return {
        "id": str(uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "workspace_id": str(data.get("workspace_id") or "default"),
        "instance_id": str(data.get("instance_id") or "A"),
        "session_id": str(data.get("session_id") or ""),
        "type": normalized,
        "source": source,
        "data": json.dumps(data, default=str, sort_keys=True),
    }


async def mirror_promotable_event(
    redis_client: Any,
    *,
    stream: str,
    event_type: str,
    data: Dict[str, Any],
    source: str,
) -> bool:
    """Mirror a promotable event to MEMORY_INPUT_STREAM. Never raises.

    Returns True when a mirror entry was written. Skips events already
    published to the memory input stream and non-promotable types.
    """
    if stream == MEMORY_INPUT_STREAM:
        return False
    envelope = build_mirror_envelope(event_type, data, source)
    if envelope is None:
        return False
    try:
        await redis_client.xadd(MEMORY_INPUT_STREAM, envelope)
        return True
    except Exception as exc:  # best-effort: never fail the primary publish
        logger.warning("Promotable event mirror to %s failed: %s", MEMORY_INPUT_STREAM, exc)
        return False
