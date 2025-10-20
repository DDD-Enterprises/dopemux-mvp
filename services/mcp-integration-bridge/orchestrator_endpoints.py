#!/usr/bin/env python3
"""
Task-Orchestrator Query Endpoints - Component 5
================================================

Provides REST API for cross-plane queries of Task-Orchestrator state.
Enables ConPort, UI dashboards, and other services to query:
- Task status and details
- ADHD state (energy, attention)
- Session and sprint information
- Task recommendations

Architecture:
  ConPort/UI → Integration Bridge (3016) → Task-Orchestrator (internal)
                Query Endpoints              State Provider
"""

from fastapi import APIRouter, HTTPException, Query as QueryParam
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import aiohttp
import os

logger = logging.getLogger(__name__)

# Orchestrator HTTP server configuration
PORT_BASE = int(os.getenv("PORT_BASE", "3000"))
ORCHESTRATOR_URL = f"http://localhost:{PORT_BASE + 17}"  # 3017

# Create router
router = APIRouter(
    prefix="/orchestrator",
    tags=["task-orchestrator"],
    responses={404: {"description": "Not found"}}
)


# Response Models
class TaskStatus(BaseModel):
    """Task status information."""
    task_id: str
    status: str  # TODO, IN_PROGRESS, BLOCKED, DONE
    progress: Optional[float] = None
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskDetail(BaseModel):
    """Detailed task information."""
    task_id: str
    title: str
    description: Optional[str] = None
    status: str
    progress: float
    priority: str
    complexity: Optional[float] = None
    estimated_duration: Optional[int] = None  # minutes
    dependencies: List[str] = []
    tags: List[str] = []


class ADHDState(BaseModel):
    """Current ADHD state."""
    energy_level: str  # very_low, low, medium, high, hyperfocus
    attention_level: str  # scattered, transitioning, focused, hyperfocused
    time_since_break: int  # minutes
    break_recommended: bool
    current_session_duration: int  # minutes


class TaskRecommendation(BaseModel):
    """Task recommendation based on ADHD state."""
    task_id: str
    title: str
    reason: str  # Why recommended for current state
    confidence: float  # 0.0-1.0
    priority: int  # 1-5


class SessionStatus(BaseModel):
    """Current session status."""
    session_id: Optional[str] = None
    active: bool
    started_at: Optional[datetime] = None
    duration_minutes: int
    break_count: int
    tasks_completed: int


class SprintInfo(BaseModel):
    """Active sprint information."""
    sprint_id: Optional[str] = None
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int


# Query Endpoints (All wired to Task-Orchestrator HTTP server at PORT_BASE+17)

@router.get("/tasks", response_model=List[TaskDetail])
async def list_tasks(
    status: Optional[str] = QueryParam(None, description="Filter by status"),
    sprint_id: Optional[str] = QueryParam(None, description="Filter by sprint"),
    limit: int = QueryParam(50, ge=1, le=200)
):
    """
    List all active tasks.

    **Query Parameters**:
    - status: Filter by task status (TODO, IN_PROGRESS, BLOCKED, DONE)
    - sprint_id: Filter by sprint ID
    - limit: Maximum number of results (default: 50)

    **Returns**: List of task details
    """
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        if sprint_id:
            params["sprint_id"] = sprint_id

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/tasks", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"Orchestrator returned {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Task-Orchestrator unavailable")
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskDetail)
async def get_task(task_id: str):
    """
    Get detailed information about a specific task.

    **Path Parameters**:
    - task_id: Unique task identifier

    **Returns**: Task details including status, progress, dependencies

    **Raises**: 404 if task not found
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/tasks/{task_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
                else:
                    error_text = await resp.text()
                    logger.error(f"Orchestrator returned {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)

    except HTTPException:
        raise
    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Task-Orchestrator unavailable")
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get current status of a specific task.

    **Path Parameters**:
    - task_id: Unique task identifier

    **Returns**: Task status information

    **Raises**: 404 if task not found
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/tasks/{task_id}/status") as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
                else:
                    error_text = await resp.text()
                    logger.error(f"Orchestrator returned {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)

    except HTTPException:
        raise
    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Task-Orchestrator unavailable")
    except Exception as e:
        logger.error(f"Failed to get task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adhd-state", response_model=ADHDState)
async def get_adhd_state():
    """
    Get current ADHD state (energy, attention, break status).

    **Returns**: Current ADHD state including energy level, attention level,
                time since last break, and break recommendation

    **Use Case**: UI dashboard, ConPort ADHD-aware task selection
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/adhd-state") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"Orchestrator returned {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Task-Orchestrator unavailable")
    except Exception as e:
        logger.error(f"Failed to get ADHD state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=List[TaskRecommendation])
async def get_task_recommendations(
    limit: int = QueryParam(5, ge=1, le=20)
):
    """
    Get task recommendations based on current ADHD state.

    **Query Parameters**:
    - limit: Maximum number of recommendations (default: 5)

    **Returns**: List of recommended tasks with confidence scores

    **Use Case**: ADHD-aware task selection, "what should I work on next?"
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/recommendations", params={"limit": limit}) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"Orchestrator returned {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Task-Orchestrator unavailable")
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session", response_model=SessionStatus)
async def get_session_status():
    """
    Get current session status.

    **Returns**: Session information including duration, break count,
                tasks completed

    **Use Case**: Session monitoring, break reminders, productivity tracking
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/session") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"Orchestrator returned {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Task-Orchestrator unavailable")
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active-sprint", response_model=SprintInfo)
async def get_active_sprint():
    """
    Get active sprint information.

    **Returns**: Sprint metadata, task counts, progress

    **Use Case**: Sprint dashboard, progress tracking, planning
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/active-sprint") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"Orchestrator returned {resp.status}: {error_text}")
                    raise HTTPException(status_code=resp.status, detail=error_text)

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Task-Orchestrator unavailable")
    except Exception as e:
        logger.error(f"Failed to get active sprint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
