# Tmux Dashboard Metrics - Exhaustive Inventory

**Complete data sources and metrics available for Dopemux tmux monitoring dashboards**

Generated: 2025-10-28

---

## 🎯 CORE SERVICES & METRICS

### 1. ConPort Knowledge Graph (PostgreSQL + AGE)

**Data Available:**
- Decisions logged (count, types, confidence scores)
- Context queries (semantic, cross-plane, unified)
- Graph nodes/edges (tasks, decisions, files, relationships)
- Workspace contexts (active, historical)
- Session continuity metrics
- Query performance (latency, cache hits)
- Full-text search stats
- User workspaces & permissions (multi-user)
- Audit logs (security events)

**Actionable Metrics:**
- Decisions per session/day/week
- Context retrieval latency (<200ms target)
- Graph size (nodes, edges)
- Active workspace count
- Query types distribution

**API Endpoints:**
- `http://localhost:8005/api/adhd/decisions/recent`
- `http://localhost:8005/api/adhd/graph/stats`
- `http://localhost:8005/api/adhd/context/active`

---

### 2. ADHD Engine (Cognitive State)

**Data Available:**
- Energy levels (hyperfocus, high, medium, low, depleted)
- Attention states (hyperfocused, focused, transitioning, scattered, overwhelmed)
- Cognitive load score (0.0-1.0)
- Break timing & adherence
- Accommodation recommendations
- Context switch count & recovery time
- Session duration tracking
- Activity patterns (from ActivityTracker)
- Feature flags status

**Actionable Metrics:**
- Current energy level gauge
- Current attention state
- Cognitive load (with thresholds: <0.3 low, 0.6-0.7 optimal, >0.85 critical)
- Time since last break
- Breaks suggested vs taken
- Context switches per hour/day
- Average focus session duration
- Energy optimization events

**API Endpoints:**
- `http://localhost:8001/api/v1/state`
- `http://localhost:8001/api/v1/accommodations`
- `http://localhost:8001/api/v1/breaks`

**Redis Keys:**
- `adhd:state:{user_id}`
- `adhd:energy:{user_id}`
- `adhd:attention:{user_id}`
- `adhd:breaks:{user_id}`

---

### 3. Serena V2 (Untracked Work Detection)

**Data Available:**
- F1-F4: Detection confidence scores, pass rates
- F5: Pattern learning (boost rates, top patterns)
- F6: Abandonment tracking (idle days, severity)
- F7: Metrics dashboard aggregations
- Session intelligence queries
- LSP/AST complexity analysis
- Git status parsing
- Performance monitoring (operation latency)
- Navigation cache stats
- Redis optimization metrics

**Actionable Metrics:**
- Total detections (passed threshold)
- Average confidence score
- Pattern boost rate
- Abandoned work count by severity
- Session distribution (1, 2, 3+)
- Top 5 matching patterns
- LSP health status
- Cache hit/miss ratio

**API Endpoints:**
- `http://localhost:8003/api/metrics`
- `http://localhost:8003/api/detections/summary`
- `http://localhost:8003/api/patterns/top`

---

### 4. Task Orchestrator (Flow & Intelligence)

**Data Available:**
- Flow state detection (in flow yes/no)
- Flow session duration
- Task velocity (tasks/day, complexity-adjusted)
- Task completion rate (completed vs started)
- Cognitive load balancer metrics
- Batch processing stats
- Predictive orchestration insights
- Dependency monitoring
- Multi-team coordination

**Actionable Metrics:**
- Currently in flow? (boolean + duration)
- Task completion rate (target: 85%)
- Tasks completed today
- Complexity-adjusted velocity
- Flow sessions count (short/medium/long)
- Cognitive load trends

**Prometheus Metrics:**
- `adhd_task_completion_rate`
- `adhd_task_velocity_per_day`
- `adhd_current_flow_state`
- `adhd_flow_duration_seconds`

---

### 5. Break Suggester (F-NEW-8)

**Data Available:**
- Break suggestions by priority (low, medium, high, critical)
- Cognitive load window (25-min sliding)
- Complexity event correlation
- Session start time
- Last break timestamp
- Break adherence tracking

**Actionable Metrics:**
- Time until next suggested break
- Break priority level
- Breaks suggested vs ignored vs snoozed
- Time in current session
- High complexity events in last 25min

**Prometheus Metrics:**
- `adhd_break_suggestions_total{priority}`
- `fnew8_break_adherence_total{action}`

---

### 6. MCP Servers

**MCP Integration Bridge:**
- Tool call counts by server/tool
- Tool execution duration
- Tool errors by type
- Event bus metrics (published, consumed, lag)
- Circuit breaker status
- Rate limiter stats
- Cache performance

