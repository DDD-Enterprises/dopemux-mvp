# Monitoring & Tmux Comprehensive Audit & Remediation Plan

**Date**: 2025-11-13  
**Status**: 🔴 Critical Issues Identified  
**Priority**: HIGH

## 🎯 Executive Summary

Deep investigation reveals **significant architectural gaps** in both monitoring and tmux integration:

### Critical Findings

1. **Monitoring System**: Fragmented, incomplete, lacks multi-workspace/multi-instance support
2. **Tmux Integration**: Poorly designed, non-functional, lacks cohesion  
3. **Multi-Workspace Support**: Monitoring has **ZERO** workspace awareness
4. **Data Flow**: Broken integration between monitoring, tmux, and services

### Impact

- ❌ No real-time monitoring of multi-workspace operations
- ❌ Tmux dashboards show mock/stale data
- ❌ Cannot track metrics across workspace boundaries
- ❌ User experience is degraded and misleading

---

## 📊 Current State Analysis

### 1. Monitoring System Architecture

#### What Exists

```
services/
├── monitoring/
│   ├── prometheus_metrics.py  ✅ Good metric definitions
│   ├── prometheus.yml         ⚠️  Service endpoints hardcoded
│   ├── health_checks.py       ⚠️  Basic health checks only
│   └── alerting_rules.yml     ⚠️  Not integrated
│
shared/
└── monitoring.py              ✅ Comprehensive monitoring class
│
src/core/
└── monitoring.py              ⚠️  Simple metrics collector
│
services/orchestrator/src/
└── health_monitor.py          ✅ Process health monitoring
```

#### Problems Identified

1. **No Multi-Workspace Support**
   - Metrics lack `workspace_id` labels
   - Single Prometheus instance can't distinguish workspaces
   - No workspace-scoped retention policies

2. **No Multi-Instance Support**
   - Services hard-coded to single endpoints
   - No instance ID in metrics
   - Can't run multiple instances per workspace

3. **Fragmented Implementation**
   - 4 different monitoring modules (no cohesion)
   - Different patterns in each service
   - No shared monitoring base class

4. **Incomplete Integration**
   - Prometheus not running (no Docker container)
   - Services don't export metrics
   - Grafana absent
   - Alert manager not configured

5. **Data Accuracy Issues**
   - ADHD Engine metrics mock in many places
   - Dashboard shows simulated data
   - Health checks return hardcoded values

### 2. Tmux Integration Analysis

#### What Exists

```
.tmux.conf                      ⚠️  Basic keybindings, broken status bar
tmux-dopemux-orchestrator.yaml  ⚠️  8 panes with watch commands
scripts/pm-dashboard.sh         ⚠️  Mock data, no real integration
scripts/tmux_dopemux_dashboard.sh ⚠️  Incomplete
dopemux_dashboard.py            ✅ Rich Textual dashboard (not used in tmux)
```

#### Problems Identified

1. **Non-Functional Status Bar**
   ```bash
   # From .tmux.conf - BROKEN
   status-right: "#{run-shell:~/scripts/tmux-adhd-load.sh}"
   # Scripts don't exist! Returns empty or errors
   ```

2. **Clunky Dashboard Design**
   - 8 panes running `watch` commands (resource intensive)
   - No real-time updates (30s polling via `watch`)
   - Mock data in most panes
   - Visual inconsistency

3. **Poor Multi-Workspace Support**
   - No workspace context in tmux sessions
   - Can't switch between workspace views
   - Status bar doesn't show current workspace

4. **Broken Integration**
   - pm-dashboard.sh queries non-existent APIs
   - Status bar scripts missing
   - Keybindings reference broken commands

5. **Accessibility Issues**
   - Too much information at once (ADHD hostile)
   - No progressive disclosure
   - Hard to scan quickly
   - Colors not optimized

### 3. Multi-Workspace Integration

#### Current State

- ✅ Services support workspace awareness (Phase 1 complete)
- ❌ Monitoring doesn't track per-workspace metrics
- ❌ Tmux doesn't show workspace context
- ❌ No workspace-scoped health checks
- ❌ Cross-workspace metrics aggregation missing

---

## 🏗️ Architectural Solution

### Design Principles

1. **Label-Based Multi-Tenancy** (Prometheus best practice)
   - Every metric includes `workspace_id` label
   - Every metric includes `instance_id` label
   - Central Prometheus with label filtering

