---
id: MONITORING_TMUX_QUICK_REF
title: Monitoring_Tmux_Quick_Ref
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Monitoring & Tmux Quick Reference

**Status**: 🔴 **NEEDS IMMEDIATE ACTION**
**Full Details**: See `MONITORING_TMUX_COMPREHENSIVE_AUDIT.md`

---

## 🚨 Critical Issues

| Issue | Impact | Priority |
|-------|--------|----------|
| No multi-workspace metrics | Can't track workspace-specific data | 🔴 CRITICAL |
| Tmux shows mock data | Misleading user experience | 🔴 CRITICAL |
| Prometheus not running | No metrics collection | 🔴 CRITICAL |
| Fragmented monitoring code | Inconsistent implementation | 🟠 HIGH |
| Broken status bar scripts | tmux status bar non-functional | 🟠 HIGH |

---

## 🏗️ Solution Overview

### Architecture Choice

**Label-Based Multi-Tenancy** (Prometheus Best Practice)

```
Every metric includes:
  workspace_id="workspace-name"
  instance_id="instance-0"
  service="service-name"
```

### New Structure

```
Monitoring:           Tmux:
- Unified base class  - 4 panes (not 8)
- workspace_id labels - Real-time data (5s refresh)
- instance_id labels  - Workspace-aware status bar
- /metrics endpoints  - No mock data
- Prometheus + Grafana - ADHD-optimized colors
```

---

## 🚀 Quick Start (3 Steps)

### 1. Deploy Monitoring Stack (5 min)

```bash
# Start Prometheus + Grafana
cd /Users/dopemux/code/dopemux-mvp
docker-compose -f docker-compose.monitoring.yml up -d

# Verify
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000  # Grafana (admin/dopemux_admin)
```

### 2. Add Monitoring to a Service (15 min)

```python
# In service's main file
from shared.monitoring import DopemuxMonitoring
from prometheus_client import make_asgi_app

# Initialize
monitoring = DopemuxMonitoring(
    service_name="my-service",
    workspace_id=os.getenv("WORKSPACE_ID"),
    instance_id=os.getenv("INSTANCE_ID")
)

# Mount metrics endpoint
app.mount("/metrics", make_asgi_app(registry=monitoring.registry))

# Use in endpoints
@app.get("/api/endpoint")
async def my_endpoint():
    start = time.time()

    try:
        result = do_work()
        monitoring.record_request(
            endpoint="/api/endpoint",
            method="GET",
            status=200,
            duration=time.time() - start
        )
        return result
    except Exception as e:
        monitoring.record_request(
            endpoint="/api/endpoint",
            method="GET",
            status=500,
            duration=time.time() - start
        )
        raise
```

### 3. Set Up Tmux (10 min)

```bash
# Install helper scripts
mkdir -p ~/scripts
cp scripts/tmux-services-health.sh ~/scripts/
chmod +x ~/scripts/*.sh

# Source new tmux config
tmux source-file .tmux.conf

# Create workspace session
bash scripts/tmux-workspace-session.sh my-workspace

# Or reload tmux
tmux kill-server
tmux
```

---

## 📊 Verification Checklist

### Monitoring

- [ ] Prometheus accessible at http://localhost:9090
- [ ] Grafana accessible at http://localhost:3000
- [ ] Service exports `/metrics` endpoint
- [ ] Metrics include `workspace_id` label
- [ ] Metrics include `instance_id` label
- [ ] Prometheus scraping service (check Targets page)

### Tmux

- [ ] Status bar shows real data (not "unknown")
- [ ] Status bar scripts execute < 100ms
- [ ] Workspace ID visible in status bar
- [ ] Services health indicator shows actual status
- [ ] Keybindings work (Ctrl-b h, Ctrl-b m, etc.)
- [ ] No error messages in panes

---

## 🎯 Key Commands

### Monitoring

```bash
# Check service metrics
curl http://localhost:8001/metrics  # ADHD Engine
curl http://localhost:3004/metrics  # ConPort

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=dopemux_requests_total'

# Query workspace-specific
curl 'http://localhost:9090/api/v1/query?query=dopemux_requests_total{workspace_id="my-workspace"}'

# Restart monitoring stack
docker-compose -f docker-compose.monitoring.yml restart
```

### Tmux

```bash
# Create workspace session
bash scripts/tmux-workspace-session.sh <workspace-id>

# List sessions
tmux ls

# Attach to session
tmux attach -t dopemux-<workspace-id>

# Kill session
tmux kill-session -t dopemux-<workspace-id>

# Reload config
tmux source-file ~/.tmux.conf
# Or within tmux: Ctrl-b : source-file ~/.tmux.conf
```

### Keybindings (within tmux)

| Key | Action |
|-----|--------|
| `Ctrl-b w` | List workspaces |
| `Ctrl-b W` | Switch workspace |
| `Ctrl-b h` | Health check popup |
| `Ctrl-b m` | Full dashboard |
| `Ctrl-b b` | Take break (ADHD) |
| `Ctrl-b e` | Show energy level |
| `Ctrl-b s` | Services status |
| `Ctrl-b l` | View logs |

---

## 🐛 Troubleshooting

### "Prometheus not scraping"

```bash
# Check Prometheus logs
docker logs dopemux-prometheus

# Check if service is accessible
curl http://localhost:8001/metrics

# Verify prometheus.yml config
cat services/monitoring/prometheus.yml
```

### "Tmux status bar shows 'unknown'"

```bash
# Test API endpoints
curl http://localhost:8001/api/v1/energy-level/default_user
curl http://localhost:8001/api/v1/cognitive-load/default_user

# Test status bar script directly
bash ~/scripts/tmux-services-health.sh

# Check tmux environment
tmux show-environment -g
```

### "Metrics missing workspace_id"

```python
# Verify service initialization
monitoring = DopemuxMonitoring(
    service_name="my-service",
    workspace_id=os.getenv("WORKSPACE_ID", "default"),  # ← Must be set
    instance_id=os.getenv("INSTANCE_ID", "0")
)

# Check environment variable
echo $WORKSPACE_ID
```

---

## 📈 Success Metrics

| Metric | Target | How to Check |
|--------|--------|--------------|
| Metrics export overhead | < 100ms | `curl -w "%{time_total}" http://localhost:8001/metrics` |
| Status bar refresh | < 50ms | Time status bar script execution |
| All services healthy | 100% | Check `http://localhost:9090/targets` |
| Workspace filtering works | Yes | Query Prometheus with workspace_id |
| No mock data in tmux | Yes | Verify tmux shows real API responses |

---

## 🔗 Related Docs

- **Full Audit**: `MONITORING_TMUX_COMPREHENSIVE_AUDIT.md` (Complete analysis + implementation plan)
- **Multi-Workspace**: `MULTI_WORKSPACE_INDEX.md` (Workspace support docs)
- **Monitoring Base**: `shared/monitoring/base.py` (Code reference)
- **Tmux Config**: `.tmux.conf` (Configuration file)

---

## 📅 Implementation Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Monitoring foundation | Base class, ADHD Engine, ConPort integrated |
| 2 | Tmux redesign | New config, status bar, real-time dashboards |
| 3 | Complete rollout | All services, Grafana, tests, docs |

**Current Status**: 🔴 Week 0 (Planning Complete)
**Next Step**: Week 1 kickoff - Create monitoring base class

---

**Need help? Read the full audit or start with deploying the monitoring stack!**
