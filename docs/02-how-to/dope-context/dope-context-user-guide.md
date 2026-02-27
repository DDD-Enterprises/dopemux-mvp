---
id: HOWTO-DOPE-CONTEXT-USER-GUIDE
title: Dope-Context User Guide
type: how-to
owner: '@hu3mann'
date: '2026-02-26'
author: '@codex'
prelude: Operator-facing guide for indexing, searching, startup autoindex, and troubleshooting dope-context with deterministic contracts.
last_review: '2026-02-26'
next_review: '2026-05-27'
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/dope-context/src/mcp/server.py
    - src/dopemux/cli.py
---
# Dope-Context User Guide

This guide is the primary operator guide for dope-context indexing and search.

## 1) Start Dopemux and trigger autoindex

Canonical startup commands:

```bash
dopemux start
```

```bash
dopemux launch --preset standard
```

```bash
dopemux dope --theme muted
```

By default, startup triggers:

1. one batch bootstrap pass (`index_workspace` + `index_docs`)
2. ongoing async autonomous indexing for code and docs

## 2) Configure startup behavior

Disable startup trigger:

```bash
DOPEMUX_AUTO_INDEX_ON_STARTUP=0 dopemux start
```

Tune debounce and periodic fallback:

```bash
DOPEMUX_AUTO_INDEX_DEBOUNCE_SECONDS=3 \
DOPEMUX_AUTO_INDEX_PERIODIC_SECONDS=300 \
dopemux start
```

## 3) Run manual indexing on demand

Code index:

```python
mcp__dope-context__index_workspace(workspace_path="/absolute/workspace/path")
```

Docs index:

```python
mcp__dope-context__index_docs(workspace_path="/absolute/workspace/path")
```

Multi-workspace batch indexing:

```python
mcp__dope-context__index_workspace(
    workspace_paths=["/path/a", "/path/b"]
)
```

## 4) Search docs with contextual embeddings

```python
mcp__dope-context__docs_search(
    query="two-plane architecture decision flow",
    top_k=5,
    workspace_path="/absolute/workspace/path"
)
```

Contracted response includes:

- `lane_used="docs"`
- `embed_model_used="voyage-context-3"`
- `fusion_strategy`
- `rerank_used`
- `timings_ms`

## 5) Search code + docs together

```python
mcp__dope-context__search_all(
    query="how retry policy is implemented",
    top_k=10,
    workspace_path="/absolute/workspace/path",
    include_decisions=True
)
```

Notes:

- decision enrichment is optional and read-only
- Trinity boundary rails enforce:
  - default Top-3 decision limit
  - hard max decision limit of 10

## 6) Check startup autoindex status

HTTP status endpoint:

```bash
curl "http://localhost:3010/autoindex/status?workspace_path=$(pwd)"
```

Force a bootstrap rerun for current workspace:

```bash
curl -X POST "http://localhost:3010/autoindex/bootstrap" \
  -H "content-type: application/json" \
  -d "{\"workspace_path\":\"$(pwd)\",\"force\":true,\"wait_for_completion\":false}"
```

## 7) Verify server runtime mode

```bash
curl "http://localhost:3010/info"
```

Validate:

- `canonical_entrypoint == "python -m src.mcp.server"`
- `fastmcp_available == true` in production images
- runtime transport and connection URL match deployment config

## 8) Troubleshooting quick checks

If docs search returns embedding errors:

1. verify `VOYAGE_API_KEY` or `VOYAGEAI_API_KEY`
2. run `mcp__dope-context__index_docs` again
3. confirm `/info` shows expected runtime mode

If startup autoindex is skipped unexpectedly:

1. check `autoindex/status` for snapshot idempotence marker
2. rerun bootstrap with `force=true`

If results look unstable:

1. ensure latest code has deterministic hybrid tie-breaks
2. rerun identical query and compare ordered IDs

## 9) Recommended operator flow

1. `dopemux start`
2. confirm `/info`
3. run `docs_search` and `search_all` sanity queries
4. keep autonomous indexing enabled for ongoing updates
5. only force bootstrap when snapshot has materially changed