2. **Unified Monitoring Base**
   - Single monitoring base class
   - Consistent integration pattern
   - Shared metric registry

3. **Tmux Simplification**
   - Fewer, smarter panes
   - Real-time data feeds (not polling)
   - Clean, scannable interface
   - Workspace-aware status bar

4. **Progressive Disclosure** (ADHD-optimized)
   - Summary view by default
   - Drill-down on demand
   - Visual hierarchy
   - Minimal cognitive load

---

## 🔧 Implementation Plan

### Phase 1: Monitoring Foundation (Week 1)

#### 1.1 Unified Monitoring Base Class

**File**: `shared/monitoring/base.py`

```python
"""Unified monitoring base for all Dopemux services."""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import CollectorRegistry
from typing import Optional, Dict, Any
import os

class DopemuxMonitoring:
    """
    Unified monitoring for Dopemux services.
    
    Features:
    - Multi-workspace support via labels
    - Multi-instance support via instance_id
    - Consistent metric naming
    - Automatic service registration
    """
    
    def __init__(
        self,
        service_name: str,
        workspace_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        registry: Optional[CollectorRegistry] = None
    ):
        self.service_name = service_name
        self.workspace_id = workspace_id or os.getenv("WORKSPACE_ID", "default")
        self.instance_id = instance_id or os.getenv("INSTANCE_ID", "0")
        self.registry = registry or CollectorRegistry()
        
        # Core labels applied to ALL metrics
        self.core_labels = {
            "service": service_name,
            "workspace_id": self.workspace_id,
            "instance_id": self.instance_id
        }
        
        self._init_common_metrics()
    
    def _init_common_metrics(self):
        """Initialize metrics common to all services."""
        
        # Service info (metadata)
        self.info = Info(
            'dopemux_service_info',
            'Service metadata',
            registry=self.registry
        )
        self.info.info({
            **self.core_labels,
            'version': os.getenv('SERVICE_VERSION', 'unknown')
        })
        
        # Request metrics
        self.requests_total = Counter(
            'dopemux_requests_total',
            'Total requests processed',
            ['endpoint', 'method', 'status', **self.core_labels.keys()],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'dopemux_request_duration_seconds',
            'Request processing time',
            ['endpoint', **self.core_labels.keys()],
            buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
        
        # Health metrics
        self.health_status = Gauge(
            'dopemux_health_status',
            'Service health (1=healthy, 0=unhealthy)',
            [**self.core_labels.keys()],
            registry=self.registry
        )
        
        # Set initial health
        self.health_status.labels(**self.core_labels).set(1)
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        duration: float
    ):
        """Record request metrics with automatic labeling."""
        self.requests_total.labels(
            endpoint=endpoint,
            method=method,
            status=str(status),
            **self.core_labels
        ).inc()
        
        self.request_duration.labels(
            endpoint=endpoint,
            **self.core_labels
        ).observe(duration)
    
    def set_health(self, healthy: bool):
        """Update health status."""
        self.health_status.labels(**self.core_labels).set(1 if healthy else 0)
```

#### 1.2 Service Integration Pattern

**Pattern for all services**:

```python
# In each service's main.py or __init__.py

from shared.monitoring import DopemuxMonitoring
from prometheus_client import make_asgi_app

# Initialize monitoring
monitoring = DopemuxMonitoring(
    service_name="adhd-engine",  # Or "conport", "serena", etc.
    workspace_id=os.getenv("WORKSPACE_ID"),
    instance_id=os.getenv("INSTANCE_ID")
)

# Mount metrics endpoint (FastAPI example)
app.mount("/metrics", make_asgi_app(registry=monitoring.registry))

# Use in endpoints
@app.get("/api/v1/energy-level")
async def get_energy_level():
    start = time.time()
    
    try:
        # ... your logic
        result = {"energy_level": "high"}
        
        monitoring.record_request(
            endpoint="/api/v1/energy-level",
            method="GET",
            status=200,
            duration=time.time() - start
        )
        
        return result
    except Exception as e:
        monitoring.record_request(
            endpoint="/api/v1/energy-level",
            method="GET",
            status=500,
            duration=time.time() - start
        )
        raise
```

#### 1.3 Prometheus Configuration

