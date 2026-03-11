---
id: ADR-218-REPO-TRUTH-EXTRACTOR-HARD-CUTOVER-NAMESPACE
title: ADR 218 Repo Truth Extractor Hard Cutover Namespace
type: adr
owner: '@hu3mann'
author: '@codex'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Hard cutover from UPGRADES runtime namespace to Repo Truth Extractor service identity.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - services/repo-truth-extractor/run_extraction_v3.py
    - services/repo-truth-extractor/run_extraction_v4.py
    - src/dopemux/cli.py
    - scripts/repo_truth_extractor_promptset_audit_v4.py
---
# ADR-218: Repo Truth Extractor hard cutover namespace

## Status
- Accepted

## Date
- 2026-02-20

## Supersedes
- ADR-215
- ADR-216
- ADR-217

## Context
- Active extraction runtime and prompt assets were under the `UPGRADES` namespace.
- Active CLI/API naming drift (`upgrades`, `--pipeline-version`) no longer matched intended service ownership.
- Output roots were split across legacy layouts, reducing operational clarity.
- Historical `UPGRADES_*` reports must remain preserved as archival evidence.

## Decision
Adopt a hard cutover to one active service identity: `Repo Truth Extractor`.

- Canonical code root is `services/repo-truth-extractor/`.
- `dopemux extractor` is the only active CLI group.
- `--engine-version {v3|v4}` replaces `--pipeline-version`.
- Active runners are:
  - `services/repo-truth-extractor/run_extraction_v3.py`
  - `services/repo-truth-extractor/run_extraction_v4.py`
- Active prompt roots are:
  - `services/repo-truth-extractor/prompts/v3/`
  - `services/repo-truth-extractor/promptsets/v4/`
- Active output roots are:
  - `extraction/repo-truth-extractor/v3/`
  - `extraction/repo-truth-extractor/v4/`
- `UPGRADES/` remains docs-only legacy content.

## Invariants
- No active extractor runtime code executes from `UPGRADES/`.
- No runtime `dopemux upgrades` alias is maintained.
- Historical artifacts and archived report names containing `UPGRADES` remain unchanged.
- Existing old run outputs are preserved and not migrated.

## Alternatives Considered
- Keep runtime aliases (`upgrades` + `extractor`) indefinitely.
  - Rejected: prolongs naming drift and operator confusion.
- Flatten v3 and v4 into one mixed engine path.
  - Rejected: weakens versioned invariants and complicates rollback.
- Keep active code in `UPGRADES/` and rename docs only.
  - Rejected: does not solve ownership clarity or governance enforcement.

## Consequences
- Operators must use `dopemux extractor` and `--engine-version`.
- Automation/scripts/tests/docs require namespace updates.
- Pre-commit enforcement blocks new executable/config files under `UPGRADES/`.

## Migration Strategy
- Move active extraction code, libs, prompts, promptsets, and tests into `services/repo-truth-extractor/`.
- Rename scripts to Repo Truth Extractor names and update internal paths.
- Cut over CLI group/flags and remove `upgrades` runtime interface.
- Update active docs/indexes to new paths and command examples.
- Keep `UPGRADES/` legacy docs with explicit README guardrails.

## Verification
- `PYTHONPATH=src python3 -m dopemux.cli extractor list --engine-version v4`
- `PYTHONPATH=src python3 -m dopemux.cli extractor run --engine-version v4 --phase A --dry-run --run-id rte_smoke_a`
- `PYTHONPATH=src python3 -m dopemux.cli extractor status --engine-version v4 --run-id rte_smoke_a`
- `python3 scripts/repo_truth_extractor_promptset_audit_v4.py --repo-root /Users/hue/code/dopemux-mvp --strict`
- `python3 -m pytest -q services/repo-truth-extractor/tests`
