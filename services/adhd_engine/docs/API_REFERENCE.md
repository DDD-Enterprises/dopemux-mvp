# ADHD Engine API Reference

## Overview

The ADHD Engine provides REST APIs for intelligent accommodation and ML-powered insights. All endpoints require `X-API-Key` header authentication.

## Base URL
```
http://localhost:8001/api/v1
```

## Core Endpoints

### Energy Level Assessment

**GET** `/energy-level/{user_id}`

Get current energy level with optional ML predictions.

**Response:**
```json
{
  "energy_level": "MEDIUM",
  "confidence": 0.85,
  "last_updated": "2025-11-07T20:30:00Z",
  "ml_prediction": {
    "predicted_value": "HIGH",
    "confidence": 0.82,
    "explanation": "Based on 47 observations, you typically have HIGH energy at 2pm on Thursdays",
    "ml_used": true
  }
}
```

**Caching:** 5-minute TTL

### Attention State Assessment

**GET** `/attention-state/{user_id}`

Get current attention state with indicators and predictions.

**Response:**
```json
{
  "attention_state": "FOCUSED",
  "indicators": {
    "context_switches_per_hour": 3,
    "average_focus_duration": 25,
    "distraction_events": 2
  },
  "last_updated": "2025-11-07T20:30:00Z",
  "ml_prediction": {
    "predicted_value": "FOCUSED",
    "confidence": 0.78,
    "explanation": "Session context indicates continued focus for afternoon work",
    "ml_used": true
  }
}
```

**Caching:** 3-minute TTL

### Break Recommendations

**POST** `/recommend-break`

Get personalized break recommendations.

**Request:**
```json
{
  "user_id": "user123",
  "work_duration": 45
}
```

**Response:**
```json
{
  "break_needed": true,
  "reason": "optimal_duration_reached",
  "urgency": "soon",
  "suggestions": [
    "5-minute walk",
    "Deep breathing exercise",
    "Eye rest (20-20-20 rule)"
  ],
  "message": "Time for a break after 45 minutes of focused work!",
  "ml_prediction": {
    "predicted_value": "20 minutes",
    "confidence": 0.71,
    "explanation": "Based on your patterns, you're most productive with 45-minute work intervals",
    "ml_used": true
  }
}
```

**Caching:** 1-minute TTL (includes work_duration in cache key)

### Activity Logging

**PUT** `/activity/{user_id}`

Log user activity for pattern learning.

**Request:**
```json
{
  "completion_rate": 0.85,
  "break_compliance": true,
  "minutes_since_break": 20,
  "task_complexity": 0.6,
  "distraction_level": 0.2
}
```

**Response:**
```json
{
  "recorded": true,
  "energy_updated": true,
  "attention_updated": true,
  "message": "Activity logged successfully",
  "ml_prediction": {
    "predicted_value": "Attention may become FOCUSED",
    "confidence": 0.73,
    "explanation": "High completion rate suggests improving attention state",
    "ml_used": true
  }
}
```

**Caching:** 1-minute TTL

### Task Suitability Assessment

**POST** `/assess-task`

Assess if a task is suitable for current ADHD state.

**Request:**
```json
{
  "user_id": "user123",
  "task_data": {
    "complexity_score": 0.6,
    "estimated_minutes": 25,
    "description": "implement authentication system",
    "dependencies": []
  }
}
```

**Response:**
```json
{
  "suitability_score": 0.82,
  "energy_match": 0.85,
  "attention_compatibility": 0.78,
  "cognitive_load": 0.65,
  "cognitive_load_level": "MODERATE",
  "recommendations": [
    {
      "accommodation_type": "task_chunking",
      "urgency": "when_convenient",
      "message": "Consider breaking this into smaller tasks",
      "action_required": false,
      "suggested_actions": ["Split into 15-minute chunks", "Add progress checkpoints"],
      "cognitive_benefit": "Reduces overwhelm and improves completion rate",
      "implementation_effort": "low"
    }
  ],
  "accommodations_needed": ["complexity_reduction"],
  "optimal_timing": {
    "is_optimal_time": true,
    "suggested_hours": [9, 10, 14, 15],
    "reason": "peak_energy_hours"
  },
  "adhd_insights": {
    "hyperfocus_risk": "low",
    "distraction_risk": "medium",
    "context_switch_impact": "medium"
  }
}
```

### User Profile Management

**POST** `/user-profile`

Create or update ADHD profile.

**Request:**
```json
{
  "user_id": "user123",
  "hyperfocus_tendency": 0.7,
  "distraction_sensitivity": 0.6,
  "optimal_task_duration": 25,
  "max_task_duration": 90,
  "peak_hours": [9, 10, 14, 15],
  "break_resistance": 0.3
}
```

**Response:**
```json
{
  "created": true,
  "profile": {
    "user_id": "user123",
    "hyperfocus_tendency": 0.7,
    "distraction_sensitivity": 0.6,
    "optimal_task_duration": 25,
    "max_task_duration": 90,
    "peak_hours": [9, 10, 14, 15],
    "break_resistance": 0.3,
    "created_at": "2025-11-07T20:30:00Z"
  }
}
```

**Note:** Invalidates user-specific caches when updated.

### Cognitive Load Assessment

**GET** `/cognitive-load/{user_id}`

Get current cognitive load assessment.

**Response:**
```json
{
  "cognitive_load": 0.65,
  "category": "moderate",
  "threshold_status": "normal",
  "last_updated": "2025-11-07T20:30:00Z"
}
```

