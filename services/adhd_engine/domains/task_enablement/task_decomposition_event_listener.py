"""
Task Decomposition Event Listener

Listens to task.created and task.updated events from DopeconBridge EventBus.
Triggers automatic decomposition detection and coordination.

This is the entry point for implicit (automatic) task decomposition.
"""
from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from decomposition_coordinator import DecompositionCoordinator
from task_decomposition_assistant import TaskDecompositionAssistant

logger = logging.getLogger(__name__)


class TaskDecompositionEventListener:
    """
    Listens to task events from DopeconBridge and triggers decomposition.
    
    Event Flow:
    1. Task created in Leantime or via CLI
    2. Task Orchestrator publishes task.created event
    3. EventListener receives event
    4. DecompositionCoordinator analyzes complexity
    5. If complex, asks user consent
    6. If consented, triggers decomposition via Task Orchestrator
    """
    
    def __init__(
        self,
        coordinator: DecompositionCoordinator,
        bridge_client=None,  # AsyncDopeconBridgeClient
        enabled: bool = True
    ):
        """
        Initialize event listener.
        
        Args:
            coordinator: Decomposition coordinator
            bridge_client: DopeconBridge client for event subscription
            enabled: Whether listener is active (default True)
        """
        self.coordinator = coordinator
        self.bridge_client = bridge_client
        self.enabled = enabled
        self.running = False
        self._listener_task: Optional[asyncio.Task] = None
        
        logger.info(f"TaskDecompositionEventListener initialized (enabled: {enabled})")
    
    async def start(self) -> None:
        """
        Start listening to task events.
        
        Subscribes to:
        - task.created: New tasks from Leantime/CLI
        - task.updated: Task changes (estimate, description updates)
        """
        if not self.enabled:
            logger.info("Event listener disabled, not starting")
            return
        
        if not self.bridge_client:
            logger.warning(
                "No DopeconBridge client provided, event listener cannot start. "
                "Decomposition will only work via explicit API calls."
            )
            return
        
        if self.running:
            logger.warning("Event listener already running")
            return
        
        logger.info("Starting task decomposition event listener...")
        self.running = True
        
        # Start listener task in background
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("Event listener started successfully")
    
    async def stop(self) -> None:
        """Stop listening to events."""
        if not self.running:
            logger.debug("Event listener not running")
            return
        
        logger.info("Stopping task decomposition event listener...")
        self.running = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                logger.debug("Listener task cancelled successfully")
        
        logger.info("Event listener stopped")
    
    async def _listen_loop(self) -> None:
        """
        Main event listening loop.
        
        Subscribes to task events and processes them via coordinator.
        """
        try:
            logger.info("Subscribing to task events (task.created, task.updated)...")
            
            async for event in self.bridge_client.subscribe_to_events(
                event_types=["task.created", "task.updated"],
                stream="dopemux:events"
            ):
                if not self.running:
                    logger.info("Listener stopped, exiting event loop")
                    break
                
                await self._process_event(event)
        
        except asyncio.CancelledError:
            logger.info("Event listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Event listener error: {e}", exc_info=True)
            # Don't crash, just log and continue
            if self.running:
                # Restart listener after error
                logger.info("Restarting listener after error...")
                await asyncio.sleep(5)
                self._listener_task = asyncio.create_task(self._listen_loop())
    
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """
        Process a single task event.
        
        Args:
            event: Event data from DopeconBridge
                {
                    "event_type": "task.created",
                    "data": {
                        "id": "T-123",
                        "description": "...",
                        "estimated_minutes": 180,
                        "status": "TODO",
                        "created_at": "...",
                        ...
                    },
                    "source": "task-orchestrator",
                    "timestamp": "..."
                }
        """
        event_type = event.get("event_type")
        task_data = event.get("data", {})
        task_id = task_data.get("id", "unknown")
        source = event.get("source", "unknown")
        
        logger.debug(f"Received {event_type} from {source} for task {task_id}")
        
        # Filter events
        if event_type not in ["task.created", "task.updated"]:
            logger.debug(f"Ignoring event type: {event_type}")
            return
        
        # Ignore events from adhd-engine to avoid loops
        if source == "adhd-engine":
            logger.debug(f"Ignoring event from adhd-engine (avoid loops)")
            return
        
        # Ignore already decomposed tasks
        if task_data.get("metadata", {}).get("decomposed"):
            logger.debug(f"Task {task_id} already decomposed, ignoring")
            return
        
        # Process through coordinator
        try:
            await self.coordinator.handle_task_event(event)
        except Exception as e:
            logger.error(
                f"Failed to process {event_type} for task {task_id}: {e}",
                exc_info=True
            )
    
    def is_running(self) -> bool:
        """Check if listener is currently running."""
        return self.running
    
    def enable(self) -> None:
        """Enable the listener (will start on next start() call)."""
        self.enabled = True
        logger.info("Event listener enabled")
    
    def disable(self) -> None:
        """Disable the listener."""
        self.enabled = False
        logger.info("Event listener disabled")
        if self.running:
            asyncio.create_task(self.stop())


async def create_and_start_listener(
    decomposer: TaskDecompositionAssistant,
    bridge_client=None,
    task_orchestrator_url: str = "http://localhost:8000"
) -> TaskDecompositionEventListener:
    """
    Factory function to create and start event listener.
    
    Args:
        decomposer: Task decomposition assistant
        bridge_client: DopeconBridge client
        task_orchestrator_url: Task Orchestrator API URL
    
    Returns:
        Running event listener instance
    
    Example:
        >>> decomposer = TaskDecompositionAssistant(...)
        >>> bridge_client = AsyncDopeconBridgeClient.from_env()
        >>> listener = await create_and_start_listener(decomposer, bridge_client)
        >>> # Listener now running in background
        >>> # Stop later:
        >>> await listener.stop()
    """
    # Create coordinator
    coordinator = DecompositionCoordinator(
        decomposer=decomposer,
        task_orchestrator_url=task_orchestrator_url,
        bridge_client=bridge_client
    )
    
    # Create listener
    listener = TaskDecompositionEventListener(
        coordinator=coordinator,
        bridge_client=bridge_client,
        enabled=True
    )
    
    # Start listening
    await listener.start()
    
    return listener
