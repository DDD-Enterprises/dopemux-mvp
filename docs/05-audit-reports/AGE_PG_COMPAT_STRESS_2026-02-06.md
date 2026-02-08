---
id: AGE_PG_COMPAT_STRESS_2026_02_06
title: Age Pg Compat Stress 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Compatibility and concurrency stress validation results for postgres-age with ConPort public schema workload on 2026-02-06.
---
# AGE/PG Compatibility + Stress Validation (2026-02-06)

## Scope

Validate and evidence closure for:

1. `1.1.2: Run concurrent operations stress test`
2. `1.1.3: Validate AGE/PG compatibility`

## Runtime Execution

Validator script:

- `scripts/deploy/migration/validate_age_pg_compat_stress.py`

Executed against:

- `postgresql://dopemux_age@dopemux-postgres-age:5432/dopemux_knowledge_graph`
- workspace: `/Users/hue/code/dopemux-mvp`
- detected schema: `public`

Output artifact:

- `reports/strict_closure/age_pg_compat_stress_2026-02-06.json`

## Compatibility Results

1. Required runtime tables present: `decisions`, `progress_entries`, `custom_data`, `entity_relationships`, `workspace_contexts`.
2. `age` extension was available and then explicitly installed/registered (`extversion 1.6.0`).
3. `LOAD 'age'` succeeds.
4. Workspace row counts align with ConPort import expectations:
   decisions `294`, progress_entries `209`, custom_data `14`, entity_relationships `111`, workspace_contexts `1`.

## Concurrency Stress Results

Concurrency levels: `1, 5, 10, 20` with `60` iterations per worker.

1. Query failures: `0` across all runs.
2. P95 latency remained below `50ms` at all tested levels:
   `0.36ms`, `0.66ms`, `1.45ms`, `2.65ms`.
3. Throughput remained high under load:
   `~4.8k`, `~5.7k`, `~6.9k`, `~6.6k` qps.
4. Overall validator status: `overall_ok = true`.

## Closure Status

Both miss-matrix items are now evidenced as complete in this wave:

1. concurrent operations stress test: complete
2. AGE/PG compatibility validation: complete
