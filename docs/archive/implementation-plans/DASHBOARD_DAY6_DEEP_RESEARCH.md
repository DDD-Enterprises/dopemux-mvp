---
id: DASHBOARD_DAY6_DEEP_RESEARCH
title: Dashboard_Day6_Deep_Research
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dashboard_Day6_Deep_Research (explanation) for dopemux documentation and
  developer workflows.
---
# Dashboard Day 6 - Deep Research & Planning 🔬
## Complete API Integration & Production Readiness

**Created:** 2025-10-29
**Sprint:** Week 2, Day 6 - Real Data Integration
**Status:** 🧠 Deep Research Phase
**Goal:** Transform modals from prototypes to production with real APIs

---

## 🎯 EXECUTIVE SUMMARY

### Where We Are (Day 5 Complete)
- ✅ 4 modal dialogs fully functional (task/service/pattern/metric)
- ✅ Keyboard shortcuts working (`d`, `l`, `p`, `h`)
- ✅ Rich formatting and async infrastructure
- ✅ SparklineGenerator fetching Prometheus data
- ⚠️  **All modal data still mocked**

### What We're Building Today
**Transform from UI prototype → Production monitoring tool**

1. **Wire 4 modals to real backend APIs**
   - Task Detail → ADHD Engine + ConPort
   - Service Logs → Docker logs + Health checks
   - Pattern Analysis → Prometheus aggregations
   - Metric History → Prometheus time-series

2. **Build robust data layer**
   - API client abstraction
   - Caching & retry logic
   - Graceful degradation
   - Error recovery

3. **Performance optimization**
   - Response < 500ms for all modals
   - Background prefetching
   - Smart cache invalidation

### Success Criteria

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Modal Load Time** | < 500ms | ADHD users need instant feedback |
| **API Success Rate** | > 95% | Dashboard must be reliable |
| **Data Freshness** | < 5s lag | Real-time state tracking |
| **Cache Hit Rate** | > 70% | Reduce backend pressure |
| **Error Recovery** | Auto-retry 3x | Services restart in dev |
| **Fallback Quality** | Graceful msgs | Never show stack traces |

---

## 📊 PHASE 1: API LANDSCAPE DEEP DIVE

### 1.1 Backend Services Inventory

#### Service Map
```
┌─────────────────────────────────────────────────────────────┐
│                    DOPEMUX BACKEND ECOSYSTEM                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ADHD Engine  │  │   ConPort    │  │    Serena    │      │
│  │  Port 8000   │  │  Port 5432   │  │   Port TBD   │      │
│  │              │  │              │  │              │      │
│  │ • Energy     │  │ • Decisions  │  │ • Tasks      │      │
│  │ • Attention  │  │ • Context    │  │ • Scoring    │      │
│  │ • Breaks     │  │ • Search     │  │ • Matching   │      │
│  │ • Tasks      │  │ • History    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Prometheus   │  │    Redis     │  │  PostgreSQL  │      │
│  │  Port 9090   │  │  Port 6379   │  │  Port 5432   │      │
│  │              │  │              │  │              │      │
│  │ • Metrics    │  │ • Events     │  │ • Decisions  │      │
│  │ • History    │  │ • Cache      │  │ • Sessions   │      │
│  │ • Queries    │  │ • PubSub     │  │ • Analytics  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 API Endpoint Research

#### ADHD Engine (Port 8000)
**Status:** ✅ Production Ready
**Location:** `services/adhd-engine/` (assumed - needs verification)
**Protocol:** HTTP REST + WebSocket (future)

```python
# === CURRENT STATE ENDPOINTS ===

GET /api/v1/energy-level/{user_id}
Response: {
    "energy_level": "LOW" | "MEDIUM" | "HIGH" | "PEAK",
    "confidence": 0.85,  # 0.0-1.0
    "factors": [
        "time_of_day: morning_optimal",
        "sleep_quality: good",
        "recent_breaks: insufficient"
    ],
    "recommendations": [
        "Consider a 5-minute walk before starting complex tasks"
    ],
    "last_updated": "2025-10-29T09:45:00Z",
    "next_update_in": 600  # seconds
}

GET /api/v1/attention-state/{user_id}
Response: {
    "state": "FOCUSED" | "SCATTERED" | "HYPERFOCUS" | "DISTRACTED",
    "duration_minutes": 45,
    "interruptions_count": 3,
    "context_switches": 7,
    "quality_score": 0.72,  # 0.0-1.0
    "stability": "HIGH" | "MEDIUM" | "LOW",
    "trend": "IMPROVING" | "STABLE" | "DEGRADING",
    "metadata": {
        "session_start": "2025-10-29T08:00:00Z",
        "last_focus_event": "2025-10-29T09:30:00Z"
    }
}

# === TASK ASSESSMENT ===

