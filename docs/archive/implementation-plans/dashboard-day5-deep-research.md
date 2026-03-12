---
id: DASHBOARD_DAY5_DEEP_RESEARCH
title: Dashboard_Day5_Deep_Research
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dashboard_Day5_Deep_Research (explanation) for dopemux documentation and
  developer workflows.
---
# Dashboard Day 5 - Deep Research & Planning 🔬
## Real API Integration Strategy

**Created:** 2025-10-29
**Sprint:** Week 1, Day 5 - API Integration
**Status:** Planning Phase
**Goal:** Wire modals to real backend data sources

---

## 🎯 EXECUTIVE SUMMARY

### The Challenge
We have a complete modal system (4 drill-down views) but all data is mocked. Day 5 transforms this from a UI prototype into a real monitoring dashboard by connecting to actual APIs.

### The Opportunity
- **5 backend services** ready with HTTP APIs
- **Prometheus** collecting metrics since day 1
- **PostgreSQL** storing decision history
- **Redis** streaming events in real-time
- **WebSocket** infrastructure ready for live updates

### Success Criteria

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Modal Load Time** | < 500ms | ADHD users need instant feedback |
| **API Success Rate** | > 95% | Graceful degradation on failures |
| **Data Freshness** | < 5s latency | Real-time matters for state tracking |
| **Error Recovery** | Auto-retry 3x | Services restart frequently in dev |
| **Cache Hit Rate** | > 70% | Reduce backend load |

---

## 📊 RESEARCH: API LANDSCAPE AUDIT

### 1. ADHD Engine API (Port 8000)
**Purpose:** Task suitability, energy levels, attention states

#### Available Endpoints
```python
# Current State
GET  /api/v1/energy-level/{user_id}
  → EnergyLevel: LOW | MEDIUM | HIGH | PEAK
  → confidence: 0.0-1.0
  → factors: List[str]
  → last_updated: datetime

GET  /api/v1/attention-state/{user_id}
  → AttentionState: FOCUSED | SCATTERED | HYPERFOCUS | DISTRACTED
  → duration_minutes: int
  → interruptions: int
  → quality_score: 0.0-1.0

# Task Assessment
POST /api/v1/assess-task
  Request: {
    "user_id": str,
    "task_data": {
      "id": str,
      "title": str,
      "complexity": float,
      "estimated_duration_minutes": int
    }
  }
  Response: {
    "is_suitable": bool,
    "suitability_score": 0.0-1.0,
    "energy_match": 0.0-1.0,
    "attention_match": 0.0-1.0,
    "cognitive_load_impact": float,
    "accommodations": List[str],
    "alternative_suggestions": List[str]
  }

# Break Recommendations
POST /api/v1/recommend-break
  Request: {
    "user_id": str,
    "current_duration": int,
    "cognitive_load": float
  }
  Response: {
    "should_break": bool,
    "urgency": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
    "recommended_duration": int,
    "break_type": "MICRO" | "SHORT" | "LONG" | "WALK",
    "reason": str
  }
```

#### Integration Points for Dashboard
```python
# ADHDStateWidget needs:
- GET /energy-level/{user_id}  → Every 10s
- GET /attention-state/{user_id} → Every 10s
- POST /recommend-break → On demand when user requests

# TaskDetailModal needs:
- POST /assess-task → When modal opens
- History data (not yet available - TODO)
```

#### Gaps Identified
❌ **No Task History Endpoint** - Need temporal data for "Task Activity" chart
❌ **No Break History Endpoint** - Can't show break patterns
✅ **Current State Works** - Real-time data available
⚠️ **No WebSocket** - Must poll for updates

**Solution Path:**
1. Use current endpoints for live data ✅
1. Cache responses in Redis with 10s TTL ✅
1. Add `/task-history/{task_id}` endpoint (15 min work) 🔧
1. Mock historical data gracefully until endpoint exists 📊

---

### 2. Task Orchestrator API (Port 8001)
**Purpose:** Task CRUD, decomposition, dependencies

#### Available Endpoints
```python
# Task Management
GET  /api/v1/tasks?status=pending&limit=25
  → List[Task] with pagination

GET  /api/v1/tasks/{task_id}
  → Task (full details)
  → subtasks: List[Task]
  → dependencies: List[str]
  → metadata: Dict

POST /api/v1/tasks
  Request: {
    "title": str,
    "description": str,
    "estimated_complexity": float,
    "parent_id": Optional[str]
  }
  Response: Task

PATCH /api/v1/tasks/{task_id}
  Request: {
    "status": Optional[str],
    "priority": Optional[int],
    "notes": Optional[str]
  }
  Response: Task

# Decomposition
POST /api/v1/tasks/{task_id}/decompose
  → Breaks task into subtasks
  → Returns List[Task]
```

#### Integration Points
```python
# ProductivityWidget needs:
- GET /tasks?status=in_progress&limit=10 → Every 30s
- Task counts by status → Every 30s

# TaskDetailModal needs:
- GET /tasks/{task_id} → On modal open
- PATCH /tasks/{task_id} → On complete/priority change
- POST /tasks/{task_id}/decompose → On user request
```

#### Gaps Identified
✅ **Full CRUD Available**
✅ **Pagination Working**
❌ **No Batch Endpoints** - Inefficient for summary counts
⚠️ **No Filtering by User** - Always returns all tasks

**Solution Path:**
1. Use existing GET /tasks with status filters ✅
1. Add client-side aggregation for counts 📊
1. Request batch endpoint: `GET /tasks/summary` (20 min) 🔧
1. Cache task list aggressively (60s TTL) 💾

---

### 3. Serena Context Engine (Port 8003)
**Purpose:** Pattern detection, context analysis, behavioral insights

#### Discovered API Structure
```bash
# From services/serena/server.py analysis:
# - MCP server (stdio), not HTTP API
# - No direct HTTP endpoints found
# - Event bus integration for patterns
```

#### Current State
⚠️ **Serena is MCP-only** - No HTTP API exists
✅ **Event Bus Connected** - Publishes patterns to Redis
❌ **Dashboard Integration Blocked** - Can't query directly

