"""
Event Bus Bridge for Genetic Agent Integration

Bridges the Genetic Agent's EventBus with the Orchestrator's MessageBus.
Enables real-time communication between the genetic agent and orchestrator services.

Complexity: 0.35 (Low)
Integration: Connects genetic agent events to orchestrator message bus
"""

from typing import Optional, Callable, Dict, Any
import asyncio
import logging
import time
import json
from datetime import datetime

from .message_bus import MessageBus, Event as OrchestratorEvent, EventType
from services.genetic_agent.shared.eventbus import SimpleEventBus as GeneticEventBus, Event as GeneticEvent

logger = logging.getLogger(__name__)


class EventBusError(Exception):
    """Base exception for event bus operations."""
    pass


class NetworkError(EventBusError):
    """Network connectivity errors."""
    pass


class SerializationError(EventBusError):
    """JSON serialization/deserialization errors."""
    pass


class MCPServiceError(EventBusError):
    """MCP service-specific errors."""
    pass


class EventBusBridge:
    """Event bus bridge with retry logic for robust connections."""

    def __init__(self, orchestrator_bus: MessageBus, genetic_bus: Optional[GeneticEventBus] = None):
        self.orchestrator_bus = orchestrator_bus
        self.genetic_bus = genetic_bus
        self._bridge_task: Optional[asyncio.Task] = None
        self._running = False

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 30.0  # seconds

    @staticmethod
    def _calculate_delay(attempt: int, base_delay: float, max_delay: float) -> float:
        """Calculate exponential backoff delay for retries."""

        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)

    async def _retry_operation(self, operation, operation_name: str, *args, **kwargs):
        """Execute operation with exponential backoff retry logic."""

        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Last attempt failed
                    logger.error(f"{operation_name} failed after {self.max_retries} attempts: {e}")
                    raise e

                delay = self._calculate_delay(attempt, self.base_delay, self.max_delay)
                logger.warning(f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

    async def start_bridge(self):
        """Start the event bridge between systems."""

        if self._running:
            return

        self._running = True

        # Initialize genetic event bus with retry logic
        if self.genetic_bus is None:
            try:
                await self._retry_operation(
                    self._initialize_genetic_bus,
                    "Genetic event bus initialization"
                )
            except Exception as e:
                logger.error(f"Could not initialize genetic event bus after retries: {e}")
                return

        # Start the bridge task
        self._bridge_task = asyncio.create_task(self._run_bridge())
        logger.info("Event bus bridge started")

    async def _initialize_genetic_bus(self):
        """Initialize the genetic event bus."""

        from services.genetic_agent.shared.eventbus import SimpleEventBus
        # Use same Redis DB as orchestrator (typically 0)
        self.genetic_bus = SimpleEventBus(redis_url="redis://localhost:6379", db=0)

    async def stop_bridge(self):
        """Stop the event bridge."""

        self._running = False
        if self._bridge_task:
            self._bridge_task.cancel()
            try:
                await self._bridge_task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus bridge stopped")

    async def _run_bridge(self):
        """Run the event bridging loop."""

        # Set up genetic event handlers
        genetic_event_handlers = {
            "bug_detected": self._handle_bug_detected,
            "repair_attempted": self._handle_repair_attempted,
            "repair_successful": self._handle_repair_successful,
            "test_results": self._handle_test_results,
            "user_feedback": self._handle_user_feedback,
        }

        # Subscribe to genetic events
        for event_type, handler in genetic_event_handlers.items():
            try:
                await self.genetic_bus.subscribe(
                    event_type=event_type,
                    callback=handler,
                    filter_fn=None  # Accept all events
                )
            except Exception as e:
                logger.error(f"Failed to subscribe to genetic event {event_type}: {e}")

        # Keep the bridge running
        while self._running:
            await asyncio.sleep(1)

    async def _handle_bug_detected(self, genetic_event: GeneticEvent):
        """Handle bug detection events from genetic agent."""

        try:
            # Translate to orchestrator event
            orchestrator_event = OrchestratorEvent(
                type=EventType.AGENT_OUTPUT,
                source="genetic_agent",
                timestamp=datetime.now(),
                payload={
                    "event_type": "bug_detected",
                    "bug_description": genetic_event.payload.get("bug_description", ""),
                    "file_path": genetic_event.payload.get("file_path", ""),
                    "line_number": genetic_event.payload.get("line_number", 0),
                    "workspace_id": genetic_event.payload.get("workspace_id"),
                    "user_id": genetic_event.payload.get("user_id"),
                },
                correlation_id=genetic_event.payload.get("correlation_id")
            )

            # Publish to orchestrator bus
            await self.orchestrator_bus.publish(orchestrator_event)
            logger.debug(f"Bridged bug_detected event: {genetic_event.payload.get('bug_description', '')[:50]}...")

        except Exception as e:
            await self._handle_event_error("bug_detected", e, {"event": genetic_event})

            logger.error(f"Error: {e}")
    async def _handle_repair_attempted(self, genetic_event: GeneticEvent):
        """Handle repair attempt events from genetic agent."""

        try:
            orchestrator_event = OrchestratorEvent(
                type=EventType.COMMAND_SENT,
                source="genetic_agent",
                timestamp=datetime.now(),
                payload={
                    "event_type": "repair_attempted",
                    "confidence": genetic_event.payload.get("confidence", 0.0),
                    "source": genetic_event.payload.get("source", "unknown"),
                    "file_path": genetic_event.payload.get("file_path", ""),
                    "attempt_number": genetic_event.payload.get("attempt_number", 0),
                    "workspace_id": genetic_event.payload.get("workspace_id"),
                    "user_id": genetic_event.payload.get("user_id"),
                }
            )

            await self.orchestrator_bus.publish(orchestrator_event)
            logger.debug(f"Bridged repair_attempted event (attempt #{genetic_event.payload.get('attempt_number', 0)})")

        except Exception as e:
            logger.error(f"Failed to handle repair_attempted event: {e}")

    async def _handle_repair_successful(self, genetic_event: GeneticEvent):
        """Handle successful repair events from genetic agent."""

        try:
            orchestrator_event = OrchestratorEvent(
                type=EventType.COMMAND_COMPLETED,
                source="genetic_agent",
                timestamp=datetime.now(),
                payload={
                    "event_type": "repair_successful",
                    "confidence": genetic_event.payload.get("confidence", 0.0),
                    "method": genetic_event.payload.get("method", "unknown"),
                    "success": genetic_event.payload.get("success", False),
                    "iterations": genetic_event.payload.get("iterations", 0),
                    "workspace_id": genetic_event.payload.get("workspace_id"),
                    "user_id": genetic_event.payload.get("user_id"),
                }
            )

            await self.orchestrator_bus.publish(orchestrator_event)
            logger.info(f"Bridged repair_successful event: {genetic_event.payload.get('method', 'unknown')} method")

        except Exception as e:
            logger.error(f"Failed to handle repair_successful event: {e}")

    async def _handle_test_results(self, genetic_event: GeneticEvent):
        """Handle test result events from genetic agent."""

        try:
            orchestrator_event = OrchestratorEvent(
                type=EventType.AGENT_OUTPUT,
                source="genetic_agent",
                timestamp=datetime.now(),
                payload={
                    "event_type": "test_results",
                    "test_score": genetic_event.payload.get("test_score", 0.0),
                    "passed": genetic_event.payload.get("passed", False),
                    "attempt_id": genetic_event.payload.get("attempt_id", 0),
                    "workspace_id": genetic_event.payload.get("workspace_id"),
                    "user_id": genetic_event.payload.get("user_id"),
                }
            )

            await self.orchestrator_bus.publish(orchestrator_event)
            logger.debug(f"Bridged test_results event: {'PASS' if genetic_event.payload.get('passed') else 'FAIL'}")

        except Exception as e:
            logger.error(f"Failed to handle test_results event: {e}")

    async def _handle_user_feedback(self, genetic_event: GeneticEvent):
        """Handle user feedback events from genetic agent."""

        try:
            orchestrator_event = OrchestratorEvent(
                type=EventType.AGENT_OUTPUT,
                source="genetic_agent",
                timestamp=datetime.now(),
                payload={
                    "event_type": "user_feedback",
                    "rating": genetic_event.payload.get("rating", 0.0),
                    "feedback": genetic_event.payload.get("feedback", ""),
                    "user_id": genetic_event.payload.get("user_id"),
                    "workspace_id": genetic_event.payload.get("workspace_id"),
                }
            )

            await self.orchestrator_bus.publish(orchestrator_event)
            logger.debug(f"Bridged user_feedback event: rating {genetic_event.payload.get('rating', 0.0)}")

        except Exception as e:
            logger.error(f"Failed to handle user_feedback event: {e}")

    async def send_command_to_genetic_agent(self, command: str, payload: Dict[str, Any]):
        """Send command to genetic agent through the bridge."""

        if not self.genetic_bus:
            logger.warning("Genetic event bus not available")
            return

        try:
            # Create genetic event for command
            genetic_event = GeneticEvent(
                type="orchestrator_command",
                source="orchestrator",
                payload={
                    "command": command,
                    **payload
                }
            )

            # Publish to genetic bus
            await self.genetic_bus.publish(genetic_event)
            logger.debug(f"Sent command to genetic agent: {command}")

        except Exception as e:
            logger.error(f"Failed to send command to genetic agent: {e}")


# Global bridge instance
_bridge_instance: Optional[EventBusBridge] = None


def get_event_bridge(orchestrator_bus: Optional[MessageBus] = None) -> EventBusBridge:
    """Get or create the global event bridge instance."""

    global _bridge_instance

    if _bridge_instance is None and orchestrator_bus:
        _bridge_instance = EventBusBridge(orchestrator_bus)

    return _bridge_instance


async def start_event_bridge(orchestrator_bus: MessageBus):
    """Start the event bridge with the orchestrator bus."""

    bridge = get_event_bridge(orchestrator_bus)
    await bridge.start_bridge()
    return bridge


async def stop_event_bridge():
    """Stop the global event bridge."""

    global _bridge_instance

    if _bridge_instance:
        await _bridge_instance.stop_bridge()
        _bridge_instance = None