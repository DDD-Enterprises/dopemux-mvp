# Tools Context

> **TL;DR**: Development and operational tools. Well-documented, standalone, with clear CLI interfaces.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Purpose

Standalone tools for development and operations:
- Port auditing
- Health checking
- Code analysis
- Development utilities

---

## Directory Structure

```
tools/
├── auditor_router/       # PAL clink audit routing
├── copilot_repair/       # Copilot import repair utilities
├── pr_action_bridge/     # PR action bridge (GitHub → internal)
├── pr_steward/           # PR steward automation
├── prompt_rewrite_v4/    # Prompt rewrite v4 engine
├── env_drift_scan.py     # Detect env var drift
├── generate_smoke_env.py # Generate smoke test env files
├── ports_health_audit.py # Check service port health
├── smoke_runtime_gate.py # Smoke test runtime gate
├── webhook_receiver.py   # Incoming webhook receiver
└── __init__.py
```

## Key Tools

| Tool | Purpose |
|------|---------|
| `ports_health_audit.py` | Check service port health |
| `env_drift_scan.py` | Detect environment variable drift |
| `generate_smoke_env.py` | Generate smoke test env configurations |
| `smoke_runtime_gate.py` | Gate deployments on smoke test pass |
| `webhook_receiver.py` | Receive and dispatch incoming webhooks |
| `auditor_router/` | Route PAL clink audit requests |
| `pr_action_bridge/` | Bridge PR actions to internal systems |
| `pr_steward/` | Automate PR stewardship workflows |
| `prompt_rewrite_v4/` | V4 prompt rewrite engine |

---

## Tool Standards

- **Standalone** - No complex dependencies
- **CLI interface** - argparse or click
- **Documentation** - Clear --help output
- **Exit codes** - 0 success, non-zero error

```python
#!/usr/bin/env python3
"""Tool description.

Usage:
    python tool.py --option value
"""
```
