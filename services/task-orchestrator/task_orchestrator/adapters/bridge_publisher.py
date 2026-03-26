"""Publish orchestrator events to DopeconBridge for cross-plane coordination.

Events are published fire-and-forget to the bridge's event endpoint.
If DopeconBridge is unavailable, events are silently dropped.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

BRIDGE_URL = os.environ.get("DOPECON_BRIDGE_URL", "http://localhost:3016")


def _post_event(event_type: str, data: Dict[str, Any], timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    """Post event to DopeconBridge."""
    try:
        payload = {
            "event_type": event_type,
            "source": "task-orchestrator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        url = f"{BRIDGE_URL}/api/events"
        body = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            result = resp.read()
            return json.loads(result.decode("utf-8")) if result else None
    except (HTTPError, URLError, TimeoutError, ConnectionRefusedError, OSError) as e:
        logger.debug(f"DopeconBridge unavailable for {event_type}: {e}")
        return None


async def publish_session_event(event_type: str, data: Dict[str, Any]) -> None:
    """Publish session lifecycle events.

    event_type: "session.started", "session.ended", "session.break_needed"
    """
    _post_event(event_type, data)


async def publish_task_event(event_type: str, data: Dict[str, Any]) -> None:
    """Publish task lifecycle events.

    event_type: "task.decomposed", "task.completed", "task.blocked"
    """
    _post_event(event_type, data)
