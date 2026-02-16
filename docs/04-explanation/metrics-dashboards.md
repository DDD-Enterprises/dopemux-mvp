---
id: metrics-dashboards-for-tmux
title: Metrics Dashboards For Tmux
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Metrics Dashboards For Tmux (explanation) for dopemux documentation and developer
  workflows.
---
# Metrics & Dashboards for tmux - Dopemux Ultra UI

Comprehensive guide to available metrics, APIs, and data sources for designing tmux dashboards with real-time Dopemux Ultra UI data.

## 📊 Available Metrics Overview

The Dopemux Ultra UI provides multiple data sources for tmux dashboard integration:

### 🧠 ADHD Engine Core Metrics (Port 8080)
**Base URL**: `http://localhost:8080/api/v1/`

| Metric | Endpoint | Update Frequency | Data Type | Use Case |
|--------|----------|------------------|-----------|----------|
| **Attention State** | `/attention-state` \| 60s \| `{"state": "focused", "confidence": 0.85, "distraction_risk": "LOW"}` | Show current focus level |
| **Energy Level** | `/energy-level` \| 60s \| `{"current_level": 0.72, "trend": "increasing"}` | Display energy status |
| **Cognitive Load** | `/cognitive-load` \| 30s \| `{"current_load": 0.45, "capacity_remaining": 0.55}` | Monitor mental workload |
| **Break Recommendation** | `/break-recommendation` \| 60s \| `{"should_break": false, "next_break_in": "15min"}` | Show break timer |
| **Task Assessment** | `/assess-task` \| On-demand \| `{"complexity_score": 0.73, "estimated_duration": "90min"}` | Task planning data |
| **User Profile** | `/user-profile` \| Static \| `{"attention_span": 25, "energy_patterns": {...}}` | User preferences |

### 🧠 ADHD Dashboard Metrics (Port 8097)
**Base URL**: `http://localhost:8097/api/`

| Metric | Endpoint | Update Frequency | Data Type | Use Case |
|--------|----------|------------------|-----------|----------|
| **Current Metrics** | `/metrics` \| 30s \| `{"attention": 0.85, "energy": 0.72, "load": 0.45}` | Real-time status |
| **ADHD State** | `/adhd-state` \| 30s \| `{"state": "focused", "trends": [...], "alerts": []}` | State overview |
| **Session Data** | `/sessions/today` \| 5min \| `{"total_sessions": 4, "avg_duration": "45min"}` | Session stats |
| **Analytics Trends** | `/analytics/trends` \| 15min \| `{"energy_trend": "stable", "attention_trend": "improving"}` | Historical trends |

### 🔍 Dope-Context Search Metrics (MCP Server)
**Available via MCP**: `mcp__dope-context__get_search_metrics()`

| Metric | Data Type | Update Frequency | Use Case |
|--------|-----------|------------------|----------|
| **Search Counts** | `{"total_searches": 1247, "explicit_searches": 892}` | 5min | Usage analytics |
| **Scenario Breakdown** | `{"understanding_code": 0.45, "debugging": 0.23}` | 5min | Search patterns |
| **Tool Usage** | `{"search_code": 0.67, "docs_search": 0.22}` | 5min | Tool effectiveness |
| **Performance** | `{"avg_response_time": 1.2, "cache_hit_rate": 0.787}` | 1min | System health |

### 🛡️ Health Monitoring Metrics
**Available via CLI**: `python -m src.dopemux.cli doctor`

| Metric | Data Type | Update Frequency | Use Case |
|--------|-----------|------------------|----------|
| **Service Health** | `{"status": "healthy", "uptime": "2h45m"}` | 30s | System status |
| **Resource Usage** | `{"cpu_percent": 45.2, "memory_percent": 67.8}` | 10s | Performance monitoring |
| **Error Rates** | `{"total_errors": 12, "error_rate_per_minute": 0.3}` | 1min | Reliability tracking |

## 🎨 tmux Dashboard Design Patterns