POST /api/v1/assess-task
Request: {
    "user_id": "user_123",
    "task_data": {
        "id": "task_456",
        "title": "Refactor authentication module",
        "description": "Update OAuth2 implementation...",
        "complexity": 0.75,  # 0.0-1.0
        "estimated_duration_minutes": 120,
        "requires_deep_focus": true,
        "can_be_interrupted": false,
        "tags": ["backend", "security", "refactoring"]
    },
    "context": {
        "current_energy": "HIGH",  # optional, will fetch if missing
        "current_attention": "FOCUSED",
        "available_time_minutes": 90
    }
}

Response: {
    "assessment_id": "assess_789",
    "is_suitable": true,
    "suitability_score": 0.82,  # Overall match
    "match_breakdown": {
        "energy_match": 0.90,
        "attention_match": 0.85,
        "time_match": 0.70,  # Has 90min, needs 120min
        "complexity_match": 0.85
    },
    "cognitive_load_impact": {
        "predicted_load": 0.78,
        "load_category": "HIGH",
        "sustainability": "2_hours",  # Can sustain for this long
        "recovery_needed": "15_minutes"
    },
    "accommodations": [
        {
            "type": "BREAK_SCHEDULE",
            "description": "Take 5-min break at 45-minute mark",
            "importance": "HIGH"
        },
        {
            "type": "ENVIRONMENT",
            "description": "Use noise-cancelling headphones",
            "importance": "MEDIUM"
        }
    ],
    "warnings": [
        "Task duration (120min) exceeds available time (90min)",
        "Consider breaking into 2 sessions"
    ],
    "alternative_suggestions": [
        {
            "task_id": "task_123",
            "title": "Update API documentation",
            "suitability_score": 0.95,
            "reason": "Better match for current energy/time"
        }
    ],
    "created_at": "2025-10-29T09:45:00Z"
}

# === BREAK RECOMMENDATIONS ===

POST /api/v1/recommend-break
Request: {
    "user_id": "user_123",
    "session_context": {
        "current_duration_minutes": 75,
        "cognitive_load": 0.82,
        "interruption_count": 5,
        "last_break_minutes_ago": 90
    }
}

Response: {
    "recommendation_id": "break_456",
    "should_break": true,
    "urgency": "HIGH",  # LOW | MEDIUM | HIGH | CRITICAL
    "recommended_duration_minutes": 10,
    "break_type": "WALK",  # MICRO | SHORT | LONG | WALK | MEAL
    "activities": [
        "Walk outside for 10 minutes",
        "Stretch and hydrate",
        "Look at distant objects (eye rest)"
    ],
    "reasons": [
        "Cognitive load approaching threshold (0.82)",
        "No break in 90 minutes",
        "Quality score declining (0.72 -> 0.65)"
    ],
    "impact_prediction": {
        "expected_recovery": 0.40,  # Load reduction
        "estimated_boost": "20-30 minutes of renewed focus",
        "productivity_gain": "15% for next session"
    },
    "created_at": "2025-10-29T09:45:00Z"
}

# === HISTORICAL DATA ===

GET /api/v1/history/energy-levels/{user_id}
Query Params:
  - start_date: ISO8601 (default: 7 days ago)
  - end_date: ISO8601 (default: now)
  - granularity: hour | day | week

Response: {
    "user_id": "user_123",
    "period": {
        "start": "2025-10-22T00:00:00Z",
        "end": "2025-10-29T09:45:00Z"
    },
    "data_points": [
        {
            "timestamp": "2025-10-29T08:00:00Z",
            "energy_level": "HIGH",
            "confidence": 0.85
        },
        // ... more points
    ],
    "statistics": {
        "most_common_level": "MEDIUM",
        "peak_hours": ["09:00-11:00", "14:00-16:00"],
        "low_hours": ["13:00-14:00", "16:00-17:00"],
        "average_confidence": 0.82
    }
}
```

#### ConPort - Context & Decision Database (PostgreSQL + HTTP)
**Status:** ✅ Production Ready
**Location:** `docker/mcp-servers/conport/`
**Protocol:** MCP (stdio) + PostgreSQL direct + HTTP (via bridge)

```python
# === DECISION HISTORY ===

# Via PostgreSQL (direct queries)
"""
SELECT
    decision_id,
    decision_type,
    context_summary,
    outcome,
    created_at,
    confidence_score,
    tags
FROM decisions
WHERE user_id = $1
    AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 50;
"""

# Via MCP (stdio - existing)
# Already have: unified_queries.py with decision search

# Via HTTP Bridge (NEW - need to build)
GET /api/v1/decisions/recent?user_id={user_id}&limit=50
Response: {
    "decisions": [
        {
            "id": "dec_123",
            "type": "TASK_SELECTION",
            "summary": "Chose refactoring over new feature",
            "rationale": "Energy level optimal for deep focus",
            "outcome": "SUCCESSFUL",
            "created_at": "2025-10-29T08:30:00Z",
            "tags": ["task_management", "prioritization"]
        }
    ]
}

