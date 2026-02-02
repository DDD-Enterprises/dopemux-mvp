"""
Context Switch Tracker Service - FastAPI Application

Tracks context switches between files/tasks and analyzes distraction patterns.
"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import logging

from .tracker import ContextSwitchTracker
from .bridge_adapter import ContextSwitchBridgeAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
tracker: ContextSwitchTracker = None
bridge_adapter: ContextSwitchBridgeAdapter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global tracker, bridge_adapter
    
    logger.info("🚀 Starting Context Switch Tracker service")
    
    # Initialize components
    tracker = ContextSwitchTracker()
    bridge_adapter = ContextSwitchBridgeAdapter(workspace_id="default")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Context Switch Tracker service")


app = FastAPI(
    title="Context Switch Tracker",
    description="Track context switches and distraction patterns",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "context-switch-tracker",
        "version": "1.0.0"
    }


@app.post("/api/v1/track-switch")
async def track_switch(
    from_context: str,
    to_context: str,
    user_id: str = "default"
):
    """
    Track a context switch event.
    
    Args:
        from_context: Source context (file, task, etc.)
        to_context: Target context
        user_id: User identifier
    """
    try:
        result = await tracker.track_switch(from_context, to_context, user_id)
        
        # Emit event to DopeconBridge
        await bridge_adapter.emit_event(
            event_type="context.switch.detected",
            data=result
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to track context switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/switches/{user_id}")
async def get_switches(user_id: str, hours: int = 24):
    """
    Get context switches for user.
    
    Args:
        user_id: User identifier
        hours: Hours of history (default: 24)
    """
    try:
        switches = await tracker.get_switches(user_id, hours)
        return {
            "user_id": user_id,
            "hours": hours,
            "total_switches": len(switches),
            "switches": switches
        }
    except Exception as e:
        logger.error(f"Failed to get context switches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/distraction-score/{user_id}")
async def get_distraction_score(user_id: str):
    """
    Get distraction score based on context switching patterns.
    
    Args:
        user_id: User identifier
    """
    try:
        score = await tracker.calculate_distraction_score(user_id)
        return {
            "user_id": user_id,
            "distraction_score": score,
            "level": "high" if score > 0.7 else "medium" if score > 0.4 else "low"
        }
    except Exception as e:
        logger.error(f"Failed to calculate distraction score: {e}")
        raise HTTPException(status_code=500, detail=str(e))
