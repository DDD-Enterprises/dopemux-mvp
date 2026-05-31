---
id: dopemux-mission-control-plugin
title: Dopemux Mission Control Plugin
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-30'
last_review: '2026-05-30'
next_review: '2026-08-28'
prelude: Repo-owned Codex plugin distribution for Dopemux PAL and Task Orchestrator MCP wiring.
---
# Dopemux Mission Control Plugin

This directory is the repo-owned distribution for the local Codex plugin installed at:

```bash
/Users/hue/plugins/dopemux-mission-control
```

The plugin exposes:

- `pal` through the validated local Docker stdio path.
- `task-orchestrator` through `scripts/task-orchestrator-current-stdio.sh`.

The Task Orchestrator launcher stores durable state under:

```bash
~/.local/share/dopemux-mission-control/task-orchestrator/<repo-id>/current-tasks.db
```

To update the installed local plugin from this repo-owned distribution:

```bash
rsync -a --delete plugins/dopemux-mission-control/ /Users/hue/plugins/dopemux-mission-control/
```

After updating the installed plugin, restart Codex so required MCP servers are relaunched.
