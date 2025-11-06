"""
ML Predictions API - Main FastAPI Application
Real-time cognitive load prediction service for ADHD optimization
"""

import logging
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from api.routes import router
from api.schemas import (
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    ErrorResponse
)
from lstm_cognitive_predictor import LSTMCognitivePredictor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
_predictor: LSTMCognitivePredictor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ML Predictions API...")
    await startup_event()
    yield
    # Shutdown
    logger.info("Shutting down ML Predictions API...")


async def startup_event():
    """Initialize services on startup."""
    global _predictor

    try:
        # Initialize the LSTM predictor
        _predictor = LSTMCognitivePredictor()
        logger.info("LSTM Cognitive Predictor initialized successfully")

        # Try to load existing model (for development, we'll initialize fresh)
        # In production, this would load a pre-trained model
        logger.info("Model ready for predictions")

    except Exception as e:
        logger.error(f"Failed to initialize predictor: {str(e)}")
        # Don't raise - allow service to start without model
        _predictor = None


async def shutdown_event():
    """Clean up resources on shutdown."""
    pass


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Dopemux ML Predictions API",
        description="Real-time cognitive load prediction for ADHD-optimized development",
        version="1.0.0",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add performance monitoring middleware
    @app.middleware("http")
    async def add_performance_headers(request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log slow requests
        if process_time > 0.1:  # > 100ms
            logger.warning(
                f"Slow request: {request.method} {request.url} "
                f"took {process_time:.3f}s"
            )

        return response

    # Include API routes
    app.include_router(router, prefix="/api/v1", tags=["predictions"])

    # Error handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "timestamp": datetime.utcnow(),
                "request_id": getattr(request, 'headers', {}).get('x-request-id')
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An internal error occurred",
                "timestamp": datetime.utcnow(),
                "request_id": getattr(request, 'headers', {}).get('x-request-id')
            }
        )

    # Root endpoint
    @app.get("/")
    async def root():
        """API root endpoint."""
        return {
            "message": "Dopemux ML Predictions API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/v1/health"
        }

    return app


# Create the FastAPI application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )