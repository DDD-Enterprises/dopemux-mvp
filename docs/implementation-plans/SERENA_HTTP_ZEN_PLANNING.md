# Serena HTTP Wrapper - Zen Research & Deep Planning

**Date:** 2025-10-29  
**Time:** Evening Session  
**Status:** Research & Planning Phase  
**Philosophy:** Zen approach - understand deeply before building  

---

## 🧘 ZEN RESEARCH PHASE

### What is Serena?

**Core Purpose:** Pattern detection and intelligent code analysis system

**Key Capabilities:**
1. **Untracked Work Detection** - Finds uncommitted work
2. **Pattern Learning** - Learns from developer behavior  
3. **Abandonment Tracking** - Identifies stuck/abandoned work
4. **Design-First Detection** - Suggests design before implementation
5. **ADHD-Optimized** - Progressive disclosure, cognitive load management
6. **Metrics & Analytics** - Aggregates detection results (F1-F8 features)

**Architecture Discovery:**
```
services/serena/
├── server.py                    # MCP wrapper (stdio mode)
├── v2/
│   ├── metrics_dashboard.py     # F7: Metrics aggregation
│   ├── pattern_learner.py       # Pattern detection
│   ├── abandonment_tracker.py   # Abandonment scoring
│   ├── design_first_detector.py # Design prompting
│   ├── git_detector.py          # Git-based detection
│   └── intelligence/            # Phase 3 intelligence layer
│       ├── cognitive_load_orchestrator.py
│       ├── fatigue_detection_engine.py
│       ├── performance_validation_system.py
│       └── ...
```

---

## 🔍 DEEP DISCOVERY

### What Dashboard Needs

From our planning docs, dashboard wants:
1. **Pattern Detection Metrics**
   - Total detections
   - Pass rate (threshold)
   - Average confidence scores

2. **Detection Summary**
   - Recent detections
   - Top patterns found
   - Session distribution

3. **Performance Metrics** (nice to have)
   - Latency
   - Cache hit rate
   - Processing time

### What Serena Actually Has

**From metrics_dashboard.py:**
- `MetricsAggregator` class
- `aggregate_detections(results)` - Aggregates F1-F6 metrics
- `calculate_f1_f4_metrics()` - Detection system metrics
- `calculate_f5_metrics()` - Pattern learning metrics
- `calculate_f6_metrics()` - Abandonment metrics

**Metrics Available:**
```python
{
    "total_detections": 42,
    "timestamp": "2025-10-29T...",
    "f1_f4_metrics": {
        "total_detections": 42,
        "passed": 28,
        "pass_rate": 0.67,
        "avg_confidence": 0.75,
        "avg_threshold": 0.6,
        "session_distribution": {"1": 10, "2": 15, "3+": 17}
    },
    "f5_metrics": {
        "patterns_learned": 8,
        "boost_rate": 0.35,
        "avg_boost": 0.12,
        "top_patterns": [...]
    },
    "f6_metrics": {
        "abandoned_count": 5,
        "avg_severity": "medium",
        "action_suggestions": [...]
    }
}
```

**Current State:**
- ✅ Metrics aggregation code exists
- ❓ No HTTP interface yet (only MCP)
- ❓ No persistent storage (metrics calculated on-demand)
- ❓ No recent detections endpoint

---

## 🤔 PHILOSOPHICAL QUESTIONS

### Question 1: Real Data vs Mock Data?

**Option A: Mock Data (Like ConPort)**
```python
# Simple, fast, ships today
mock_metrics = {
    "detections": {
        "total": 42,
        "passed": 28,
        "confidence_avg": 0.75
    }
}
```

**Option B: Call Real Serena Logic**
```python
# Complex, requires integration
from serena.v2.metrics_dashboard import MetricsAggregator
aggregator = MetricsAggregator()
# But where to get results from?
```

**Option C: Hybrid Approach**
```python
# Use Serena's data structures, populate with mock
# Validates integration path, provides real schema
```

**🧘 Zen Decision:** Option C  
**Why:** Honors Serena's design while shipping working dashboard today

### Question 2: What Data to Expose?

**Minimal (MVP):**
- Total detection count
- Pass rate
- Average confidence
- Top 3 patterns

**Complete:**
- Full F1-F8 metrics
- Historical trends
- Per-session breakdowns
- Abandonment tracking
- Design suggestions

**🧘 Zen Decision:** Minimal + Progressive Disclosure  
**Why:** ADHD-friendly, matches Serena's philosophy, expandable

### Question 3: Architecture Pattern?

**Option A: Standalone HTTP (Like ConPort)**
```
HTTP Server (Port 8003)
└── Mock/Static data
```

**Option B: Wrapper Around Serena Logic**
```
HTTP Server (Port 8003)
└── Import Serena modules
    └── Call MetricsAggregator
```

