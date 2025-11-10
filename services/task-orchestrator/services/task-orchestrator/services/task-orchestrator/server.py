#!/usr/bin/env python3
"""
Task-Orchestrator MCP Server Wrapper

Simplified MCP server for Task-Orchestrator with ConPort integration.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

import uvicorn

# Import ConPort adapter
from adapters.conport_adapter import ConPortEventAdapter
from auth import verify_api_key
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from task_coordinator import TaskCoordinator

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
app = FastAPI(title="Task-Orchestrator MCP Server")

# CORS middleware for web integration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8097",
    ],  # ADHD Dashboard, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key"],  # Include X-API-Key for authentication
)

conport_adapter: Optional[ConPortEventAdapter] = None
task_coordinator: Optional[TaskCoordinator] = None


@app.on_event("startup")
async def startup_event():
    """Initialize ConPort adapter and Task Coordinator on startup."""
    global conport_adapter, task_coordinator

    workspace_id = "/Users/hue/code/dopemux-mvp"  # Should come from env
    logger.info(f"Starting Task-Orchestrator MCP Server for workspace: {workspace_id}")

    # Initialize ConPort adapter
    conport_adapter = ConPortEventAdapter(workspace_id)
    logger.info("ConPort adapter initialized")

    # Initialize Task Coordinator
    task_coordinator = TaskCoordinator(workspace_id)
    logger.info("Task Coordinator initialized")

    logger.info("Task-Orchestrator MCP Server startup complete")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "task-orchestrator-mcp",
        "conport_connected": conport_adapter is not None,
        "coordinator_ready": task_coordinator is not None,
    }


@app.post("/api/v1/tasks")
async def create_task(request: Request, api_key: str = Security(verify_api_key)):
    """Create a new task via ConPort."""
    if not conport_adapter:
        raise HTTPException(status_code=500, detail="ConPort adapter not initialized")

    data = await request.json()
    task_id = data.get("id")
    title = data.get("title", "")
    description = data.get("description", "")

    # Create task object (simplified)
    class SimpleTask:
        def __init__(self, id, title, description):
            self.id = id
            self.title = title
            self.description = description
            self.status = "PENDING"
            self.complexity_score = 0.5
            self.energy_required = "medium"

    task = SimpleTask(task_id, title, description)

    # Create in ConPort
    conport_id = await conport_adapter.create_task_in_conport(task)

    return {"task_id": task_id, "conport_id": conport_id}


@app.get("/api/v1/tasks")
async def get_tasks(api_key: str = Security(verify_api_key)):
    """Get all tasks from ConPort."""
    if not conport_adapter:
        raise HTTPException(status_code=500, detail="ConPort adapter not initialized")

    tasks = await conport_adapter.get_all_tasks_from_conport()
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": (
                    t.status.value if hasattr(t.status, "value") else str(t.status)
                ),
            }
            for t in tasks
        ]
    }


@app.post("/api/v1/coordinate")
async def coordinate_tasks(request: Request, api_key: str = Security(verify_api_key)):
    """Coordinate tasks using the Task Coordinator."""
    if not task_coordinator:
        raise HTTPException(status_code=500, detail="Task Coordinator not initialized")

    data = await request.json()
    tasks_data = data.get("tasks", [])
    adhd_state = data.get("adhd_state", {"energy": "medium", "attention": "focused"})

    # Convert to task objects
    tasks = []
    for task_data in tasks_data:

        class SimpleTask:
            def __init__(self, data):
                self.id = data.get("id")
                self.title = data.get("title", "")
                self.description = data.get("description", "")
                self.status = data.get("status", "PENDING")
                self.complexity_score = data.get("complexity", 0.5)
                self.energy_required = data.get("energy", "medium")

        tasks.append(SimpleTask(task_data))

    # Coordinate
    result = await task_coordinator.coordinate_tasks(tasks, adhd_state)
    return result


@app.get("/")
async def root():
    """Service information."""
    return {
        "service": "Task-Orchestrator MCP Server",
        "description": "ConPort-integrated task coordination service",
        "endpoints": [
            "GET /health",
            "POST /api/v1/tasks",
            "GET /api/v1/tasks",
            "POST /api/v1/coordinate",
        ],
    }


if __name__ == "__main__":
    # Get port from environment
    port = int(os.getenv("PORT", "3014"))

    logger.info(f"Starting Task-Orchestrator MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
