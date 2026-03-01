"""
Task-Orchestrator - Slim Application Entrypoint (FastAPI)

This is the new modular HTTP entrypoint replacing the monolithic script.
It provides a REST API compatible with DopeconBridge's MCP client.

- GET /health: Service health
- POST /api/tools/{tool_name}: Execute MCP tool
- POST /api/decompose: Task decomposition endpoint (ADHD Engine integration)
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from task_orchestrator.adhd import adhd_monitor
from task_orchestrator.agents import agent_coordinator
from task_orchestrator.config import settings
from task_orchestrator.core import leantime_client, redis_manager
from task_orchestrator.mcp import handle_tool_call, MCP_TOOLS
from fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("Task-Orchestrator")

# Register tools from MCP_TOOLS to FastMCP
for tool_def in MCP_TOOLS:
    name = tool_def["name"]
    desc = tool_def["description"]
    
    if name == "analyze_dependencies":
        @mcp.tool(name=name, description=desc)
        async def analyze_dependencies(tasks: list) -> dict:
            return await handle_tool_call("analyze_dependencies", {"tasks": tasks})
    elif name == "batch_tasks":
        @mcp.tool(name=name, description=desc)
        async def batch_tasks(task_ids: list, session_minutes: int = 25) -> dict:
            return await handle_tool_call("batch_tasks", {"task_ids": task_ids, "session_minutes": session_minutes})
    elif name == "get_adhd_state":
        @mcp.tool(name=name, description=desc)
        async def get_adhd_state() -> dict:
            return await handle_tool_call("get_adhd_state", {})
    elif name == "get_task_recommendations":
        @mcp.tool(name=name, description=desc)
        async def get_task_recommendations(limit: int = 5, energy_level: str = "medium") -> dict:
            return await handle_tool_call("get_task_recommendations", {"limit": limit, "energy_level": energy_level})
    elif name == "record_break":
        @mcp.tool(name=name, description=desc)
        async def record_break() -> dict:
            return await handle_tool_call("record_break", {})
    elif name == "get_agent_status":
        @mcp.tool(name=name, description=desc)
        async def get_agent_status() -> dict:
            return await handle_tool_call("get_agent_status", {})

# Import decomposition endpoint
from task_decomposition_endpoint import (
    DecompositionRequest,
    DecompositionResponse,
    handle_decomposition_request
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Task-Orchestrator v2.0 - HTTP Mode")
    logger.info("=" * 60)
    logger.info(f"📊 Instance: {settings.instance_name}")
    logger.info(f"🔌 Port: {settings.port}")
    logger.info("=" * 60)
    
    try:
        # Initialize connections
        await leantime_client.initialize()
        await redis_manager.initialize()
        
        # Initialize components
        agent_coordinator.initialize_pool()
        await adhd_monitor.start_monitoring()
        
        logger.info("✅ Task-Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Task-Orchestrator...")
    await adhd_monitor.stop_monitoring()
    await leantime_client.close()
    await redis_manager.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Task-Orchestrator",
    version="2.0.0",
    description="Intelligent PM automation middleware",
    lifespan=lifespan
)

# Mount FastMCP HTTP app
app.mount("/mcp", mcp.http_app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "instance": settings.instance_name
    }


@app.get("/api/tools")
async def list_tools():
    """List available MCP tools."""
    return {"tools": MCP_TOOLS}


@app.post("/api/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """Execute an MCP tool."""
    try:
        arguments = await request.json()
        logger.info(f"🔧 Executing tool: {tool_name}")
        
        result = await handle_tool_call(tool_name, arguments)
        
        if "error" in result:
            logger.warning(f"❌ Tool execution failed: {result['error']}")
            # We return 200 even on logical error to match MCP protocol behavior style,
            # but usually REST implies 4xx/5xx. DopeconBridge expects 200 with result
            # or it raises HTTP exception. 
            # If result has "error", DopeconBridge might treat it as result.
            return result
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/decompose", response_model=DecompositionResponse)
async def decompose_task(request: DecompositionRequest):
    """
    Decompose a complex task into ADHD-friendly micro-tasks.
    
    Called by ADHD Engine when automatic decomposition is triggered.
    
    Flow:
    1. Get task from internal storage
    2. Call Pal planner for AI decomposition
    3. Convert to OrchestrationTask objects
    4. Persist to ConPort (parent BLOCKED, subtasks TODO, DECOMPOSED_INTO links)
    5. Sync to Leantime (create child tickets for team visibility)
    6. Return structured breakdown
    """
    try:
        logger.info(f"📋 Decomposition request for task {request.task_id}")
        
        # Get singleton instances
        from task_orchestrator.core import (
            get_task_coordinator,
            get_pal_client,
            get_conport_adapter
        )
        
        task_coordinator = get_task_coordinator()
        pal_client = get_pal_client()
        conport_adapter = get_conport_adapter()
        
        # Execute decomposition
        response = await handle_decomposition_request(
            request=request,
            task_coordinator=task_coordinator,
            pal_client=pal_client,
            leantime_client=leantime_client,
            conport_adapter=conport_adapter,
            workspace_id=settings.workspace_id
        )
        
        logger.info(
            f"✅ Decomposition complete: {len(response.subtask_ids)} subtasks, "
            f"{response.total_estimated_minutes}min total"
        )
        
        return response
    
    except ValueError as e:
        logger.error(f"❌ Decomposition validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Decomposition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower()
    )