**Option C: Event-Based**
```
HTTP Server (Port 8003)
└── Subscribe to Redis events
    └── Aggregate from event stream
```

**🧘 Zen Decision:** Option A with B-readiness  
**Why:**
- Ships today (mock data)
- Structure ready for real integration
- No blocking dependencies
- Can iterate to Option B later

---

## 📐 ARCHITECTURE DESIGN

### Endpoint Design

#### 1. GET `/api/metrics`

**Purpose:** Dashboard metrics overview

**Response Schema:**
```json
{
  "detections": {
    "total": 42,
    "passed": 28,
    "pass_rate": 0.67,
    "confidence_avg": 0.75
  },
  "patterns": [
    {
      "name": "feature_branch_work",
      "frequency": 12,
      "confidence": 0.82
    }
  ],
  "performance": {
    "latency_ms": 45,
    "cache_hit_rate": 0.85
  },
  "source": "mock|real",
  "timestamp": "2025-10-29T..."
}
```

#### 2. GET `/api/detections/summary`

**Purpose:** Recent detection summary

**Response Schema:**
```json
{
  "total": 42,
  "passed_threshold": 28,
  "top_patterns": [
    {
      "pattern": "uncommitted_feature",
      "count": 8,
      "avg_confidence": 0.78
    }
  ],
  "session_distribution": {
    "single": 10,
    "double": 15,
    "triple_plus": 17
  },
  "abandonment": {
    "count": 5,
    "severity": "medium"
  },
  "source": "mock|real",
  "timestamp": "2025-10-29T..."
}
```

#### 3. GET `/health`

**Purpose:** Service health check

**Response Schema:**
```json
{
  "status": "healthy",
  "service": "serena",
  "version": "v2",
  "detectors": {
    "git": "ready",
    "pattern": "ready",
    "abandonment": "ready"
  },
  "timestamp": "2025-10-29T..."
}
```

---

## 🎨 SERENA'S ADHD PHILOSOPHY

### Core Principles (From Code Analysis)

1. **Progressive Disclosure**
   - Don't overwhelm with all metrics at once
   - Show summary → details → trends (3 levels)
   - Max 5 items per view

2. **Cognitive Load Management**
   - Limit search results (max 10)
   - Context depth limited (3 levels)
   - Visual indicators instead of numbers

3. **Gentle Guidance**
   - Suggest, don't command
   - Acknowledge energy levels
   - Adaptive to user state

4. **ADHD-Optimized Presentation**
   ```python
   # From metrics_dashboard.py
   self.adhd_config = {
       "max_items_per_level": 5,
       "use_visual_indicators": True,
       "progressive_disclosure": True,
       "context_aware_suggestions": True
   }
   ```

**🧘 Zen Insight:** Our HTTP wrapper should honor these principles

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Skeleton Server (10 min)

**Goal:** Server running, responding

**File:** `services/serena/v2/http_server.py`

**Code:**
```python
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Serena HTTP API", version="2.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "serena"}

@app.get("/api/metrics")
async def get_metrics():
    return {"detections": {"total": 0}}

@app.get("/api/detections/summary")
async def get_detections_summary():
    return {"total": 0}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

### Phase 2: Mock Data (15 min)

**Goal:** Dashboard-ready responses

**Approach:**
1. Create mock data based on Serena's real schema
2. Use realistic values (from code analysis)
3. Include "source": "mock" field
4. Add ADHD-friendly formatting

**Mock Data Design:**
```python
MOCK_METRICS = {
    "detections": {
        "total": 42,
        "passed": 28,
        "pass_rate": 0.67,
        "confidence_avg": 0.75
    },
    "patterns": [
        {"name": "feature_branch_work", "frequency": 12, "confidence": 0.82},
        {"name": "quick_fix_iteration", "frequency": 8, "confidence": 0.74},
        {"name": "exploratory_coding", "frequency": 7, "confidence": 0.69}
    ],
    "performance": {
        "latency_ms": 45,
        "cache_hit_rate": 0.85
    },
    "source": "mock",
    "adhd_friendly": {
        "top_insight": "Most work happens in feature branches (12 detections)",
        "suggestion": "Consider committing exploratory work to preserve context"
    }
}
```

### Phase 3: Integration Preparation (10 min)

**Goal:** Structure ready for real Serena integration

**Code:**
```python
from typing import Optional
from serena.v2.metrics_dashboard import MetricsAggregator

aggregator: Optional[MetricsAggregator] = None

@app.on_event("startup")
async def startup():
    global aggregator
    try:
        aggregator = MetricsAggregator()
        logger.info("✅ Serena metrics aggregator ready")
    except Exception as e:
        logger.warning(f"⚠️  Using mock data: {e}")

