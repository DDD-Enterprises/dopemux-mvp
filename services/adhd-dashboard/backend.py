#!/usr/bin/env python3
"""
ADHD Dashboard Backend - REST API for ADHD Metrics

Provides REST API for querying ADHD metrics, session history, and analytics.
Serves data to frontend dashboard for visualization.

Endpoints:
- GET /api/metrics - Current activity metrics
- GET /api/adhd-state - Current ADHD state
- GET /api/sessions/today - Today's sessions
- GET /api/analytics/trends - Energy/attention trends
- GET /api/health - Service health

ADHD Benefit: Visualize patterns, track progress, celebrate wins
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

import aiohttp
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ADHD Dashboard API", version="1.0.0")

# API Key authentication (optional, disabled by default for localhost)
API_KEY = os.getenv("DASHBOARD_API_KEY", None)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key if authentication is enabled"""
    if API_KEY is None:
        # Auth disabled (localhost development)
        return None

    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Restricted CORS - localhost only
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8097,http://127.0.0.1:8097"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Localhost only
    allow_credentials=True,
    allow_methods=["GET"],  # Read-only dashboard
    allow_headers=["X-API-Key"],
)

# Service URLs
ACTIVITY_CAPTURE_URL = "http://localhost:8096"
ADHD_ENGINE_URL = "http://localhost:8095"


@app.get("/")
async def root():
    """Simple HTML dashboard"""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/metrics")
async def get_metrics(api_key: str = Security(verify_api_key)):
    """Get current activity metrics from Activity Capture"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ACTIVITY_CAPTURE_URL}/metrics") as response:
                if response.status == 200:
                    return await response.json()
                return {"error": "Activity Capture unavailable"}
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {"error": str(e)}


@app.get("/api/adhd-state")
async def get_adhd_state(api_key: str = Security(verify_api_key)):
    """Get current ADHD state from ADHD Engine"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get health
            async with session.get(f"{ADHD_ENGINE_URL}/health") as response:
                if response.status == 200:
                    health = await response.json()

            # Get energy
            async with session.get(f"{ADHD_ENGINE_URL}/api/v1/energy-level/hue") as response:
                energy = await response.json() if response.status == 200 else {}

            # Get attention
            async with session.get(f"{ADHD_ENGINE_URL}/api/v1/attention-state/hue") as response:
                attention = await response.json() if response.status == 200 else {}

            return {
                "health": health,
                "energy": energy,
                "attention": attention
            }

    except Exception as e:
        logger.error(f"Failed to get ADHD state: {e}")
        return {"error": str(e)}


@app.get("/api/sessions/today")
async def get_today_sessions(api_key: str = Security(verify_api_key)):
    """Get today's session summary"""
    metrics = await get_metrics()

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sessions_tracked": metrics.get("sessions_tracked", 0),
        "activities_logged": metrics.get("activities_logged", 0),
        "session_active": metrics.get("session_active", False),
        "current_duration": metrics.get("current_session_duration_minutes", 0)
    }


@app.get("/api/analytics/summary")
async def get_analytics_summary(api_key: str = Security(verify_api_key)):
    """Get analytics summary combining all sources"""
    metrics = await get_metrics()
    adhd = await get_adhd_state()

    return {
        "activity": metrics,
        "adhd_state": adhd,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Dashboard health check"""
    return {
        "status": "healthy",
        "service": "adhd-dashboard",
        "activity_capture": ACTIVITY_CAPTURE_URL,
        "adhd_engine": ADHD_ENGINE_URL
    }


# Simple HTML dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ADHD Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { font-size: 24px; margin-bottom: 20px; border-bottom: 2px solid #444; padding-bottom: 10px; }
        .section { margin: 20px 0; padding: 15px; background: #2d2d2d; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .label { color: #888; }
        .value { color: #4ec9b0; font-size: 20px; font-weight: bold; }
        .energy { color: #dcdcaa; }
        .attention { color: #9cdcfe; }
        .status-good { color: #4ec9b0; }
        .status-warning { color: #ce9178; }
        .status-urgent { color: #f48771; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">ADHD Activity Dashboard</div>

        <div class="section">
            <h3>Current Session</h3>
            <div id="current-session">Loading...</div>
        </div>

        <div class="section">
            <h3>ADHD State</h3>
            <div id="adhd-state">Loading...</div>
        </div>

        <div class="section">
            <h3>Today's Activity</h3>
            <div id="today-activity">Loading...</div>
        </div>
    </div>

    <script>
        async function loadData() {
            try {
                // Load metrics
                const metrics = await fetch('/api/metrics').then(r => r.json());
                document.getElementById('current-session').innerHTML = `
                    <div class="metric"><span class="label">Active:</span> <span class="value">${metrics.session_active ? 'YES' : 'NO'}</span></div>
                    <div class="metric"><span class="label">Duration:</span> <span class="value">${metrics.current_session_duration_minutes || 0} min</span></div>
                    <div class="metric"><span class="label">Interruptions:</span> <span class="value">${metrics.current_session_interruptions || 0}</span></div>
                `;

                // Load ADHD state
                const adhd = await fetch('/api/adhd-state').then(r => r.json());
                const energy = adhd.energy?.energy_level || 'unknown';
                const attention = adhd.attention?.attention_state || 'unknown';

                document.getElementById('adhd-state').innerHTML = `
                    <div class="metric"><span class="label">Energy:</span> <span class="value energy">${energy}</span></div>
                    <div class="metric"><span class="label">Attention:</span> <span class="value attention">${attention}</span></div>
                `;

                // Load today's activity
                const today = await fetch('/api/sessions/today').then(r => r.json());
                document.getElementById('today-activity').innerHTML = `
                    <div class="metric"><span class="label">Sessions:</span> <span class="value">${today.sessions_tracked}</span></div>
                    <div class="metric"><span class="label">Activities Logged:</span> <span class="value">${today.activities_logged}</span></div>
                `;

            } catch (e) {
                console.error('Failed to load data:', e);
            }
        }

        // Load immediately and refresh every 5 seconds
        loadData();
        setInterval(loadData, 5000);
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    logger.info("Starting ADHD Dashboard...")
    uvicorn.run(app, host="0.0.0.0", port=8097, log_level="info")