**File**: `services/monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'production'
    cluster: 'dopemux'

# Alert manager (to be added)
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/alerting_rules.yml'

scrape_configs:
  # Self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # ADHD Engine (multi-instance capable)
  - job_name: 'adhd-engine'
    metrics_path: '/metrics'
    # DNS-based service discovery
    dns_sd_configs:
      - names: ['adhd-engine.dopemux.local']
        type: 'A'
        port: 8001
    # OR static configs for multiple instances
    static_configs:
      - targets:
        - 'adhd-engine-0:8001'
        - 'adhd-engine-1:8001'
        labels:
          service: 'adhd-engine'

  # ConPort (multi-workspace, multi-instance)
  - job_name: 'conport'
    metrics_path: '/metrics'
    static_configs:
      - targets:
        - 'conport-workspace1:3004'
        - 'conport-workspace2:3004'
        labels:
          service: 'conport'

  # Serena
  - job_name: 'serena'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['serena:3001']
        labels:
          service: 'serena'

  # Orchestrator
  - job_name: 'orchestrator'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['orchestrator:8000']
        labels:
          service: 'orchestrator'

  # Dopecon Bridge
  - job_name: 'dopecon-bridge'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['dopecon-bridge:8080']
        labels:
          service: 'dopecon-bridge'

  # Dope Context
  - job_name: 'dope-context'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['dope-context:8000']
        labels:
          service: 'dope-context'
```

#### 1.4 Docker Compose Integration

**File**: `docker-compose.monitoring.yml`

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: dopemux-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./services/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./services/monitoring/alerting_rules.yml:/etc/prometheus/alerting_rules.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    networks:
      - dopemux

  grafana:
    image: grafana/grafana:10.1.0
    container_name: dopemux-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=dopemux_admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./services/monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./services/monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - dopemux
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: dopemux-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./services/monitoring/alertmanager.yml:/etc/alertmanager/config.yml
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    networks:
      - dopemux

volumes:
  prometheus-data:
  grafana-data:
  alertmanager-data:

networks:
  dopemux:
    external: true
```

### Phase 2: Tmux Redesign (Week 2)

#### 2.1 New Tmux Architecture

**Simplified Pane Layout** (4 panes instead of 8):

```
┌──────────────────────────────────────────────────────┐
│  Pane 0: Workspace Overview (Main Focus)            │
│  ┌─ Dopemux: workspace-mvp ─────────────────────┐   │
│  │ Energy: ████████░░ 80%  Load: ██████░░░░ 60% │   │
│  │ Services: 8/8 ✓  Tasks: 12 active            │   │
│  │ Next: Implement monitoring base class         │   │
│  └───────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────┤
│  Pane 1: Service Health │ Pane 2: Active Logs       │
│  ✓ ADHD Engine  45ms    │ [INFO] Request processed  │
│  ✓ ConPort      12ms    │ [WARN] Cache miss         │
│  ✗ Serena       offline │ [INFO] Task completed     │
│  ✓ Orchestrator 8ms     │                           │
├─────────────────────────┴───────────────────────────┤
│  Pane 3: Interactive Shell / Context                │
│  $ dopemux status --workspace=mvp                   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### 2.2 Smart Status Bar

**File**: `.tmux.conf`