@app.get("/api/metrics")
async def get_metrics():
    if aggregator:
        try:
            # TODO: Get real detection results
            # results = await get_detection_results()
            # real_metrics = aggregator.aggregate_detections(results)
            # return real_metrics
            pass
        except Exception as e:
            logger.warning(f"Falling back to mock: {e}")
    
    return MOCK_METRICS
```

### Phase 4: Dashboard Integration (10 min)

**Goal:** Dashboard shows Serena data

**Changes:**
1. Update `dopemux_dashboard.py` ENDPOINTS
2. Update `get_patterns()` method
3. Test end-to-end
4. Verify graceful fallback

**Total Time:** 45 minutes

---

## 🎯 SUCCESS CRITERIA

### Must Have
- [ ] HTTP server running on port 8003
- [ ] `/health` endpoint responds
- [ ] `/api/metrics` returns metrics
- [ ] `/api/detections/summary` returns summary
- [ ] Dashboard connects without errors
- [ ] Mock data follows Serena's schema
- [ ] ADHD-friendly formatting

### Nice to Have
- [ ] Real Serena aggregator initialized
- [ ] Structure ready for real data
- [ ] Progressive disclosure levels
- [ ] Visual indicators

### Can Defer
- [ ] Real detection results
- [ ] Historical trends
- [ ] Persistent storage
- [ ] Event bus integration

---

## ⚠️ POTENTIAL CHALLENGES

### Challenge 1: Understanding Serena's Data Flow
**Issue:** Serena is complex, lots of modules  
**Solution:** Start with MetricsAggregator interface, ignore internals  
**Time:** Already researched, mitigated

### Challenge 2: Mock Data Quality
**Issue:** Mock data doesn't match reality  
**Solution:** Base on real Serena schema, realistic values  
**Time:** 10 min extra for research

### Challenge 3: Integration Complexity
**Issue:** Serena uses async, events, Redis, etc.  
**Solution:** Defer to post-MVP, use mock for dashboard  
**Time:** No time lost (deferred)

---

## 📊 DECISION MATRIX

| Aspect | Mock Data | Real Integration | Hybrid | Chosen |
|--------|-----------|------------------|--------|--------|
| Time to Ship | 30 min | 3+ hours | 45 min | Hybrid ✅ |
| Dashboard Works | ✅ Yes | ✅ Yes | ✅ Yes | All good |
| Future-Ready | ⚠️ No | ✅ Yes | ✅ Yes | Hybrid ✅ |
| ADHD-Friendly | ✅ Can design | ✅ Built-in | ✅ Both | Hybrid ✅ |
| Complexity | Low | High | Medium | Hybrid ✅ |

**🧘 Zen Choice:** Hybrid approach  
**Rationale:**
- Ship working dashboard today (mock)
- Structure honors Serena's design (schema)
- Path to real integration clear (aggregator)
- No wasted work (mock validates API)

---

## 🌊 IMPLEMENTATION FLOW

```
┌─────────────────────────────────────────────────┐
│ Step 1: Create http_server.py                   │
│ Time: 10 min                                     │
│ Output: Server running on :8003                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Step 2: Add mock metrics (Serena schema)        │
│ Time: 15 min                                     │
│ Output: Endpoints return realistic data         │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Step 3: Prepare integration hooks               │
│ Time: 10 min                                     │
│ Output: MetricsAggregator ready                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Step 4: Dashboard integration                   │
│ Time: 10 min                                     │
│ Output: Dashboard shows Serena panel            │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Step 5: Test & document                         │
│ Time: 5 min                                      │
│ Output: Working, documented, shippable          │
└─────────────────────────────────────────────────┘

