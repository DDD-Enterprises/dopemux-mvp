---
id: UPGRADES_V4_GOLDEN_RUN_CHECKLIST_2026-02-20
title: UPGRADES V4 Golden Run Checklist
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Regression checklist for comparing v3 and v4 extraction behavior on one commit.
---
# UPGRADES v4 golden run checklist (2026-02-20)

## Objective

Validate that v4 achieves strict determinism and full-service coverage while preserving v3 fallback.

## Pre-flight

- Promptset lint passes:
  - `python scripts/upgrades_promptset_audit_v4.py --strict`
- Providers healthy:
  - `dopemux upgrades preflight --pipeline-version v4 --auth-doctor`

## Run matrix

1. Baseline v3 run:
   - `dopemux upgrades run --pipeline-version v3 --phase ALL --run-id golden_v3_001 --execute --resume`
2. v4 run #1:
   - `dopemux upgrades run --pipeline-version v4 --phase ALL --run-id golden_v4_001 --execute --resume`
3. v4 run #2 (same commit/config):
   - `dopemux upgrades run --pipeline-version v4 --phase ALL --run-id golden_v4_002 --execute --resume`

## Checks

### 1) Service coverage

- `extraction/v4/runs/golden_v4_001/Q_quality_assurance/qa/QA_SERVICE_COVERAGE.json`
- Pass criteria:
  - `status == PASS`
  - `missing_services == []`
  - `duplicate_services == []`

### 2) Canonical collision policy

- For each phase:
  - `extraction/v4/runs/golden_v4_001/<phase>/qa/PHASE_<PHASE>_COLLISIONS.json`
- Pass criteria:
  - each file reports `status == PASS`
  - `collisions == []`

### 3) Determinism of canonical norm artifacts

- Compare hashes for all canonical norm files between runs:
  - `extraction/v4/runs/golden_v4_001/*/norm/*.json`
  - `extraction/v4/runs/golden_v4_002/*/norm/*.json`
- Pass criteria:
  - identical file sets
  - identical sha256 for each matching path

### 4) v3 fallback continuity

- `dopemux upgrades status --pipeline-version v3 --run-id golden_v3_001`
- Pass criteria:
  - run status is healthy and complete
  - no regression in v3 invocation path

## Notes

- If any check fails, attach run IDs and relevant QA artifact paths to the failure report.