```bash
# Dopemux Status Bar - Multi-Workspace Aware
# Enhanced for ADHD optimization and real-time monitoring

# Core Settings
set -g status-interval 5  # 5s refresh (balance between real-time and performance)
set -g status-position bottom
set -g status-justify left

# Status Bar Style (Catppuccin Mocha - ADHD-friendly)
set -g status-style bg='#1e1e2e',fg='#cdd6f4'

# LEFT: Session + Workspace + Mode
set -g status-left-length 50
set -g status-left "\
#[fg=#89b4fa,bg=#1e1e2e,bold] #{session_name} \
#[fg=#f5c2e7,bg=#1e1e2e] #{?WORKSPACE_ID,󰳐 #{WORKSPACE_ID}, default} \
#[fg=#cdd6f4,bg=#1e1e2e] "

# RIGHT: ADHD Metrics + Services + Time
set -g status-right-length 150
set -g status-right "\
#[fg=#a6e3a1,bg=#1e1e2e] #{run-shell 'curl -sf http://localhost:8001/api/v1/energy-level/default_user | jq -r .energy_level // \"unknown\"'} \
#[fg=#f9e2af,bg=#1e1e2e] Load:#{run-shell 'curl -sf http://localhost:8001/api/v1/cognitive-load/default_user | jq -r .cognitive_load // 0.5 | awk \"{printf \\\"%d%%\\\", \\$1*100}\"'} \
#[fg=#89b4fa,bg=#1e1e2e]  #{run-shell '~/scripts/tmux-services-health.sh'} \
#[fg=#cdd6f4,bg=#1e1e2e]  %H:%M "

# Window Status (Minimal, ADHD-friendly)
setw -g window-status-format "#[fg=#6c7086] #I:#W "
setw -g window-status-current-format "#[fg=#89b4fa,bg=#313244,bold] #I:#W "
setw -g window-status-separator ""

# Message styling
set -g message-style bg='#f38ba8',fg='#1e1e2e',bold

# Keybindings (Enhanced)
# Prefix = Ctrl-b

# Workspace Management
bind-key w run-shell "tmux display-popup -E -w 80% -h 60% 'dopemux workspace list'"
bind-key W command-prompt -p "Switch workspace:" "run-shell 'dopemux workspace switch %%'"

# Monitoring & Health
bind-key h run-shell "tmux display-popup -E -w 80% -h 60% 'dopemux health-check --detailed'"
bind-key m run-shell "tmux split-window -v -p 40 'python dopemux_dashboard.py'"

# ADHD Controls
bind-key b run-shell "curl -X POST http://localhost:8001/api/v1/break/start"
bind-key e run-shell "tmux display-message \"$(curl -s http://localhost:8001/api/v1/energy-level/default_user | jq -r .energy_level)\""

# Dashboard Cycling
bind-key d run-shell "~/scripts/cycle-dashboard-mode.sh"

# Quick Service Actions
bind-key s run-shell "tmux display-popup -E -w 60% -h 40% 'dopemux services status'"
bind-key r run-shell "dopemux services restart-failed"

# Logs
bind-key l run-shell "tmux display-popup -E -w 90% -h 80% 'dopemux logs --follow --workspace #{WORKSPACE_ID}'"
```

#### 2.3 Status Bar Helper Scripts

**File**: `scripts/tmux-services-health.sh`

```bash
#!/bin/bash
# Tmux status bar helper - Service health summary
# Returns: "8/8" or "7/8" with color coding

SERVICES=(
    "http://localhost:8001/health|ADHD"
    "http://localhost:3004/health|ConPort"
    "http://localhost:3001/health|Serena"
    "http://localhost:8000/health|Orchestrator"
    "http://localhost:8080/health|Bridge"
    "http://localhost:8005/health|Context"
)

HEALTHY=0
TOTAL=${#SERVICES[@]}

for service in "${SERVICES[@]}"; do
    url=$(echo "$service" | cut -d'|' -f1)
    if curl -sf "$url" >/dev/null 2>&1; then
        ((HEALTHY++))
    fi
done

if [ $HEALTHY -eq $TOTAL ]; then
    echo "✓ $HEALTHY/$TOTAL"
elif [ $HEALTHY -gt $((TOTAL / 2)) ]; then
    echo "⚠ $HEALTHY/$TOTAL"
else
    echo "✗ $HEALTHY/$TOTAL"
fi
```

#### 2.4 Workspace-Aware Tmux Session

**File**: `scripts/tmux-workspace-session.sh`

```bash
#!/bin/bash
# Create tmux session for a specific workspace
# Usage: ./tmux-workspace-session.sh <workspace_id>

WORKSPACE_ID="${1:-default}"
SESSION_NAME="dopemux-${WORKSPACE_ID}"

# Check if session exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Session $SESSION_NAME already exists. Attaching..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# Create new session
tmux new-session -d -s "$SESSION_NAME" -n "overview"

# Set workspace environment variable
tmux set-environment -t "$SESSION_NAME" WORKSPACE_ID "$WORKSPACE_ID"

# Pane 0: Workspace overview dashboard
tmux send-keys -t "$SESSION_NAME:overview.0" \
    "python dopemux_dashboard.py --workspace=$WORKSPACE_ID" C-m

# Split for service health (Pane 1)
tmux split-window -h -t "$SESSION_NAME:overview.0" -p 40
tmux send-keys -t "$SESSION_NAME:overview.1" \
    "watch -n 5 'dopemux services status --workspace=$WORKSPACE_ID'" C-m

# Split for logs (Pane 2)
tmux split-window -v -t "$SESSION_NAME:overview.1" -p 50
tmux send-keys -t "$SESSION_NAME:overview.2" \
    "dopemux logs --follow --workspace=$WORKSPACE_ID" C-m

# Create shell window (Pane 3)
tmux split-window -v -t "$SESSION_NAME:overview.0" -p 30
tmux send-keys -t "$SESSION_NAME:overview.3" \
    "export WORKSPACE_ID=$WORKSPACE_ID" C-m

# Set focus to main pane
tmux select-pane -t "$SESSION_NAME:overview.0"

# Attach to session
tmux attach-session -t "$SESSION_NAME"
```

