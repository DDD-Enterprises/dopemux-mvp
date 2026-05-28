---
id: orchestrator-mcp-wrappers
title: MCP Wrapper Surfaces
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference for stdio-based Task Orchestrator MCP wrapper surfaces and local containers.
related_packets:
  - TP-DMX-ORCH-005
---

# Task Orchestrator MCP Wrappers

This document outlines the stdio-based MCP wrapper surfaces used to drive task-orchestrator within the local development environments.

## Stdio MCP Service Launcher
The stdio launcher script manages the singleton Docker container and mounts:
```bash
/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh
```

*   **Singleton Lock**: Assigns a deterministic name per workspace (`task-orchestrator-<workspace_id>`) to prevent WAL SQLite db lock contention.
*   **Resolution Output**: Supports `--print-resolution` to list state paths without starting a container.
