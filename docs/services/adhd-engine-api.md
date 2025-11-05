# ADHD Engine API Documentation

## Overview

The ADHD Accommodation Engine is a microservice providing AI-powered task management and accommodation recommendations for ADHD developers. It features 6 API endpoints for real-time assessment and monitoring, plus 6 background monitors that run continuously.

**Base URL**: `http://localhost:8095` (default) or configured via `API_PORT` environment variable

**Authentication**: All endpoints require `X-API-Key` header with the API key (default: `dev-key-123` for development)

**Content-Type**: `application/json` for all requests and responses

---

## Authentication

All API endpoints require an `X-API-Key` header for authentication. The key is configured via the `ADHD_ENGINE_API_KEY` environment variable.

**Example Header**:
```
X-API-Key: dev-key-123
```

---

## API Endpoints

### 1. Task Assessment

**Endpoint**: `POST /api/v1/assess-task`

**Description**: Assess task suitability for the current user state (energy, attention, cognitive load). Returns suitability score and accommodation recommendations.

**Request Body** (JSON):
```
{
  "user_id": "hue",  // User identifier (string)
  "task_id": "task-001",  // Task identifier (string)
  "task_data": {
    "description": "Implement user authentication middleware",
    "estimated_complexity": 0.7,  // 0.0-1.0 scale
    "duration_minutes": 45,
    "tags": ["backend", "security"],
    "dependencies": ["database-setup"]
  }
}
```

**Response** (JSON):
```
{
  "suitability_score": 0.75,  // 0.0-1.0 overall suitability
  "energy_match": "good",  // low/medium/high mismatch
  "attention_compatibility": "moderate",  // low/medium/high
  "cognitive_load": 0.65,  // 0.0-1.0 cognitive load estimate
  "cognitive_load_level": "moderate",  // minimal/low/moderate/high/extreme
  "recommendations": [
    {
      "type": "time-blocking",  // accommodation type
      "description": "Schedule for 25-minute focused sessions with 5-minute breaks"
    },
    {
      "type": "tool-setup",
      "description": "Use Serena MCP for code navigation to reduce cognitive load"
    }
  ],
  "accommodations_needed": ["time-blocking", "tool-setup"],
  "optimal_timing": "morning-high-energy",  // morning-high-energy/afternoon-break
  "adhd_insights": {
    "hyperfocus_risk": "low",  // low/medium/high
    "distraction_risk": "medium",
    "context_switch_impact": "medium"
  }
}
```

**Example Usage** (cURL):
```bash
curl -X POST "http://localhost:8095/api/v1/assess-task" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "user_id": "hue",
    "task_id": "auth-middleware",
    "task_data": {
      "description": "Implement JWT authentication middleware",
      "estimated_complexity": 0.6,
      "duration_minutes": 30,
      "tags": ["security", "backend"]
    }
  }'
```

---

### 2. Energy Level

**Endpoint**: `GET /api/v1/energy-level/{user_id}`

**Description**: Get current energy level for a user. Returns the current energy state and trend.

**Path Parameters**:
- `user_id` (string): User identifier

**Response** (JSON):
```
{
  "user_id": "hue",
  "energy_level": 0.75,  // 0.0-1.0 current energy
  "energy_trend": "declining",  // rising/steady/declining
  "energy_category": "high",  // low/medium/high
  "last_updated": "2025-11-04T16:45:00Z",
  "recommendations": [
    "Continue with complex tasks while energy is high",
    "Schedule breaks if energy drops below 0.4"
  ]
}
```

**Example Usage** (cURL):
```bash
curl -H "X-API-Key: dev-key-123" "http://localhost:8095/api/v1/energy-level/hue"
```

---

### 3. Attention State

**Endpoint**: `GET /api/v1/attention-state/{user_id}`

**Description**: Get current attention state for a user. Returns attention level and focus recommendations.

**Path Parameters**:
- `user_id` (string): User identifier

**Response** (JSON):
```
{
  "user_id": "hue",
  "attention_state": "focused",  // focused/scattered/transitioning
  "focus_duration": 22,  // minutes in current state
  "distraction_count": 3,  // distractions in last 10 minutes
  "recommendations": [
    "Maintain current task - focus state is good",
    "If distractions increase, consider 5-minute reset"
  ],
  "last_updated": "2025-11-04T16:45:00Z"
}
```

**Example Usage** (cURL):
```bash
curl -H "X-API-Key: dev-key-123" "http://localhost:8095/api/v1/attention-state/hue"
```

---

### 4. Break Recommendation

**Endpoint**: `POST /api/v1/recommend-break`

**Description**: Get personalized break recommendation based on current user state.

**Request Body** (JSON):
```
{
  "user_id": "hue",
  "current_task": "Implementing authentication middleware",
  "elapsed_time": 25,  // minutes on current task
  "distractions": 2,  // number of distractions
  "cognitive_load": 0.6  // current cognitive load
}
```

**Response** (JSON):
```
{
  "recommendation": "take_break",  // take_break/continue/focus_mode
  "break_type": "short_reset",  // short_reset/deep_breath/outdoor_walk
  "duration_minutes": 5,
  "reason": "Moderate cognitive load detected, short break recommended",
  "next_action": "Resume task after 5-minute break for optimal performance"
}
```

**Example Usage** (cURL):
```bash
curl -X POST "http://localhost:8095/api/v1/recommend-break" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "user_id": "hue",
    "current_task": "Authentication middleware",
    "elapsed_time": 25,
    "distractions": 1,
    "cognitive_load": 0.5
  }'
```

---

### 5. User Profile

**Endpoint**: `POST /api/v1/user-profile`

**Description**: Create or update ADHD user profile for personalized recommendations.

