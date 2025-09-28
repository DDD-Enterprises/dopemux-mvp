# GPT-Researcher Phase 2 API Documentation

## 🚀 Implementation Status (Updated 2025-09-27)

**BREAKTHROUGH COMPLETE**: Major compatibility issues resolved, API server fully operational!

### ✅ Recent Fixes Applied
- **Pydantic v2 Compatibility**: All `.dict()` calls replaced with `.model_dump()`
- **ResearchTask Object Handling**: Fixed bracket notation access patterns
- **ADHDConfiguration Mapping**: Corrected field mappings for break/work duration
- **API Server**: FastAPI running stable at localhost:8000 with session management
- **Task Tracking Integration**: Verified orchestrator.get_task_status() properly handles API requests
- **End-to-End Workflow**: Complete research workflow tested and operational

### 🎯 Current Status
- **Phase 1 MCP Server**: ✅ Production ready
- **Phase 2 API Server**: ✅ Operational with ADHD features
- **Session Persistence**: ✅ Working (24 active sessions restored)
- **WebSocket Progress**: ✅ Connected
- **Research Workflow**: ✅ **FULLY OPERATIONAL** - End-to-end testing complete

## Overview

The Phase 2 API provides programmatic access to GPT-Researcher with advanced ADHD features including session persistence, real-time progress tracking, and attention state management.

## Quick Start

1. **Start the API**:
```bash
cd backend
./start_api.sh
```

2. **Access API Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

3. **Test the API**:
```bash
python test_api.py
```

## API Endpoints

### Health & Status

#### GET /health
Check API health and status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "orchestrator": true,
  "session_manager": true,
  "active_tasks": 2,
  "active_websockets": 1
}
```

#### GET /api/v1/status
Get API capabilities and limits.

**Response:**
```json
{
  "version": "0.2.0",
  "capabilities": {
    "research_types": ["exploratory", "technical", "comparative", "systematic"],
    "search_engines": ["exa", "tavily", "perplexity", "context7"],
    "adhd_features": [
      "session_persistence",
      "break_management",
      "attention_detection",
      "progress_tracking",
      "hyperfocus_alerts"
    ]
  }
}
```

### Research Operations

#### POST /api/v1/research
Create a new research task with ADHD optimizations.

**Request Body:**
```json
{
  "topic": "Python async best practices",
  "research_type": "technical",
  "depth": "balanced",
  "adhd_config": {
    "break_interval": 25,
    "focus_duration": 25,
    "notification_style": "gentle",
    "hyperfocus_protection": true
  },
  "max_sources": 10,
  "timeout_minutes": 25
}
```

**Response:**
```json
{
  "task_id": "uuid-here",
  "session_id": "session-uuid",
  "status": "started",
  "created_at": "2025-09-27T20:00:00Z",
  "estimated_time_minutes": 15,
  "adhd_notes": [
    "⏰ Estimated time: 15 minutes",
    "☕ Break reminder set for 25 minutes",
    "🎯 Focus mode activated with gentle notifications",
    "💾 Session saved - can resume anytime"
  ]
}
```

#### GET /api/v1/research/{task_id}
Get research task status and results.

**Response:**
```json
{
  "task_id": "uuid",
  "session_id": "session-uuid",
  "status": "in_progress",
  "progress": 45,
  "results": [],
  "summary": "",
  "key_findings": [],
  "created_at": "2025-09-27T20:00:00Z",
  "attention_metrics": {
    "breaks": [],
    "focus_periods": [],
    "attention_score": 0
  }
}
```

#### DELETE /api/v1/research/{task_id}
Cancel a research task.

### Session Management

#### GET /api/v1/sessions/{session_id}
Get session information and history.

**Response:**
```json
{
  "session_id": "uuid",
  "task_ids": ["task-1", "task-2"],
  "created_at": "2025-09-27T20:00:00Z",
  "last_activity": "2025-09-27T20:15:00Z",
  "attention_state": "focused",
  "break_history": [
    {
      "type": "pause",
      "timestamp": "2025-09-27T20:25:00Z",
      "reason": "user_initiated"
    }
  ],
  "total_focus_minutes": 25
}
```

#### POST /api/v1/sessions/{session_id}/pause
Pause a session for break or interruption.

**Response:**
```json
{
  "message": "Session paused",
  "session_id": "uuid",
  "tip": "🧘 Take a break! Stretch, hydrate, or take a short walk."
}
```

#### POST /api/v1/sessions/{session_id}/resume
Resume a paused session with context reminder.

**Response:**
```json
{
  "message": "Session resumed",
  "session_id": "uuid",
  "context_reminder": "You were away for 5 minutes. Last completed: Python async research. Total focus time today: 25 minutes",
  "tip": "🎯 Welcome back! Let's continue where you left off."
}
```

## WebSocket for Real-time Updates

### WS /ws/{task_id}
Connect to receive real-time progress updates for a research task.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/task-uuid');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Message Types:**

1. **Connected**:
```json
{
  "type": "connected",
  "task_id": "uuid",
  "message": "Connected to progress tracker"
}
```

2. **Progress Update**:
```json
{
  "type": "progress",
  "task_id": "uuid",
  "progress": 45,
  "stage": "searching",
  "message": "Analyzing 5 sources",
  "attention_level": "focused",
  "break_suggested": false,
  "timestamp": "2025-09-27T20:00:00Z"
}
```

3. **Completion**:
```json
{
  "type": "completed",
  "task_id": "uuid",
  "message": "Research completed successfully",
  "summary": "Key findings..."
}
```

4. **Error**:
```json
{
  "type": "error",
  "task_id": "uuid",
  "message": "Error details"
}
```

## ADHD Features

### Attention State Detection

The API monitors attention states and provides recommendations:

- **warming_up** (0-5 min): Getting started
- **focused** (5-20 min): Optimal productivity
- **sustained_focus** (20-45 min): Deep work mode
- **potential_hyperfocus** (45-90 min): Consider a break
- **hyperfocus_alert** (90+ min): Break strongly recommended

### Break Management

- Automatic break reminders every 25 minutes (Pomodoro)
- Break history tracking
- Context preservation during breaks
- Gentle re-engagement after breaks

### Session Persistence

- Auto-save every 30 seconds
- Restore sessions after interruptions
- Track total focus time and productivity metrics
- Context reminders when resuming

### Progress Tracking

- Real-time progress via WebSocket
- Visual progress indicators
- Stage-by-stage updates
- Estimated completion time

## Configuration

### Environment Variables

```bash
# API Configuration
API_PORT=8000
WORKSPACE_PATH=/path/to/workspace
SESSION_STORAGE_PATH=/path/to/sessions

