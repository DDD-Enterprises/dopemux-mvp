---
id: 08_phased_roadmap
title: 08_Phased_Roadmap
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 08_Phased_Roadmap (explanation) for dopemux documentation and developer workflows.
---
# Dope-Memory v1 — Phased Roadmap

## Phase 0 — Spec + Wiring (1-2 days)
Deliverables
- Event envelope finalized
- Event stream names standardized
- Workspace/instance/session ID strategy confirmed
- Docs/spec/dope-memory/v1/ committed

Exit criteria
- Producers can emit decision.logged and task.failed into EventBus

## Phase 1 — Chronicle Spine (Signal-to-Noise Proof)
Deliverables
1) SQLite canonical DB with:
- raw_activity_events
- work_log_entries
- issue_links
2) Postgres mirror with:
- dm_raw_activity_events
- dm_work_log_entries + tsvector index
- dm_issue_links
3) Ingestor + Redactor
4) Promotion engine (deterministic rules)
5) MCP server with:
- memory_search, memory_store, memory_recap, mark_issue, link_resolution, replay_session
6) Retention job for raw events

Scope constraints
- Promote ONLY high-signal event types listed in taxonomy.
- No AST-aware chunking.
- No embeddings needed inside Dope-Memory.
- No causal graph edges.

Exit criteria (must be true)
- Daily use does not create noise overload.
- "Where was I?" recap is correct and useful most of the time.
- Redaction proves no secrets stored.

## Phase 2 — Reflective Pulse + Trajectory
Deliverables
- reflection_cards generation (session end / idle trigger)
- memory.pulse emission every 30-60 minutes or on end
- trajectory_state store + deterministic boosting
- DopeContext indexing:
- curated work logs into a dedicated collection (worklog_index)
- Hybrid bundle retrieval mode (optional):
- fuse worklogs + decisions + semantic hits via deterministic RRF

Exit criteria
- Reflection cards accurately capture decisions/blockers/progress for typical sessions.
- Trajectory boost improves relevance without confusing ordering.

## Phase 3 — Causal Graph Mapping (AGE Proposals)
Deliverables
- AGE nodes: WorkLogEntry, ReflectionCard
- Edge proposal engine:
- FOLLOWED_BY
- RESULTED_IN (entry->decision)
- RESOLVED_BY (issue->resolution)
- LIKELY_CAUSED (entry->error), confidence + evidence
- Promote-edge workflow:
- proposed edges require explicit acceptance or strict heuristics

Exit criteria
- Proposed edges are explainable with evidence windows and confidence.
- No graph pollution from low-quality edges.

## Phase 4 — Flow-Aware Surfacing
Deliverables
- ADHD Engine focus-state integration
- Surfacing rules:
- Focus mode: blockers only unless asked
- Drift mode: current goal + last steps
- Recovery: recap on resume after interruption

Exit criteria
- Reduced interruptions in focus mode.
- Better "return-to-task" recovery.
