"""
DopeconBridge - Central coordination layer for Dopemux services.

Unified entrypoint that integrates modular routers, database, and cache.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dopecon_bridge.config import settings
from dopecon_bridge.core import cache_manager, db_manager
from dopecon_bridge.routes import get_all_routers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for database and cache connections."""
    logger.info("🚀 Starting DopeconBridge service...")
    
    # Initialize database
    try:
        await db_manager.initialize()
    except Exception as e:
        logger.error(f"❌ Could not initialize database: {e}")
        # Continue anyway, let medical checks handle it
        
    # Initialize cache
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.error(f"❌ Could not initialize cache: {e}")
        
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down DopeconBridge service...")
    await db_manager.close()
    await cache_manager.close()


# Initialize FastAPI app
app = FastAPI(
    title="Dopemux DopeconBridge",
    description="Central task management and event coordination layer",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all modular routers
for router in get_all_routers():
    app.include_router(router)

# Expose constants for uvicorn wrapper
HOST = settings.host
MCP_INTEGRATION_PORT = settings.port
LOG_LEVEL = settings.log_level

if __name__ == "__main__":
    import uvicorn
    logger.info(f"📍 Starting DopeconBridge on {HOST}:{MCP_INTEGRATION_PORT}")
    uvicorn.run(
        "main:app",
        host=HOST,
        port=MCP_INTEGRATION_PORT,
        reload=False,
        log_level=LOG_LEVEL.lower()
    )
