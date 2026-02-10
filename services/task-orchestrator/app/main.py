"""
Coordination API Service - REST API for Two-Plane Coordination

Provides RESTful endpoints for cross-plane operations and event handling.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dopemux.workspace_detection import get_workspace_root
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
import json

# Add repo root to path
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(repo_root, "src"))

try:
    from dopemux.logging import configure_logging, RequestIDMiddleware
except Exception:
    RequestIDMiddleware = None
    def configure_logging(service_name, *, level=None, **_):
        resolved_level = getattr(logging, str(level or "INFO").upper(), logging.INFO)
        logging.basicConfig(
            level=resolved_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        return logging.getLogger(service_name)
from .core.coordinator import create_plane_coordinator

# Configure structured logging
configure_logging("task-orchestrator")
logger = logging.getLogger(__name__)

# Import shared models from local models
from .models.coordination import (
    PlaneType,
    CoordinationEventType,
    ConflictResolutionStrategy,
    CoordinationOperationRequest,
    CoordinationOperationResponse,
    PlaneHealthResponse,
    CoordinationMetricsResponse,
    EmitEventRequest,
    ConflictResolutionRequest,
    HealthResponse
)

logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI Application
# ============================================================================

async def init_coordinator():
    """Initialize plane coordinator"""
    logger.info("Initializing plane coordinator...")
    coordinator = await create_plane_coordinator(get_workspace_root())
    logger.info("Plane coordinator initialized")
    return {"coordinator": coordinator}


async def shutdown_coordinator():
    """Shutdown plane coordinator"""
    # Coordinator shutdown handled by lifespan_context
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    async with lifespan_context("task-orchestrator", init_coordinator, shutdown_coordinator) as state:
        app.state.coordinator = state.get("coordinator")
        yield


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

# Request ID middleware
app.add_middleware(RequestIDMiddleware)

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
    """Standard health check endpoint with dependency tracking"""
    from .core.health_utils import check_dependency, check_redis, determine_overall_status
    
    dependencies = {}
    
    try:
        coordinator = app.state.coordinator
        
        # Check Redis if available
        if hasattr(coordinator, 'redis_client') and coordinator.redis_client:
            redis_status = await check_dependency(
                "redis",
                lambda: check_redis(coordinator.redis_client),
                timeout_ms=200,
                critical=False
            )
            dependencies["redis"] = redis_status
        
        # Determine overall status (no critical deps)
        overall_status = determine_overall_status(dependencies, critical_deps=set())
        
        return HealthResponse(
            service="task-orchestrator",
            status=overall_status,
            ts=datetime.utcnow().isoformat() + "Z",
            dependencies={k: v.status for k, v in dependencies.items()}
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            service="task-orchestrator",
            status="fail",
            ts=datetime.utcnow().isoformat() + "Z",
            dependencies={}
        )


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

    # Log startup configuration
    port = int(os.getenv("PORT", 3014))
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    logger.info("=" * 60)
    logger.info("🚀 Task Orchestrator - Starting")
    logger.info("=" * 60)
    logger.info(f"  Service: task-orchestrator")
    logger.info(f"  Port: {port}")
    logger.info(f"  Redis: {redis_url}")
    logger.info(f"  Workspace: {os.getenv('DOPEMUX_WORKSPACE_ROOT', get_workspace_root())}")
    logger.info("=" * 60)

    # Run the FastAPI application
    uvicorn.run(
        "coordination_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
