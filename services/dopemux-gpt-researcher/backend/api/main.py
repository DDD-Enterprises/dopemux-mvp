#!/usr/bin/env python3
"""
GPT-Researcher FastAPI Application
Phase 2: ADHD-Optimized API with session management and real-time progress
"""

import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add backend to path for imports
import sys
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

# Import from backend modules using absolute imports
from models.research_task import ResearchType, ADHDConfiguration, ProjectContext
from services.orchestrator import ResearchTaskOrchestrator
from services.session_manager import SessionManager
from engines.search.search_orchestrator import SearchStrategy

# ========================
# Configuration
# ========================

API_VERSION = "0.2.0"
API_TITLE = "GPT-Researcher ADHD-Optimized API"
API_DESCRIPTION = """
Phase 2 Implementation: Advanced research API with ADHD accommodations.

Features:
- Session persistence for interruption recovery
- Real-time progress via WebSocket
- Adaptive break management
- Attention state detection
- Visual progress tracking
"""

# ========================
# Request/Response Models
# ========================

class ResearchRequest(BaseModel):
    """Research task request with ADHD configuration"""
    topic: str = Field(..., description="Research topic or query")
    research_type: str = Field(default="exploratory", description="Type: exploratory, technical, comparative, systematic")
    depth: str = Field(default="balanced", description="Depth: shallow, balanced, deep")
    adhd_config: Optional[Dict[str, Any]] = Field(default=None, description="ADHD-specific settings")
    session_id: Optional[str] = Field(default=None, description="Session ID for resuming")
    max_sources: int = Field(default=10, description="Maximum sources to analyze")
    timeout_minutes: int = Field(default=25, description="Pomodoro-aligned timeout")


class ResearchResponse(BaseModel):
    """Research task response"""
    task_id: str
    session_id: str
    status: str
    created_at: datetime
    estimated_time_minutes: int
    adhd_notes: List[str]


class ProgressUpdate(BaseModel):
    """Real-time progress update"""
    task_id: str
    progress: int  # 0-100
    stage: str
    message: str
    attention_level: str  # focused, scattered, hyperfocus
    break_suggested: bool
    timestamp: datetime


class SessionInfo(BaseModel):
    """Session information for persistence"""
    session_id: str
    task_ids: List[str]
    created_at: datetime
    last_activity: datetime
    attention_state: str
    break_history: List[Dict[str, Any]]
    total_focus_minutes: int


# ========================
# Attention Monitoring
# ========================

