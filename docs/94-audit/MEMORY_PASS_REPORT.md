---
id: MEMORY_PASS_REPORT
title: Memory Pass Report
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-08'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: Memory Pass Report (explanation) for dopemux documentation and developer
  workflows.
---
# Memory Pass Report (Current Repo, Evidence-First)

Date: 2026-02-08
Repo: dopemux-mvp-llm-20260207-152347

This report describes what the current codebase actually implements for memory ingestion, promotion, redaction, storage, and injection. It treats historical archive docs as idea sources only.

## Findings (Observed)

### A) Memory components and lanes (what exists)

1) Dope-Memory (Working Memory Assistant service)
- Location: services/working-memory-assistant/
- Canonical store: SQLite via ChronicleStore
  - Schema file: services/working-memory-assistant/chronicle/schema.sql
  - Raw events table: raw_activity_events (short retention)
  - Curated table: work_log_entries (durable)
- Promotion engine:
  - services/working-memory-assistant/promotion/promotion.py
  - PROMOTABLE_EVENT_TYPES is an explicit allowlist:
    - decision.logged
    - task.completed
    - task.failed
    - task.blocked
    - error.encountered
    - workflow.phase_changed
    - manual.memory_store
  - Importance scores are deterministic (no LLM in Phase 1)

1) EventBus Consumer (Redis Streams)
- Location: services/working-memory-assistant/eventbus_consumer.py
- Input stream: activity.events.v1
- Output stream: memory.derived.v1
- Event classification:
  - HIGH_SIGNAL_EVENTS: decision.logged, task.completed, task.failed, task.blocked, error.encountered, manual.memory_store, workflow.phase_changed
  - HEARTBEAT_EVENTS: message.sent, file.opened, git.commit.created
- Only high-signal events are eligible for promotion; heartbeat events are raw-only.

1) Redaction gates (fail-closed)
- Spec: 05_promotion_redaction.md
- Implementation: services/working-memory-assistant/promotion/redactor.py
- Implements:
  - denylist path prefix hashing (for example .env, secrets/, .ssh/, id_rsa)
  - sensitive key dropping (password, api_key, token, authorization, cookie, etc.)
  - regex detectors for known secret shapes
  - payload size cap (64KB) with truncation

1) Dope-Context decision inclusion boundary
- Dope-Context can include decision results in unified search via an explicit bridge connector
- Connector: services/dope-context/src/integration_bridge_connector.py (you provided file)
- This is a separate lane from code/docs retrieval and should remain opt-in per workspace.

### B) Storage and determinism

- SQLite is canonical for Dope-Memory chronicle data (ChronicleStore).
- Promotion is deterministic:
  - allowlisted event types only
  - deterministic importance scores
  - no LLM-based promotion in Phase 1
- Redaction is deterministic and applied before persistence and again before promotion (per spec).

### C) Injection surfaces (how memory can enter a model context)

Observed injection candidates:
1) Explicit memory query tools:
   - Dope-Memory exposes memory_search / memory_recap / memory_trajectory style endpoints (see dope_memory_main.py).
2) Derived events stream:
   - memory.derived.v1 can feed downstream consumers (for example dashboards or orchestrators).
3) Dope-Context unified search:
   - search_all can include decision-like artifacts via bridge (must be opt-in).

Key principle already present in code: promotion and derived outputs are bounded and typed. The system avoids free-form LLM "summarize and store everything" as a default.

## Overlap and collision map (Trinity view)

- Dope-Context: retrieval/indexing (code + docs + optional decisions)
- Dope-Memory: event-derived chronicle (raw + curated)
- ConPort: decision store / knowledge base (present in docker/mcp-servers/conport and bridge)

Collision risks:
1) Decision duplication:
   - decision.logged promoted into Dope-Memory work_log_entries
   - the same decision may also exist in ConPort and be retrieved via bridge into Dope-Context
   Mitigation: label decision sources, dedupe by stable ids if available, and keep injection per-lane opt-in.

2) "Unified search" overreach:
   - search_all is powerful; if default settings include decisions without clear labeling, it can confuse users and agents.
   Mitigation: keep decision inclusion opt-in and clearly labeled in output.

3) Derived stream feedback loops:
   - memory.derived.v1 events should not be re-ingested as raw activity events without guardrails.
   Mitigation: enforce source allowlists and loop detection (source field).

## Conflicts vs non-negotiables (Dope-Memory v1)

Top-3 check:
1) SQLite canonical: satisfied (ChronicleStore and schema.sql)
2) Fail-closed redaction: satisfied (spec + Redactor implementation)
3) Deterministic ranking + cursor pagination: partially satisfied
   - Promotion is deterministic
   - Cursor pagination exists in Dope-Memory search implementation (dope_memory_main.py has encode/decode cursor functions)
   - Still needs explicit documentation of ordering and tie-break rules in the public API contracts

## What we do not know (UNKNOWN)

- Whether any downstream consumer currently auto-injects memory.derived.v1 into model prompts without explicit lane opt-in.
- The exact dedupe key strategy across Dope-Memory and ConPort (do ids align, or do we need hashing).
- The authoritative "lane router" implementation location (ToolOrchestrator vs agent prompts vs MCP broker selection).

## Next actions (conservative)

1) Document lane boundaries and opt-in injection in a single ADR (ADR-212 below).
2) Update public API contracts for Dope-Memory search ordering and cursor semantics.
3) Add a loop guard rule: do not re-ingest memory.derived.v1 into activity.events.v1.

## Stop conditions

Stop and request evidence if any of the following are true:
- A service is observed injecting derived memory into prompts by default without an opt-in flag.
- ConPort and Dope-Memory both store the same decision without stable ids (cannot dedupe deterministically).
- Any redaction failure is detected (secrets or credential paths stored in plaintext).
