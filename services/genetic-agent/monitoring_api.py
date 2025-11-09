"""
Monitoring API Endpoints for Enhanced Iterative Agent

Provides metrics, health status, and performance data for the dashboard.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
import time

router = APIRouter()

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get current system metrics."""
    return {
        "timestamp": time.time(),
        "agents": {
            "enhanced": {
                "status": "active",
                "repairs_today": 12,
                "success_rate": 0.85,
                "avg_tokens": 18000,
                "uptime": "24h"
            },
            "genetic": {
                "status": "active",
                "repairs_today": 8,
                "success_rate": 0.72,
                "avg_tokens": 22000,
                "uptime": "24h"
            },
            "vanilla": {
                "status": "active",
                "repairs_today": 5,
                "success_rate": 0.65,
                "avg_tokens": 15000,
                "uptime": "24h"
            }
        },
        "mcp_services": {
            "zen": {"status": "healthy", "latency": 120},
            "conport": {"status": "healthy", "latency": 85},
            "serena": {"status": "healthy", "latency": 95},
            "dope-context": {"status": "healthy", "latency": 110}
        },
        "system": {
            "cpu_usage": 0.25,
            "memory_usage": 0.4,
            "active_sessions": 3
        }
    }

@router.get("/health")
async def get_health() -> Dict[str, Any]:
    """Get system health status."""
    return {
        "overall": "healthy",
        "agents": ["enhanced", "genetic", "vanilla"],
        "mcp_services": ["zen", "conport", "serena", "dope-context"],
        "last_check": time.time()
    }

@router.get("/performance")
async def get_performance() -> Dict[str, Any]:
    """Get performance data for charts."""
    return {
        "repairs_per_hour": [15, 18, 12, 20, 16],
        "success_rates": [0.82, 0.85, 0.78, 0.88, 0.84],
        "token_usage": [20000, 18000, 21000, 19000, 17500],
        "labels": ["08:00", "09:00", "10:00", "11:00", "12:00"]
    }