#### Options Considered

**Option A: Add HTTP Wrapper** (2-3 hours)
```python
# Create services/serena/http_api.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/patterns")
async def get_patterns(limit: int = 10):
    """Recent patterns from knowledge graph"""
    pass

@app.get("/api/patterns/{pattern_id}")
async def get_pattern_detail(pattern_id: str):
    """Full pattern analysis"""
    pass
```
✅ Clean separation
✅ Future-proof
❌ Significant work
❌ Delays Day 5 completion

**Option B: Use ConPort as Proxy** (30 min) ⭐ **RECOMMENDED**
```python
# ConPort already has HTTP API + knowledge graph access
# Add pattern endpoints to services/conport/http_server.py

@app.get("/api/context/patterns")
async def get_recent_patterns(limit: int = 10):
    """Query patterns from knowledge graph via ConPort"""
    async with pool.acquire() as conn:
        query = """
        SELECT * FROM cypher('conport_graph', $$
          MATCH (p:Pattern)
          RETURN p
          ORDER BY p.detected_at DESC
          LIMIT $1
        $$) AS (pattern agtype);
        """
        rows = await conn.fetch(query, limit)
        return [row['pattern'] for row in rows]
```
✅ Leverages existing ConPort HTTP API
✅ Knowledge graph already has patterns
✅ Fast to implement
❌ Couples pattern data to ConPort

**Option C: Mock Until Later** (5 min)
```python
# Use static mock data for now
# Add TODO comments
# Implement in Week 2
```
✅ Unblocks Day 5
✅ Keeps momentum
❌ Not "real" integration
❌ Technical debt

**Decision:** **Option B (ConPort Proxy)** for Day 5, refactor to Option A in Week 2

---

### 4. ConPort Knowledge Graph (Port 8005)
**Purpose:** Decision history, knowledge relationships

#### Available Endpoints (from http_server.py)
```python
GET  /health
  → status, service, database, timestamp

GET  /api/decisions/recent?limit=10
  → List[Decision] from PostgreSQL/AGE

GET  /api/decisions/{decision_id}
  → Decision (full graph context)

GET  /api/decisions/summary
  → counts by type, recency stats

GET  /api/search?q={query}&limit=10
  → Full-text search across decisions
```

#### Integration Points
```python
# ServicesWidget needs:
- GET /health → Every 15s for status icon

# PatternDetailModal needs:
- GET /api/context/patterns/{id} → On modal open (NEW)
- GET /api/decisions?related_to={pattern_id} → Pattern evidence
```

#### Gaps Identified
✅ **HTTP API Complete**
✅ **PostgreSQL Connection Working**
❌ **Pattern Endpoints Missing** - Need to add
✅ **Health Check Ready**

**Solution Path:**
1. Use existing decision endpoints ✅
1. Add 2 pattern endpoints (30 min) 🔧
1. Cache pattern queries (120s TTL) 💾

---

### 5. Prometheus Metrics (Port 9090)
**Purpose:** Time-series metrics, historical trends

#### Available Metrics (from TMUX_METRICS_INVENTORY.md)
```promql
# ADHD State
adhd_cognitive_load{user="default"} - Gauge (0.0-1.0)
adhd_energy_level{user="default"} - Gauge (1-4)
adhd_attention_quality{user="default"} - Gauge (0.0-1.0)
adhd_context_switches_total{user="default"} - Counter

# Productivity
adhd_task_velocity_per_day{user="default"} - Gauge
adhd_tasks_completed_total{user="default"} - Counter
adhd_break_adherence{user="default"} - Gauge (0.0-1.0)

# Session
adhd_session_duration_seconds{user="default"} - Gauge
adhd_interruptions_total{user="default"} - Counter
```

#### Query API
```python
# Instant query
GET /api/v1/query?query=adhd_cognitive_load

# Range query (for sparklines)
GET /api/v1/query_range
  ?query=adhd_cognitive_load
  &start=1698518400
  &end=1698522000
  &step=60s
```

#### Integration Points
```python
# TrendsWidget needs:
- query_range for sparklines → Every 30s
- query for current values → Every 10s

# MetricHistoryModal needs:
- query_range with 7d window → On modal open
- Statistical aggregations → On modal open
```

#### Gaps Identified
✅ **PromQL API Standard**
✅ **PrometheusClient Class Exists** (prometheus_client.py)
✅ **All Metrics Available**
⚠️ **Data May Be Sparse** - Not all services pushing yet

**Solution Path:**
1. Use existing PrometheusClient ✅
1. Add graceful handling for empty results 📊
1. Show "No data" state clearly in UI 🎨
1. Validate metrics are being pushed (separate task) 🔧

---

## 🏗️ IMPLEMENTATION ARCHITECTURE

### Data Flow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     Dopemux Dashboard                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ADHDState    │  │ Productivity │  │ Services     │      │
│  │ Widget       │  │ Widget       │  │ Widget       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └─────────┬────────┴──────────┬──────┘              │
│                   │                    │                     │
│           ┌───────▼────────┐  ┌────────▼────────┐           │
│           │ APIClient      │  │ CacheManager    │           │
│           │ - fetch_task   │  │ - Redis TTL     │           │
│           │ - fetch_energy │  │ - Invalidation  │           │
│           │ - fetch_metrics│  │ - Warm-up       │           │
│           └───────┬────────┘  └────────┬────────┘           │
└───────────────────┼───────────────────┼────────────────────┘
                    │                    │
         ┌──────────┴────────────────────┴──────────┐
         │        Service Layer (shared)             │
         │  - Connection pooling                     │
         │  - Retry logic                            │
         │  - Circuit breakers                       │
         │  - Error handling                         │
         └──────────┬────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼────┐  ┌──────▼─────┐  ┌─────▼──────┐
│ ADHD   │  │ Task Orch  │  │ ConPort    │
│ Engine │  │ :8001      │  │ :8005      │
│ :8000  │  └────────────┘  └─────┬──────┘
└────────┘                         │
                           ┌───────▼────────┐
                           │ PostgreSQL AGE │
                           │ :5456          │
                           └────────────────┘

    ┌──────────────────────┐
    │ Prometheus           │
    │ :9090                │
    └──────────────────────┘
