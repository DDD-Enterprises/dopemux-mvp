# Phase 11: Production Features Specification

**Status**: 📋 Planning
**Phase**: Post-Architecture 3.0 Production Enhancements
**Target**: Production-grade authentication, caching, and analytics
**Timeline**: 5-7 days implementation

---

## Executive Summary

Phase 11 builds on Architecture 3.0's bidirectional PM ↔ Cognitive communication with production-grade features required for multi-user deployment:

1. **Authentication & Authorization** - Secure multi-user access with JWT tokens
2. **Redis Caching Layer** - Sub-50ms ADHD-aware caching for frequent queries
3. **Analytics & Monitoring** - Prometheus metrics + Grafana dashboards

**ADHD Considerations**: All features designed to maintain < 200ms latency targets and provide attention-safe performance.

---

## Feature 1: Authentication & Authorization

### Objectives

- [ ] Secure API endpoints with JWT-based authentication
- [ ] Support multi-user workspaces (isolation)
- [ ] Maintain ADHD latency targets (< 200ms with auth)
- [ ] Enable user-specific ADHD profiles

### Requirements

**Functional**:
- User registration and login
- JWT token generation and validation
- API key authentication for service-to-service
- Workspace-based data isolation
- User-specific ADHD state tracking

**Non-Functional**:
- Token validation: < 10ms overhead
- Password hashing: bcrypt with 12 rounds
- Token expiry: 1 hour (access), 7 days (refresh)
- Rate limiting: 100 req/min per user

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Client (UI, MCP)                                    │
└────────────┬────────────────────────────────────────┘
             │
             │ ← JWT Token (Authorization header)
             │
┌────────────▼────────────────────────────────────────┐
│  Integration Bridge (PORT 3016)                      │
│  • JWT Middleware (validate token)                   │
│  • Extract user_id from token                        │
│  • Add user context to request                       │
└────────────┬────────────────────────────────────────┘
             │
             │ ← user_id in query params
             │
┌────────────▼────────────────────────────────────────┐
│  Task-Orchestrator (PORT 3017)                       │
│  • User-scoped queries                               │
│  • Workspace isolation                               │
│  • User-specific ADHD state                          │
└─────────────────────────────────────────────────────┘
```

### Implementation Plan

**1. Authentication Service** (2 days)
```python
# services/auth/auth_service.py
class AuthService:
    """JWT-based authentication service."""

    async def register_user(email, password, adhd_profile):
        """Create new user with ADHD profile."""
        # Hash password (bcrypt, 12 rounds)
        # Store in PostgreSQL users table
        # Return user_id

    async def login(email, password):
        """Authenticate user and return JWT tokens."""
        # Verify password
        # Generate access token (1 hour)
        # Generate refresh token (7 days)
        # Return tokens

    async def validate_token(token):
        """Validate JWT token and extract user_id."""
        # Verify signature
        # Check expiry
        # Extract user_id
        # Return user context
```

**2. JWT Middleware** (1 day)
```python
# services/mcp-integration-bridge/middleware/auth.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def jwt_middleware(request: Request, call_next):
    """Validate JWT token on all requests."""
    # Extract Authorization header
    token = request.headers.get("Authorization")

    if not token:
        raise HTTPException(401, "Missing authentication token")

    # Validate token (< 10ms)
    user_context = await auth_service.validate_token(token)

    # Add user context to request state
    request.state.user = user_context

    # Continue request
    response = await call_next(request)
    return response
```

**3. User-Scoped Queries** (1 day)
```python
# services/task-orchestrator/query_server.py
@router.get("/tasks")
async def list_tasks(
    request: Request,  # Contains user context
    limit: int = 50
):
    """List tasks scoped to authenticated user."""
    user_id = request.state.user.id
    workspace_id = request.state.user.workspace_id

    # Query ConPort with user/workspace filter
    tasks = await conport_client.get_progress(
        workspace_id=workspace_id,
        filters={"user_id": user_id},
        limit=limit
    )
    return tasks
```

**4. Database Schema** (0.5 days)
```sql
-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    adhd_profile JSONB  -- Energy patterns, attention preferences
);

-- Workspaces table (multi-user isolation)
CREATE TABLE workspaces (
    workspace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workspace members
CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(workspace_id),
    user_id UUID REFERENCES users(user_id),
    role VARCHAR(50),  -- owner, member, viewer
    PRIMARY KEY (workspace_id, user_id)
);

-- Add user_id to progress_entry for scoping
ALTER TABLE conport.progress_entry ADD COLUMN user_id UUID REFERENCES users(user_id);
CREATE INDEX idx_progress_user ON conport.progress_entry(user_id);
```

### Testing

- [ ] Unit tests: Token generation, validation, expiry
- [ ] Integration tests: End-to-end auth flow
- [ ] Performance tests: Auth overhead < 10ms
- [ ] Security tests: Invalid tokens, expired tokens, token tampering

---

## Feature 2: Redis Caching Layer

### Objectives

- [ ] Reduce query latency to < 50ms for frequent requests
- [ ] Implement ADHD-aware cache TTL (30-60 seconds)
- [ ] Cache invalidation on state changes
- [ ] Maintain cache hit rate > 80%

### Requirements

**Functional**:
- Cache frequent queries (tasks, ADHD state, recommendations)
- User-scoped cache keys
- Automatic cache invalidation on updates
- Cache statistics for monitoring

**Non-Functional**:
- Cache hit latency: < 5ms
- Cache miss latency: < 70ms (fallback to DB)
- Cache TTL: 30 seconds (ADHD state), 60 seconds (tasks)
- Memory limit: 256MB Redis cache

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Query Request                                       │
└────────────┬────────────────────────────────────────┘
             │
             ▼
      ┌──────────────┐
      │ Cache Check  │
      │ Redis GET    │
      └──────┬───────┘
             │
        ┌────┴────┐
        │         │
   Cache Hit  Cache Miss
        │         │
        ▼         ▼
   Return     Query DB
   Cached     Store in
   Data       Cache
              Return
```

### Implementation Plan

**1. Cache Service** (1 day)
```python
# services/task-orchestrator/cache/redis_cache.py
import redis.asyncio as aioredis
import json
from typing import Optional, Any

class RedisCache:
    """ADHD-aware Redis caching layer."""

    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[dict]:
        """Get cached value (< 5ms target)."""
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(
        self,
        key: str,
        value: dict,
        ttl_seconds: int = 30
    ):
        """Cache value with TTL."""
        await self.redis.setex(
            key,
            ttl_seconds,
            json.dumps(value)
        )

    async def invalidate(self, pattern: str):
        """Invalidate cache by pattern."""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        info = await self.redis.info("stats")
        return {
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) /
                       (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0) + 1)
        }
```

**2. Cached Query Endpoints** (1 day)
```python
# services/task-orchestrator/query_server.py
from cache.redis_cache import RedisCache

cache = RedisCache(redis_url=REDIS_URL)

@router.get("/tasks")
async def list_tasks(
    request: Request,
    limit: int = 50
):
    """List tasks with caching."""
    user_id = request.state.user.id
    cache_key = f"tasks:{user_id}:limit:{limit}"

    # Check cache (< 5ms)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Cache miss: Query DB (< 70ms)
    tasks = await conport_client.get_progress(
        workspace_id=request.state.user.workspace_id,
        filters={"user_id": user_id},
        limit=limit
    )

    # Cache for 60 seconds
    await cache.set(cache_key, tasks, ttl_seconds=60)

    return tasks

@router.get("/adhd-state")
async def get_adhd_state(request: Request):
    """Get ADHD state with caching."""
    user_id = request.state.user.id
    cache_key = f"adhd_state:{user_id}"

    # Check cache
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Cache miss: Query ADHD engine
    adhd_state = await adhd_engine.get_current_state(user_id)

    # Cache for 30 seconds (ADHD state changes frequently)
    await cache.set(cache_key, adhd_state, ttl_seconds=30)

    return adhd_state
```

**3. Cache Invalidation** (0.5 days)
```python
# Invalidate on task updates
@router.post("/tasks/{task_id}")
async def update_task(task_id: str, request: Request):
    """Update task and invalidate cache."""
    user_id = request.state.user.id

    # Update task
    await conport_client.update_progress(task_id, ...)

    # Invalidate user's task cache
    await cache.invalidate(f"tasks:{user_id}:*")
    await cache.invalidate(f"recommendations:{user_id}:*")

    return {"status": "updated"}
```

**4. Cache Monitoring** (0.5 days)
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

cache_hits = Counter("cache_hits_total", "Cache hits")
cache_misses = Counter("cache_misses_total", "Cache misses")
cache_latency = Histogram("cache_latency_ms", "Cache operation latency")
```

### Testing

- [ ] Unit tests: Cache get/set/invalidate
- [ ] Integration tests: End-to-end caching
- [ ] Performance tests: Cache hit < 5ms, miss < 70ms
- [ ] Load tests: 80%+ hit rate under load

---

## Feature 3: Analytics & Monitoring

### Objectives

- [ ] Real-time performance metrics (Prometheus)
- [ ] ADHD latency dashboards (Grafana)
- [ ] Alerting for performance degradation
- [ ] User behavior analytics

### Requirements

**Functional**:
- Expose Prometheus metrics endpoint
- Track ADHD performance metrics
- Grafana dashboards for Architecture 3.0
- Alerts for P95 > 200ms

**Non-Functional**:
- Metrics collection overhead: < 1ms
- Metrics retention: 30 days
- Dashboard refresh: 5 seconds
- Alert latency: < 30 seconds

### Implementation Plan

**1. Prometheus Metrics** (1 day)
```python
# services/mcp-integration-bridge/metrics/prometheus.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration = Histogram(
    "http_request_duration_ms",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[10, 25, 50, 70, 100, 150, 200, 300, 500]
)

