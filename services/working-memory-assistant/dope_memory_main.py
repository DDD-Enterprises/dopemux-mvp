#!/usr/bin/env python3
"""
Dope-Memory HTTP Server - FastAPI wrapper for MCP tools.

Exposes Dope-Memory MCP tools over HTTP on port 3020.
This is the canonical entry point for the Dope-Memory service.

Per registry.yaml:
- Port: 3020
- Health: /health
- Category: mcp
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add parent dir to path for package imports when run directly
_THIS_DIR = Path(__file__).parent.resolve()
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Use absolute imports now that we've fixed the path
from chronicle.store import ChronicleStore
from promotion.redactor import Redactor
from promotion.promotion import PromotionEngine


# Logging setup
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.getenv("PORT", os.getenv("DOPE_MEMORY_PORT", "3020")))
DATA_DIR = Path(os.getenv("DOPE_MEMORY_DATA_DIR", str(Path.home() / ".dope-memory")))
DEFAULT_WORKSPACE_ID = os.getenv("DOPE_MEMORY_WORKSPACE_ID", "default")
DEFAULT_INSTANCE_ID = os.getenv("DOPE_MEMORY_INSTANCE_ID", "A")

# Global MCP server instance
mcp_server: Optional[DopeMemoryMCPServer] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class MemorySearchRequest(BaseModel):
    """Request for memory_search tool."""

    query: str = ""
    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    session_id: Optional[str] = None
    category: Optional[str] = None
    entry_type: Optional[str] = None
    workflow_phase: Optional[str] = None
    tags_any: Optional[list[str]] = None
    time_range: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=20)
    cursor: Optional[str] = None


class MemoryStoreRequest(BaseModel):
    """Request for memory_store tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    category: str
    entry_type: str
    summary: str
    session_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    reasoning: Optional[str] = None
    outcome: str = "in_progress"
    importance_score: int = Field(default=6, ge=1, le=10)
    tags: Optional[list[str]] = None
    links: Optional[dict[str, Any]] = None


class MemoryRecapRequest(BaseModel):
    """Request for memory_recap tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    scope: str = Field(default="session", pattern=r"^(session|today|last_2_hours)$")
    session_id: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=10)


class MemoryMarkIssueRequest(BaseModel):
    """Request for memory_mark_issue tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    issue_entry_id: str
    description: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    evidence_window_min: int = Field(default=30, ge=1, le=1440)
    tags: Optional[list[str]] = None


class MemoryLinkResolutionRequest(BaseModel):
    """Request for memory_link_resolution tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    issue_entry_id: str
    resolution_entry_id: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence_window_min: int = Field(default=30, ge=1, le=1440)


class MemoryReplaySessionRequest(BaseModel):
    """Request for memory_replay_session tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    session_id: str
    top_k: int = Field(default=3, ge=1, le=20)
    cursor: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Application Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global mcp_server

    # Initialize MCP server
    logger.info(f"Initializing Dope-Memory MCP server with data_dir={DATA_DIR}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    mcp_server = DopeMemoryMCPServer(
        data_dir=DATA_DIR,
        workspace_id=DEFAULT_WORKSPACE_ID,
        instance_id=DEFAULT_INSTANCE_ID,
    )

    logger.info(f"Dope-Memory HTTP server started on port {PORT}")
    yield

    # Cleanup
    logger.info("Dope-Memory HTTP server stopping")


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Dope-Memory",
    description="Temporal chronicle and working-context manager for Dopemux",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Health & Info Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/health")
async def health_check():
    """Health check endpoint per registry contract."""
    return {
        "status": "healthy",
        "service": "dope-memory",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "dope-memory",
        "version": "1.0.0",
        "description": "Temporal chronicle and working-context manager",
        "spec_path": "docs/spec/dope-memory/v1/",
        "tools": [
            "memory_search",
            "memory_store",
            "memory_recap",
            "memory_mark_issue",
            "memory_link_resolution",
            "memory_replay_session",
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@app.post("/tools/memory_search")
async def memory_search(request: MemorySearchRequest):
    """Search work log entries.

    Returns Top-3 (default) with pagination support.
    """
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    filters = {
        "category": request.category,
        "entry_type": request.entry_type,
        "workflow_phase": request.workflow_phase,
        "tags_any": request.tags_any,
        "time_range": request.time_range,
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    result = mcp_server.memory_search(
        query=request.query,
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        session_id=request.session_id,
        filters=filters if filters else None,
        top_k=request.top_k,
        cursor=request.cursor,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@app.post("/tools/memory_store")
async def memory_store(request: MemoryStoreRequest):
    """Store a manual work log entry."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_store(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        category=request.category,
        entry_type=request.entry_type,
        summary=request.summary,
        session_id=request.session_id,
        details=request.details,
        reasoning=request.reasoning,
        outcome=request.outcome,
        importance_score=request.importance_score,
        tags=request.tags,
        links=request.links,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@app.post("/tools/memory_recap")
async def memory_recap(request: MemoryRecapRequest):
    """Get a recap of recent work (session/today/last_2_hours)."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_recap(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        scope=request.scope,
        session_id=request.session_id,
        top_k=request.top_k,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@app.post("/tools/memory_mark_issue")
async def memory_mark_issue(request: MemoryMarkIssueRequest):
    """Mark an entry as an issue source."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_mark_issue(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        issue_entry_id=request.issue_entry_id,
        description=request.description,
        confidence=request.confidence,
        evidence_window_min=request.evidence_window_min,
        tags=request.tags,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@app.post("/tools/memory_link_resolution")
async def memory_link_resolution(request: MemoryLinkResolutionRequest):
    """Link an issue entry to its resolution."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_link_resolution(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        issue_entry_id=request.issue_entry_id,
        resolution_entry_id=request.resolution_entry_id,
        confidence=request.confidence,
        evidence_window_min=request.evidence_window_min,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@app.post("/tools/memory_replay_session")
async def memory_replay_session(request: MemoryReplaySessionRequest):
    """Replay session entries chronologically."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_replay_session(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        session_id=request.session_id,
        top_k=request.top_k,
        cursor=request.cursor,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


# ═══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "dope_memory_main:app",
        host="0.0.0.0",
        port=PORT,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
