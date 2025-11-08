# ADHD Engine Phase 3: Proactive Intelligence Implementation

## Overview

Phase 3 transforms the ADHD Engine from a reactive accommodation system into a proactive, intelligent platform that anticipates user needs and continuously learns from patterns. This implementation adds ML prediction capabilities, performance monitoring, and background intelligence gathering.

## Phase 3.3: Core API Extensions

### ML Prediction Integration

All 6 core API endpoints now include optional `ml_prediction` fields containing machine learning insights:

```json
{
  "energy_level": "HIGH",
  "confidence": 0.8,
  "last_updated": "2025-11-07T20:30:00Z",
  "ml_prediction": {
    "predicted_value": "HIGH",
    "confidence": 0.85,
    "explanation": "Based on time patterns, you typically have HIGH energy at 2pm on Thursdays",
    "ml_used": true
  }
}
```

### Redis Caching Layer

Implemented endpoint-specific caching to achieve <100ms latency targets:

- **Energy Level**: 5-minute TTL (relatively stable)
- **Attention State**: 3-minute TTL (moderately dynamic)
- **Break Recommendations**: 1-minute TTL (time-sensitive)
- **Activity Updates**: 1-minute TTL (event-driven)

### Prometheus Metrics

Added comprehensive performance monitoring:

```prometheus
# API Performance
adhd_api_requests_total{endpoint="energy", method="GET", status="success"} 1250
adhd_api_request_duration_seconds{endpoint="energy", quantile="0.95"} 0.023

# Cache Performance
adhd_cache_hits_total{endpoint="energy"} 890
adhd_cache_misses_total{endpoint="energy"} 360

# ML Metrics
adhd_ml_predictions_total{endpoint="energy", prediction_type="energy"} 450
adhd_ml_prediction_confidence{endpoint="energy", quantile="0.5"} 0.82
```

### Performance Benchmarking

Created `scripts/benchmark_api.py` for load testing:

```bash
# Test energy endpoint with 100 concurrent requests
python scripts/benchmark_api.py \
  --endpoint /api/v1/energy-level/{user_id} \
  --iterations 100 \
  --concurrency 10
```

**Expected Results**:
- Average Response Time: <100ms
- Cache Hit Rate: >80%
- Error Rate: 0%

## Phase 3.4: Background Prediction Service

### Architecture

The Background Prediction Service runs as an asyncio task within the ADHD Engine, providing continuous ML prediction updates without impacting API performance.

### Key Components

#### BackgroundPredictionService Class

```python
class BackgroundPredictionService:
    """
    Continuous ML prediction monitoring with <5% performance overhead.

    Features:
    - User scanning every 5 minutes
    - Concurrent prediction limiting (max 5 simultaneous)
    - Performance overhead monitoring and auto-adjustment
    - Graceful shutdown handling
    """
```

#### Service Features

1. **Continuous User Monitoring**
   - Scans all active users every 5 minutes
   - Updates energy and attention predictions proactively
   - Stores results in Redis with 10-minute TTL

2. **Performance Controls**
   - Semaphore-based concurrency limiting
   - Overhead measurement and automatic adjustment
   - Redis connection pooling for efficiency

3. **Error Resilience**
   - Individual user failures don't stop the service
   - Graceful degradation when ML engine unavailable
   - Comprehensive logging for debugging

### Configuration

```python
# Environment variables
ENABLE_BACKGROUND_PREDICTIONS=true  # Enable/disable service
REDIS_URL=redis://localhost:6379     # Redis connection
WORKSPACE_ID=/path/to/project       # ConPort workspace
```

### Monitoring Endpoints

```http
# Service status
GET /background-service/status

# Response
{
  "running": true,
  "predictions_made": 1250,
  "users_being_monitored": 3,
  "avg_overhead_seconds": 0.003,
  "monitoring_interval_seconds": 300
}
```

### Integration Points

The background service integrates with:

- **ADHD Engine**: Starts during engine initialization
- **Redis**: Stores predictions and service metrics
- **ML Engine**: Calls predictive models for updates
- **Health Checks**: Reports status in engine health endpoint

## Technical Implementation

### API Schema Extensions

```python
class EnergyLevelResponse(BaseModel):
    energy_level: str
    confidence: float
    last_updated: datetime
    ml_prediction: Optional[MLPrediction] = None  # NEW

class MLPrediction(BaseModel):
    predicted_value: Any
    confidence: float
    explanation: str
    ml_used: bool
```

### Cache Implementation

