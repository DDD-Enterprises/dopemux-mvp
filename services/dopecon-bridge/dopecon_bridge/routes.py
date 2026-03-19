"""
DopeconBridge API routes for the active runtime.

The active bridge is an adapter and proxy layer only. It must not act as
canonical task, workflow, decision, or progress authority.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from .auth import authenticate_user, create_access_token, get_current_user, security
from .clients import conport_client, mcp_client, update_context_delta
from .config import settings
from .core import cache_manager
from .leantime_contract import (
    build_leantime_tool_request,
    normalize_leantime_route_response,
)


logger = logging.getLogger(__name__)


WORKFLOW_SIGNIFICANT_OPERATIONS = {
    "update_task_status",
    "leantime.update_task_status",
    "update_sprint",
    "leantime.update_sprint",
    "transition_work_item",
    "pm_transition_work_item",
    "next_action",
    "get_next_action",
}
SAFE_PM_ROUTE_OPERATIONS = {
    "get_tasks",
    "list_tasks",
    "create_task",
    "update_task",
    "create_project",
    "get_project_status",
    "allocate_resource",
    "leantime.get_tasks",
    "leantime.list_tasks",
    "leantime.create_task",
    "leantime.update_task",
    "leantime.create_project",
    "leantime.get_project_status",
    "leantime.allocate_resource",
}


class PRDParseRequest(BaseModel):
    """Legacy task-creation request that now fails closed."""

    content: str = Field(..., description="PRD content to parse")
    project_id: str = Field(..., description="Project ID for task creation")


class PublishEventRequest(BaseModel):
    """Request to publish an event."""

    stream: str = Field(default="dopemux:events", description="Redis Stream name")
    event_type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    source: Optional[str] = Field(None, description="Event source identifier")


class TaskUpdateRequest(BaseModel):
    """Legacy task update request that now fails closed."""

    status: str = Field(..., description="New task status")
    assigned_to: Optional[str] = Field(None, description="User assignment")


class PMRouteRequest(BaseModel):
    """Normalized PM-plane request body."""

    source: str = Field(default="cognitive", description="Source plane label")
    operation: str = Field(..., description="Normalized PM operation")
    data: Dict[str, Any] = Field(default_factory=dict, description="Operation payload")
    requester: str = Field(..., description="Calling client or service")


class CustomDataRequest(BaseModel):
    workspace_id: Optional[str] = None
    category: str
    key: str
    value: Dict[str, Any]


class DecisionRequest(BaseModel):
    workspace_id: Optional[str] = None
    summary: Optional[str] = None
    rationale: str
    implementation_details: Optional[str] = None
    alternatives: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    confidence_level: str = "medium"
    decision_type: str = "implementation"


class ProgressRequest(BaseModel):
    workspace_id: Optional[str] = None
    description: str
    status: str = "IN_PROGRESS"
    percentage: int = 0
    priority: str = "medium"
    linked_decision_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
events_router = APIRouter(prefix="/events", tags=["EventBus"])
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])
ddg_router = APIRouter(prefix="/ddg", tags=["Decision Graph"])
pm_router = APIRouter(prefix="/route", tags=["PM Routing"])
kg_router = APIRouter(prefix="/kg", tags=["ConPort Proxy"])
health_router = APIRouter(tags=["Health"])


def _default_workspace_id(workspace_id: Optional[str]) -> str:
    return workspace_id or settings.default_workspace_id


def _correlation_id(request: Request) -> str:
    return request.headers.get("X-Request-ID") or str(uuid4())


def _reject_policy_blocked(detail: str) -> None:
    raise HTTPException(status_code=409, detail=detail)


def _is_workflow_significant_pm_mutation(operation: str, payload: Dict[str, Any]) -> bool:
    normalized = (operation or "").strip().lower()
    if normalized in WORKFLOW_SIGNIFICANT_OPERATIONS:
        return True
    return "status" in payload or "transition" in normalized or "workflow" in normalized


def _normalize_decision_list(payload: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
    items = list(payload.get("decisions", []))
    return {
        "count": int(payload.get("count", len(items))),
        "items": items,
        "decisions": items,
        "query": query,
        "source": "conport",
    }


def _normalize_search_results(payload: Dict[str, Any], query: str) -> Dict[str, Any]:
    results = payload.get("results", {})
    items = list(results.get("decisions", []))
    return {
        "count": int(payload.get("total_count", len(items))),
        "items": items,
        "decisions": items,
        "query": query,
        "source": "conport",
    }


def _normalize_progress_list(payload: Dict[str, Any]) -> Dict[str, Any]:
    entries = list(payload.get("progress", []))
    return {
        "count": int(payload.get("count", len(entries))),
        "entries": entries,
        "progress": entries,
        "source": "conport",
    }


def _normalize_custom_data_read(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "items" in payload and isinstance(payload["items"], list):
        items = list(payload["items"])
    elif "value" in payload:
        items = [payload]
    else:
        items = []
    return {
        "success": True,
        "count": int(payload.get("count", len(items))),
        "data": items,
        "source": "conport",
    }


async def _publish_event_internal(request: PublishEventRequest) -> Dict[str, Any]:
    from .event_bus import Event, EventBus

    event_bus = EventBus()
    await event_bus.initialize()
    try:
        event = Event(
            type=request.event_type,
            data=request.data,
            source=request.source or settings.service_name,
        )
        msg_id = await event_bus.publish(request.stream, event)
        return {
            "status": "published",
            "message_id": msg_id,
            "stream": request.stream,
            "event_type": request.event_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        await event_bus.close()


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
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/refresh")
async def refresh_token(current_token: str = Depends(security)):
    """Refresh access token."""
    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@health_router.get("/health")
async def health_check():
    """Health check with service status."""
    try:
        services_health = await mcp_client.health_check_all()
        services_health["conport"] = await conport_client.health_check()
        return {
            "status": "healthy",
            "instance": settings.instance_name,
            "port": settings.port,
            "services": services_health,
        }
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return {
            "status": "degraded",
            "instance": settings.instance_name,
            "error": str(exc),
        }


@health_router.get("/")
async def root():
    """Service information."""
    return {
        "service": "DopeconBridge",
        "version": "2.0.0",
        "instance": settings.instance_name,
        "port": settings.port,
        "architecture": "adapter-only-active-runtime",
        "docs": f"http://localhost:{settings.port}/docs",
    }


@events_router.post("")
async def publish_event(
    request: PublishEventRequest,
    current_user: dict = Depends(get_current_user),
):
    """Publish authenticated event traffic into the shared event stream."""
    del current_user
    try:
        return await _publish_event_internal(request)
    except Exception as exc:
        logger.error("Event publish failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@events_router.get("/stream")
async def subscribe_to_events(
    stream: str = "dopemux:events",
    consumer_group: str = "dashboard",
    current_user: dict = Depends(get_current_user),
):
    """Subscribe to event stream via server-sent events."""
    del current_user
    from .event_bus import EventBus

    event_bus = EventBus()
    await event_bus.initialize()

    async def event_generator():
        consumer = f"sse-{settings.instance_name}"
        async for msg_id, event in event_bus.subscribe(stream, consumer_group, consumer):
            yield f"data: {json.dumps({'id': msg_id, 'event': event.to_dict()})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@events_router.get("/history")
async def get_event_history(
    stream: str = "dopemux:events",
    count: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """Get event history from Redis Stream."""
    del current_user
    try:
        cache_client = await cache_manager.get_client()
        entries = await cache_client.xrevrange(stream, count=count)
        events = []
        for msg_id, data in entries:
            events.append(
                {
                    "id": msg_id,
                    "type": data.get("type", "unknown"),
                    "data": json.loads(data.get("data", "{}")) if data.get("data") else {},
                    "source": data.get("source"),
                    "timestamp": data.get("timestamp"),
                }
            )

        return {
            "stream": stream,
            "count": len(events),
            "events": events,
            "instance": settings.instance_name,
        }
    except Exception as exc:
        logger.error("Event history retrieval failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@events_router.get("/{stream:path}")
async def get_stream_info(stream: str, current_user: dict = Depends(get_current_user)):
    """Return Redis stream info for the requested event stream."""
    del current_user
    try:
        cache_client = await cache_manager.get_client()
        info = await cache_client.xinfo_stream(stream)
        return {
            "stream": stream,
            "info": info,
            "instance": settings.instance_name,
        }
    except Exception as exc:
        logger.error("Stream info retrieval failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@events_router.post("/tasks-imported")
async def publish_tasks_imported(
    task_count: int,
    sprint_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Publish tasks_imported event (authenticated convenience endpoint)."""
    del current_user
    return await _publish_event_internal(
        PublishEventRequest(
            event_type="tasks_imported",
            data={"task_count": task_count, "sprint_id": sprint_id},
        )
    )


