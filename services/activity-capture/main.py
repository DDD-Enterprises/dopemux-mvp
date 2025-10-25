"""
Activity Capture Service - Automatic Development Activity Tracking

Subscribes to ConPort-KG event streams and automatically logs development
activity to the ADHD Accommodation Engine.

Event Sources:
- workspace.switched (Desktop-Commander) → Track interruptions, focus duration
- progress.updated (ConPort) → Track task completion (future)

ADHD Benefits:
- Zero manual logging overhead
- Real-time interruption detection
- Automatic energy/attention assessment
- Session duration tracking for break recommendations

Architecture:
- FastAPI service (port 8096)
- Redis Streams consumer (workspace events)
- HTTP client to ADHD Engine (port 8095)
- 5-minute activity aggregation windows
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from event_subscriber import EventSubscriber
from activity_tracker import ActivityTracker
from adhd_client import ADHDEngineClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
event_subscriber: EventSubscriber = None
activity_tracker: ActivityTracker = None
adhd_client: ADHDEngineClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Startup:
    - Initialize ADHD Engine client
    - Create activity tracker
    - Start event subscriber (Redis Streams)

    Shutdown:
    - Stop event subscriber
    - Flush pending activities
    - Close connections
    """
    global event_subscriber, activity_tracker, adhd_client

    # STARTUP
    logger.info("=" * 60)
    logger.info("🎯 Activity Capture Service - Starting...")
    logger.info("=" * 60)

    try:
        # Read configuration from environment
        adhd_engine_url = os.getenv("ADHD_ENGINE_URL", "http://localhost:8095")
        user_id = os.getenv("ADHD_USER_ID", "hue")
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        stream_name = os.getenv("STREAM_NAME", "dopemux:events")
        consumer_group = os.getenv("CONSUMER_GROUP", "activity-capture")
        consumer_name = os.getenv("CONSUMER_NAME", "activity-capture-1")
        aggregation_window = int(os.getenv("AGGREGATION_WINDOW_SECONDS", "300"))

        logger.info(f"📋 Configuration:")
        logger.info(f"   Redis: {redis_url}")
        logger.info(f"   ADHD Engine: {adhd_engine_url}")
        logger.info(f"   User: {user_id}")
        logger.info(f"   Stream: {stream_name}")

        # Initialize ADHD Engine client
        adhd_client = ADHDEngineClient(
            base_url=adhd_engine_url,
            user_id=user_id
        )
        logger.info("✅ ADHD Engine client initialized")

        # Initialize activity tracker
        activity_tracker = ActivityTracker(
            adhd_client=adhd_client,
            aggregation_window_seconds=aggregation_window
        )
        logger.info(f"✅ Activity tracker initialized ({aggregation_window}s windows)")

        # Initialize event subscriber
        event_subscriber = EventSubscriber(
            redis_url=redis_url,
            stream_name=stream_name,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
            activity_tracker=activity_tracker
        )

        # Start subscribing to events
        await event_subscriber.start()
        logger.info("✅ Event subscriber started (dopemux:events)")

        logger.info("")
        logger.info("🎉 Activity Capture Service ready!")
        logger.info(f"📊 Health check: http://localhost:8096/health")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # SHUTDOWN
    logger.info("=" * 60)
    logger.info("🛑 Activity Capture Service - Shutting down...")
    logger.info("=" * 60)

    try:
        if event_subscriber:
            await event_subscriber.stop()
            logger.info("✅ Event subscriber stopped")

        if activity_tracker:
            await activity_tracker.flush_all()
            logger.info("✅ Activity tracker flushed")

        logger.info("✅ Shutdown complete")

    except Exception as e:
        logger.error(f"⚠️ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="Activity Capture Service",
    description="Automatic development activity tracking for ADHD Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Service information endpoint."""
    return {
        "service": "Activity Capture Service",
        "version": "1.0.0",
        "status": "operational",
        "purpose": "Automatic development activity tracking for ADHD Engine",
        "event_sources": [
            "workspace.switched (Desktop-Commander)",
            "progress.updated (ConPort - future)"
        ],
        "adhd_engine": "http://localhost:8095"
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
    - Event subscriber status
    - Activity tracker metrics
    - ADHD Engine connection status
    """
    health_status = {
        "status": "healthy",
        "components": {}
    }

    # Check event subscriber
    if event_subscriber:
        health_status["components"]["event_subscriber"] = {
            "status": "running" if event_subscriber.running else "stopped",
            "events_processed": event_subscriber.events_processed,
            "errors": event_subscriber.errors
        }
    else:
        health_status["components"]["event_subscriber"] = {"status": "not_initialized"}

    # Check activity tracker
    if activity_tracker:
        metrics = activity_tracker.get_metrics()
        health_status["components"]["activity_tracker"] = {
            "status": "active",
            "sessions_tracked": metrics["sessions_tracked"],
            "activities_logged": metrics["activities_logged"],
            "current_session_duration": metrics["current_session_duration_minutes"]
        }
    else:
        health_status["components"]["activity_tracker"] = {"status": "not_initialized"}

    # Check ADHD Engine connectivity
    if adhd_client:
        adhd_healthy = await adhd_client.check_health()
        health_status["components"]["adhd_engine"] = {
            "status": "connected" if adhd_healthy else "unreachable",
            "url": adhd_client.base_url
        }
    else:
        health_status["components"]["adhd_engine"] = {"status": "not_initialized"}

    return health_status


@app.get("/metrics")
async def metrics():
    """Get detailed service metrics"""
    if not activity_tracker:
        return {"error": "Activity tracker not initialized"}

    return activity_tracker.get_metrics()


# Development server
if __name__ == "__main__":
    import uvicorn

    logger.info("🔧 Starting in development mode...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8096,
        reload=True,
        log_level="info"
    )
