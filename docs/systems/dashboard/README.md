---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Dashboard System Documentation

The Dopemux Dashboard is a tmux-based ADHD-optimized interface providing real-time visibility into your development environment, cognitive state, and system health.

## Quick Links

- **[Dashboard README](TMUX_DASHBOARD_README.md)** - Main documentation and usage guide
- **[Design Document](TMUX_DASHBOARD_DESIGN.md)** - Architecture and design philosophy
- **[Metrics Inventory](TMUX_METRICS_INVENTORY.md)** - Complete metrics catalog

## Overview

The dashboard provides:
- **Focus & Cognitive State** - Current context, energy level, break suggestions
- **Task & Work Context** - Active tasks, session progress, blockers
- **System Health** - Service status, resource usage, alerts

## Documentation Index

### User Guides
- [Dashboard README](TMUX_DASHBOARD_README.md) - How to use the dashboard
- [Customization Guide](DASHBOARD_ENHANCEMENTS.md) - Customize your dashboard

### Design & Architecture
- [Design Document](TMUX_DASHBOARD_DESIGN.md) - Complete design specification
- [Metrics Inventory](TMUX_METRICS_INVENTORY.md) - All available metrics
- [Implementation Tracker](DASHBOARD_IMPLEMENTATION_TRACKER.md) - Development progress

### Implementation Details
- [Enhancement Plans](DASHBOARD_ENHANCEMENTS.md) - Planned improvements
- [Session Summaries](../../implementation-plans/DASHBOARD_SESSION_SUMMARY.md) - Development notes

## Dashboard Components

### Pane 1: Focus & Cognitive State
- Current focus area
- Energy level indicator
- Time since last break
- Break suggestions (Serena AI)
- Flow state tracking

### Pane 2: Tasks & Work Context
- Active task/epic
- Session progress
- Recent commits
- Current blockers
- Next actions

### Pane 3: System Health
- Service status (Redis, PostgreSQL, etc.)
- Resource usage (CPU, Memory)
- MCP server health
- Active alerts
- Quick actions

## Key Features

### ADHD Optimization
- Visual clarity (color coding, clear sections)
- Cognitive load reduction (essential info only)
- Break reminders (intelligent timing)
- Focus preservation (non-intrusive updates)

### Real-Time Updates
- Auto-refresh (configurable interval)
- Event-driven updates for critical changes
- Minimal latency (<1s for most metrics)

### Integration
- **ConPort** - Context and session data
- **Serena (ADHD Engine)** - Break suggestions and energy tracking
- **Task Orchestrator** - Epic and task status
- **System Monitoring** - Service health and metrics

## Usage

### Launch Dashboard
```bash
# Standard 3-pane layout
./scripts/launch-adhd-dashboard.sh

# Custom layout
tmux source-file config/dashboard-custom.conf
```

### Navigate
- `Ctrl+b` then arrow keys - Switch between panes
- `Ctrl+b z` - Zoom current pane
- `Ctrl+b [` - Scroll mode (q to exit)

### Customize
Edit configuration files:
- `config/dashboard-config.yaml` - Metrics and thresholds
- `scripts/dashboard-pane*.sh` - Pane scripts
- Custom layouts in `config/`

## Metrics Reference

See [Metrics Inventory](TMUX_METRICS_INVENTORY.md) for complete catalog including:
- Cognitive & focus metrics
- Task & session metrics
- System health metrics
- Integration metrics

## Development

### Implementation Status
See [Implementation Tracker](DASHBOARD_IMPLEMENTATION_TRACKER.md)

Current phase: **Production Ready**
- ✅ 3-pane bash implementation
- ✅ Real-time metrics
- ✅ ADHD optimization
- 🚧 Advanced integrations (ongoing)

### Enhancement Roadmap
See [Enhancement Plans](DASHBOARD_ENHANCEMENTS.md)

Planned:
- Serena V2 integration
- Custom metric plugins
- Mobile companion
- Advanced visualizations

## Related Documentation

- [ADHD Engine Documentation](../../ADHD_COMPLETE_DOCUMENTATION.md)
- [Architecture Overview](../../04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md)
- [Implementation Plans](../../implementation-plans/)

## Troubleshooting

### Dashboard not updating
Check refresh interval in config and ensure services are running.

### Missing metrics
Verify integration services (Redis, PostgreSQL, ConPort) are accessible.

### Performance issues
Adjust refresh rate, disable expensive metrics, or optimize queries.

---

**Maintained by:** Dopemux Core Team
**Last Updated:** 2025-10-29
