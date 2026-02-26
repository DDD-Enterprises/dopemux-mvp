---
id: TP-DOPECONTEXT-CTX3-0003
title: Tp Dopecontext Ctx3 0003
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-26'
last_review: '2026-02-26'
next_review: '2026-05-27'
prelude: Tp Dopecontext Ctx3 0003 (explanation) for dopemux documentation and developer
  workflows.
---
# Task Packet: TP-DOPECONTEXT-CTX3-0003 · Dope-Context · docs_search Embedding Space + Provenance

## Objective
Ensure docs queries use `voyage-context-3` query mode and return provenance envelope fields.

## Scope
IN:
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/tests/test_mcp_server.py`

OUT:
- Code search model routing changes

## Acceptance
- docs search response includes `lane_used`, `fusion_strategy`, `rerank_used`, `embed_model_used`, `timings_ms`.
- Tests assert docs embedder called with `model=voyage-context-3`, `input_type=query`.
