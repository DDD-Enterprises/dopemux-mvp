#!/usr/bin/env python3
"""
ConPort HTTP API - Dashboard Access Layer

Standalone FastAPI server exposing ConPort knowledge graph data via HTTP.
Connects directly to PostgreSQL + AGE database.

Day 2 Afternoon Implementation
"""
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from contextlib import asynccontextmanager
import sys
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncpg

# Add repo root to path before importing dopemux modules
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(repo_root, "src"))

from dopemux.logging import configure_logging, RequestIDMiddleware
from dopemux.runtime import lifespan_context, record_crash

# Configure structured logging
configure_logging("conport")
logger = logging.getLogger(__name__)


def log_startup_config():
    """Log resolved configuration at startup (redacted)"""
    import os
    logger.info("=" * 60)
    logger.info("🚀 ConPort HTTP API - Starting")
    logger.info("=" * 60)
    logger.info(f"  Service: conport")
    logger.info(f"  Port: 8005")
    logger.info(f"  DB Host: {os.getenv('POSTGRES_HOST', '172.26.0.2')}")
    logger.info(f"  DB Port: {os.getenv('POSTGRES_PORT', '5432')}")
    logger.info(f"  DB Name: {os.getenv('POSTGRES_DB', 'dopemux_knowledge_graph')}")
    logger.info(f"  DB User: {os.getenv('POSTGRES_USER', 'dopemux_age')}")
    logger.info("=" * 60)

# Database connection pool
pool: Optional[asyncpg.Pool] = None

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "172.26.0.2"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "dopemux_age"),
    "password": os.getenv("POSTGRES_PASSWORD", "dopemux_age_dev_password"),
    "database": os.getenv("POSTGRES_DB", "dopemux_knowledge_graph")
}


async def init_db():
    """Initialize database pool"""
    global pool
    
    log_startup_config()
    
    try:
        logger.info("🔗 Connecting to PostgreSQL...")
        pool = await asyncpg.create_pool(
            **DB_CONFIG,
            min_size=2,
            max_size=10,
            command_timeout=10
        )
        logger.info("✅ Database connection pool created")
        
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM ag_catalog.decisions")
            logger.info(f"✅ Connected! Found {result} decisions in database")
    
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.warning("⚠️  Server will start but queries will fail")
        record_crash(e)  # Record for /health endpoint