### 1. ADHD Status Bar (Top Bar)
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🧠 ADHD: focused(85%) ⚡ Energy: high(72%) 🧮 Load: 45% ⏰ Break: 22min │ 15:30 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Data Sources**:
- Attention State: `GET /api/v1/attention-state`
- Energy Level: `GET /api/v1/energy-level`
- Cognitive Load: `GET /api/v1/cognitive-load`
- Break Timer: `GET /api/v1/break-recommendation`

**Update Frequency**: Every 30 seconds

**tmux Configuration**:
```bash
# In ~/.tmux.conf
set -g status-interval 30
set -g status-right "#(curl -s http://localhost:8080/api/v1/attention-state | jq -r '.state') (#(curl -s http://localhost:8080/api/v1/energy-level | jq -r '.current_level * 100 | floor')%)"
```

### 2. Service Health Panel (Left Sidebar)
```
┌─ Services ──────┐
│ 🟢 ADHD Engine  │
│ 🟢 Dashboard    │
│ 🟢 Redis        │
│ 🟢 Dope-Context │
│ ⚠️  CPU: 45%    │
│ ⚠️  Mem: 68%    │
└─────────────────┘
```

**Data Sources**:
- Health Status: Individual `/health` endpoints
- Resource Usage: `docker stats` or system monitoring

**Update Frequency**: Every 60 seconds

### 3. Session Analytics Panel (Right Sidebar)
```
┌─ Today's Progress ──┐
│ Sessions: 4/6       │
│ Avg Duration: 42min │
│ Energy Trend: ↗️    │
│ Tasks Completed: 12 │
│ Break Compliance: 85%│
└─────────────────────┘
```

**Data Sources**:
- Session Data: `GET /api/sessions/today`
- Analytics: `GET /api/analytics/trends`
- Progress: ConPort task tracking

### 4. Real-time Metrics Dashboard (Main Panel)
```
┌─ ADHD Metrics ──────────────────────┬─ Search Analytics ──┐
│ Attention: ████████░ 85%            │ Searches: 1,247     │
│ Energy:    ███████░░░ 72%           │ Today: 89           │
│ Load:      ████░░░░░░ 45%           │ Code: 67%           │
│                                     │ Docs: 22%           │
├─ Recent Tasks ──────────────────────┼─ System Health ─────┤
│ 🔄 Task assessment (complexity: 0.73) │ CPU: 45%          │
│ ✅ Break taken (5min)               │ Mem: 68%          │
│ ⚠️  Energy dropping                  │ Disk: 23%          │
└─────────────────────────────────────┴─────────────────────┘
```

## 🔧 tmux Integration Techniques

### 1. Status Bar Integration
```bash
# ~/.tmux.conf
set -g status-interval 30

# ADHD Status
ADHD_STATUS="#(curl -s http://localhost:8080/api/v1/attention-state | jq -r '.state')"
ENERGY_LEVEL="#(curl -s http://localhost:8080/api/v1/energy-level | jq -r '.current_level * 100 | floor')"
BREAK_TIME="#(curl -s http://localhost:8080/api/v1/break-recommendation | jq -r '.next_break_in')"

set -g status-left "#[fg=green]🧠 ${ADHD_STATUS} #[fg=yellow]⚡${ENERGY_LEVEL}% #[fg=blue]⏰${BREAK_TIME}"
```

### 2. Pane Content Updates
```bash
# Update pane with latest metrics
tmux send-keys -t dashboard:0.0 "curl -s http://localhost:8097/api/metrics | jq .attention" Enter
tmux send-keys -t dashboard:0.0 "curl -s http://localhost:8080/api/v1/cognitive-load | jq .current_load" Enter
```

### 3. Window Naming with Status
```bash
# Dynamic window naming
ATTENTION_STATE=$(curl -s http://localhost:8080/api/v1/attention-state | jq -r .state)
tmux rename-window "ADHD-${ATTENTION_STATE}"
```