# ADHD performance metrics
adhd_query_latency = Histogram(
    "adhd_query_latency_ms",
    "ADHD-aware query latency",
    ["endpoint"],
    buckets=[10, 25, 50, 70, 100, 150, 200]
)

adhd_attention_safety = Gauge(
    "adhd_attention_safety",
    "Percentage of queries < 200ms",
    ["endpoint"]
)

# Cache metrics
cache_hit_rate = Gauge(
    "cache_hit_rate",
    "Cache hit rate percentage"
)

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**2. Metrics Middleware** (0.5 days)
```python
# Track metrics on every request
from time import time

async def metrics_middleware(request: Request, call_next):
    """Track request metrics."""
    start_time = time()

    # Process request
    response = await call_next(request)

    # Record metrics
    duration_ms = (time() - start_time) * 1000

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration_ms)

    # ADHD attention safety (< 200ms)
    if duration_ms < 200:
        adhd_attention_safety.labels(
            endpoint=request.url.path
        ).inc()

    return response
```

**3. Grafana Dashboards** (1 day)

**Dashboard 1: Architecture 3.0 Performance**
- HTTP request rate (req/s)
- P50/P95/P99 latency
- ADHD attention safety (% < 200ms)
- Error rate

**Dashboard 2: ADHD Latency Breakdown**
- Component latencies (HTTP, Bridge, Orchestrator, ConPort)
- Latency histogram
- Attention safety by endpoint
- Performance trends (24 hour)

**Dashboard 3: Cache Performance**
- Cache hit rate (target: > 80%)
- Cache latency (hit vs miss)
- Cache memory usage
- Cache invalidation rate

**4. Alerting Rules** (0.5 days)
```yaml
# prometheus/alerts.yml
groups:
  - name: adhd_performance
    rules:
      - alert: ADHDLatencyHigh
        expr: histogram_quantile(0.95, http_request_duration_ms) > 200
        for: 5m
        annotations:
          summary: "P95 latency exceeds ADHD target (200ms)"

      - alert: AttentionSafetyLow
        expr: adhd_attention_safety < 0.9
        for: 10m
        annotations:
          summary: "< 90% queries meet ADHD attention safety"

      - alert: CacheHitRateLow
        expr: cache_hit_rate < 0.7
        for: 15m
        annotations:
          summary: "Cache hit rate below 70%"
```

### Testing

- [ ] Unit tests: Metrics collection
- [ ] Integration tests: Prometheus scraping
- [ ] Dashboard validation: All panels display correctly
- [ ] Alert testing: Trigger test alerts

---

## Implementation Timeline

**Week 1** (Authentication + Caching):
- Day 1-2: Authentication service + JWT middleware
- Day 3: User-scoped queries + database schema
- Day 4: Redis caching layer
- Day 5: Cache invalidation + monitoring

**Week 2** (Analytics + Integration):
- Day 6: Prometheus metrics + middleware
- Day 7: Grafana dashboards + alerting
- Day 8-9: Integration testing + documentation
- Day 10: Performance validation + deployment

---

## Success Criteria

**Authentication**:
- [ ] Multi-user login working
- [ ] JWT token validation < 10ms
- [ ] User-scoped queries returning correct data
- [ ] Workspace isolation verified

**Caching**:
- [ ] Cache hit rate > 80%
- [ ] Cache hit latency < 5ms
- [ ] Cache miss latency < 70ms
- [ ] Cache invalidation working correctly

**Analytics**:
- [ ] Prometheus metrics exposing correctly
- [ ] Grafana dashboards displaying data
- [ ] Alerts triggering correctly
- [ ] ADHD latency targets tracked

**Overall Performance**:
- [ ] P95 latency < 200ms (with auth + caching)
- [ ] ADHD attention safety > 90%
- [ ] Cache reduces average latency to < 50ms
- [ ] No security vulnerabilities (auth system)

---

## Deployment Strategy

1. **Staging Deployment** (Day 8)
   - Deploy all Phase 11 features to staging
   - Run comprehensive tests
   - Monitor for 24 hours

2. **Canary Production Deployment** (Day 9)
   - 10% traffic with auth + caching
   - Monitor metrics and alerts
   - Gradually increase to 100%

3. **Full Production Rollout** (Day 10)
   - All users on Phase 11
   - Monitor ADHD performance metrics
   - Validate success criteria

---

**Next**: Begin implementation with Feature 1 (Authentication)
**Documentation**: Architecture 3.0 established foundation
**Status**: Ready to begin Phase 11 implementation 🚀
