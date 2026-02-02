#!/usr/bin/env python3
"""
Task-Orchestrator MCP-to-HTTP Wrapper with Circuit Breaker
Provides REST API interface for the MCP-based task-orchestrator
"""

from fastapi import FastAPI, HTTPException
from subprocess import Popen, PIPE
import json
import time
import threading
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Import circuit breaker
from circuit_breaker import CircuitBreaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Task-Orchestrator MCP Wrapper", version="1.0.0")

# Global process reference
task_orchestrator_process: Optional[Popen] = None

# Circuit breaker for MCP communication
mcp_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30.0,
    adhd_aware=True  # Longer timeouts for focus sessions
)

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: Optional[str] = "medium"
    complexity: Optional[float] = 0.5

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    complexity: Optional[float] = None

def start_task_orchestrator():
    """Start the task-orchestrator as a subprocess in stdio mode."""
    global task_orchestrator_process
    if task_orchestrator_process is None or task_orchestrator_process.poll() is not None:
        logger.info("Starting task-orchestrator subprocess...")
        try:
            task_orchestrator_process = Popen([
                'docker', 'run', '--rm', '-i',
                'ghcr.io/jpicklyk/task-orchestrator:latest'
            ], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, bufsize=1)
            logger.info("Task-orchestrator subprocess started successfully")
        except Exception as e:
            logger.error(f"Failed to start task-orchestrator: {e}")
            raise

def send_mcp_command(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send MCP command to task-orchestrator and get response with circuit breaker."""
    if task_orchestrator_process is None or task_orchestrator_process.poll() is not None:
        start_task_orchestrator()

    if task_orchestrator_process is None:
        raise HTTPException(status_code=500, detail="Task-Orchestrator not available")

    def _send_command():
        try:
            command = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": int(time.time() * 1000)
            }

            logger.info(f"Sending MCP command: {command}")

            task_orchestrator_process.stdin.write(json.dumps(command) + '\n')
            task_orchestrator_process.stdin.flush()

            response_line = None
            timeout = 5.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                if task_orchestrator_process.stdout.readable():
                    response_line = task_orchestrator_process.stdout.readline().strip()
                    if response_line:
                        break
                time.sleep(0.1)

            if not response_line:
                # Mock response for Phase 1
                logger.warning(f"No response from task-orchestrator for method '{method}', returning mock response")
                return {
                    "method": method,
                    "status": "mock_response",
                    "note": "MCP protocol under investigation - using mock responses",
                    "params": params,
                    "timestamp": time.time()
                }

            logger.info(f"Received response: {response_line}")

            response = json.loads(response_line)
            if "error" in response:
                raise Exception(f"MCP error: {response['error']}")

            return response.get("result", {})

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {response_line}")
            raise Exception(f"Invalid response format: {e}")
        except Exception as e:
            logger.error(f"MCP communication error: {e}")
            raise Exception(f"MCP communication failed: {e}")

    try:
        result = mcp_circuit_breaker.call(_send_command)
        return result
    except Exception as e:
        logger.error(f"Circuit breaker blocked MCP call: {e}")
        raise HTTPException(status_code=503, detail=f"Circuit breaker OPEN - MCP service unavailable: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize task-orchestrator on startup."""
    try:
        start_task_orchestrator()
        logger.info("MCP Wrapper startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Don't fail startup, let health check handle it

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up subprocess on shutdown."""
    global task_orchestrator_process
    if task_orchestrator_process and task_orchestrator_process.poll() is None:
        task_orchestrator_process.terminate()
        task_orchestrator_process.wait(timeout=5)
        logger.info("Task-orchestrator subprocess terminated")

@app.post("/tasks")
async def create_task(task: TaskCreate):
    """
    Create a new task in the task-orchestrator.
    """
    try:
        result = send_mcp_command("create_task", {
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "complexity": task.complexity
        })
        return result
    except Exception as e:
        logger.error(f"Create task failed: {e}")
        raise

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """
    Retrieve a specific task by ID.
    """
    try:
        result = send_mcp_command("get_task", {"task_id": task_id})
        return result
    except Exception as e:
        logger.error(f"Get task {task_id} failed: {e}")
        raise

@app.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """
    List tasks from the task-orchestrator.
    """
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        result = send_mcp_command("list_tasks", params)
        return result
    except Exception as e:
        logger.error(f"List tasks failed: {e}")
        raise

@app.put("/tasks/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate):
    """
    Update an existing task.
    """
    try:
        update_data = {}
        if updates.status:
            update_data["status"] = updates.status
        if updates.priority:
            update_data["priority"] = updates.priority
        if updates.complexity is not None:
            update_data["complexity"] = updates.complexity

        result = send_mcp_command("update_task", {
            "task_id": task_id,
            **update_data
        })
        return result
    except Exception as e:
        logger.error(f"Update task {task_id} failed: {e}")
        raise

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the MCP wrapper and task-orchestrator.
    """
    health_status = {
        "wrapper": "healthy",
        "circuit_breaker": mcp_circuit_breaker.get_state().value,
        "task_orchestrator": "unknown",
        "timestamp": time.time(),
        "phase": "investigation"
    }

    try:
        # Test MCP communication through circuit breaker
        result = send_mcp_command("health")
        health_status["task_orchestrator"] = "responding"
        health_status["details"] = result
    except Exception as e:
        health_status["task_orchestrator"] = "unhealthy"
        health_status["details"] = str(e)

    return health_status

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Task-Orchestrator MCP Wrapper with Circuit Breaker",
        "version": "1.0.0",
        "phase": "investigation",
        "circuit_breaker_state": mcp_circuit_breaker.get_state().value,
        "endpoints": [
            "POST /tasks - Create task",
            "GET /tasks - List tasks",
            "GET /tasks/{task_id} - Get task",
            "PUT /tasks/{task_id} - Update task",
            "GET /health - Health check"
        ],
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting MCP Wrapper with Circuit Breaker on port 8084...")
    uvicorn.run(app, host="0.0.0.0", port=8084, log_level="info")