### 4. Alert Integration
```bash
# Check for break recommendations
BREAK_NEEDED=$(curl -s http://localhost:8080/api/v1/break-recommendation | jq -r .should_break)
if [ "$BREAK_NEEDED" = "true" ]; then
    tmux display-message "🔔 Time for a break!"
fi
```

## 📈 Real-Time Data Sources

### Polling-Based Updates
```bash
#!/bin/bash
# update_adhd_metrics.sh

while true; do
    # Fetch latest metrics
    ATTENTION=$(curl -s http://localhost:8080/api/v1/attention-state | jq -r .confidence)
    ENERGY=$(curl -s http://localhost:8080/api/v1/energy-level | jq -r .current_level)
    LOAD=$(curl -s http://localhost:8080/api/v1/cognitive-load | jq -r .current_load)

    # Update tmux status
    tmux set -g status-right "🧠${ATTENTION} ⚡${ENERGY} 🧮${LOAD}"

    sleep 30
done
```

### WebSocket Integration (Future)
```javascript
// dashboard.js - Future WebSocket integration
const ws = new WebSocket('ws://localhost:8080/ws/metrics');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateTmuxStatus(data.attention, data.energy, data.load);
};
```

### Cron-Based Updates
```bash
# /etc/cron.d/dopemux-dashboard
*/1 * * * * root /usr/local/bin/update_adhd_dashboard.sh
```

## 🎨 Visualization Options

### Text-Based Charts
```
Attention Level: ████████░ 85%
Energy Level:   ███████░░░ 72%
Cognitive Load: ████░░░░░░ 45%

Energy Trend (Last 24h):
20:00 ▄█▆▅▃▂▁▂▃▅▆█▄ 08:00
      │         │
      └─Low     └─High
```

### Color-Coded Status
```bash
# Color mapping for tmux
if [ "$ATTENTION" -gt 80 ]; then
    COLOR="#[fg=green]"
elif [ "$ATTENTION" -gt 60 ]; then
    COLOR="#[fg=yellow]"
else
    COLOR="#[fg=red]"
fi

tmux set -g status-left "${COLOR}🧠 ${ATTENTION}%"
```

### Progress Bars
```bash
# ASCII progress bars
draw_progress_bar() {
    local percent=$1
    local width=20
    local filled=$((percent * width / 100))
    local empty=$((width - filled))

    printf "["
    printf "█%.0s" $(seq 1 $filled)
    printf "░%.0s" $(seq 1 $empty)
    printf "] %d%%\n" $percent
}

# Usage
ATTENTION=$(curl -s http://localhost:8080/api/v1/attention-state | jq -r '.confidence * 100 | floor')
draw_progress_bar $ATTENTION
```

## 🔄 Data Flow Architecture

### Metric Collection Pipeline
```
Sensors → ADHD Engine → Redis Cache → Dashboard API → tmux Scripts → Display
    ↑         ↑            ↑            ↑            ↑            ↑
  Monitors  Processing   Caching      REST API    Polling     Rendering
```

### Update Frequencies
- **Real-time**: Attention state, cognitive load (30-60s)
- **Near real-time**: Energy levels, break recommendations (60s)
- **Periodic**: Session analytics, trends (5-15min)
- **On-demand**: Task assessments, detailed reports

### Data Persistence
- **Short-term**: Redis cache (current session data)
- **Medium-term**: ConPort knowledge graph (session history)
- **Long-term**: PostgreSQL (analytics, trends)

## 📋 Dashboard Configuration Examples

### Minimal Status Bar
```bash
# ~/.tmux.conf
set -g status-interval 60
set -g status-right "#[fg=green]🧠#(curl -s http://localhost:8080/api/v1/attention-state | jq -r .state)#[fg=yellow] ⚡#(curl -s http://localhost:8080/api/v1/energy-level | jq -r '.current_level * 100 | floor')%#[fg=blue] ⏰#(curl -s http://localhost:8080/api/v1/break-recommendation | jq -r .next_break_in)"
```

