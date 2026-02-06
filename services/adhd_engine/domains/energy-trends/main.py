"""
Energy Trends Service - FastAPI Application

Provides REST API for energy pattern visualization and analysis.
"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Dict, Any
import logging

from .visualizer import EnergyTrendVisualizer as EnergyVisualizer
from .bridge_adapter import EnergyTrendsBridgeAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
visualizer: EnergyVisualizer = None
bridge_adapter: EnergyTrendsBridgeAdapter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global visualizer, bridge_adapter
    
    logger.info("🚀 Starting Energy Trends service")
    
    # Initialize components
    visualizer = EnergyVisualizer()
    bridge_adapter = EnergyTrendsBridgeAdapter(workspace_id="default")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Energy Trends service")


app = FastAPI(
    title="Energy Trends Service",
    description="ADHD energy pattern visualization and analysis",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "energy-trends",
        "version": "1.0.0"
    }


@app.get("/api/v1/energy-trends/{user_id}")
async def get_energy_trends(user_id: str, days: int = 7):
    """
    Get energy trends for user over specified days.
    
    Args:
        user_id: User identifier
        days: Number of days to analyze (default: 7)
    """
    try:
        trends = await visualizer.analyze_trends(user_id, days)
        try:
            async with EnergyTrendsBridgeAdapter(workspace_id=user_id) as adapter:
                historical = await adapter.get_energy_trends(days=days)
                if historical:
                    trends["historical"] = historical
        except Exception as bridge_exc:
            logger.debug("Bridge-backed trend enrichment unavailable: %s", bridge_exc)
        return {
            "user_id": user_id,
            "days": days,
            "trends": trends
        }
    except Exception as e:
        logger.error(f"Failed to get energy trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/energy-visualization/{user_id}")
async def get_visualization(user_id: str, format: str = "daily"):
    """
    Get energy visualization for user.
    
    Args:
        user_id: User identifier
        format: Visualization format (daily, weekly, monthly)
    """
    try:
        viz_data = await visualizer.generate_visualization(user_id, format)
        if viz_data.get("error"):
            raise HTTPException(status_code=400, detail=viz_data["error"])
        return {
            "user_id": user_id,
            "format": format,
            "visualization": viz_data
        }
    except Exception as e:
        logger.error(f"Failed to generate visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))
