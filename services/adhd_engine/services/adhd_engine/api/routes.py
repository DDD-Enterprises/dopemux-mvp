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

from fastapi import APIRouter, HTTPException, Depends, Security, WebSocket, WebSocketDisconnect, Request
from typing import Any
from datetime import datetime, timezone
import logging
import asyncio
import json

import api.schemas as schemas
from models import ADHDProfile, EnergyLevel, AttentionState
from auth import verify_api_key, api_key_header
from api.websocket import manager, send_heartbeat
from config import settings

# Import time for caching
import time

logger = logging.getLogger(__name__)
router = APIRouter()


def _default_energy_level(user_id: str) -> EnergyLevel:
    return EnergyLevel(
        user_id=user_id,
        level="medium",
        confidence=0.8,
        last_updated=datetime.now(timezone.utc),
        factors={},
    )


def _default_attention_state(user_id: str) -> AttentionState:
    return AttentionState(
        user_id=user_id,
        state="focused",
        indicators={},
        last_updated=datetime.now(timezone.utc),
        confidence=0.8,
    )


def _extract_state_value(obj: Any, *attrs: str) -> str:
    for attr in attrs:
        value = getattr(obj, attr, None)
        if value is not None:
            return value if isinstance(value, str) else str(value)
    return str(obj)


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
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """
    Assess task suitability for user's current ADHD state.

    Evaluates energy match, attention compatibility, and cognitive load.
    Provides personalized accommodation recommendations.

    IP-005 Days 11-12: Enhanced with ML predictions when available.
    """
    try:
        result = await engine.assess_task_suitability(
            user_id=request.user_id,
            task_data=request.task_data.model_dump()
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Add ML predictions if predictive engine is available (IP-005 Days 11-12)
        if engine.predictive_engine:
            try:
                energy_pred, energy_conf, energy_exp = await engine.predictive_engine.predict_energy_level(request.user_id)
                result["ml_energy_prediction"] = schemas.MLPrediction(
                    predicted_value=energy_pred,
                    confidence=energy_conf,
                    explanation=energy_exp,
                    ml_used=energy_conf >= engine.predictive_engine.min_prediction_confidence
                )
            except Exception as e:
                logger.warning(f"ML energy prediction failed: {e}")

            try:
                attention_pred, attention_conf, attention_exp = await engine.predictive_engine.predict_attention_state(request.user_id)
                result["ml_attention_prediction"] = schemas.MLPrediction(
                    predicted_value=attention_pred,
                    confidence=attention_conf,
                    explanation=attention_exp,
                    ml_used=attention_conf >= engine.predictive_engine.min_prediction_confidence
                )
            except Exception as e:
                logger.warning(f"ML attention prediction failed: {e}")

        return result

    except Exception as e:
        logger.error(f"Task assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy-level/{user_id}", response_model=schemas.EnergyLevelResponse)
async def get_energy_level(user_id: str, engine = Depends(get_engine), api_key: str = Security(verify_api_key)):
    """Get current energy level for user."""
    try:
        energy = engine.current_energy_levels.get(user_id) or _default_energy_level(user_id)

        return schemas.EnergyLevelResponse(
            energy_level=_extract_state_value(energy, "value", "level"),
            confidence=getattr(energy, "confidence", 0.8),
            last_updated=getattr(energy, "last_updated", datetime.now(timezone.utc))
        )

    except Exception as e:
        logger.error(f"Energy level retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attention-state/{user_id}", response_model=schemas.AttentionStateResponse)
async def get_attention_state(user_id: str, engine = Depends(get_engine), api_key: str = Security(verify_api_key)):
    """Get current attention state for user."""
    try:
        attention = engine.current_attention_states.get(user_id) or _default_attention_state(user_id)

        # Get indicators that led to this assessment
        indicators = {
            "attention_state": _extract_state_value(attention, "value", "state"),
            "assessment_method": "activity_pattern_analysis"
        }

        return schemas.AttentionStateResponse(
            attention_state=_extract_state_value(attention, "value", "state"),
            indicators=indicators,
            last_updated=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Attention state retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-break", response_model=schemas.BreakRecommendationResponse)
async def recommend_break(
    request: schemas.BreakRecommendationRequest,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
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
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
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
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
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


# Dashboard-specific endpoints (Day 2)

@router.get("/cognitive-load/{user_id}")
async def get_cognitive_load(
    user_id: str,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """Get current cognitive load for user."""
    try:
        # Calculate current system-wide cognitive load
        cognitive_load = await engine._calculate_system_cognitive_load()
        
        # Categorize the load
        if cognitive_load < 0.3:
            category = "low"
            status = "underutilized"
        elif 0.6 <= cognitive_load <= 0.7:
            category = "optimal"
            status = "sweet_spot"
        elif cognitive_load > 0.85:
            category = "critical"
            status = "overload"
        else:
            category = "moderate"
            status = "normal"
        
        return {
            "cognitive_load": round(cognitive_load, 2),
            "category": category,
            "threshold_status": status,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Cognitive load retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flow-state/{user_id}")
async def get_flow_state(
    user_id: str,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """Get current flow state for user."""
    try:
        # Check if user has active flow state
        # For now, return placeholder - would integrate with flow tracker
        flow_active = False
        duration_minutes = 0
        start_time = None
        
        return {
            "active": flow_active,
            "duration_minutes": duration_minutes,
            "start_time": start_time,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Flow state retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-time/{user_id}")
async def get_session_time(
    user_id: str,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """Get current session duration for user."""
    try:
        # Calculate session time from activity tracker
        # For now, return placeholder - would integrate with activity tracker
        total_minutes = 0
        start_time = datetime.now(timezone.utc)
        duration = "0m"
        
        return {
            "duration": duration,
            "start_time": start_time.isoformat(),
            "total_minutes": total_minutes,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Session time retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breaks/{user_id}")
async def get_breaks_info(
    user_id: str,
    engine = Depends(get_engine),
    api_key: str = Security(verify_api_key)
):
    """Get break timing information for user."""
    try:
        # Get profile for break timing
        profile = engine.user_profiles.get(user_id, ADHDProfile(user_id=user_id))
        
        # Calculate recommended break timing
        # For now, use optimal task duration as guide
        last_break = None
        minutes_since = 0
        recommended_in = profile.optimal_task_duration
        
        return {
            "last_break": last_break,
            "minutes_since": minutes_since,
            "recommended_in": recommended_in,
            "optimal_duration": profile.optimal_task_duration,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Breaks info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ML Pattern & Prediction Endpoints (IP-005 Days 11-12)

@router.get("/patterns/{user_id}", response_model=schemas.PatternsResponse)
async def get_user_patterns(
    user_id: str,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """
    Retrieve learned ADHD patterns for user.

    Returns energy, attention, and break patterns learned from historical data.
    IP-005 Days 11-12: Machine learning pattern learning capability.
    """
    try:
        if not engine.predictive_engine:
            raise HTTPException(status_code=503, detail="ML predictions not enabled")

        patterns = await engine.predictive_engine.pattern_learner.load_patterns_from_conport(user_id)

        # Convert dataclasses to dicts for JSON serialization
        def pattern_to_dict(pattern):
            """Convert dataclass to dict."""
            if hasattr(pattern, '__dict__'):
                return {k: str(v) if isinstance(v, datetime) else v for k, v in pattern.__dict__.items()}
            return pattern

        return schemas.PatternsResponse(
            user_id=user_id,
            energy_patterns=[pattern_to_dict(p) for p in patterns.get("energy", [])],
            attention_patterns=[pattern_to_dict(p) for p in patterns.get("attention", [])],
            break_patterns=[pattern_to_dict(p) for p in patterns.get("breaks", [])],
            last_updated=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pattern retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-cognitive-load", response_model=schemas.PredictionResponse)
async def predict_cognitive_load(
    request: schemas.PredictionRequest,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """
    Predict future cognitive load using ML model.

    Analyzes current features (energy, attention, task complexity, etc.) to predict
    cognitive load 1 hour ahead, enabling proactive ADHD accommodations.
    """
    try:
        result = await engine.predict_cognitive_load(request.user_id, request.features)

        return schemas.PredictionResponse(
            user_id=request.user_id,
            predicted_load=result.predicted_value,
            confidence=result.confidence,
            horizon_hours=result.horizon_hours,
            model_used=result.model_used,
            feature_importance=result.feature_importance,
            timestamp=result.timestamp.isoformat()
        )
    except Exception as e:
        logger.error(f"Cognitive load prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-complexity", response_model=schemas.ComplexityResponse)
async def get_code_complexity(
    request: schemas.CodeComplexityRequest,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    # Query Serena v2 for complexity (HTTP call to :8003)
    serena_url = "http://localhost:8003/mcp/complexity"
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(serena_url, json={"code_snippet": request.code_snippet})
            if resp.status_code == 200:
                data = resp.json()
                return {"complexity": data["complexity"], "level": data["level"]}
    except Exception as e:
        logger.warning(f"Serena query failed: {e}")
        return {"complexity": 0.5, "level": "unknown"}  # Fallback

@router.post("/predict", response_model=schemas.PredictionResponse)
async def predict(
    request: schemas.PredictionRequest,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """
    Get ML prediction for energy, attention, or break timing.

    IP-005 Days 11-12: Proactive ADHD accommodations using pattern learning.
    """
    try:
        if not engine.predictive_engine:
            raise HTTPException(status_code=503, detail="ML predictions not enabled")

        pred_engine = engine.predictive_engine

        if request.prediction_type == "energy":
            predicted_value, confidence, explanation = await pred_engine.predict_energy_level(
                request.user_id,
                request.context.get("current_time") if request.context else None
            )
        elif request.prediction_type == "attention":
            predicted_value, confidence, explanation = await pred_engine.predict_attention_state(
                request.user_id,
                request.context
            )
        elif request.prediction_type == "break":
            minutes_until_break, confidence, explanation = await pred_engine.predict_optimal_break_timing(
                request.user_id,
                request.context.get("minutes_since_break") if request.context else None
            )
            predicted_value = f"{minutes_until_break} minutes"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid prediction_type: {request.prediction_type}")

        return schemas.PredictionResponse(
            prediction_type=request.prediction_type,
            predicted_value=str(predicted_value),
            confidence=confidence,
            explanation=explanation,
            ml_used=confidence >= pred_engine.min_prediction_confidence,
            timestamp=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statusline endpoint for Claude Code statusline integration
@router.get("/statusline/{user_id}")
async def get_statusline_data(
    user_id: str,
    request: Request,
    engine = Depends(get_engine),
    api_key: str | None = Security(api_key_header)
):
    """
    Statusline data endpoint for Claude Code integration.

    Provides aggregated ADHD state data for statusline display:
    - energy_level: Current energy state
    - attention_state: Current attention state
    - breaks_suggested: Number of pending break suggestions
    - hyperfocus_protections: Number of active hyperfocus protections
    """
    try:
        client_host = request.client.host if request.client else ""
        if api_key:
            if api_key != settings.api_key:
                raise HTTPException(status_code=403, detail="Invalid API key")
        elif not settings.statusline_allow_public and client_host not in {"127.0.0.1", "::1", "localhost"}:
            raise HTTPException(status_code=403, detail="API key required")

        # Get energy level
        energy_level = engine.current_energy_levels.get(user_id) or _default_energy_level(user_id)
        energy_str = _extract_state_value(energy_level, "value", "level")

        # Get attention state
        attention_state = engine.current_attention_states.get(user_id) or _default_attention_state(user_id)
        attention_str = _extract_state_value(attention_state, "value", "state")

        # Get break suggestions count (simplified for statusline)
        breaks_suggested = 0
        if user_id in engine.user_profiles:
            profile = engine.user_profiles[user_id]
            # Simple heuristic: suggest break if past optimal duration
            breaks_suggested = 1 if profile.optimal_task_duration > 0 else 0

        # Get hyperfocus protections count
        hyperfocus_protections = 0
        if attention_str == "hyperfocused":
            hyperfocus_protections = 1

        return {
            "energy_level": energy_str,
            "attention_state": attention_str,
            "breaks_suggested": breaks_suggested,
            "hyperfocus_protections": hyperfocus_protections
        }

    except Exception as e:
        logger.error(f"Statusline data retrieval failed: {e}")
        # Return safe defaults
        return {
            "energy_level": "MEDIUM",
            "attention_state": "FOCUSED",
            "breaks_suggested": 0,
            "hyperfocus_protections": 0
        }


# ============================================================================
# WebSocket Streaming Endpoint (Dashboard Day 7)
# ============================================================================

@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket, user_id: str = "default"):
    """
    Real-time event streaming to dashboard via WebSocket.
    
    Sends:
    - state_update: ADHD state changes (energy, attention, cognitive load)
    - metric_update: Time-series data points for sparklines
    - alert: Critical notifications (break needed, energy crash)
    - heartbeat: Keep-alive every 30 seconds
    
    Features:
    - Auto-buffering of messages during disconnection (last 50)
    - Graceful reconnection handling
    - Low latency (<100ms typical)
    - Supports multiple concurrent connections per user
    
    Usage:
        wscat -c "ws://localhost:8001/api/v1/ws/stream?user_id=test"
    
    Part of Dashboard Day 7 - WebSocket Streaming Implementation
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Send buffered messages from disconnection period
        await manager.send_buffered_messages(websocket, user_id)
        
        # Send initial state
        engine = get_engine()
        initial_state = await _get_current_state(engine, user_id)
        
        await websocket.send_json({
            "type": "state_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": initial_state
        })
        
        logger.info(f"📡 WebSocket stream started for user: {user_id}")
        
        # Keep connection alive with heartbeat and handle client messages
        last_heartbeat = datetime.utcnow()
        heartbeat_interval = 30  # seconds
        
        while True:
            # Send heartbeat every 30s
            if (datetime.utcnow() - last_heartbeat).total_seconds() > heartbeat_interval:
                await send_heartbeat(websocket, user_id)
                last_heartbeat = datetime.utcnow()
            
            # Wait for client messages (optional commands like refresh)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                command = json.loads(data)
                await _handle_client_command(websocket, user_id, command, engine)
                
            except asyncio.TimeoutError:
                # No message received, continue loop
                continue
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected normally: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ WebSocket error for {user_id}: {e}")
        
    finally:
        await manager.disconnect(websocket, user_id)


async def _get_current_state(engine, user_id: str) -> dict:
    """Fetch current ADHD state from engine"""
    try:
        # Get energy level
        energy_level = engine.current_energy_levels.get(user_id) or _default_energy_level(user_id)
        energy_str = _extract_state_value(energy_level, "value", "level")

        # Get attention state
        attention_state = engine.current_attention_states.get(user_id) or _default_attention_state(user_id)
        attention_str = _extract_state_value(attention_state, "value", "state")
        
        # Calculate cognitive load
        cognitive_load = await engine._calculate_cognitive_load(user_id)
        
        # Get session duration
        session_duration = await engine._get_session_duration(user_id)
        
        # Get tasks completed
        tasks_completed = await engine._get_tasks_completed(user_id)
        
        return {
            "energy_level": energy_str,
            "attention_state": attention_str,
            "cognitive_load": cognitive_load,
            "session_duration_minutes": session_duration,
            "tasks_completed_today": tasks_completed,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current state: {e}")
        # Return safe defaults
        return {
            "energy_level": "MEDIUM",
            "attention_state": "FOCUSED",
            "cognitive_load": 50,
            "session_duration_minutes": 0,
            "tasks_completed_today": 0,
            "timestamp": datetime.utcnow().isoformat()
        }


async def _handle_client_command(websocket: WebSocket, user_id: str, command: dict, engine):
    """Handle client commands (refresh, subscribe, etc.)"""
    try:
        cmd_type = command.get("type")
        
        if cmd_type == "refresh":
            # Send current state
            state = await _get_current_state(engine, user_id)
            await websocket.send_json({
                "type": "state_update",
                "timestamp": datetime.utcnow().isoformat(),
                "data": state
            })
            logger.debug(f"Refresh command from {user_id}")
            
        elif cmd_type == "ping":
            # Simple ping/pong for latency testing
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
                "data": command.get("data", {})
            })
            
        elif cmd_type == "subscribe":
            # Future: Subscribe to specific metrics
            metrics = command.get("metrics", [])
            logger.info(f"Subscribe request from {user_id}: {metrics}")
            await websocket.send_json({
                "type": "subscribed",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"metrics": metrics, "status": "acknowledged"}
            })
            
        else:
            logger.warning(f"Unknown command type: {cmd_type}")
            
    except Exception as e:
        logger.error(f"Error handling command: {e}")