@events_router.post("/session-started")
async def publish_session_started(
    task_id: str,
    duration_minutes: int = 25,
    current_user: dict = Depends(get_current_user),
):
    """Publish session_started event (authenticated convenience endpoint)."""
    del current_user
    return await _publish_event_internal(
        PublishEventRequest(
            event_type="session_started",
            data={"task_id": task_id, "duration_minutes": duration_minutes},
        )
    )


@events_router.post("/progress-updated")
async def publish_progress_updated(
    task_id: str,
    status: str,
    progress: float,
    current_user: dict = Depends(get_current_user),
):
    """Publish progress_updated event (authenticated convenience endpoint)."""
    del current_user
    return await _publish_event_internal(
        PublishEventRequest(
            event_type="progress_updated",
            data={"task_id": task_id, "status": status, "progress": progress},
        )
    )


@tasks_router.post("/parse-prd")
async def parse_prd(request: PRDParseRequest, http_request: Request):
    """Fail closed: PRD parsing is blocked until canonical workflow adjudication exists."""
    update_context_delta(
        http_request,
        "blocked_task_route",
        {"operation": "parse_prd", "project_id": request.project_id},
    )
    _reject_policy_blocked(
        "POST /tasks/parse-prd is disabled: bridge-local task creation is non-canonical and the "
        "active Task Orchestrator runtime does not expose the required adjudication surface."
    )


