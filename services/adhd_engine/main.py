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
import asyncio
import importlib.util
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
PROMETHEUS_AVAILABLE = importlib.util.find_spec("prometheus_client") is not None

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

# Use relative imports for module execution (python -m services.adhd_engine.main)
from .core.engine import ADHDAccommodationEngine
from .api import routes
from .config import settings
from .middleware.rate_limit import RateLimitMiddleware
from .core.error_handling import with_error_handling
try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional dependency for local test envs
    class FastMCP:  # type: ignore[override]
        """Minimal FastMCP fallback so API can boot without MCP extras."""

        def __init__(self, name: str):
            self.name = name
            self.http_app = FastAPI(title=f"{name} MCP Fallback")

        def tool(self):
            def decorator(func):
                return func

            return decorator

# Initialize FastMCP
mcp = FastMCP("ADHD-Engine")

@mcp.tool()
async def get_cognitive_state(user_id: str = "default") -> dict:
    """Get current cognitive state (energy, attention, load)."""
    if not engine:
        return {"error": "Engine not initialized"}

    # We call the engine directly for speed
    energy = await engine.get_energy_level(user_id)
    attention = await engine.get_attention_state(user_id)
    load = await engine.get_cognitive_load(user_id)

    return {
        "energy_level": energy.level,
        "energy_score": energy.score,
        "attention_state": attention.state,
        "cognitive_load": load
    }

@mcp.tool()
async def assess_task_complexity(title: str, description: str = "") -> dict:
    """Assess task complexity and ADHD impact."""
    if not engine:
        return {"error": "Engine not initialized"}

    assessment = await engine.assess_task(title, description)
    return assessment.dict()

# Import shared Redis pool and cache for performance optimization
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'docker', 'mcp-servers', 'shared'))
from redis_pool import get_redis_pool
from cache import get_cache

# Import shared monitoring (optional - from repo root shared/, not services/shared)
try:
    import sys
    import os
    # Add repo root to path to find shared/monitoring
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from shared.monitoring.base import DopemuxMonitoring
except ImportError:
    DopemuxMonitoring = None
    logger = logging.getLogger(__name__)
    logger.warning("DopemuxMonitoring not available - metrics disabled")

# Use relative imports for module execution
from .core.error_handling import (
    GlobalErrorHandler,
    CircuitBreaker,
    CircuitBreakerConfig,
    ErrorType,
    ErrorSeverity
)

# Configure logging
configure_logging("adhd-engine", level=str(settings.log_level))
logger = logging.getLogger(__name__)

# Global instances
engine: ADHDAccommodationEngine = None
error_handler: GlobalErrorHandler = None
circuit_breakers = {}
monitoring: DopemuxMonitoring = None

# Phase 7: Full I/O Wiring globals
workspace_watcher = None
output_dispatcher = None


