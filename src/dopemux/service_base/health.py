"""Health check endpoints for services."""
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def mark_phase(app, name: str, status: str, detail: Optional[str] = None) -> None:
    """Mark a startup phase with timestamp.
    
    Args:
        app: FastAPI app instance
        name: Phase name (e.g., "postgres_probe", "redis_init")
        status: Phase status - must be one of: "start", "ok", "fail"
        detail: Optional detail string (e.g., error class name)
    
    Stores phase in app.state.health_timeline as:
        {"t": <unix_ts>, "phase": name, "status": status, "detail": <optional>}
    
    Also logs the phase transition.
    """
    if status not in ("start", "ok", "fail"):
        logger.warning(f"Invalid phase status: {status}, expected start|ok|fail")
        return
    
    # Initialize timeline if not present
    if not hasattr(app.state, "health_timeline"):
        app.state.health_timeline = []
    
    # Create phase entry
    phase_entry = {
        "t": time.time(),
        "phase": name,
        "status": status
    }
    
    if detail:
        # Sanitize detail to avoid secret leakage
        if "://" in detail and "@" in detail:
            detail = "<REDACTED_URL>"
        phase_entry["detail"] = detail
    
    # Append to timeline (keep last 20 entries)
    app.state.health_timeline.append(phase_entry)
    if len(app.state.health_timeline) > 20:
        app.state.health_timeline = app.state.health_timeline[-20:]
    
    # Log phase transition
    service_name = getattr(app.state, "service_name", "unknown")
    log_msg = f"PHASE service={service_name} phase={name} status={status} t={phase_entry['t']:.3f}"
    if detail:
        log_msg += f" detail={detail}"
    logger.info(log_msg)


class HealthResponse(BaseModel):
    """Standard health check response."""
    
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    ts: str = Field(..., description="Current timestamp (ISO 8601)")
    version: Optional[str] = Field(None, description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    
    model_config = {"extra": "allow"}  # Allow additional fields from custom checks


def create_health_router(
    service_name: str,
    version: Optional[str] = None,
    custom_checks: Optional[Dict[str, Any]] = None
) -> APIRouter:
    """Create a health check router for a service.
    
    Args:
        service_name: Name of the service
        version: Optional service version
        custom_checks: Optional dict of custom health check data
        
    Returns:
        Configured APIRouter with /health endpoint
        
    Example:
        router = create_health_router("my-service", version="1.0.0")
        app.include_router(router)
    """
    router = APIRouter(tags=["Health"])
    
    @router.get("/health", response_model=HealthResponse)
    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint.
        
        Returns service status and basic metadata.
        Returns 200 OK only if service initialization completed successfully.
        Returns 503 Service Unavailable if service is not ready.
        
        Optional: Set HEALTH_DETAIL=1 to include startup timeline.
        """
        # Check if service is ready (initialized successfully)
        is_ready = getattr(request.app.state, "ready", False)
        
        if not is_ready:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "service": service_name,
                    "ts": datetime.utcnow().isoformat(),
                    "reason": "Service initialization not complete"
                }
            )
        
        response_data = {
            "status": "ok",
            "service": service_name,
            "ts": datetime.utcnow().isoformat(),
        }
        
        if version:
            response_data["version"] = version
        
        # Add custom health check data if provided
        if custom_checks:
            response_data.update(custom_checks)
        
        # Optional: Include timeline when HEALTH_DETAIL=1
        if os.environ.get("HEALTH_DETAIL") == "1":
            response_data["ready"] = is_ready
            
            # Include timeline if available
            if hasattr(request.app.state, "health_timeline"):
                response_data["timeline"] = request.app.state.health_timeline
            
            # Include started_at if metrics available
            if hasattr(request.app.state, "metrics") and hasattr(request.app.state.metrics, "_started_at"):
                if request.app.state.metrics._started_at:
                    response_data["started_at"] = request.app.state.metrics._started_at
        
        logger.debug(f"Health check for {service_name}: OK")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
    
    return router
