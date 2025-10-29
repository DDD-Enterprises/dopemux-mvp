"""
WebSocket Streaming Client for Real-Time Dashboard Updates

Connects to ADHD Engine WebSocket endpoint and routes real-time events
to dashboard widgets.

Part of Dashboard Day 7 - WebSocket Streaming Implementation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Dict, Optional, Any
from dataclasses import dataclass

try:
    from websockets import connect, WebSocketClientProtocol, ConnectionClosed
    from websockets.exceptions import WebSocketException
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logging.warning("websockets library not installed - WebSocket streaming unavailable")

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for WebSocket streaming client"""
    url: str = "ws://localhost:8001/api/v1/ws/stream"
    user_id: str = "default"
    heartbeat_timeout: int = 60  # seconds
    reconnect_min_delay: float = 1.0  # seconds
    reconnect_max_delay: float = 60.0  # seconds
    max_reconnect_attempts: int = 5


class StreamingClient:
    """
    WebSocket client for real-time dashboard updates.
    
    Features:
    - Auto-reconnect with exponential backoff
    - Message routing to callbacks
    - Heartbeat monitoring
    - Graceful fallback to polling on failure
    - Connection state tracking
    
    Usage:
        client = StreamingClient(
            url="ws://localhost:8001/api/v1/ws/stream",
            on_state_update=handle_state,
            on_metric_update=handle_metric,
            on_alert=handle_alert
        )
        await client.start()
    """
    
    def __init__(
        self,
        config: Optional[StreamingConfig] = None,
        on_state_update: Optional[Callable] = None,
        on_metric_update: Optional[Callable] = None,
        on_alert: Optional[Callable] = None,
        on_connection_change: Optional[Callable] = None,
    ):
        self.config = config or StreamingConfig()
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.running = False
        self.connected = False
        
        # Callbacks
        self.on_state_update = on_state_update
        self.on_metric_update = on_metric_update
        self.on_alert = on_alert
        self.on_connection_change = on_connection_change
        
        # Reconnection logic
        self.reconnect_delay = self.config.reconnect_min_delay
        self.reconnect_attempts = 0
        
        # Heartbeat monitoring
        self.last_heartbeat = datetime.utcnow()
        
        # Statistics
        self.stats = {
            "messages_received": 0,
            "state_updates": 0,
            "metric_updates": 0,
            "alerts": 0,
            "heartbeats": 0,
            "reconnections": 0,
            "errors": 0
        }
    
    @property
    def is_available(self) -> bool:
        """Check if WebSocket is available (library installed)"""
        return WEBSOCKETS_AVAILABLE
    
    @property
    def connection_url(self) -> str:
        """Get full WebSocket URL with user_id"""
        return f"{self.config.url}?user_id={self.config.user_id}"
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection.
        
        Returns:
            True if connected successfully, False otherwise
        """
        if not self.is_available:
            logger.error("❌ WebSocket library not available")
            return False
        
        try:
            self.websocket = await connect(self.connection_url)
            self.connected = True
            self.reconnect_delay = self.config.reconnect_min_delay
            self.reconnect_attempts = 0
            self.last_heartbeat = datetime.utcnow()
            
            logger.info(f"✅ WebSocket connected: {self.config.url}")
            
            if self.on_connection_change:
                await self.on_connection_change("connected")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.connected = False
            self.stats["errors"] += 1
            
            if self.on_connection_change:
                await self.on_connection_change("disconnected")
            
            return False
    
    async def disconnect(self):
        """Close WebSocket connection gracefully"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
        
        self.connected = False
        logger.info("🔌 WebSocket disconnected")
        
        if self.on_connection_change:
            await self.on_connection_change("disconnected")
    
    async def send_command(self, command: Dict[str, Any]):
        """
        Send command to server.
        
        Args:
            command: Command dictionary (e.g., {"type": "refresh"})
        """
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(command))
                logger.debug(f"Sent command: {command.get('type')}")
            except Exception as e:
                logger.error(f"❌ Error sending command: {e}")
                self.stats["errors"] += 1
    
    async def start(self):
        """
        Start listening for messages (main loop).
        
        This will run until stop() is called or max reconnection attempts reached.
        """
        if not self.is_available:
            logger.error("❌ Cannot start WebSocket client - library not available")
            return
        
        self.running = True
        logger.info(f"🚀 Starting WebSocket client: {self.connection_url}")
        
        while self.running:
            if not self.connected:
                # Try to connect/reconnect
                if await self.connect():
                    # Successfully connected, start receiving
                    await self._receive_loop()
                else:
                    # Connection failed, check if should retry
                    self.reconnect_attempts += 1
                    
                    if self.reconnect_attempts > self.config.max_reconnect_attempts:
                        logger.error(
                            f"❌ Max reconnection attempts ({self.config.max_reconnect_attempts}) "
                            f"reached - stopping WebSocket client"
                        )
                        self.running = False
                        
                        if self.on_connection_change:
                            await self.on_connection_change("failed")
                        break
                    
                    # Wait before retry with exponential backoff
                    logger.warning(
                        f"⏳ Reconnection attempt #{self.reconnect_attempts} "
                        f"in {self.reconnect_delay}s"
                    )
                    
                    if self.on_connection_change:
                        await self.on_connection_change("reconnecting")
                    
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(
                        self.reconnect_delay * 2,
                        self.config.reconnect_max_delay
                    )
                    self.stats["reconnections"] += 1
            else:
                # Already connected, should be in receive loop
                await asyncio.sleep(0.1)
    
    async def _receive_loop(self):
        """Receive and route messages from WebSocket"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.stats["messages_received"] += 1
                    await self._handle_message(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON from server: {e}")
                    self.stats["errors"] += 1
                    
        except ConnectionClosed:
            logger.warning("🔌 WebSocket connection closed by server")
            self.connected = False
            
        except WebSocketException as e:
            logger.error(f"❌ WebSocket error: {e}")
            self.connected = False
            self.stats["errors"] += 1
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in receive loop: {e}")
            self.connected = False
            self.stats["errors"] += 1
    
    async def _handle_message(self, message: Dict[str, Any]):
        """
        Route message to appropriate callback.
        
        Args:
            message: Message dictionary with type and data fields
        """
        msg_type = message.get("type")
        timestamp = message.get("timestamp")
        data = message.get("data")
        
        if msg_type == "state_update":
            self.stats["state_updates"] += 1
            if self.on_state_update:
                try:
                    await self.on_state_update(data)
                except Exception as e:
                    logger.error(f"❌ Error in state_update callback: {e}")
                    
        elif msg_type == "metric_update":
            self.stats["metric_updates"] += 1
            if self.on_metric_update:
                try:
                    await self.on_metric_update(data)
                except Exception as e:
                    logger.error(f"❌ Error in metric_update callback: {e}")
                    
        elif msg_type == "alert":
            self.stats["alerts"] += 1
            if self.on_alert:
                try:
                    await self.on_alert(data)
                except Exception as e:
                    logger.error(f"❌ Error in alert callback: {e}")
                    
        elif msg_type == "heartbeat":
            self.last_heartbeat = datetime.utcnow()
            self.stats["heartbeats"] += 1
            logger.debug(f"💓 Heartbeat received: {data}")
            
        elif msg_type == "pong":
            # Response to ping command
            logger.debug(f"🏓 Pong received: {data}")
            
        else:
            logger.warning(f"⚠️ Unknown message type: {msg_type}")
    
    async def stop(self):
        """Stop the streaming client"""
        logger.info("🛑 Stopping WebSocket client")
        self.running = False
        await self.disconnect()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            **self.stats,
            "connected": self.connected,
            "reconnect_attempts": self.reconnect_attempts,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }
    
    async def is_healthy(self) -> bool:
        """
        Check if connection is healthy.
        
        Returns:
            True if connected and received heartbeat within timeout
        """
        if not self.connected:
            return False
        
        # Check heartbeat timeout
        if self.last_heartbeat:
            seconds_since_heartbeat = (datetime.utcnow() - self.last_heartbeat).total_seconds()
            if seconds_since_heartbeat > self.config.heartbeat_timeout:
                logger.warning(
                    f"⚠️ No heartbeat for {seconds_since_heartbeat}s "
                    f"(timeout: {self.config.heartbeat_timeout}s)"
                )
                return False
        
        return True
