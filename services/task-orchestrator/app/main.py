"""
Coordination API Service - REST API for Two-Plane Coordination

Provides RESTful endpoints for cross-plane operations and event handling:

- POST /api/coordination/operations - Execute coordination operations
- GET /api/coordination/health - Plane health status
- GET /api/coordination/metrics - Coordination analytics
- POST /api/coordination/events - Emit coordination events
- GET /api/coordination/conflicts - Active conflicts
- POST /api/coordination/conflicts/{id}/resolve - Resolve conflicts

Features:
- Async FastAPI endpoints with proper error handling
- ADHD-aware request processing (cognitive load consideration)
- Event-driven coordination with WebSocket support
- Real-time health monitoring and alerting
- Conflict resolution workflows
- Comprehensive logging and telemetry

Created: 2025-11-05
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import json

from app.core.coordinator import (
    PlaneType,
    CoordinationEventType,
    ConflictResolutionStrategy,
    create_plane_coordinator
)

logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for API
# ============================================================================


class CoordinationOperationRequest(BaseModel):
    """Request model for coordination operations."""
    operation: str = Field(..., description="Operation name (create_task, update_progress, etc.)")
    source_plane: str = Field(..., description="Source plane (pm, cognitive, integration)")
    data: Dict[str, Any] = Field(..., description="Operation-specific data")
    priority: Optional[int] = Field(5, ge=1, le=10, description="Operation priority (1-10)")

    @validator('source_plane')
    def validate_source_plane(cls, v):
        valid_planes = [p.value for p in PlaneType]
        if v not in valid_planes:
            raise ValueError(f"source_plane must be one of: {valid_planes}")
        return v


class CoordinationOperationResponse(BaseModel):
    """Response model for coordination operations."""
    success: bool
    operation_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlaneHealthResponse(BaseModel):
    """Response model for plane health status."""
    plane: str
    status: str
    last_check: datetime
    services: Dict[str, str]
    issues: List[str]
    metrics: Dict[str, Any] = Field(default_factory=dict)


class CoordinationMetricsResponse(BaseModel):
    """Response model for coordination metrics."""
    metrics: Dict[str, int]
    plane_health: Dict[str, Dict[str, Any]]
    active_conflicts: int
    timestamp: datetime


class EmitEventRequest(BaseModel):
    """Request model for emitting coordination events."""
    event_type: str = Field(..., description="Event type (task_created, decision_made, etc.)")
    source_plane: str = Field(..., description="Source plane")
    target_plane: str = Field(..., description="Target plane")
    entity_type: str = Field(..., description="Entity type (task, decision, etc.)")
    entity_id: str = Field(..., description="Entity ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    priority: Optional[int] = Field(5, description="Event priority")

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = [e.value for e in CoordinationEventType]
        if v not in valid_types:
            raise ValueError(f"event_type must be one of: {valid_types}")
        return v

    @validator('source_plane', 'target_plane')
    def validate_planes(cls, v):
        valid_planes = [p.value for p in PlaneType]
        if v not in valid_planes:
            raise ValueError(f"plane must be one of: {valid_planes}")
        return v


class ConflictResolutionRequest(BaseModel):
    """Request model for conflict resolution."""
    resolution_strategy: str = Field(..., description="Resolution strategy")
    resolved_value: Optional[Any] = Field(None, description="Manually specified resolved value")

    @validator('resolution_strategy')
    def validate_strategy(cls, v):
        valid_strategies = [s.value for s in ConflictResolutionStrategy]
        if v not in valid_strategies:
            raise ValueError(f"resolution_strategy must be one of: {valid_strategies}")
        return v


# ============================================================================
# FastAPI Application
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Coordination API Service...")
    workspace_id = os.environ.get("WORKSPACE_ID", "/app")
    app.state.coordinator = await create_plane_coordinator(workspace_id)
    logger.info("✅ Coordination API Service ready")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Coordination API Service...")
    await app.state.coordinator.shutdown()
    logger.info("✅ Coordination API Service shutdown complete")

app = FastAPI(
    title="Dopemux Plane Coordination API",
    description="REST API for two-plane architecture coordination",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8097"],  # ADHD Dashboard, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# WebSocket Connection Manager
# ============================================================================


class ConnectionManager:
    """WebSocket connection manager for real-time coordination events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = client_info or {}
        logger.info(f"🔗 WebSocket client connected: {len(self.active_connections)} total")

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            del self.connection_metadata[websocket]
            logger.info(f"🔌 WebSocket client disconnected: {len(self.active_connections)} remaining")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)


# Global connection manager
manager = ConnectionManager()

# ============================================================================
# Event Handler Integration
# ============================================================================


