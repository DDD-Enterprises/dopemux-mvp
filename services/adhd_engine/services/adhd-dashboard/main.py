"""
ADHD Dashboard Backend - REST API for ADHD Metrics

Provides REST API for querying ADHD metrics, session history, and analytics.
Serves data to frontend dashboard for visualization.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="ADHD Dashboard API", version="1.0.0")

# API Key authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
EXPECTED_API_KEY = os.getenv("DASHBOARD_API_KEY", "dashboard-key-456")

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key if authentication is enabled"""
    if not EXPECTED_API_KEY:
        return None

    if api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# CORS middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8097").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


@app.get("/")
async def root():
    """Service information endpoint."""
    return {
        "service": "ADHD Dashboard Backend",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/api/metrics",
            "/api/adhd-state",
            "/api/sessions/today",
            "/api/analytics/trends",
            "/health"
        ]
    }


@app.get("/api/metrics")
async def get_metrics(api_key: str = Security(verify_api_key)):
    """Get current activity metrics."""
    # Mock data - in real implementation, would fetch from ADHD Engine
    return {
        "attention_score": 0.75,
        "energy_level": "medium",
        "session_duration_minutes": 45,
        "breaks_taken": 2,
        "tasks_completed": 8,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/adhd-state")
async def get_adhd_state(api_key: str = Security(verify_api_key)):
    """Get current ADHD state."""
    return {
        "attention_state": "focused",
        "energy_level": "medium",
        "cognitive_load": 0.6,
        "recommendations": ["Take a 5-minute break in 15 minutes"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/sessions/today")
async def get_sessions_today(api_key: str = Security(verify_api_key)):
    """Get today's sessions."""
    return {
        "sessions": [
            {
                "start_time": "09:00",
                "duration_minutes": 90,
                "tasks_completed": 5,
                "breaks_taken": 2,
                "attention_score": 0.8
            },
            {
                "start_time": "14:00",
                "duration_minutes": 60,
                "tasks_completed": 3,
                "breaks_taken": 1,
                "attention_score": 0.7
            }
        ],
        "total_sessions": 2,
        "total_duration": 150,
        "average_attention": 0.75
    }


@app.get("/api/analytics/trends")
async def get_analytics_trends(api_key: str = Security(verify_api_key)):
    """Get energy and attention trends."""
    return {
        "energy_trends": {
            "morning_average": 0.8,
            "afternoon_average": 0.6,
            "evening_average": 0.4
        },
        "attention_trends": {
            "morning_average": 0.85,
            "afternoon_average": 0.75,
            "evening_average": 0.65
        },
        "productivity_patterns": {
            "best_time": "morning",
            "optimal_session_length": 45,
            "recommended_break_frequency": 25
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "adhd-dashboard",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8097"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )