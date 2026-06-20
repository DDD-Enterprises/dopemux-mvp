---
description: "Index then search a path via dope-context (code and/or docs)"
arguments: "<path> :: <query> [--docs]"
allowed-tools: [
  "Read", "Bash",
  "mcp__dope-context__index_workspace",
  "mcp__dope-context__index_docs",
  "mcp__dope-context__search_code",
  "mcp__dope-context__docs_search",
  "mcp__dope-context__get_index_status"
]
model: "claude-sonnet-4-5"
---

# /ctx:index-search — Index + Search (dope-context)

Index a path, then search it with **dope-context**.

**Args**: `$ARGUMENTS` = `<PATH> :: <QUERY>` (path defaults to `.`)

**Authority**: Memory Trinity plane 3 — retrieval only.

## Steps

1. Confirm dope-context MCP is connected; if not, stop with `dopemux mcp sync-globals` + `docker compose up -d dope-context` remediation.
2. Resolve `<PATH>` to absolute under repo root.
3. Call `get_index_status`; if stale/missing, call `index_workspace` (code) and/or `index_docs` when `--docs` passed.
4. Run `search_code` or `docs_search` for `<QUERY>`; return top 5 hits as `file — score — snippet`.
5. On failure, show exact MCP error + next fix (Qdrant down, VOYAGE_API_KEY missing, etc.).

> Token thrift: cap results to ≤5; prefer `search_code` over `search_all` for targeted lookups.