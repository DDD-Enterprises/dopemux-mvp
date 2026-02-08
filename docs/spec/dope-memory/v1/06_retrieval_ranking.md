---
id: 06_retrieval_ranking
title: 06_Retrieval_Ranking
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 06_Retrieval_Ranking (explanation) for dopemux documentation and developer
  workflows.
---
# Dope-Memory v1 — Retrieval + Ranking

## Phase 1 Retrieval: Deterministic Keyword First
Source: dm_work_log_entries.summary_tsv (Postgres) or LIKE fallback in SQLite.

### Query normalization
- trim
- ASCII normalize
- collapse whitespace to single spaces
- lower-case for keyword parsing

### Filtering
Always apply:
- workspace_id AND instance_id
Optionally apply:
- session_id
- category
- entry_type
- workflow_phase
- tags_any overlap
- time_range: today/week/month/all

### Ranking (Deterministic)
Phase 1 ranking order:
1) importance_score DESC
2) ts DESC
3) id ASC

No semantic vectors, no rerankers, no probabilistic reorder in Phase 1.

### Pagination
Cursor token contains:
- last_seen tuple: (importance_score, ts, id)
- filter scope hash
Server must reject cursor if scope hash mismatches.

## Phase 2 Retrieval: Trajectory Boosting
Trajectory state includes:
- current_stream: string
- current_goal: optional
- last_steps: last 3 entry ids

Boost logic:
- if tags contain "stream:{current_stream}" => +0.2
- if entry is within last 2 hours => +0.1
- if entry linked to current_goal => +0.2

Phase 2 ranking uses a composite numeric score but remains deterministic:
```
FinalScore = BaseScore + TrajectoryBoost + RecencyBoost
```
where:
- BaseScore = importance_score / 10.0
- TrajectoryBoost as above
- RecencyBoost = clamp(0.0, 0.2, 0.2 / (1 + hours_old))

Tie-breakers remain:
- ts DESC
- id ASC

## Phase 2/3 Hybrid Bundle Across Trinity (Optional Tool Mode)
When memory_search is invoked with sources including:
- "worklog" (Dope-Memory)
- "decisions" (DopeQuery)
- "semantic" (DopeContext)

Return a fused bundle:
- retrieve top N candidates per source (N=20)
- apply RRF fusion (k=60)
- apply ADHD Top-3 boundary

RRF is deterministic.

## ADHD Boundary Enforcement
Every tool must return:
- items: max top_k (default 3)
- more_count: total_matches - len(items)
- next_token: optional

Never return more than 3 unless top_k explicitly provided and <= 10.

## Time Range Definitions (UTC)
- today: [00:00Z, now]
- week: [now-7d, now]
- month: [now-30d, now]
- all: unbounded

## Performance Targets
Phase 1:
- p50 < 50ms for keyword search on recent data
- p99 < 250ms

Phase 2:
- p50 < 100ms
- p99 < 500ms
