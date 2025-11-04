# Monitoring Setup Guide - Component 6 Observability

Complete guide for setting up Prometheus + Grafana monitoring for ADHD Intelligence Layer.

**Time to Setup**: ~5 minutes
**Requirements**: Docker + Docker Compose

---

## Quick Start (one-liner)

```bash
./scripts/monitoring_stack.sh start
```

This helper script wraps the Docker Compose stack below (and also supports `stop`, `status`, and `logs`).

## Quick Start (Docker Compose - Recommended)

### 1. Start Monitoring Stack

```bash
cd services/task-orchestrator/observability

# Start Prometheus + Grafana
docker-compose -f docker-compose-monitoring.yml up -d

# Check status
docker-compose -f docker-compose-monitoring.yml ps

# View logs
docker-compose -f docker-compose-monitoring.yml logs -f
```

**Expected Output**:
```
dopemux-prometheus   running   0.0.0.0:9090->9090/tcp
dopemux-grafana      running   0.0.0.0:3000->3000/tcp
dopemux-pushgateway  running   0.0.0.0:9091->9091/tcp
```

### 2. Access Services

- **Prometheus**: http://localhost:9090
  - Check targets: http://localhost:9090/targets
  - Query metrics: http://localhost:9090/graph

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin` (change on first login)

---

## Import ADHD Intelligence Dashboard

### Option 1: Export and Import (Quick)

```bash
# Export dashboard JSON
cd services/task-orchestrator/observability
python adhd_dashboard.py

# Output: adhd_intelligence_dashboard.json

# Import to Grafana:
# 1. Open http://localhost:3000
# 2. Login (admin/admin)
# 3. Dashboards → Import
# 4. Upload JSON file: adhd_intelligence_dashboard.json
# 5. Select Prometheus datasource
# 6. Click Import
```

### Option 2: Python Script (Automated)

```python
from observability.adhd_dashboard import generate_default_dashboard

# Export to specific path
dashboard_path = generate_default_dashboard()
print(f"Dashboard exported: {dashboard_path}")

# Then import via Grafana UI
```

---

## Configure Prometheus Datasource in Grafana

If Prometheus datasource isn't auto-configured:

1. Open http://localhost:3000
2. Configuration (⚙️) → Data Sources
3. Add data source → Prometheus
4. URL: `http://prometheus:9090` (from inside Docker network)
5. Access: Server (default)
6. Click "Save & Test"

Expected: ✅ "Data source is working"

---

## Expose Metrics from Task-Orchestrator

Add Prometheus endpoint to your Task-Orchestrator FastAPI app:

```python
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from observability.metrics_collector import get_metrics

app = FastAPI()

# Initialize metrics
metrics = get_metrics()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Now Prometheus can scrape http://localhost:8000/metrics
```

Update `prometheus.yml` with your actual Task-Orchestrator port:

```yaml
scrape_configs:
  - job_name: 'task-orchestrator'
    static_configs:
      - targets: ['host.docker.internal:8000']  # Your FastAPI port
```

Reload Prometheus config:
```bash
docker-compose -f docker-compose-monitoring.yml restart prometheus
```

---

## Verify Metrics Collection

### 1. Check Prometheus Targets

Visit: http://localhost:9090/targets

Expected:
- `prometheus` (1/1 up)
- `task-orchestrator` (1/1 up)
- `pushgateway` (1/1 up)

### 2. Query ADHD Metrics

Visit: http://localhost:9090/graph

Try these queries:
```promql
# Task completion rate
rate(adhd_tasks_completed_total[5m]) / rate(adhd_tasks_started_total[5m])

# Current cognitive load
adhd_cognitive_load

# Context switch frequency
rate(adhd_context_switches_total[1h])

# Flow state sessions
increase(adhd_flow_sessions_total[1d])
```

### 3. View Grafana Dashboard

Visit: http://localhost:3000

Navigate to:
- Dashboards → Browse
- Select "ADHD Intelligence Layer - Component 6"

You should see 8 panels:
1. 🎯 Workflow Completion Rate (gauge)
2. ⏱️ Focus Session Duration Distribution (histogram)
3. 🌊 Flow State Timeline (timeseries)
4. 🧠 Current Cognitive Load (gauge)
5. 📊 Cognitive Load Heatmap (heatmap)
6. 🚀 Task Velocity (timeseries)
7. 🔄 Context Switches per Day (timeseries)
8. ⏱️ Context Switch Recovery Time (histogram)

