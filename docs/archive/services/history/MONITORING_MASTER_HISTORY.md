---
id: MONITORING_MASTER_HISTORY
title: Monitoring Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Monitoring Master History (explanation) for dopemux documentation and developer
  workflows.
---
# Monitoring Stack: Master History & Feature Catalog

**Service ID**: `monitoring` (Infrastructure Layer)
**Role**: Observability, Metrics, & Health Tracking
**Primary Owner**: @hu3mann
**Latest Version**: 1.0.0 (Fully Operational)
**Ports**: 9090 (Prometheus), 3000 (Grafana), 9093 (AlertManager)

---

## 1. Executive Summary & Evolution

The Monitoring Stack provides deep observability into the Dopemux platform, designed not just for system health but for "Cognitive Health". It tracks typical metrics (CPU, latency) alongside ADHD-specific metrics (Energy Levels, Cognitive Load) to help users optimize their biological performance as well as their software's.

**Evolutionary Phases:**
* **Phase 1 (Logs)**: Simple logs and `docker stats`.
* **Phase 2 (Fragmented)**: Disparate health checks and scripts.
* **Phase 3 (Unified Stack)**: Deployment of Prometheus/Grafana with a shared `DopemuxMonitoring` base class enforcing consistent labeling (`workspace_id`, `instance_id`).

---

## 2. Feature Catalog (Exhaustive)

### Core Components
* **Prometheus**: Scrapes `/metrics` endpoints every 15s.
* **Grafana**: Visualizes system and cognitive state. Pre-provisioned "Dopemux Service Overview" dashboard.
* **AlertManager**: Routes alerts (e.g., "Service Down" or "High Cognitive Load").

### ADHD Metrics
* `adhd_energy_level`: User's current energy (0-100).
* `adhd_cognitive_load`: Real-time cognitive load estimation.
* `adhd_attention_state`: Focused vs. Scattered state tracking.

### Architecture Features
* **Multi-Workspace**: All metrics tagged with `workspace_id` for isolated tracking.
* **Shared Library**: `shared.monitoring.base.DopemuxMonitoring` simplifies integration for Python services.
* **Zero-Config**: Dashboards and data sources are auto-provisioned via config files.

---

## 3. Architecture Deep Dive

### Data Flow
```
[Service: ADHD Engine] --(exposes /metrics)--> [Prometheus] --(queries)--> [Grafana]
                                                    |
                                                 (alerts)
                                                    v
                                             [AlertManager]
```

### Integration
* **Python Services**: Use `DopemuxMonitoring` class to expose standard metrics (requests, latency, errors) + custom business metrics.
* **Dashboard**: Integrates with `Session Manager` to display real-time stats in the TUI/Tmux.

---

## 4. Validated Status (Audit Results)

**✅ Production Ready:**
* **Status**: "FULLY OPERATIONAL" (95% complete).
* **Coverage**: All core services (ADHD Engine, ConPort, Bridge, Context) are instrumented.
* **Performance**: <100ms overhead per request.

---

*Sources: `MONITORING_COMPLETE.md`, `MONITORING_DEPLOYMENT_GUIDE.md`, `MONITORING_TMUX_COMPREHENSIVE_AUDIT.md`.*
