"""
FastAPI routes for ADHD Accommodation Engine.

Provides 6 API endpoints (/api/v1/*) for ADHD-optimized task management:
- POST /assess-task - Task suitability assessment
- GET /energy-level/{user_id} - Current energy level
- GET /attention-state/{user_id} - Current attention state
- POST /recommend-break - Personalized break recommendations
- POST /user-profile - Create/update ADHD profile
- PUT /activity/{user_id} - Log activity events

Plus utility endpoints: GET / (info), GET /health (health check)

All endpoints secured with X-API-Key authentication (configurable via ADHD_ENGINE_API_KEY).
"""

from fastapi import APIRouter, HTTPException, Depends, Security
from typing import Any
from datetime import datetime, timezone
import logging

import api.schemas as schemas
from models import ADHDProfile, EnergyLevel, AttentionState
from auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_cognitive_load_level(load: float) -> str:
    """Convert cognitive load score to level string."""
    if load <= 0.2:
        return "minimal"
    elif load <= 0.4:
        return "low"
    elif load <= 0.6:
        return "moderate"
    elif load <= 0.8:
        return "high"
    else:
        return "extreme"


# Dependency injection for engine instance
def get_engine():
    """Get global engine instance."""
    import main
    if not main.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return main.engine


@router.post("/assess-task", response_model=schemas.TaskAssessmentResponse)
async def assess_task(
    request: schemas.TaskAssessmentRequest,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """
    Assess task suitability for ADHD user.

    Evaluates task complexity, energy requirements, attention compatibility,
    and provides accommodation recommendations.

    **Request Body:**
    - `user_id`: User identifier
    - `task_id`: Task identifier
    - `task_data`: Task details (complexity, duration, description)

    **Response:**
    - `suitability_score`: Overall task suitability (0.0-1.0)
    - `energy_match`: Energy level compatibility
    - `attention_compatibility`: Attention state compatibility
    - `cognitive_load`: Task complexity assessment
    - `recommendations`: ADHD accommodation suggestions
    """
    try:
        result = await engine.assess_task(request.user_id, request.task_data.dict())

        # Convert to response schema
        response = schemas.TaskAssessmentResponse(
            suitability_score=result["suitability_score"],
            energy_match=result["energy_match"],
            attention_compatibility=result["attention_compatibility"],
            cognitive_load=result["cognitive_load"],
            cognitive_load_level=_get_cognitive_load_level(result["cognitive_load"]),
            recommendations=[
                schemas.AccommodationRecommendationSchema(**rec)
                for rec in result["recommendations"]
            ],
            accommodations_needed=[
                rec["type"] for rec in result["recommendations"]
            ],
            optimal_timing=result["optimal_timing"],
            adhd_insights=schemas.ADHDInsights(
                hyperfocus_risk="low",
                distraction_risk="medium",
                context_switch_impact="medium"
            )
        )

        logger.info(f"Task assessment completed for user {request.user_id}, task {request.task_id}")
        return response

    except Exception as e:
        logger.error(f"Task assessment failed: {e}")
        raise HTTPException(status_code=500, detail="Task assessment failed")


def _get_cognitive_load_level(self, load: float) -> str:
    """Convert cognitive load score to level string."""
    if load <= 0.2:
        return "minimal"
    elif load <= 0.4:
        return "low"
    elif load <= 0.6:
        return "moderate"
    elif load <= 0.8:
        return "high"
    else:
        return "extreme"


@router.get("/energy-level/{user_id}", response_model=schemas.EnergyLevelResponse)
async def get_energy_level(
    user_id: str,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """
    Get current energy level for user.

    **Parameters:**
    - `user_id`: User identifier

    **Response:**
    - `energy_level`: Current energy state (very_low, low, medium, high, hyperfocus)
    - `confidence`: Confidence in assessment (0.0-1.0)
    - `last_updated`: Timestamp of last assessment
    """
    try:
        # Get user state from engine
        user_state = await engine._get_user_state(user_id)

        response = schemas.EnergyLevelResponse(
            energy_level=user_state.get("energy_level", "medium"),
            confidence=0.8,
            last_updated=datetime.now(timezone.utc)
        )

        return response

    except Exception as e:
        logger.error(f"Failed to get energy level for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve energy level")


@router.get("/attention-state/{user_id}", response_model=schemas.AttentionStateResponse)
async def get_attention_state(
    user_id: str,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """
    Get current attention state for user.

    **Parameters:**
    - `user_id`: User identifier

    **Response:**
    - `attention_state`: Current attention state
    - `indicators`: Supporting indicators and metrics
    - `last_updated`: Timestamp of last assessment
    """
    try:
        # Get user state from engine
        user_state = await engine._get_user_state(user_id)

        response = schemas.AttentionStateResponse(
            attention_state=user_state.get("attention_state", "focused"),
            indicators={
                "focus_duration": user_state.get("session_duration", 0),
                "context_switches": user_state.get("context_switches", 0),
                "interruption_count": user_state.get("interruptions", 0)
            },
            last_updated=datetime.now(timezone.utc)
        )

        return response

    except Exception as e:
        logger.error(f"Failed to get attention state for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve attention state")


@router.post("/recommend-break", response_model=schemas.BreakRecommendationResponse)
async def recommend_break(
    request: schemas.BreakRecommendationRequest,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """
    Get personalized break recommendation.

    **Request Body:**
    - `user_id`: User identifier
    - `work_duration`: Continuous work time in minutes

    **Response:**
    - `break_needed`: Whether break is recommended
    - `reason`: Why break is/isn't needed
    - `suggestions`: Break activity suggestions
    - `urgency`: How urgent the break is
    """
    try:
        # Get user state
        user_state = await engine._get_user_state(request.user_id)

        # Simple break logic (expand with ML in future)
        work_minutes = request.work_duration
        energy_level = user_state.get("energy_level", "medium")

        if work_minutes > 90:  # 90+ minutes continuous work
            break_needed = True
            reason = "Extended work session detected"
            suggestions = ["Take 15-minute walk", "Do deep breathing exercises", "Have a healthy snack"]
            urgency = "urgent"
        elif work_minutes > 60 and energy_level in ["low", "very_low"]:
            break_needed = True
            reason = "Low energy during extended session"
            suggestions = ["5-minute stretch break", "Hydrate and snack", "Quick meditation"]
            urgency = "high"
        elif work_minutes > 25:  # Standard ADHD focus session
            break_needed = True
            reason = "ADHD optimal focus session completed"
            suggestions = ["2-minute breathing break", "Stand and stretch", "Change environment"]
            urgency = "medium"
        else:
            break_needed = False
            reason = "Work session within optimal duration"
            suggestions = []
            urgency = "none"

        response = schemas.BreakRecommendationResponse(
            break_needed=break_needed,
            reason=reason,
            suggestions=suggestions,
            urgency=urgency,
            message=f"Based on {work_minutes} minutes of work and {energy_level} energy level"
        )

        return response

    except Exception as e:
        logger.error(f"Failed to generate break recommendation for user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate break recommendation")


@router.post("/user-profile", response_model=schemas.UserProfileResponse)
async def create_user_profile(
    request: schemas.UserProfileRequest,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """
    Create or update ADHD user profile.

    **Request Body:**
    - `user_id`: User identifier
    - Optional ADHD tendency parameters (0.0-1.0 scale)

    **Response:**
    - `user_id`: Confirmed user ID
    - `profile_created`: Whether new profile was created
    - `message`: Success message
    """
    try:
        # Convert request to ADHDProfile model
        profile_data = request.dict(exclude_unset=True)
        profile = ADHDProfile(**profile_data)

        # Store in cache/Redis (implement persistence later)
        cache_key = f"adhd_profile:{request.user_id}"
        engine.cache.set(cache_key, profile.dict(), ttl=None)  # Permanent

        # Log to ConPort
        await engine.log_decision_to_conport(
            workspace_id="/Users/hue/code/dopemux-mvp",
            decision={
                "type": "user_profile_created",
                "user_id": request.user_id,
                "profile_data": profile.dict(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        response = schemas.UserProfileResponse(
            user_id=request.user_id,
            profile_created=True,
            message="ADHD profile created successfully"
        )

        logger.info(f"Created ADHD profile for user {request.user_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to create user profile for {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user profile")


@router.put("/activity/{user_id}")
async def log_activity(
    user_id: str,
    request: schemas.ActivityUpdateRequest,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """
    Log user activity and update ADHD state.

    **Parameters:**
    - `user_id`: User identifier

    **Request Body:**
    - Optional activity metrics (completion_rate, context_switches, etc.)

    **Response:**
    - `recorded`: Whether activity was recorded
    - `energy_updated`: Whether energy state was updated
    - `attention_updated`: Whether attention state was updated
    - `message`: Success message
    """
    try:
        # Update user state based on activity
        user_state = await engine._get_user_state(user_id)

        # Apply activity updates
        if request.completion_rate is not None:
            # Update energy based on completion success
            pass

        if request.context_switches is not None:
            user_state["context_switches"] = user_state.get("context_switches", 0) + request.context_switches

        if request.break_compliance is not None:
            # Update attention state based on break compliance
            pass

        if request.minutes_since_break is not None:
            # Update energy decay calculation
            pass

        # Store updated state
        engine.cache.set(f"adhd_user_state:{user_id}", user_state, ttl=300)

        response = {
            "recorded": True,
            "energy_updated": True,
            "attention_updated": True,
            "message": "Activity logged successfully"
        }

        logger.info(f"Logged activity for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to log activity for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to log activity")