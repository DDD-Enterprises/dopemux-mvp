"""
Integration Bridge Client for ConPort
Publishes events to Integration Bridge EventBus
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)


class IntegrationBridgeClient:
    """
    HTTP client for publishing events to Integration Bridge

    Enables ConPort to publish events when decisions/progress changes occur,
    allowing Dashboard and ADHD Engine to react in real-time.
    """

    def __init__(self, bridge_url: str = "http://mcp-integration-bridge:3016"):
        """
        Initialize Integration Bridge client

        Args:
            bridge_url: Base URL for Integration Bridge service
        """
        self.bridge_url = bridge_url
        self.events_endpoint = f"{bridge_url}/events"
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
                    logger.info("✅ Integration Bridge client initialized")
                    self._enabled = True
                else:
                    logger.warning(f"⚠️  Integration Bridge unhealthy: {response.status}")
                    self._enabled = False
        except Exception as e:
            logger.warning(f"⚠️  Integration Bridge unavailable: {e}")
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
        Publish event to Integration Bridge

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
        tags: Optional[List[str]] = None
    ) -> bool:
        """Publish decision_logged event"""
        return await self.publish_event(
            event_type="decision_logged",
            data={
                "decision_id": decision_id,
                "summary": summary,
                "workspace_id": workspace_id,
                "tags": tags or []
            }
        )

    async def publish_progress_updated(
        self,
        progress_id: str,
        status: str,
        description: str,
        workspace_id: str,
        percentage: float = 0.0
    ) -> bool:
        """Publish progress_updated event"""
        return await self.publish_event(
            event_type="progress_updated",
            data={
                "progress_id": progress_id,
                "status": status,
                "description": description,
                "workspace_id": workspace_id,
                "percentage": percentage
            }
        )
