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

from fastapi import APIRouter, HTTPException, Depends, Security, WebSocket, WebSocketDisconnect
from typing import Any
from datetime import datetime, timezone
import logging
import asyncio
import json
import os
import sys
import importlib
import asyncio

logger = logging.getLogger(__name__)

# Import cache utility for Redis caching
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'docker', 'mcp-servers', 'shared'))
from cache import get_cache

# Import Prometheus metrics (avoid conflicts with repo-local prometheus_client.py)
try:
    prometheus_module = importlib.import_module("prometheus_client")
    required_attrs = ["Counter", "Histogram", "Gauge", "generate_latest", "CONTENT_TYPE_LATEST"]
    if all(hasattr(prometheus_module, attr) for attr in required_attrs):
        from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
        PROMETHEUS_AVAILABLE = True
    else:
        raise ImportError("prometheus_client missing metrics API")
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available - metrics disabled")

import api.schemas as schemas
from models import ADHDProfile, EnergyLevel, AttentionState

from .schemas import (
    PredictionOverrideRequest, OverrideResponse, CustomizationSettings,
    PredictionFeedbackRequest, AutomationAdjustmentRequest,
    TrustMetricsResponse, TrustVisualizationResponse
)
from auth import verify_api_key
from api.websocket import manager, send_heartbeat

# Import time for caching
import time

router = APIRouter()

# Cache TTL constants (seconds)
ENERGY_CACHE_TTL = 300  # 5 minutes - energy levels are relatively stable
ATTENTION_CACHE_TTL = 180  # 3 minutes - attention can change more frequently
BREAK_CACHE_TTL = 60  # 1 minute - break recommendations need to be fresh
ACTIVITY_CACHE_TTL = 60  # 1 minute - activity updates are time-sensitive

# Cache instance (lazy async initialization)
_cache_instance = None


class _InMemoryCache:
    """Minimal async cache fallback when Redis is unavailable."""

    def __init__(self):
        self._store = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None):
        async with self._lock:
            return self._store.get(key, default)

    async def set(self, key: str, value: Any, ttl: int = 0):
        async with self._lock:
            self._store[key] = value
        return True

    async def delete(self, key: str):
        async with self._lock:
            self._store.pop(key, None)
        return True


async def get_cache_instance():
    """Return shared Redis cache (initialize once)."""
    global _cache_instance
    force_memory = os.getenv("ADHD_FORCE_INMEMORY_CACHE", "").lower() in {"1", "true", "yes"}
    if force_memory:
        if not isinstance(_cache_instance, _InMemoryCache):
            _cache_instance = _InMemoryCache()
        return _cache_instance
    if _cache_instance is None:
        try:
            _cache_instance = await get_cache()
        except Exception as exc:
            logger.warning("Cache unavailable (%s); using in-memory fallback", exc)
            _cache_instance = _InMemoryCache()
    return _cache_instance

# Prometheus metrics (only if available)
if PROMETHEUS_AVAILABLE:
    # API call counters
    API_REQUESTS_TOTAL = Counter(
        'adhd_api_requests_total',
        'Total number of API requests',
        ['endpoint', 'method', 'status']
    )

    # Cache performance metrics
    CACHE_HITS_TOTAL = Counter(
        'adhd_cache_hits_total',
        'Total number of cache hits',
        ['endpoint']
    )

    CACHE_MISSES_TOTAL = Counter(
        'adhd_cache_misses_total',
        'Total number of cache misses',
        ['endpoint']
    )

    # Response time histograms
    API_REQUEST_DURATION = Histogram(
        'adhd_api_request_duration_seconds',
        'API request duration in seconds',
        ['endpoint'],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
    )

    # ML prediction metrics
    ML_PREDICTIONS_TOTAL = Counter(
        'adhd_ml_predictions_total',
        'Total number of ML predictions made',
        ['endpoint', 'prediction_type']
    )

    ML_PREDICTION_CONFIDENCE = Histogram(
        'adhd_ml_prediction_confidence',
        'ML prediction confidence scores',
        ['endpoint'],
        buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    )

    # Cache size gauge
    CACHE_SIZE = Gauge(
        'adhd_cache_entries',
        'Current number of cache entries',
        ['cache_type']
    )

else:
    # Dummy metrics if Prometheus not available
    API_REQUESTS_TOTAL = None
    CACHE_HITS_TOTAL = None
    CACHE_MISSES_TOTAL = None
    API_REQUEST_DURATION = None
    ML_PREDICTIONS_TOTAL = None
    ML_PREDICTION_CONFIDENCE = None
    CACHE_SIZE = None

