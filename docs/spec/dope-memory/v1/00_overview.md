---
id: 00_overview
title: 00_Overview
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Dope-Memory v1 — Overview

## Purpose
Dope-Memory provides the temporal spine and working-context narrative for Dopemux:
- "What happened, when, and why?"
- "Where was I?"
- "What are the last 3 steps and current constraints?"

It is designed to integrate with:
- DopeQuery (ConPort + ConPort-KG): structured truth + decision genealogy
- DopeContext: semantic archival retrieval for code/docs/history
- EventBus: activity stream ingestion and derived event publishing
- ADHD Engine: focus-state gating (Phase 4)

## Principles (Non-Negotiables)
1) No duplication
   - Dope-Memory is not a second DopeQuery or DopeContext.
   - Dope-Memory stores temporal narrative and derived summaries, not canonical facts.

2) ADHD-first output boundary
   - All default outputs return Top-3 items max.
   - Additional results only on explicit pagination/expand.

3) Redaction before persistence (strict)
   - Secrets/PII must be scrubbed before writing to storage.
   - Redaction applies at raw ingestion and again at promotion/curation.

4) Local-first canonical
   - SQLite is canonical for the Chronicle store.
   - Postgres is a mirrored substrate for query speed and multi-service access.
   - Mirroring must be idempotent and tolerant of partial failures.

5) Deterministic tool outputs
   - Stable schemas.
   - Stable sorting and tie-breakers.
   - Cursor-based pagination with opaque tokens.

## Trinity Placement
- DopeContext (Archival/Semantic): "What did we do last month?"
- DopeQuery (Structured/Graph): "Why are these connected?"
- Dope-Memory (Temporal/Working): "What am I doing right now, and what led here?"

## Cognitive Tiers and Phases
Phase 1 — Chronicle Spine
- Ingest raw events (7 day retention).
- Promote only high-signal events into curated work logs.
- Deterministic keyword search + filters.
- MCP tools with Top-3 boundary.

Phase 2 — Reflective Pulse
- Session reflections ("Reflection Cards") generated at session end or idle trigger.
- Trajectory-aware re-ranking (boost active stream).
- Index curated work logs into DopeContext as a dedicated collection.

Phase 3 — Causal Graph Mapping
- Propose edges in AGE with confidence + evidence windows.
- "Promote edge" workflow (never auto-truth by default).

Phase 4 — Flow-Aware Surfacing
- Integrate ADHD Engine focus states.
- Suppress proactive surfacing in focus mode.
- Provide recovery prompts in drift/recovery modes.

## Data Stores
SQLite (Canonical)
- raw_activity_events (short retention)
- work_log_entries (curated)
- reflection_cards (Phase 2)
- issue_links (issue/resolution graph, Phase 1+)
- trajectory_state (Phase 2+)

Postgres (Mirror)
- dm_* mirror tables, JSONB + GIN indexes
- summary_tsv for fast keyword search

AGE (Graph, Phase 3+)
- WorkLogEntry, ReflectionCard nodes
- FOLLOWED_BY, RESULTED_IN, RESOLVED_BY, LIKELY_CAUSED edges

## Success Criteria
Phase 1 success:
- You can ask "where was I?" and get a correct Top-3 recap.
- The curated log remains high-signal (no drowning in file-save noise).
- Retrieval is deterministic and fast.
- Redaction demonstrably prevents secret leakage into logs.

Phase 2 success:
- Reflection Cards capture decisions/blockers/progress accurately.
- Trajectory boosts improve relevance without causing confusion.

Phase 3 success:
- Proposed causal edges are useful and explainable with evidence windows.

Phase 4 success:
- Context appears only when it helps; minimal interruption.
