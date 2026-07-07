"""
DopeconBridge Client for ConPort
Publishes events to DopeconBridge EventBus

Configuration:
    DOPECON_BRIDGE_URL: Base URL for the bridge (default resolves to
        dope-decision-graph bridge inside Docker or falls back to service name)
        Examples:
          - http://dope-decision-graph-bridge:3016  (same compose project)
          - http://localhost:3016                    (host access)
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Direct chronicle emit (bypasses the bridge HTTP publish path).
#
# The bridge /events endpoint requires a user JWT but its user store is empty,
# so ConPort's HTTP publishes 401 and never reach dope-memory. This emitter
# writes the promotable decision.logged event straight to the dope-memory
# INPUT stream (activity.events.v1) on the *events* Redis — the same stream+
# envelope dope-memory's EventBusConsumer + promotion engine consume. Fail-open:
# a decision is never blocked by chronicle emission.
#
# Note: ConPort's own REDIS_URL points at the primary (data/cache) Redis; the
# event stream lives on the dedicated events Redis, hence a separate URL.
# ---------------------------------------------------------------------------
try:  # redis.asyncio is already a ConPort dependency (see enhanced_server)
    import redis.asyncio as _chronicle_redis
except Exception:  # pragma: no cover - redis unavailable
    _chronicle_redis = None  # type: ignore[assignment]

CHRONICLE_STREAM = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")
CHRONICLE_REDIS_URL = (
    os.getenv("DOPE_MEMORY_EVENTS_REDIS_URL")
    or os.getenv("EVENTS_REDIS_URL")
    or "redis://redis-events:6379"
)
CHRONICLE_REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def build_chronicle_envelope(
    *,
    event_type: str,
    data: Dict[str, Any],
    workspace_id: Optional[str],
    instance_id: Optional[str] = "A",
    session_id: Optional[str] = "",
    source: str = "conport",
) -> Dict[str, str]:
    """Capture-envelope shape expected by dope-memory (see capture_client)."""
    return {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "workspace_id": str(workspace_id or "default"),
        "instance_id": str(instance_id or "A"),
        "session_id": str(session_id or ""),
        "type": event_type,
        "source": source,
        "data": json.dumps(data, default=str, sort_keys=True),
    }


async def emit_decision_to_chronicle(
    *,
    decision_id: str,
    summary: Optional[str],
    rationale: Optional[str],
    workspace_id: Optional[str],
    tags: Optional[List[str]] = None,
    instance_id: Optional[str] = None,
) -> bool:
    """Emit decision.logged to the dope-memory input stream. Never raises.

    Maps ConPort's ``summary`` -> the promotion handler's required ``title``
    field (the handler needs decision_id + title + choice|rationale).
    """
    if _chronicle_redis is None or not summary:
        return False
    client = None
    try:
        client = _chronicle_redis.from_url(
            CHRONICLE_REDIS_URL,
            password=CHRONICLE_REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=2,
        )
        envelope = build_chronicle_envelope(
            event_type="decision.logged",
            data={
                "decision_id": decision_id,
                "title": summary,
                "rationale": rationale or "",
                "workspace_id": workspace_id,
                "tags": tags or [],
            },
            workspace_id=workspace_id,
            instance_id=instance_id,
        )
        await client.xadd(CHRONICLE_STREAM, envelope)
        return True
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("chronicle emit failed: %s", exc)
        return False
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


class DopeconBridgeClient:
    """
    HTTP client for publishing events to DopeconBridge

    Enables ConPort to publish events when decisions/progress changes occur,
    allowing Dashboard and ADHD Engine to react in real-time.
    """

    def __init__(self, bridge_url: Optional[str] = None):
        """
        Initialize DopeconBridge client

        Args:
            bridge_url: Base URL for DopeconBridge service
        """
        # Prefer explicit arg → env override → sane defaults
        if bridge_url:
            self.bridge_url = bridge_url
        else:
            self.bridge_url = (
                os.getenv("DOPECON_BRIDGE_URL")
                or "http://dope-decision-graph-bridge:3016"
            )
        self.events_endpoint = f"{self.bridge_url}/events"
        self.session: Optional[aiohttp.ClientSession] = None
        self._enabled = True  # Can disable if Bridge unavailable

    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=5, connect=2)
        self.session = aiohttp.ClientSession(timeout=timeout)

        # Test connection
        try:
            async with self.session.get(f"{self.bridge_url}/health") as response:
                if response.status == 200:
                    logger.info("✅ DopeconBridge client initialized")
                    self._enabled = True
                else:
                    logger.warning(f"⚠️  DopeconBridge unhealthy: {response.status}")
                    self._enabled = False
        except Exception as e:
            logger.warning(f"⚠️  DopeconBridge unavailable: {e}")
            self._enabled = False

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "conport"
    ) -> bool:
        """
        Publish event to DopeconBridge

        Args:
            event_type: Event type (e.g., decision_logged, progress_updated)
            data: Event data payload
            source: Event source identifier

        Returns:
            True if published successfully, False otherwise
        """
        if not self._enabled or not self.session:
            return False

        try:
            payload = {
                "stream": "dopemux:events",
                "event_type": event_type,
                "data": data,
                "source": source
            }

            async with self.session.post(
                self.events_endpoint,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=2)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"📡 Published {event_type}: {result.get('message_id')}")
                    return True
                else:
                    logger.warning(f"⚠️  Event publish failed: {response.status}")
                    return False

        except asyncio.TimeoutError:
            logger.debug(f"⏱️  Event publish timeout (non-blocking): {event_type}")
            return False
        except Exception as e:
            logger.debug(f"❌ Event publish error (non-blocking): {e}")
            return False

    # Convenience methods for common events

    async def publish_decision_logged(
        self,
        decision_id: str,
        summary: str,
        workspace_id: str,
        tags: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Publish decision_logged event"""
        return await self.publish_event(
            event_type="decision_logged",
            data={
                "decision_id": decision_id,
                "summary": summary,
                "workspace_id": workspace_id,
                "tags": tags or [],
                **(extra or {})
            }
        )

    async def publish_progress_updated(
        self,
        progress_id: str,
        status: str,
        description: str,
        workspace_id: str,
        percentage: float = 0.0,
        extra: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Publish progress_updated event"""
        return await self.publish_event(
            event_type="progress_updated",
            data={
                "progress_id": progress_id,
                "status": status,
                "description": description,
                "workspace_id": workspace_id,
                "percentage": percentage,
                **(extra or {})
            }
        )