```python
# Cache key generation
def _make_cache_key(endpoint: str, user_id: str, **params) -> str:
    return f"adhd:{endpoint}:{user_id}:{':'.join(f'{k}:{v}' for k, v in params.items())}"

# Caching pattern
cache_key = _make_cache_key("energy", user_id)
cached = await cache.get(cache_key)
if cached:
    return EnergyLevelResponse.model_validate_json(cached)

# Generate response, cache it
response = EnergyLevelResponse(...)
await cache.set(cache_key, response.model_dump_json(), ttl=ENERGY_CACHE_TTL)
```

### Background Service Lifecycle

```python
# Initialization
async def initialize(self):
    self.redis_client = redis.from_url(settings.redis_url)
    self.predictive_engine = PredictiveADHDEngine(self.workspace_id)

# Monitoring loop
async def _continuous_user_monitoring(self):
    while self.running:
        await self._scan_and_update_users()
        await asyncio.sleep(self.monitoring_interval)

# Prediction updates
async def _update_user_predictions(self, user_id: str):
    async with self.prediction_semaphore:
        energy_pred, energy_conf, energy_exp = await self.predictive_engine.predict_energy_level(user_id)
        # Store in Redis...
```

## Performance Characteristics

### Latency Targets
- **Cache Hit**: <10ms (Redis retrieval + JSON parsing)
- **Cache Miss**: <100ms (ML prediction + caching)
- **Background Service Overhead**: <5% of total system resources

### Scalability
- **Concurrent Users**: Scales to 100+ users with semaphore control
- **Prediction Frequency**: Adjustable monitoring intervals (default 5 minutes)
- **Memory Usage**: Bounded by Redis TTL and semaphore limits

### Reliability
- **Uptime**: 99.9% with automatic error recovery
- **Data Consistency**: Redis atomic operations
- **Graceful Degradation**: Continues operation when components fail

## Testing Strategy

### Unit Tests
```python
class TestBackgroundPredictionService:
    async def test_service_initialization(self):
        service = BackgroundPredictionService("/workspace")
        await service.initialize()
        assert service.redis_client is not None

    async def test_prediction_updates(self):
        # Mock Redis and ML engine
        # Test prediction storage and retrieval
```

### Integration Tests
```python
class TestAPICaching:
    async def test_energy_level_cache_hit(self):
        # Populate cache, verify hit behavior
        # Check metrics are recorded

    async def test_background_service_status(self):
        # Verify status endpoint returns correct data
```

### Performance Tests
```bash
# Load testing
python scripts/benchmark_api.py --endpoint /api/v1/energy-level/{user_id} --iterations 1000 --concurrency 50

# Expected results:
# - P95 latency: <100ms
# - Cache hit rate: >80%
# - Background service overhead: <5%
```

## Configuration Guide

### Environment Variables

```bash
# Core settings
ENABLE_ML_PREDICTIONS=true
ENABLE_BACKGROUND_PREDICTIONS=true
REDIS_URL=redis://localhost:6379
WORKSPACE_ID=/path/to/project

# Performance tuning
ENERGY_CACHE_TTL=300          # 5 minutes
ATTENTION_CACHE_TTL=180       # 3 minutes
BREAK_CACHE_TTL=60            # 1 minute
ACTIVITY_CACHE_TTL=60         # 1 minute

# Background service
MONITORING_INTERVAL=300       # 5 minutes between scans
MAX_CONCURRENT_PREDICTIONS=5  # Limit concurrent ML calls
```

### Docker Deployment

```yaml
services:
  adhd-engine:
    environment:
      - ENABLE_BACKGROUND_PREDICTIONS=true
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
```

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Cache Performance**
   - Hit rate should be >80%
   - Miss rate indicates cache TTL tuning needed

2. **ML Prediction Quality**
   - Confidence scores should average >0.7
   - Monitor prediction accuracy over time

3. **Background Service Health**
   - Should show "running": true
   - Overhead should stay <5%
   - Predictions made should increase over time

### Troubleshooting

**High Latency Issues**
- Check Redis connection health
- Verify cache TTL settings
- Monitor background service overhead

**Low Cache Hit Rate**
- Reduce TTL values for more dynamic data
- Check cache key consistency
- Monitor user behavior patterns

**Background Service Problems**
- Check Redis connectivity
- Verify ML engine availability
- Monitor semaphore usage

## Future Enhancements

### Phase 3.5: User Control Layer
- Prediction confidence override mechanisms
- Customization settings interface
- User feedback integration for model improvement

### Phase 3.6: Trust Building Layer
- Prediction accuracy tracking and visualization
- User feedback mechanisms
- Gradual automation adoption controls

This implementation establishes the ADHD Engine as a truly proactive, intelligent accommodation system that learns and adapts to user needs continuously.