#### 2.5 Updated Dashboard Script

**File**: `scripts/pm-dashboard.sh` (complete rewrite)

```bash
#!/bin/bash
# Real-time Dopemux Dashboard
# Uses actual APIs instead of mock data

set -euo pipefail

WORKSPACE_ID="${WORKSPACE_ID:-default}"
PANE_TYPE="${1:-overview}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# API Base URLs
ADHD_BASE="http://localhost:8001/api/v1"
CONPORT_BASE="http://localhost:3004/api"
ORCHESTRATOR_BASE="http://localhost:8000/api"

# Fetch real ADHD metrics
get_adhd_state() {
    curl -sf "$ADHD_BASE/state?user_id=default_user" 2>/dev/null || echo '{}'
}

# Fetch energy level
get_energy() {
    curl -sf "$ADHD_BASE/energy-level/default_user" 2>/dev/null | \
        jq -r '.energy_level // "unknown"'
}

# Fetch cognitive load
get_cognitive_load() {
    curl -sf "$ADHD_BASE/cognitive-load/default_user" 2>/dev/null | \
        jq -r '.cognitive_load // 0.5' | \
        awk '{printf "%d%%", $1*100}'
}

# Progress bar function
progress_bar() {
    local percent="$1"
    local width=10
    local filled=$((percent * width / 100))
    local empty=$((width - filled))
    
    printf "["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d%%" "$percent"
}

# Main dashboard view
show_overview() {
    clear
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Dopemux Workspace: ${YELLOW}${WORKSPACE_ID}${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo
    
    # ADHD Metrics (REAL DATA)
    echo -e "${BLUE}🧠 ADHD State${NC}"
    ENERGY=$(get_energy)
    LOAD=$(get_cognitive_load)
    
    echo -e "  Energy Level:    ${GREEN}${ENERGY}${NC}"
    echo -e "  Cognitive Load:  ${YELLOW}${LOAD}${NC}"
    echo
    
    # Service Health (REAL DATA)
    echo -e "${BLUE}🔧 Services${NC}"
    
    # Check each service
    check_service "ADHD Engine" "http://localhost:8001/health"
    check_service "ConPort" "http://localhost:3004/health"
    check_service "Serena" "http://localhost:3001/health"
    check_service "Orchestrator" "http://localhost:8000/health"
    echo
    
    # Active tasks (from orchestrator)
    echo -e "${BLUE}📋 Active Tasks${NC}"
    TASK_COUNT=$(curl -sf "$ORCHESTRATOR_BASE/tasks/active?workspace_id=$WORKSPACE_ID" 2>/dev/null | \
        jq -r 'length // 0')
    echo -e "  ${GREEN}${TASK_COUNT}${NC} tasks in progress"
    echo
    
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "Press ${YELLOW}Ctrl-b h${NC} for health check | ${YELLOW}Ctrl-b m${NC} for full dashboard"
}

# Service health check
check_service() {
    local name="$1"
    local url="$2"
    
    if curl -sf "$url" >/dev/null 2>&1; then
        local latency=$(curl -sf -w "%{time_total}" -o /dev/null "$url" 2>/dev/null | \
            awk '{printf "%.0fms", $1*1000}')
        echo -e "  ${GREEN}✓${NC} $name (${latency})"
    else
        echo -e "  ${RED}✗${NC} $name (offline)"
    fi
}

# Route to appropriate view
case "$PANE_TYPE" in
    overview)
        show_overview
        ;;
    *)
        show_overview
        ;;
esac
```

