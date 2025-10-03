"""
Pydantic schemas for ADHD Engine API.

Request/response models for all 7 REST endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Task Assessment

class TaskData(BaseModel):
    """Task data for ADHD assessment."""
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="Task complexity (0.0-1.0)")
    estimated_minutes: int = Field(..., gt=0, description="Estimated duration in minutes")
    description: str = Field(..., min_length=1, description="Task description")
    dependencies: List[str] = Field(default_factory=list, description="List of dependency task IDs")


class TaskAssessmentRequest(BaseModel):
    """Request to assess task suitability."""
    user_id: str = Field(..., min_length=1)
    task_id: str = Field(..., min_length=1)
    task_data: TaskData


class AccommodationRecommendationSchema(BaseModel):
    """ADHD accommodation recommendation."""
    accommodation_type: str
    urgency: str  # immediate, soon, when_convenient
    message: str
    action_required: bool
    suggested_actions: List[str]
    cognitive_benefit: str
    implementation_effort: str  # minimal, low, moderate, high


class ADHDInsights(BaseModel):
    """ADHD-specific insights about task."""
    hyperfocus_risk: str  # low, medium, high
    distraction_risk: str  # low, medium, high
    context_switch_impact: str  # low, medium, high


class TaskAssessmentResponse(BaseModel):
    """Response from task suitability assessment."""
    suitability_score: float = Field(..., ge=0.0, le=1.0)
    energy_match: float = Field(..., ge=0.0, le=1.0)
    attention_compatibility: float = Field(..., ge=0.0, le=1.0)
    cognitive_load: float = Field(..., ge=0.0, le=1.0)
    cognitive_load_level: str  # minimal, low, moderate, high, extreme
    recommendations: List[AccommodationRecommendationSchema]
    accommodations_needed: List[str]
    optimal_timing: Dict[str, Any]
    adhd_insights: ADHDInsights


# Energy & Attention State

class EnergyLevelResponse(BaseModel):
    """Current energy level for user."""
    energy_level: str  # very_low, low, medium, high, hyperfocus
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    last_updated: datetime


class AttentionStateResponse(BaseModel):
    """Current attention state for user."""
    attention_state: str  # scattered, transitioning, focused, hyperfocused, overwhelmed
    indicators: Dict[str, Any]
    last_updated: datetime


# Break Recommendation

class BreakRecommendationRequest(BaseModel):
    """Request for break recommendation."""
    user_id: str
    work_duration: float = Field(..., gt=0, description="Minutes of continuous work")


class BreakRecommendationResponse(BaseModel):
    """Break recommendation response."""
    break_needed: bool
    reason: str
    suggestions: List[str]
    urgency: str
    message: str


# User Profile

class UserProfileRequest(BaseModel):
    """Create or update user ADHD profile."""
    user_id: str
    hyperfocus_tendency: Optional[float] = Field(None, ge=0.0, le=1.0)
    distraction_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    context_switch_penalty: Optional[float] = Field(None, ge=0.0, le=1.0)
    break_resistance: Optional[float] = Field(None, ge=0.0, le=1.0)
    optimal_task_duration: Optional[int] = Field(None, gt=0, le=120)
    max_task_duration: Optional[int] = Field(None, gt=0, le=180)
    peak_hours: Optional[List[int]] = Field(None, description="Hours 0-23")


class UserProfileResponse(BaseModel):
    """User profile response."""
    user_id: str
    profile_created: bool
    message: str


# Activity Update

class ActivityUpdateRequest(BaseModel):
    """Log user activity metrics."""
    user_id: str
    completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    context_switches: Optional[int] = Field(None, ge=0)
    break_compliance: Optional[float] = Field(None, ge=0.0, le=1.0)
    minutes_since_break: Optional[int] = Field(None, ge=0)


class ActivityUpdateResponse(BaseModel):
    """Activity update response."""
    recorded: bool
    energy_updated: bool
    attention_updated: bool
    message: str


# Health Check

class ComponentStatus(BaseModel):
    """Status of engine component."""
    redis_persistence: str
    monitors_active: str
    user_profiles: int


class HealthResponse(BaseModel):
    """Health check response."""
    overall_status: str
    components: ComponentStatus
    accommodation_stats: Dict[str, int]
    current_state: Dict[str, Any]
    effectiveness_metrics: Dict[str, Any]