@tasks_router.get("/next/{project_id}")
async def get_next_tasks(project_id: str, limit: int = Query(5, ge=1, le=20)):
    """Fail closed: next-action must resolve through Task Orchestrator."""
    del limit
    _reject_policy_blocked(
        f"GET /tasks/next/{project_id} is disabled: canonical next-action authority belongs to "
        "Task Orchestrator, and the active runtime does not expose a project-scoped next-action API."
    )


@tasks_router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Fail closed: bridge-local task status mutation is non-canonical."""
    del request, current_user
    _reject_policy_blocked(
        f"PATCH /tasks/{task_id}/status is disabled: workflow-significant writes must be adjudicated by "
        "Task Orchestrator before any Leantime reflection."
    )


@pm_router.post("/pm")
async def route_pm(
    request: PMRouteRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Route adapter-safe PM operations to the Leantime backend."""
    del current_user
    correlation_id = _correlation_id(http_request)
    operation = request.operation.strip()
    payload = dict(request.data or {})

    if operation.lower() not in SAFE_PM_ROUTE_OPERATIONS and operation.lower() not in WORKFLOW_SIGNIFICANT_OPERATIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported PM operation: {operation}")

    if _is_workflow_significant_pm_mutation(operation, payload):
        _reject_policy_blocked(
            f"Operation {operation!r} is blocked: workflow-significant mutations require Task Orchestrator "
            "adjudication before any Leantime reflection, and the active runtime lacks that project-scoped surface."
        )

    try:
        tool_name, tool_payload = build_leantime_tool_request(operation, payload)
        update_context_delta(
            http_request,
            "last_pm_route",
            {
                "operation": operation,
                "requester": request.requester,
                "correlation_id": correlation_id,
            },
        )
        result = await mcp_client.call_tool("leantime-bridge", tool_name, tool_payload)
        normalized = normalize_leantime_route_response(operation, result)
        return {
            "success": True,
            "data": normalized,
            "error": None,
            "correlation_id": correlation_id,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("PM routing failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@kg_router.post("/custom_data")
async def save_custom_data(request: CustomDataRequest, current_user: dict = Depends(get_current_user)):
    """Proxy custom-data writes to the active ConPort REST surface."""
    del current_user
    payload = request.model_dump()
    payload["workspace_id"] = _default_workspace_id(payload.get("workspace_id"))
    result = await conport_client.save_custom_data(payload)
    return {
        "success": result.get("status") == "saved",
        "status": result.get("status"),
        "workspace_id": payload["workspace_id"],
        "category": payload["category"],
        "key": payload["key"],
        "source": "conport",
    }


@kg_router.get("/custom_data")
async def get_custom_data(
    workspace_id: Optional[str] = None,
    category: Optional[str] = None,
    key: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """Proxy custom-data reads to ConPort and normalize the response."""
    del current_user
    params: Dict[str, Any] = {"workspace_id": _default_workspace_id(workspace_id), "limit": limit}
    if category:
        params["category"] = category
    if key:
        params["key"] = key
    result = await conport_client.get_custom_data(params)
    return _normalize_custom_data_read(result)


@kg_router.post("/decisions")
async def create_decision(request: DecisionRequest, current_user: dict = Depends(get_current_user)):
    """Proxy decision writes to ConPort."""
    del current_user
    payload = request.model_dump()
    payload["workspace_id"] = _default_workspace_id(payload.get("workspace_id"))
    if not payload.get("summary"):
        implementation_details = payload.get("implementation_details")
        if implementation_details:
            payload["summary"] = implementation_details
        else:
            raise HTTPException(status_code=400, detail="Decision summary is required")
    result = await conport_client.log_decision(payload)
    if result.get("status") == "logged":
        await _publish_event_internal(
            PublishEventRequest(
                stream="dopemux:events",
                event_type="decision.logged",
                data={
                    "workspace_id": payload["workspace_id"],
                    "summary": payload.get("summary"),
                    "rationale": payload.get("rationale"),
                    "decision": result.get("decision", {}),
                    "tags": payload.get("tags", []),
                },
                source="conport",
            )
        )
    return {
        "success": result.get("status") == "logged",
        "status": result.get("status"),
        "decision": result.get("decision"),
        "source": "conport",
    }


@kg_router.get("/decisions")
async def list_decisions(
    workspace_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Proxy decision reads to ConPort."""
    del current_user
    result = await conport_client.list_decisions(
        workspace_id=_default_workspace_id(workspace_id),
        limit=limit,
    )
    return _normalize_decision_list(result)


@kg_router.post("/progress")
async def create_progress(request: ProgressRequest, current_user: dict = Depends(get_current_user)):
    """Proxy progress writes to ConPort."""
    del current_user
    payload = request.model_dump()
    payload["workspace_id"] = _default_workspace_id(payload.get("workspace_id"))
    result = await conport_client.log_progress(payload)
    if result.get("status") == "logged":
        await _publish_event_internal(
            PublishEventRequest(
                stream="dopemux:events",
                event_type="progress.updated",
                data={
                    "workspace_id": payload["workspace_id"],
                    "description": payload.get("description"),
                    "status": payload.get("status"),
                    "progress": payload.get("percentage"),
                    "metadata": payload.get("metadata", {}),
                },
                source="conport",
            )
        )
    return {
        "success": result.get("status") == "logged",
        "status": result.get("status"),
        "progress": result.get("progress"),
        "source": "conport",
    }


@kg_router.get("/progress")
async def list_progress(
    workspace_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Proxy progress reads to ConPort and normalize the response."""
    del current_user
    result = await conport_client.list_progress(
        workspace_id=_default_workspace_id(workspace_id),
        limit=limit,
        status=status,
    )
    return _normalize_progress_list(result)


@ddg_router.get("/decisions")
async def ddg_recent_decisions(
    workspace_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Expose recent decisions through a ConPort-backed compatibility surface."""
    del current_user
    result = await conport_client.list_decisions(
        workspace_id=_default_workspace_id(workspace_id),
        limit=limit,
    )
    return _normalize_decision_list(result)


@ddg_router.get("/search")
async def ddg_search_decisions(
    q: str,
    workspace_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Expose decision search through a ConPort-backed compatibility surface."""
    del current_user
    result = await conport_client.search_decisions(
        query=q,
        workspace_id=_default_workspace_id(workspace_id),
        limit=limit,
    )
    return _normalize_search_results(result, q)


def get_all_routers() -> List[APIRouter]:
    """Return all API routers for inclusion in the app."""
    return [
        health_router,
        auth_router,
        events_router,
        tasks_router,
        pm_router,
        kg_router,
        ddg_router,
    ]
