#!/usr/bin/env python3
"""
Integration Bridge Connector for Task-Orchestrator

Provides event-driven communication with other Dopemux services via Redis streams.
Implements Component 3: Integration Bridge wiring for bidirectional coordination.

Features:
- Redis Stream-based event publishing/subscription
- Task status change events
- Service coordination events
- Error handling and reconnection
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Integration Bridge Configuration
INTEGRATION_BRIDGE_CONFIG = {
    "redis_url": os.getenv("INTEGRATION_BRIDGE_REDIS_URL", "redis://localhost:6379"),
    "stream_name": "dopemux:events",
    "consumer_group": "task-orchestrator",
    "max_stream_length": 1000,
    "read_timeout_ms": 5000,
}


class IntegrationBridgeConnector:
    """
    Integration Bridge connector for task-orchestrator.

    Handles event publishing and subscription for cross-service coordination.
    """

    def __init__(self, workspace_id: str, consumer_name: Optional[str] = None):
        """
        Initialize Integration Bridge connector.

        Args:
            workspace_id: Workspace identifier for event routing
            consumer_name: Unique consumer name (auto-generated if None)
        """
        self.workspace_id = workspace_id
        self.consumer_name = (
            consumer_name or f"orchestrator-{workspace_id.split('/')[-1]}"
        )
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Connect to Integration Bridge Redis instance.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(
                    INTEGRATION_BRIDGE_CONFIG["redis_url"]
                )

            # Test connection
            await self.redis_client.ping()
            self._connected = True

            # Create consumer group if it doesn't exist
            try:
                await self.redis_client.xgroup_create(
                    INTEGRATION_BRIDGE_CONFIG["stream_name"],
                    INTEGRATION_BRIDGE_CONFIG["consumer_group"],
                    "$",  # Start from end of stream
                    mkstream=True,
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.warning(f"Consumer group creation failed: {e}")

            logger.info("✅ Connected to Integration Bridge")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Integration Bridge: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Disconnect from Integration Bridge."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        self._connected = False
        logger.info("🛑 Disconnected from Integration Bridge")

    async def emit_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Emit event to Integration Bridge.

        Args:
            event_type: Type of event (e.g., "task.status.changed")
            payload: Event payload data
            correlation_id: Optional correlation ID for tracking

        Returns:
            True if event emitted successfully, False otherwise
        """
        if not self._connected:
            logger.warning("Integration Bridge not connected, cannot emit event")
            return False

        try:
            event_data = {
                "event_type": event_type,
                "source": "task-orchestrator",
                "workspace_id": self.workspace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
                "correlation_id": correlation_id,
            }

            # Add to stream
            message_id = await self.redis_client.xadd(
                INTEGRATION_BRIDGE_CONFIG["stream_name"],
                {"data": json.dumps(event_data)},
                maxlen=INTEGRATION_BRIDGE_CONFIG["max_stream_length"],
            )

            logger.debug(f"📤 Emitted event: {event_type} (ID: {message_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}")
            return False

    async def subscribe_events(
        self,
        callback: Callable[[Dict[str, Any]], None],
        event_filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        """
        Subscribe to events from Integration Bridge.

        Args:
            callback: Async function to handle events
            event_filter: Optional filter function (return True to process event)
        """
        if not self._connected:
            logger.warning("Integration Bridge not connected, cannot subscribe")
            return

        logger.info(
            f"📡 Subscribed to Integration Bridge events as {self.consumer_name}"
        )

        while self._connected:
            try:
                # Read from stream
                messages = await self.redis_client.xreadgroup(
                    INTEGRATION_BRIDGE_CONFIG["consumer_group"],
                    self.consumer_name,
                    {INTEGRATION_BRIDGE_CONFIG["stream_name"]: ">"},
                    count=10,
                    block=INTEGRATION_BRIDGE_CONFIG["read_timeout_ms"],
                )

                for stream_name, message_list in messages:
                    for message_id, message_data in message_list:
                        try:
                            # Parse event data
                            event_data = json.loads(message_data["data"])

                            # Apply filter if provided
                            if event_filter and not event_filter(event_data):
                                continue

                            # Call callback
                            await callback(event_data)

                            # Acknowledge message
                            await self.redis_client.xack(
                                INTEGRATION_BRIDGE_CONFIG["stream_name"],
                                INTEGRATION_BRIDGE_CONFIG["consumer_group"],
                                message_id,
                            )

                        except Exception as e:
                            logger.error(f"Failed to process message {message_id}: {e}")

            except Exception as e:
                logger.error(f"Event subscription error: {e}")
                await asyncio.sleep(5)  # Wait before retry

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Integration Bridge health.

        Returns:
            Health status dictionary
        """
        if not self._connected:
            return {
                "status": "disconnected",
                "service": "integration_bridge",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            # Check Redis connectivity
            await self.redis_client.ping()

            # Check stream info
            stream_info = await self.redis_client.xinfo_stream(
                INTEGRATION_BRIDGE_CONFIG["stream_name"]
            )

            return {
                "status": "healthy",
                "service": "integration_bridge",
                "stream_length": stream_info.get("length", 0),
                "consumer_groups": len(stream_info.get("groups", [])),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "service": "integration_bridge",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Global connector instance
_bridge_connector: Optional[IntegrationBridgeConnector] = None


async def get_integration_bridge_connector(
    workspace_id: str,
) -> IntegrationBridgeConnector:
    """
    Get or create Integration Bridge connector instance.

    Args:
        workspace_id: Workspace identifier

    Returns:
        IntegrationBridgeConnector instance
    """
    global _bridge_connector

    if not _bridge_connector:
        _bridge_connector = IntegrationBridgeConnector(workspace_id)
        await _bridge_connector.connect()

    return _bridge_connector


async def emit_task_status_change(
    task_id: str,
    old_status: str,
    new_status: str,
    workspace_id: str,
    additional_data: Optional[Dict[str, Any]] = None,
):
    """
    Emit task status change event to Integration Bridge.

    Args:
        task_id: Task identifier
        old_status: Previous task status
        new_status: New task status
        workspace_id: Workspace identifier
        additional_data: Optional additional event data
    """
    connector = await get_integration_bridge_connector(workspace_id)

    payload = {
        "task_id": task_id,
        "old_status": old_status,
        "new_status": new_status,
        "change_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if additional_data:
        payload.update(additional_data)

    success = await connector.emit_event("task.status.changed", payload)

    if success:
        logger.info(f"📤 Task {task_id} status changed: {old_status} → {new_status}")
    else:
        logger.warning(f"Failed to emit task status change for {task_id}")


async def emit_service_coordination_event(
    event_type: str, payload: Dict[str, Any], workspace_id: str
):
    """
    Emit service coordination event.

    Args:
        event_type: Type of coordination event
        payload: Event payload
        workspace_id: Workspace identifier
    """
    connector = await get_integration_bridge_connector(workspace_id)
    success = await connector.emit_event(f"service.{event_type}", payload)

    if success:
        logger.debug(f"📤 Service coordination event: {event_type}")
    else:
        logger.warning(f"Failed to emit service coordination event: {event_type}")


async def emit_adhd_coordination_event(
    event_type: str, payload: Dict[str, Any], workspace_id: str
):
    """
    Emit ADHD coordination event.

    Args:
        event_type: Type of ADHD event (e.g., "energy.changed", "break.reminder")
        payload: Event payload
        workspace_id: Workspace identifier
    """
    connector = await get_integration_bridge_connector(workspace_id)
    success = await connector.emit_event(f"adhd.{event_type}", payload)

    if success:
        logger.debug(f"🧠 ADHD coordination event: {event_type}")
    else:
        logger.warning(f"Failed to emit ADHD coordination event: {event_type}")


# Export functions for use by enhanced_orchestrator.py
__all__ = [
    "get_integration_bridge_connector",
    "emit_task_status_change",
    "emit_service_coordination_event",
    "emit_adhd_coordination_event",
    "IntegrationBridgeConnector",
]
