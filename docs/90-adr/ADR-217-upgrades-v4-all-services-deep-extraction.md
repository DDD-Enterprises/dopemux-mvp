---
id: ADR-217-UPGRADES-V4-ALL-SERVICES-DEEP-EXTRACTION
title: ADR 217 Upgrades V4 All Services Deep Extraction
type: adr
owner: '@hu3mann'
author: '@codex'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Define v4 all-services deep extraction contract and QA coverage gate.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - UPGRADES/v4/prompts/PROMPT_C10_SERVICE_CATALOG_DEEP.md
    - UPGRADES/v4/artifacts.yaml
    - services/registry.yaml
---
# ADR-217: UPGRADES v4 all-services deep extraction

## Status
- Accepted

## Date
- 2026-02-20

## Owners
- @hu3mann
- @codex

## Context
- Promptset audit identified incomplete service coverage risk in v3.
- Repo has a canonical service inventory in `services/registry.yaml`.
- v4 requires full-service extraction coverage as a hard gate.

## Decision
Add explicit v4 service-catalog contract:
- New deep extraction step: `C10` outputs `SERVICE_CATALOG.partX.json`.
- Canonical merged artifact: `SERVICE_CATALOG.json` promoted in phase `C`.
- QA artifact: `QA_SERVICE_COVERAGE.json` verifies registry-to-catalog completeness.

Required service fields:
- `service_id`, `category`, `description`
- `ports`, `health`
- `repo_locations`, `entrypoints`
- `interfaces`, `dependencies`, `config`

Coverage gate:
- Every `services[].name` in `services/registry.yaml` must appear exactly once in `SERVICE_CATALOG.json`.

Invariants:
- Service IDs are exact registry names.
- Catalog sorting is deterministic by `service_id`.
- Coverage QA reports missing services, duplicates, and missing required fields.

Non-goals:
- Runtime health probing of all services.
- Dynamic service discovery outside repository truth surfaces.

## Alternatives Considered
- Keep service extraction as optional.
  - Pros: lower cost.
  - Cons: leaves blind spots in architectural truth model.
  - Rejected: conflicts with all-services requirement.
- Cover only key services.
  - Pros: faster.
  - Cons: misses long-tail service drift.
  - Rejected: does not satisfy requested coverage depth.

## Consequences
- Phase `C` scope increases and produces richer service topology artifacts.
- Phase `Q` adds concrete service coverage gate.
- Downstream arbitration/task-packet quality improves due fuller service truth.

## Migration Strategy
- Step 1: add `C10` prompt and service catalog artifacts to v4 manifests.
- Step 2: generate deterministic service catalog during v4 sync.
- Step 3: emit `QA_SERVICE_COVERAGE.json` during v4 run sync.

## Verification
- Tests:
  - `UPGRADES/tests/test_run_extraction_v4_core.py`
- Commands:
  - `python UPGRADES/run_extraction_v4.py --phase C --run-id <RUN_ID> --dry-run`
  - `python UPGRADES/run_extraction_v4.py --phase Q --run-id <RUN_ID> --dry-run`
- Expected signals:
  - `SERVICE_CATALOG.json` exists under phase `C` norm.
  - `QA_SERVICE_COVERAGE.json` exists and reports deterministic coverage details.
