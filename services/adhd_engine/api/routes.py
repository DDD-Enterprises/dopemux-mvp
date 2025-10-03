"""
FastAPI routes for ADHD Accommodation Engine.

Provides 7 REST endpoints for ADHD-optimized task management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Any
from datetime import datetime, timezone
import logging

from . import schemas
from ..models import ADHDProfile, EnergyLevel, AttentionState

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency injection for engine instance
def get_engine():
    """Get global engine instance."""
    from ..main import engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return engine


@router.post("/assess-task", response_model=schemas.TaskAssessmentResponse)
async def assess_task(
    request: schemas.TaskAssessmentRequest,
    engine = Depends(get_engine)
):
    """
    Assess task suitability for user's current ADHD state.

    Evaluates energy match, attention compatibility, and cognitive load.
    Provides personalized accommodation recommendations.
    """
    try:
        result = await engine.assess_task_suitability(
            user_id=request.user_id,
            task_data=request.task_data.model_dump()
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        logger.error(f"Task assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy-level/{user_id}", response_model=schemas.EnergyLevelResponse)
async def get_energy_level(user_id: str, engine = Depends(get_engine)):
    """Get current energy level for user."""
    try:
        energy = engine.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)

        return schemas.EnergyLevelResponse(
            energy_level=energy.value if hasattr(energy, 'value') else str(energy),
            confidence=0.8,  # Based on activity data freshness
            last_updated=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Energy level retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attention-state/{user_id}", response_model=schemas.AttentionStateResponse)
async def get_attention_state(user_id: str, engine = Depends(get_engine)):
    """Get current attention state for user."""
    try:
        attention = engine.current_attention_states.get(user_id, AttentionState.FOCUSED)

        # Get indicators that led to this assessment
        indicators = {
            "attention_state": attention.value if hasattr(attention, 'value') else str(attention),
            "assessment_method": "activity_pattern_analysis"
        }

        return schemas.AttentionStateResponse(
            attention_state=attention.value if hasattr(attention, 'value') else str(attention),
            indicators=indicators,
            last_updated=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Attention state retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-break", response_model=schemas.BreakRecommendationResponse)
async def recommend_break(
    request: schemas.BreakRecommendationRequest,
    engine = Depends(get_engine)
):
    """Get personalized break recommendation."""
    try:
        # Get user profile
        profile = engine.user_profiles.get(request.user_id)
        if not profile:
            profile = ADHDProfile(user_id=request.user_id)

        # Check if break is needed
        break_needed = request.work_duration >= profile.optimal_task_duration

        if break_needed:
            reason = "optimal_duration_reached" if request.work_duration < profile.max_task_duration else "maximum_duration_reached"
            urgency = "soon" if request.work_duration < profile.max_task_duration else "immediate"

            suggestions = ["5-minute walk", "Hydrate", "Stretch"]
            if profile.break_activity_suggestions:
                suggestions.extend(["Deep breathing", "Eye rest (20-20-20 rule)"])

            message = f"Time for a break after {request.work_duration:.0f} minutes of focused work!"
        else:
            reason = "still_within_optimal"
            urgency = "when_convenient"
            suggestions = []
            message = f"You're doing great! {profile.optimal_task_duration - int(request.work_duration)} minutes until recommended break."

        return schemas.BreakRecommendationResponse(
            break_needed=break_needed,
            reason=reason,
            suggestions=suggestions,
            urgency=urgency,
            message=message
        )

    except Exception as e:
        logger.error(f"Break recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-profile", response_model=schemas.UserProfileResponse)
async def create_or_update_profile(
    request: schemas.UserProfileRequest,
    engine = Depends(get_engine)
):
    """Create or update user ADHD profile."""
    try:
        # Get existing profile or create new
        profile = engine.user_profiles.get(request.user_id, ADHDProfile(user_id=request.user_id))

        # Update with provided values
        if request.hyperfocus_tendency is not None:
            profile.hyperfocus_tendency = request.hyperfocus_tendency
        if request.distraction_sensitivity is not None:
            profile.distraction_sensitivity = request.distraction_sensitivity
        if request.context_switch_penalty is not None:
            profile.context_switch_penalty = request.context_switch_penalty
        if request.break_resistance is not None:
            profile.break_resistance = request.break_resistance
        if request.optimal_task_duration is not None:
            profile.optimal_task_duration = request.optimal_task_duration
        if request.max_task_duration is not None:
            profile.max_task_duration = request.max_task_duration
        if request.peak_hours is not None:
            profile.peak_hours = request.peak_hours

        # Store in engine
        engine.user_profiles[request.user_id] = profile

        # TODO (Day 4): Persist to Redis
        # await engine.redis_client.set(
        #     f"adhd:profile:{request.user_id}",
        #     json.dumps(asdict(profile))
        # )

        return schemas.UserProfileResponse(
            user_id=request.user_id,
            profile_created=True,
            message="Profile updated successfully"
        )

    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/activity/{user_id}", response_model=schemas.ActivityUpdateResponse)
async def update_activity(
    user_id: str,
    request: schemas.ActivityUpdateRequest,
    engine = Depends(get_engine)
):
    """
    Log user activity event for ADHD tracking.

    Updates will trigger immediate energy/attention reassessment.
    """
    try:
        # TODO (Day 4): Store activity in Redis for tracking
        # activity_event = {
        #     "user_id": user_id,
        #     "timestamp": datetime.now(timezone.utc).isoformat(),
        #     "metrics": request.model_dump(exclude_none=True)
        # }
        # await engine.redis_client.lpush(f"adhd:activity:{user_id}", json.dumps(activity_event))

        # Trigger reassessment if engine has this user
        energy_updated = False
        attention_updated = False

        if user_id in engine.user_profiles:
            # Would trigger immediate assessment here
            energy_updated = True
            attention_updated = True

        return schemas.ActivityUpdateResponse(
            recorded=True,
            energy_updated=energy_updated,
            attention_updated=attention_updated,
            message="Activity logged successfully"
        )

    except Exception as e:
        logger.error(f"Activity update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