class AttentionMonitor:
    """Monitor attention states and suggest breaks"""

    def __init__(self):
        self.task_metrics = {}

    def detect_attention_state(self, task_id: str, start_time: datetime) -> str:
        """Detect current attention state"""

        elapsed_minutes = (datetime.utcnow() - start_time).total_seconds() / 60

        if elapsed_minutes < 5:
            return "warming_up"
        elif elapsed_minutes < 20:
            return "focused"
        elif elapsed_minutes < 45:
            return "sustained_focus"
        elif elapsed_minutes < 90:
            return "potential_hyperfocus"
        else:
            return "hyperfocus_alert"

    def should_take_break(self, task_id: str, start_time: datetime) -> bool:
        """Determine if a break is needed"""

        elapsed_minutes = (datetime.utcnow() - start_time).total_seconds() / 60

        # Suggest break every 25 minutes (Pomodoro)
        return elapsed_minutes > 0 and elapsed_minutes % 25 < 1

    def record_break(self, session_id: str):
        """Record a break taken"""

        if session_id not in self.task_metrics:
            self.task_metrics[session_id] = {
                'breaks': [],
                'focus_periods': []
            }

        self.task_metrics[session_id]['breaks'].append({
            'timestamp': datetime.utcnow(),
            'type': 'user_initiated'
        })

    def get_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get attention metrics for a task"""

        return self.task_metrics.get(task_id, {
            'breaks': [],
            'focus_periods': [],
            'attention_score': 0
        })


# ========================
# Application State
# ========================

class AppState:
    """Application state management"""
    def __init__(self):
        self.orchestrator: Optional[ResearchTaskOrchestrator] = None
        self.session_manager: Optional[SessionManager] = None
        self.active_websockets: Dict[str, WebSocket] = {}
        self.active_tasks: Dict[str, Any] = {}
        self.attention_monitor = AttentionMonitor()


app_state = AppState()


# ========================
# Lifecycle Management
# ========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    print("🚀 Starting GPT-Researcher API (Phase 2)")

    # Initialize orchestrator
    api_keys = {
        'exa_api_key': os.getenv('EXA_API_KEY'),
        'tavily_api_key': os.getenv('TAVILY_API_KEY'),
        'perplexity_api_key': os.getenv('PERPLEXITY_API_KEY'),
        'context7_api_key': os.getenv('CONTEXT7_API_KEY'),
    }

    project_context = ProjectContext(
        workspace_path=os.getenv('WORKSPACE_PATH', '/Users/hue/code/dopemux-mvp'),
        tech_stack=['Python', 'TypeScript', 'React'],
        architecture_patterns=['MCP', 'microservices', 'ADHD-optimized']
    )

    app_state.orchestrator = ResearchTaskOrchestrator(
        project_context=project_context,
        search_api_keys=api_keys
    )

    # Initialize session manager
    app_state.session_manager = SessionManager()
    await app_state.session_manager.initialize()

    print("✅ API initialized successfully")
    print(f"📡 Listening on port {os.getenv('API_PORT', 8000)}")

    yield

    # Shutdown
    print("🛑 Shutting down GPT-Researcher API")

    # Close all WebSocket connections
    for ws in app_state.active_websockets.values():
        await ws.close()

    # Save active sessions
    if app_state.session_manager:
        await app_state.session_manager.save_all_sessions()

    print("👋 API shutdown complete")


# ========================
# FastAPI Application
# ========================

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================
# Health & Status Endpoints
# ========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.utcnow(),
        "orchestrator": app_state.orchestrator is not None,
        "session_manager": app_state.session_manager is not None,
        "active_tasks": len(app_state.active_tasks),
        "active_websockets": len(app_state.active_websockets)
    }


@app.get("/api/v1/status")
async def get_status():
    """Get API status and capabilities"""
    return {
        "version": API_VERSION,
        "capabilities": {
            "research_types": ["feature_research", "system_architecture", "bug_investigation", "technology_evaluation", "documentation_research", "competitive_analysis"],
            "search_engines": ["exa", "tavily", "perplexity", "context7"],
            "adhd_features": [
                "session_persistence",
                "break_management",
                "attention_detection",
                "progress_tracking",
                "hyperfocus_alerts"
            ]
        },
        "limits": {
            "max_concurrent_tasks": 5,
            "max_session_duration_minutes": 120,
            "default_break_interval_minutes": 25
        }
    }


# ========================
# Research Endpoints
# ========================

@app.post("/api/v1/research", response_model=ResearchResponse)
async def create_research_task(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """Create a new research task with ADHD optimizations"""

    if not app_state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        # Create or restore session
        session_id = request.session_id or str(uuid4())

        if app_state.session_manager:
            session = await app_state.session_manager.get_or_create_session(session_id)

        # Configure ADHD settings
        adhd_config = ADHDConfiguration(
            break_duration_minutes=request.adhd_config.get('break_interval', 5) if request.adhd_config else 5,
            work_duration_minutes=request.adhd_config.get('focus_duration', 25) if request.adhd_config else 25,
            gentle_notifications=request.adhd_config.get('notification_style', 'gentle') == 'gentle' if request.adhd_config else True,
            visual_progress_enabled=True,
            progressive_disclosure=True,
            pomodoro_enabled=True,
            max_concurrent_sources=5,
            auto_save_interval_seconds=30
        )

        # Create research task
        task = await app_state.orchestrator.create_research_task(
            user_id=session_id,  # Use session_id as user_id
            prompt=request.topic,  # Map topic to prompt
            research_type=request.research_type,
            adhd_config=adhd_config,
            user_context={'depth': request.depth} if request.depth else None
        )

        # Store task info
        app_state.active_tasks[str(task.id)] = {
            'task': task,
            'session_id': session_id,
            'created_at': datetime.utcnow(),
            'status': 'created'
        }

        # Schedule background execution
        background_tasks.add_task(
            execute_research_task,
            str(task.id),
            session_id
        )

        # Calculate estimated time
        estimated_time = 5 if request.depth == "shallow" else 15 if request.depth == "balanced" else 25

        # ADHD-specific notes
        adhd_notes = [
            f"⏰ Estimated time: {estimated_time} minutes",
            f"☕ Break reminder set for {adhd_config.break_duration_minutes} minutes",
            "🎯 Focus mode activated with gentle notifications",
            "💾 Session saved - can resume anytime"
        ]

        return ResearchResponse(
            task_id=str(task.id),
            session_id=session_id,
            status="started",
            created_at=datetime.utcnow(),
            estimated_time_minutes=estimated_time,
            adhd_notes=adhd_notes
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create research task: {str(e)}")


@app.get("/api/v1/research/{task_id}")
async def get_research_status(task_id: str):
    """Get research task status and results"""

    if task_id not in app_state.active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task_info = app_state.active_tasks[task_id]

    if not app_state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Get current status
    status = await app_state.orchestrator.get_task_status(task_id)

    return {
        "task_id": task_id,
        "session_id": task_info['session_id'],
        "status": status.get('status', 'unknown'),
        "progress": status.get('progress', 0),
        "results": status.get('results', []),
        "summary": status.get('summary', ''),
        "key_findings": status.get('key_findings', []),
        "created_at": task_info['created_at'],
        "attention_metrics": app_state.attention_monitor.get_metrics(task_id)
    }


@app.delete("/api/v1/research/{task_id}")
async def cancel_research_task(task_id: str):
    """Cancel a research task"""

    if task_id not in app_state.active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    if app_state.orchestrator:
        await app_state.orchestrator.cancel_task(task_id)

    # Update task status
    app_state.active_tasks[task_id]['status'] = 'cancelled'

    return {"message": "Task cancelled", "task_id": task_id}


# ========================
# Session Management
# ========================

@app.get("/api/v1/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get session information and history"""

    if not app_state.session_manager:
        raise HTTPException(status_code=503, detail="Session manager not initialized")

    session = await app_state.session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfo(
        session_id=session_id,
        task_ids=session.get('task_ids', []),
        created_at=session.get('created_at'),
        last_activity=session.get('last_activity'),
        attention_state=session.get('attention_state', 'unknown'),
        break_history=session.get('break_history', []),
        total_focus_minutes=session.get('total_focus_minutes', 0)
    )