async def handle_coordination_events(event):
    """Handle coordination events by broadcasting to WebSocket clients."""
    try:
        event_data = {
            "type": "coordination_event",
            "event_type": event.event_type.value,
            "source_plane": event.source_plane.value,
            "target_plane": event.target_plane.value,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "correlation_id": event.correlation_id,
            "priority": event.priority
        }

        await manager.broadcast(event_data)
        logger.debug(f"📡 Broadcasted event: {event.event_type.value}")

    except Exception as e:
        logger.error(f"Failed to handle coordination event: {e}")

# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "task-orchestrator-coordination-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    coordinator = app.state.coordinator

    # Get orchestration metrics
    orchestration_stats = getattr(coordinator, 'metrics', {})

    # Format as Prometheus metrics
    metrics_output = f"""# HELP task_orchestrator_tasks_orchestrated_total Total number of tasks orchestrated
# TYPE task_orchestrator_tasks_orchestrated_total counter
task_orchestrator_tasks_orchestrated_total {orchestration_stats.get('tasks_orchestrated', 0)}

# HELP task_orchestrator_sync_events_processed_total Total number of sync events processed
# TYPE task_orchestrator_sync_events_processed_total counter
task_orchestrator_sync_events_processed_total {orchestration_stats.get('sync_events_processed', 0)}

# HELP task_orchestrator_ai_agent_dispatches_total Total number of AI agent dispatches
# TYPE task_orchestrator_ai_agent_dispatches_total counter
task_orchestrator_ai_agent_dispatches_total {orchestration_stats.get('ai_agent_dispatches', 0)}

# HELP task_orchestrator_active_workers Number of active background workers
# TYPE task_orchestrator_active_workers gauge
task_orchestrator_active_workers {len(getattr(coordinator, 'workers', []))}

# HELP task_orchestrator_health_status Service health status (1=healthy, 0=unhealthy)
# TYPE task_orchestrator_health_status gauge
task_orchestrator_health_status 1
"""

    return Response(content=metrics_output, media_type="text/plain; version=0.0.4; charset=utf-8")


