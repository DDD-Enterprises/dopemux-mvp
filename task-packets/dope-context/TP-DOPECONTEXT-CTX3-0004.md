# Task Packet: TP-DOPECONTEXT-CTX3-0004 · Dope-Context · Deterministic Hybrid Fusion

## Objective
Make hybrid retrieval deterministic and expose timing/provenance in responses.

## Scope
IN:
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/search/hybrid_search.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/tests/test_hybrid_determinism.py`

OUT:
- New retrieval models/providers

## Acceptance
- Tie-breaks are stable (`doc_id/chunk_id` ascending).
- Repeat runs return identical order for same query and corpus.
