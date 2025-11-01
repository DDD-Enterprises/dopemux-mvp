# Shared Services Infrastructure

Centralized services and utilities that power the Dopemux Ultra UI ecosystem. These shared components provide common functionality, configuration management, monitoring, and service discovery across all ADHD Engine microservices.

## 🏗️ Architecture Overview

### Service Components
```
Shared Infrastructure
├── Configuration Management (config.py)
├── Service Discovery (service_discovery.py)
├── Monitoring & Metrics (monitoring.py)
├── Dependency Injection (dependency_container.py)
├── Storage Abstraction (storage.py)
└── Redis Connection Pool (redis_pool.py)
```

### Integration Pattern
```python
# All services follow this pattern
from shared.config import settings
from shared.monitoring import monitor
from shared.service_discovery import registry
from shared.dependency_container import container

# Service initialization
service = MyService(
    config=settings,
    monitor=monitor,
    registry=registry
)
container.register(service)
```

## ⚙️ Configuration Management (`config.py`)

### Features
- **Environment-Based Configuration**: Development, staging, production profiles
- **Validation**: Runtime configuration validation with helpful error messages
- **Dynamic Reloading**: Hot configuration updates without service restart
- **Type Safety**: Full type annotations and validation

### Configuration Classes

#### DatabaseConfig
```python
@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    url: str = "postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph"
    pool_min_size: int = 5
    pool_max_size: int = 20
    connection_timeout: float = 30.0
    command_timeout: float = 60.0
```

#### RedisConfig
```python
@dataclass
class RedisConfig:
    """Redis connection configuration."""
    url: str = "redis://localhost:6379"
    db: int = 0
    max_connections: int = 10
    retry_on_timeout: bool = True
    socket_timeout: float = 5.0
```

#### ServiceConfig
```python
@dataclass
class ServiceConfig:
    """General service configuration."""
    name: str
    version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    health_check_interval: int = 30
```

### Usage
```python
from shared.config import settings

# Access configuration
database_url = settings.database.url
redis_config = settings.redis
service_name = settings.service.name

# Environment-specific logic
if settings.environment == Environment.PRODUCTION:
    # Production-specific setup
    pass
```

## 🔍 Service Discovery (`service_discovery.py`)

### Features
- **Automatic Registration**: Services auto-register on startup
- **Health Monitoring**: Continuous health checks and status updates
- **Load Balancing**: Intelligent service selection based on health/load
- **Service Dependencies**: Automatic dependency resolution

### Service Registration
```python
from shared.service_discovery import registry

# Register service
service_id = registry.register(
    name="adhd-engine",
    host="localhost",
    port=8080,
    health_endpoint="/health",
    tags=["adhd", "api", "microservice"]
)

# Update service metadata
registry.update_metadata(service_id, {
    "version": "2.0.0",
    "capabilities": ["assessment", "monitoring", "break_suggestions"]
})
```

### Service Discovery
```python
# Find healthy services
adhd_services = registry.discover(
    name="adhd-engine",
    tags=["healthy"],
    limit=3
)

# Get service endpoint
for service in adhd_services:
    endpoint = f"http://{service.host}:{service.port}"
    # Use service...
```

### Health Monitoring
```python
# Check service health
health_status = registry.check_health(service_id)

# Get service statistics
stats = registry.get_statistics(service_id)
print(f"Requests: {stats.requests_total}")
print(f"Errors: {stats.errors_total}")
print(f"Response time: {stats.avg_response_time}ms")
```

## 📊 Monitoring & Metrics (`monitoring.py`)

### Features
- **Prometheus Integration**: Standard metrics export
- **Custom Metrics**: ADHD-specific monitoring
- **Performance Tracking**: Response times, error rates, throughput
- **Alert Integration**: Configurable alerting thresholds

### Metric Types

