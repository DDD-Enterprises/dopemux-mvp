"""
FastAPI routes for ML Predictions API
Provides cognitive load prediction endpoints with async handling and performance monitoring
"""

import time
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .schemas import (
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    ErrorResponse
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from lstm_cognitive_predictor import LSTMCognitivePredictor

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Global model instance (will be loaded on startup)
_predictor: Optional[LSTMCognitivePredictor] = None


def get_predictor() -> LSTMCognitivePredictor:
    """Get the global predictor instance."""
    global _predictor
    if _predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Prediction model not loaded"
        )
    return _predictor


@router.post(
    "/predict/cognitive-load",
    response_model=PredictionResponse,
    summary="Predict cognitive load",
    description="Predict cognitive load for the next 15 minutes based on historical data"
)
async def predict_cognitive_load(
    request: PredictionRequest,
    req: Request
) -> PredictionResponse:
    """
    Predict cognitive load using LSTM model.

    - **user_id**: User identifier
    - **historical_data**: List of cognitive metrics (1-120 data points)
    - **context**: Optional context information
    """
    start_time = time.time()

    try:
        # Get predictor instance
        predictor = get_predictor()

        # Validate request data
        if len(request.historical_data) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient historical data: minimum 10 data points required"
            )

        # Prepare data for prediction
        # Convert Pydantic models to format expected by predictor
        historical_data = []
        for metric in request.historical_data:
            data_point = {
                'timestamp': metric.timestamp,
                'energy_level': metric.energy_level,
                'attention_focus': metric.attention_focus,
                'cognitive_load': metric.cognitive_load,
                'task_complexity': metric.task_complexity,
                'context_switches': metric.context_switches,
                'break_frequency': metric.break_frequency,
                'session_duration': metric.session_duration,
                'interruptions': metric.interruptions
            }
            historical_data.append(data_point)

        # Run prediction
        prediction_result = await predictor.predict_next_load_async(
            historical_data=historical_data,
            context=request.context
        )

        # Extract results
        prediction = prediction_result.get('prediction', 0.5)
        confidence = prediction_result.get('confidence', 0.5)
        recommended_actions = prediction_result.get('recommended_actions', [])

        # Ensure prediction is within bounds
        prediction = max(0.0, min(1.0, prediction))
        confidence = max(0.0, min(1.0, confidence))

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Log performance
        logger.info(
            f"Prediction completed for user {request.user_id} in {processing_time_ms:.2f}ms "
            f"(prediction: {prediction:.3f}, confidence: {confidence:.3f})"
        )

        # Check performance requirement (<100ms)
        if processing_time_ms > 100:
            logger.warning(
                f"Performance requirement violated: {processing_time_ms:.2f}ms > 100ms"
            )

        return PredictionResponse(
            prediction=prediction,
            confidence=confidence,
            recommended_actions=recommended_actions,
            timestamp=datetime.utcnow(),
            processing_time_ms=processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        # Calculate processing time even for errors
        processing_time_ms = (time.time() - start_time) * 1000

        logger.error(
            f"Prediction failed for user {request.user_id}: {str(e)} "
            f"({processing_time_ms:.2f}ms)"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health and model status"
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    global _predictor

    cache_status = "unknown"
    try:
        # Check if predictor is loaded
        if _predictor is not None:
            # Could add more detailed health checks here
            cache_status = "operational"
        else:
            cache_status = "model_not_loaded"
    except Exception as e:
        cache_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if _predictor is not None else "degraded",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        model_loaded=_predictor is not None,
        cache_status=cache_status
    )


@router.get(
    "/metrics",
    summary="Performance metrics",
    description="Get API performance metrics"
)
async def get_metrics():
    """Get performance metrics (for monitoring)."""
    # This would integrate with a metrics collection system
    # For now, return basic info
    return {
        "uptime": "unknown",  # Would track actual uptime
        "total_predictions": "unknown",  # Would track via metrics system
        "average_response_time": "unknown",  # Would calculate from metrics
        "error_rate": "unknown",  # Would calculate from metrics
        "timestamp": datetime.utcnow()
    }


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=exc.detail,
            timestamp=datetime.utcnow(),
            request_id=getattr(request, 'headers', {}).get('x-request-id')
        ).dict()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An internal error occurred",
            timestamp=datetime.utcnow(),
            request_id=getattr(request, 'headers', {}).get('x-request-id')
        ).dict()
    )