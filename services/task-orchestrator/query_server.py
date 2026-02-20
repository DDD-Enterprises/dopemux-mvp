#!/usr/bin/env python3
"""
Task-Orchestrator Query HTTP Server - Component 5 Wiring
Exposes orchestrator state via REST API on PORT_BASE+17 (default: 3017)
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query as QueryParam
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import orchestrator (assuming enhanced_orchestrator.py is in same directory)
from enhanced_orchestrator import EnhancedTaskOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PORT_BASE = int(os.getenv("PORT_BASE", "3000"))
QUERY_PORT = PORT_BASE + 17  # 3017, 3047, 3077, etc.
LEANTIME_URL = os.getenv("LEANTIME_URL", "http://leantime:80")
LEANTIME_TOKEN = os.getenv("LEANTIME_TOKEN", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
WORKSPACE_ID = os.getenv("DOPEMUX_WORKSPACE_ROOT", "/Users/hue/code/dopemux-mvp")

# Create FastAPI app
app = FastAPI(
    title="Task-Orchestrator Query API",
    description="Component 5: Cross-plane query endpoints for orchestrator state",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator: Optional[EnhancedTaskOrchestrator] = None


@app.on_event("startup")
async def startup():
    """Initialize orchestrator on startup."""
    global orchestrator
    logger.info("🚀 Starting Task-Orchestrator Query Server...")

    # Get MCP tools for ConPort integration
    from orchestrator_mcp_tools import get_mcp_tools
    mcp_tools = await get_mcp_tools()

    orchestrator = EnhancedTaskOrchestrator(
        leantime_url=LEANTIME_URL,
        leantime_token=LEANTIME_TOKEN,
        redis_url=REDIS_URL,
        workspace_id=WORKSPACE_ID,
        mcp_tools=mcp_tools
    )
    
    await orchestrator.initialize()
    logger.info(f"✅ Query server ready on port {QUERY_PORT}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    global orchestrator
    if orchestrator:
        orchestrator.running = False
        logger.info("👋 Query server shutting down")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "port": QUERY_PORT,
        "orchestrator_running": orchestrator.running if orchestrator else False
    }


@app.get("/tasks")
async def get_tasks(
    status: Optional[str] = QueryParam(None),
    sprint_id: Optional[str] = QueryParam(None),
    limit: int = QueryParam(50, ge=1, le=200)
):
    """Query tasks from orchestrator."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    tasks = await orchestrator.get_tasks(
        status_filter=status,
        sprint_id_filter=sprint_id,
        limit=limit
    )
    
    return tasks


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get single task details."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    task = await orchestrator.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task


@app.get("/adhd-state")
async def get_adhd_state():
    """Get current ADHD state."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return await orchestrator.get_adhd_state()


@app.get("/recommendations")
async def get_recommendations(
    limit: int = QueryParam(5, ge=1, le=20)
):
    """Get ADHD-aware task recommendations."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return await orchestrator.get_task_recommendations(limit=limit)


@app.get("/session")
async def get_session():
    """Get current session status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return await orchestrator.get_session_status()


@app.get("/active-sprint")
async def get_active_sprint_info():
    """Get active sprint information."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return await orchestrator.get_active_sprint_info()


if __name__ == "__main__":
    uvicorn.run(
        "query_server:app",
        host="0.0.0.0",
        port=QUERY_PORT,
        log_level="info"
    )