GET /api/v1/context/current?user_id={user_id}
Response: {
    "current_project": "dopemux-mvp",
    "active_tasks": ["task_456", "task_789"],
    "recent_files": ["/path/to/file1.py", "/path/to/file2.py"],
    "session_duration_minutes": 120,
    "context_switches_count": 7
}

# === SEARCH (via unified_queries.py) ===
# Already implemented - just need HTTP wrapper
```

#### Prometheus (Port 9090)
**Status:** ✅ Already integrated (prometheus_client.py exists)
**Location:** `prometheus_client.py` (root)
**Protocol:** HTTP REST

```python
# Already have PrometheusClient class ✅
# Need to add aggregation queries

# === NEW AGGREGATION QUERIES ===

# Pattern Detection Query
query = """
rate(adhd_context_switches_total[5m]) > 2
"""
# Returns: High context-switch periods

# Cognitive Load Patterns
query = """
avg_over_time(adhd_cognitive_load[1h])
"""
# Returns: Hourly average load

# Service Health Rollup
query = """
up{job=~"adhd_engine|conport|serena"}
"""
# Returns: Which services are up/down

# Task Completion Velocity
query = """
increase(adhd_tasks_completed_total[24h])
"""
# Returns: Tasks completed per day
```

#### Docker Services (Health & Logs)
**Status:** ✅ System commands available
**Protocol:** Shell commands via subprocess

```python
# === HEALTH CHECKS ===

# Get service status
import subprocess
result = subprocess.run(
    ['docker', 'ps', '--filter', 'name=adhd_engine', '--format', '{{.Status}}'],
    capture_output=True,
    text=True
)
# Returns: "Up 3 hours" or "Exited (1) 5 minutes ago"

# === LOGS ===

# Fetch recent logs
result = subprocess.run(
    ['docker', 'logs', '--tail', '100', 'adhd_engine'],
    capture_output=True,
    text=True
)
# Returns: Last 100 log lines

# Stream logs (for modal)
process = subprocess.Popen(
    ['docker', 'logs', '-f', '--tail', '50', 'service_name'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)
# Returns: Streaming file-like object
```

---

## 🏗️ PHASE 2: DATA LAYER ARCHITECTURE

### 2.1 API Client Design Pattern

```python
"""
Unified API Client with retry, caching, and fallback
"""

from typing import Optional, Dict, Any, List, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import httpx
import logging
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    NO_CACHE = "no_cache"
    SHORT = "short"      # 5 seconds
    MEDIUM = "medium"    # 30 seconds
    LONG = "long"        # 5 minutes
    PERSISTENT = "persistent"  # Until explicit invalidation


@dataclass
class CacheEntry(Generic[T]):
    """Cached data with metadata"""
    data: T
    cached_at: datetime
    ttl_seconds: int

    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.now() - self.cached_at).total_seconds()
        return age < self.ttl_seconds


@dataclass
class APIConfig:
    """Configuration for API client"""
    base_url: str
    timeout: float = 5.0
    max_retries: int = 3
    retry_delay: float = 0.5
    cache_strategy: CacheStrategy = CacheStrategy.MEDIUM
    fallback_enabled: bool = True


class APIClient:
    """
    Base API client with built-in retry, caching, and error handling

    Features:
    - Automatic retry with exponential backoff
    - Response caching with TTL
    - Graceful fallback to cached/default data
    - Request deduplication (prevent duplicate in-flight requests)
    - Comprehensive error logging
    """

    def __init__(self, config: APIConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            follow_redirects=True
        )
        self._cache: Dict[str, CacheEntry] = {}
        self._in_flight: Dict[str, asyncio.Task] = {}

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        fallback_data: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute GET request with retry and caching

        Args:
            endpoint: API endpoint (e.g., '/api/v1/energy-level/user123')
            params: Query parameters
            cache_key: Key for caching (default: endpoint)
            fallback_data: Data to return if all retries fail

        Returns:
            Response data or fallback_data or None
        """
        cache_key = cache_key or endpoint

        # Check cache first
        if cached := self._get_from_cache(cache_key):
            logger.debug(f"Cache hit: {cache_key}")
            return cached

        # Check if request already in flight (deduplication)
        if cache_key in self._in_flight:
            logger.debug(f"Request already in flight: {cache_key}")
            return await self._in_flight[cache_key]

        # Create new request task
        task = asyncio.create_task(
            self._execute_with_retry(endpoint, params, fallback_data)
        )
        self._in_flight[cache_key] = task

        try:
            result = await task
            if result is not None:
                self._store_in_cache(cache_key, result)
            return result
        finally:
            del self._in_flight[cache_key]

    async def _execute_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        fallback_data: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute request with exponential backoff retry"""
        url = f"{self.config.base_url}{endpoint}"

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.get(url, params=params)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Endpoint not found: {url}")
                    return fallback_data
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries} "
                        f"failed with status {response.status_code}"
                    )
            except httpx.TimeoutException:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries} "
                    f"timed out for {url}"
                )
            except Exception as e:
                logger.error(
                    f"Attempt {attempt + 1}/{self.config.max_retries} "
                    f"failed with error: {e}"
                )

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        # All retries failed
        if self.config.fallback_enabled:
            logger.error(
                f"All retries failed for {url}, returning fallback data"
            )
            return fallback_data

        return None

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_valid():
            return entry.data

        # Expired, remove from cache
        del self._cache[key]
        return None

    def _store_in_cache(self, key: str, data: Any) -> None:
        """Store data in cache with TTL"""
        ttl_map = {
            CacheStrategy.SHORT: 5,
            CacheStrategy.MEDIUM: 30,
            CacheStrategy.LONG: 300,
            CacheStrategy.PERSISTENT: 86400,  # 24 hours
        }

        ttl = ttl_map.get(self.config.cache_strategy, 30)

        self._cache[key] = CacheEntry(
            data=data,
            cached_at=datetime.now(),
            ttl_seconds=ttl
        )

    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry or all cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
