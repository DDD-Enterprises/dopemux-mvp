---
id: 12_OPUS_PROMPTS_READY
title: 12 Opus Prompts Ready
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: 12 Opus Prompts Ready (explanation) for dopemux documentation and developer
  workflows.
---
# 12 Opus Prompts Ready

Policy stance: **Policy B (authority-writer + authenticated emitters)**

## Prompt 1: Master Contract v1
```text
You are drafting Dopemux Master Contract v1 from evidence only.

Use ONLY these files as primary inputs:
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/00-bundle-index.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/01-global-service-inventory.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/02-topology-and-stores.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/03-store-write-ownership-matrix.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/04-event-envelope-streams-and-schema.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/05-conport-authority-surfaces.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/06-dope-memory-promotion-retention-provenance.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/08-adhd-cognitive-plane-surfaces.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/09-search-plane-surfaces.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/10-determinism-leaks-and-enforcement-points.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/11-unknowns-and-required-evidence.md

Hard rules:
1) No invention. If evidence missing, output UNKNOWN.
2) Use Policy B: only designated authority-writer services may mutate authority stores.
3) Require authenticated emitters for authority-impacting events.
4) Distinguish authority records vs temporal memory vs coordination state vs search cache.
5) Every normative clause must cite one or more evidence file paths.

Output format:
A) Contract scope and glossary
B) Authority model (writers/readers per store)
C) Event contract (envelope + streams + auth)
D) Determinism guarantees and explicit non-guarantees
E) Enforcement controls (code/config/tests)
F) Migration plan with staged gates
G) UNKNOWNs carried forward

If UNKNOWNs from file 11 block a normative clause, mark clause as PROVISIONAL and include exact evidence acquisition step.
```

## Prompt 2: PM Plane Constitution + Tier-0 Refactor
```text
Produce a PM Plane Constitution and Tier-0 Refactor plan from evidence only.

Primary inputs:
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/07-pm-plane-bypass-and-execution-surfaces.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/05-conport-authority-surfaces.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/04-event-envelope-streams-and-schema.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/10-determinism-leaks-and-enforcement-points.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/11-unknowns-and-required-evidence.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/01-global-service-inventory.md

Policy target:
- PM plane is coordination-first.
- Authority writes must go through authenticated authority-writer surfaces.
- Tool execution and LLM calls must be explicitly gated and auditable.

Required output:
1) Constitution clauses (MUST/SHOULD/MUST NOT) with citations.
2) Tier-0 refactor backlog with severity and sequence:
- Close unauthenticated emitter surfaces
- Remove/guard direct authority bypasses
- Enforce idempotent write API contract
- Normalize event envelope and stream topology
- Add deterministic mode for retrieval
3) Acceptance tests and CI gates per clause.
4) Rollback strategy.
5) Explicit PROVISIONAL tags for clauses blocked by UNKNOWNs.

Do not propose architecture outside evidence. Use UNKNOWN where unresolved.
```
