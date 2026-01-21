"""
ADHDEngineClient - Integration with ADHD Engine for attention state monitoring.

Subscribes to attention state changes and forwards to ShieldCoordinator.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

import aiohttp

logger = logging.getLogger(__name__)


class AttentionState(Enum):
    """ADHD Engine attention states (mirrored from ADHD Engine)."""

    SCATTERED = "scattered"
    TRANSITIONING = "transitioning"
    FOCUSED = "focused"
    HYPERFOCUS = "hyperfocus"
    FATIGUED = "fatigued"


class ADHDEngineClient:
    """
    Client for ADHD Engine API integration.

    Supports:
    - HTTP polling for attention state
    - Callback registration for state changes
    - Automatic reconnection on failures
    """

    def __init__(self, base_url: str = "http://localhost:8095", poll_interval: int = 5):
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval  # seconds

        # State tracking
        self.current_state: Optional[AttentionState] = None
        self.callbacks: list[Callable] = []
        self.polling_task: Optional[asyncio.Task] = None

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Start ADHD Engine client and begin polling."""
        self.session = aiohttp.ClientSession()

        # Test connection
        try:
            await self._get_current_state()
            logger.info(f"✅ Connected to ADHD Engine at {self.base_url}")
        except Exception as e:
            logger.warning(
                f"⚠️ ADHD Engine not reachable at {self.base_url}: {e}. "
                f"Will retry during polling."
            )

        # Start polling task
        self.polling_task = asyncio.create_task(self._poll_loop())

        logger.info(f"ADHD Engine client started (polling every {self.poll_interval}s)")

    async def stop(self):
        """Stop ADHD Engine client."""
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        logger.info("ADHD Engine client stopped")

    async def subscribe_attention_state(self, callback: Callable):
        """
        Subscribe to attention state changes.

        Callback signature: async def callback(new_state: AttentionState, user_id: str)
        """
        self.callbacks.append(callback)
        logger.info(f"Registered callback for attention state changes ({len(self.callbacks)} total)")

    async def get_current_state(self) -> Optional[AttentionState]:
        """Get current attention state."""
        return self.current_state

    async def _poll_loop(self):
        """Poll ADHD Engine for attention state changes."""
        while True:
            try:
                await asyncio.sleep(self.poll_interval)

                # Get current state from ADHD Engine
                new_state = await self._get_current_state()

                # Check if state changed
                if new_state != self.current_state:
                    old_state = self.current_state
                    self.current_state = new_state

                    logger.info(
                        f"🧠 Attention state changed: {old_state.value if old_state else 'None'} "
                        f"→ {new_state.value}"
                    )

                    # Notify all subscribers
                    await self._notify_callbacks(new_state)

            except asyncio.CancelledError:
                logger.info("Polling loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                # Continue polling despite errors

    async def _get_current_state(self) -> AttentionState:
        """
        Fetch current attention state from ADHD Engine API.

        Endpoint: GET /api/v1/state/current
        """
        if not self.session:
            raise Exception("Client not started")

        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/state/current", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Parse attention state
                state_str = data.get("attention_state", "scattered")
                state = AttentionState(state_str)

                logger.debug(f"Current attention state: {state.value}")
                return state

        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch attention state: {e}")
            # Return last known state or default to SCATTERED
            return self.current_state or AttentionState.SCATTERED

    async def _notify_callbacks(self, new_state: AttentionState):
        """Notify all registered callbacks of state change."""
        user_id = "current_user"  # TODO: Get from auth

        for callback in self.callbacks:
            try:
                await callback(new_state, user_id)
            except Exception as e:
                logger.error(f"Error in callback {callback.__name__}: {e}", exc_info=True)


# Example usage
if __name__ == "__main__":
    import asyncio

    async def on_state_changed(state: AttentionState, user_id: str):
        logger.info(f"State changed: {state.value} for user {user_id}")

    async def main():
        client = ADHDEngineClient()
        await client.subscribe_attention_state(on_state_changed)
        await client.start()

        # Run for 60 seconds
        await asyncio.sleep(60)

        await client.stop()

    asyncio.run(main())
