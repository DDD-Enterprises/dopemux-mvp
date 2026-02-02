"""
DopeconBridge API Routes - FastAPI route definitions.

Extracted and organized from main.py ~1700-2915.
"""

import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    security,
)
from .clients import conport_client, mcp_client, update_context_delta
from .config import settings
from .core import cache_manager, db_manager
from .models import TaskPriority, TaskStatus


logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PRDParseRequest(BaseModel):
    """Request to parse a PRD document."""
    content: str = Field(..., description="PRD content to parse")
    project_id: str = Field(..., description="Project ID for task creation")


class PublishEventRequest(BaseModel):
    """Request to publish an event."""
    stream: str = Field(default="dopemux:events", description="Redis Stream name")
    event_type: str = Field(..., description="Event type (e.g., tasks_imported)")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    source: Optional[str] = Field(None, description="Event source identifier")


class TaskUpdateRequest(BaseModel):
    """Request to update task status."""
    status: str = Field(..., description="New task status")
    assigned_to: Optional[str] = Field(None, description="User assignment")


# ============================================================================
# ROUTERS
# ============================================================================

# Auth routes
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Event routes
events_router = APIRouter(prefix="/events", tags=["EventBus"])

# Task routes  
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])

# DDG routes (Dope Decision Graph)
ddg_router = APIRouter(prefix="/ddg", tags=["Decision Graph"])

# Health routes
health_router = APIRouter(tags=["Health"])


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@auth_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/refresh")
async def refresh_token(current_token: str = Depends(security)):
    """Refresh access token."""
    # In production, validate the current token and issue a new one
    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@health_router.get("/health")
async def health_check():
    """Health check with service status."""
    try:
        services_health = await mcp_client.health_check_all()
        return {
            "status": "healthy",
            "instance": settings.instance_name,
            "port": settings.port,
            "services": services_health
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "instance": settings.instance_name,
            "error": str(e)
        }


@health_router.get("/")
async def root():
    """Service information."""
    return {
        "service": "DopeconBridge",
        "version": "2.0.0",
        "instance": settings.instance_name,
        "port": settings.port,
        "architecture": "modular",
        "docs": f"http://localhost:{settings.port}/docs"
    }


# ============================================================================
# EVENT BUS ENDPOINTS
# ============================================================================

