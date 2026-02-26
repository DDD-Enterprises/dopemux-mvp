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