#### Performance Metrics
```python
from shared.monitoring import monitor

# Track API response time
with monitor.timer("api.request.duration", labels={"endpoint": "/assess-task"}):
    result = assess_task(request)

# Increment counter
monitor.increment("api.requests.total", labels={"method": "POST", "status": "200"})

# Record gauge value
monitor.gauge("adhd.complexity_score", value=0.73, labels={"task_type": "feature"})
```

#### ADHD-Specific Metrics
```python
# Attention state tracking
monitor.gauge("adhd.attention_state", value=0.85, labels={"state": "focused"})

# Cognitive load monitoring
monitor.histogram("adhd.cognitive_load", value=0.45, labels={"service": "engine"})

# Break suggestion metrics
monitor.counter("adhd.break_suggestions", labels={"accepted": True, "reason": "fatigue"})
```

### Alert Configuration
```python
# Configure alerts
monitor.add_alert(
    name="high_error_rate",
    condition="rate(errors_total[5m]) > 0.05",
    severity="warning",
    description="Error rate above 5% for 5 minutes"
)

monitor.add_alert(
    name="adhd_burnout_risk",
    condition="adhd_cognitive_load > 0.8",
    severity="critical",
    description="High cognitive load detected - break recommended"
)
```

## 🏭 Dependency Injection (`dependency_container.py`)

### Features
- **Service Wiring**: Clean dependency management and injection
- **Lifecycle Management**: Proper startup/shutdown handling
- **Testing Support**: Easy mocking and dependency replacement
- **Circular Dependency Detection**: Automatic detection and prevention

### Service Registration
```python
from shared.dependency_container import container

# Register service implementations
container.register(DatabaseService, singleton=True)
container.register(RedisCache, singleton=True)
container.register(TaskAssessor)

# Register with interface
container.register(ITaskAssessor, TaskAssessor)

# Register factory function
container.register(CacheService, lambda: RedisCache(settings.redis.url))
```

### Dependency Injection
```python
class ADHDAssessmentService:
    def __init__(self, database: DatabaseService, cache: ICache):
        self.database = database
        self.cache = cache

# Automatic injection
service = container.resolve(ADHDAssessmentService)
# Dependencies automatically resolved and injected
```

### Testing Support
```python
# Create test container
test_container = DependencyContainer()

# Register mocks
test_container.register(DatabaseService, MockDatabase())
test_container.register(ICache, MockCache())

# Resolve with mocks
test_service = test_container.resolve(ADHDAssessmentService)
```

## 💾 Storage Abstraction (`storage.py`)

### Features
- **Unified Interface**: Consistent storage operations across backends
- **Multiple Backends**: Redis, PostgreSQL, file system support
- **Caching Layer**: Automatic caching with TTL support
- **Serialization**: Automatic JSON serialization/deserialization

### Storage Operations
```python
from shared.storage import storage

# Store user profile
await storage.set("user:123:profile", {
    "attention_span": 25,
    "energy_patterns": ["10:00-12:00"],
    "break_preferences": {"reminder_style": "gentle"}
}, ttl=3600)  # 1 hour

# Retrieve with caching
profile = await storage.get("user:123:profile")

# Store complex object
assessment_result = {
    "task_id": "feature-123",
    "complexity_score": 0.73,
    "recommendations": ["break every 25min", "focus on mornings"]
}
await storage.set(f"assessment:{task_id}", assessment_result)

# Batch operations
await storage.set_many({
    "key1": "value1",
    "key2": "value2",
    "key3": {"complex": "object"}
})

# Get multiple keys
results = await storage.get_many(["key1", "key2", "key3"])
```

### Storage Backends

#### Redis Backend (Default)
```python
# High-performance caching and session storage
redis_storage = RedisStorage(settings.redis.url, db=0)
```

#### PostgreSQL Backend
```python
# Persistent storage for large datasets
pg_storage = PostgreSQLStorage(settings.database.url, table="key_value_store")
```