class _FallbackADHDEngine:
    """Lightweight engine used when test-mode startup must proceed without infra."""

    def __init__(self, startup_error: str):
        self.startup_error = startup_error
        self.user_profiles = {}
        self.current_energy_levels = {}
        self.current_attention_states = {}
        self.predictive_engine = None
        self.is_fallback_engine = True

    async def close(self) -> None:
        return None

    async def _calculate_system_cognitive_load(self) -> float:
        return 0.35

    async def get_energy_level(self, user_id: str):
        class _EnergyState:
            def __init__(self, level: str = "medium", score: float = 0.5):
                self.level = level
                self.score = score

        energy = self.current_energy_levels.get(user_id, "medium")
        energy_text = energy.value if hasattr(energy, "value") else str(energy)
        return _EnergyState(level=energy_text, score=0.5)

    async def get_attention_state(self, user_id: str):
        class _AttentionSnapshot:
            def __init__(self, state: str = "focused"):
                self.state = state

        state = self.current_attention_states.get(user_id, "focused")
        state_text = state.value if hasattr(state, "value") else str(state)
        return _AttentionSnapshot(state=state_text)

    async def get_cognitive_load(self, user_id: str) -> float:
        return await self._calculate_system_cognitive_load()

    async def get_accommodation_health(self) -> dict:
        return {
            "overall_status": "🟡 Degraded",
            "service": "adhd-engine",
            "mode": "fallback",
            "startup_error": self.startup_error,
        }

    async def assess_task_suitability(self, user_id: str, task_data: dict) -> dict:
        complexity = float(task_data.get("complexity_score", 0.5))
        estimated_minutes = int(task_data.get("estimated_minutes", 30))
        suitability_score = max(0.0, min(1.0, 1.0 - (complexity * 0.5)))
        cognitive_load = max(0.0, min(1.0, complexity * 0.8 + (estimated_minutes / 180.0)))

        if cognitive_load < 0.2:
            load_level = "minimal"
        elif cognitive_load < 0.4:
            load_level = "low"
        elif cognitive_load < 0.6:
            load_level = "moderate"
        elif cognitive_load < 0.8:
            load_level = "high"
        else:
            load_level = "extreme"

        return {
            "suitability_score": suitability_score,
            "energy_match": max(0.0, min(1.0, 1.0 - complexity)),
            "attention_compatibility": max(0.0, min(1.0, 1.0 - (complexity * 0.7))),
            "cognitive_load": cognitive_load,
            "cognitive_load_level": load_level,
            "recommendations": [
                {
                    "accommodation_type": "task_chunking",
                    "urgency": "soon",
                    "message": "Break this task into smaller steps",
                    "action_required": False,
                    "suggested_actions": ["Split into 15-minute chunks"],
                    "cognitive_benefit": "Reduces overwhelm",
                    "implementation_effort": "low",
                }
            ],
            "accommodations_needed": ["task_chunking"],
            "optimal_timing": {"recommended_window": "now", "reason": "fallback_engine"},
            "adhd_insights": {
                "hyperfocus_risk": "low",
                "distraction_risk": "medium",
                "context_switch_impact": "medium",
            },
        }

    async def assess_task(self, title: str, description: str = ""):
        class _Assessment:
            def __init__(self, payload: dict):
                self._payload = payload

            def dict(self) -> dict:
                return self._payload

        payload = await self.assess_task_suitability(
            user_id="default",
            task_data={
                "title": title,
                "description": description,
                "complexity_score": 0.5,
                "estimated_minutes": 30,
            },
        )
        return _Assessment(payload)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Startup:
    - Initialize ADHD accommodation engine
    - Connect to Redis
    - Start 6 background monitoring tasks
    - Start ADHD Event Listener for implicit triggers

    Shutdown:
    - Stop background monitors gracefully
    - Stop ADHD Event Listener
    - Close Redis connections
    - Clean up resources
    """
    global engine, error_handler, circuit_breakers, monitoring, workspace_watcher, output_dispatcher

    # Track background tasks for cleanup
    event_listener_task = None
    event_listener = None
    event_bus = None

    # STARTUP
    logger.info("=" * 60)
    logger.info("🚀 ADHD Accommodation Engine - Starting...")
    logger.info("=" * 60)

    try:
        # Initialize monitoring
        if DopemuxMonitoring is not None:
            monitoring = DopemuxMonitoring(
                service_name="adhd-engine",
                workspace_id=os.getenv("WORKSPACE_ID"),
                instance_id=os.getenv("INSTANCE_ID"),
                version=os.getenv("SERVICE_VERSION", "1.0.0")
            )
            logger.info("✅ Monitoring initialized")
        else:
            monitoring = None
            logger.info("ℹ️ Monitoring disabled (shared.monitoring unavailable)")
        # Initialize error handler and circuit breakers
        error_handler = GlobalErrorHandler("adhd_engine")

        # Initialize circuit breakers for external services
        circuit_breakers["redis"] = CircuitBreaker(
            CircuitBreakerConfig(
                name="redis_circuit",
                failure_threshold=5,
                recovery_timeout=60,
                success_threshold=2,
                timeout=10.0
            )
        )

        circuit_breakers["conport"] = CircuitBreaker(
            CircuitBreakerConfig(
                name="conport_circuit",
                failure_threshold=3,
                recovery_timeout=90,
                success_threshold=3,
                timeout=15.0
            )
        )

        circuit_breakers["zen_mcp"] = CircuitBreaker(
            CircuitBreakerConfig(
                name="zen_mcp_circuit",
                failure_threshold=3,
                recovery_timeout=120,
                success_threshold=2,
                timeout=5.0
            )
        )

        logger.info("✅ Circuit breakers initialized for external services")

        # Initialize engine
        engine = ADHDAccommodationEngine()
        try:
            await engine.initialize()
        except Exception as startup_error:
            degraded_mode = os.getenv("ADHD_ENGINE_ALLOW_DEGRADED_STARTUP", "0").lower() in {"1", "true", "yes"}
            if not degraded_mode:
                raise
            logger.warning(
                "⚠️ Engine startup failed, continuing in degraded mode for local/test workflows: %s",
                startup_error,
            )
            engine = _FallbackADHDEngine(str(startup_error))

        # Initialize ADHD Event Listener for implicit triggers (Phase 6)
        # Initialize Output Dispatcher (Phase 7)
        try:
            from .core.output_dispatcher import create_output_dispatcher

            output_dispatcher = create_output_dispatcher(
                enable_voice=True,
                enable_push=False,
            )
            engine.output_dispatcher = output_dispatcher
            logger.info("✅ Output Dispatcher initialized (Console, Tmux, Voice channels)")
        except ImportError as e:
            logger.debug(f"Output Dispatcher not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Output Dispatcher: {e}")

        try:
            from .event_listener import create_adhd_event_listener

            # Get EventBus from engine if available, or create connection
            event_bus = getattr(engine, 'event_bus', None)

            if event_bus:
                output_channels = []
                if output_dispatcher is not None:
                    output_channels = list(output_dispatcher.channels.values())

                event_listener = create_adhd_event_listener(
                    event_bus,
                    engine,
                    output_channels=output_channels,
                )

                # Start event listener as background task
                event_listener_task = asyncio.create_task(
                    event_listener.start(user_id="default"),
                    name="adhd_event_listener"
                )

                logger.info("✅ ADHD Event Listener started (implicit triggers enabled)")
            else:
                logger.warning("⚠️ EventBus not available - ADHD Event Listener not started")

        except ImportError as e:
            logger.warning(f"⚠️ ADHD Event Listener not available: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to start ADHD Event Listener: {e}")

        # Initialize Workspace Watcher (Phase 7)
        workspace_path = os.getenv("WORKSPACE_PATH", os.getcwd())
        if event_bus:
            try:
                from .workspace_watcher import create_workspace_watcher
                workspace_watcher = create_workspace_watcher(event_bus, workspace_path)
                await workspace_watcher.start()
                logger.info(f"✅ Workspace Watcher started for {workspace_path}")
            except ImportError as e:
                logger.debug(f"Workspace Watcher not available: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to start Workspace Watcher: {e}")

        # Initialize External Activity Manager (Desktop Commander + Calendar)
        external_activity_manager = None
        try:
            from .external_activity import create_external_activity_manager
            
            event_bus = getattr(engine, 'event_bus', None)
            
            if event_bus:
                external_activity_manager = create_external_activity_manager(event_bus)
                await external_activity_manager.start()
                
                # Store reference in engine for API access
                engine.external_activity = external_activity_manager
                
                logger.info("✅ External Activity Manager started (Desktop Commander + Calendar)")
            else:
                logger.warning("⚠️ EventBus not available - External Activity Manager not started")
                
        except ImportError as e:
            logger.debug(f"External Activity Manager not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to start External Activity Manager: {e}")

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
        # Stop workspace watcher (Phase 7)
        if workspace_watcher:
            await workspace_watcher.stop()
            logger.info("✅ Workspace Watcher stopped")
        
        # Stop external activity manager
        if external_activity_manager:
            await external_activity_manager.stop()
            logger.info("✅ External Activity Manager stopped")
        
        # Stop event listener
        if event_listener:
            await event_listener.stop()
            logger.info("✅ ADHD Event Listener stopped")
        
        if event_listener_task and not event_listener_task.done():
            event_listener_task.cancel()
            try:
                await event_listener_task
            except asyncio.CancelledError:
                pass
        
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

# Mount FastMCP HTTP app
app.mount("/mcp", mcp.http_app)

# CORS middleware for browser access
# Security: Use environment-based origin whitelist with secure defaults and validation
from .config import ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to safe HTTP methods only
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],  # Restrict to necessary headers
)
if RequestIDMiddleware is not None:
    app.add_middleware(RequestIDMiddleware)

# Rate limiting middleware - protect against abuse
app.add_middleware(RateLimitMiddleware)

# Monitoring middleware - track all requests
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if monitoring and not request.url.path.startswith("/metrics"):
            start_time = time.time()
            monitoring.requests_in_progress.labels(**monitoring.core_labels).inc()
            
            try:
                response = await call_next(request)
                duration = time.time() - start_time
                
                # Record metrics
                monitoring.record_request(
                    endpoint=request.url.path,
                    method=request.method,
                    status=response.status_code,
                    duration=duration
                )
                
                return response
            finally:
                monitoring.requests_in_progress.labels(**monitoring.core_labels).dec()
        else:
            return await call_next(request)

app.add_middleware(MonitoringMiddleware)

# Include API routes
app.include_router(routes.router, prefix="/api/v1", tags=["adhd"])

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if monitoring and PROMETHEUS_AVAILABLE:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from starlette.responses import Response
        metrics_output = generate_latest(monitoring.registry)
        return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
    if not monitoring:
        return {"error": "Monitoring not initialized"}
    return {"error": "prometheus_client not installed"}


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
        try:
            from .services.background_prediction_service import get_background_prediction_service
        except ImportError:
            from services.background_prediction_service import get_background_prediction_service
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
        "services.adhd_engine.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True,  # Hot reload for development
        log_level=settings.log_level.lower()
    )