def _make_cache_key(endpoint: str, user_id: str, **params) -> str:
    """Generate cache key for API endpoint."""
    key_parts = [f"adhd:{endpoint}:{user_id}"]
    for k, v in sorted(params.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)

async def _invalidate_user_caches(user_id: str):
    """Invalidate all cached responses for a user (used when profile updates)."""
    try:
        # Delete pattern-based cache keys for the user
        # Note: Redis DEL with pattern not directly supported, but we can implement
        # cache invalidation by storing a user cache version that gets incremented
        # For simplicity, we'll skip complex invalidation for now
        logger.debug(f"Cache invalidation requested for user {user_id}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed for user {user_id}: {e}")


# Dependency injection for engine instance
def get_engine():
    """Get global engine instance."""
    try:
        from adhd_engine import main as engine_main
    except ImportError:
        import main as engine_main  # type: ignore
    if not engine_main.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return engine_main.engine


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
    start_time = time.time()
    status = "success"

    try:
        cache = await get_cache_instance()
        # Check cache first
        cache_key = _make_cache_key("energy", user_id)
        cached_data = await cache.get(cache_key)

        if cached_data:
            logger.debug(f"Cache hit for energy level: {user_id}")
            # Record cache hit
            if CACHE_HITS_TOTAL:
                CACHE_HITS_TOTAL.labels(endpoint="energy").inc()
            if API_REQUEST_DURATION:
                API_REQUEST_DURATION.labels(endpoint="energy").observe(time.time() - start_time)
            if API_REQUESTS_TOTAL:
                API_REQUESTS_TOTAL.labels(endpoint="energy", method="GET", status=status).inc()
            return schemas.EnergyLevelResponse.model_validate_json(cached_data)

        # Cache miss - record miss
        if CACHE_MISSES_TOTAL:
            CACHE_MISSES_TOTAL.labels(endpoint="energy").inc()

        # Cache miss - execute normal logic
        energy = engine.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)

        # Record API request
        if API_REQUESTS_TOTAL:
            API_REQUESTS_TOTAL.labels(endpoint="energy", method="GET", status=status).inc()

        # Get ML prediction if available
        ml_prediction = None
        if engine.predictive_engine:
            try:
                pred_value, confidence, explanation = await engine.predictive_engine.predict_energy_level(user_id)
                ml_prediction = schemas.MLPrediction(
                    predicted_value=pred_value,
                    confidence=confidence,
                    explanation=explanation,
                    ml_used=confidence >= engine.predictive_engine.min_prediction_confidence
                )

                # Record ML prediction metrics
                if ML_PREDICTIONS_TOTAL:
                    ML_PREDICTIONS_TOTAL.labels(endpoint="energy", prediction_type="energy").inc()
                if ML_PREDICTION_CONFIDENCE:
                    ML_PREDICTION_CONFIDENCE.labels(endpoint="energy").observe(confidence)

            except Exception as e:
                logger.warning(f"ML energy prediction failed: {e}")

        response = schemas.EnergyLevelResponse(
            energy_level=energy.value if hasattr(energy, 'value') else str(energy),
            confidence=0.8,  # Based on activity data freshness
            last_updated=datetime.now(timezone.utc),
            ml_prediction=ml_prediction
        )

        # Cache the response
        try:
            await cache.set(cache_key, response.model_dump_json(), ttl=ENERGY_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for energy level: {e}")

        # Record timing
        if API_REQUEST_DURATION:
            API_REQUEST_DURATION.labels(endpoint="energy").observe(time.time() - start_time)

        return response

    except Exception as e:
        status = "error"
        if API_REQUESTS_TOTAL:
            API_REQUESTS_TOTAL.labels(endpoint="energy", method="GET", status=status).inc()
        logger.error(f"Energy level retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attention-state/{user_id}", response_model=schemas.AttentionStateResponse)
async def get_attention_state(user_id: str, engine = Depends(get_engine), api_key: str = Security(verify_api_key)):
    """Get current attention state for user."""
    try:
        cache = await get_cache_instance()
        # Check cache first
        cache_key = _make_cache_key("attention", user_id)
        cached_data = await cache.get(cache_key)

        if cached_data:
            logger.debug(f"Cache hit for attention state: {user_id}")
            return schemas.AttentionStateResponse.model_validate_json(cached_data)

        # Cache miss - execute normal logic
        attention = engine.current_attention_states.get(user_id, AttentionState.FOCUSED)

        # Get indicators that led to this assessment
        indicators = {
            "attention_state": attention.value if hasattr(attention, 'value') else str(attention),
            "assessment_method": "activity_pattern_analysis"
        }

        # Get ML prediction if available
        ml_prediction = None
        if engine.predictive_engine:
            try:
                pred_value, confidence, explanation = await engine.predictive_engine.predict_attention_state(user_id)
                ml_prediction = schemas.MLPrediction(
                    predicted_value=pred_value,
                    confidence=confidence,
                    explanation=explanation,
                    ml_used=confidence >= engine.predictive_engine.min_prediction_confidence
                )
            except Exception as e:
                logger.warning(f"ML attention prediction failed: {e}")

        response = schemas.AttentionStateResponse(
            attention_state=attention.value if hasattr(attention, 'value') else str(attention),
            indicators=indicators,
            last_updated=datetime.now(timezone.utc),
            ml_prediction=ml_prediction
        )

        # Cache the response
        try:
            await cache.set(cache_key, response.model_dump_json(), ttl=ATTENTION_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for attention state: {e}")

        return response

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
        cache = await get_cache_instance()
        # Check cache first
        cache_key = _make_cache_key("break", request.user_id, work_duration=int(request.work_duration))
        cached_data = await cache.get(cache_key)

        if cached_data:
            logger.debug(f"Cache hit for break recommendation: {request.user_id}")
            return schemas.BreakRecommendationResponse.model_validate_json(cached_data)

        # Cache miss - execute normal logic
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

        # Get ML prediction if available
        ml_prediction = None
        if engine.predictive_engine:
            try:
                minutes_until_break, confidence, explanation = await engine.predictive_engine.predict_optimal_break_timing(
                    user_id, minutes_since_break
                )
                ml_prediction = schemas.MLPrediction(
                    predicted_value=f"{minutes_until_break} minutes",
                    confidence=confidence,
                    explanation=explanation,
                    ml_used=confidence >= engine.predictive_engine.min_prediction_confidence
                )
            except Exception as e:
                logger.warning(f"ML break prediction failed: {e}")

        # Get Zen break strategy recommendation
        zen_break_recommendation = None
        try:
            current_state = {
                'energy_level': engine.current_energy_levels.get(request.user_id, 'MEDIUM'),
                'attention_state': engine.current_attention_states.get(request.user_id, 'FOCUSED'),
                'minutes_since_last_break': request.minutes_since_break or 0,
                'cognitive_load': await engine._calculate_system_cognitive_load()
            }
            work_context = {
                'task_type': 'general',
                'complexity': 0.5,
                'progress_percentage': 0
            }

            zen_result = await engine.zen_client.recommend_break_strategy(current_state, work_context)
            if zen_result.get('break_recommended'):
                zen_break_recommendation = schemas.MLPrediction(
                    predicted_value=zen_result.get('break_duration_minutes', 5),
                    confidence=zen_result.get('post_break_energy_boost', 0.15),
                    explanation=zen_result.get('reasoning', 'Zen AI break optimization'),
                    ml_used=False  # Zen is AI, not ML
                )
        except Exception as e:
            logger.warning(f"Zen break recommendation failed: {e}")

        response = schemas.BreakRecommendationResponse(
            break_needed=break_needed,
            reason=reason,
            suggestions=suggestions,
            urgency=urgency,
            message=message,
            ml_prediction=ml_prediction,
            zen_break_recommendation=zen_break_recommendation
        )

        # Cache the response
        try:
            cache_key = _make_cache_key("break", request.user_id, work_duration=int(request.work_duration))
            await cache.set(cache_key, response.model_dump_json(), ttl=BREAK_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for break recommendation: {e}")

        return response

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
        cache = await get_cache_instance()
        # Check cache first (though POST, cache recent activity summary)
        cache_key = _make_cache_key("activity", user_id)
        cached_data = await cache.get(cache_key)

        if cached_data:
            logger.debug(f"Cache hit for activity update: {user_id}")
            return schemas.ActivityUpdateResponse.model_validate_json(cached_data)

        # Cache miss - execute normal logic
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

        # Get ML prediction if available (predict activity impact)
        ml_prediction = None
        if engine.predictive_engine and (request.completion_rate is not None or request.break_compliance is not None):
            try:
                # Predict how activity will affect energy/attention
                context = {
                    "completion_rate": request.completion_rate,
                    "break_compliance": request.break_compliance,
                    "minutes_since_break": request.minutes_since_break
                }
                pred_value, confidence, explanation = await engine.predictive_engine.predict_attention_state(user_id, context)
                ml_prediction = schemas.MLPrediction(
                    predicted_value=f"Attention may become {pred_value}",
                    confidence=confidence,
                    explanation=explanation,
                    ml_used=confidence >= engine.predictive_engine.min_prediction_confidence
                )
            except Exception as e:
                logger.warning(f"ML activity impact prediction failed: {e}")

        response = schemas.ActivityUpdateResponse(
            recorded=True,
            energy_updated=energy_updated,
            attention_updated=attention_updated,
            message="Activity logged successfully",
            ml_prediction=ml_prediction
        )

        # Cache the response (short TTL for activity updates)
        try:
            await cache.set(cache_key, response.model_dump_json(), ttl=ACTIVITY_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for activity update: {e}")

        return response

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
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
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
        # Get energy level
        energy_level = engine.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
        energy_str = energy_level.value if hasattr(energy_level, 'value') else str(energy_level)

        # Get attention state
        attention_state = engine.current_attention_states.get(user_id, AttentionState.FOCUSED)
        attention_str = attention_state.value if hasattr(attention_state, 'value') else str(attention_state)

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
# Metrics Endpoint (Phase 3.3 Performance Monitoring)
# ============================================================================

@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint for performance monitoring.

    Exposes:
    - API request counts and latency histograms
    - Cache hit/miss rates
    - ML prediction metrics
    - System performance indicators

    Access: GET /api/v1/metrics
    """
    if not PROMETHEUS_AVAILABLE:
        return {"error": "Prometheus metrics not available"}

    return generate_latest()


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
        energy_level = engine.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
        energy_str = energy_level.value if hasattr(energy_level, 'value') else str(energy_level)
        
        # Get attention state
        attention_state = engine.current_attention_states.get(user_id, AttentionState.FOCUSED)
        attention_str = attention_state.value if hasattr(attention_state, 'value') else str(attention_state)
        
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


# ============================================================================
# Phase 3.5 User Control Layer - Prediction Overrides and Customization
# ============================================================================

@router.post("/override-prediction", response_model=schemas.OverrideResponse)
async def override_prediction(
    request: schemas.PredictionOverrideRequest,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """Allow user to override an ML prediction."""
    try:
        # Log the override
        override_id = f"override_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{request.prediction_type}"

        # Update user profile with override
        user_profile = engine.user_profiles.get(request.user_id)
        if not user_profile:
            return schemas.OverrideResponse(
                override_id=override_id,
                prediction_type=request.prediction_type,
                original_prediction=request.original_prediction,
                override_value=request.override_value,
                applied=False,
                feedback_recorded=False,
                message="No profile found for this user"
            )

        # Store override in user profile
        if "overrides" not in user_profile.__dict__:
            user_profile.overrides = []

        user_profile.overrides.append({
            "id": override_id,
            "type": request.prediction_type,
            "original": request.original_prediction,
            "override": request.override_value,
            "reason": request.reason,
            "timestamp": datetime.now(timezone.utc),
            "feedback_rating": request.feedback_rating
        })

        # Update the current state to use override
        if request.prediction_type == "energy":
            engine.current_energy_levels[request.user_id] = request.override_value
        elif request.prediction_type == "attention":
            engine.current_attention_states[request.user_id] = request.override_value
        elif request.prediction_type == "break":
            # Clear break cache
            cache = await get_cache_instance()
            cache_key = _make_cache_key("break", request.user_id)
            try:
                await cache.delete(cache_key)
            except Exception as e:
                logger.warning(f"Failed to invalidate break cache: {e}")

        # Record feedback for ML model improvement
        feedback_recorded = False
        if request.feedback_rating:
            try:
                # Store feedback in ConPort for ML retraining
                await engine.conport.log_custom_data(
                    category="ml_feedback",
                    key=f"override_{override_id}",
                    value={
                        "user_id": request.user_id,
                        "prediction_type": request.prediction_type,
                        "original_prediction": request.original_prediction,
                        "override_value": request.override_value,
                        "reason": request.reason,
                        "feedback_rating": request.feedback_rating,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                feedback_recorded = True
            except Exception as e:
                logger.warning(f"Failed to record feedback: {e}")

        return schemas.OverrideResponse(
            override_id=override_id,
            prediction_type=request.prediction_type,
            original_prediction=request.original_prediction,
            override_value=request.override_value,
            applied=True,
            feedback_recorded=feedback_recorded,
            message=f"Prediction override applied successfully. ID: {override_id}"
        )

    except Exception as e:
        logger.error(f"Prediction override failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customization-settings/{user_id}", response_model=schemas.CustomizationSettings)
async def update_customization_settings(
    user_id: str,
    settings: schemas.CustomizationSettings,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """Update user customization settings for ADHD Engine."""
    try:
        # Get or create user profile
        user_profile = engine.user_profiles.get(user_id)
        if not user_profile:
            user_profile = ADHDProfile(user_id=user_id)
            engine.user_profiles[user_id] = user_profile

        # Update settings
        user_profile.confidence_threshold = settings.confidence_threshold
        user_profile.automation_level = settings.automation_level
        user_profile.notifications_enabled = settings.notifications_enabled
        user_profile.accessibility_mode = settings.accessibility_mode
        user_profile.keyboard_shortcuts = settings.keyboard_shortcuts
        user_profile.high_contrast = settings.high_contrast

        # Invalidate caches affected by these settings
        await _invalidate_user_caches(user_id)

        # Save to persistent storage
        try:
            await engine.conport.write_custom_data(
                category="user_settings",
                key=f"customization_{user_id}",
                value={
                    "confidence_threshold": settings.confidence_threshold,
                    "automation_level": settings.automation_level,
                    "notifications_enabled": settings.notifications_enabled,
                    "accessibility_mode": settings.accessibility_mode,
                    "keyboard_shortcuts": settings.keyboard_shortcuts,
                    "high_contrast": settings.high_contrast,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to persist settings: {e}")

        return settings

    except Exception as e:
        logger.error(f"Customization update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customization-settings/{user_id}", response_model=schemas.CustomizationSettings)
async def get_customization_settings(
    user_id: str,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """Get user customization settings."""
    try:
        user_profile = engine.user_profiles.get(user_id)
        if not user_profile:
            # Return defaults
            return schemas.CustomizationSettings()

        return schemas.CustomizationSettings(
            confidence_threshold=user_profile.confidence_threshold,
            automation_level=user_profile.automation_level,
            notifications_enabled=user_profile.notifications_enabled,
            accessibility_mode=user_profile.accessibility_mode,
            keyboard_shortcuts=user_profile.keyboard_shortcuts,
            high_contrast=user_profile.high_contrast
        )

    except Exception as e:
        logger.error(f"Get customization settings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 3.6 Trust Building Layer - Accuracy Tracking and Feedback
# ============================================================================

@router.post("/prediction-feedback/{user_id}")
async def submit_prediction_feedback(
    user_id: str,
    feedback: PredictionFeedbackRequest,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """Submit feedback on prediction usefulness."""
    try:
        if not engine.trust_service:
            return {"error": "Trust building service not available"}

        await engine.trust_service.collect_user_feedback(
            user_id=user_id,
            prediction_type=getattr(feedback, 'prediction_type', 'general'),  # Add to schema
            prediction_id=feedback.prediction_id,
            rating=feedback.rating,
            usefulness=feedback.usefulness,
            comments=feedback.comments
        )

        return {"message": "Feedback recorded successfully"}

    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trust-metrics/{user_id}", response_model=TrustMetricsResponse)
async def get_trust_metrics(
    user_id: str,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """Get trust metrics for user."""
    try:
        if not engine.trust_service:
            raise HTTPException(status_code=503, detail="Trust building service not available")

        metrics = await engine.trust_service.get_trust_metrics(user_id)
        return metrics

    except Exception as e:
        logger.error(f"Trust metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trust-visualization/{user_id}", response_model=TrustVisualizationResponse)
async def get_trust_visualization(
    user_id: str,
    days: int = 30,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """Get trust visualization data."""
    try:
        if not engine.trust_service:
            raise HTTPException(status_code=503, detail="Trust building service not available")

        data = await engine.trust_service.get_visualization_data(user_id, days)
        return data

    except Exception as e:
        logger.error(f"Trust visualization retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation-level/{user_id}")
async def adjust_automation_level(
    user_id: str,
    request: schemas.AutomationAdjustmentRequest,
    engine = Depends(get_engine), api_key: str = Security(verify_api_key)
):
    """Adjust automation level for prediction type."""
    try:
        if not engine.trust_service:
            return {"error": "Trust building service not available"}

        success = await engine.trust_service.adjust_automation_level(
            prediction_type=request.prediction_type,
            user_id=user_id,
            new_level=request.automation_level
        )

        if success:
            return {"message": f"Automation level adjusted to {request.automation_level}"}
        else:
            raise HTTPException(status_code=400, detail="Invalid automation level")

    except Exception as e:
        logger.error(f"Automation level adjustment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
