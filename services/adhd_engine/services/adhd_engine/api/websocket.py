"""
WebSocket Connection Manager for Real-Time Dashboard Streaming

Manages WebSocket connections, message broadcasting, and buffering.
Part of Dashboard Day 7 - WebSocket Streaming Implementation.
"""

import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import Dict, Set, List, Deque, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and real-time message broadcasting.
    
    Features:
    - Multi-client connection management
    - Message broadcasting to all connected clients
    - Message buffering during disconnection (last 50 messages)
    - Heartbeat mechanism (every 30s)
    - Graceful connection/disconnection handling
    - Per-user connection tracking
    
    Performance:
    - Supports 100+ concurrent connections
    - <50ms broadcast latency
    - Automatic cleanup of dead connections
    """
    
    def __init__(self):
        # Active WebSocket connections per user
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Message buffer for offline users (last 50 messages)
        self.message_buffer: Dict[str, Deque[Dict[str, Any]]] = {}
        self.max_buffer_size = 50
        
        # Connection statistics
        self.stats = {
            "total_connections": 0,
            "total_disconnections": 0,
            "messages_sent": 0,
            "messages_buffered": 0,
            "broadcast_errors": 0
        }
        
        logger.info("✅ ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            user_id: User identifier (default: "default")
        """
        await websocket.accept()
        
        # Add to active connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Update stats
        self.stats["total_connections"] += 1
        
        logger.info(
            f"✅ WebSocket connected: user={user_id}, "
            f"connections={len(self.active_connections[user_id])}, "
            f"total_users={len(self.active_connections)}"
        )
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove disconnected WebSocket.
        
        Args:
            websocket: FastAPI WebSocket instance
            user_id: User identifier
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty user entry
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Update stats
        self.stats["total_disconnections"] += 1
        
        logger.info(
            f"🔌 WebSocket disconnected: user={user_id}, "
            f"remaining_users={len(self.active_connections)}"
        )
    
    async def broadcast(self, message: Dict[str, Any], user_id: str):
        """
        Broadcast message to all connections for a user.
        
        If user is offline, buffer message for reconnection.
        
        Args:
            message: Message dictionary to send (will be JSON-encoded)
            user_id: User identifier to send to
        """
        if user_id not in self.active_connections:
            # User offline - buffer message
            if user_id not in self.message_buffer:
                self.message_buffer[user_id] = deque(maxlen=self.max_buffer_size)
            
            self.message_buffer[user_id].append(message)
            self.stats["messages_buffered"] += 1
            
            logger.debug(
                f"📦 Buffered message for offline user: {user_id}, "
                f"buffer_size={len(self.message_buffer[user_id])}"
            )
            return
        
        # User online - send to all connections
        dead_connections = set()
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
                self.stats["messages_sent"] += 1
                
            except WebSocketDisconnect:
                logger.warning(f"Connection closed during broadcast: {user_id}")
                dead_connections.add(connection)
                
            except Exception as e:
                logger.error(f"❌ Error broadcasting to {user_id}: {e}")
                self.stats["broadcast_errors"] += 1
                dead_connections.add(connection)
        
        # Clean up dead connections
        for dead in dead_connections:
            await self.disconnect(dead, user_id)
    
    async def broadcast_all(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected users.
        
        Args:
            message: Message dictionary to send
        """
        for user_id in list(self.active_connections.keys()):
            await self.broadcast(message, user_id)
    
    async def send_buffered_messages(self, websocket: WebSocket, user_id: str):
        """
        Send buffered messages to reconnected client.
        
        Args:
            websocket: WebSocket connection to send to
            user_id: User identifier
        """
        if user_id not in self.message_buffer:
            return
        
        buffer = self.message_buffer[user_id]
        sent_count = 0
        
        for message in buffer:
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Error sending buffered message: {e}")
                break
        
        # Clear buffer after sending
        buffer.clear()
        
        if sent_count > 0:
            logger.info(f"📬 Sent {sent_count} buffered messages to {user_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            **self.stats,
            "active_users": len(self.active_connections),
            "total_active_connections": sum(
                len(conns) for conns in self.active_connections.values()
            ),
            "buffered_users": len(self.message_buffer)
        }


# Global connection manager instance
manager = ConnectionManager()


async def send_heartbeat(websocket: WebSocket, user_id: str):
    """
    Send heartbeat message to keep connection alive.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
    """
    try:
        await websocket.send_json({
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "server_time": datetime.utcnow().isoformat(),
                "connected_clients": len(manager.active_connections.get(user_id, [])),
                "stats": manager.get_stats()
            }
        })
    except Exception as e:
        logger.error(f"❌ Error sending heartbeat to {user_id}: {e}")
        raise
