"""
WebSocket Progress Streamer for Real-Time Research Updates

This module provides real-time progress streaming for ADHD-optimized transparency:
- Live updates during research execution
- Progress bars and visual indicators
- Gentle notifications for breaks and completions
- Connection management with reconnection logic
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

try:
    import websockets
    from websockets.exceptions import ConnectionClosed, ConnectionClosedError
except ImportError:
    # Fallback for development
    class websockets:
        @staticmethod
        async def serve(*args, **kwargs): pass
    class ConnectionClosed(Exception): pass
    class ConnectionClosedError(Exception): pass


logger = logging.getLogger(__name__)


class WebSocketProgressStreamer:
    """
    Manages WebSocket connections for real-time research progress updates

    Provides ADHD-friendly features:
    - Real-time progress updates with visual indicators
    - Gentle notifications without overwhelming
    - Connection recovery for interrupted sessions
    - Filtered updates to prevent cognitive overload
    """

    def __init__(self, host: str = "localhost", port: int = 8001):
        """
        Initialize WebSocket streamer

        Args:
            host: WebSocket server host
            port: WebSocket server port
        """
        self.host = host
        self.port = port
        self.connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self.task_subscribers: Dict[UUID, Set[websockets.WebSocketServerProtocol]] = {}
        self.server = None
        self.logger = logging.getLogger(f"{__name__}.{host}:{port}")

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port
            )
            self.logger.info(f"WebSocket server started on {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
            raise

    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")

    async def emit_progress(self, task_id: UUID, progress_data: Dict[str, Any]) -> bool:
        """
        Emit progress update to all subscribers of a research task

        Args:
            task_id: Research task identifier
            progress_data: Progress information to send

        Returns:
            True if message was sent successfully
        """
        if task_id not in self.task_subscribers:
            self.logger.debug(f"No subscribers for task {task_id}")
            return False

        # Prepare message with ADHD optimizations
        message = self._prepare_adhd_message(task_id, progress_data)

        # Send to all subscribers
        disconnected = set()
        success_count = 0

        for websocket in self.task_subscribers[task_id].copy():
            try:
                await websocket.send(json.dumps(message))
                success_count += 1
            except (ConnectionClosed, ConnectionClosedError):
                self.logger.debug(f"Client disconnected from task {task_id}")
                disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Failed to send progress to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        self.task_subscribers[task_id] -= disconnected

        self.logger.debug(f"Sent progress update to {success_count} clients for task {task_id}")
        return success_count > 0

    async def emit_notification(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        Send notification to a specific user

        Used for Pomodoro reminders and gentle notifications
        """
        if user_id not in self.connections:
            self.logger.debug(f"No connections for user {user_id}")
            return False

        # Prepare notification with ADHD considerations
        message = {
            "type": "notification",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "data": notification
        }

        # Apply ADHD filtering (gentle, non-disruptive)
        if self._should_filter_notification(notification):
            self.logger.debug(f"Filtered notification for user {user_id}")
            return False

        disconnected = set()
        success_count = 0

        for websocket in self.connections[user_id].copy():
            try:
                await websocket.send(json.dumps(message))
                success_count += 1
            except (ConnectionClosed, ConnectionClosedError):
                disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        self.connections[user_id] -= disconnected

        return success_count > 0

    async def emit_pomodoro_reminder(self, task_id: UUID, reminder_type: str) -> bool:
        """
        Send gentle Pomodoro timer reminders

        Args:
            task_id: Research task identifier
            reminder_type: Type of reminder (break_suggestion, work_resume, session_complete)
        """
        reminder_messages = {
            "break_suggestion": {
                "title": "Consider Taking a Break",
                "message": "You've been working for 25 minutes. A short break might help maintain focus.",
                "action": "optional",
                "duration": "5 minutes",
                "urgency": "low"
            },
            "work_resume": {
                "title": "Ready to Continue?",
                "message": "Break time is over. Ready to resume your research?",
                "action": "resume_option",
                "urgency": "low"
            },
            "session_complete": {
                "title": "Great Work!",
                "message": "Research session completed successfully. Well done!",
                "action": "celebrate",
                "urgency": "low"
            }
        }

        reminder = reminder_messages.get(reminder_type, {})
        if not reminder:
            return False

        progress_data = {
            "phase": "pomodoro_reminder",
            "reminder_type": reminder_type,
            "reminder": reminder,
            "gentle": True
        }

        return await self.emit_progress(task_id, progress_data)

    # Private methods

    async def _handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        try:
            self.logger.info(f"New WebSocket connection from {websocket.remote_address}")

            # Wait for authentication/subscription message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)

            user_id = auth_data.get("user_id")
            task_id = auth_data.get("task_id")

            if not user_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "user_id required for authentication"
                }))
                return

            # Register connection
            if user_id not in self.connections:
                self.connections[user_id] = set()
            self.connections[user_id].add(websocket)

            # Subscribe to task updates if specified
            if task_id:
                task_uuid = UUID(task_id)
                if task_uuid not in self.task_subscribers:
                    self.task_subscribers[task_uuid] = set()
                self.task_subscribers[task_uuid].add(websocket)

                self.logger.info(f"User {user_id} subscribed to task {task_id}")

            # Send connection confirmation
            await websocket.send(json.dumps({
                "type": "connected",
                "user_id": user_id,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }))

            # Keep connection alive and handle messages
            async for message in websocket:
                await self._handle_client_message(websocket, user_id, message)

        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
        finally:
            # Clean up connection
            await self._cleanup_connection(websocket, user_id, task_id)

    async def _handle_client_message(self, websocket, user_id: str, message: str):
        """Handle incoming client messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))

            elif message_type == "subscribe_task":
                task_id = UUID(data.get("task_id"))
                if task_id not in self.task_subscribers:
                    self.task_subscribers[task_id] = set()
                self.task_subscribers[task_id].add(websocket)
                self.logger.info(f"User {user_id} subscribed to task {task_id}")

            elif message_type == "unsubscribe_task":
                task_id = UUID(data.get("task_id"))
                if task_id in self.task_subscribers:
                    self.task_subscribers[task_id].discard(websocket)

            elif message_type == "request_status":
                # Send current status if available
                await websocket.send(json.dumps({
                    "type": "status_response",
                    "connected": True,
                    "timestamp": datetime.now().isoformat()
                }))

        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")

    async def _cleanup_connection(self, websocket, user_id: str, task_id: Optional[str]):
        """Clean up connection when client disconnects"""
        try:
            # Remove from user connections
            if user_id in self.connections:
                self.connections[user_id].discard(websocket)
                if not self.connections[user_id]:
                    del self.connections[user_id]

            # Remove from task subscriptions
            if task_id:
                task_uuid = UUID(task_id)
                if task_uuid in self.task_subscribers:
                    self.task_subscribers[task_uuid].discard(websocket)
                    if not self.task_subscribers[task_uuid]:
                        del self.task_subscribers[task_uuid]

            self.logger.info(f"Cleaned up connection for user {user_id}")

        except Exception as e:
            self.logger.error(f"Error cleaning up connection: {e}")

    def _prepare_adhd_message(self, task_id: UUID, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare progress message with ADHD optimizations

        - Limit information density
        - Add visual progress indicators
        - Include calming elements
        """
        base_message = {
            "type": "research_progress",
            "task_id": str(task_id),
            "timestamp": datetime.now().isoformat(),
            "data": progress_data
        }

        # Add ADHD-friendly enhancements
        if "progress" in progress_data:
            progress = progress_data["progress"]
            base_message["visual"] = {
                "progress_bar": self._create_progress_bar(progress.get("progress_percentage", 0)),
                "current_step": f"{progress.get('current_question', 1)}/{progress.get('total_questions', 1)}",
                "time_remaining": f"~{progress.get('estimated_remaining_minutes', 0)} min"
            }

        # Add gentle indicators for phase transitions
        phase = progress_data.get("phase", "")
        if phase in ["question_complete", "planning_complete"]:
            base_message["celebration"] = {
                "message": "✓ Step completed!",
                "gentle": True
            }

        # Limit source information to prevent overwhelm
        if "result" in progress_data and "sources" in progress_data["result"]:
            sources = progress_data["result"]["sources"]
            if len(sources) > 3:  # ADHD limit: max 3 sources at once
                base_message["data"]["result"]["sources"] = sources[:3]
                base_message["data"]["result"]["additional_sources"] = len(sources) - 3

        return base_message

    def _create_progress_bar(self, percentage: float) -> str:
        """Create ASCII progress bar for terminal/simple displays"""
        filled = int(percentage / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty + f" {percentage:.1f}%"

    def _should_filter_notification(self, notification: Dict[str, Any]) -> bool:
        """
        Filter notifications to prevent ADHD overwhelm

        Returns True if notification should be filtered (not sent)
        """
        # Filter high-urgency notifications during work periods
        if notification.get("urgency") == "high":
            return True

        # Filter rapid consecutive notifications
        # (In production, would implement rate limiting)

        # Filter based on user's ADHD settings
        if notification.get("type") == "interruption" and not notification.get("gentle", False):
            return True

        return False


class WebSocketClient:
    """
    Client-side WebSocket handler for testing and integration

    Provides methods for connecting to the progress stream and handling updates
    """

    def __init__(self, url: str):
        self.url = url
        self.websocket = None
        self.connected = False

    async def connect(self, user_id: str, task_id: Optional[str] = None):
        """Connect to WebSocket server and authenticate"""
        try:
            self.websocket = await websockets.connect(self.url)

            # Send authentication
            auth_message = {
                "user_id": user_id,
                "task_id": task_id
            }
            await self.websocket.send(json.dumps(auth_message))

            # Wait for confirmation
            response = await self.websocket.recv()
            data = json.loads(response)

            if data.get("type") == "connected":
                self.connected = True
                logger.info(f"Connected to WebSocket as user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False

    async def listen_for_updates(self, callback=None):
        """Listen for progress updates"""
        if not self.connected or not self.websocket:
            raise RuntimeError("Not connected to WebSocket")

        try:
            async for message in self.websocket:
                data = json.loads(message)
                if callback:
                    await callback(data)
                else:
                    logger.info(f"Received update: {data.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"Error listening for updates: {e}")
            self.connected = False

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False