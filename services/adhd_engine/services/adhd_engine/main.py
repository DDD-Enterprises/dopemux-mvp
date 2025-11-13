"""
ADHD Accommodation Engine - FastAPI Application

Standalone microservice extracted from task-orchestrator (Decision #140).

Features:
- 6 API endpoints (/api/v1/*) + 2 utility endpoints for ADHD assessments
- 6 background async monitors (energy, attention, cognitive load, breaks, hyperfocus, context switching)
- Redis persistence for user profiles and state
- DopeconBridge connection for ConPort data (✅ COMPLETE as of 2025-10-16)
- API key authentication (X-API-Key header)
- Environment-based CORS configuration
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Prometheus metrics + core modules (support script + package execution)
try:
    from .metrics import (
        REQUEST_COUNT, REQUEST_LATENCY, ENERGY_LEVEL, ATTENTION_STATE,
        COGNITIVE_LOAD, BREAK_RECOMMENDATIONS, ACCOMMODATION_STATS,
        ACTIVE_USERS, MONITORING_CYCLES, record_request, update_energy_level,
        update_attention_state, update_cognitive_load, record_break_recommendation,
        record_accommodation_action, update_active_users, record_monitoring_cycle,
        get_metrics,
    )
    from .engine import ADHDAccommodationEngine
    from .api import routes
    from .config import settings
except ImportError:  # pragma: no cover - fallback outside package context
    from metrics import (  # type: ignore
        REQUEST_COUNT, REQUEST_LATENCY, ENERGY_LEVEL, ATTENTION_STATE,
        COGNITIVE_LOAD, BREAK_RECOMMENDATIONS, ACCOMMODATION_STATS,
        ACTIVE_USERS, MONITORING_CYCLES, record_request, update_energy_level,
        update_attention_state, update_cognitive_load, record_break_recommendation,
        record_accommodation_action, update_active_users, record_monitoring_cycle,
        get_metrics,
    )
    from engine import ADHDAccommodationEngine  # type: ignore
    from api import routes  # type: ignore
    from config import settings  # type: ignore
# from middleware.rate_limit import RateLimitMiddleware  # Disabled for testing

# Import shared Redis pool and cache for performance optimization
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'docker', 'mcp-servers', 'shared'))
from redis_pool import get_redis_pool
from cache import get_cache

# Parse allowed origins from environment
def get_allowed_origins():
    """Parse ALLOWED_ORIGINS environment variable with fallback for malformed entries."""
    origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8097")
    origins = []

    for origin in origins_str.split(","):
        origin = origin.strip()
        # Basic validation - skip obviously malformed origins
        if origin and "://" in origin and not origin.startswith("javascript:"):
            origins.append(origin)

    # Always include fallback origins if parsing resulted in empty list
    if not origins:
        origins = ["http://localhost:3000", "http://localhost:8097"]

    return origins

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
    - Start 6 background monitors
    - Initialize ConPort integration
    - Setup Redis connections

    Shutdown:
    - Stop background monitors
    - Flush Redis cache
    - Close ConPort connections
    """
    global engine

    # STARTUP
    logger.info("=" * 60)
    logger.info("🧠 ADHD Accommodation Engine - Starting...")
    logger.info("=" * 60)

    try:
        # Initialize Redis pool and cache
        redis_pool = get_redis_pool()
        cache = get_cache()

        # Initialize ADHD Accommodation Engine
        engine = ADHDAccommodationEngine(
            redis_pool=redis_pool,
            cache=cache
        )

        # Start background monitors
        await engine.start_monitors()

        logger.info("✅ ADHD Accommodation Engine started successfully")
        logger.info("   6 background monitors active")
        logger.info("   Redis persistence enabled")
        logger.info("   ConPort integration ready")

    except Exception as e:
        logger.error(f"❌ Failed to start ADHD Accommodation Engine: {e}")
        raise

    yield

    # SHUTDOWN
    logger.info("🧠 ADHD Accommodation Engine - Shutting down...")

    try:
        if engine:
            # Stop background monitors
            await engine.stop_monitors()

        logger.info("✅ ADHD Accommodation Engine shut down gracefully")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    """
    # Initialize FastAPI app
    app = FastAPI(
        title="ADHD Accommodation Engine",
        description="AI-powered ADHD task management and accommodation engine",
        version="1.0.0",
        lifespan=lifespan
    )

    # Configure CORS with environment-based origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Rate limiting disabled for initial testing

    # Include API routes
    app.include_router(
        routes.router,
        prefix="/api/v1",
        tags=["adhd-accommodation"]
    )

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for container orchestration."""
        return {
            "status": "healthy",
            "service": "adhd-accommodation-engine",
            "version": "1.0.0",
            "monitors": {
                "energy_tracking": getattr(engine.monitors.get("energy_tracking"), "is_running", False) if engine and engine.monitors else False,
                "attention_monitoring": getattr(engine.monitors.get("attention_monitoring"), "is_running", False) if engine and engine.monitors else False,
                "cognitive_load": getattr(engine.monitors.get("cognitive_load"), "is_running", False) if engine and engine.monitors else False,
                "break_suggestions": getattr(engine.monitors.get("break_suggester"), "is_running", False) if engine and engine.monitors else False,
                "hyperfocus_detection": getattr(engine.monitors.get("hyperfocus_detector"), "is_running", False) if engine and engine.monitors else False,
                "context_switching": getattr(engine.monitors.get("context_switch_tracker"), "is_running", False) if engine and engine.monitors else False
            } if engine else "engine_not_initialized"
        }

    # Info endpoint
    @app.get("/", tags=["info"])
    async def root():
        """Service information endpoint."""
        return {
            "service": "ADHD Accommodation Engine",
            "description": "AI-powered ADHD task management and accommodation engine",
            "version": "1.0.0",
            "endpoints": [
                "POST /api/v1/assess-task",
                "GET /api/v1/energy-level/{user_id}",
                "GET /api/v1/attention-state/{user_id}",
                "POST /api/v1/recommend-break",
                "POST /api/v1/user-profile",
                "PUT /api/v1/activity/{user_id}",
                "GET /health"
            ]
        }

    return app


# Create application instance
app = create_application()


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for ADHD Engine"""
    from metrics import get_metrics
    from fastapi.responses import Response
    return Response(get_metrics(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn

    # Get port from environment
    port = int(os.getenv("API_PORT", "8095"))

    # Start server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=settings.log_level.lower()
    )
