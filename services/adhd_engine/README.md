# ADHD Engine - Comprehensive ADHD Accommodation Platform

The ADHD Engine provides intelligent, real-time assistance for neurodivergent developers through a suite of specialized microservices. This platform reduces cognitive load, prevents burnout, and optimizes development workflows for ADHD brains.

## 🏗️ Architecture Overview

### Core Engine (`main.py`)
- **FastAPI Application** with 6 API endpoints and 6 background monitors
- **Redis Integration** for high-performance state management
- **ConPort Integration** for knowledge graph and decision logging
- **CORS Configuration** with secure origin validation

### Service Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ADHD Engine   │────│  Shared Redis    │────│   ConPort KG    │
│   (FastAPI)     │    │   Cache & State  │    │   Knowledge     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ├─ Activity Capture      ├─ ADHD Dashboard      ├─ Decision Logging
         ├─ Break Suggester       ├─ ADHD Notifier       ├─ Pattern Storage
         ├─ Complexity Coord.     ├─ Energy Trends       ├─ Session Context
         ├─ Context Switch Tr.    └─ Workspace Watcher   └─ Progress Tracking
         └─ Cognitive Load Mon.
```

## 🔌 API Endpoints

### Core Assessment APIs

#### `POST /api/v1/assess-task`
**Purpose**: Evaluate task complexity for ADHD-safe planning
**Request Body**:
```json
{
  "task_description": "Implement user authentication system",
  "estimated_hours": 8,
  "technologies": ["Python", "FastAPI", "PostgreSQL"],
  "dependencies": ["user model", "JWT library"]
}
```
**Response**:
```json
{
  "complexity_score": 0.73,
  "cognitive_load": "HIGH",
  "recommended_chunks": 4,
  "break_frequency": "25min",
  "energy_requirement": "HIGH",
  "attention_span_needed": "90min"
}
```

#### `GET /api/v1/user-profile`
**Purpose**: Retrieve current ADHD profile and preferences
**Response**:
```json
{
  "attention_span_avg": 25,
  "energy_patterns": {
    "peak_hours": ["10:00-12:00", "15:00-17:00"],
    "low_energy_hours": ["14:00-15:00", "20:00-22:00"]
  },
  "preferred_session_length": 25,
  "break_preferences": {
    "reminder_style": "gentle",
    "activities": ["stretch", "walk", "meditate"]
  },
  "notification_settings": {
    "break_reminders": true,
    "energy_alerts": true,
    "focus_shift_warnings": true
  }
}
```

#### `GET /api/v1/energy-level`
**Purpose**: Get current energy assessment
**Response**:
```json
{
  "current_level": 0.65,
  "trend": "increasing",
  "peak_predicted": "11:30",
  "recommendations": [
    "High-energy task suitable",
    "Complex problem solving optimal"
  ]
}
```

#### `GET /api/v1/attention-state`
**Purpose**: Real-time attention monitoring
**Response**:
```json
{
  "state": "focused",
  "confidence": 0.82,
  "distraction_risk": "LOW",
  "time_to_break": "18min",
  "context_switches_last_hour": 2
}
```

#### `GET /api/v1/cognitive-load`
**Purpose**: Current cognitive load assessment
**Response**:
```json
{
  "current_load": 0.45,
  "capacity_remaining": 0.55,
  "overload_risk": "LOW",
  "recovery_time_needed": "5min"
}
```

#### `GET /api/v1/break-recommendation`
**Purpose**: Intelligent break suggestions
**Response**:
```json
{
  "should_break": false,
  "reason": "Optimal focus window active",
  "next_break_in": "22min",
  "suggested_duration": "5min",
  "recommended_activity": "stretch",
  "expected_benefit": "15% productivity increase"
}
```

## 🧠 Specialized Services

### ADHD Dashboard (`services/adhd-dashboard/`)
**Purpose**: REST API backend for ADHD metrics visualization
**Port**: 8097
**Health Check**: `GET /health`

**API Endpoints**:
- `GET /api/metrics` - Current ADHD metrics
- `GET /api/adhd-state` - Current attention state
- `GET /api/sessions/today` - Today's session data
- `GET /api/analytics/trends` - Historical trends

### ADHD Notifier (`services/adhd-notifier/`)
**Purpose**: Intelligent notification system for ADHD accommodations
**Features**:
- Break reminders (25-minute focus sessions)
- Attention alerts
- Multiple notification methods (terminal, voice, system)
- Priority-based notifications
- Redis-based state management

### Break Suggester (`services/break-suggester/`)
**Purpose**: Proactive break suggestions using cognitive load patterns
**Features**:
- 25-minute ADHD-optimized focus sessions
- Cognitive load monitoring
- Automatic break recommendations
- Session state tracking

### Complexity Coordinator (`services/complexity-coordinator/`)
**Purpose**: Centralized code complexity assessments
**Features**: 0.0-1.0 complexity scoring for ADHD-safe reading assessment

### Context Switch Tracker (`services/context-switch-tracker/`)
**Purpose**: Monitor and optimize context switching patterns
**Features**: Track context switches and provide transition assistance

### Energy Trends (`services/energy-trends/`)
**Purpose**: Track developer energy patterns throughout the day
**Features**: Daily energy pattern analysis and optimization recommendations

### Workspace Watcher (`services/workspace-watcher/`)
**Purpose**: Monitor workspace changes and activity
**Features**:
- App detection
- File activity monitoring
- Event emission for other services

### Activity Capture (`services/activity-capture/`)
**Purpose**: Real-time activity pattern analysis
**Features**:
- Cognitive load assessment
- ADHD event subscription
- Activity pattern learning

## 🔧 Configuration

### Environment Variables

#### Required
```bash
# Redis connection
REDIS_URL=redis://localhost:6379

# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8097
```

#### Optional ADHD Settings
```bash
# Session Management
SESSION_THRESHOLD_MINUTES=25
BREAK_FREQUENCY_MINUTES=25

# Complexity Thresholds
COMPLEXITY_THRESHOLD=0.6

# Notification Settings
NOTIFICATION_METHODS=terminal,system
```

### Docker Deployment

```yaml
version: '3.8'
services:
  adhd-engine:
    build: .
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8097
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific service tests
pytest tests/test_engine.py -v
pytest tests/test_adhd_apis.py -v
```

### Integration Tests
```bash
# Test with Redis
pytest tests/integration/ -v

# Test with ConPort
pytest tests/integration/test_conport_integration.py -v
```

### Security Tests
```bash
# CORS security tests
pytest tests/security/test_cors.py -v

# Input validation tests
pytest tests/security/test_input_validation.py -v
```

## 📊 Monitoring & Health Checks

### Health Endpoints
```bash
# Main engine health
curl http://localhost:8080/health

# Dashboard health
curl http://localhost:8097/health

# Individual services health
curl http://localhost:8098/health  # notifier
curl http://localhost:8099/health  # break-suggester
```

### Metrics Collection
- **Prometheus Integration**: `/metrics` endpoint for monitoring
- **Custom Metrics**:
  - API response times
  - Error rates
  - ADHD state distributions
  - Break suggestion acceptance rates

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **ADHD Events**: Special logging for accommodation events

## 🔗 Integration Points

### ConPort Knowledge Graph
- **Decision Logging**: All architectural decisions automatically logged
- **Pattern Storage**: Reusable ADHD accommodation patterns
- **Progress Tracking**: Session and task progress preservation
- **Context Preservation**: Mental model maintenance across interruptions

### MCP Server Integration
- **Serena**: Code complexity assessments and navigation assistance
- **Zen**: Multi-model reasoning with ADHD-aware prompting
- **Context7**: Documentation lookup for ADHD-friendly patterns

### Development Workflow Integration
1. **Session Start**: Query ADHD state and energy levels
2. **Task Planning**: Use complexity scoring for realistic estimates
3. **Active Development**: Monitor for break suggestions and fatigue
4. **Context Switching**: Provide gentle re-orientation when detected
5. **Session End**: Log patterns and preserve context

## 🛡️ Security Features

### Authentication
- **API Key Authentication**: X-API-Key header required
- **Service-to-Service**: Mutual TLS for internal communications
- **User Sessions**: Secure session management with Redis

### Input Validation
- **URL Validation**: Regex-based origin validation
- **Input Sanitization**: All user inputs validated and sanitized
- **Rate Limiting**: Token bucket algorithm for API protection

### CORS Security
- **Origin Whitelisting**: Only explicitly allowed origins permitted
- **Method Restrictions**: Limited to necessary HTTP methods
- **Header Validation**: Strict header validation and filtering

## 🚀 Performance Optimization

### Caching Strategy
- **Redis Caching**: High-frequency queries cached for 5-15 minutes
- **Complexity Scores**: Cached for 30 minutes to reduce computation
- **User Profiles**: Cached for session duration

### Background Processing
- **Async Operations**: Non-blocking background monitors
- **Queue Processing**: Redis queues for notification delivery
- **Batch Operations**: Efficient bulk data processing

### Scalability Considerations
- **Horizontal Scaling**: Stateless design allows multiple instances
- **Database Sharding**: Redis cluster support for high availability
- **Load Balancing**: Nginx or similar for API distribution

## 📚 API Documentation

### OpenAPI Specification
- **Swagger UI**: Available at `/docs` when running locally
- **ReDoc**: Alternative documentation at `/redoc`
- **OpenAPI JSON**: Available at `/openapi.json`

### Example Usage

#### Assess Task Complexity
```python
import requests

response = requests.post("http://localhost:8080/api/v1/assess-task", json={
    "task_description": "Implement user authentication with JWT",
    "estimated_hours": 4,
    "technologies": ["Python", "FastAPI", "JWT"]
})

result = response.json()
print(f"Complexity: {result['complexity_score']}")
print(f"Recommended breaks every: {result['break_frequency']}")
```

#### Get Current ADHD State
```python
response = requests.get("http://localhost:8080/api/v1/attention-state")
state = response.json()

if state['state'] == 'scattered':
    print("Consider breaking task into smaller chunks")
elif state['state'] == 'focused':
    print("Optimal time for complex problem solving")
```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd dopemux/services/adhd_engine

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start development server
python main.py
```

### Code Standards
- **Type Hints**: All functions must have proper type annotations
- **Docstrings**: Comprehensive docstrings for all public APIs
- **Testing**: 90%+ test coverage required
- **Security**: All inputs validated, no security vulnerabilities

### ADHD Accommodation Guidelines
- **Progressive Disclosure**: Show essential information first
- **25-minute Sessions**: Respect ADHD-optimized work periods
- **Gentle Communication**: Use encouraging, non-judgmental language
- **Context Preservation**: Maintain mental models across interruptions

---

**Status**: ✅ Production-ready ADHD accommodation platform
**Services**: 8 microservices with comprehensive API coverage
**Integration**: Full ConPort and MCP server integration
**Security**: Comprehensive input validation and CORS protection
**Performance**: Redis caching and async processing for optimal performance