async def close_db():
    """Close database pool"""
    global pool
    if pool:
        await pool.close()
        logger.info("✅ Database pool closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    async with lifespan_context("conport", init_db, close_db):
        yield


# FastAPI app
app = FastAPI(
    title="ConPort HTTP API",
    version="1.0.0",
    description="Dashboard access to ConPort knowledge graph",
    lifespan=lifespan
)

# CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Request ID middleware
app.add_middleware(RequestIDMiddleware)


@app.get("/health")
async def health():
    """Health check endpoint with dependency tracking"""
    from dopemux.health import check_dependency, check_postgres, determine_overall_status, HealthResponse
    from datetime import datetime, timezone
    
    # Check PostgreSQL
    pg_status = await check_dependency(
        "postgres",
        lambda: check_postgres(pool),
        timeout_ms=200,
        critical=True
    )
    
    dependencies = {"postgres": pg_status}
    
    # Determine overall status
    overall_status = determine_overall_status(dependencies, critical_deps={"postgres"})
    
    return HealthResponse(
        service="conport",
        status=overall_status,
        ts=datetime.now(timezone.utc).isoformat(),
        dependencies={k: v.dict() for k, v in dependencies.items()}
    )


@app.get("/api/adhd/decisions/recent")
async def get_recent_decisions(
    limit: int = Query(10, ge=1, le=100, description="Number of decisions to return"),
    workspace_id: str = Query("dopemux-mvp", description="Workspace ID filter")
):
    """
    Get recent decisions logged in the knowledge graph.
    
    Returns decisions ordered by creation time (most recent first).

    Uses PostgreSQL when available and falls back to mock data for resiliency.
    """
    # Mock data for MVP - dashboard won't crash
    mock_decisions = [
        {
            "id": "20d95436-873f-472b-a533-9bfc7f867046",
            "title": "Implement hybrid database backend for ConPort persistence",
            "context": "Provides real ADHD memory persistence while maintaining stability",
            "type": "architecture",
            "confidence": "medium",
            "tags": ["architecture", "persistence", "adhd-optimization"],
            "cognitive_load": 0.7,
            "energy_level": "medium",
            "decision_time": 15.0,
            "created_at": "2025-10-29T07:00:00Z"
        },
        {
            "id": "3b5b05cb-2cdb-41a3-b946-04928300b49a",
            "title": "Use Rich library for CLI terminal formatting",
            "context": "Provides ADHD-friendly visual output with minimal code",
            "type": "technical",
            "confidence": "high",
            "tags": ["cli", "adhd-optimization", "dependencies"],
            "cognitive_load": 0.3,
            "energy_level": "high",
            "decision_time": 5.0,
            "created_at": "2025-10-13T02:22:00Z"
        },
        {
            "id": "day2-mock-001",
            "title": "Create dual-mode services (MCP + HTTP)",
            "context": "Dashboard needs HTTP, MCP tools need stdio mode",
            "type": "architecture",
            "confidence": "high",
            "tags": ["architecture", "dashboard", "mcp"],
            "cognitive_load": 0.6,
            "energy_level": "high",
            "decision_time": 30.0,
            "created_at": "2025-10-29T06:00:00Z"
        }
    ]
    
    # Try real database first, fall back to mock
    if pool:
        try:
            async with pool.acquire() as conn:
                query = """
                    SELECT 
                        id::text,
                        workspace_id,
                        summary,
                        rationale,
                        tags,
                        confidence_level,
                        decision_type,
                        created_at,
                        cognitive_load,
                        energy_level,
                        decision_time_minutes
                    FROM ag_catalog.decisions
                    WHERE workspace_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """
                
                rows = await conn.fetch(query, workspace_id, limit)
                
                if rows:
                    decisions = [
                        {
                            "id": row["id"],
                            "title": row["summary"],
                            "context": row["rationale"],
                            "type": row["decision_type"],
                            "confidence": row["confidence_level"],
                            "tags": row["tags"] or [],
                            "cognitive_load": float(row["cognitive_load"]) if row["cognitive_load"] else None,
                            "energy_level": row["energy_level"],
                            "decision_time": float(row["decision_time_minutes"]) if row["decision_time_minutes"] else None,
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None
                        }
                        for row in rows
                    ]
                    
                    return {
                        "count": len(decisions),
                        "decisions": decisions,
                        "workspace_id": workspace_id,
                        "source": "database",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.warning(f"Database query failed, using mock data: {e}")
    
    # Return mock data
    return {
        "count": len(mock_decisions[:limit]),
        "decisions": mock_decisions[:limit],
        "workspace_id": workspace_id,
        "source": "mock",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/adhd/graph/stats")
async def get_graph_stats(
    workspace_id: str = Query("dopemux-mvp", description="Workspace ID filter")
):
    """
    Get knowledge graph statistics.
    
    Returns counts of nodes, edges, and other graph metrics.

    Uses PostgreSQL when available and falls back to mock data for resiliency.
    """
    # Mock data for MVP
    mock_stats = {
        "nodes": {
            "total": 156,
            "decisions": 48,
            "tasks": 73,
            "concepts": 35
        },
        "edges": 234,
        "workspaces": 1,
        "workspace_id": workspace_id,
        "source": "mock",
        "last_updated": datetime.utcnow().isoformat()
    }
    
    # Try real database first, fall back to mock
    if pool:
        try:
            async with pool.acquire() as conn:
                decisions_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM ag_catalog.decisions WHERE workspace_id = $1",
                    workspace_id
                )
                
                tasks_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM ag_catalog.tasks WHERE workspace_id = $1",
                    workspace_id
                )
                
                workspaces_count = await conn.fetchval(
                    "SELECT COUNT(DISTINCT workspace_id) FROM ag_catalog.workspaces"
                )
                
                concepts_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM ag_catalog.custom_data WHERE workspace_id = $1",
                    workspace_id
                )
                
                edges_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM ag_catalog.decision_relationships"
                )
                
                total_nodes = decisions_count + tasks_count + concepts_count
                
                return {
                    "nodes": {
                        "total": total_nodes,
                        "decisions": decisions_count,
                        "tasks": tasks_count,
                        "concepts": concepts_count
                    },
                    "edges": edges_count,
                    "workspaces": workspaces_count,
                    "workspace_id": workspace_id,
                    "source": "database",
                    "last_updated": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.warning(f"Database query failed, using mock data: {e}")
    
    # Return mock data
    return mock_stats


@app.post("/api/progress/log")
async def log_progress(
    progress_data: Dict[str, Any],
    workspace_id: str = Query(..., description="Workspace ID")
):
    """
    Log progress entry to ConPort knowledge graph.

    Exposes mcp__conport__log_progress via HTTP API.
    """
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            # Insert progress entry
            query = """
                INSERT INTO ag_catalog.progress_entries
                (workspace_id, status, description, tags, linked_item_type, linked_item_id, link_relationship_type, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                RETURNING id
            """

            result = await conn.fetchrow(
                query,
                workspace_id,
                progress_data.get("status"),
                progress_data.get("description"),
                progress_data.get("tags", []),
                progress_data.get("linked_item_type"),
                progress_data.get("linked_item_id"),
                progress_data.get("link_relationship_type")
            )

            if result:
                progress_id = result["id"]
                return {
                    "success": True,
                    "progress_id": progress_id,
                    "workspace_id": workspace_id
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create progress entry")

    except Exception as e:
        logger.error(f"Failed to log progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/progress")
async def get_progress(
    workspace_id: str = Query(..., description="Workspace ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """
    Get progress entries from ConPort knowledge graph.

    Exposes mcp__conport__get_progress via HTTP API.
    """
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            query = """
                SELECT
                    id, workspace_id, status, description, tags,
                    linked_item_type, linked_item_id, link_relationship_type,
                    created_at, updated_at
                FROM ag_catalog.progress_entries
                WHERE workspace_id = $1
            """
            params = [workspace_id]

            if status_filter:
                query += " AND status = $2"
                params.append(status_filter)

            query += " ORDER BY created_at DESC LIMIT $%d" % (len(params) + 1)
            params.append(limit)

            rows = await conn.fetch(query, *params)

            progress_entries = [
                {
                    "id": row["id"],
                    "workspace_id": row["workspace_id"],
                    "status": row["status"],
                    "description": row["description"],
                    "tags": row["tags"] or [],
                    "linked_item_type": row["linked_item_type"],
                    "linked_item_id": row["linked_item_id"],
                    "link_relationship_type": row["link_relationship_type"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                }
                for row in rows
            ]

            return {
                "count": len(progress_entries),
                "progress_entries": progress_entries,
                "workspace_id": workspace_id,
                "status_filter": status_filter,
                "limit": limit
            }

    except Exception as e:
        logger.error(f"Failed to get progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/api/progress/{progress_id}")
async def update_progress(
    progress_id: int,
    status: Optional[str] = None,
    description: Optional[str] = None,
    workspace_id: str = Query(..., description="Workspace ID")
):
    """
    Update progress entry in ConPort knowledge graph.

    Exposes mcp__conport__update_progress via HTTP API.
    """
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            # Build update query dynamically
            update_fields = []
            params = [progress_id, workspace_id]

            if status is not None:
                update_fields.append("status = $%d" % (len(params) + 1))
                params.append(status)

            if description is not None:
                update_fields.append("description = $%d" % (len(params) + 1))
                params.append(description)

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            update_fields.append("updated_at = NOW()")

            query = """
                UPDATE ag_catalog.progress_entries
                SET %s
                WHERE id = $1 AND workspace_id = $2
                RETURNING id
            """ % ", ".join(update_fields)

            result = await conn.fetchrow(query, *params)

            if result:
                return {
                    "success": True,
                    "progress_id": result["id"],
                    "workspace_id": workspace_id,
                    "updated_fields": ["status" if status else None, "description" if description else None]
                }
            else:
                raise HTTPException(status_code=404, detail="Progress entry not found")

    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/links")
async def link_conport_items(
    source_item_type: str,
    source_item_id: str,
    target_item_type: str,
    target_item_id: str,
    relationship_type: str,
    description: Optional[str] = None,
    workspace_id: str = Query(..., description="Workspace ID")
):
    """
    Create relationship link between ConPort items.

    Exposes mcp__conport__link_conport_items via HTTP API.
    """
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            # Insert link
            query = """
                INSERT INTO ag_catalog.item_relationships
                (workspace_id, source_item_type, source_item_id, target_item_type,
                 target_item_id, relationship_type, description, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                RETURNING id
            """

            result = await conn.fetchrow(
                query,
                workspace_id,
                source_item_type,
                source_item_id,
                target_item_type,
                target_item_id,
                relationship_type,
                description
            )

            if result:
                link_id = result["id"]
                return {
                    "success": True,
                    "link_id": link_id,
                    "workspace_id": workspace_id,
                    "source": f"{source_item_type}:{source_item_id}",
                    "target": f"{target_item_type}:{target_item_id}",
                    "relationship": relationship_type
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create link")

    except Exception as e:
        logger.error(f"Failed to create link: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/adhd/patterns")
async def get_system_patterns(
    limit: int = Query(10, ge=1, le=100),
    workspace_id: str = Query("dopemux-mvp")
):
    """Get system patterns from the knowledge graph."""
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT id::text, name, description, tags, created_at
                FROM ag_catalog.system_patterns
                WHERE workspace_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, workspace_id, limit)
            return {
                "count": len(rows),
                "patterns": [dict(r) for r in rows],
                "workspace_id": workspace_id
            }
    except Exception as e:
        logger.error(f"Failed to get patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/links")
async def get_linked_items(
    item_id: str = Query(...),
    item_type: str = Query(...),
    workspace_id: str = Query("dopemux-mvp")
):
    """Get items linked to a specific item."""
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT id, source_item_type, source_item_id, target_item_type, 
                       target_item_id, relationship_type, description, created_at
                FROM ag_catalog.item_relationships
                WHERE workspace_id = $1 AND (
                    (source_item_id = $2 AND source_item_type = $3) OR
                    (target_item_id = $2 AND target_item_type = $3)
                )
            """
            rows = await conn.fetch(query, workspace_id, item_id, item_type)
            return {
                "count": len(rows),
                "links": [dict(r) for r in rows]
            }
    except Exception as e:
        logger.error(f"Failed to get links: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/adhd/semantic-search")
async def semantic_search(
    payload: Dict[str, Any],
    workspace_id: str = Query("dopemux-mvp")
):
    """
    Deprecated compatibility endpoint for ConPort semantic search.
    Uses keyword fallback across decisions and progress entries.
    """
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")

    query_text = (payload.get("query_text") or "").strip()
    top_k = max(int(payload.get("top_k", 5)), 1)
    if not query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    logger.warning(
        "/api/adhd/semantic-search is deprecated and running in keyword fallback mode; "
        "use dope-context/serena semantic search for vector retrieval."
    )

    try:
        async with pool.acquire() as conn:
            sql = """
                SELECT id::text, 'decision' as type, summary as content, created_at
                FROM ag_catalog.decisions
                WHERE workspace_id = $1 AND (summary ILIKE $2 OR rationale ILIKE $2)
                UNION ALL
                SELECT id::text, 'progress_entry' as type, description as content, created_at
                FROM ag_catalog.progress_entries
                WHERE workspace_id = $1 AND description ILIKE $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            search_pattern = f"%{query_text}%"
            rows = await conn.fetch(sql, workspace_id, search_pattern, top_k)

            deprecation_notice = (
                "Deprecated compatibility endpoint: keyword fallback only. "
                "Use dope-context/serena semantic search for vector retrieval."
            )
            return {
                "query": query_text,
                "results": [dict(r) for r in rows],
                "workspace_id": workspace_id,
                "search_mode": "keyword_fallback",
                "deprecated": True,
                "deprecation_notice": deprecation_notice
            }
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "ConPort HTTP API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "decisions": "/api/adhd/decisions/recent",
            "graph_stats": "/api/adhd/graph/stats",
            "log_progress": "/api/progress/log",
            "get_progress": "/api/progress",
            "update_progress": "/api/progress/{progress_id}",
            "link_items": "/api/links",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8005))
    logger.info("=" * 60)
    logger.info("🚀 ConPort HTTP API")
    logger.info("=" * 60)
    logger.info(f"📊 Database: {DB_CONFIG['database']}")
    logger.info(f"🔌 Port: {port}")
    logger.info(f"📚 Docs: http://localhost:{port}/docs")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
