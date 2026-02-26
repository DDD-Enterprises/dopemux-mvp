---
id: TP-DOPECONTEXT-CTX3-0005
title: Tp Dopecontext Ctx3 0005
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-26'
last_review: '2026-02-26'
next_review: '2026-05-27'
prelude: Tp Dopecontext Ctx3 0005 (explanation) for dopemux documentation and developer
  workflows.
---
# Task Packet: TP-DOPECONTEXT-CTX3-0005 · Dope-Context · Canonical FastMCP Entrypoint

## Objective
Remove deployment ambiguity by standardizing on `python -m src.mcp.server`.

## Scope
IN:
- `/Users/hue/code/dopemux-mvp/services/dope-context/Dockerfile`
- `/Users/hue/code/dopemux-mvp/services/dope-context/Dockerfile.fixed`
- `/Users/hue/code/dopemux-mvp/services/dope-context/services/dope-context/Dockerfile`
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/tests/test_mcp_server.py`

OUT:
- Removal of `simple_server.py` fallback code

## Acceptance
- `/info` includes `fastmcp_available`, active transport, and canonical entrypoint marker.
