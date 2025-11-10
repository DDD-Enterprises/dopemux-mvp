---
id: orchestrator-dashboard
title: Orchestrator Dashboard
type: how-to
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Orchestrator Dashboard Quickstart

Use the standalone Rich TUI (`scripts/orchestrator_dashboard.py`) to monitor the Dope layout orchestrator without launching the full tmux preset.

## Prerequisites

- Python 3.10+
- Project dependencies installed (`pip install -r requirements.txt`) – the dashboard now relies on `rich`, `httpx`, and `aiohttp`
- Dopemux services running so the data reflects reality:
  - ADHD engine (`localhost:3008`) and activity capture (`localhost:3006`)
  - ConPort / Leantime APIs for sprint + task data
  - LiteLLM proxy (`localhost:4000`) for cost & latency
  - Prometheus on `http://localhost:9090` (start with `./scripts/monitoring_stack.sh start`)

## Launching

```bash
cd /Users/hue/code/dopemux-mvp
pip install -r requirements.txt   # first time only
python scripts/orchestrator_dashboard.py
```

Keyboard shortcuts are displayed in the footer (same hotkeys as the Dope layout: `M`, `P`, `C`, `D`, `?`, `Q`). Press `Ctrl+C` to exit.

## Pane Layout

- **Header:** Mode branding with live clock
- **Status:** Current mode, ADHD engine session stats, focus, velocity (Prometheus fallback-aware)
- **Services:** LiteLLM cost/latency, Docker compose health, MCP probe status
- **Active Tasks:** ConPort/Leantime work-in-progress with progress + remaining hours
- **Alerts:** Serena untracked-work hints plus git diff reminders
- **Metrics:** Git churn, context switches (activity capture), LiteLLM cost/latency, Prometheus cognitive load

## Optional tmux integration

Add a Makefile target (see `docs/archive/completed-projects/ORCHESTRATOR-INTEGRATION-COMPLETE.md`) or create a tmux preset that runs `python scripts/orchestrator_dashboard.py` in a dedicated pane. This pairs well with the Dope layout when you want the orchestrator view side-by-side with the Textual monitors.

## Live Data Sources

| Panel            | Source(s)                                       | Notes |
| ---------------- | ------------------------------------------------ | ----- |
| Status           | `ImplementationCollector` → ADHD engine & activity capture | Falls back to placeholders if endpoints are offline. |
| Services         | `ImplementationCollector` → LiteLLM metrics + Docker compose | LiteLLM `/metrics` must be enabled (default when running Dopemux with routing). |
| Active Tasks     | `PMCollector` → ConPort sprint API + Leantime epics | Displays up to six non-completed tasks across active epics. |
| Metrics          | `ImplementationCollector` + Prometheus client    | Prometheus health check guards the cognitive load / velocity rows. |
| Alerts           | Serena untracked-work API + git porcelain scan   | Alerts collapse to “✅ No active alerts” when nothing actionable is found. |

## Future Enhancements

- **Event bridge:** Subscribe to the same Redis/Event bus used by the Dope layout to surface transient notifications and task assignments.
- **Unified layout:** Expose the Rich dashboard as an optional right-hand pane in the Dope layout so orchestrator operators can toggle between Textual and Rich modes without leaving tmux.
- **Export hooks:** Emit metrics to the Prometheus stack (via the new `scripts/monitoring_stack.sh`) so Grafana mirrors the orchestrator view.
- **Command hotkeys:** Add quick actions (plan, commit, halt orchestrator) that call the Dopemux CLI from within the Rich interface.
