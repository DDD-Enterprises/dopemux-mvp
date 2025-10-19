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

from engine import ADHDAccommodationEngine
from api import routes
from config import settings

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
# Security: Use environment-based origin whitelist
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
