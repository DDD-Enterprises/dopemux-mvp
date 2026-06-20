---
description: "Semantic code+docs search in the current workspace via dope-context (Memory Trinity plane 3)"
arguments: "<query> [--code-only|--docs-only] [--top-k N]"
allowed-tools: [
  "Read", "Bash",
  "mcp__dope-context__search_code",
  "mcp__dope-context__docs_search",
  "mcp__dope-context__search_all",
  "mcp__dope-context__get_index_status"
]
model: "claude-sonnet-4-5"
---

# /ctx:search-here — Semantic Search (dope-context)

Fast semantic search in the **current workspace** using **dope-context** (retrieval plane only — not a canonical memory writer).

**Authority**: Memory Trinity plane 3 per `docs/90-adr/adr-dope-context-as-search-and-retrieval-plane.md`.

## Phase 1 — Preflight

1. Confirm `mcp__dope-context__*` is available (singleton `http://localhost:3010/mcp` in `~/.claude.json`).
2. If unreachable: report `docker ps --filter name=dope-context` and `dopemux mcp sync-globals --apply` remediation; stop.

## Phase 2 — Parse

- `$ARGUMENTS` → query string (required)
- `--code-only` → `search_code` only
- `--docs-only` → `docs_search` only
- `--top-k N` → default 5 (max 10 for ADHD scannability)

## Phase 3 — Search

1. Optionally call `get_index_status` — if empty, run `index_workspace` first (offer, don't auto-index large trees without confirmation).
2. Default: `search_all` with `top_k` capped at 5 unless operator passed `--top-k`.
3. Pass `workspace_path` = git repo root (`git rev-parse --show-toplevel`).

## Phase 4 — Render

Show hits as: `file — score — 1-line snippet`. Cap at 5 results. Note `trinity_boundaries.marker` when `search_all` includes decision projections (DERIVED, not canonical).

> Token thrift: refine query before widening; never request >10 results.