"""
ConPort HTTP API - Dashboard Access Layer

Standalone FastAPI server exposing ConPort knowledge graph data via HTTP.
Connects directly to PostgreSQL + AGE database.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from fastapi import FastAPI, Query

try:
    from dopemux.logging import configure_logging, RequestIDMiddleware
except Exception:  # pragma: no cover - fallback path for isolated service images
    RequestIDMiddleware = None

    def configure_logging(service_name, *, level=None, **_):
        resolved_level = getattr(logging, str(level or "INFO").upper(), logging.INFO)
        logging.basicConfig(
            level=resolved_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        return logging.getLogger(service_name)

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
configure_logging("conport", level=LOG_LEVEL)
logger = logging.getLogger("conport")

# Environment variable contract (G33)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "3004"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
SERVICE_NAME = os.getenv("SERVICE_NAME", "conport")
HEALTH_CHECK_PATH = os.getenv("HEALTH_CHECK_PATH", "/health")

# Global database pool (managed by lifespan)
pool: Optional[asyncpg.Pool] = None

# PostgreSQL settings from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "dopemux")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "dopemux_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dopemux_tasks")


async def init_db():
    """Initialize database pool with dependency validation"""
    global pool
    
    # Dependency constants
    CONNECT_TIMEOUT_SECONDS = 3
    RETRIES = 3
    BACKOFF_SECONDS = [0.2, 0.5, 1.0]
    
    # Initialize dependency status
    deps = {"postgres": "unknown"}
    
    # Probe postgres with retries
    deps = {"postgres": "unknown"}
    
    # Attempt connection with retries
    last_error = None
    for attempt in range(RETRIES):
        try:
            if attempt > 0:
                import asyncio
                await asyncio.sleep(BACKOFF_SECONDS[attempt - 1])
                logger.info(f"🔄 Retry {attempt + 1}/{RETRIES}...")
            
            logger.info("🔗 Probing PostgreSQL connection...")
            # Simple connection probe with timeout
            conn = await asyncpg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                timeout=CONNECT_TIMEOUT_SECONDS
            )
            await conn.close()
            logger.info("✅ PostgreSQL probe successful")
            
            # Now create the pool
            logger.info("🔗 Creating connection pool...")
            pool = await asyncpg.create_pool(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                min_size=2,
                max_size=10,
                command_timeout=10,
                timeout=CONNECT_TIMEOUT_SECONDS
            )
            logger.info("✅ Database connection pool created")
            
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM ag_catalog.decisions")
                logger.info(f"✅ Connected! Found {result} decisions in database")
            
            deps["postgres"] = "ok"
            return deps
        
        except Exception as e:
            last_error = e
            logger.warning(f"⚠️  Attempt {attempt + 1}/{RETRIES} failed: {e}")
            continue
    
    # All retries exhausted
    deps["postgres"] = "fail"
    logger.error(f"❌ PostgreSQL dependency FAILED after {RETRIES} attempts")
    logger.error(f"   Last error: {last_error}")
    logger.error(f"   Host: {POSTGRES_HOST}:{POSTGRES_PORT}")
    logger.error(f"   Database: {POSTGRES_DB}")
    # record_crash(last_error)
    raise RuntimeError(f"PostgreSQL unavailable: {last_error}")


async def close_db():
    """Close database pool"""
    global pool
    if pool:
        await pool.close()
        logger.info("✅ Database pool closed")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Application lifespan with database initialization"""
    logger.info(f"Starting {SERVICE_NAME} on {HOST}:{PORT}")
    
    app.state.ready = False
    app.state.deps = {"postgres": "unknown"}
    
    try:
        # Init DB
        deps = await init_db()
        app.state.deps = deps
        if deps.get("postgres") == "ok":
            app.state.ready = True
            logger.info("Service ready and dependencies healthy")
        else:
            logger.warning("Service started but dependencies probing failed")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        logger.info(f"Shutting down {SERVICE_NAME}")
        await close_db()
        app.state.ready = False


def create_app() -> FastAPI:
    """Create ConPort FastAPI application"""
    
    app = FastAPI(
        title="ConPort API",
        version="1.0.0",
        description="Dashboard access to ConPort knowledge graph",
        lifespan=app_lifespan
    )
    if RequestIDMiddleware is not None:
        app.add_middleware(RequestIDMiddleware)
    
    # Health check route
    @app.get(HEALTH_CHECK_PATH)
    async def health_check():
        status = "ok" if app.state.ready else "error"
        return {
            "status": status,
            "service": SERVICE_NAME,
            "dependencies": getattr(app.state, "deps", {})
        }
    
    # Store service name in app.state for error logging
    app.state.service_name = "conport"
    
    # Register ConPort-specific routes
    register_routes(app)
    
    return app


def register_routes(app: FastAPI):
    """Register ConPort API routes"""
    
    @app.get("/api/adhd/decisions/recent")
    async def get_recent_decisions(
        limit: int = Query(10, ge=1, le=100, description="Number of decisions to return"),
        workspace_id: str = Query("dopemux-mvp", description="Workspace ID filter")
    ):
        """
        Get recent decisions logged in the knowledge graph.
        
        Returns decisions ordered by creation time (most recent first).
        
        NOTE: Using mock data for MVP. TODO: Connect to real PostgreSQL database.
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
        
        return {
            "decisions": mock_decisions[:limit],
            "workspace_id": workspace_id,
            "total_count": len(mock_decisions)
        }
    
    @app.get("/api/adhd/cognitive_load/current")
    async def get_current_cognitive_load(workspace_id: str = Query("dopemux-mvp")):
        """Get current cognitive load estimate"""
        return {
            "workspace_id": workspace_id,
            "cognitive_load": 0.65,
            "status": "moderate",
            "factors": {
                "active_tasks": 3,
                "context_switches": 12,
                "open_questions": 5
            },
            "timestamp": "2025-10-29T07:30:00Z"
        }
    
    @app.get("/api/adhd/context/active")
    async def get_active_context(workspace_id: str = Query("dopemux-mvp")):
        """Get currently active context markers"""
        return {
            "workspace_id": workspace_id,
            "active_contexts": [
                {
                    "id": "ctx-dashboard-integration",
                    "type": "feature",
                    "description": "Building dashboard with real-time ADHD metrics",
                    "started_at": "2025-10-29T06:00:00Z",
                    "energy_level": "high",
                    "focus_score": 0.8
                },
                {
                    "id": "ctx-conport-api",
                    "type": "technical",
                    "description": "HTTP API implementation for knowledge graph access",
                    "started_at": "2025-10-29T06:30:00Z",
                    "energy_level": "medium",
                    "focus_score": 0.7
                }
            ],
            "total_count": 2
        }


# App instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_config=None  # Use dopemux logging config
    )
