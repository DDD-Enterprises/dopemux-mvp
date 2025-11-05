"""
Pydantic schemas for ADHD Accommodation Engine API.

Defines request/response models for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Task Assessment Schemas
class TaskAssessmentRequest(BaseModel):
    """Request model for task assessment."""
    task_description: str = Field(..., description="Description of the task to assess")
    estimated_hours: float = Field(..., ge=0, description="Estimated hours to complete the task")
    technologies: List[str] = Field(default_factory=list, description="Technologies involved")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")


class AccommodationRecommendationSchema(BaseModel):
    """Schema for accommodation recommendations."""
    accommodation_type: str = Field(..., description="Type of accommodation recommended")
    description: str = Field(..., description="Description of the accommodation")
    priority: str = Field(..., description="Priority level (low, medium, high)")


class ADHDInsights(BaseModel):
    """Schema for ADHD-specific insights."""
    attention_span_needed: str = Field(..., description="Required attention span")
    energy_requirement: str = Field(..., description="Energy level required")
    break_frequency: str = Field(..., description="Recommended break frequency")


class TaskAssessmentResponse(BaseModel):
    """Response model for task assessment."""
    complexity_score: float = Field(..., ge=0, le=1, description="Cognitive complexity score")
    cognitive_load: str = Field(..., description="Cognitive load level")
    recommended_chunks: int = Field(..., ge=1, description="Recommended task chunks")
    break_frequency: str = Field(..., description="Recommended break frequency")
    energy_requirement: str = Field(..., description="Energy requirement level")
    attention_span_needed: str = Field(..., description="Attention span needed")
    accommodations: List[AccommodationRecommendationSchema] = Field(default_factory=list)
    adhd_insights: ADHDInsights


# Energy Level Schemas
class EnergyLevelResponse(BaseModel):
    """Response model for energy level queries."""
    user_id: str = Field(..., description="User identifier")
    energy_level: float = Field(..., ge=0, le=1, description="Current energy level")
    timestamp: datetime = Field(..., description="Timestamp of measurement")
    trend: str = Field(..., description="Energy trend (increasing, decreasing, stable)")


# Attention State Schemas
class AttentionStateResponse(BaseModel):
    """Response model for attention state queries."""
    user_id: str = Field(..., description="User identifier")
    attention_state: str = Field(..., description="Current attention state")
    focus_level: float = Field(..., ge=0, le=1, description="Current focus level")
    distraction_level: float = Field(..., ge=0, le=1, description="Current distraction level")
    timestamp: datetime = Field(..., description="Timestamp of measurement")
    recommendations: List[str] = Field(default_factory=list, description="Personalized recommendations")


# Break Recommendation Schemas
class BreakRecommendationRequest(BaseModel):
    """Request model for break recommendations."""
    user_id: str = Field(..., description="User identifier")
    current_task: Optional[str] = Field(None, description="Current task being worked on")
    time_since_last_break: int = Field(..., ge=0, description="Minutes since last break")


class BreakRecommendationResponse(BaseModel):
    """Response model for break recommendations."""
    should_take_break: bool = Field(..., description="Whether a break is recommended")
    recommended_duration: int = Field(..., ge=0, description="Recommended break duration in minutes")
    reason: str = Field(..., description="Reason for the recommendation")
    break_type: str = Field(..., description="Type of break recommended")
    next_check_in: int = Field(..., ge=0, description="Minutes until next check")


# User Profile Schemas
class UserProfileRequest(BaseModel):
    """Request model for user profile creation/updates."""
    user_id: str = Field(..., description="User identifier")
    adhd_type: Optional[str] = Field(None, description="ADHD subtype or presentation")
    work_style: Optional[str] = Field(None, description="Preferred work style")
    energy_patterns: Optional[Dict[str, Any]] = Field(None, description="Energy pattern preferences")
    attention_characteristics: Optional[Dict[str, Any]] = Field(None, description="Attention characteristics")
    accommodation_preferences: Optional[List[str]] = Field(None, description="Preferred accommodations")


class UserProfileResponse(BaseModel):
    """Response model for user profile operations."""
    user_id: str = Field(..., description="User identifier")
    profile_created: bool = Field(..., description="Whether profile was created or updated")
    message: str = Field(..., description="Operation result message")


# Activity Update Schemas
class ActivityUpdateRequest(BaseModel):
    """Request model for activity updates."""
    user_id: str = Field(..., description="User identifier")
    activity_type: str = Field(..., description="Type of activity")
    duration: int = Field(..., ge=0, description="Activity duration in minutes")
    context: Optional[Dict[str, Any]] = Field(None, description="Activity context")
    cognitive_load: Optional[float] = Field(None, ge=0, le=1, description="Perceived cognitive load")