#### File System Backend
```python
# Local development and testing
fs_storage = FileSystemStorage("/tmp/dopemux-storage")
```

## 🔗 Redis Connection Pool (`redis_pool.py`)

### Features
- **Connection Pooling**: Efficient Redis connection management
- **Health Monitoring**: Automatic connection health checks
- **Failover Support**: Graceful handling of Redis failures
- **Performance Optimization**: Pipelining and batch operations

### Usage
```python
from shared.redis_pool import get_redis_pool

# Get Redis connection pool
redis = await get_redis_pool()

# Use like regular aioredis
await redis.set("key", "value")
value = await redis.get("key")

# Pipeline operations for performance
async with redis.pipeline() as pipe:
    pipe.set("key1", "value1")
    pipe.set("key2", "value2")
    pipe.expire("key1", 3600)
    await pipe.execute()
```

### ADHD-Specific Redis Usage
```python
# Attention state caching
await redis.setex("attention:state:user123", 300, "focused:0.85")

# Cognitive load tracking
await redis.hset("cognitive:load", "current", "0.45")
await redis.hset("cognitive:load", "peak_today", "0.78")

# Break suggestion queue
await redis.lpush("breaks:pending", "user123:25min_break")

# Session data with TTL
session_data = {
    "start_time": datetime.now().isoformat(),
    "task_count": 0,
    "break_count": 0,
    "energy_levels": []
}
await redis.setex(f"session:{session_id}", 86400, json.dumps(session_data))  # 24 hours
```

## 🔧 Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=adhd-engine
SERVICE_VERSION=2.0.0
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dopemux
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=10

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/...

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Service Initialization
```python
from shared import init_shared_services

# Initialize all shared services
config, monitor, registry, container, storage, redis = await init_shared_services()

# Services are now ready to use
logger.info(f"Service {config.service.name} v{config.service.version} initialized")
```

## 🧪 Testing

### Unit Tests
```bash
# Test individual components
pytest shared/tests/test_config.py -v
pytest shared/tests/test_monitoring.py -v
pytest shared/tests/test_storage.py -v
```

### Integration Tests
```bash
# Test service interactions
pytest shared/tests/integration/test_service_discovery.py -v
pytest shared/tests/integration/test_dependency_injection.py -v
```

### Mock Services for Testing
```python
from shared.testing import MockRedis, MockDatabase, MockMonitor

# Use mocks in tests
@pytest.fixture
async def mock_services():
    return {
        "redis": MockRedis(),
        "database": MockDatabase(),
        "monitor": MockMonitor()
    }
```

## 📊 Monitoring & Observability

### Health Checks
```bash
# Individual service health
curl http://localhost:8080/health

# Shared services health
curl http://localhost:8081/health/shared

# Metrics endpoint
curl http://localhost:9090/metrics
```

### Logging
```python
import structlog

# Structured logging with shared configuration
logger = structlog.get_logger()

logger.info("service_started", service="adhd-engine", version="2.0.0")
logger.error("redis_connection_failed", error=str(e), retry_count=3)
```

### Tracing
```python
from shared.monitoring import tracer

# Distributed tracing
with tracer.trace("assess_task") as span:
    span.set_tag("task_type", "feature")
    span.set_tag("complexity", assessment.complexity_score)

    result = await perform_assessment(task)
    span.set_tag("result", "success")

    return result
```

## 🔒 Security

### Authentication & Authorization
```python
from shared.security import JWTManager, APIKeyValidator

# JWT token management
jwt_manager = JWTManager(settings.security.jwt_secret)

# API key validation
api_validator = APIKeyValidator(settings.security.api_keys)

# Validate requests
async def authenticate_request(request):
    token = request.headers.get("Authorization")
    if token:
        payload = jwt_manager.decode_token(token)
        return payload.get("user_id")

    api_key = request.headers.get("X-API-Key")
    if api_key:
        return await api_validator.validate(api_key)

    raise HTTPException(status_code=401, detail="Authentication required")
```

