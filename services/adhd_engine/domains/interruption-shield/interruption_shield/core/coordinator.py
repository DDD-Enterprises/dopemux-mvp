"""
ShieldCoordinator - Core orchestration for interruption shield.

Subscribes to ADHD Engine attention state changes and coordinates
shield activation/deactivation across all integrated services.
"""

import asyncio
import logging
import websockets
import json
from datetime import datetime, timedelta
from typing import Optional

from .models import ShieldState, ShieldMode, ShieldConfig, AttentionState

logger = logging.getLogger(__name__)


class ShieldCoordinator:
    """
    Coordinates interruption shield activation based on ADHD Engine state.

    Subscribes to ADHD Engine attention state changes and activates/deactivates
    shields across all integrated services (macOS, Slack, notifications).
    """

    def __init__(
        self,
        config: ShieldConfig,
        adhd_engine_client=None,
        dnd_manager=None,
        message_triage=None,
        notification_manager=None,
    ):
        self.config = config
        self.adhd_engine = adhd_engine_client
        self.dnd = dnd_manager
        self.triage = message_triage
        self.notifications = notification_manager

        # State tracking
        self.state = ShieldState(
            user_id=getattr(config, "user_id", "current_user"),
            active=False,
            attention_state=AttentionState.SCATTERED,
            mode=config.mode
        )

    async def start(self):
        """Start monitoring ADHD Engine and coordinating shields."""
        logger.info("Starting ShieldCoordinator...")

        # Subscribe to ADHD Engine attention state changes via WebSocket
        asyncio.create_task(self._connect_to_adhd_engine())

        # Start background monitoring tasks
        asyncio.create_task(self._monitor_productivity())
        asyncio.create_task(self._periodic_metrics_log())

        logger.info("ShieldCoordinator started successfully")

    async def _connect_to_adhd_engine(self):
        """Connect to ADHD Engine WebSocket and listen for attention state changes."""
        adhd_ws_url = f"{self.config.adhd_engine_url.rstrip('/')}/api/v1/ws/stream"
        user_id = self.state.user_id

        while True:  # Reconnect on disconnection
            try:
                logger.info(f"Connecting to ADHD Engine WebSocket for user {user_id}")
                async with websockets.connect(f"{adhd_ws_url}?user_id={user_id}") as websocket:
                    logger.info("Connected to ADHD Engine WebSocket")

                    # Send initial state request
                    await websocket.send(json.dumps({"type": "refresh"}))

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            if data.get("type") == "state_update":
                                attention_state = data.get("data", {}).get("attention_state")
                                if attention_state:
                                    # Convert string to AttentionState enum
                                    try:
                                        attention_enum = AttentionState(attention_state.lower())
                                        await self.on_attention_state_changed(attention_enum, user_id)
                                    except ValueError:
                                        logger.warning(f"Unknown attention state: {attention_state}")

                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON from ADHD Engine: {message}")
                        except Exception as e:
                            logger.error(f"Error processing ADHD Engine message: {e}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("ADHD Engine WebSocket connection closed, reconnecting...")
                await asyncio.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"ADHD Engine WebSocket error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

    async def on_attention_state_changed(
        self,
        new_state: AttentionState,
        user_id: str
    ):
        """
        Handle attention state changes from ADHD Engine.

        FOCUSED/HYPERFOCUS → Activate shields
        SCATTERED/TRANSITIONING/FATIGUED → Deactivate shields
        """
        logger.info(f"Attention state changed: {new_state.value} for user {user_id}")

        self.state.attention_state = new_state

        if new_state in [AttentionState.FOCUSED, AttentionState.HYPERFOCUS]:
            if self.config.auto_activate:
                await self.activate_shields(user_id)
        else:
            await self.deactivate_shields(user_id)

    async def activate_shields(self, user_id: str):
        """Activate all interruption shields."""
        if self.state.active:
            logger.debug("Shields already active, skipping activation")
            return

        logger.info(f"🛡️ Activating interruption shields for user {user_id}")

        try:
            # Activate all components in parallel
            tasks = []

            if self.dnd:
                tasks.append(self.dnd.enable_macos_focus_mode())
                tasks.append(self.dnd.set_slack_status(
                    status="In focus mode",
                    until=self._calculate_end_time()
                ))

            if self.notifications:
                tasks.append(self.notifications.enable_batching())

            if self.triage:
                tasks.append(self.triage.start_queuing())

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Update state
            self.state.active = True
            self.state.activated_at = datetime.now()

            # Log to ConPort
            await self._log_to_conport(user_id, "shields_activated")

            logger.info("✅ Shields activated successfully")

        except Exception as e:
            logger.error(f"Failed to activate shields: {e}", exc_info=True)
            # Graceful degradation - continue even if some components fail

    async def deactivate_shields(self, user_id: str):
        """Deactivate shields and deliver queued messages."""
        if not self.state.active:
            logger.debug("Shields already inactive, skipping deactivation")
            return

        logger.info(f"🔓 Deactivating interruption shields for user {user_id}")

        try:
            # Deactivate all components in parallel
            tasks = []

            if self.dnd:
                tasks.append(self.dnd.disable_macos_focus_mode())
                tasks.append(self.dnd.clear_slack_status())

            if self.notifications:
                tasks.append(self.notifications.disable_batching_and_deliver())

            if self.triage:
                tasks.append(self.triage.stop_queuing_and_deliver())

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Update state
            self.state.active = False
            self.state.deactivated_at = datetime.now()

            if self.state.activated_at:
                self.state.duration_seconds = int(
                    (self.state.deactivated_at - self.state.activated_at).total_seconds()
                )

            # Show summary of what was queued
            await self._show_queued_summary(user_id)

            # Log to ConPort
            await self._log_to_conport(
                user_id,
                "shields_deactivated",
                metadata={"duration_seconds": self.state.duration_seconds}
            )

            logger.info("✅ Shields deactivated successfully")

        except Exception as e:
            logger.error(f"Failed to deactivate shields: {e}", exc_info=True)

    async def manual_override(self, user_id: str, duration_minutes: int = 10):
        """
        Manually override shields for N minutes.

        Used when user needs to check messages urgently.
        """
        logger.info(f"Manual override requested for {duration_minutes} minutes")

        if not self.config.allow_manual_override:
            logger.warning("Manual override not allowed in current configuration")
            return

        # Temporarily deactivate
        await self.deactivate_shields(user_id)

        # Schedule reactivation after cooldown
        await asyncio.sleep(duration_minutes * 60)

        # Reactivate if still in FOCUSED/HYPERFOCUS
        if self.state.attention_state in [AttentionState.FOCUSED, AttentionState.HYPERFOCUS]:
            await self.activate_shields(user_id)

    async def _monitor_productivity(self):
        """
        Monitor for false positive focus states.

        If no code changes in 15 minutes during FOCUSED state,
        downgrade to SCATTERED to prevent blocking communications.
        """
        while True:
            await asyncio.sleep(60)  # Check every minute

            if not self.state.active:
                continue

            if not self.state.activated_at:
                continue

            duration = (datetime.now() - self.state.activated_at).total_seconds()

            if duration > 900:  # 15 minutes
                has_activity = await self._check_code_activity()

                if not has_activity:
                    logger.warning(
                        "⚠️ No code activity in 15min during FOCUSED state. "
                        "Deactivating shields to prevent communication blockage."
                    )
                    await self.deactivate_shields(self.state.user_id)

    async def _check_code_activity(self) -> bool:
        """
        Check if user has made code changes recently.

        Queries Serena for recent file modifications and git for uncommitted changes.
        """
        try:
            # Query Serena for recent file modifications (last 15 minutes)
            import httpx
            serena_url = "http://localhost:8003/mcp/serena/check_recent_activity"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{serena_url}?minutes=15")
                if response.status_code == 200:
                    serena_data = response.json()
                    if serena_data.get("has_recent_activity", False):
                        logger.debug("Recent file activity detected via Serena")
                        return True

            # Query git for uncommitted changes
            import subprocess
            result = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="."  # Assuming we're in a git repo
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0 and stdout.strip():
                logger.debug("Uncommitted changes detected via git")
                return True

            logger.debug("No recent code activity detected")
            return False

        except Exception as e:
            logger.warning(f"Error checking code activity: {e}")
            # Default to True to avoid false positives
            return True

    async def _periodic_metrics_log(self):
        """Log metrics to ConPort every 5 minutes."""
        while True:
            await asyncio.sleep(300)  # 5 minutes

            if self.state.active:
                await self._log_metrics()

    def _calculate_end_time(self) -> datetime:
        """Calculate when to auto-deactivate shields."""
        return datetime.now() + timedelta(minutes=self.config.default_duration)

    async def _show_queued_summary(self, user_id: str):
        """Show user a summary of queued communications."""
        if not self.triage:
            return

        summary = await self.triage.get_queued_summary()

        # Display via Desktop Commander notification
        try:
            import httpx
            desktop_commander_url = f"{self.config.desktop_commander_url.rstrip('/')}/desktop-commander/notify"
            notification_data = {
                "title": "Interruption Shield Deactivated",
                "message": f"Queued communications summary: {summary}",
                "type": "info",
                "user_id": user_id
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(desktop_commander_url, json=notification_data)
                if response.status_code == 200:
                    logger.info("Queued summary notification sent via Desktop Commander")
                else:
                    logger.warning(f"Failed to send notification: {response.status_code}")

        except Exception as e:
            logger.warning(f"Desktop Commander notification failed: {e}")
            # Fallback to logging
            logger.info(f"Queued summary: {summary}")

    async def _log_to_conport(
        self,
        user_id: str,
        event: str,
        metadata: dict = None
    ):
        """Log shield events to ConPort for analytics."""
        try:
            import httpx
            conport_url = f"{self.config.conport_url.rstrip('/')}/conport/log_custom_data"

            log_data = {
                "workspace_id": self.config.workspace_id,
                "category": "shield_events",
                "key": f"{event}_{datetime.now().isoformat()}",
                "value": {
                    "user_id": user_id,
                    "event": event,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(conport_url, json=log_data)
                if response.status_code == 200:
                    logger.debug(f"Shield event logged to ConPort: {event}")
                else:
                    logger.warning(f"Failed to log to ConPort: {response.status_code}")

        except Exception as e:
            logger.warning(f"ConPort logging failed: {e}")
            # Fallback to debug logging
            logger.debug(f"ConPort log: {event} - {metadata}")

    async def _log_metrics(self):
        """Log current shield metrics."""
        try:
            # Log to ConPort
            metrics_data = {
                "workspace_id": self.config.workspace_id,
                "category": "shield_metrics",
                "key": f"metrics_{datetime.now().isoformat()}",
                "value": {
                    "user_id": self.state.user_id,
                    "active": self.state.active,
                    "attention_state": self.state.attention_state.value if self.state.attention_state else None,
                    "activated_at": self.state.activated_at.isoformat() if self.state.activated_at else None,
                    "duration_seconds": self.state.duration_seconds,
                    "timestamp": datetime.now().isoformat()
                }
            }

            import httpx
            conport_url = f"{self.config.conport_url.rstrip('/')}/conport/log_custom_data"

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(conport_url, json=metrics_data)
                if response.status_code == 200:
                    logger.debug("Shield metrics logged to ConPort")
                else:
                    logger.warning(f"Failed to log metrics to ConPort: {response.status_code}")

        except Exception as e:
            logger.warning(f"Metrics logging failed: {e}")
            # Fallback to debug logging
            logger.debug(f"Metrics: {self.state}")
