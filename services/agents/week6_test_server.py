"""
Week 6: Standalone Two-Plane Routing Test Server

Minimal server for testing /route/pm and /route/cognitive endpoints
without DopeconBridge dependencies.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

# ============================================================================
# Models
# ============================================================================

class CrossPlaneRouteRequest(BaseModel):
    """Request to route operation from one plane to another"""
    source: str = Field(..., description="Source plane: 'pm' or 'cognitive'")
    operation: str = Field(..., description="Operation name (e.g., 'get_tasks')")
    data: Dict[str, Any] = Field(default_factory=dict, description="Operation data")
    requester: str = Field(default="unknown", description="Requesting agent/service")

class CrossPlaneRouteResponse(BaseModel):
    """Response from cross-plane routing"""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    correlation_id: Optional[str] = None

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Two-Plane Routing Test Server",
    description="Week 6 test server for TwoPlaneOrchestrator endpoints",
    version="1.0.0"
)

# ============================================================================
# Route Handlers
# ============================================================================

async def _route_to_pm(request: CrossPlaneRouteRequest) -> CrossPlaneRouteResponse:
    """Route request to PM plane (mock responses for testing)"""
    correlation_id = str(uuid.uuid4())
    is_query = request.operation.startswith("get_") or request.operation.startswith("query_")

    try:
        if is_query:
            if request.operation == "get_tasks":
                return CrossPlaneRouteResponse(
                    success=True,
                    data={
                        "tasks": [
                            {"id": "1", "title": "Implement auth", "status": "TODO"},
                            {"id": "2", "title": "Add tests", "status": "IN_PROGRESS"}
                        ],
                        "source": "pm_plane"
                    },
                    correlation_id=correlation_id
                )
            else:
                return CrossPlaneRouteResponse(
                    success=True,
                    data={"message": f"Query {request.operation} processed"},
                    correlation_id=correlation_id
                )

        # Commands return acknowledgment
        return CrossPlaneRouteResponse(
            success=True,
            data={"message": f"Command {request.operation} queued"},
            correlation_id=correlation_id
        )

    except Exception as e:
        return CrossPlaneRouteResponse(
            success=False,
            error=str(e),
            correlation_id=correlation_id
        )

        logger.error(f"Error: {e}")
async def _route_to_cognitive(request: CrossPlaneRouteRequest) -> CrossPlaneRouteResponse:
    """Route request to Cognitive plane (mock responses for testing)"""
    correlation_id = str(uuid.uuid4())
    is_query = request.operation.startswith("get_") or request.operation.startswith("query_")

    try:
        if is_query:
            if request.operation == "get_complexity":
                return CrossPlaneRouteResponse(
                    success=True,
                    data={
                        "complexity": 0.6,
                        "file": request.data.get("file", "unknown"),
                        "function": request.data.get("function", "unknown"),
                        "source": "cognitive_plane"
                    },
                    correlation_id=correlation_id
                )
            elif request.operation == "get_adhd_state":
                return CrossPlaneRouteResponse(
                    success=True,
                    data={
                        "energy": "medium",
                        "attention": "focused",
                        "cognitive_load": 0.5,
                        "source": "adhd_engine"
                    },
                    correlation_id=correlation_id
                )
            else:
                return CrossPlaneRouteResponse(
                    success=True,
                    data={"message": f"Query {request.operation} processed"},
                    correlation_id=correlation_id
                )

        # Commands return acknowledgment
        return CrossPlaneRouteResponse(
            success=True,
            data={"message": f"Command {request.operation} queued"},
            correlation_id=correlation_id
        )

    except Exception as e:
        return CrossPlaneRouteResponse(
            success=False,
            error=str(e),
            correlation_id=correlation_id
        )

        logger.error(f"Error: {e}")
# ============================================================================
# Endpoints
# ============================================================================

@app.post("/route/pm", response_model=CrossPlaneRouteResponse)
async def route_to_pm_plane(request: CrossPlaneRouteRequest):
    """
    Route request to PM plane (Project Management).

    Examples:
    - Get tasks: {"source": "cognitive", "operation": "get_tasks"}
    - Update task: {"source": "cognitive", "operation": "update_task_status", "data": {"task_id": "123"}}
    """
    return await _route_to_pm(request)

@app.post("/route/cognitive", response_model=CrossPlaneRouteResponse)
async def route_to_cognitive_plane(request: CrossPlaneRouteRequest):
    """
    Route request to Cognitive plane (AI agents).

    Examples:
    - Get complexity: {"source": "pm", "operation": "get_complexity", "data": {"file": "auth.py"}}
    - Get ADHD state: {"source": "pm", "operation": "get_adhd_state"}
    """
    return await _route_to_cognitive(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "week6-test",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Week 6: Two-Plane Routing Test Server")
    print("="*70)
    print("\nEndpoints available:")
    print("  POST /route/pm - Route to PM plane")
    print("  POST /route/cognitive - Route to Cognitive plane")
    print("  GET /health - Health check")
    print("\nServer starting on http://localhost:3017")
    print("="*70 + "\n")

    uvicorn.run(
        "week6_test_server:app",
        host="0.0.0.0",
        port=3017,  # Using 3017 to avoid conflict with DopeconBridge
        reload=False
    )
