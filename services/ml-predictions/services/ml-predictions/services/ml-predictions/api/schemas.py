"""
Pydantic schemas for ML Predictions API
Defines request/response models for cognitive load prediction endpoints
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class CognitiveMetric(BaseModel):
    """Cognitive metric data point."""
    timestamp: datetime
    user_id: str
    energy_level: float = Field(..., ge=0.0, le=1.0, description="Energy level (0.0-1.0)")
    attention_focus: float = Field(..., ge=0.0, le=1.0, description="Attention focus (0.0-1.0)")
    cognitive_load: float = Field(..., ge=0.0, le=1.0, description="Current cognitive load (0.0-1.0)")
    task_complexity: float = Field(..., ge=0.0, le=1.0, description="Current task complexity (0.0-1.0)")
    context_switches: int = Field(..., ge=0, description="Context switches in last hour")
    break_frequency: int = Field(..., ge=0, description="Breaks taken in last hour")
    session_duration: int = Field(..., ge=0, description="Current session duration in minutes")
    interruptions: int = Field(..., ge=0, description="Interruptions in last hour")


class PredictionRequest(BaseModel):
    """Request model for cognitive load prediction."""
    user_id: str = Field(..., description="User identifier")
    historical_data: List[CognitiveMetric] = Field(
        ..., min_items=1, max_items=120,
        description="Historical cognitive metrics (1-120 data points, typically 60 minutes)"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Optional context (current task, environment, etc.)"
    )

    @validator('historical_data')
    def validate_historical_data(cls, v):
        """Ensure historical data is chronologically ordered."""
        if len(v) > 1:
            timestamps = [metric.timestamp for metric in v]
            if timestamps != sorted(timestamps):
                raise ValueError("Historical data must be chronologically ordered by timestamp")
        return v


class PredictionResponse(BaseModel):
    """Response model for cognitive load prediction."""
    prediction: float = Field(
        ..., ge=0.0, le=1.0,
        description="Predicted cognitive load (0.0-1.0)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Prediction confidence (0.0-1.0)"
    )
    recommended_actions: List[str] = Field(
        ..., description="Recommended actions based on prediction"
    )
    timestamp: datetime = Field(
        ..., description="Prediction timestamp"
    )
    processing_time_ms: float = Field(
        ..., description="API processing time in milliseconds"
    )


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime
    version: str
    model_loaded: bool
    cache_status: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime
    request_id: Optional[str] = None