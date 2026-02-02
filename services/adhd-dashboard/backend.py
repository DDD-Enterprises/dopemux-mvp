import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

import aiohttp
import redis.asyncio as redis
from fastapi import FastAPI, Security, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ADHD Dashboard API", version="1.0.0")

# API Key authentication
API_KEY = os.getenv("DASHBOARD_API_KEY", None)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if API_KEY is None: return None
    if api_key != API_KEY: raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8097,http://127.0.0.1:8097").split(",")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["GET"], allow_headers=["X-API-Key"])

# Service URLs
ACTIVITY_CAPTURE_URL = os.getenv("ACTIVITY_CAPTURE_URL", "http://localhost:8096")
ADHD_ENGINE_URL = os.getenv("ADHD_ENGINE_URL", "http://localhost:8095")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

async def redis_pubsub_reader():
    """Background task to read from Redis Pub/Sub and broadcast to WebSockets."""
    logger.info("📡 Starting Redis Pub/Sub reader for ADHD state changes...")
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe("adhd:state_changes:*")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                data = message["data"]
                await manager.broadcast(data)
    except Exception as e:
        logger.error(f"Redis Pub/Sub error: {e}")
    finally:
        await pubsub.unpsubscribe("adhd:state_changes:*")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_pubsub_reader())

@app.get("/")
async def root():
    return HTMLResponse(content=DASHBOARD_HTML)

@app.websocket("/ws/state")
async def websocket_endpoint(websocket: WebSocket, user_id: str = "hue"):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/metrics")
async def get_metrics(api_key: str = Security(verify_api_key)):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ACTIVITY_CAPTURE_URL}/metrics") as response:
                if response.status == 200: return await response.json()
                return {"error": "Activity Capture unavailable"}
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {"error": str(e)}

@app.get("/api/adhd-state")
async def get_adhd_state(api_key: str = Security(verify_api_key)):
    try:
        async with aiohttp.ClientSession() as session:
            health_res = await session.get(f"{ADHD_ENGINE_URL}/health")
            health = await health_res.json() if health_res.status == 200 else {}
            energy_res = await session.get(f"{ADHD_ENGINE_URL}/api/v1/energy-level/hue")
            energy = await energy_res.json() if energy_res.status == 200 else {}
            attn_res = await session.get(f"{ADHD_ENGINE_URL}/api/v1/attention-state/hue")
            attention = await attn_res.json() if attn_res.status == 200 else {}
            return {"health": health, "energy": energy, "attention": attention}
    except Exception as e:
        logger.error(f"Failed to get ADHD state: {e}")
        return {"error": str(e)}

@app.get("/api/sessions/today")
async def get_today_sessions(api_key: str = Security(verify_api_key)):
    metrics = await get_metrics()
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sessions_tracked": metrics.get("sessions_tracked", 0),
        "activities_logged": metrics.get("activities_logged", 0),
        "session_active": metrics.get("session_active", False),
        "current_duration": metrics.get("current_session_duration_minutes", 0)
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "adhd-dashboard"}

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ADHD Dashboard 🚀</title>
    <style>
        body { font-family: 'Inter', -apple-system, sans-serif; background: #0f0f12; color: #e0e0e6; padding: 40px; margin: 0; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; }
        .title { font-size: 32px; font-weight: 800; background: linear-gradient(90deg, #4ec9b0, #9cdcfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .live-indicator { display: flex; align-items: center; font-size: 14px; color: #888; }
        .dot { width: 8px; height: 8px; border-radius: 50%; background: #4ec9b0; margin-right: 8px; box-shadow: 0 0 10px #4ec9b0; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }
        .card { background: #1a1a20; border: 1px solid #2d2d35; border-radius: 16px; padding: 24px; transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); border-color: #444; }
        .card-title { font-size: 14px; text-transform: uppercase; color: #888; letter-spacing: 1px; margin-bottom: 16px; }
        .card-value { font-size: 36px; font-weight: 700; color: #fff; }
        .card-subtext { font-size: 16px; color: #bbb; margin-top: 8px; }
        .metric-highlight { color: #4ec9b0; }
        .metric-warn { color: #ce9178; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">ADHD Operations Dashboard</div>
            <div class="live-indicator"><div class="dot"></div> LIVE UPDATES ENABLED</div>
        </div>
        <div class="grid">
            <div class="card">
                <div class="card-title">Current Energy Level</div>
                <div id="energy-value" class="card-value">--</div>
                <div id="energy-sub" class="card-subtext">Calculating patterns...</div>
            </div>
            <div class="card">
                <div class="card-title">Attention State</div>
                <div id="attention-value" class="card-value">--</div>
                <div id="attention-sub" class="card-subtext">Monitoring focus...</div>
            </div>
            <div class="card">
                <div class="card-title">Cognitive Load</div>
                <div id="load-value" class="card-value">--</div>
                <div id="load-sub" class="card-subtext">System equilibrium...</div>
            </div>
            <div class="card">
                <div class="card-title">Current Session</div>
                <div id="session-value" class="card-value">-- min</div>
                <div id="session-sub" class="card-subtext">0 tasks completed today</div>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws/state?user_id=hue`);
        
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === "state_update") {
                const data = msg.data;
                
                document.getElementById('energy-value').innerText = data.energy_level.toUpperCase();
                document.getElementById('energy-value').className = 'card-value ' + (data.energy_level === 'low' ? 'metric-warn' : 'metric-highlight');
                
                document.getElementById('attention-value').innerText = data.attention_state.toUpperCase();
                
                document.getElementById('load-value').innerText = (data.cognitive_load * 100).toFixed(0) + '%';
                
                document.getElementById('session-value').innerText = data.session_duration_minutes + ' min';
                document.getElementById('session-sub').innerText = data.tasks_completed_today + ' tasks completed today';
            }
        };

        // Fallback or Initial Load
        async function initialLoad() {
            const adhd = await fetch('/api/adhd-state').then(r => r.json());
            if (adhd.energy) document.getElementById('energy-value').innerText = adhd.energy.energy_level?.toUpperCase() || '--';
            if (adhd.attention) document.getElementById('attention-value').innerText = adhd.attention.attention_state?.toUpperCase() || '--';
            
            const sessions = await fetch('/api/sessions/today').then(r => r.json());
            document.getElementById('session-value').innerText = sessions.current_duration + ' min';
            document.getElementById('session-sub').innerText = sessions.activities_logged + ' tasks completed today';
        }

        initialLoad();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8097)
