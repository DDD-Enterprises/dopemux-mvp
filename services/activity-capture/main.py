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
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.shared.brand_voice import StatusChip, brand_log, brand_payload, voice_header
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
subscriber_task: Optional[asyncio.Task] = None


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
    del app
    global event_subscriber, activity_tracker, adhd_client, subscriber_task

    # STARTUP
    logger.info(brand_log("=" * 60, chip=StatusChip.LIVE))
    logger.info(brand_log("🎯 Activity Capture Service - Starting...", chip=StatusChip.LIVE))
    logger.info(brand_log("=" * 60, chip=StatusChip.LIVE))

    try:
        # Read configuration from environment
        adhd_engine_url = os.getenv("ADHD_ENGINE_URL", "http://adhd-engine:8095")
        user_id = os.getenv("ADHD_USER_ID", "default")
        redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")
        stream_name = os.getenv("STREAM_NAME", "dopemux:events")
        consumer_group = os.getenv("CONSUMER_GROUP", "activity-capture")
        consumer_name = os.getenv("CONSUMER_NAME", "activity-capture-1")
        aggregation_window = int(os.getenv("AGGREGATION_WINDOW_SECONDS", "300"))

        logger.info(brand_log(f"📋 Configuration:", chip=StatusChip.LIVE))
        logger.info(brand_log(f"   Redis: {redis_url}", chip=StatusChip.LIVE))
        logger.info(brand_log(f"   ADHD Engine: {adhd_engine_url}", chip=StatusChip.LIVE))
        logger.info(brand_log(f"   User: {user_id}", chip=StatusChip.LIVE))
        logger.info(brand_log(f"   Stream: {stream_name}", chip=StatusChip.LIVE))

        # Initialize ADHD Engine client
        adhd_client = ADHDEngineClient(
            base_url=adhd_engine_url,
            user_id=user_id,
            api_key=os.getenv("ADHD_ENGINE_API_KEY"),
        )
        await adhd_client.initialize()
        logger.info(brand_log("✅ ADHD Engine client initialized", chip=StatusChip.LIVE))

        # Initialize activity tracker
        activity_tracker = ActivityTracker(
            adhd_client=adhd_client,
            aggregation_window_seconds=aggregation_window
        )
        logger.info(brand_log(f"✅ Activity tracker initialized ({aggregation_window}s windows)", chip=StatusChip.LIVE))

        # Initialize event subscriber
        event_subscriber = EventSubscriber(
            redis_url=redis_url,
            stream_name=stream_name,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
            activity_tracker=activity_tracker
        )

        # Start subscribing to events in the background so FastAPI startup can complete.
        subscriber_task = asyncio.create_task(
            event_subscriber.start(),
            name="activity-capture-event-subscriber",
        )
        logger.info(brand_log("✅ Event subscriber task started (dopemux:events)", chip=StatusChip.LIVE))

        logger.info(brand_log("", chip=StatusChip.LIVE))
        logger.info(brand_log("🎉 Activity Capture Service ready!", chip=StatusChip.LIVE))
        logger.info(brand_log(f"📊 Health check: http://localhost:{os.getenv('API_PORT', '8096')}/health", chip=StatusChip.LIVE))
        logger.info(brand_log("", chip=StatusChip.LIVE))

    except Exception as e:
        logger.error(brand_log(f"❌ Startup failed: {e}", chip=StatusChip.BLOCKER))
        raise

    yield

    # SHUTDOWN
    logger.info(brand_log("=" * 60, chip=StatusChip.LIVE))
    logger.info(brand_log("🛑 Activity Capture Service - Shutting down...", chip=StatusChip.LIVE))
    logger.info(brand_log("=" * 60, chip=StatusChip.LIVE))

    try:
        if event_subscriber:
            await event_subscriber.stop()
            logger.info(brand_log("✅ Event subscriber stopped", chip=StatusChip.LIVE))

        if subscriber_task:
            subscriber_task.cancel()
            await asyncio.gather(subscriber_task, return_exceptions=True)
            subscriber_task = None

        if activity_tracker:
            await activity_tracker.flush_all()
            logger.info(brand_log("✅ Activity tracker flushed", chip=StatusChip.LIVE))

        if adhd_client:
            await adhd_client.close()
            logger.info(brand_log("✅ ADHD Engine client closed", chip=StatusChip.LIVE))

        logger.info(brand_log("✅ Shutdown complete", chip=StatusChip.LIVE))

    except Exception as e:
        logger.error(brand_log(f"⚠️ Shutdown error: {e}", chip=StatusChip.BLOCKER))


# Create FastAPI application
app = FastAPI(
    title="Activity Capture Service",
    description="Automatic development activity tracking for ADHD Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Restricted to dashboard and localhost
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8097,http://127.0.0.1:8097,http://localhost:8096,http://127.0.0.1:8096"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Whitelist only dashboard and self
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
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
        "adhd_engine": os.getenv("ADHD_ENGINE_URL", "http://adhd-engine:8095"),
        **brand_payload("Activity Capture is auditing signals.")
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
            "events_processed": getattr(event_subscriber, 'events_processed', 0),
            "errors": getattr(event_subscriber, 'errors', 0)
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

    logger.info(brand_log("🔧 Starting in development mode...", chip=StatusChip.LIVE))

    port = int(os.getenv("API_PORT", "8096"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