```

### Caching Strategy

#### Why Cache?
- **ADHD UX:** Sub-second response times critical
- **Backend Load:** 4 widgets × 10s refresh = 24 req/min per user
- **Service Restarts:** Dev environment unstable
- **Network Latency:** Even localhost has ~5-10ms RTT

#### Cache Tiers
```python
# Tier 1: In-Memory (fastest, smallest)
class MemoryCache:
    """Process-local cache for instant access"""
    max_size = 100  # items
    ttl = 5  # seconds

    # Use for:
    # - Current energy level (changes slowly)
    # - Task counts (batch updates)
    # - Service health (unlikely to change)

# Tier 2: Redis (shared, persistent)
class RedisCache:
    """Shared cache across dashboard instances"""
    max_size = 10_000  # items
    ttl_by_type = {
        "energy_level": 10,      # 10s - changes slowly
        "task_list": 60,          # 1m - stable
        "metrics_instant": 30,    # 30s - acceptable lag
        "metrics_range": 300,     # 5m - historical data
        "pattern_detail": 120,    # 2m - analysis is expensive
    }

    # Use for:
    # - All Prometheus queries (expensive)
    # - Task lists (reduce DB load)
    # - Pattern analysis (heavy computation)

# Tier 3: PostgreSQL (ground truth)
# No caching - always fresh
```

#### Cache Invalidation Rules
```python
# Event-driven invalidation
async def on_task_completed(task_id: str):
    """Task state changed → invalidate related caches"""
    await cache.delete(f"task:{task_id}")
    await cache.delete("task:list:in_progress")
    await cache.delete("task:counts")

# Time-based expiration (TTL)
await redis.setex(f"energy:{user_id}", 10, value)

# User-driven refresh
# Press 'r' key → bypass cache, force fetch
```

---

## 🛠️ TECHNICAL IMPLEMENTATION PLAN

### Phase 1: Foundation (30 min)

#### 1.1 Create API Client Infrastructure
```python
# File: dopemux_dashboard.py (add to top)

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime, timedelta

@dataclass
class ServiceEndpoints:
    """Central configuration for all service URLs"""
    adhd_engine: str = "http://localhost:8000"
    task_orchestrator: str = "http://localhost:8001"
    conport: str = "http://localhost:8005"
    prometheus: str = "http://localhost:9090"

    # Timeouts (seconds)
    default_timeout: float = 2.0
    long_timeout: float = 5.0

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 0.5