```

### 2.2 Service-Specific Clients

```python
"""
High-level clients for each backend service
"""

class ADHDEngineClient(APIClient):
    """Client for ADHD Engine API"""

    def __init__(self):
        super().__init__(APIConfig(
            base_url="http://localhost:8000",
            cache_strategy=CacheStrategy.SHORT  # 5s for real-time state
        ))

    async def get_energy_level(self, user_id: str) -> Dict[str, Any]:
        """Get current energy level"""
        return await self.get(
            f"/api/v1/energy-level/{user_id}",
            cache_key=f"energy_{user_id}",
            fallback_data={
                "energy_level": "MEDIUM",
                "confidence": 0.5,
                "factors": ["Service unavailable"],
                "recommendations": [],
                "last_updated": datetime.now().isoformat()
            }
        )

    async def assess_task(
        self,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess task suitability"""
        # POST requests don't use cache
        url = f"{self.config.base_url}/api/v1/assess-task"

        try:
            response = await self.client.post(url, json={
                "user_id": user_id,
                "task_data": task_data
            })

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Task assessment failed: {e}")

        # Fallback
        return {
            "is_suitable": True,
            "suitability_score": 0.5,
            "accommodations": [],
            "warnings": ["Assessment service unavailable"]
        }


class ConPortClient:
    """Client for ConPort decision database"""

    def __init__(self):
        self.db_connection = None  # PostgreSQL connection
        # Could also use HTTP bridge (future)

    async def get_recent_decisions(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent decisions from PostgreSQL"""
        # Direct PostgreSQL query for now
        # TODO: Switch to HTTP API when bridge is ready

        try:
            # Simplified - would use asyncpg in production
            query = """
                SELECT
                    decision_id,
                    decision_type,
                    context_summary,
                    outcome,
                    created_at
                FROM decisions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            # Execute query...
            return []  # Placeholder
        except Exception as e:
            logger.error(f"Failed to fetch decisions: {e}")
            return []


class DockerServiceClient:
    """Client for Docker service health and logs"""

    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get Docker service status"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'ps',
                '--filter', f'name={service_name}',
                '--format', '{{.Status}}|{{.State}}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode().strip()
                if output:
                    status, state = output.split('|')
                    return {
                        "service": service_name,
                        "status": status,
                        "state": state,
                        "is_healthy": state == "running"
                    }
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")

        return {
            "service": service_name,
            "status": "Unknown",
            "state": "unknown",
            "is_healthy": False
        }

    async def get_recent_logs(
        self,
        service_name: str,
        lines: int = 100
    ) -> List[str]:
        """Get recent logs from Docker service"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'logs',
                '--tail', str(lines),
                service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                return stdout.decode().split('\n')
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")

        return ["Unable to fetch logs"]
```

---

## 🎨 PHASE 3: MODAL DATA WIRING

### 3.1 Task Detail Modal

```python
"""
Task Detail Modal - Real ADHD Engine Integration
"""

class TaskDetailModal(ModalScreen):
    """Enhanced task detail with real API data"""

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id
        self.adhd_client = ADHDEngineClient()
        self.conport_client = ConPortClient()

    async def compose(self) -> ComposeResult:
        """Build modal with real data"""
        # Fetch data in parallel
        task_data, assessment, history = await asyncio.gather(
            self._fetch_task_data(),
            self._fetch_task_assessment(),
            self._fetch_task_history()
        )

        yield Container(
            Static(self._render_task_header(task_data)),
            Static(self._render_assessment(assessment)),
            Static(self._render_history(history)),
            Static(self._render_actions(assessment)),
            id="task-detail-modal"
        )

    async def _fetch_task_data(self) -> Dict[str, Any]:
        """Get task details from ConPort"""
        # TODO: Implement when ConPort HTTP API ready
        return {
            "id": self.task_id,
            "title": "Implement API integration",
            "complexity": 0.75,
            "estimated_duration": 120
        }

    async def _fetch_task_assessment(self) -> Dict[str, Any]:
        """Get real-time ADHD assessment"""
        task_data = await self._fetch_task_data()

        assessment = await self.adhd_client.assess_task(
            user_id="current_user",  # TODO: Get from session
            task_data=task_data
        )

        return assessment

    async def _fetch_task_history(self) -> List[Dict[str, Any]]:
        """Get task decision history"""
        decisions = await self.conport_client.get_recent_decisions(
            user_id="current_user",
            limit=10
        )

        # Filter for this task
        return [d for d in decisions if d.get('task_id') == self.task_id]

    def _render_assessment(self, assessment: Dict[str, Any]) -> str:
        """Render ADHD assessment section"""
        if not assessment:
            return "[yellow]⚠ Assessment unavailable[/yellow]"

        score = assessment.get('suitability_score', 0)
        is_suitable = assessment.get('is_suitable', False)

        # Color coding
        if score >= 0.8:
            color = "green"
            icon = "✓"
        elif score >= 0.6:
            color = "yellow"
            icon = "!"
        else:
            color = "red"
            icon = "✗"

        output = f"[{color}]{icon} Suitability: {score:.0%}[/{color}]\n\n"

        # Match breakdown
        breakdown = assessment.get('match_breakdown', {})
        output += "Match Scores:\n"
        output += f"  Energy:    {breakdown.get('energy_match', 0):.0%}\n"
        output += f"  Attention: {breakdown.get('attention_match', 0):.0%}\n"
        output += f"  Time:      {breakdown.get('time_match', 0):.0%}\n\n"

        # Accommodations
        if accommodations := assessment.get('accommodations', []):
            output += "Recommended Accommodations:\n"
            for acc in accommodations:
                output += f"  • {acc['description']}\n"

        # Warnings
        if warnings := assessment.get('warnings', []):
            output += "\n[yellow]Warnings:[/yellow]\n"
            for warning in warnings:
                output += f"  ⚠ {warning}\n"

        return output
```

### 3.2 Service Logs Modal

```python
"""
Service Logs Modal - Real Docker Integration
"""

class ServiceLogsModal(ModalScreen):
    """Live service logs viewer"""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.docker_client = DockerServiceClient()
        self.log_widget = None

    async def compose(self) -> ComposeResult:
        """Build modal with streaming logs"""
        # Fetch initial data
        status = await self.docker_client.get_service_status(self.service_name)
        logs = await self.docker_client.get_recent_logs(self.service_name, lines=50)

        self.log_widget = Static(
            "\n".join(logs),
            id="log-content"
        )

        yield Container(
            Static(self._render_header(status)),
            self.log_widget,
            Static(self._render_footer()),
            id="service-logs-modal"
        )

        # Start log streaming
        self.set_interval(2.0, self._refresh_logs)

    def _render_header(self, status: Dict[str, Any]) -> str:
        """Render service status header"""
        is_healthy = status.get('is_healthy', False)
        status_text = status.get('status', 'Unknown')

        if is_healthy:
            color = "green"
            icon = "●"
        else:
            color = "red"
            icon = "●"

        return f"[{color}]{icon}[/{color}] {self.service_name} - {status_text}"

    async def _refresh_logs(self) -> None:
        """Refresh logs periodically"""
        logs = await self.docker_client.get_recent_logs(self.service_name, lines=50)

        if self.log_widget:
            self.log_widget.update("\n".join(logs))
```

### 3.3 Pattern Analysis Modal

```python
"""
Pattern Analysis Modal - Prometheus Aggregations
"""

class PatternAnalysisModal(ModalScreen):
    """Pattern detection from Prometheus metrics"""

    def __init__(self):
        super().__init__()
        self.prom_client = PrometheusClient()

    async def compose(self) -> ComposeResult:
        """Build modal with pattern analysis"""
        # Fetch patterns in parallel
        patterns = await asyncio.gather(
            self._detect_context_switch_pattern(),
            self._detect_energy_pattern(),
            self._detect_break_pattern()
        )

        yield Container(
            Static(self._render_patterns(patterns)),
            id="pattern-analysis-modal"
        )

    async def _detect_context_switch_pattern(self) -> Dict[str, Any]:
        """Detect high context-switch periods"""
        query = 'rate(adhd_context_switches_total[5m]) > 2'
        data = await self.prom_client.query_range(query, hours=24)

        if not data:
            return {"pattern": "none", "severity": "low"}

        # Analyze data
        high_periods = []
        for timestamp, value in data:
            if value > 2:
                high_periods.append(timestamp)

        if len(high_periods) > 10:
            return {
                "pattern": "frequent_context_switches",
                "severity": "high",
                "count": len(high_periods),
                "recommendation": "Consider longer focus blocks"
            }

        return {"pattern": "normal", "severity": "low"}

    async def _detect_energy_pattern(self) -> Dict[str, Any]:
        """Detect energy level patterns"""
        query = 'adhd_energy_level'
        data = await self.prom_client.query_range(query, hours=168)  # 7 days

        # Analyze by hour of day
        hour_energy = {}
        for timestamp, value in data:
            hour = timestamp.hour
            if hour not in hour_energy:
                hour_energy[hour] = []
            hour_energy[hour].append(value)

        # Find peak hours
        avg_by_hour = {
            hour: sum(values) / len(values)
            for hour, values in hour_energy.items()
        }

        peak_hours = sorted(
            avg_by_hour.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return {
            "pattern": "daily_energy_cycle",
            "peak_hours": [h for h, _ in peak_hours],
            "recommendation": f"Schedule deep work between {peak_hours[0][0]}-{peak_hours[0][0]+2}"
        }

    def _render_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Render pattern analysis"""
        output = "Pattern Analysis (Last 7 Days)\n\n"

        for pattern in patterns:
            if pattern.get('pattern') != 'none':
                severity = pattern.get('severity', 'low')
                color = {
                    'low': 'green',
                    'medium': 'yellow',
                    'high': 'red'
                }.get(severity, 'white')

                output += f"[{color}]● {pattern.get('pattern')}[/{color}]\n"
                if rec := pattern.get('recommendation'):
                    output += f"  → {rec}\n"
                output += "\n"

        return output
```

### 3.4 Metric History Modal

```python
"""
Metric History Modal - Time-Series Visualization
"""

class MetricHistoryModal(ModalScreen):
    """Detailed metric history from Prometheus"""

    def __init__(self, metric_name: str):
        super().__init__()
        self.metric_name = metric_name
        self.prom_client = PrometheusClient()
        self.sparkline_gen = SparklineGenerator(
            PrometheusConfig(base_url="http://localhost:9090")
        )

    async def compose(self) -> ComposeResult:
        """Build modal with metric history"""
        # Fetch different time ranges
        data_2h, data_24h, data_7d = await asyncio.gather(
            self.prom_client.query_range(self.metric_name, hours=2, step="1m"),
            self.prom_client.query_range(self.metric_name, hours=24, step="5m"),
            self.prom_client.query_range(self.metric_name, hours=168, step="1h")
        )

        yield Container(
            Static(self._render_header()),
            Static(self._render_sparklines(data_2h, data_24h, data_7d)),
            Static(self._render_statistics(data_7d)),
            Static(self._render_table(data_24h)),
            id="metric-history-modal"
        )

    def _render_sparklines(
        self,
        data_2h: List[Tuple[datetime, float]],
        data_24h: List[Tuple[datetime, float]],
        data_7d: List[Tuple[datetime, float]]
    ) -> str:
        """Render sparklines for different time ranges"""
        output = "Trends:\n\n"

        if data_2h:
            sparkline_2h = self.sparkline_gen._render_sparkline(
                [v for _, v in data_2h],
                width=40
            )
            output += f"Last 2 hours:  {sparkline_2h}\n"

        if data_24h:
            sparkline_24h = self.sparkline_gen._render_sparkline(
                [v for _, v in data_24h],
                width=40
            )
            output += f"Last 24 hours: {sparkline_24h}\n"

        if data_7d:
            sparkline_7d = self.sparkline_gen._render_sparkline(
                [v for _, v in data_7d],
                width=40
            )
            output += f"Last 7 days:   {sparkline_7d}\n"

        return output

    def _render_statistics(
        self,
        data: List[Tuple[datetime, float]]
    ) -> str:
        """Calculate and render statistics"""
        if not data:
            return ""

        values = [v for _, v in data]

        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)

        # Calculate trend
        if len(values) >= 2:
            recent_avg = sum(values[-10:]) / min(10, len(values))
            older_avg = sum(values[:10]) / min(10, len(values))
            trend = "↑" if recent_avg > older_avg else "↓"
        else:
            trend = "→"

        return f"""
Statistics (7 days):
  Average: {avg:.2f}
  Min:     {min_val:.2f}
  Max:     {max_val:.2f}
  Trend:   {trend}
"""
```

---

## 📈 PHASE 4: PERFORMANCE OPTIMIZATION

### 4.1 Prefetching Strategy

```python
"""
Background prefetching for instant modal display
"""

class DashboardDataPrefetcher:
    """Prefetch data for modals in background"""

    def __init__(self):
        self.adhd_client = ADHDEngineClient()
        self.docker_client = DockerServiceClient()
        self.prom_client = PrometheusClient()

        self.prefetched_data = {}
        self.prefetch_task = None

    def start(self):
        """Start background prefetching"""
        self.prefetch_task = asyncio.create_task(self._prefetch_loop())

    async def _prefetch_loop(self):
        """Continuously prefetch likely-needed data"""
        while True:
            try:
                # Prefetch most commonly viewed data
                await asyncio.gather(
                    self._prefetch_energy_state(),
                    self._prefetch_service_status(),
                    self._prefetch_common_metrics()
                )
            except Exception as e:
                logger.error(f"Prefetch error: {e}")

            await asyncio.sleep(10)  # Prefetch every 10s

    async def _prefetch_energy_state(self):
        """Prefetch ADHD state for task modal"""
        data = await self.adhd_client.get_energy_level("current_user")
        self.prefetched_data['energy_state'] = {
            'data': data,
            'timestamp': datetime.now()
        }

    async def _prefetch_service_status(self):
        """Prefetch service status for logs modal"""
        services = ["adhd_engine", "conport", "serena"]
        statuses = await asyncio.gather(*[
            self.docker_client.get_service_status(svc)
            for svc in services
        ])

        self.prefetched_data['service_status'] = {
            'data': dict(zip(services, statuses)),
            'timestamp': datetime.now()
        }

    async def _prefetch_common_metrics(self):
        """Prefetch commonly viewed metrics"""
        metrics = [
            "adhd_cognitive_load",
            "adhd_task_velocity_per_day",
            "adhd_context_switches_total"
        ]

        data = await asyncio.gather(*[
            self.prom_client.query_range(metric, hours=24)
            for metric in metrics
        ])

        self.prefetched_data['common_metrics'] = {
            'data': dict(zip(metrics, data)),
            'timestamp': datetime.now()
        }

    def get_prefetched(self, key: str, max_age_seconds: int = 30):
        """Get prefetched data if fresh enough"""
        if key not in self.prefetched_data:
            return None

        entry = self.prefetched_data[key]
        age = (datetime.now() - entry['timestamp']).total_seconds()

        if age < max_age_seconds:
            return entry['data']

        return None
```

### 4.2 Response Time Monitoring

```python
"""
Track and optimize modal load times
"""

from contextlib import asynccontextmanager
import time

class PerformanceMonitor:
    """Monitor modal performance metrics"""

    def __init__(self):
        self.metrics = {
            'task_modal_load': [],
            'service_modal_load': [],
            'pattern_modal_load': [],
            'metric_modal_load': []
        }

    @asynccontextmanager
    async def track(self, metric_name: str):
        """Track execution time of async operations"""
        start = time.perf_counter()

        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            self.metrics.setdefault(metric_name, []).append(duration_ms)

            # Log if slow
            if duration_ms > 500:
                logger.warning(
                    f"{metric_name} took {duration_ms:.0f}ms (target: <500ms)"
                )

            # Keep only last 100 measurements
            if len(self.metrics[metric_name]) > 100:
                self.metrics[metric_name] = self.metrics[metric_name][-100:]

    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get performance statistics"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}

        values = self.metrics[metric_name]

        return {
            'avg_ms': sum(values) / len(values),
            'min_ms': min(values),
            'max_ms': max(values),
            'p95_ms': sorted(values)[int(len(values) * 0.95)],
            'count': len(values)
        }

# Usage in modals
perf_monitor = PerformanceMonitor()

async def show_task_modal(task_id: str):
    async with perf_monitor.track('task_modal_load'):
        modal = TaskDetailModal(task_id)
        await modal.compose()
```

---

## 🚀 PHASE 5: IMPLEMENTATION PLAN

### Day 6 Timeline

#### Morning (4 hours)
1. **Build base API client infrastructure** (90 min)
   - Implement APIClient class with retry/cache
   - Add CacheEntry and CacheStrategy
   - Write unit tests

2. **Create service-specific clients** (90 min)
   - ADHDEngineClient
   - DockerServiceClient
   - Test against real services

3. **Wire Task Detail Modal** (60 min)
   - Integrate ADHDEngineClient
   - Real task assessment
   - Test with live data

#### Afternoon (4 hours)
1. **Wire Service Logs Modal** (60 min)
   - Integrate DockerServiceClient
   - Live log streaming
   - Health status display

2. **Wire Pattern Analysis Modal** (90 min)
   - Prometheus aggregation queries
   - Pattern detection logic
   - Visualization

3. **Wire Metric History Modal** (60 min)
   - Multi-timeframe data fetching
   - Statistics calculation
   - Sparkline rendering

4. **Testing & refinement** (30 min)
   - End-to-end modal testing
   - Performance verification
   - Error handling validation

### Acceptance Criteria

- [ ] All 4 modals fetch real data from backends
- [ ] Modal load time < 500ms (95th percentile)
- [ ] API success rate > 95% with retry logic
- [ ] Graceful fallback on service failures
- [ ] Cache hit rate > 70% for repeated views
- [ ] No crashes during 30-minute stress test
- [ ] Error messages user-friendly (no stack traces)
- [ ] All data updates automatically (no manual refresh)

---

## 📊 TESTING STRATEGY

### Integration Tests

```python
"""
Integration tests for API-connected modals
"""

import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_task_modal_with_real_api():
    """Test task modal with live ADHD Engine"""

    # This test requires ADHD Engine running
    modal = TaskDetailModal("task_123")

    # Should load without errors
    result = await modal.compose()
    assert result is not None

    # Should show real assessment data
    assessment = await modal._fetch_task_assessment()
    assert 'suitability_score' in assessment
    assert 0 <= assessment['suitability_score'] <= 1

@pytest.mark.asyncio
async def test_api_client_retry_logic():
    """Test retry mechanism"""

    client = APIClient(APIConfig(
        base_url="http://localhost:9999",  # Non-existent
        max_retries=3,
        retry_delay=0.1
    ))

    result = await client.get(
        "/test",
        fallback_data={"status": "fallback"}
    )

    # Should return fallback after retries
    assert result == {"status": "fallback"}

@pytest.mark.asyncio
async def test_cache_hit_rate():
    """Test caching effectiveness"""

    client = ADHDEngineClient()

    # First call - cache miss
    start = time.time()
    result1 = await client.get_energy_level("user_123")
    first_duration = time.time() - start

    # Second call - cache hit
    start = time.time()
    result2 = await client.get_energy_level("user_123")
    second_duration = time.time() - start

    # Cached call should be much faster
    assert second_duration < first_duration / 10
    assert result1 == result2
```

### Performance Tests

```python
"""
Performance benchmarks for modals
"""

@pytest.mark.asyncio
async def test_modal_load_time():
    """All modals should load in <500ms"""

    modals = [
        TaskDetailModal("task_123"),
        ServiceLogsModal("adhd_engine"),
        PatternAnalysisModal(),
        MetricHistoryModal("adhd_cognitive_load")
    ]

    for modal in modals:
        start = time.perf_counter()
        await modal.compose()
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 500, f"{modal.__class__.__name__} took {duration_ms}ms"
```

---

## 🎯 SUCCESS METRICS

### Performance Targets
- **Modal Load Time:** < 500ms (p95)
- **API Success Rate:** > 95%
- **Cache Hit Rate:** > 70%
- **Memory Usage:** < 100MB total
- **CPU Usage:** < 5% average

### User Experience
- **No Crashes:** 0 crashes in 30-min session
- **Error Clarity:** User-friendly error messages
- **Data Freshness:** < 5s lag from backend
- **Responsiveness:** Keyboard shortcuts instant

### Code Quality
- **Test Coverage:** > 80% for API clients
- **Type Hints:** 100% of public APIs
- **Documentation:** Docstrings for all classes/methods
- **Logging:** Comprehensive error/warning logs

---

## 🔄 NEXT STEPS (Day 7+)

After completing Day 6 API integration:

1. **WebSocket Integration** (Day 7)
   - Real-time event streaming
   - Live sparkline updates
   - Push notifications

2. **Advanced Analytics** (Day 8)
   - Predictive break suggestions
   - Task correlation analysis
   - Productivity forecasting

3. **Polish & UX** (Day 9-10)
   - Animation and transitions
   - Theme customization
   - Accessibility features

4. **Documentation** (Day 11-12)
   - User guide
   - API documentation
   - Troubleshooting guide

5. **Production Deployment** (Day 13-14)
   - Docker containerization
   - CI/CD pipeline
   - Monitoring & alerting

---

## 📝 NOTES & DECISIONS

### Architecture Decisions

**Q: Why build custom API client vs using existing library?**
A: Need specific features (request deduplication, smart caching, ADHD-optimized retry) not available in standard httpx/aiohttp.

**Q: Should we use PostgreSQL directly or wait for HTTP bridge?**
A: Start with direct PostgreSQL for decisions (already have asyncpg), migrate to HTTP when bridge ready.

**Q: Cache strategy for real-time data?**
A: 5s TTL for energy/attention (frequently changing), 30s for metrics (less critical), 5min for historical data (static).

### Risk Mitigation

**Risk:** Backend services down during development
**Mitigation:** Comprehensive fallback data, mock mode toggle

**Risk:** Slow Prometheus queries
**Mitigation:** Optimize PromQL, limit time ranges, cache aggressively

**Risk:** Modal load time > 500ms
**Mitigation:** Prefetching, parallel requests, streaming rendering

---

**LET'S BUILD! 🚀**

Ready to wire these modals to production data and create a truly intelligent ADHD-optimized dashboard!
