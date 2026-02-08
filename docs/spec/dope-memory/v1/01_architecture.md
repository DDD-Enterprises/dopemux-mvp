---
id: 01_architecture
title: 01_Architecture
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 01_Architecture (explanation) for dopemux documentation and developer workflows.
---
# Dope-Memory v1 — Architecture

## Service Responsibilities

### Dope-Memory owns
1) Chronicle store
   - Raw activity events (short retention)
   - Curated work log entries (durable)

2) Promotion + redaction engine
   - Ingest raw events from EventBus
   - Redact sensitive content
   - Promote only high-signal events to curated log (Phase 1 rule set)

3) Retrieval + ranking
   - Phase 1: deterministic keyword search + filters
   - Phase 2+: trajectory boosts, hybrid bundles across Trinity

4) MCP interface
   - Exposes stable tool contracts for search/store/recap/issues/replay

### Dope-Memory integrates with (but does not own)
- DopeQuery (ConPort): decisions, tasks, rationale, genealogy
- ConPort-KG (AGE): structured graph of decisions and long-term relationships
- DopeContext (Qdrant): semantic archival retrieval and indexing
- EventBus (Redis Streams): event ingestion + derived event publication
- ADHD Engine: focus-state gating

## Component Diagram (Conceptual)

Event Producers
- Workspace watcher
- Git watcher
- TaskMaster
- DopeQuery/ConPort hooks
- Test runner / CI reporter
- Manual tool calls (memory_store, mark_issue, etc)

EventBus (Redis Streams)
- Stream: activity.events.v1
- Stream: memory.derived.v1

Dope-Memory
- Ingestor: subscribes to activity.events.v1
- Redactor: scrubs payload
- Raw store: writes raw_activity_events (SQLite canonical)
- Promotion engine: selects events to curate
- Curated store: writes work_log_entries (SQLite canonical)
- Mirror worker: upserts to Postgres dm_* tables (idempotent)
- Retrieval engine: keyword search + filters
- MCP server: exposes tools

Downstream
- DopeContext indexer: indexes curated work logs (Phase 2)
- DopeQuery learning importer: accepts promoted learning nodes (Phase 2+)
- AGE edge proposal engine: proposes causal edges (Phase 3+)
- ADHD engine: gates surfacing (Phase 4)

## IDs and Partitioning
All stored objects must include:
- workspace_id: stable ID of a workspace
- instance_id: worktree/instance key (e.g., "A", "B")
- session_id: optional (may be absent for some system events)

Every query must scope by workspace_id and instance_id at minimum.

## Phase 1 Minimal Event Policy (to avoid noise)
Phase 1 promotion MUST be high-signal only:
- decision.logged (from DopeQuery)
- task.completed / task.failed / task.blocked (TaskMaster)
- error.encountered (test runner / CI)
- workflow.phase_changed (explicit transitions)
- manual.memory_store (user-initiated)
All other events are stored as raw only.

## Data Lifecycle
Raw events
- Retention: default 7 days
- Purpose: correlation windows for issues and reflection context
Curated entries
- Durable
- Purpose: narrative and retrieval
Reflections (Phase 2)
- Durable, derived from curated entries

## Capture Adapters and Canonical Ledger
- Canonical per-project ledger path: `repo_root/.dopemux/chronicle.sqlite`
- Repo root resolution is deterministic:
  - Walk upward from current path
  - First match of `.git/` or `.dopemux/` is authoritative
  - If no marker exists, capture fails closed with a user-visible error
- Capture adapters must write through one shared capture client:
  - `plugin` (Claude hook capture)
  - `cli` (Dopemux CLI capture)
  - `mcp` (MCP/bridge capture)
  - `auto` (context-driven selection)
- Capture writes append-only `raw_activity_events` with:
  - redaction before persistence
  - deterministic idempotency key (`event_id`)
  - duplicate-safe inserts (`INSERT OR IGNORE`)
- Injection policy remains explicit:
  - Capture does not auto-inject prompt context
  - Retrieval/injection is controlled by explicit tool calls only

## Determinism Requirements
Ordering
- Primary: importance_score DESC
- Secondary: ts DESC
- Tertiary: id ASC (stable tie-breaker)

Pagination
- Cursor token must encode:
  - last_sort_tuple (importance_score, ts, id)
  - scope (workspace_id, instance_id, session_id, filters)
Cursor token is opaque to callers (base64 JSON, signed if needed).

Normalization
- All tool inputs are ASCII-normalized and trimmed.
- Timestamps are stored in UTC ISO8601 in SQLite, TIMESTAMPTZ in Postgres.

## Failure Modes and Handling
- EventBus lag: process with at-least-once; store idempotently using id key.
- Postgres down: continue writing to SQLite; queue mirror retries.
- Redaction failures: fail closed (drop/strip) rather than persist unredacted.
- Duplicate events: dedupe by event id.