**Request Body** (JSON):
```
{
  "user_id": "hue",
  "profile": {
    "adhd_type": "combined",  // inattentive/combined/hyperfocus-prone
    "energy_patterns": {
      "morning_peak": 0.8,
      "afternoon_dip": 0.4,
      "evening_recovery": 0.6
    },
    "focus_duration_average": 25,  // minutes
    "distraction_threshold": 3,  // distractions per 10 minutes
    "preferred_break_types": ["short_reset", "deep_breath"],
    "cognitive_load_sensitivity": "high"  // low/medium/high
  }
}
```

**Response** (JSON):
```
{
  "status": "profile_updated",
  "user_id": "hue",
  "profile_id": "profile-hue-001",
  "last_updated": "2025-11-04T16:45:00Z",
  "validation": {
    "valid": true,
    "warnings": []
  }
}
```

**Example Usage** (cURL):
```bash
curl -X POST "http://localhost:8095/api/v1/user-profile" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "user_id": "hue",
    "profile": {
      "adhd_type": "combined",
      "energy_patterns": {
        "morning_peak": 0.8,
        "afternoon_dip": 0.4
      },
      "focus_duration_average": 25,
      "distraction_threshold": 3
    }
  }'
```

---

### 6. Activity Log

**Endpoint**: `PUT /api/v1/activity/{user_id}`

**Description**: Log activity events for pattern analysis and state tracking.

**Request Body** (JSON):
```
{
  "event_type": "task_start",  // task_start/task_complete/distractions/break_taken/context_switch
  "event_data": {
    "task_id": "auth-middleware",
    "duration_minutes": 25,
    "cognitive_load": 0.6,
    "distractions": 2,
    "notes": "Focused work with minor interruptions"
  }
}
```

**Response** (JSON):
```
{
  "status": "logged",
  "event_id": "event-001",
  "user_id": "hue",
  "timestamp": "2025-11-04T16:45:00Z",
  "analysis": {
    "pattern_matched": "productive_focus",
    "recommendation": "Continue current work pattern"
  }
}
```

**Example Usage** (cURL):
```bash
curl -X PUT "http://localhost:8095/api/v1/activity/hue" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "event_type": "task_complete",
    "event_data": {
      "task_id": "auth-middleware",
      "duration_minutes": 30,
      "cognitive_load": 0.65,
      "distractions": 1
    }
  }'
```

---

## Utility Endpoints

### Health Check

**Endpoint**: `GET /health`

**Description**: Health check for container orchestration and monitoring.

**Response** (JSON):
```
{
  "status": "healthy",
  "service": "adhd-accommodation-engine",
  "version": "1.0.0",
  "monitors": {
    "energy_tracking": true,
    "attention_monitoring": true,
    "cognitive_load": true,
    "break_suggestions": true,
    "hyperfocus_detection": true,
    "context_switching": true
  }
}
```

**Example Usage** (cURL):
```bash
curl -H "X-API-Key: dev-key-123" "http://localhost:8095/health"
```

---

### Root Info

**Endpoint**: `GET /`

**Description**: Basic service information.

**Response** (JSON):
```
{
  "service": "ADHD Accommodation Engine",
  "version": "1.0.0",
  "endpoints": "/api/v1/assess-task, /api/v1/energy-level/{user_id}, ...",
  "documentation": "See docs/services/adhd-engine-api.md",
  "status": "running"
}
```

**Example Usage** (cURL):
```bash
curl -H "X-API-Key: dev-key-123" "http://localhost:8095/"
```

---

## Background Monitors

The ADHD Engine runs 6 background monitors that operate continuously:

1. **Energy Tracking**: Monitors user energy levels based on activity patterns
2. **Attention Monitoring**: Detects attention state changes and focus duration
3. **Cognitive Load Assessment**: Measures real-time cognitive load during work
4. **Break Suggester**: Provides proactive break recommendations
5. **Hyperfocus Detection**: Identifies potential hyperfocus states for intervention
6. **Context Switching Tracker**: Tracks context switches and their impact

These monitors run asynchronously and update user state in Redis for real-time recommendations.

---

## Configuration

The service is configured via environment variables in `.env`:

**Core Settings**:
- `API_PORT`: Service port (default: 8095)
- `HOST`: Bind address (default: 0.0.0.0)
- `ADHD_ENGINE_API_KEY`: Authentication key (default: dev-key-123)
- `REDIS_URL`: Redis connection (default: redis://redis-primary:6379)

**CORS Settings**:
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins (default: localhost:3000, localhost:8097, adhd-dashboard:8097)

**Monitor Settings**:
- `MONITOR_CHECK_INTERVAL`: Monitor check interval in seconds (default: 60)
- `ENERGY_DECAY_RATE`: Energy decay rate per hour (default: 0.95)
- `ATTENTION_RESET_THRESHOLD`: Attention reset threshold in seconds (default: 300)

**ML Settings** (Future):
- `ENABLE_ML_PREDICTIONS`: Enable ML predictions (default: false)

---

## Integration with Dopemux

The ADHD Engine integrates with:

**ConPort MCP**: Knowledge graph for decisions and patterns
**Redis**: User state and cache persistence
**SuperClaude Commands**: Task assessment and accommodation recommendations
**Leantime**: Project management and task tracking
**Serena MCP**: Code complexity scoring for task estimation

---

## Development Notes

- **Port Conflicts**: If port 8095 is in use, set `API_PORT` to an available port
- **Redis Required**: Service requires Redis for state management
- **Authentication**: Use `X-API-Key` header for all requests
- **Testing**: Run `pytest services/adhd_engine/services/adhd_engine/tests/` for unit tests

**Status**: Production-ready with all 6 monitors operational

---

**🚀 ADHD Engine - Ready for Integration!**

For full integration, add the service to your docker-compose.yml and update the API key in your frontend applications.