### Phase 3: Integration & Testing (Week 3)

#### 3.1 Service-by-Service Integration

**Priority Order**:

1. ✅ ADHD Engine (week 1)
   - Add monitoring base
   - Export metrics endpoint
   - Test with Prometheus

2. ✅ ConPort (week 1)
   - Add monitoring base
   - Multi-workspace metrics
   - Test workspace filtering

3. ✅ Orchestrator (week 2)
   - Add monitoring base
   - Task metrics
   - Health monitoring

4. ✅ Serena (week 2)
   - Add monitoring base
   - Pattern metrics

5. ✅ Dopecon Bridge (week 2)
   - Add monitoring base
   - Bridge metrics

6. ✅ Dope Context (week 3)
   - Add monitoring base
   - Search metrics

#### 3.2 End-to-End Testing

**Test Suite**: `tests/monitoring/test_e2e_monitoring.py`

```python
"""End-to-end monitoring tests."""

import pytest
import requests
import time

@pytest.fixture
def workspace_id():
    return "test-workspace"

@pytest.fixture
def instance_id():
    return "test-instance"

class TestMonitoringIntegration:
    """Test full monitoring stack integration."""
    
    def test_prometheus_running(self):
        """Verify Prometheus is accessible."""
        resp = requests.get("http://localhost:9090/-/healthy")
        assert resp.status_code == 200
    
    def test_service_metrics_export(self):
        """Verify all services export metrics."""
        services = [
            ("adhd-engine", 8001),
            ("conport", 3004),
            ("serena", 3001),
            ("orchestrator", 8000),
        ]
        
        for name, port in services:
            resp = requests.get(f"http://localhost:{port}/metrics")
            assert resp.status_code == 200
            assert "dopemux_service_info" in resp.text
            assert name in resp.text
    
    def test_workspace_label_present(self, workspace_id):
        """Verify workspace_id label in metrics."""
        resp = requests.get("http://localhost:3004/metrics")
        metrics = resp.text
        
        # Check for workspace_id label
        assert f'workspace_id="{workspace_id}"' in metrics
    
    def test_prometheus_scraping(self):
        """Verify Prometheus is scraping targets."""
        resp = requests.get("http://localhost:9090/api/v1/targets")
        data = resp.json()
        
        active_targets = data['data']['activeTargets']
        assert len(active_targets) > 0
        
        # Verify all expected services
        services = {t['labels']['job'] for t in active_targets}
        expected = {'adhd-engine', 'conport', 'serena', 'orchestrator'}
        assert expected.issubset(services)
    
    def test_query_workspace_metrics(self, workspace_id):
        """Test querying metrics by workspace."""
        # Wait for metrics to be scraped
        time.sleep(5)
        
        # Query Prometheus for workspace-specific metrics
        query = f'dopemux_requests_total{{workspace_id="{workspace_id}"}}'
        resp = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": query}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'success'
    
    def test_grafana_datasource(self):
        """Verify Grafana is connected to Prometheus."""
        resp = requests.get(
            "http://localhost:3000/api/datasources",
            auth=("admin", "dopemux_admin")
        )
        
        assert resp.status_code == 200
        datasources = resp.json()
        
        prometheus_ds = next(
            (ds for ds in datasources if ds['type'] == 'prometheus'),
            None
        )
        assert prometheus_ds is not None
```

#### 3.3 Tmux Integration Tests

```bash
#!/bin/bash
# Test tmux integration

set -e

echo "Testing tmux setup..."

# Test 1: Status bar scripts exist and run
echo "✓ Testing status bar scripts..."
if [[ ! -f ~/scripts/tmux-services-health.sh ]]; then
    echo "✗ tmux-services-health.sh missing"
    exit 1
fi

bash ~/scripts/tmux-services-health.sh
echo "✓ Status bar scripts work"

# Test 2: Workspace session creation
echo "✓ Testing workspace session creation..."
WORKSPACE_ID="test-workspace"
bash scripts/tmux-workspace-session.sh "$WORKSPACE_ID"

# Check if session was created
if ! tmux has-session -t "dopemux-$WORKSPACE_ID" 2>/dev/null; then
    echo "✗ Failed to create tmux session"
    exit 1
fi

echo "✓ Workspace session created"

# Cleanup
tmux kill-session -t "dopemux-$WORKSPACE_ID"

echo "✅ All tmux integration tests passed"
```

