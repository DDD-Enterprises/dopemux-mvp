---
id: 02_derived_memory_pipeline
title: 02_Derived_Memory_Pipeline
type: reference
owner: '@hu3mann'
last_review: '2026-02-08'
next_review: '2026-05-09'
author: '@hu3mann'
date: '2026-02-08'
prelude: Deterministic derived-memory pipeline spec for capture, normalization,
  promotion, derivation, and read-only global rollup.
---

# Dope-Memory v1 — Derived Memory Pipeline

## Purpose

Define a deterministic, auditable pipeline from raw capture to derived memory
products without implicit injection and without introducing a second authority
for project truth.

## Stage 0: Capture (ADR-213: Dual-Capture Design)

Inputs:

1. Claude hook/plugin adapter events.
1. CLI/MCP trigger adapter events.

Storage:

1. Canonical per-project SQLite ledger:
   `repo_root/.dopemux/chronicle.sqlite`.
1. Table: `raw_activity_events`.

Rules:

1. Resolve repo root deterministically (`.git` or `.dopemux` marker).
1. Redact payload before persistence.
1. Generate deterministic `event_id` for retry-idempotency.
1. Use duplicate-safe insert semantics (`INSERT OR IGNORE`).

**Dual-Capture Convergence** (ADR-213):

- All capture modes (`plugin`, `cli`, `mcp`, `auto`) write to **same canonical ledger**
- Same event from different modes produces **identical event_id**
- Event ID is content-based (hash of event_type + payload + ts_utc), mode-independent
- Enables idempotent retry: capturing same event twice via different modes deduplicates correctly
- Capture fails closed (raises `CaptureError`) if repo root cannot be resolved

## Stage 1: Normalize

Inputs:

1. Redacted raw events from `raw_activity_events`.

Storage (implementation-flexible):

1. In-memory normalization or optional normalized table.

Rules:

1. Deterministic transforms only.
1. No probabilistic ranking or heuristic mutation.
1. Preserve stable provenance fields (`workspace_id`, `instance_id`,
   `session_id`, `event_id`).

## Stage 2: Promote

Inputs:

1. Normalized event stream from Stage 1.

Storage:

1. Table: `work_log_entries` (durable curated history).

Rules:

1. Promotion allowlist is deterministic and explicit.
1. Promotion-level redaction remains fail-closed.
1. Stable ordering for retrieval remains deterministic:
   `importance_score DESC`, `ts DESC`, `id ASC`.

## Stage 3: Derive

Inputs:

1. Curated `work_log_entries`.

Outputs (deterministic products):

1. Session recaps.
1. Issue-resolution chains.
1. Reflection/trajectory artifacts (phase-gated).

Rules:

1. Derived artifacts must retain provenance pointers.
1. Derived artifacts must not back-write into raw capture history.

## Stage 4: Global Rollup (Read-Only Index, ADR-213)

Purpose:

1. Cross-project lookup over project-owned chronicle ledgers.

Storage:

1. Global index DB (default): `~/.dopemux/global_index.sqlite`.
1. `projects` registry table.
1. `promoted_pointers` table with bounded summaries and metadata pointers.

Rules (ADR-213 Read-Only Guarantees):

1. Rollup reads project ledgers in **read-only mode** (SQLite URI: `file:path?mode=ro`)
1. Rollup stores pointers and bounded redacted summaries only.
1. **Rollup NEVER writes into project ledgers** (architectural invariant)
1. Rollup never overrides per-project truth.
1. Deterministic ordering: `ts_utc DESC`, `event_id ASC`.

**Critical Invariants**:

- Project ledger `repo_root/.dopemux/chronicle.sqlite` is **single source of truth**
- Global rollup is an **index only**, not a second authority
- Opening project ledgers with read-only SQLite connection prevents accidental writes
- Any attempt to write to project ledger from rollup code will fail with `OperationalError`

## Injection Contract

1. Injection is explicit only through tool/command calls.
1. No default auto-injection in capture, rollup, or retrieval pathways.
1. Responses must include provenance (`project_id`, `event_id`, timestamps).

## CLI Interface

### Global Rollup Commands

Build and query the global rollup index using the `dopemux memory rollup` command group:

**Build Index:**
```bash
dopemux memory rollup build --projects-file projects.txt
```

Creates or updates the global rollup index at `~/.dopemux/global_index.sqlite` by reading project ledgers in read-only mode.

**List Registered Projects:**
```bash
dopemux memory rollup list
```

Displays all projects registered in the global index with their repository roots and last-seen timestamps.

**Search Across Projects:**
```bash
dopemux memory rollup search "authentication" --limit 10
```

Searches promoted work log entries across all registered projects using LIKE patterns. Results include timestamp, event type, summary, and originating project.

**Options:**
- `--index-path PATH` - Override default global index location
- `--projects-file PATH` - Specify projects list (newline or JSON format)
- `--limit N` - Maximum search results (default: 10, max: 100)

### Read-Only Guarantees (ADR-213)

All global rollup operations follow these guarantees:

1. Project ledgers are opened in read-only mode (`file:path?mode=ro`)
1. Only pointers and bounded summaries are stored in global index
1. **No writes back to project ledgers occur** (architectural invariant)
1. Deterministic ordering is preserved: `ts_utc DESC`, `event_id ASC`
1. Project ledger remains single source of truth

**See**: ADR-213 for dual-capture design and global rollup guarantees

## Out of Scope (This Spec Version)

1. LLM-based promotion/summarization.
1. Embedding-based global semantic retrieval.
1. Implicit prompt enrichment in any runtime path.