@app.post("/api/coordination/operations", response_model=CoordinationOperationResponse)
async def coordinate_operation(request: CoordinationOperationRequest):
    """
    Execute a coordination operation across planes.

    This endpoint provides the unified coordination API for cross-plane operations.
    """
    try:
        coordinator = app.state.coordinator

        # Convert string plane to enum
        source_plane = PlaneType(request.source_plane)

        # Execute coordination operation
        result = await coordinator.coordinate_operation(
            request.operation,
            source_plane,
            request.data,
            priority=request.priority
        )

        return CoordinationOperationResponse(
            success=result.get("success", False),
            operation_id=result.get("sync_operation_id"),
            result=result,
            timestamp=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Coordination operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/coordination/health", response_model=List[PlaneHealthResponse])
async def get_plane_health():
    """Get health status of all planes."""
    try:
        coordinator = app.state.coordinator

        health_responses = []
        for plane, health in coordinator.plane_health.items():
            health_responses.append(PlaneHealthResponse(
                plane=plane.value,
                status=health.status,
                last_check=health.last_check,
                services=health.services,
                issues=health.issues,
                metrics=health.metrics
            ))

        return health_responses

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/coordination/metrics", response_model=CoordinationMetricsResponse)
async def get_coordination_metrics():
    """Get coordination performance metrics."""
    try:
        coordinator = app.state.coordinator
        metrics = coordinator.get_coordination_metrics()

        return CoordinationMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/coordination/events")
async def emit_coordination_event(request: EmitEventRequest, background_tasks: BackgroundTasks):
    """
    Emit a coordination event for processing.

    This endpoint allows external systems to trigger coordination events.
    """
    try:
        coordinator = app.state.coordinator

        # Convert strings to enums
        event_type = CoordinationEventType(request.event_type)
        source_plane = PlaneType(request.source_plane)
        target_plane = PlaneType(request.target_plane)

        # Emit event
        await coordinator.emit_coordination_event(
            event_type,
            source_plane,
            target_plane,
            request.entity_type,
            request.entity_id,
            request.data,
            priority=request.priority
        )

        # Handle event broadcasting in background
        background_tasks.add_task(handle_coordination_events, {
            "event_type": event_type,
            "source_plane": source_plane,
            "target_plane": target_plane,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "data": request.data,
            "timestamp": datetime.now(timezone.utc),
            "correlation_id": f"api_{request.entity_id}_{int(datetime.now().timestamp())}",
            "priority": request.priority
        })

        return {"success": True, "message": "Event emitted successfully"}

    except Exception as e:
        logger.error(f"Event emission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/coordination/conflicts")
async def get_active_conflicts():
    """Get list of active coordination conflicts."""
    try:
        coordinator = app.state.coordinator

        conflicts = []
        for conflict_id, conflict in coordinator.active_conflicts.items():
            conflicts.append({
                "id": conflict.id,
                "entity_type": conflict.entity_type,
                "entity_id": conflict.entity_id,
                "field_name": conflict.field_name,
                "pm_value": conflict.pm_value,
                "cognitive_value": conflict.cognitive_value,
                "resolution_strategy": conflict.resolution_strategy.value,
                "detected_at": conflict.detected_at.isoformat(),
                "resolved": conflict.resolved_value is not None,
                "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None,
                "resolution_reason": conflict.resolution_reason
            })

        return {"conflicts": conflicts, "count": len(conflicts)}

    except Exception as e:
        logger.error(f"Conflict retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/coordination/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, request: ConflictResolutionRequest):
    """Resolve a specific coordination conflict."""
    try:
        coordinator = app.state.coordinator

        if conflict_id not in coordinator.active_conflicts:
            raise HTTPException(status_code=404, detail=f"Conflict {conflict_id} not found")

        conflict = coordinator.active_conflicts[conflict_id]

        # Update conflict with resolution request
        conflict.resolution_strategy = ConflictResolutionStrategy(request.resolution_strategy)
        if request.resolved_value is not None:
            conflict.resolved_value = request.resolved_value

        # Resolve conflict
        resolved_value = await coordinator.resolve_conflict(conflict)

        if resolved_value is not None:
            return {
                "success": True,
                "conflict_id": conflict_id,
                "resolved_value": resolved_value,
                "resolution_reason": conflict.resolution_reason
            }
        else:
            raise HTTPException(status_code=400, detail="Conflict resolution failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conflict resolution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/coordination")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time coordination event streaming.

    Clients can subscribe to coordination events in real-time.
    """
    client_info = {"client_id": client_id, "connected_at": datetime.now(timezone.utc)}

    await manager.connect(websocket, client_info)

    try:
        # Register event handler for this connection
        async def ws_event_handler(event):
            """Handle events for this WebSocket client."""
            await handle_coordination_events(event)

        coordinator = app.state.coordinator
        coordinator.register_event_handler(
            CoordinationEventType.TASK_CREATED,  # Register for key events
            ws_event_handler
        )
        coordinator.register_event_handler(
            CoordinationEventType.TASK_UPDATED,
            ws_event_handler
        )
        coordinator.register_event_handler(
            CoordinationEventType.DECISION_MADE,
            ws_event_handler
        )
        coordinator.register_event_handler(
            CoordinationEventType.BREAK_RECOMMENDED,
            ws_event_handler
        )

        # Keep connection alive and handle client messages
        while True:
            try:
                # Receive message from client (optional)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client messages if needed
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON message"})
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_json({"error": str(e)})

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)

# ============================================================================
# Utility Endpoints
# ============================================================================


@app.get("/api/coordination/status")
async def get_coordination_status():
    """Get overall coordination system status."""
    try:
        coordinator = app.state.coordinator

        status = {
            "coordinator_running": True,
            "event_processor_active": coordinator.processing_task is not None,
            "sync_engine_running": coordinator.sync_engine.running,
            "websocket_clients": len(manager.active_connections),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return status

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "coordinator_running": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.post("/api/coordination/test")
async def test_coordination():
    """Test endpoint to verify coordination functionality."""
    try:
        coordinator = app.state.coordinator

        # Test task creation coordination
        test_task = {
            "id": f"test_task_{int(datetime.now().timestamp())}",
            "title": "Coordination Test Task",
            "description": "Testing cross-plane coordination",
            "complexity_score": 0.3,
            "energy_required": "low"
        }

        result = await coordinator.coordinate_operation(
            "create_task",
            PlaneType.COGNITIVE,
            {"task": test_task}
        )

        return {
            "success": True,
            "test_result": result,
            "message": "Coordination test completed successfully"
        }

    except Exception as e:
        logger.error(f"Coordination test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Coordination test failed"
        }

# ============================================================================
# Main Application Runner
# ============================================================================

if __name__ == "__main__":
    # Register event handlers with coordinator after startup
    @app.on_event("startup")
    async def setup_event_handlers():
        """Setup event handlers after application startup."""
        coordinator = app.state.coordinator

        # Register handlers for all event types to enable WebSocket broadcasting
        for event_type in CoordinationEventType:
            coordinator.register_event_handler(event_type, handle_coordination_events)

        logger.info("📡 Event handlers registered for WebSocket broadcasting")

    # Run the FastAPI application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
        log_level="info"
    )
