#!/usr/bin/env python3
"""
Real-Time Coordination Dashboard

Web-based dashboard for monitoring and coordinating multiple Dopemux instances
through the event system. Provides ADHD-friendly visualization of events,
instance status, and coordination capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import sys
from pathlib import Path

# Add dopemux to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aiohttp import web
from aiohttp.web import Request, Response, WebSocketResponse
import aiohttp_cors

from dopemux.event_bus import RedisStreamsAdapter, DopemuxEvent
from dopemux.instance_registry import InstanceRegistry, InstanceStatus


class CoordinationDashboard:
    """
    Real-time dashboard for multi-instance coordination.

    Provides WebSocket-based live updates, instance monitoring,
    and coordination controls with ADHD-optimized visualization.
    """

    def __init__(self, event_bus: RedisStreamsAdapter):
        self.event_bus = event_bus
        self.instance_registry = InstanceRegistry(event_bus)

        # WebSocket connections
        self.websockets: List[WebSocketResponse] = []

        # Event tracking
        self.event_history = deque(maxlen=1000)  # Last 1000 events
        self.event_stats = defaultdict(lambda: {"count": 0, "last_seen": None})
        self.instance_events = defaultdict(list)  # Events per instance

        # Performance metrics
        self.call_durations = defaultdict(list)  # Tool call durations
        self.error_counts = defaultdict(int)  # Error counts per tool

        # Subscription ID
        self.subscription_id: Optional[str] = None

    async def start(self):
        """Start the dashboard services."""
        await self.instance_registry.start()

        # Subscribe to all events for monitoring
        self.subscription_id = await self.event_bus.subscribe(
            "*",  # Subscribe to all events
            self.handle_event
        )

        print("📊 Coordination Dashboard started")

    async def stop(self):
        """Stop the dashboard services."""
        if self.subscription_id:
            await self.event_bus.unsubscribe(self.subscription_id)

        await self.instance_registry.stop()

        # Close all websockets
        for ws in self.websockets:
            await ws.close()

        print("📊 Coordination Dashboard stopped")

    def handle_event(self, event: DopemuxEvent):
        """Handle incoming events for dashboard display."""
        # Store event
        event_data = {
            "id": event.envelope.id,
            "type": event.envelope.type,
            "namespace": event.envelope.namespace,
            "priority": event.envelope.priority.value,
            "timestamp": event.envelope.timestamp,
            "payload": event.payload,
            "adhd": {
                "cognitive_load": event.envelope.adhd_metadata.cognitive_load.value,
                "attention_required": event.envelope.adhd_metadata.attention_required,
                "focus_context": event.envelope.adhd_metadata.focus_context
            } if event.envelope.adhd_metadata else None
        }

        self.event_history.append(event_data)

        # Update statistics
        event_type = event.envelope.type
        self.event_stats[event_type]["count"] += 1
        self.event_stats[event_type]["last_seen"] = event.envelope.timestamp

        # Track by instance
        if "instance." in event.envelope.namespace:
            parts = event.envelope.namespace.split(".")
            if len(parts) > 1:
                instance_id = parts[1]
                self.instance_events[instance_id].append(event_data)

        # Track performance metrics
        if "mcp.tool_call.completed" in event_type:
            tool_name = event.payload.get("tool_name", "unknown")
            duration_ms = event.payload.get("duration_ms", 0)
            self.call_durations[tool_name].append(duration_ms)

            if event.payload.get("error"):
                self.error_counts[tool_name] += 1

        # Broadcast to websockets
        asyncio.create_task(self.broadcast_event(event_data))

    async def broadcast_event(self, event_data: Dict[str, Any]):
        """Broadcast event to all connected websockets."""
        message = json.dumps({
            "type": "event",
            "data": event_data
        })

        # Send to all connected clients
        for ws in self.websockets[:]:
            try:
                await ws.send_str(message)
            except ConnectionError:
                self.websockets.remove(ws)

    async def handle_websocket(self, request: Request):
        """Handle WebSocket connections from dashboard clients."""
        ws = WebSocketResponse()
        await ws.prepare(request)
        self.websockets.append(ws)

        # Send initial state
        await ws.send_str(json.dumps({
            "type": "initial_state",
            "data": {
                "instances": self.get_instance_summary(),
                "event_stats": dict(self.event_stats),
                "recent_events": list(self.event_history)[-50:],  # Last 50 events
                "performance": self.get_performance_summary()
            }
        }))

        # Handle client messages
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)

                if data["action"] == "request_handoff":
                    await self.handle_handoff_request(data)
                elif data["action"] == "clear_events":
                    self.event_history.clear()
                    await ws.send_str(json.dumps({
                        "type": "events_cleared"
                    }))

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')

        self.websockets.remove(ws)
        return ws

    async def handle_handoff_request(self, data: Dict[str, Any]):
        """Handle session handoff request from dashboard."""
        from_instance = data.get("from_instance")
        to_instance = data.get("to_instance")
        session_data = data.get("session_data", {})

        success = await self.instance_registry.request_session_handoff(
            from_instance, to_instance, session_data
        )

        # Broadcast result
        await self.broadcast_event({
            "type": "handoff_result",
            "success": success,
            "from_instance": from_instance,
            "to_instance": to_instance
        })

    def get_instance_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all instances."""
        instances = []
        for instance_id, instance_info in self.instance_registry.instances.items():
            instances.append({
                "id": instance_id,
                "status": instance_info.status.value,
                "port_base": instance_info.port_base,
                "uptime_minutes": int((datetime.now() - instance_info.started_at).total_seconds() / 60),
                "event_count": len(self.instance_events.get(instance_id, [])),
                "last_heartbeat": instance_info.last_heartbeat.isoformat()
            })
        return instances

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        perf = {}
        for tool_name, durations in self.call_durations.items():
            if durations:
                perf[tool_name] = {
                    "call_count": len(durations),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "max_duration_ms": max(durations),
                    "min_duration_ms": min(durations),
                    "error_count": self.error_counts.get(tool_name, 0)
                }
        return perf

    async def serve_dashboard(self, request: Request):
        """Serve the dashboard HTML."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Dopemux Coordination Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            border-radius: 10px;
        }

        h1 {
            font-size: 28px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }

        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #3fb950;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
        }

        .card h2 {
            font-size: 16px;
            margin-bottom: 15px;
            color: #58a6ff;
        }

        .instance {
            background: #0d1117;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .instance-status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-active { background: #1f6feb; }
        .status-idle { background: #8b949e; }
        .status-error { background: #da3633; }

        .event-stream {
            background: #0d1117;
            height: 300px;
            overflow-y: auto;
            padding: 10px;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
        }

        .event-item {
            padding: 4px 0;
            border-bottom: 1px solid #21262d;
        }

        .event-type { color: #58a6ff; }
        .event-time { color: #8b949e; }
        .event-priority-HIGH { color: #ffa657; }
        .event-priority-CRITICAL { color: #f85149; }

        .metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }

        .metric {
            text-align: center;
            padding: 10px;
            background: #0d1117;
            border-radius: 6px;
        }

        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #58a6ff;
        }

        .metric-label {
            font-size: 12px;
            color: #8b949e;
            margin-top: 5px;
        }

        .controls {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }

        button {
            background: #238636;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }

        button:hover {
            background: #2ea043;
        }

        button:disabled {
            background: #484f58;
            cursor: not-allowed;
        }

        .adhd-indicator {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 5px;
        }

        .load-minimal { background: #0969da; }
        .load-low { background: #1f6feb; }
        .load-medium { background: #fb8500; }
        .load-high { background: #fa7343; }
        .load-extreme { background: #da3633; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Dopemux Coordination Dashboard</h1>
        <div class="status">
            <span class="status-indicator"></span>
            <span id="connection-status">Connected</span>
            <span id="event-rate">0 events/sec</span>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>📊 Instances</h2>
            <div id="instances"></div>
            <div class="controls">
                <button onclick="requestHandoff()">Request Handoff</button>
            </div>
        </div>

        <div class="card">
            <h2>📈 Performance</h2>
            <div class="metrics" id="metrics">
                <div class="metric">
                    <div class="metric-value" id="total-events">0</div>
                    <div class="metric-label">Total Events</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="avg-latency">0ms</div>
                    <div class="metric-label">Avg Latency</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="error-rate">0%</div>
                    <div class="metric-label">Error Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="active-tools">0</div>
                    <div class="metric-label">Active Tools</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🧠 ADHD Metrics</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value" id="focus-events">0</div>
                    <div class="metric-label">Focus Events</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="high-load">0</div>
                    <div class="metric-label">High Load</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="completions">0</div>
                    <div class="metric-label">Completions</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="interruptions">0</div>
                    <div class="metric-label">Safe to Interrupt</div>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>🔄 Event Stream</h2>
        <div class="event-stream" id="event-stream"></div>
        <div class="controls">
            <button onclick="clearEvents()">Clear Events</button>
            <button onclick="togglePause()" id="pause-btn">Pause</button>
        </div>
    </div>

    <script>
        let ws;
        let paused = false;
        let eventCount = 0;
        let eventRate = 0;
        let lastEventTime = Date.now();

        function connect() {
            ws = new WebSocket('ws://localhost:8090/ws');

            ws.onopen = () => {
                document.getElementById('connection-status').textContent = 'Connected';
            };

            ws.onclose = () => {
                document.getElementById('connection-status').textContent = 'Disconnected';
                setTimeout(connect, 3000);
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);

                if (message.type === 'initial_state') {
                    updateDashboard(message.data);
                } else if (message.type === 'event' && !paused) {
                    handleEvent(message.data);
                }
            };
        }

        function updateDashboard(data) {
            // Update instances
            const instancesDiv = document.getElementById('instances');
            instancesDiv.innerHTML = data.instances.map(inst => `
                <div class="instance">
                    <span>Instance ${inst.id} (Port ${inst.port_base})</span>
                    <span class="instance-status status-${inst.status}">${inst.status}</span>
                </div>
            `).join('');

            // Update metrics
            document.getElementById('total-events').textContent = data.recent_events.length;

            // Calculate average latency from performance data
            const perfs = Object.values(data.performance || {});
            if (perfs.length > 0) {
                const avgLatency = perfs.reduce((sum, p) => sum + p.avg_duration_ms, 0) / perfs.length;
                document.getElementById('avg-latency').textContent = Math.round(avgLatency) + 'ms';
            }
        }

        function handleEvent(eventData) {
            eventCount++;
            document.getElementById('total-events').textContent = eventCount;

            // Calculate event rate
            const now = Date.now();
            const timeDiff = (now - lastEventTime) / 1000;
            eventRate = 1 / timeDiff;
            lastEventTime = now;
            document.getElementById('event-rate').textContent = eventRate.toFixed(1) + ' events/sec';

            // Add to event stream
            const stream = document.getElementById('event-stream');
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event-item';

            const timestamp = new Date(eventData.timestamp).toLocaleTimeString();
            const priority = eventData.priority || 'NORMAL';

            let cognitiveLoad = '';
            if (eventData.adhd) {
                cognitiveLoad = `<span class="adhd-indicator load-${eventData.adhd.cognitive_load}">
                    ${eventData.adhd.cognitive_load}
                </span>`;
            }

            eventDiv.innerHTML = `
                <span class="event-time">${timestamp}</span>
                <span class="event-type">${eventData.type}</span>
                <span class="event-priority-${priority}">${priority}</span>
                ${cognitiveLoad}
            `;

            stream.insertBefore(eventDiv, stream.firstChild);

            // Keep only last 100 events in view
            while (stream.children.length > 100) {
                stream.removeChild(stream.lastChild);
            }

            // Update ADHD metrics
            if (eventData.adhd) {
                if (eventData.adhd.cognitive_load === 'HIGH' || eventData.adhd.cognitive_load === 'EXTREME') {
                    const highLoad = document.getElementById('high-load');
                    highLoad.textContent = parseInt(highLoad.textContent) + 1;
                }

                if (eventData.adhd.focus_context === 'positive_reinforcement') {
                    const completions = document.getElementById('completions');
                    completions.textContent = parseInt(completions.textContent) + 1;
                }
            }
        }

        function clearEvents() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    action: 'clear_events'
                }));
                document.getElementById('event-stream').innerHTML = '';
                eventCount = 0;
            }
        }

        function togglePause() {
            paused = !paused;
            document.getElementById('pause-btn').textContent = paused ? 'Resume' : 'Pause';
        }

        function requestHandoff() {
            const from = prompt('From instance:');
            const to = prompt('To instance:');

            if (from && to && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    action: 'request_handoff',
                    from_instance: from,
                    to_instance: to,
                    session_data: {}
                }));
            }
        }

        // Connect on load
        connect();

        // Update rate every second
        setInterval(() => {
            if (!paused) {
                // Decay rate if no recent events
                const timeSinceLastEvent = (Date.now() - lastEventTime) / 1000;
                if (timeSinceLastEvent > 1) {
                    eventRate = Math.max(0, eventRate * 0.9);
                    document.getElementById('event-rate').textContent = eventRate.toFixed(1) + ' events/sec';
                }
            }
        }, 1000);
    </script>
</body>
</html>
"""
        return Response(text=html, content_type="text/html")


async def create_app():
    """Create the web application."""
    # Initialize event bus
    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    await event_bus.connect()

    # Create dashboard
    dashboard = CoordinationDashboard(event_bus)
    await dashboard.start()

    # Create web app
    app = web.Application()

    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })

    # Add routes
    app.router.add_get("/", dashboard.serve_dashboard)
    app.router.add_get("/ws", dashboard.handle_websocket)

    # Configure CORS for routes
    for route in list(app.router.routes()):
        cors.add(route)

    # Cleanup on shutdown
    async def cleanup(app):
        await dashboard.stop()
        await event_bus.disconnect()

    app.on_shutdown.append(cleanup)

    return app


def main():
    """Run the coordination dashboard."""
    print("🚀 Starting Dopemux Coordination Dashboard")
    print("=" * 50)
    print("Dashboard URL: http://localhost:8090")
    print("Redis Commander: http://localhost:8081")
    print()

    # Run the web server
    web.run_app(create_app(), host="0.0.0.0", port=8090)


if __name__ == "__main__":
    main()