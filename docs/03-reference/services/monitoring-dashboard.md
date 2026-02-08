---
id: monitoring-dashboard
title: Monitoring Dashboard
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Monitoring Dashboard (reference) for dopemux documentation and developer
  workflows.
---
# Monitoring Dashboard

**Extracted from**: PHASE1_SERVICES_INTEGRATION_COMPLETED.md
**Date**: 2026-02-02

## Monitoring & Health Features (from Phase 1)

### Unified Monitoring Dashboard
**Architecture**: FastAPI service (Port 8098)

**Features**:
- Real-time monitoring with parallel checks of 8+ core services
- Progressive disclosure: Overview → Details → Deep diagnostics
- 30-second caching for performance
- ADHD-optimized UI with color-coded status
- Web dashboard with live updates
- REST API endpoints: /health, /api/dashboard, /api/services/{name}

**Implementation**:
- MonitoringDashboard class with async health checking
- ServiceHealth and DashboardResponse Pydantic models
- Multi-modal health checks (HTTP + fallbacks)

### Health Endpoint Standardization
**Service Categories**:
- Web APIs: Standard JSON responses
- Database Services: PostgreSQL process checks as fallback
- Web Applications: Auth-aware redirects
- MCP Servers: Socket connectivity checks

**Fallback Mechanisms**:
- Process checks: pg_isready for PostgreSQL
- Docker checks: Container status
- Socket pings: Port connectivity
- Auth handling: Login redirects treated as healthy

### ADHD-Optimized Alert System
**Progressive Urgency Framework**: 5-level alert system

**Alert Levels**:
- Level 1 (Soft Reminder): Minor issues, handle when convenient
- Level 2 (Gentle Alert): Check during next break
- Level 3 (Action Needed): Focused troubleshooting time
- Level 4 (Critical Attention): Prioritize fixing
- Level 5 (Emergency): Immediate action required

**ADHD Optimizations**:
- Break integration: Queries ADHD Engine for contextual suggestions
- Gentle notifications: No jarring alerts, progressive urgency
- Context awareness: Considers mental bandwidth and energy levels
- Cooldown logic: 5-minute minimum between similar alerts
- Smart escalation: Only alerts on urgency increases or critical thresholds
