"""
DopeconBridge - Slim Application Entrypoint

This is the new modular entrypoint replacing the 2915-line main.py monolith.
All functionality has been extracted into focused modules:

- config.py: Environment configuration
- models.py: SQLAlchemy ORM + Pydantic schemas
- core.py: Database and cache managers
- auth.py: JWT authentication
- clients.py: MCP and ConPort HTTP clients  
- routes.py: FastAPI route definitions
- services/: Business logic modules
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dopecon_bridge.auth import init_default_users
from dopecon_bridge.clients import conport_client, mcp_client, ConPortMiddleware
from dopecon_bridge.config import settings
from dopecon_bridge.core import cache_manager, db_manager
from dopecon_bridge.routes import get_all_routers


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
    logger.info("🚀 DopeconBridge v2.0 - Modular Architecture")
    logger.info("=" * 60)
    logger.info(f"📊 Instance: {settings.instance_name}")
    logger.info(f"🔌 Port: {settings.port}")
    logger.info(f"📚 Docs: http://localhost:{settings.port}/docs")
    logger.info("=" * 60)
    
    try:
        await db_manager.initialize()
        await cache_manager.initialize()
        await mcp_client.initialize()
        await conport_client.initialize()
        init_default_users()
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DopeconBridge...")
    await mcp_client.close()
    await conport_client.close()
    await cache_manager.close()
    await db_manager.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="DopeconBridge",
    version="2.0.0",
    description="Central coordination layer for Dopemux task management - Modular Architecture",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ConPort context middleware for ADHD-friendly context preservation
conport_middleware = ConPortMiddleware(conport_client)

@app.middleware("http")
async def context_middleware(request, call_next):
    """Apply ConPort context middleware."""
    return await conport_middleware(request, call_next)

# Register all routers
for router in get_all_routers():
    app.include_router(router)


# Entry point
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