### Input Validation
```python
from shared.validation import Validator

validator = Validator()

# Validate ADHD assessment input
assessment_data = {
    "task_description": "Implement authentication",
    "estimated_hours": 8,
    "technologies": ["Python", "FastAPI"]
}

is_valid, errors = validator.validate(assessment_data, "adhd_assessment")
if not is_valid:
    raise ValueError(f"Validation failed: {errors}")
```

### Rate Limiting
```python
from shared.rate_limiting import RateLimiter

limiter = RateLimiter(storage=redis_storage)

# Apply rate limiting
@limiter.limit("10/minute")
async def assess_task_endpoint(request):
    # Endpoint logic here
    pass
```

## 🚀 Performance Optimization

### Connection Pooling
- **Database**: SQLAlchemy async engine with connection pooling
- **Redis**: aioredis connection pool with automatic reconnection
- **HTTP**: aiohttp client session reuse

### Caching Strategies
```python
from shared.caching import Cache

cache = Cache(redis_storage)

# Cache with TTL
@cache.cached(ttl=300)  # 5 minutes
async def get_user_profile(user_id: str):
    return await database.get_user_profile(user_id)

# Cache with custom key
@cache.cached(key_func=lambda user_id, task_type: f"profile:{user_id}:{task_type}")
async def get_task_preferences(user_id: str, task_type: str):
    return await database.get_preferences(user_id, task_type)
```

### Async Optimization
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# CPU-bound operations in thread pool
executor = ThreadPoolExecutor(max_workers=4)

async def complex_calculation(data):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, sync_complex_calculation, data)
    return result

# I/O-bound operations with proper async
async def fetch_external_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## 📈 Scaling Considerations

### Horizontal Scaling
```yaml
# Docker Compose for scaled deployment
version: '3.8'
services:
  adhd-engine-1:
    image: dopemux/adhd-engine:latest
    environment:
      - SERVICE_ID=engine-1
    depends_on:
      - redis
      - postgres

  adhd-engine-2:
    image: dopemux/adhd-engine:latest
    environment:
      - SERVICE_ID=engine-2
    depends_on:
      - redis
      - postgres
```

### Load Balancing
```python
# Service discovery with load balancing
service_instances = await registry.discover("adhd-engine", healthy_only=True)

# Round-robin load balancing
next_instance = service_instances[current_index % len(service_instances)]

# Weighted load balancing based on capacity
available_instances = sorted(service_instances, key=lambda s: s.capacity, reverse=True)
best_instance = available_instances[0]
```

### Database Sharding
```python
# Shard by user ID for scalability
def get_shard(user_id: str) -> str:
    shard_number = int(user_id, 16) % NUM_SHARDS
    return f"shard_{shard_number}"

shard = get_shard(user_id)
await storage.set(f"{shard}:user:{user_id}:profile", profile_data)
```

## 🤝 Contributing

### Development Setup
```bash
cd shared/

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Type checking
mypy shared/

# Linting
flake8 shared/
```

### Code Standards
- **Type Hints**: All functions must have complete type annotations
- **Async/Await**: Use async patterns consistently
- **Error Handling**: Comprehensive exception handling with proper logging
- **Documentation**: Detailed docstrings and usage examples
- **Testing**: 95%+ test coverage required

### Architecture Decisions
- **Dependency Injection**: Use container pattern for testability
- **Observer Pattern**: Event-driven architecture for loose coupling
- **Repository Pattern**: Data access abstraction
- **Strategy Pattern**: Configurable algorithms (caching, storage backends)

---

**Status**: ✅ Production-ready shared infrastructure
**Services**: 6 core components with comprehensive functionality
**Integration**: Seamless integration across all Dopemux services
**Performance**: Optimized for ADHD Engine workloads
**Scalability**: Horizontal scaling support with service discovery