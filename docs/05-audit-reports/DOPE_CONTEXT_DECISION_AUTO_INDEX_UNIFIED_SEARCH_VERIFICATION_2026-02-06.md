---
id: DOPE_CONTEXT_DECISION_AUTO_INDEX_UNIFIED_SEARCH_VERIFICATION_2026_02_06
title: Dope Context Decision Auto Index Unified Search Verification 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: active
prelude: Verification for ConPort packet rows 14 and 17, covering dope-context decision retrieval configuration and unified search behavior across code, docs, and decisions.
---
# Dope Context Decision Auto Index and Unified Search Verification

## Scope

1. Row `14`: `3.3.1 Configure dope-context auto-index for decisions`.
2. Row `17`: `3.3.2 Test unified search (code + decisions + docs)`.

## Implemented Changes

1. Added workspace-scoped decision retrieval configuration in `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`:
   - `configure_decision_auto_indexing(...)`
   - config persistence via `decision_sync_config.json`.
2. Extended unified search path to include decisions:
   - `_search_all_impl(..., include_decisions=True)` now returns `decision_results` and `decision_search_enabled`.
   - Added `_search_decisions_impl(...)` that queries dopecon-bridge `/kg/decisions/search`.
3. Updated dope-context runtime docs:
   - `/Users/hue/code/dopemux-mvp/services/dope-context/README.md`.

## Verification Commands

```bash
PYTHONPATH=/Users/hue/code/dopemux-mvp/services/dope-context pytest -q --no-cov -k 'not trio' services/dope-context/tests/test_mcp_server.py
```

## Result

1. Command passed.
2. New coverage added for:
   - decision config persistence.
   - unified search merge behavior when decision retrieval is enabled.
3. Row `14` and row `17` are reclassified to implemented.