Total: 50 minutes
```

---

## 💡 ZEN INSIGHTS

### Insight 1: Serena is ADHD-First
Every design decision in Serena's code shows ADHD awareness:
- Progressive disclosure (don't overwhelm)
- Max items limits (reduce cognitive load)
- Visual indicators (quick scanning)
- Gentle suggestions (not commands)

**Implication:** Our HTTP wrapper should preserve this philosophy

### Insight 2: Metrics Are Aggregations
Serena doesn't store metrics - it calculates them from detection results:
- `aggregate_detections(results)` is the entry point
- Results come from various detectors (git, pattern, etc.)
- Each detector runs independently

**Implication:** MVP can't easily get "real" data without running detectors

### Insight 3: Mock Data is Acceptable
ConPort HTTP wrapper uses mock data successfully:
- Dashboard works perfectly
- Users see value immediately
- Real integration deferred

**Implication:** Same approach works for Serena

### Insight 4: Dashboard Doesn't Need Everything
Dashboard just needs:
- A few key metrics (total, pass rate, confidence)
- Top 3-5 patterns
- Basic health check

**Implication:** Simple API is sufficient

---

## 🎨 MOCK DATA DESIGN PHILOSOPHY

### Principle 1: Honor Serena's Schema
```python
# Use Serena's actual data structure
f1_f4_metrics = {
    "total_detections": 42,
    "passed": 28,
    "pass_rate": 0.67,  # Realistic ratio
    "avg_confidence": 0.75,
    "session_distribution": {"1": 10, "2": 15, "3+": 17}
}
```

### Principle 2: Realistic Values
- Detection counts: 20-50 (typical workday)
- Pass rate: 60-70% (some fail threshold)
- Confidence: 0.65-0.85 (reasonable range)
- Patterns: 3-5 top patterns (ADHD limit)

### Principle 3: ADHD-Friendly Formatting
```python
{
    "adhd_friendly": {
        "top_insight": "Most work in feature branches",
        "suggestion": "Consider committing exploratory work",
        "visual_indicator": "🟢",  # Green = good
        "cognitive_load": "low"  # Explicit
    }
}
```

### Principle 4: Progressive Disclosure Ready
```python
{
    "summary": {...},          # Level 1: Quick glance
    "breakdown": {...},        # Level 2: More detail
    "trends": {...}            # Level 3: Historical
}
```

---

## 📝 MOCK DATA SPECIFICATION

### /api/metrics Response
```json
{
  "detections": {
    "total": 42,
    "passed": 28,
    "pass_rate": 0.67,
    "confidence_avg": 0.75,
    "visual": "🟢 Healthy detection rate"
  },
  "patterns": [
    {
      "name": "feature_branch_work",
      "frequency": 12,
      "confidence": 0.82,
      "insight": "Most active pattern",
      "visual": "🔵"
    },
    {
      "name": "quick_fix_iteration",
      "frequency": 8,
      "confidence": 0.74,
      "visual": "🟢"
    },
    {
      "name": "exploratory_coding",
      "frequency": 7,
      "confidence": 0.69,
      "visual": "🟡"
    }
  ],
  "performance": {
    "latency_ms": 45,
    "cache_hit_rate": 0.85,
    "status": "optimal"
  },
  "adhd_insight": {
    "summary": "Strong pattern detection across 42 code sessions",
    "suggestion": "Current confidence levels are healthy (75% avg)",
    "cognitive_load": "low"
  },
  "source": "mock",
  "timestamp": "2025-10-29T07:27:37Z"
}
```

### /api/detections/summary Response
```json
{
  "total": 42,
  "passed_threshold": 28,
  "top_patterns": [
    {"pattern": "feature_branch", "count": 12, "avg_confidence": 0.82},
    {"pattern": "quick_fix", "count": 8, "avg_confidence": 0.74},
    {"pattern": "exploratory", "count": 7, "avg_confidence": 0.69}
  ],
  "session_distribution": {
    "single": 10,
    "double": 15,
    "triple_plus": 17,
    "insight": "Most work spans multiple sessions (healthy for ADHD)"
  },
  "abandonment": {
    "count": 5,
    "severity": "low",
    "suggestion": "5 items might need attention (12% of total)"
  },
  "source": "mock",
  "timestamp": "2025-10-29T07:27:37Z"
}
```

---

## ✅ IMPLEMENTATION CHECKLIST

### Phase 1: Server Setup
- [ ] Create `services/serena/v2/http_server.py`
- [ ] Add FastAPI imports
- [ ] Create app instance
- [ ] Add CORS middleware
- [ ] Add basic health endpoint
- [ ] Test server starts on :8003

### Phase 2: Mock Endpoints
- [ ] Design mock data structure
- [ ] Implement `/api/metrics` with mock
- [ ] Implement `/api/detections/summary` with mock
- [ ] Add ADHD-friendly formatting
- [ ] Include "source": "mock" field
- [ ] Test all endpoints respond

### Phase 3: Integration Hooks
- [ ] Import MetricsAggregator (try/except)
- [ ] Add startup handler
- [ ] Add fallback logic (try real → use mock)
- [ ] Add logger warnings
- [ ] Document TODO items

### Phase 4: Dashboard Integration
- [ ] Update dashboard ENDPOINTS
- [ ] Update get_patterns() method
- [ ] Test dashboard connection
- [ ] Verify graceful fallback
- [ ] Test full dashboard

### Phase 5: Documentation
- [ ] Document endpoints
- [ ] Document mock data
- [ ] Document integration path
- [ ] Create completion summary
- [ ] Update progress tracker

---

## 🚀 EXECUTION READINESS

**Planning Status:** ✅ COMPLETE  
**Understanding:** ✅ DEEP  
**Approach:** ✅ CLEAR  
**Philosophy:** ✅ ALIGNED  
**Estimated Time:** 50 minutes  
**Confidence:** HIGH  

**🧘 Zen State:** Achieved  
**Ready to Code:** YES  

---

**Next Action:** Begin implementation Phase 1 (Server Setup)

🎯 **Let's build with intention and clarity.**
