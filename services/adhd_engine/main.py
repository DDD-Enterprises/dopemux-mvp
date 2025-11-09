"""
ADHD Accommodation Engine - FastAPI Application

Standalone microservice extracted from task-orchestrator (Decision #140).

Features:
- 6 API endpoints (/api/v1/*) + 2 utility endpoints for ADHD assessments
- 6 background async monitors (energy, attention, cognitive load, breaks, hyperfocus, context switching)
- Redis persistence for user profiles and state
- Integration Bridge connection for ConPort data (✅ COMPLETE as of 2025-10-16)
- API key authentication (X-API-Key header)
- Environment-based CORS configuration
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

try:
    from .engine import ADHDAccommodationEngine
    from .api import routes
    from .config import settings
    from .middleware.rate_limit import RateLimitMiddleware
except ImportError:  # pragma: no cover - fallback when run as script
    from engine import ADHDAccommodationEngine  # type: ignore
    from api import routes  # type: ignore
    from config import settings  # type: ignore
    from middleware.rate_limit import RateLimitMiddleware  # type: ignore

# Import shared Redis pool and cache for performance optimization
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'docker', 'mcp-servers', 'shared'))
from redis_pool import get_redis_pool
from cache import get_cache

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global engine instance
engine: ADHDAccommodationEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Startup:
    - Initialize ADHD accommodation engine
    - Connect to Redis
    - Start 6 background monitoring tasks

    Shutdown:
    - Stop background monitors gracefully
    - Close Redis connections
    - Clean up resources
    """
    global engine

    # STARTUP
    logger.info("=" * 60)
    logger.info("🚀 ADHD Accommodation Engine - Starting...")
    logger.info("=" * 60)

    try:
        # Initialize engine
        engine = ADHDAccommodationEngine()
        await engine.initialize()

        logger.info("✅ Startup complete - Service ready!")
        logger.info(f"📊 API Documentation: http://{settings.api_host}:{settings.api_port}/docs")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # SHUTDOWN
    logger.info("=" * 60)
    logger.info("🛑 ADHD Accommodation Engine - Shutting down...")
    logger.info("=" * 60)

    try:
        if engine:
            await engine.close()
        logger.info("✅ Shutdown complete")

    except Exception as e:
        logger.error(f"⚠️ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="ADHD Accommodation Engine",
    description="Neurodivergent developer support with intelligent accommodations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for browser access
# Security: Use environment-based origin whitelist with secure defaults and validation
from config import ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to safe HTTP methods only
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],  # Restrict to necessary headers
)

# Rate limiting middleware - protect against abuse
app.add_middleware(RateLimitMiddleware)

# Include API routes
app.include_router(routes.router, prefix="/api/v1", tags=["adhd"])


# Root endpoint
@app.get("/")
async def root():
    """Service information endpoint."""
    return {
        "service": "ADHD Accommodation Engine",
        "version": "1.0.0",
        "status": "operational",
        "migration": "Path C - Week 1",
        "decision": "#140",
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
async def health():
    """
    Detailed health check for Docker and monitoring.

    Returns status of:
    - Redis connection
    - Background monitors (6 total)
    - User profiles loaded
    - Accommodation statistics
    """
    if engine:
        try:
            health_status = await engine.get_accommodation_health()
            return health_status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "overall_status": "🔴 Error",
                "error": str(e),
                "service": "adhd-engine"
            }

    return {
        "overall_status": "⚠️ Starting",
        "message": "Engine initializing...",
        "service": "adhd-engine"
    }


@app.get("/background-service/status")
async def background_service_status():
    """Get background prediction service status (Phase 3.4)."""
    try:
        from engine.services.background_prediction_service import get_background_prediction_service
        service = await get_background_prediction_service()
        return await service.get_status()
    except Exception as e:
        logger.error(f"Failed to get background service status: {e}")
        return {"error": str(e), "running": False}

# Test endpoint to verify new routes work
@app.get("/test")
async def test():
    """Test endpoint to verify the API is working."""
    return {"message": "ADHD Engine API is operational!"}


# Development server
if __name__ == "__main__":
    import uvicorn

    logger.info("🔧 Starting in development mode...")

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Hot reload for development
        log_level=settings.log_level.lower()
    )