**Individual MCP Servers:**
- **Sequential Thinking**: Reasoning steps, depth
- **Context7**: Context queries, embeddings
- **Exa**: Web search calls, results
- **Zen**: Session state, thinkdeep analysis
- **Serena MCP**: Code analysis, complexity
- **Leantime Bridge**: Project sync, tasks imported

**Prometheus Metrics:**
- `dopemux_mcp_tool_calls_total{server,tool}`
- `dopemux_mcp_tool_duration_seconds{server,tool}`
- `dopemux_mcp_tool_errors_total{server,tool,error_type}`

---

### 7. Workspace Watcher

**Data Available:**
- File activity tracking
- Application detection (active editor)
- Workspace mapping
- Real-time file changes

**Actionable Metrics:**
- Files changed in last hour
- Active application
- Workspace activity level

---

### 8. Redis (State & Caching)

**Data Available:**
- Cache operations (hit/miss/set/invalidate)
- Cache latency
- Redis connection pool stats
- Event streams (ADHD events, integration events)
- Session state persistence

**Actionable Metrics:**
- Cache hit rate
- Cache size/memory
- Event stream lag
- Redis connection count

**Prometheus Metrics:**
- `dopemux_cache_operations_total{cache_type,operation}`
- `dopemux_cache_latency_seconds{cache_type,operation}`

---

### 9. Qdrant (Vector Search)

**Data Available:**
- Embeddings stored
- Semantic search queries
- Collection sizes
- Search latency

**Actionable Metrics:**
- Total embeddings
- Search queries per hour
- Average search latency

---

### 10. Prometheus (System Metrics)

**ADHD-Specific Metrics:**
- `adhd_search_latency{search_type}` - semantic, unified, code, docs
- `adhd_complexity_calculations_total{feature}` - F-NEW-3, AST, LSP, unified
- `adhd_break_suggestions_total{priority}` - low, medium, high, critical
- `adhd_task_completions_total{outcome}` - completed, abandoned, switched
- `adhd_cognitive_state{user_id,metric}` - energy, attention, cognitive_load

**Feature-Specific:**
- `dopemux_fnew6_session_intelligence_total{user_id}`
- `dopemux_fnew8_break_adherence_total{action}`

**System Metrics:**
- `dopemux_http_requests_total{service,endpoint,method,status}`
- `dopemux_db_query_duration_seconds{operation,table}`
- `dopemux_db_connections{pool}`
- `dopemux_eventbus_events_published_total{event_type,source}`
- `dopemux_eventbus_consumer_lag{consumer_group}`

---

## 🔥 PRIORITY TIERS FOR DASHBOARD

### TIER 1: Always Visible (HUD)
**Critical real-time state - must be visible at all times**

1. **Current energy level** (⚡ icon + state)
2. **Current attention state** (👁️ icon + state)
3. **Cognitive load** (0.0-1.0 gauge with color)
4. **Time in session** (auto-updating)
5. **Break warning** (☕ icon if needed)
6. **Flow state** (🌊 if active)
7. **ConPort connection** (📊 connected / 📴 disconnected)
8. **Token usage** (raw + percentage + model)

### TIER 2: High Value (Toggle View)
**Important context - show in expanded view**

9. **Tasks completed today** (with completion rate %)
10. **Decisions logged** (count with trend)
11. **Context switches** (count with rate)
12. **Pattern boosts** (active patterns count)
13. **Abandoned work** (by severity: stale/likely/definitely)
14. **MCP tool calls** (total + by server)
15. **Cache hit rate** (percentage)

### TIER 3: Deep Metrics (Detailed Panel)
**Diagnostic data - for troubleshooting and optimization**

16. **Session intelligence**: Focus duration history
17. **Complexity trends**: Avg complexity over time
18. **Break adherence**: Suggested vs taken ratio
19. **Error rates**: By service
20. **Performance**: P95 latencies by operation
21. **Event bus**: Consumer lag, throughput
22. **Database**: Query performance, connection pool
23. **Workspace**: File activity heatmap

---

## 📊 SAMPLE DASHBOARD LAYOUTS

### Compact Mode (3 lines)
```
Session: 2h 15m | ⚡= 👁️● Cognitive:0.65 | Flow:✓ Break:☕ 15m
Tasks: 8/10 (80%) | Decisions:23 | Switches:4 | 128K/200K (64%) Sonnet
ConPort:📊 MCP:45 calls | Redis:94% hit | Errors:0
```

### Standard Mode (5-7 lines)
```
Session: 2h 15m | ⚡= 👁️● Cognitive:0.65 | Flow:✓ Break:☕ 15m
Tasks: 8/10 (80%) | Decisions:23 | Switches:4 | 128K/200K (64%) Sonnet
ConPort:📊 MCP:45 calls | Redis:94% hit | Errors:0
Patterns: +12 boosts | Abandoned: 3 stale, 1 likely
F-NEW-8: Last break 45m ago (next in 15m)
Services: ConPort 15ms, ADHD 8ms, Serena 120ms
```

