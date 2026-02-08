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

## Stage 0: Capture

Inputs:

1. Claude hook/plugin adapter events.
2. CLI/MCP trigger adapter events.

Storage:

1. Canonical per-project SQLite ledger:
   `repo_root/.dopemux/chronicle.sqlite`.
2. Table: `raw_activity_events`.

Rules:

1. Resolve repo root deterministically (`.git` or `.dopemux` marker).
2. Redact payload before persistence.
3. Generate deterministic `event_id` for retry-idempotency.
4. Use duplicate-safe insert semantics (`INSERT OR IGNORE`).

## Stage 1: Normalize

Inputs:

1. Redacted raw events from `raw_activity_events`.

Storage (implementation-flexible):

1. In-memory normalization or optional normalized table.

Rules:

1. Deterministic transforms only.
2. No probabilistic ranking or heuristic mutation.
3. Preserve stable provenance fields (`workspace_id`, `instance_id`,
   `session_id`, `event_id`).

## Stage 2: Promote

Inputs:

1. Normalized event stream from Stage 1.

Storage:

1. Table: `work_log_entries` (durable curated history).

Rules:

1. Promotion allowlist is deterministic and explicit.
2. Promotion-level redaction remains fail-closed.
3. Stable ordering for retrieval remains deterministic:
   `importance_score DESC`, `ts DESC`, `id ASC`.

## Stage 3: Derive

Inputs:

1. Curated `work_log_entries`.

Outputs (deterministic products):

1. Session recaps.
2. Issue-resolution chains.
3. Reflection/trajectory artifacts (phase-gated).

Rules:

1. Derived artifacts must retain provenance pointers.
2. Derived artifacts must not back-write into raw capture history.

## Stage 4: Global Rollup (Read-Only Index)

Purpose:

1. Cross-project lookup over project-owned chronicle ledgers.

Storage:

1. Global index DB (default): `~/.dopemux/global_index.sqlite`.
2. `projects` registry table.
3. `promoted_pointers` table with bounded summaries and metadata pointers.

Rules:

1. Rollup reads project ledgers in read-only mode.
2. Rollup stores pointers and bounded redacted summaries only.
3. Rollup never writes into project ledgers.
4. Rollup never overrides per-project truth.
5. Deterministic ordering: `ts_utc DESC`, `event_id ASC`.

## Injection Contract

1. Injection is explicit only through tool/command calls.
2. No default auto-injection in capture, rollup, or retrieval pathways.
3. Responses must include provenance (`project_id`, `event_id`, timestamps).

## Out of Scope (This Spec Version)

1. LLM-based promotion/summarization.
2. Embedding-based global semantic retrieval.
3. Implicit prompt enrichment in any runtime path.