---

## Alternative: Homebrew Installation (macOS)

If you prefer native installation over Docker:

### Install Prometheus

```bash
brew install prometheus

# Start Prometheus
brew services start prometheus

# Or run manually:
prometheus --config.file=/opt/homebrew/etc/prometheus.yml
```

### Install Grafana

```bash
brew install grafana

# Start Grafana
brew services start grafana

# Or run manually:
grafana-server --config=/opt/homebrew/etc/grafana/grafana.ini
```

### Configure Prometheus

Edit `/opt/homebrew/etc/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'task-orchestrator'
    static_configs:
      - targets: ['localhost:8000']  # Your Task-Orchestrator port
```

Restart: `brew services restart prometheus`

---

## Troubleshooting

### Prometheus Not Scraping Metrics

**Problem**: Target shows "DOWN" in http://localhost:9090/targets

**Solutions**:
1. Check Task-Orchestrator is running: `curl http://localhost:8000/metrics`
2. Check port in `prometheus.yml` matches Task-Orchestrator
3. Check firewall isn't blocking port 8000
4. If using Docker: Use `host.docker.internal` not `localhost`

### Grafana Dashboard Shows "No Data"

**Problem**: Dashboard panels empty

**Solutions**:
1. Check Prometheus datasource configured correctly
2. Check Prometheus is scraping metrics (see above)
3. Wait 1-2 minutes for initial data collection
4. Verify metrics exist in Prometheus: http://localhost:9090/graph

### Docker Compose Fails to Start

**Problem**: Port already in use

**Solutions**:
1. Check what's using the port: `lsof -i :9090` or `lsof -i :3000`
2. Stop conflicting service
3. Or change ports in `docker-compose-monitoring.yml`:
   ```yaml
   ports:
     - "19090:9090"  # Prometheus on 19090
     - "13000:3000"  # Grafana on 13000
   ```

---

## Stopping/Removing Monitoring Stack

### Stop Services

```bash
docker-compose -f docker-compose-monitoring.yml stop
```

### Stop and Remove Containers

```bash
docker-compose -f docker-compose-monitoring.yml down
```

### Remove All Data (Reset)

```bash
docker-compose -f docker-compose-monitoring.yml down -v
```

⚠️ This deletes all metrics history and Grafana configuration

---

## Next Steps

1. ✅ Start monitoring stack
2. ✅ Import ADHD dashboard
3. ✅ Expose metrics from Task-Orchestrator
4. ✅ Verify data collection
5. 🎯 Use dashboard to monitor ADHD workflows!

**Key Metrics to Watch**:
- Task completion rate (target: 85%)
- Context switch recovery time (target: < 2 seconds)
- Flow state frequency (ADHD hyperfocus)
- Cognitive load trends (prevent overwhelm)

---

## Dashboard Panels Explained

### 1. Workflow Completion Rate
**What**: Percentage of started tasks that are completed
**Target**: 85% or higher
**Colors**: Green (85%+), Yellow (70-85%), Red (<70%)
**Action**: If < 85%, investigate abandoned tasks

### 2. Focus Session Duration Distribution
**What**: Histogram of focus session lengths
**ADHD Optimal**: 15-45 minutes
**Action**: Identify your sweet spot, adjust task sizing

### 3. Flow State Timeline
**What**: Green areas show hyperfocus/flow state
**Action**: Protect green areas from interruptions

### 4. Current Cognitive Load
**What**: Real-time cognitive load (0.0-1.0)
**Optimal**: 0.6-0.7 (green)
**Action**: Red (>0.85) = take break immediately

### 5. Cognitive Load Heatmap
**What**: Load patterns by hour of day
**Action**: Schedule complex tasks during low-load hours

### 6. Task Velocity
**What**: Tasks completed per day
**Complexity-Adjusted**: Weights by task complexity
**Action**: Track productivity trends over time

### 7. Context Switches per Day
**What**: Frequency and reasons for context switches
**Green**: Intentional switches
**Yellow**: Break returns
**Red**: Interrupts
**Action**: Minimize red (interrupts)

### 8. Context Switch Recovery Time
**What**: Time to recover from switches
**Target**: < 2 seconds (with Context Switch Recovery Engine)
**Baseline**: 5-10 min (neurotypical), 15-25 min (ADHD without tool)
**Action**: Verify recovery engine working

---

**Created**: 2025-10-20
**Component**: 6 - Phase 1a (Observability Foundation)
**Status**: Ready for deployment
