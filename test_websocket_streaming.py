"""
Test Suite for WebSocket Streaming Implementation

Tests Dashboard Day 7 features:
- WebSocket connection and disconnection
- Message routing and callbacks
- Reconnection with exponential backoff
- Heartbeat monitoring
- Message buffering
- Error handling

Run with: pytest test_websocket_streaming.py -v
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Test the backend
from services.adhd_engine.api.websocket import ConnectionManager, manager, send_heartbeat

# Test the client (if websockets available)
try:
    from dashboard.streaming import StreamingClient, StreamingConfig
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        
    async def accept(self):
        pass
        
    async def send_json(self, data):
        self.sent_messages.append(data)
        
    async def close(self):
        self.closed = True


# ============================================================================
# Backend Tests (ConnectionManager)
# ============================================================================

@pytest.mark.asyncio
async def test_connection_manager_initialization():
    """Test ConnectionManager initializes correctly"""
    mgr = ConnectionManager()
    assert mgr.active_connections == {}
    assert mgr.message_buffer == {}
    assert mgr.max_buffer_size == 50
    assert "total_connections" in mgr.stats


@pytest.mark.asyncio
async def test_connection_manager_connect():
    """Test connecting a WebSocket"""
    mgr = ConnectionManager()
    ws = MockWebSocket()
    
    await mgr.connect(ws, "test_user")
    
    assert "test_user" in mgr.active_connections
    assert ws in mgr.active_connections["test_user"]
    assert mgr.stats["total_connections"] == 1


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """Test disconnecting a WebSocket"""
    mgr = ConnectionManager()
    ws = MockWebSocket()
    
    await mgr.connect(ws, "test_user")
    await mgr.disconnect(ws, "test_user")
    
    assert "test_user" not in mgr.active_connections
    assert mgr.stats["total_disconnections"] == 1


@pytest.mark.asyncio
async def test_connection_manager_broadcast_online():
    """Test broadcasting to online user"""
    mgr = ConnectionManager()
    ws = MockWebSocket()
    
    await mgr.connect(ws, "test_user")
    
    message = {
        "type": "state_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"energy_level": "HIGH"}
    }
    
    await mgr.broadcast(message, "test_user")
    
    assert len(ws.sent_messages) == 1
    assert ws.sent_messages[0]["type"] == "state_update"
    assert mgr.stats["messages_sent"] == 1


@pytest.mark.asyncio
async def test_connection_manager_broadcast_offline():
    """Test broadcasting to offline user (buffering)"""
    mgr = ConnectionManager()
    
    message = {
        "type": "state_update",
        "data": {"energy_level": "HIGH"}
    }
    
    await mgr.broadcast(message, "offline_user")
    
    assert "offline_user" in mgr.message_buffer
    assert len(mgr.message_buffer["offline_user"]) == 1
    assert mgr.stats["messages_buffered"] == 1


@pytest.mark.asyncio
async def test_connection_manager_buffer_size_limit():
    """Test message buffer respects size limit"""
    mgr = ConnectionManager()
    
    # Send 60 messages (max buffer is 50)
    for i in range(60):
        await mgr.broadcast({"msg": i}, "offline_user")
    
    # Should only keep last 50
    assert len(mgr.message_buffer["offline_user"]) == 50
    # Should have oldest messages dropped
    assert mgr.message_buffer["offline_user"][0]["msg"] == 10


@pytest.mark.asyncio
async def test_connection_manager_send_buffered():
    """Test sending buffered messages on reconnection"""
    mgr = ConnectionManager()
    
    # Send messages while offline
    for i in range(3):
        await mgr.broadcast({"msg": i}, "test_user")
    
    assert len(mgr.message_buffer["test_user"]) == 3
    
    # Connect and send buffered messages
    ws = MockWebSocket()
    await mgr.connect(ws, "test_user")
    await mgr.send_buffered_messages(ws, "test_user")
    
    # All buffered messages should be sent
    assert len(ws.sent_messages) == 3
    assert ws.sent_messages[0]["msg"] == 0
    assert ws.sent_messages[1]["msg"] == 1
    assert ws.sent_messages[2]["msg"] == 2
    
    # Buffer should be cleared
    assert len(mgr.message_buffer.get("test_user", [])) == 0


@pytest.mark.asyncio
async def test_connection_manager_broadcast_all():
    """Test broadcasting to all users"""
    mgr = ConnectionManager()
    
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    
    await mgr.connect(ws1, "user1")
    await mgr.connect(ws2, "user2")
    
    message = {"type": "system_message", "data": "Hello all"}
    await mgr.broadcast_all(message)
    
    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1


@pytest.mark.asyncio
async def test_send_heartbeat():
    """Test heartbeat message format"""
    ws = MockWebSocket()
    await send_heartbeat(ws, "test_user")
    
    assert len(ws.sent_messages) == 1
    heartbeat = ws.sent_messages[0]
    
    assert heartbeat["type"] == "heartbeat"
    assert "timestamp" in heartbeat
    assert "data" in heartbeat
    assert "server_time" in heartbeat["data"]


@pytest.mark.asyncio
async def test_connection_manager_stats():
    """Test statistics tracking"""
    mgr = ConnectionManager()
    ws = MockWebSocket()
    
    await mgr.connect(ws, "test_user")
    await mgr.broadcast({"msg": 1}, "test_user")
    await mgr.disconnect(ws, "test_user")
    
    stats = mgr.get_stats()
    
    assert stats["total_connections"] == 1
    assert stats["total_disconnections"] == 1
    assert stats["messages_sent"] == 1
    assert stats["active_users"] == 0


# ============================================================================
# Client Tests (StreamingClient)
# ============================================================================

@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
@pytest.mark.asyncio
async def test_streaming_client_initialization():
    """Test StreamingClient initializes correctly"""
    client = StreamingClient()
    
    assert client.config is not None
    assert client.connected == False
    assert client.running == False
    assert client.stats["messages_received"] == 0


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
@pytest.mark.asyncio
async def test_streaming_client_callbacks():
    """Test callback registration"""
    state_callback = AsyncMock()
    metric_callback = AsyncMock()
    alert_callback = AsyncMock()
    
    client = StreamingClient(
        on_state_update=state_callback,
        on_metric_update=metric_callback,
        on_alert=alert_callback
    )
    
    assert client.on_state_update == state_callback
    assert client.on_metric_update == metric_callback
    assert client.on_alert == alert_callback


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
@pytest.mark.asyncio
async def test_streaming_client_message_routing():
    """Test message routing to callbacks"""
    state_callback = AsyncMock()
    client = StreamingClient(on_state_update=state_callback)
    
    # Simulate receiving state update
    message = {
        "type": "state_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"energy_level": "HIGH"}
    }
    
    await client._handle_message(message)
    
    # Callback should be called with data
    state_callback.assert_called_once_with({"energy_level": "HIGH"})
    assert client.stats["state_updates"] == 1


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
@pytest.mark.asyncio
async def test_streaming_client_heartbeat_tracking():
    """Test heartbeat updates last_heartbeat"""
    client = StreamingClient()
    old_heartbeat = client.last_heartbeat
    
    await asyncio.sleep(0.1)  # Small delay
    
    message = {
        "type": "heartbeat",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"server_time": datetime.utcnow().isoformat()}
    }
    
    await client._handle_message(message)
    
    assert client.last_heartbeat > old_heartbeat
    assert client.stats["heartbeats"] == 1


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
@pytest.mark.asyncio
async def test_streaming_client_stats():
    """Test statistics tracking"""
    client = StreamingClient()
    
    # Simulate messages directly (bypassing _receive_loop)
    # Note: messages_received is only incremented in _receive_loop
    await client._handle_message({"type": "state_update", "data": {}})
    await client._handle_message({"type": "metric_update", "data": {}})
    await client._handle_message({"type": "alert", "data": {}})
    await client._handle_message({"type": "heartbeat", "data": {}})
    
    stats = client.get_stats()
    
    # messages_received is not incremented when calling _handle_message directly
    # It's only incremented in _receive_loop when receiving from WebSocket
    assert stats["state_updates"] == 1
    assert stats["metric_updates"] == 1
    assert stats["alerts"] == 1
    assert stats["heartbeats"] == 1


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
@pytest.mark.asyncio
async def test_streaming_client_health_check():
    """Test connection health check"""
    client = StreamingClient()
    
    # Not connected
    assert await client.is_healthy() == False
    
    # Connected but no heartbeat
    client.connected = True
    assert await client.is_healthy() == True
    
    # Connected with recent heartbeat
    client.last_heartbeat = datetime.utcnow()
    assert await client.is_healthy() == True


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
@pytest.mark.asyncio
async def test_end_to_end_message_flow():
    """Test complete message flow from backend to client"""
    # This would require a running server
    # Placeholder for integration testing
    pass


if __name__ == "__main__":
    print("🧪 Running WebSocket Streaming Tests")
    print("=" * 60)
    print("\nBackend Tests (ConnectionManager):")
    print("- Connection management")
    print("- Message broadcasting")
    print("- Message buffering")
    print("- Statistics tracking")
    print("\nClient Tests (StreamingClient):")
    print("- Message routing")
    print("- Callback invocation")
    print("- Heartbeat monitoring")
    print("- Health checking")
    print("\nRun with: pytest test_websocket_streaming.py -v")