### Full Mode (Dedicated tmux pane)
- Real-time graphs (sparklines)
- Historical trends
- Service health matrix
- Top N lists (patterns, errors, slow queries)

---

## 🎨 VISUALIZATION OPTIONS

### Text-Based Graphs
1. **Sparklines** (trending over time)
   - Cognitive load: `▁▂▃▅▆▇█▇▆▅`
   - Task velocity: `▃▄▅▅▆▇▆▅▄`
   - Context switches: `▂▁▂▃▅▃▂▁`

2. **Gauges** (current value with scale)
   ```
   Cognitive: [||||····] 65%
   Token:     [███████·] 80%
   Energy:    [███·····] 40%
   ```

3. **Progress bars**
   ```
   Session: [====>   ] 2h 15m / 4h
   Break:   [=>      ] 5m / 25m
   ```

### Color Coding (tmux status colors)
- 🟢 **Green**: Optimal states, healthy metrics
- 🟡 **Yellow**: Warnings, approaching thresholds
- 🔴 **Red**: Critical, immediate action needed
- 🔵 **Blue**: Info, neutral state
- ⚪ **Gray**: Disabled, inactive

### Icons/Emojis (quick scanning)
- ⚡ Energy levels
- 👁️ Attention states
- 🧠 Cognitive load
- ☕ Break reminders
- 🌊 Flow state
- 🛡️ Protection active
- 📊 Connected
- 📴 Offline/Disconnected
- 🎯 Tasks/Focus
- 🔄 Context switches
- 📈 Trending up
- 📉 Trending down

---

## 🔌 DATA ACCESS METHODS

### REST APIs
```bash
# ADHD Engine
curl http://localhost:8001/api/v1/state

# ConPort KG
curl http://localhost:8005/api/adhd/decisions/recent

# Serena
curl http://localhost:8003/api/metrics

# Prometheus
curl 'http://localhost:9090/api/v1/query?query=adhd_cognitive_state'
```

### Direct Database Access
```bash
# PostgreSQL (ConPort)
psql -h localhost -U postgres -d dopemux -c "SELECT * FROM decisions LIMIT 10"

# Redis (ADHD state)
redis-cli GET adhd:state:default

# Qdrant (Vector stats)
curl http://localhost:6333/collections
```

### Event Streams (Redis Streams)
```bash
# Subscribe to ADHD events
redis-cli XREAD BLOCK 0 STREAMS adhd:events 0

# Subscribe to integration events
redis-cli XREAD BLOCK 0 STREAMS integration:events 0
```

### MCP Tools (via proxy)
```bash
# Query MCP server health
mcp__serena__health_check

# Get ConPort stats
mcp__conport__get_stats
```

---

## 🚀 IMPLEMENTATION NOTES

### Performance Considerations
- **Cache aggressively**: Most metrics should be cached (5-30s TTL)
- **Batch queries**: Combine multiple metrics in single API call
- **Use Redis**: For real-time state (ADHD, sessions)
- **Prometheus for trends**: Historical data, aggregations
- **Async updates**: Don't block tmux rendering

### ADHD-Friendly Design
- **Progressive disclosure**: Show critical → detailed
- **Visual hierarchy**: Icons, colors, alignment
- **No cognitive overload**: Max 5-7 items per view
- **Actionable alerts**: "Take a break NOW" not "high load"
- **Celebrate wins**: Green ✓ for completed tasks

### Update Frequencies
- **Real-time** (1s): Energy, attention, cognitive load, flow state
- **Fast** (5s): Break timer, session time, token usage
- **Medium** (30s): Tasks, decisions, context switches, cache stats
- **Slow** (60s+): Patterns, trends, service health, database stats

---

## 📚 REFERENCES

### Existing Components
- `/services/task-orchestrator/observability/metrics_collector.py`
- `/services/task-orchestrator/observability/adhd_dashboard.py`
- `/services/monitoring/prometheus_metrics.py`
- `/src/dopemux/mcp/observability.py`
- `/services/serena/v2/metrics_dashboard.py`

### Configuration Files
- `/docker-compose.staging.yml` - Service endpoints
- `/services/task-orchestrator/observability/prometheus.yml`
- `/services/monitoring/alerting_rules.yml`

### Documentation
- `/docs/COMPONENT_6_ADHD_INTELLIGENCE.md`
- `/docs/F-NEW-7_COMPLETE_IMPLEMENTATION.md`
- `/docs/F-NEW-8_INTEGRATION_PLAN.md`
- `/MONITORING-DESIGN-SPRINT-SUMMARY.md`

---

**Next Steps:**
1. Research best tmux dashboard frameworks
2. Design optimal layout for maximum density + readability
3. Implement data collection scripts
4. Build tmux status bar + pane integrations
5. Add interactivity (keyboard shortcuts for views)