## Monitoring Endpoints

### Health Check

**GET** `/health`

Comprehensive system health check.

**Response:**
```json
{
  "overall_status": "🧠 Highly Active",
  "components": {
    "redis_persistence": "🟢 Connected",
    "monitors_active": "6/6",
    "user_profiles": 3,
    "background_prediction": "🟢 Active"
  },
  "accommodation_stats": {
    "recommendations_made": 1250,
    "breaks_suggested": 89,
    "energy_optimizations": 156,
    "cognitive_load_reductions": 234,
    "context_switch_preventions": 67,
    "hyperfocus_protections": 23
  },
  "current_state": {
    "energy_levels": {
      "user1": "HIGH",
      "user2": "MEDIUM",
      "user3": "LOW"
    },
    "attention_states": {
      "user1": "FOCUSED",
      "user2": "SCATTERED",
      "user3": "FOCUSED"
    },
    "active_accommodations": {
      "user1": 2,
      "user2": 1,
      "user3": 0
    }
  },
  "effectiveness_metrics": {
    "accommodation_rate": "416.7 per user",
    "cognitive_load_reductions": 234,
    "break_compliance": "monitoring_active"
  }
}
```

### Background Service Status

**GET** `/background-service/status`

Background prediction service monitoring.

**Response:**
```json
{
  "running": true,
  "predictions_made": 1250,
  "users_being_monitored": 3,
  "monitoring_interval_seconds": 300,
  "avg_overhead_seconds": 0.003,
  "max_overhead_seconds": 0.045,
  "target_max_seconds": 0.005,
  "predictions_per_minute": 0.42,
  "last_prediction_updates": {
    "user1": "2025-11-07T20:25:00Z",
    "user2": "2025-11-07T20:24:00Z",
    "user3": "2025-11-07T20:23:00Z"
  }
}
```

### Prometheus Metrics

**GET** `/metrics`

Prometheus-compatible metrics for monitoring.

**Response:**
```
# HELP adhd_api_requests_total Total number of API requests
# TYPE adhd_api_requests_total counter
adhd_api_requests_total{endpoint="energy",method="GET",status="success"} 1250

# HELP adhd_api_request_duration_seconds API request duration in seconds
# TYPE adhd_api_request_duration_seconds histogram
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="0.01"} 0
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="0.05"} 850
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="0.1"} 1150
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="0.25"} 1200
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="0.5"} 1225
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="1.0"} 1240
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="2.0"} 1250
adhd_api_request_duration_seconds_bucket{endpoint="energy",le="+Inf"} 1250
adhd_api_request_duration_seconds_count{endpoint="energy"} 1250
adhd_api_request_duration_seconds_sum{endpoint="energy"} 187.5

# HELP adhd_cache_hits_total Total number of cache hits
# TYPE adhd_cache_hits_total counter
adhd_cache_hits_total{endpoint="energy"} 890

# HELP adhd_cache_misses_total Total number of cache misses
# TYPE adhd_cache_misses_total counter
adhd_cache_misses_total{endpoint="energy"} 360

# HELP adhd_ml_predictions_total Total number of ML predictions made
# TYPE adhd_ml_predictions_total counter
adhd_ml_predictions_total{endpoint="energy",prediction_type="energy"} 450

# HELP adhd_ml_prediction_confidence ML prediction confidence scores
# TYPE adhd_ml_prediction_confidence histogram
adhd_ml_prediction_confidence_bucket{endpoint="energy",le="0.0"} 0
adhd_ml_prediction_confidence_bucket{endpoint="energy",le="0.2"} 0
adhd_ml_prediction_confidence_bucket{endpoint="energy",le="0.4"} 15
adhd_ml_prediction_confidence_bucket{endpoint="energy",le="0.6"} 45
adhd_ml_prediction_confidence_bucket{endpoint="energy",le="0.8"} 180
adhd_ml_prediction_confidence_bucket{endpoint="energy",le="+Inf"} 450
adhd_ml_prediction_confidence_count{endpoint="energy"} 450
adhd_ml_prediction_confidence_sum{endpoint="energy"} 337.5
```

## Data Models

### MLPrediction

```python
class MLPrediction(BaseModel):
    predicted_value: Any          # The ML model's prediction
    confidence: float            # Confidence score (0.0-1.0)
    explanation: str             # Human-readable explanation
    ml_used: bool                # Whether ML was actually used
```

### EnergyLevel Enum

```python
class EnergyLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HYPERFOCUS = "hyperfocus"
```

### AttentionState Enum

```python
class AttentionState(str, Enum):
    SCATTERED = "scattered"
    TRANSITIONING = "transitioning"
    FOCUSED = "focused"
    HYPERFOCUSED = "hyperfocused"
    OVERWHELMED = "overwhelmed"
```

## Authentication

All endpoints require the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

Default key: `dev-key-123` (development only)

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid API key)
- `404`: Not Found (user or resource not found)
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error description"
}
```

## Caching Behavior

- All endpoints implement Redis-based caching with endpoint-specific TTLs
- Cache keys include user_id for isolation
- Cache misses trigger normal processing + cache population
- Profile updates invalidate user-specific caches
- Cache failures fallback to normal operation (no errors)

## Rate Limiting

Implemented via middleware with configurable limits to prevent abuse.

## Performance Expectations

- **Cache Hit**: <10ms response time
- **Cache Miss**: <100ms response time
- **Background Service Overhead**: <5% of system resources
- **Concurrent Users**: Scales to 100+ with proper Redis configuration