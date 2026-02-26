---
id: TP-DOPECONTEXT-CTX3-0006
title: Tp Dopecontext Ctx3 0006
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-26'
last_review: '2026-02-26'
next_review: '2026-05-27'
prelude: Tp Dopecontext Ctx3 0006 (explanation) for dopemux documentation and developer
  workflows.
---
# Task Packet: TP-DOPECONTEXT-CTX3-0006 · Dope-Context · Startup Autoindex

## Objective
On Dopemux startup, run one bootstrap indexing pass for the current workspace, then enable async autonomous updates.

## Scope
IN:
- `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/README.md`
- `/Users/hue/code/dopemux-mvp/docs/02-how-to/extraction/run-v4-from-dopemux-cli.md`

OUT:
- Multi-workspace startup fanout

## Acceptance
- Startup triggers bootstrap route once.
- Bootstrap is idempotent per workspace snapshot unless forced.
- Autonomous code/docs watchers are started after bootstrap.