### Full Dashboard Layout
```bash
# Create dashboard session
tmux new-session -d -s dashboard

# ADHD Metrics pane (main)
tmux send-keys -t dashboard "watch -n 30 'curl -s http://localhost:8097/api/metrics | jq'" Enter

# System health pane (bottom)
tmux split-window -v -t dashboard
tmux send-keys -t dashboard "python -m src.dopemux.cli doctor" Enter

# Search analytics pane (right)
tmux split-window -h -t dashboard
tmux send-keys -t dashboard "watch -n 300 'curl -s http://localhost:8001/search_metrics | jq .total_searches'" Enter

# Layout
tmux select-layout -t dashboard main-vertical
```

### Alert System Integration
```bash
#!/bin/bash
# alert_system.sh

while true; do
    # Check for break recommendations
    BREAK=$(curl -s http://localhost:8080/api/v1/break-recommendation | jq -r .should_break)

    if [ "$BREAK" = "true" ]; then
        tmux display-message -d 5000 "🔔 Time for a break! Your brain needs rest."
        # Optional: Play sound
        # afplay /System/Library/Sounds/Ping.aiff
    fi

    # Check energy levels
    ENERGY=$(curl -s http://localhost:8080/api/v1/energy-level | jq -r '.current_level * 100 | floor')

    if [ "$ENERGY" -lt 30 ]; then
        tmux display-message -d 3000 "⚠️  Low energy detected. Consider taking a break."
    fi

    sleep 300  # Check every 5 minutes
done
```

## 🔧 Custom Dashboard Scripts

### ADHD Status Script
```bash
#!/bin/bash
# adhd_status.sh

# Colors for tmux
GREEN="#[fg=green]"
YELLOW="#[fg=yellow]"
RED="#[fg=red]"
BLUE="#[fg=blue]"
RESET="#[fg=default]"

# Fetch data
ATTENTION_STATE=$(curl -s http://localhost:8080/api/v1/attention-state | jq -r .state)
ATTENTION_CONFIDENCE=$(curl -s http://localhost:8080/api/v1/attention-state | jq -r '.confidence * 100 | floor')
ENERGY_LEVEL=$(curl -s http://localhost:8080/api/v1/energy-level | jq -r '.current_level * 100 | floor')
COGNITIVE_LOAD=$(curl -s http://localhost:8080/api/v1/cognitive-load | jq -r '.current_load * 100 | floor')
BREAK_TIME=$(curl -s http://localhost:8080/api/v1/break-recommendation | jq -r .next_break_in)

# Color coding
if [ "$ATTENTION_CONFIDENCE" -gt 80 ]; then
    ATTENTION_COLOR=$GREEN
elif [ "$ATTENTION_CONFIDENCE" -gt 60 ]; then
    ATTENTION_COLOR=$YELLOW
else
    ATTENTION_COLOR=$RED
fi

if [ "$ENERGY_LEVEL" -gt 70 ]; then
    ENERGY_COLOR=$GREEN
elif [ "$ENERGY_LEVEL" -gt 40 ]; then
    ENERGY_COLOR=$YELLOW
else
    ENERGY_COLOR=$RED
fi

if [ "$COGNITIVE_LOAD" -lt 50 ]; then
    LOAD_COLOR=$GREEN
elif [ "$COGNITIVE_LOAD" -lt 75 ]; then
    LOAD_COLOR=$YELLOW
else
    LOAD_COLOR=$RED
fi

# Output formatted status
echo "${ATTENTION_COLOR}🧠 ${ATTENTION_STATE}(${ATTENTION_CONFIDENCE}%)${RESET} ${ENERGY_COLOR}⚡${ENERGY_LEVEL}%${RESET} ${LOAD_COLOR}🧮${COGNITIVE_LOAD}%${RESET} ${BLUE}⏰${BREAK_TIME}${RESET}"
```