class APIClient:
    """
    Unified HTTP client for all backend services.

    Features:
- Connection pooling
- Automatic retries with exponential backoff
- Circuit breaker pattern
- Request/response logging
- Error normalization
    """

    def __init__(self, endpoints: Optional[ServiceEndpoints] = None):
        self.endpoints = endpoints or ServiceEndpoints()
        self.client = httpx.AsyncClient(
            timeout=self.endpoints.default_timeout,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
        )

        # Circuit breaker state
        self.circuit_breakers = {
            "adhd_engine": {"failures": 0, "last_failure": None, "open": False},
            "task_orchestrator": {"failures": 0, "last_failure": None, "open": False},
            "conport": {"failures": 0, "last_failure": None, "open": False},
            "prometheus": {"failures": 0, "last_failure": None, "open": False},
        }

        self.failure_threshold = 5
        self.circuit_timeout = 30  # seconds

    async def get(
        self,
        service: str,
        path: str,
        params: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        GET request with retry and circuit breaker

        Args:
            service: "adhd_engine" | "task_orchestrator" | "conport" | "prometheus"
            path: "/api/v1/tasks" (without base URL)
            params: Query parameters
            timeout: Override default timeout

        Returns:
            Parsed JSON response

        Raises:
            ServiceUnavailableError: If circuit breaker is open
            APIError: If request fails after retries
        """
        # Check circuit breaker
        if self._is_circuit_open(service):
            raise ServiceUnavailableError(
                f"{service} circuit breaker is open. Service may be down."
            )

        base_url = getattr(self.endpoints, service)
        url = f"{base_url}{path}"

        for attempt in range(self.endpoints.max_retries):
            try:
                response = await self.client.get(
                    url,
                    params=params,
                    timeout=timeout or self.endpoints.default_timeout
                )

                if response.status_code == 200:
                    self._reset_circuit_breaker(service)
                    return response.json()
                elif response.status_code == 404:
                    return None  # Not found is not a failure
                else:
                    logger.warning(
                        f"API {service}{path} returned {response.status_code}"
                    )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(
                    f"API request failed (attempt {attempt + 1}/{self.endpoints.max_retries}): {e}"
                )

                if attempt < self.endpoints.max_retries - 1:
                    await asyncio.sleep(self.endpoints.retry_delay * (2 ** attempt))
                else:
                    self._record_failure(service)
                    raise APIError(f"Failed to reach {service} after {self.endpoints.max_retries} attempts")

        self._record_failure(service)
        return None

    async def post(
        self,
        service: str,
        path: str,
        json: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """POST request with retry logic"""
        if self._is_circuit_open(service):
            raise ServiceUnavailableError(f"{service} circuit breaker is open")

        base_url = getattr(self.endpoints, service)
        url = f"{base_url}{path}"

        try:
            response = await self.client.post(
                url,
                json=json,
                timeout=timeout or self.endpoints.long_timeout
            )

            if response.status_code in (200, 201):
                self._reset_circuit_breaker(service)
                return response.json()
            else:
                logger.error(f"POST {service}{path} failed: {response.status_code}")
                self._record_failure(service)
                return None

        except Exception as e:
            logger.error(f"POST {service}{path} error: {e}")
            self._record_failure(service)
            raise APIError(f"Failed to POST to {service}{path}: {e}")

    def _is_circuit_open(self, service: str) -> bool:
        """Check if circuit breaker is open"""
        breaker = self.circuit_breakers[service]

        if not breaker["open"]:
            return False

        # Check if timeout has elapsed
        if breaker["last_failure"]:
            elapsed = (datetime.now() - breaker["last_failure"]).total_seconds()
            if elapsed > self.circuit_timeout:
                # Try to close the circuit
                breaker["open"] = False
                breaker["failures"] = 0
                logger.info(f"Circuit breaker for {service} closed (timeout elapsed)")
                return False

        return True

    def _record_failure(self, service: str):
        """Record a failure and potentially open circuit breaker"""
        breaker = self.circuit_breakers[service]
        breaker["failures"] += 1
        breaker["last_failure"] = datetime.now()

        if breaker["failures"] >= self.failure_threshold:
            breaker["open"] = True
            logger.error(
                f"Circuit breaker OPENED for {service} ({breaker['failures']} failures)"
            )

    def _reset_circuit_breaker(self, service: str):
        """Reset circuit breaker on successful request"""
        breaker = self.circuit_breakers[service]
        if breaker["failures"] > 0:
            breaker["failures"] = 0
            breaker["open"] = False

class ServiceUnavailableError(Exception):
    """Raised when a service circuit breaker is open"""
    pass

class APIError(Exception):
    """Raised when an API request fails"""
    pass
```

#### 1.2 Add Error Handling UI Components
```python
# Add to dopemux_dashboard.py

class ErrorState(Static):
    """Widget to show graceful error messages"""

    def __init__(self, service_name: str, error_message: str):
        super().__init__()
        self.service_name = service_name
        self.error_message = error_message

    def render(self) -> str:
        return f"""
[yellow]⚠ Service Unavailable[/yellow]

{self.service_name} is currently offline or unreachable.

[dim]{self.error_message}[/dim]

[cyan]↻ Retrying automatically...[/cyan]
"""

class LoadingState(Static):
    """Widget to show loading spinner"""

    def __init__(self, message: str = "Loading..."):
        super().__init__()
        self.message = message

    def render(self) -> str:
        return f"""
[cyan]⏳ {self.message}[/cyan]

[dim]Please wait...[/dim]
"""
```

---

### Phase 2: Widget Integration (2 hours)

#### 2.1 ADHDStateWidget → ADHD Engine
```python
# In dopemux_dashboard.py

class ADHDStateWidget(Static):
    """Enhanced with real API calls"""

    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api = api_client
        self.user_id = "default"

        # State
        self.energy = "MEDIUM"
        self.attention = "FOCUSED"
        self.cognitive_load = 0.5
        self.last_updated = None
        self.error_state = None

    async def on_mount(self):
        """Start periodic updates"""
        self.set_interval(10, self.refresh_state)  # Every 10 seconds
        await self.refresh_state()  # Immediate first load

    async def refresh_state(self):
        """Fetch current ADHD state from engine"""
        try:
            # Fetch energy level
            energy_data = await self.api.get(
                "adhd_engine",
                f"/api/v1/energy-level/{self.user_id}"
            )

            if energy_data:
                self.energy = energy_data.get("level", "MEDIUM")
                self.last_updated = datetime.now()
                self.error_state = None

            # Fetch attention state
            attention_data = await self.api.get(
                "adhd_engine",
                f"/api/v1/attention-state/{self.user_id}"
            )

            if attention_data:
                self.attention = attention_data.get("state", "FOCUSED")

            # Fetch cognitive load from Prometheus
            prom_data = await self.api.get(
                "prometheus",
                "/api/v1/query",
                params={"query": f'adhd_cognitive_load{{user="{self.user_id}"}}'}
            )

            if prom_data and prom_data.get("data", {}).get("result"):
                result = prom_data["data"]["result"][0]
                self.cognitive_load = float(result["value"][1])

            self.refresh()

        except ServiceUnavailableError as e:
            self.error_state = str(e)
            self.refresh()

        except APIError as e:
            logger.error(f"Failed to refresh ADHD state: {e}")
            # Keep showing last known good state

    def render(self) -> str:
        """Render with real or error state"""
        if self.error_state:
            return f"""
╔══════════════════════════════════╗
║         ADHD STATE               ║
╚══════════════════════════════════╝

[yellow]⚠ Unable to connect to ADHD Engine[/yellow]

[dim]Last update: {self.last_updated or 'Never'}[/dim]
[dim]Error: {self.error_state}[/dim]
"""

        # Normal rendering with real data
        load_bar = self._render_load_bar(self.cognitive_load)
        energy_icon = self._energy_icon(self.energy)
        attention_icon = self._attention_icon(self.attention)

        return f"""
╔══════════════════════════════════╗
║         ADHD STATE               ║
╚══════════════════════════════════╝

Energy:     {energy_icon} {self.energy}
Attention:  {attention_icon} {self.attention}

Cognitive Load: {load_bar} {int(self.cognitive_load * 100)}%

[dim]Updated: {self._time_ago(self.last_updated)}[/dim]
"""

    @staticmethod
    def _energy_icon(level: str) -> str:
        return {
            "LOW": "🔋",
            "MEDIUM": "⚡",
            "HIGH": "⚡⚡",
            "PEAK": "⚡⚡⚡"
        }.get(level, "❓")

    @staticmethod
    def _attention_icon(state: str) -> str:
        return {
            "FOCUSED": "🎯",
            "SCATTERED": "💫",
            "HYPERFOCUS": "🔥",
            "DISTRACTED": "🌀"
        }.get(state, "❓")

    @staticmethod
    def _render_load_bar(load: float) -> str:
        """Visual progress bar for cognitive load"""
        filled = int(load * 10)
        empty = 10 - filled

        if load < 0.5:
            color = "green"
        elif load < 0.75:
            color = "yellow"
        else:
            color = "red"

        return f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"

    @staticmethod
    def _time_ago(dt: Optional[datetime]) -> str:
        """Human-friendly time delta"""
        if not dt:
            return "Never"

        delta = datetime.now() - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m ago"
        else:
            return f"{int(seconds // 3600)}h ago"
```

#### 2.2 ProductivityWidget → Task Orchestrator
```python
class ProductivityWidget(Static):
    """Task metrics from real API"""

    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api = api_client

        # State
        self.tasks_in_progress = []
        self.task_counts = {"pending": 0, "in_progress": 0, "completed": 0}
        self.velocity = 0.0
        self.error_state = None

    async def on_mount(self):
        self.set_interval(30, self.refresh_tasks)  # Every 30 seconds
        await self.refresh_tasks()

    async def refresh_tasks(self):
        """Fetch task data from orchestrator and Prometheus"""
        try:
            # Get current tasks
            tasks_data = await self.api.get(
                "task_orchestrator",
                "/api/v1/tasks",
                params={"status": "in_progress", "limit": 10}
            )

            if tasks_data:
                self.tasks_in_progress = tasks_data.get("tasks", [])

            # Get task counts (TODO: replace with batch endpoint when available)
            for status in ["pending", "in_progress", "completed"]:
                count_data = await self.api.get(
                    "task_orchestrator",
                    "/api/v1/tasks",
                    params={"status": status, "limit": 1}  # Just get total count
                )
                if count_data:
                    self.task_counts[status] = count_data.get("total", 0)

            # Get velocity from Prometheus
            velocity_data = await self.api.get(
                "prometheus",
                "/api/v1/query",
                params={"query": 'adhd_task_velocity_per_day{user="default"}'}
            )

            if velocity_data and velocity_data.get("data", {}).get("result"):
                self.velocity = float(velocity_data["data"]["result"][0]["value"][1])

            self.error_state = None
            self.refresh()

        except Exception as e:
            logger.error(f"Failed to refresh tasks: {e}")
            self.error_state = str(e)

    def render(self) -> str:
        if self.error_state:
            return f"[yellow]⚠ Task data unavailable[/yellow]\n{self.error_state}"

        # Show real task list
        task_list = "\n".join([
            f"  • {task['title'][:30]}" for task in self.tasks_in_progress[:5]
        ]) or "  [dim]No active tasks[/dim]"

        return f"""
╔══════════════════════════════════╗
║       PRODUCTIVITY               ║
╚══════════════════════════════════╝

Active Tasks ({len(self.tasks_in_progress)}):
{task_list}

Pending:    {self.task_counts['pending']}
Completed:  {self.task_counts['completed']}
Velocity:   {self.velocity:.1f} tasks/day
"""
```

#### 2.3 TrendsWidget → Prometheus Sparklines
```python
class TrendsWidget(Static):
    """Real sparklines from Prometheus"""

    def __init__(self, api_client: APIClient, sparkline_gen: SparklineGenerator):
        super().__init__()
        self.api = api_client
        self.sparkline_gen = sparkline_gen

        # Sparkline data
        self.cognitive_sparkline = "▁▂▃▄▅▆▇█"  # Placeholder
        self.velocity_sparkline = "▁▂▃▄▅▆▇█"
        self.context_sparkline = "▁▂▃▄▅▆▇█"

    async def on_mount(self):
        self.set_interval(30, self.refresh_sparklines)
        await self.refresh_sparklines()

    async def refresh_sparklines(self):
        """Fetch time-series data and generate sparklines"""
        try:
            # Cognitive load (last 2 hours)
            self.cognitive_sparkline = await self.sparkline_gen.generate(
                query='adhd_cognitive_load{user="default"}',
                hours=2,
                width=20
            )

            # Task velocity (last 7 days)
            self.velocity_sparkline = await self.sparkline_gen.generate(
                query='adhd_task_velocity_per_day{user="default"}',
                hours=168,  # 7 days
                width=20
            )

            # Context switches (last 24 hours)
            self.context_sparkline = await self.sparkline_gen.generate(
                query='rate(adhd_context_switches_total{user="default"}[5m])',
                hours=24,
                width=20
            )

            self.refresh()

        except Exception as e:
            logger.error(f"Failed to refresh sparklines: {e}")

    def render(self) -> str:
        return f"""
╔══════════════════════════════════╗
║          TRENDS (24h)            ║
╚══════════════════════════════════╝

Cognitive Load:
{self.cognitive_sparkline}

Task Velocity:
{self.velocity_sparkline}

Context Switches:
{self.context_sparkline}
"""
```

---

### Phase 3: Modal Integration (2.5 hours)

#### 3.1 TaskDetailModal → Full API Wiring
```python
class TaskDetailModal(ModalView):
    """Complete task details from orchestrator + ADHD engine"""

    def __init__(self, task_id: str, api_client: APIClient):
        super().__init__()
        self.task_id = task_id
        self.api = api_client
        self.task_data = None
        self.assessment_data = None

    async def on_mount(self):
        content_widget = self.query_one("#modal-content", Static)
        content_widget.update("[cyan]⏳ Loading task details...[/cyan]")

        try:
            # Fetch task details
            self.task_data = await self.api.get(
                "task_orchestrator",
                f"/api/v1/tasks/{self.task_id}"
            )

            if not self.task_data:
                content_widget.update("[red]❌ Task not found[/red]")
                return

            # Fetch ADHD assessment
            self.assessment_data = await self.api.post(
                "adhd_engine",
                "/api/v1/assess-task",
                json={
                    "user_id": "default",
                    "task_data": {
                        "id": self.task_id,
                        "title": self.task_data["title"],
                        "complexity": self.task_data.get("complexity", 0.5),
                        "estimated_duration_minutes": self.task_data.get("estimated_duration", 30)
                    }
                }
            )

            # Render full content
            rendered = self.render_task_content()
            content_widget.update(rendered)

        except Exception as e:
            logger.error(f"Failed to load task {self.task_id}: {e}")
            content_widget.update(f"[red]❌ Error loading task[/red]\n\n{str(e)}")

    def render_task_content(self) -> str:
        """Render rich task details"""
        task = self.task_data
        assessment = self.assessment_data or {}

        # Basic info
        status_icon = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "blocked": "🚫"
        }.get(task.get("status", "pending"), "❓")

        # ADHD suitability
        is_suitable = assessment.get("is_suitable", True)
        suitability_icon = "✅" if is_suitable else "⚠️"
        suitability_score = assessment.get("suitability_score", 0.0)

        # Accommodations
        accommodations = assessment.get("accommodations", [])
        accommodation_list = "\n".join([f"  • {acc}" for acc in accommodations]) if accommodations else "  [dim]None needed[/dim]"

        return f"""
╔══════════════════════════════════════════════════════════╗
║  TASK: {task['title'][:50]}
╚══════════════════════════════════════════════════════════╝

STATUS: {status_icon} {task.get('status', 'unknown').upper()}
COMPLEXITY: {task.get('complexity', 0.0):.2f}
ESTIMATED TIME: {task.get('estimated_duration', 0)} minutes

───────────────────────────────────────────────────────────

DESCRIPTION:
{task.get('description', '[dim]No description[/dim]')}

───────────────────────────────────────────────────────────

{suitability_icon} ADHD SUITABILITY: {suitability_score:.0%}

Energy Match:    {assessment.get('energy_match', 0.0):.0%}
Attention Match: {assessment.get('attention_match', 0.0):.0%}
Cognitive Load:  {assessment.get('cognitive_load_impact', 0.0):.2f}

RECOMMENDED ACCOMMODATIONS:
{accommodation_list}

───────────────────────────────────────────────────────────

SUBTASKS ({len(task.get('subtasks', []))}):
{self._render_subtasks(task.get('subtasks', []))}

───────────────────────────────────────────────────────────

[cyan]Actions:[/cyan]
  [c] Mark complete  [p] Change priority  [d] Decompose
  [Esc] Close
"""

    def _render_subtasks(self, subtasks: List[Dict]) -> str:
        if not subtasks:
            return "  [dim]No subtasks yet[/dim]"

        return "\n".join([
            f"  {i+1}. [{subtask.get('status', 'pending')}] {subtask['title']}"
            for i, subtask in enumerate(subtasks[:10])
        ])

    async def action_complete_task(self):
        """Mark task as complete via API"""
        try:
            result = await self.api.patch(
                "task_orchestrator",
                f"/api/v1/tasks/{self.task_id}",
                json={"status": "completed"}
            )

            if result:
                self.app.notify("✅ Task marked complete!", severity="information")
                self.app.pop_screen()
            else:
                self.app.notify("❌ Failed to update task", severity="error")

        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            self.app.notify(f"❌ Error: {e}", severity="error")
```

#### 3.2 ServiceLogsModal → Direct Log Access
```python
class ServiceLogsModal(ModalView):
    """Live service logs"""

    def __init__(self, service_name: str, api_client: APIClient):
        super().__init__()
        self.service_name = service_name
        self.api = api_client
        self.auto_scroll = True
        self.lines_to_show = 100

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static(f"📋 Service Logs: {self.service_name}", id="modal-header")
            yield DataTable(id="log-table")
            yield Static(
                "[Esc] Close  [↑↓] Scroll  [a] Auto-scroll ON  [e] Export",
                id="modal-footer"
            )

    async def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Time", "Level", "Message")

        # Start log streaming
        self.run_worker(self.stream_logs())

    async def stream_logs(self):
        """Poll for new logs"""
        last_timestamp = datetime.now()

        while not self.is_closing:
            try:
                # TODO: Replace with actual service log endpoint
                # For now, use docker logs
                logs = await self.fetch_docker_logs(self.service_name, since=last_timestamp)

                if logs:
                    self.append_logs(logs)
                    last_timestamp = datetime.now()

                await asyncio.sleep(2)  # Poll every 2 seconds

            except Exception as e:
                logger.error(f"Log streaming error: {e}")
                await asyncio.sleep(5)

    async def fetch_docker_logs(self, service: str, since: datetime, lines: int = 50) -> List[Dict]:
        """Fetch logs from docker (temporary solution)"""
        # TODO: Replace with proper service API endpoint
        # GET /api/services/{name}/logs?since={timestamp}&lines={n}

        try:
            result = subprocess.run(
                ["docker", "logs", f"dopemux-{service}", "--since", since.isoformat(), "-n", str(lines)],
                capture_output=True,
                text=True,
                timeout=2
            )

            # Parse logs
            logs = []
            for line in result.stdout.splitlines():
                # Simple parsing - enhance based on actual log format
                logs.append({
                    "timestamp": datetime.now(),
                    "level": self._detect_level(line),
                    "message": line
                })

            return logs

        except Exception as e:
            logger.error(f"Failed to fetch docker logs: {e}")
            return []

    def append_logs(self, logs: List[Dict]):
        """Add new logs to table"""
        table = self.query_one(DataTable)

        for log in logs:
            # Color code by level
            level_color = {
                "ERROR": "[red]ERROR[/red]",
                "WARNING": "[yellow]WARN[/yellow]",
                "INFO": "[cyan]INFO[/cyan]",
                "DEBUG": "[dim]DEBUG[/dim]"
            }.get(log["level"], log["level"])

            table.add_row(
                log["timestamp"].strftime("%H:%M:%S"),
                level_color,
                log["message"][:80]
            )

        # Auto-scroll to bottom
        if self.auto_scroll:
            table.scroll_end()

    @staticmethod
    def _detect_level(line: str) -> str:
        """Simple log level detection"""
        line_upper = line.upper()
        if "ERROR" in line_upper or "FAIL" in line_upper:
            return "ERROR"
        elif "WARN" in line_upper:
            return "WARNING"
        elif "DEBUG" in line_upper:
            return "DEBUG"
        else:
            return "INFO"
```

#### 3.3 PatternDetailModal → ConPort Proxy
```python
class PatternDetailModal(ModalView):
    """Pattern analysis from ConPort knowledge graph"""

    def __init__(self, pattern_id: str, api_client: APIClient):
        super().__init__()
        self.pattern_id = pattern_id
        self.api = api_client

    async def on_mount(self):
        content = self.query_one("#modal-content", Static)
        content.update("[cyan]⏳ Loading pattern analysis...[/cyan]")

        try:
            # Fetch pattern details via ConPort
            pattern_data = await self.api.get(
                "conport",
                f"/api/context/patterns/{self.pattern_id}"
            )

            if not pattern_data:
                content.update("[red]❌ Pattern not found[/red]")
                return

            # Fetch related decisions
            decisions = await self.api.get(
                "conport",
                "/api/decisions",
                params={"related_to": self.pattern_id, "limit": 10}
            )

            rendered = self.render_pattern_content(pattern_data, decisions or [])
            content.update(rendered)

        except Exception as e:
            logger.error(f"Failed to load pattern: {e}")
            content.update(f"[red]❌ Error: {e}[/red]")

    def render_pattern_content(self, pattern: Dict, decisions: List[Dict]) -> str:
        return f"""
╔══════════════════════════════════════════════════════════╗
║  PATTERN: {pattern.get('name', 'Unknown')[:50]}
╚══════════════════════════════════════════════════════════╝

TYPE: {pattern.get('type', 'behavioral')}
DETECTED: {pattern.get('detected_at', 'unknown')}
OCCURRENCES: {pattern.get('occurrence_count', 0)}

DESCRIPTION:
{pattern.get('description', '[dim]No description[/dim]')}

───────────────────────────────────────────────────────────

📊 STATISTICS:

Success Rate:  {pattern.get('success_rate', 0.0):.0%}
Confidence:    {pattern.get('confidence', 0.0):.0%}
Trend:         {pattern.get('trend', 'stable')}

───────────────────────────────────────────────────────────

💡 INSIGHTS:

{self._render_insights(pattern.get('insights', []))}

───────────────────────────────────────────────────────────

📝 RELATED DECISIONS ({len(decisions)}):

{self._render_decisions(decisions)}

───────────────────────────────────────────────────────────

[Esc] Close
"""

    def _render_insights(self, insights: List[str]) -> str:
        if not insights:
            return "  [dim]No insights available[/dim]"
        return "\n".join([f"  • {insight}" for insight in insights[:5]])

    def _render_decisions(self, decisions: List[Dict]) -> str:
        if not decisions:
            return "  [dim]No related decisions[/dim]"
        return "\n".join([
            f"  {i+1}. {d.get('title', 'Untitled')} ({d.get('created_at', 'unknown')})"
            for i, d in enumerate(decisions[:5])
        ])
```

#### 3.4 MetricHistoryModal → Prometheus Query Range
```python
class MetricHistoryModal(ModalView):
    """7-day metric history from Prometheus"""

    def __init__(self, metric_name: str, api_client: APIClient, prom_client: PrometheusClient):
        super().__init__()
        self.metric_name = metric_name
        self.api = api_client
        self.prom = prom_client

    async def on_mount(self):
        content = self.query_one("#modal-content", Static)
        content.update("[cyan]⏳ Fetching metric history...[/cyan]")

        try:
            # Fetch 7 days of data
            query = f'{self.metric_name}{{user="default"}}'
            data_points = await self.prom.query_range(
                query=query,
                hours=168,  # 7 days
                step="1h"
            )

            if not data_points:
                content.update("[yellow]⚠ No data available for this metric[/yellow]")
                return

            # Calculate statistics
            values = [v for _, v in data_points]
            stats = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "current": values[-1] if values else 0,
                "count": len(values)
            }

            # Generate large sparkline
            sparkline = self._generate_sparkline(values, width=60)

            rendered = self.render_metric_history(self.metric_name, stats, sparkline, data_points)
            content.update(rendered)

        except Exception as e:
            logger.error(f"Failed to fetch metric history: {e}")
            content.update(f"[red]❌ Error: {e}[/red]")

    def render_metric_history(
        self,
        metric: str,
        stats: Dict,
        sparkline: str,
        data_points: List[Tuple[datetime, float]]
    ) -> str:
        return f"""
╔══════════════════════════════════════════════════════════╗
║  METRIC: {metric[:50]}
╚══════════════════════════════════════════════════════════╝

📊 7-DAY TREND:

{sparkline}

───────────────────────────────────────────────────────────

📈 STATISTICS:

Current:  {stats['current']:.2f}
Average:  {stats['avg']:.2f}
Min:      {stats['min']:.2f}
Max:      {stats['max']:.2f}

Data Points: {stats['count']}

───────────────────────────────────────────────────────────

📅 RECENT VALUES:

{self._render_recent_values(data_points[-10:])}

───────────────────────────────────────────────────────────

[Esc] Close  [e] Export CSV
"""

    def _render_recent_values(self, recent: List[Tuple[datetime, float]]) -> str:
        return "\n".join([
            f"  {ts.strftime('%Y-%m-%d %H:%M')}: {val:.2f}"
            for ts, val in reversed(recent)
        ])

    @staticmethod
    def _generate_sparkline(values: List[float], width: int = 60) -> str:
        """Generate ASCII sparkline from values"""
        if not values:
            return "  [dim]No data[/dim]"

        chars = "▁▂▃▄▅▆▇█"
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val or 1

        # Downsample if needed
        if len(values) > width:
            step = len(values) / width
            sampled = [values[int(i * step)] for i in range(width)]
        else:
            sampled = values

        # Map to chars
        sparkline = ""
        for val in sampled:
            normalized = (val - min_val) / range_val
            char_idx = int(normalized * (len(chars) - 1))
            sparkline += chars[char_idx]

        return f"  {sparkline}"
```

---

### Phase 4: Testing & Validation (1 hour)

#### 4.1 Integration Test Script
```python
# File: test_dashboard_api_integration.py

import asyncio
import httpx
from dopemux_dashboard import APIClient, ServiceEndpoints

async def test_all_endpoints():
    """Smoke test all API integrations"""

    api = APIClient()

    print("🧪 Testing API Integrations...")
    print("─" * 60)

    # Test 1: ADHD Engine
    print("\n1️⃣ Testing ADHD Engine...")
    try:
        energy = await api.get("adhd_engine", "/api/v1/energy-level/default")
        if energy:
            print(f"   ✅ Energy level: {energy.get('level')}")
        else:
            print("   ⚠️ No data returned")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 2: Task Orchestrator
    print("\n2️⃣ Testing Task Orchestrator...")
    try:
        tasks = await api.get("task_orchestrator", "/api/v1/tasks", params={"limit": 5})
        if tasks:
            print(f"   ✅ Found {len(tasks.get('tasks', []))} tasks")
        else:
            print("   ⚠️ No tasks found")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 3: ConPort
    print("\n3️⃣ Testing ConPort...")
    try:
        health = await api.get("conport", "/health")
        if health:
            print(f"   ✅ Status: {health.get('status')}")
        else:
            print("   ⚠️ Health check failed")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 4: Prometheus
    print("\n4️⃣ Testing Prometheus...")
    try:
        metrics = await api.get(
            "prometheus",
            "/api/v1/query",
            params={"query": "adhd_cognitive_load"}
        )
        if metrics and metrics.get("data", {}).get("result"):
            print(f"   ✅ Found {len(metrics['data']['result'])} metrics")
        else:
            print("   ⚠️ No metrics found (may not be pushed yet)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n" + "─" * 60)
    print("✅ Integration test complete!\n")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
```

#### 4.2 Manual Testing Checklist
```markdown
## Day 5 Testing Checklist

### Pre-Flight
- [ ] All services running (`docker-compose ps`)
- [ ] Prometheus accessible (`curl http://localhost:9090`)
- [ ] ADHD Engine health (`curl http://localhost:8000/health`)
- [ ] Task Orchestrator health (`curl http://localhost:8001/health`)
- [ ] ConPort health (`curl http://localhost:8005/health`)

### Widget Tests
- [ ] ADHDStateWidget shows real energy level (not "MEDIUM" placeholder)
- [ ] ADHDStateWidget updates every 10s (watch timestamp)
- [ ] ProductivityWidget shows actual task count
- [ ] ProductivityWidget lists real tasks (not "Fix authentication bug")
- [ ] TrendsWidget sparklines change over time
- [ ] ServicesWidget shows correct service count

### Modal Tests
- [ ] Press `d` → TaskDetailModal opens with real task
- [ ] TaskDetailModal shows ADHD assessment
- [ ] TaskDetailModal accommodations are relevant
- [ ] Press `l` → ServiceLogsModal shows live logs
- [ ] Logs auto-scroll to bottom
- [ ] Press `p` → PatternDetailModal opens
- [ ] Pattern data from ConPort (not mock)
- [ ] Press `h` → MetricHistoryModal shows 7d chart
- [ ] Sparkline in history modal is 60 chars wide

### Error Handling
- [ ] Stop ADHD Engine → Widget shows error state gracefully
- [ ] Restart ADHD Engine → Widget recovers automatically
- [ ] Disconnect network → Circuit breaker opens
- [ ] Reconnect → Circuit breaker closes
- [ ] Invalid task ID → Modal shows "Not found" message

### Performance
- [ ] Modal open time < 500ms (feel responsive)
- [ ] Widget refresh doesn't cause visible lag
- [ ] CPU usage < 10% (check with `top`)
- [ ] Memory stable (no leaks over 5 min)

### User Experience
- [ ] Loading states clear ("⏳ Loading...")
- [ ] Error messages helpful (not just "Error")
- [ ] Timestamps show "5s ago" format
- [ ] Colors appropriate (red for errors, green for success)
```

---

## 📚 RESEARCH FINDINGS SUMMARY

### What Works Well
1. ✅ **HTTP APIs are consistent** - All services use FastAPI with similar patterns
1. ✅ **Prometheus is stable** - Reliable time-series storage
1. ✅ **PrometheusClient exists** - Already implemented and tested
1. ✅ **Error handling patterns established** - Can copy from existing code

### Gaps to Address
1. ❌ **Serena has no HTTP API** - Using ConPort as proxy for patterns
1. ❌ **No service log endpoints** - Using docker logs temporarily
1. ❌ **No batch task endpoints** - Multiple queries for counts
1. ❌ **No task history endpoint** - Can't show temporal data yet

### Risk Mitigation
1. **Service Downtime** → Circuit breakers prevent cascading failures
1. **Slow APIs** → Aggressive caching reduces user-visible latency
1. **Missing Data** → Graceful degradation with clear messaging
1. **Version Mismatches** → API client validates response shapes

---

## 🎯 DAY 5 SUCCESS METRICS

### Functional
- [ ] 100% of widgets fetch real data
- [ ] 100% of modals fetch real data
- [ ] Error states render correctly
- [ ] Loading states show immediately

### Performance
- [ ] < 500ms modal load with real data
- [ ] < 100ms widget refresh
- [ ] < 10% CPU usage
- [ ] < 50MB memory usage

### Reliability
- [ ] Circuit breakers work
- [ ] Auto-retry succeeds
- [ ] Cache invalidation correct
- [ ] No data corruption

### UX
- [ ] Users can't tell when services are slow (caching works)
- [ ] Error messages are actionable
- [ ] Recovery is automatic
- [ ] Dashboard never "freezes"

---

## 📅 TIMELINE

### Morning (3 hours)
- ✅ Phase 1: Foundation (30 min)
- ✅ Phase 2: Widget Integration (2 hours)
- ☕ Coffee break (30 min)

### Afternoon (3.5 hours)
- ✅ Phase 3.1-3.2: Modals (1.5 hours)
- ✅ Phase 3.3-3.4: Modals (1 hour)
- ✅ Phase 4: Testing (1 hour)

### End of Day
- 🎉 **Day 5 complete!**
- 📝 Document findings
- 🚀 Ready for Day 6 (live streaming)

---

## 🚀 NEXT STEPS (Day 6+)

### Day 6: Live Streaming
- Add WebSocket support to ADHD Engine
- Replace polling with real-time updates
- Service logs via WebSocket

### Day 7: Performance Optimization
- Add Redis caching layer
- Implement request batching
- Optimize Prometheus queries

### Day 8: Error Recovery
- Implement request queue for offline mode
- Add retry policies
- Persist state across restarts

---

**Status:** Ready to implement
**Confidence:** High (90%)
**Risk:** Low
**Estimated Time:** 6-7 hours
**Dependencies:** All services must be running

---

*Let's ship real data integration! 💪*