# Search Engine APIs
EXA_API_KEY=your-key
TAVILY_API_KEY=your-key
PERPLEXITY_API_KEY=your-key
CONTEXT7_API_KEY=your-key

# Debug
DEBUG=false
```

### ADHD Configuration Options

```json
{
  "break_interval": 25,          // Minutes between breaks
  "focus_duration": 25,          // Target focus duration
  "notification_style": "gentle", // gentle, moderate, assertive
  "hyperfocus_protection": true,  // Alert for extended focus
  "visual_progress": true         // Enable progress visualization
}
```

## Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
python test_api.py
```

### WebSocket Test
```bash
python -c "
import asyncio
import websockets
import json

async def test():
    uri = 'ws://localhost:8000/ws/test-task'
    async with websockets.connect(uri) as ws:
        msg = await ws.recv()
        print(json.loads(msg))

asyncio.run(test())
"
```

## Error Handling

The API uses standard HTTP status codes:

- **200**: Success
- **404**: Resource not found
- **422**: Validation error
- **500**: Internal server error
- **503**: Service unavailable

Error responses include detailed messages:
```json
{
  "detail": "Specific error description"
}
```

## Rate Limiting

- Maximum 5 concurrent research tasks
- Session timeout: 2 hours
- WebSocket ping interval: 30 seconds
- Auto-save interval: 30 seconds

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **CORS**: Configure appropriately for production
3. **Session Storage**: Use secure file permissions
4. **WebSocket**: Implement authentication for production
5. **Rate Limiting**: Prevent abuse with request limits

## Deployment

### Development
```bash
./start_api.sh --debug
```

### Production
```bash
# Use proper process manager
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Next Steps

1. **Add Authentication**: Implement JWT-based auth
2. **Database Integration**: PostgreSQL for production sessions
3. **Caching**: Redis for performance optimization
4. **Monitoring**: Prometheus metrics endpoint
5. **UI Development**: React Ink terminal interface