@events_router.post("")
async def publish_event(request: PublishEventRequest):
    """Publish event to Redis Stream for cross-service coordination."""
    try:
        from .event_bus import EventBus, Event
        
        event_bus = EventBus()
        await event_bus.initialize()
        
        event = Event(
            type=request.event_type,
            data=request.data,
            source=request.source or settings.service_name
        )
        
        msg_id = await event_bus.publish(request.stream, event)
        
        return {
            "success": True,
            "message_id": msg_id,
            "stream": request.stream,
            "event_type": request.event_type
        }
    except Exception as e:
        logger.error(f"Event publish failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@events_router.get("/stream")
async def subscribe_to_events(
    stream: str = "dopemux:events",
    consumer_group: str = "dashboard"
):
    """Subscribe to event stream via Server-Sent Events (SSE)."""
    from .event_bus import EventBus
    
    event_bus = EventBus()
    await event_bus.initialize()
    
    async def event_generator():
        consumer = f"sse-{settings.instance_name}"
        async for msg_id, event in event_bus.subscribe(stream, consumer_group, consumer):
            yield f"data: {json.dumps({'id': msg_id, 'event': event.to_dict()})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@events_router.get("/history")
async def get_event_history(
    stream: str = "dopemux:events",
    count: int = Query(100, ge=1, le=1000)
):
    """Get event history from Redis Stream."""
    try:
        cache_client = await cache_manager.get_client()
        
        entries = await cache_client.xrevrange(stream, count=count)
        
        events = []
        for msg_id, data in entries:
            events.append({
                "id": msg_id,
                "type": data.get("type", "unknown"),
                "data": json.loads(data.get("data", "{}")) if data.get("data") else {},
                "source": data.get("source"),
                "timestamp": data.get("timestamp")
            })
        
        return {
            "stream": stream,
            "count": len(events),
            "events": events
        }
    except Exception as e:
        logger.error(f"Event history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Convenience event endpoints
@events_router.post("/tasks-imported")
async def publish_tasks_imported(task_count: int, sprint_id: str):
    """Publish tasks_imported event (convenience endpoint)."""
    request = PublishEventRequest(
        event_type="tasks_imported",
        data={"task_count": task_count, "sprint_id": sprint_id}
    )
    return await publish_event(request)


@events_router.post("/session-started")
async def publish_session_started(task_id: str, duration_minutes: int = 25):
    """Publish session_started event (convenience endpoint)."""
    request = PublishEventRequest(
        event_type="session_started",
        data={"task_id": task_id, "duration_minutes": duration_minutes}
    )
    return await publish_event(request)


@events_router.post("/progress-updated")
async def publish_progress_updated(task_id: str, status: str, progress: float):
    """Publish progress_updated event (convenience endpoint)."""
    request = PublishEventRequest(
        event_type="progress_updated",
        data={"task_id": task_id, "status": status, "progress": progress}
    )
    return await publish_event(request)


# ============================================================================
# TASK ENDPOINTS
# ============================================================================

@tasks_router.post("/parse-prd")
async def parse_prd(request: PRDParseRequest, http_request: Request):
    """Parse PRD document into tasks across all systems with ADHD context preservation."""
    from .services.task_integration import task_service
    
    try:
        # Update context for ADHD tracking
        update_context_delta(
            http_request,
            "last_prd_parse",
            {"project_id": request.project_id, "content_length": len(request.content)}
        )
        
        tasks = await task_service.parse_prd_to_tasks(request.content, request.project_id)
        
        return {
            "success": True,
            "task_count": len(tasks),
            "project_id": request.project_id,
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.value
                }
                for t in tasks
            ]
        }
    except Exception as e:
        logger.error(f"PRD parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.get("/next/{project_id}")
async def get_next_tasks(project_id: str, limit: int = Query(5, ge=1, le=20)):
    """Get next actionable tasks for ADHD-friendly workflow."""
    from .services.task_integration import task_service
    
    try:
        tasks = await task_service.get_next_actionable_tasks(project_id, limit)
        
        return {
            "success": True,
            "project_id": project_id,
            "count": len(tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description[:200] if t.description else None,
                    "priority": t.priority.value,
                    "estimated_hours": t.estimated_hours
                }
                for t in tasks
            ]
        }
    except Exception as e:
        logger.error(f"Get next tasks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@tasks_router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update task status across all systems."""
    from .services.task_integration import task_service
    
    try:
        status = TaskStatus(request.status)
        result = await task_service.update_task_status(
            task_id,
            status,
            request.assigned_to
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Task status update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DDG ENDPOINTS (Dope Decision Graph)
# ============================================================================

@ddg_router.get("/decisions")
async def ddg_recent_decisions(
    workspace_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Get recent decisions from the decision graph."""
    from sqlalchemy import select
    from .models import DdgDecision
    
    try:
        async with await db_manager.get_session() as session:
            query = select(DdgDecision).order_by(DdgDecision.created_at.desc()).limit(limit)
            if workspace_id:
                query = query.where(DdgDecision.workspace_id == workspace_id)
            
            result = await session.execute(query)
            decisions = result.scalars().all()
            
            return {
                "count": len(decisions),
                "decisions": [
                    {
                        "id": d.id,
                        "summary": d.summary,
                        "tags": d.tags or [],
                        "workspace_id": d.workspace_id,
                        "created_at": d.created_at.isoformat()
                    }
                    for d in decisions
                ]
            }
    except Exception as e:
        logger.error(f"DDG decisions query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ddg_router.get("/search")
async def ddg_search_decisions(
    q: str,
    workspace_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Search decisions by text query."""
    from sqlalchemy import select
    from .models import DdgDecision
    
    try:
        async with await db_manager.get_session() as session:
            query = select(DdgDecision).where(
                DdgDecision.summary.ilike(f"%{q}%")
            ).order_by(DdgDecision.created_at.desc()).limit(limit)
            
            if workspace_id:
                query = query.where(DdgDecision.workspace_id == workspace_id)
            
            result = await session.execute(query)
            decisions = result.scalars().all()
            
            return {
                "query": q,
                "count": len(decisions),
                "decisions": [
                    {
                        "id": d.id,
                        "summary": d.summary,
                        "tags": d.tags or [],
                        "workspace_id": d.workspace_id
                    }
                    for d in decisions
                ]
            }
    except Exception as e:
        logger.error(f"DDG search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTER AGGREGATION
# ============================================================================

def get_all_routers() -> List[APIRouter]:
    """Return all API routers for inclusion in app."""
    return [
        health_router,
        auth_router,
        events_router,
        tasks_router,
        ddg_router,
    ]
