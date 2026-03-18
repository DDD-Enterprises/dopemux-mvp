---
id: ADR-216-UPGRADES-V4-RUNNER-LAYOUT-CLI-ENTRYPOINT
title: ADR 216 Upgrades V4 Runner Layout and CLI Entrypoint
type: adr
owner: '@hu3mann'
author: '@codex'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Define extraction v4 output layout and Dopemux CLI entrypoint strategy.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - UPGRADES/run_extraction_v4.py
    - src/dopemux/cli.py
---
# ADR-216: UPGRADES v4 runner layout and CLI entrypoint

## Status
- Accepted

## Date
- 2026-02-20

## Owners
- @hu3mann
- @codex

## Context
- v3 output layout is tied to `extraction/runs/<run_id>/...`.
- v4 needs side-by-side operation without destabilizing v3.
- Users need a single canonical interface in `dopemux` CLI.

## Decision
Adopt a side-by-side v4 runner and output root:
- Runner: `UPGRADES/run_extraction_v4.py`.
- v4 run root: `extraction/v4/runs/<run_id>/`.
- v4 doctor root: `extraction/v4/doctor/`.
- v4 latest run pointer: `extraction/v4/latest_run_id.txt`.

CLI routing:
- `dopemux upgrades run` defaults to `--pipeline-version v4`.
- v3 remains available via `--pipeline-version v3`.
- `dopemux upgrades doctor`, `status`, `preflight`, and `promptset audit` invoke runner scripts directly.
- Legacy trace pipeline is preserved as `dopemux upgrades trace`.

Invariants:
- v4 does not mutate or replace v3 runner code paths.
- v4 stores per-step normalized outputs under `norm/by_step/<STEP_ID>/`.
- Canonical artifact promotion writes only canonical files to phase `norm/`.

Non-goals:
- Full v3-to-v4 execution engine rewrite.
- Removing v3 CLI compatibility.

## Alternatives Considered
- Replace v3 runner in place.
  - Pros: one runtime.
  - Cons: high blast radius and rollback risk.
  - Rejected: violates low-risk migration requirement.
- Keep only standalone scripts without dopemux CLI integration.
  - Pros: less CLI work.
  - Cons: inconsistent operator experience.
  - Rejected: conflicts with canonical CLI objective.

## Consequences
- Dual runner support adds short-term complexity but improves migration safety.
- CLI now exposes explicit v4 operational commands.
- v4 can iterate independently while v3 remains fallback.

## Migration Strategy
- Step 1: add v4 runner script and manifests.
- Step 2: wire `dopemux upgrades` commands to v4 default.
- Step 3: keep v3 flags/paths as fallback during transition.

## Verification
- Tests:
  - `UPGRADES/tests/test_run_extraction_v4_core.py`
- Commands:
  - `uv run python -m dopemux.cli upgrades run --pipeline-version v4 --dry-run --phase A`
  - `uv run python -m dopemux.cli upgrades status --pipeline-version v4 --json`
- Expected signals:
  - v4 runner starts without v3 replacement.
  - v4 output paths are under `extraction/v4/`.
