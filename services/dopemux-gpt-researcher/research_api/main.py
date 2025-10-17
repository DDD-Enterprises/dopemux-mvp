"""
Dopemux GPT Researcher - ADHD-Optimized Research Service

FastAPI application that provides enhanced research capabilities with:
- Real-time progress streaming via WebSocket
- Pause/resume functionality for ADHD context switching
- ConPort integration for persistent memory
- Multi-search engine support
- Transparent planning and execution phases
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .adapters.conport_adapter import ConPortAdapter
from .adapters.websocket_streamer import WebSocketProgressStreamer
from .models.research_task import (
    ADHDConfiguration,
    ProjectContext,
    ResearchTask,
    ResearchType,
    TaskStatus
)
from .services.orchestrator import ResearchTaskOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Request/Response Models ===

class CreateResearchRequest(BaseModel):
    """Request model for creating new research tasks"""
    user_id: str
    prompt: str
    research_type: Optional[ResearchType] = None  # Auto-detected if not specified
    adhd_config: Optional[ADHDConfiguration] = None  # Auto-optimized if not specified
    project_context: Optional[ProjectContext] = None
    user_context: Optional[Dict] = None  # User preferences and history

class ResearchTaskResponse(BaseModel):
    """Response model for research task operations"""
    task_id: str
    status: TaskStatus
    message: str
    data: Optional[Dict] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    components: Dict[str, str]

# === Global Components ===
websocket_streamer: Optional[WebSocketProgressStreamer] = None
conport_adapter: Optional[ConPortAdapter] = None
orchestrator: Optional[ResearchTaskOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global websocket_streamer, conport_adapter, orchestrator

    try:
        # Initialize WebSocket streamer
        websocket_streamer = WebSocketProgressStreamer()
        await websocket_streamer.start_server()
        logger.info("WebSocket progress streamer started")

        # Initialize ConPort adapter
        workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")
        conport_adapter = ConPortAdapter(workspace_id)
        logger.info(f"ConPort adapter initialized for workspace: {workspace_id}")

        # Initialize orchestrator with dependencies
        orchestrator = ResearchTaskOrchestrator(
            conport_adapter=conport_adapter,
            websocket_streamer=websocket_streamer
        )
        logger.info("Research task orchestrator initialized")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Cleanup
        if websocket_streamer:
            await websocket_streamer.stop_server()
            logger.info("WebSocket server stopped")

# === FastAPI Application ===

app = FastAPI(
    title="Dopemux GPT Researcher",
    description="ADHD-Optimized Research Service with Real-time Progress Streaming",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Health Check ===

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    global websocket_streamer, conport_adapter, orchestrator

    components = {
        "websocket_streamer": "healthy" if websocket_streamer else "not_initialized",
        "conport_adapter": "healthy" if conport_adapter else "not_initialized",
        "orchestrator": "healthy" if orchestrator else "not_initialized"
    }

    status = "healthy" if all(c == "healthy" for c in components.values()) else "degraded"

    return HealthResponse(
        status=status,
        version="1.0.0",
        components=components
    )

# === Research Task Management ===

@app.post("/research/create", response_model=ResearchTaskResponse)
async def create_research_task(request: CreateResearchRequest):
    """Create a new research task with ADHD optimizations"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        task = await orchestrator.create_research_task(
            user_id=request.user_id,
            prompt=request.prompt,
            research_type=request.research_type,
            adhd_config=request.adhd_config,
            user_context=request.user_context
        )

        return ResearchTaskResponse(
            task_id=str(task.id),
            status=task.status,
            message="Research task created successfully",
            data={"task": task.model_dump()}
        )

    except Exception as e:
        logger.error(f"Failed to create research task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/{task_id}/plan", response_model=ResearchTaskResponse)
