---
id: ADR-215-UPGRADES-V4-PROMPT-ARTIFACT-CONTRACTS
title: ADR 215 Upgrades V4 Prompt Artifact Contracts
type: adr
owner: '@hu3mann'
author: '@codex'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Freeze UPGRADES v4 prompt and artifact contracts for deterministic extraction.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - UPGRADES/v4/promptset.yaml
    - UPGRADES/v4/artifacts.yaml
    - scripts/upgrades_promptset_audit_v4.py
---
# ADR-215: UPGRADES v4 prompt and artifact contracts

## Status
- Accepted

## Date
- 2026-02-20

## Owners
- @hu3mann
- @codex

## Context
- v3 prompt quality is uneven; multiple prompts are schema-light stubs.
- v3 normalized artifacts can be overwritten by later steps using the same output filename.
- Determinism is weakened when timestamps are embedded in norm artifacts.
- Evidence requirements are inconsistent across prompts.

## Decision
UPGRADES v4 introduces a contract-first promptset and artifact registry:
- Prompt contract is required and linted (Goal, Inputs, Outputs, Schema, Evidence Rules, Determinism Rules, Anti-Fabrication Rules, Failure Modes).
- Artifact contract is centralized in `UPGRADES/v4/artifacts.yaml`.
- Norm artifacts are timestamp-free and deterministic.
- Evidence uses repo-relative `path`, `line_range`, and `excerpt`.

Invariants:
- Every v4 prompt must satisfy required prompt sections.
- Every declared output must exist in the v4 artifact registry.
- Norm artifacts cannot include forbidden temporal keys.
- Promptset ordering is numeric (for example `C9` before `C10`).

Non-goals:
- Rewriting v3 prompt corpus in place.
- Auto-running synthesis (phase `S`) via providers.

## Alternatives Considered
- Keep v3 prompts and only add runner checks.
  - Pros: least immediate work.
  - Cons: leaves prompt quality and evidence gaps unresolved.
  - Rejected: does not close root-cause quality drift.
- Keep timestamps in norm and filter only during diff.
  - Pros: lower migration effort.
  - Cons: deterministic artifacts remain noisy by default.
  - Rejected: weakens fail-closed determinism goals.
- No centralized artifact registry.
  - Pros: lower upfront schema overhead.
  - Cons: output contract drift remains likely.
  - Rejected: incompatible with deterministic governance.

## Consequences
- Prompt authoring quality bar increases and becomes machine-checkable.
- New promptset lint workflow is required before running v4 pipeline.
- Artifact schema ownership becomes explicit and auditable.

## Migration Strategy
- Step 1: add `UPGRADES/v4/promptset.yaml` and `UPGRADES/v4/artifacts.yaml`.
- Step 2: generate v4 prompts under `UPGRADES/v4/prompts/` with contract sections.
- Step 3: enforce with `scripts/upgrades_promptset_audit_v4.py --strict`.

## Verification
- Tests:
  - `UPGRADES/tests/test_promptset_v4_lint.py`
- Commands:
  - `python scripts/upgrades_promptset_audit_v4.py --strict`
- Expected signals:
  - `status: PASS`
  - `stub: 0`
  - `lint_failures: 0`
