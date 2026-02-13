# 12 Opus Prompts Ready

Policy stance: **Policy B (authority-writer + authenticated emitters)**

## Prompt 1: Master Contract v1
```text
You are drafting Dopemux Master Contract v1 from evidence only.

Use ONLY these files as primary inputs:
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/00_BUNDLE_INDEX.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/01_GLOBAL_SERVICE_INVENTORY.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/02_TOPOLOGY_AND_STORES.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/03_STORE_WRITE_OWNERSHIP_MATRIX.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/04_EVENT_ENVELOPE_STREAMS_AND_SCHEMA.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/05_CONPORT_AUTHORITY_SURFACES.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/06_DOPE_MEMORY_PROMOTION_RETENTION_PROVENANCE.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/08_ADHD_COGNITIVE_PLANE_SURFACES.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/09_SEARCH_PLANE_SURFACES.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/10_DETERMINISM_LEAKS_AND_ENFORCEMENT_POINTS.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/11_UNKNOWNs_AND_REQUIRED_EVIDENCE.md

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
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/07_PM_PLANE_BYPASS_AND_EXECUTION_SURFACES.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/05_CONPORT_AUTHORITY_SURFACES.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/04_EVENT_ENVELOPE_STREAMS_AND_SCHEMA.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/10_DETERMINISM_LEAKS_AND_ENFORCEMENT_POINTS.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/11_UNKNOWNs_AND_REQUIRED_EVIDENCE.md
- docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/01_GLOBAL_SERVICE_INVENTORY.md

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