---

## 📈 Success Metrics

### Monitoring

- ✅ All services export metrics with `workspace_id` and `instance_id` labels
- ✅ Prometheus scraping all services successfully
- ✅ Can query metrics per workspace
- ✅ Grafana dashboards display per-workspace data
- ✅ Alerts configured for critical thresholds
- ✅ < 100ms metric export overhead

### Tmux

- ✅ Status bar shows real-time data (5s refresh)
- ✅ < 50ms status bar script execution
- ✅ 4 panes instead of 8 (simplified)
- ✅ Workspace context visible in status bar
- ✅ ADHD-friendly color scheme
- ✅ Progressive disclosure (summary → detail on demand)
- ✅ No mock data

### Integration

- ✅ Tmux displays Prometheus data
- ✅ Can switch between workspaces in tmux
- ✅ Workspace filtering works in Grafana
- ✅ All tests passing

---

## 🚀 Deployment Plan

### Week 1: Monitoring Foundation

**Mon-Tue**: Unified monitoring base class
- Create `shared/monitoring/base.py`
- Add tests
- Document usage

**Wed-Thu**: Service integration
- ADHD Engine
- ConPort
- Basic Prometheus setup

**Fri**: Testing & validation
- Deploy Prometheus + Grafana
- Verify metrics export
- Multi-workspace tests

### Week 2: Tmux Redesign

**Mon-Tue**: Status bar implementation
- New `.tmux.conf`
- Helper scripts
- Real-time data feeds

**Wed-Thu**: Dashboard scripts
- Rewrite pm-dashboard.sh
- Workspace session script
- Test with multiple workspaces

**Fri**: Integration testing
- End-to-end tests
- Performance benchmarks
- ADHD UX validation

### Week 3: Remaining Services + Polish

**Mon-Wed**: Complete service integration
- Serena
- Orchestrator
- Dopecon Bridge
- Dope Context

**Thu**: Grafana dashboards
- Create workspace-aware dashboards
- Import templates
- Configure alerts

**Fri**: Final validation & documentation
- Complete test suite
- Update documentation
- User guide

---

## 📚 Documentation Updates Required

1. **Monitoring Guide** (`docs/monitoring/README.md`)
   - Architecture overview
   - Adding monitoring to new services
   - Query examples
   - Troubleshooting

2. **Tmux Guide** (`docs/tmux/README.md`)
   - Setup instructions
   - Keybinding reference
   - Customization guide
   - ADHD optimization notes

3. **Multi-Workspace Guide** (update existing)
   - Monitoring per workspace
   - Tmux workspace sessions
   - Filtering and querying

4. **Developer Onboarding** (update)
   - Monitoring requirements
   - Testing checklist
   - Best practices

---

## 🔍 Appendix: Research Findings

### Tmux Best Practices (from web search)

1. **Show only actionable information** - Avoid clutter
2. **Use monitor-activity for alerts** - Background task notifications
3. **Consistent theming** - Match terminal/IDE colors
4. **Leverage plugins** - tmux-powerline, tmux-mem-cpu-load
5. **Named sessions per project** - Multi-workspace organization
6. **Iterative customization** - Start simple, add as needed

### Prometheus Multi-Workspace Patterns (from web search)

1. **Label-based multi-tenancy** (CHOSEN)
   - Single Prometheus with workspace labels
   - Query proxy for access control
   - Efficient resource usage
   - Global metrics view possible

2. **Multiple Prometheus instances**
   - Strong isolation
   - High resource overhead
   - Complex management
   - NOT chosen for Dopemux

3. **Thanos/Cortex**
   - True multi-tenancy
   - Long-term storage
   - Overkill for current scale
   - Future consideration

---

## ✅ Next Steps

1. **Immediate** (Today):
   - Review and approve this plan
   - Set up project tracking (issues/tasks)
   - Assign team members

2. **Week 1 Kickoff** (Monday):
   - Create unified monitoring base class
   - Set up dev environment with Prometheus
   - Begin ADHD Engine integration

3. **Communication**:
   - Daily standup updates
   - Weekly demos
   - Documentation as we go

---

**This plan provides a complete, research-backed solution to the monitoring and tmux issues. It prioritizes ADHD-friendly design, multi-workspace support, and production-ready architecture.**