### Service Health Monitor
```bash
#!/bin/bash
# service_health.sh

SERVICES=(
    "ADHD Engine:http://localhost:8080/health"
    "ADHD Dashboard:http://localhost:8097/health"
    "Redis:redis://localhost:6379"
)

for service in "${SERVICES[@]}"; do
    NAME=$(echo $service | cut -d: -f1)
    URL=$(echo $service | cut -d: -f2-)

    if [[ $URL == redis://* ]]; then
        # Special handling for Redis
        if docker exec dopemux-redis-primary redis-cli ping &>/dev/null; then
            STATUS="🟢 UP"
        else
            STATUS="🔴 DOWN"
        fi
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
        if [ "$HTTP_CODE" = "200" ]; then
            STATUS="🟢 UP"
        else
            STATUS="🔴 DOWN ($HTTP_CODE)"
        fi
    fi

    printf "%-15s %s\n" "$NAME:" "$STATUS"
done
```

### Performance Dashboard
```bash
#!/bin/bash
# performance_dashboard.sh

echo "=== ADHD Performance Dashboard ==="
echo "Timestamp: $(date)"
echo

# ADHD Metrics
echo "🧠 ADHD Metrics:"
curl -s http://localhost:8097/api/metrics | jq -r '
    "  Attention: \(.attention * 100 | floor)%",
    "  Energy: \(.energy * 100 | floor)%",
    "  Load: \(.load * 100 | floor)%"
'
echo

# System Resources
echo "💻 System Resources:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemPerc}}" | grep dopemux
echo

# Search Performance
echo "🔍 Search Analytics:"
SEARCH_METRICS=$(curl -s http://localhost:8001/search_metrics 2>/dev/null || echo '{"total_searches": 0, "avg_response_time": 0}')
echo "$SEARCH_METRICS" | jq -r '
    "  Total Searches: \(.total_searches)",
    "  Avg Response: \(.avg_response_time // 0)s",
    "  Cache Hit Rate: \(if .cache_hit_rate then (.cache_hit_rate * 100 | floor) else 0 end)%"
'
echo

# Recent Errors
echo "🚨 Recent Errors (last 5 min):"
ERROR_COUNT=$(docker compose logs --since 5m 2>&1 | grep -i error | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "  Errors found: $ERROR_COUNT"
    docker compose logs --since 5m 2>&1 | grep -i error | tail -3
else
    echo "  ✅ No errors detected"
fi
```

## 🎯 Advanced tmux Dashboard Setup

### Multi-Pane Dashboard Session
```bash
#!/bin/bash
# create_adhd_dashboard.sh

# Create new tmux session
tmux new-session -d -s adhd-dashboard -n status

# Status pane (top)
tmux send-keys -t adhd-dashboard:status "./adhd_status.sh" Enter
tmux send-keys -t adhd-dashboard:status "watch -n 30 ./adhd_status.sh" Enter

# Split for services
tmux split-window -v -t adhd-dashboard:status
tmux send-keys -t adhd-dashboard:status.1 "watch -n 60 ./service_health.sh" Enter

# Split for performance
tmux split-window -h -t adhd-dashboard:status.1
tmux send-keys -t adhd-dashboard:status.2 "./performance_dashboard.sh" Enter
tmux send-keys -t adhd-dashboard:status.2 "watch -n 60 ./performance_dashboard.sh" Enter

# Set layout
tmux select-layout -t adhd-dashboard main-vertical

# Attach to session
tmux attach-session -t adhd-dashboard
```

### Integration with tmux Status Bar
```bash
# ~/.tmux.conf additions
set -g status-interval 30

# ADHD status in status bar
ADHD_SCRIPT="$HOME/scripts/adhd_status.sh"
if [ -f "$ADHD_SCRIPT" ]; then
    set -g status-right "#[fg=colour245]#(bash $ADHD_SCRIPT)"
fi

# Alert on break recommendations
BREAK_CHECK="$HOME/scripts/check_breaks.sh"
if [ -f "$BREAK_CHECK" ]; then
    set -g status-right "#[fg=colour245]#(bash $BREAK_CHECK) #(bash $ADHD_SCRIPT)"
fi
```

This comprehensive metrics and dashboard guide provides everything needed to build rich, real-time tmux dashboards that integrate with the Dopemux Ultra UI ADHD accommodation platform.
