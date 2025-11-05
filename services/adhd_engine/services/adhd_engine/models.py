"""
Pydantic models for ADHD Accommodation Engine data structures.

Defines data models for user profiles, energy levels, attention states,
and internal engine state.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class ADHDProfile(BaseModel):
    """
    ADHD user profile with accommodation preferences and tendencies.
    """
    user_id: str
    hyperfocus_tendency: Optional[float] = Field(None, ge=0.0, le=1.0)
    distraction_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    context_switch_penalty: Optional[float] = Field(None, ge=0.0, le=1.0)
    break_resistance: Optional[float] = Field(None, ge=0.0, le=1.0)
    optimal_task_duration: Optional[int] = Field(None, gt=0, le=120)
    max_task_duration: Optional[int] = Field(None, gt=0, le=180)
    peak_hours: Optional[list[int]] = Field(None, description="Hours 0-23")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EnergyLevel(BaseModel):
    """
    Current energy level assessment for a user.
    """
    user_id: str
    level: str = Field(..., description="very_low, low, medium, high, hyperfocus")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    last_updated: datetime
    factors: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AttentionState(BaseModel):
    """
    Current attention state assessment for a user.
    """
    user_id: str
    state: str = Field(..., description="scattered, transitioning, focused, hyperfocused, overwhelmed")
    indicators: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class CognitiveLoad(BaseModel):
    """
    Current cognitive load assessment for a user.
    """
    user_id: str
    load_level: str = Field(..., description="minimal, low, moderate, high, extreme")
    load_score: float = Field(..., ge=0.0, le=1.0)
    factors: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime


class BreakRecommendation(BaseModel):
    """
    Break recommendation with timing and rationale.
    """
    user_id: str
    needed: bool
    reason: str
    suggestions: list[str]
    urgency: str = Field(..., description="low, medium, high, urgent")
    optimal_duration: int = Field(..., gt=0, le=60)  # minutes
    generated_at: datetime


class MonitorState(BaseModel):
    """
    Internal state for background monitors.
    """
    monitor_name: str
    is_running: bool = False
    last_check: Optional[datetime] = None
    check_interval: int = Field(..., gt=0)  # seconds
    error_count: int = Field(default=0, ge=0)
    last_error: Optional[str] = None


class EngineState(BaseModel):
    """
    Overall engine state for health monitoring.
    """
    initialized: bool = False
    monitors: Dict[str, MonitorState] = Field(default_factory=dict)
    redis_connected: bool = False
    conport_connected: bool = False
    last_health_check: Optional[datetime] = None
    uptime_seconds: int = Field(default=0, ge=0)