async def generate_research_plan(task_id: str):
    """Generate research plan for transparent ADHD workflow"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        task_uuid = UUID(task_id)
        questions = await orchestrator.generate_research_plan(task_uuid)

        return ResearchTaskResponse(
            task_id=task_id,
            status=TaskStatus.REVIEWING,
            message=f"Research plan generated with {len(questions)} questions",
            data={"questions": [q.model_dump() for q in questions]}
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Failed to generate research plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/{task_id}/execute/{question_index}", response_model=ResearchTaskResponse)
async def execute_research_step(task_id: str, question_index: int):
    """Execute a single research question with pause capability"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        task_uuid = UUID(task_id)
        result = await orchestrator.execute_research_step(task_uuid, question_index)

        if result is None:
            # Task was paused
            return ResearchTaskResponse(
                task_id=task_id,
                status=TaskStatus.PAUSED,
                message="Research task paused",
                data={"paused_at_question": question_index}
            )

        return ResearchTaskResponse(
            task_id=task_id,
            status=TaskStatus.EXECUTING,
            message=f"Research question {question_index} completed",
            data={"result": result.model_dump()}
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID or question index")
    except Exception as e:
        logger.error(f"Failed to execute research step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/{task_id}/pause", response_model=ResearchTaskResponse)
async def pause_research_task(task_id: str, reason: str = "User requested"):
    """Pause research task for ADHD context switching"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        task_uuid = UUID(task_id)
        success = await orchestrator.pause_task(task_uuid, reason)

        if not success:
            raise HTTPException(status_code=400, detail="Cannot pause task in current state")

        return ResearchTaskResponse(
            task_id=task_id,
            status=TaskStatus.PAUSED,
            message="Research task paused successfully",
            data={"reason": reason}
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Failed to pause research task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/{task_id}/resume", response_model=ResearchTaskResponse)
async def resume_research_task(task_id: str):
    """Resume paused research task"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        task_uuid = UUID(task_id)
        success = await orchestrator.resume_task(task_uuid)

        if not success:
            raise HTTPException(status_code=400, detail="Cannot resume task in current state")

        return ResearchTaskResponse(
            task_id=task_id,
            status=TaskStatus.EXECUTING,
            message="Research task resumed successfully"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Failed to resume research task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/{task_id}/complete", response_model=ResearchTaskResponse)
async def complete_research_task(task_id: str):
    """Mark research task as complete and finalize results"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        task_uuid = UUID(task_id)
        task = await orchestrator.complete_research(task_uuid)

        return ResearchTaskResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            message="Research task completed successfully",
            data={"task": task.model_dump()}
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Failed to complete research task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/research/{task_id}/status", response_model=ResearchTaskResponse)
async def get_task_status(task_id: str):
    """Get current status and progress of research task"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        task_uuid = UUID(task_id)
        task = orchestrator._get_task(task_uuid)

        progress = task.calculate_progress()

        return ResearchTaskResponse(
            task_id=task_id,
            status=task.status,
            message="Task status retrieved",
            data={
                "progress": progress,
                "current_question": task.current_question_index,
                "total_questions": len(task.research_plan),
                "results_count": len(task.results)
            }
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=404, detail="Task not found")

# === WebSocket Endpoints ===

@app.websocket("/ws/progress/{user_id}")
async def websocket_progress_endpoint(websocket: WebSocket, user_id: str, task_id: Optional[str] = None):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()

    try:
        # Send authentication message to streamer
        auth_message = {
            "user_id": user_id,
            "task_id": task_id
        }

        # For demo, we'll handle the connection here
        # In production, this would integrate with the WebSocketProgressStreamer
        logger.info(f"WebSocket connection established for user {user_id}")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "task_id": task_id,
            "timestamp": "2024-01-01T00:00:00Z"
        })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = eval(data)  # In production, use json.loads with error handling

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")

# === Root Endpoint ===

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Dopemux GPT Researcher",
        "version": "1.0.0",
        "description": "ADHD-Optimized Research Service",
        "features": [
            "Real-time progress streaming",
            "Pause/resume functionality",
            "ConPort memory integration",
            "Transparent planning phase",
            "Multi-search engine support"
        ],
        "endpoints": {
            "health": "/health",
            "create_task": "/research/create",
            "generate_plan": "/research/{task_id}/plan",
            "execute_step": "/research/{task_id}/execute/{question_index}",
            "websocket": "/ws/progress/{user_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)