@app.post("/api/v1/sessions/{session_id}/pause")
async def pause_session(session_id: str):
    """Pause a session for break or interruption"""

    if not app_state.session_manager:
        raise HTTPException(status_code=503, detail="Session manager not initialized")

    # Save current state
    await app_state.session_manager.pause_session(session_id)

    # Record break
    app_state.attention_monitor.record_break(session_id)

    return {
        "message": "Session paused",
        "session_id": session_id,
        "tip": "🧘 Take a break! Stretch, hydrate, or take a short walk."
    }


@app.post("/api/v1/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    """Resume a paused session"""

    if not app_state.session_manager:
        raise HTTPException(status_code=503, detail="Session manager not initialized")

    # Restore session state
    session = await app_state.session_manager.resume_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get context reminder
    context = await app_state.session_manager.get_context_reminder(session_id)

    return {
        "message": "Session resumed",
        "session_id": session_id,
        "context_reminder": context,
        "tip": "🎯 Welcome back! Let's continue where you left off."
    }


# ========================
# WebSocket for Real-time Updates
# ========================

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket for real-time progress updates"""

    await websocket.accept()
    app_state.active_websockets[task_id] = websocket

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "Connected to progress tracker"
        })

        # Keep connection alive and send updates
        while True:
            # Check if task exists
            if task_id not in app_state.active_tasks:
                await websocket.send_json({
                    "type": "error",
                    "message": "Task not found"
                })
                break

            # Send progress update
            task_info = app_state.active_tasks[task_id]
            if app_state.orchestrator:
                status = await app_state.orchestrator.get_task_status(task_id)

                # Detect attention state
                attention_state = app_state.attention_monitor.detect_attention_state(
                    task_id,
                    task_info.get('created_at')
                )

                # Check if break needed
                break_needed = app_state.attention_monitor.should_take_break(
                    task_id,
                    task_info.get('created_at')
                )

                update = ProgressUpdate(
                    task_id=task_id,
                    progress=status.get('progress', 0),
                    stage=status.get('current_stage', 'initializing'),
                    message=status.get('message', ''),
                    attention_level=attention_state,
                    break_suggested=break_needed,
                    timestamp=datetime.utcnow()
                )

                await websocket.send_json(update.model_dump())

            # Wait before next update
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        del app_state.active_websockets[task_id]
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()


# ========================
# Helper Functions
# ========================

async def execute_research_task(task_id: str, session_id: str):
    """Execute research task in background"""

    if not app_state.orchestrator:
        return

    try:
        # Update status
        app_state.active_tasks[task_id]['status'] = 'executing'

        # Execute the research
        results = await app_state.orchestrator.execute_task(task_id)

        # Update task with results
        app_state.active_tasks[task_id]['status'] = 'completed'
        app_state.active_tasks[task_id]['results'] = results

        # Save to session
        if app_state.session_manager:
            await app_state.session_manager.save_task_results(
                session_id, task_id, results
            )

        # Send WebSocket notification if connected
        if task_id in app_state.active_websockets:
            ws = app_state.active_websockets[task_id]
            await ws.send_json({
                "type": "completed",
                "task_id": task_id,
                "message": "Research completed successfully",
                "summary": results.get('summary', '')
            })

    except Exception as e:
        app_state.active_tasks[task_id]['status'] = 'failed'
        app_state.active_tasks[task_id]['error'] = str(e)

        # Send error via WebSocket if connected
        if task_id in app_state.active_websockets:
            ws = app_state.active_websockets[task_id]
            await ws.send_json({
                "type": "error",
                "task_id": task_id,
                "message": f"Research failed: {str(e)}"
            })


# ========================
# Main Entry Point
# ========================

if __name__ == "__main__":
    port = int(os.getenv('API_PORT', 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=os.getenv('DEBUG', 'false').lower() == 'true',
        log_level="debug" if os.getenv('DEBUG', 'false').lower() == 'true' else "info"
    )