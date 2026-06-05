---
id: dcp-mcp-readonly-response-envelope
title: DCP Read-Only MCP Facade — Response Envelope Schema
type: reference
owner: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Canonical response envelope and status semantics for the read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Response Envelope Schema

> **Status.** `PROPOSED`. Field set is derived from the load-pack global invariant: *"Every returned payload includes project_id, branch, head_sha, dirty state where available, source system, authority label, freshness, limitations, warnings, redactions, and blocked reasons."* Status semantics derive from the invariant *"Missing backend capability returns PARTIAL or BLOCKED, never guessed data."*

## 1. Canonical Envelope

Every facade response — successful, partial, or blocked — uses this structure:

```json
{
  "project_id": "string",            // echoed; null only for list_projects
  "branch": "string|null",           // git branch where available
  "head_sha": "string|null",         // git HEAD where available
  "dirty": "boolean|null",           // working-tree dirty state where available
  "source_system": "string",         // e.g. conport | dope-memory | dope-context | task-orchestrator | facade
  "authority_label": "string",       // CANONICAL | DERIVED | PROXY | facade
  "status": "string",                // OK | PARTIAL | BLOCKED  (see §2)
  "freshness": "string|null",        // timestamp / staleness indicator of the underlying data
  "limitations": ["string"],         // applied caps (e.g. "results capped at 20")
  "warnings": ["string"],            // e.g. "dirty worktree", "stale proof bundle"
  "redactions": ["string"],          // what was stripped (e.g. "absolute_paths", "secrets")
  "blocked_reasons": ["string"],     // populated when status=BLOCKED (or partial denials)
  "data": {}                         // the actual read payload (object or array)
}
```

## 2. Status Semantics

| Status | Meaning |
| --- | --- |
| `OK` | The read completed fully; `data` is the requested evidence. |
| `PARTIAL` | The read partially succeeded (e.g. a bound backend was unreachable, or a cap truncated results). `data` holds what was retrieved; `limitations`/`warnings` explain the gap. |
| `BLOCKED` | The read was refused or could not run (unknown/disabled project, denied route, path escape, unavailable capability). `data` is empty/null; `blocked_reasons` explains why. |

**Core rule (load-pack invariant):** a missing backend capability returns `PARTIAL` or `BLOCKED` — **never guessed data**. The facade does not fabricate fields it could not read.

> `PROPOSED`/`CONFLICTING`: `OK` is introduced here as the success status because the load pack only names `PARTIAL`/`BLOCKED` explicitly (for the not-fully-available cases) and does not name the success token. `OK` is the proposed success label; if 0004 implementation chooses a different success token, this doc must be reconciled to it. No `DEGRADED`/`ERROR`/`SUCCESS` tokens are asserted unless implementation introduces them.

## 3. Example — successful repo-state snapshot

```json
{
  "project_id": "dopemux-mvp",
  "branch": "main",
  "head_sha": "9667f5e2d...",
  "dirty": false,
  "source_system": "facade",
  "authority_label": "facade",
  "status": "OK",
  "freshness": "2026-06-05T00:00:00Z",
  "limitations": [],
  "warnings": [],
  "redactions": ["absolute_paths"],
  "blocked_reasons": [],
  "data": { "branch": "main", "head_sha": "9667f5e2d...", "dirty": false }
}
```

## 4. Example — blocked (denied route)

```json
{
  "project_id": "dopemux-mvp",
  "branch": null, "head_sha": null, "dirty": null,
  "source_system": "conport",
  "authority_label": "CANONICAL",
  "status": "BLOCKED",
  "freshness": null,
  "limitations": [],
  "warnings": [],
  "redactions": [],
  "blocked_reasons": ["route POST /api/decisions is mutating and denied in Phase 1"],
  "data": null
}
```

## 5. Example — partial (capability unavailable / stale proof)

```json
{
  "project_id": "dopemux-mvp",
  "branch": "main", "head_sha": "abc123...", "dirty": true,
  "source_system": "dope-memory",
  "authority_label": "CANONICAL",
  "status": "PARTIAL",
  "freshness": "2026-06-01T12:00:00Z",
  "limitations": ["results capped at 20", "top_k=3 enforced"],
  "warnings": ["dope-memory profile unbound for this project", "working tree dirty"],
  "redactions": ["secrets"],
  "blocked_reasons": ["chronicle search unavailable: no dope_memory profile"],
  "data": []
}
```
