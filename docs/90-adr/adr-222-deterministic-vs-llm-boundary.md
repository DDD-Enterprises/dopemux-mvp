---
id: adr-222
title: ADR-222 - DCP Deterministic vs LLM Enforcement Boundary and Contract Promotion Ladder
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-13'
last_review: '2026-06-13'
next_review: '2026-09-13'
status: accepted
prelude: Defines the L0–L3 contract promotion ladder, version-precedence rules, and the surface table governing which DCP enforcement actions are deterministic (hard-block capable) versus llm_advisory (never blocks).
tags:
- dcp
- enforcement
- deterministic
- llm-advisory
- promotion-ladder
- contract-governance
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
  - adr-002
  - DMX-DCP-TOOLING-101
---

# ADR-222: DCP Deterministic vs LLM Enforcement Boundary and Contract Promotion Ladder

**Status**: Accepted
**Date**: 2026-06-13
**Owners**: @hu3mann
**Task Packet**: DMX-DCP-TOOLING-101
**Blocks**: contract promotion decisions in DMX-DCP-TOOLING series (102–115)

---

## Context

The DCP (Data Control Plane) maintains a set of contract schemas under `schemas/dcp/`. As the DCP matures, contracts progress from sketch-level design objects through full runtime wiring. Without a promotion ladder, the repo has no shared vocabulary for "how authoritative is this contract?" and no rules for when a contract may be enforced by a hard-blocking gate versus when it is advisory only.

Additionally, DCP enforcement is distributed across multiple surfaces — CI gates, pre-commit hooks, CLI tools, `.claude/commands` skills, and agent personas — with radically different blocking semantics. Without an explicit surface table, a probabilistic check (an LLM skill) might be mistaken for a deterministic red-lane block, violating the core DCP principle that no deny may live only in an LLM surface.

This ADR establishes:
1. The L0–L3 contract promotion ladder and its exit criteria.
2. The version-precedence rule linking `schema_version` (stability marker) and `contract_version` (semver operational version).
3. The 7-row deterministic-vs-LLM surface table.

---

## Decision

### 1. L0–L3 Contract Promotion Ladder

Each DCP contract (`schemas/dcp/*.schema.json`) occupies exactly one level at a time. Levels gate what enforcement is permitted and what a contract's `validation_state` may claim.

| Level | Name | Exit Criteria | Permitted Enforcement |
|-------|------|---------------|-----------------------|
| **L0** | DRAFT | Schema file exists; structural JSON Schema tests pass; `schema_version` ends `.v0`; `validation_state` = `PROVISIONAL_UNVERIFIED_ENFORCEMENT` or `DESIGN_ONLY` | Structural tests only; no runtime enforcement |
| **L1** | RECONCILED | L0 PLUS: shape has been verified against a repo artifact on `origin/main`; `validation_state` = `REPO_CROSS_CHECKED`; still at `.v0` | CI gate may run schema-round-trip tests; no runtime block |
| **L2** | WIRED | L1 PLUS: at least one `runtime_producer` AND one `runtime_consumer` listed in `manifest.json` that actually read/write the schema; CI gate exercises the producer→consumer coupling | CI gate exercises full path; deterministic enforcement permitted in non-merge gates (e.g. pre-commit) |
| **L3** | LOCKED | L2 PLUS: CI gate enforces on the enforcement-side path; schema file is under change-control lane (PR review required, not self-certifiable); `schema_version` bumped from `.v0` to `.v1`; `contract_version` semver bumped in `manifest.json` | Deterministic hard-block permitted in merge gate; contract version under strict change control |

**Invariants**:
- No contract may claim `LOCKED` `validation_state` while still at `.v0`.
- No L0/L1 contract may be used as the basis for a merge-blocking hard gate.
- Promotion from L2→L3 requires operator sign-off (CODEOWNERS gate, not self-certifiable by the implementing subagent).

### 2. Version-Precedence Rule

Two version fields govern each contract:

| Field | Location | Semantics |
|-------|----------|-----------|
| `schema_version` | `const` inside the `.schema.json` file itself | **Stability marker** — `.v0` = unstable/DRAFT; `.v1` = locked/change-controlled. This is the authority marker. A contract cannot exit L2 at `.v0`. |
| `contract_version` | `manifest.json` entry's `contract_version` | **Operational semver** — tracks the manifest entry's own revision history independently of the schema file. Allows manifest metadata to be updated without touching the schema file. |

**Precedence rule**: `schema_version` is the authority marker. When `schema_version` is `.v0`, the contract is UNSTABLE regardless of what `contract_version` says. Both fields bump together at the L2→L3 promotion: `schema_version` moves from `.v0` to `.v1`, `contract_version` moves from `0.x.y` to `1.0.0`.

### 3. Deterministic vs LLM Surface Table

**Governing axioms**:
- "A probabilistic guard is a vibe plane, not a red-lane gate."
- "No deny may exist only in an LLM surface."

Any enforcement that can produce a hard block on a code-change path MUST be implemented on a deterministic surface AND duplicated there if it also exists on an LLM surface.

| Surface | Enforcement Type | Block Capability | Notes |
|---------|-----------------|------------------|-------|
| `native_hooks.py` PreToolUse hook | **deterministic** | hard-block capable | Runs before every tool invocation; Python, synchronous, exit-code aware. Suitable for schema-level write guards. |
| pre-commit hooks | **deterministic** | local-only (CI duplicates) | Runs on developer workstation only; CI must duplicate any critical check. Not sufficient alone for merge-gating. |
| CI gates (`.github/workflows/`) | **deterministic** | AUTHORITY tier | Merge-blocking when required on protected branches. The only surface that satisfies L3 enforcement requirements without additional operator wiring. |
| `dopemux dcp` CLI | **deterministic** | non-zero-exit | Synchronous subprocess; exit code propagates to callers. Deterministic when schema validation is called inline. |
| `.claude/commands` skills | **llm_advisory** | never blocks | Produces natural-language guidance only. An LLM may hallucinate, defer, or misclassify. MUST NOT be the sole enforcement surface for any red-lane rule. |
| Personas and agents | **llm_advisory** | never blocks | Same as skills — advisory only. May refuse to act but cannot produce a hard system block. |
| PostToolUse / Stop hooks | **deterministic** | receipts only / no block | Record artifacts after the fact; cannot prevent the tool invocation that already completed. Useful for audit trails, not enforcement. |

---

## Consequences

- `manifest.json` MUST be updated whenever a contract promotion occurs (L0→L1, L1→L2, L2→L3). The manifest is the machine-readable source of truth for current level and validation state.
- The `test_contracts_consistency.py` test suite (`tests/dcp/`) enforces the manifest's internal consistency on every CI run.
- Contracts at L0/L1 that currently appear in `ci_gates` (e.g. `🔴 Run DCP red-lane gate (TP-DMX-DCP-CI-GATE-001)`) are exercised by schema-round-trip tests only; this is permitted. The CI gate name appearing in `ci_gates` does NOT imply merge-blocking enforcement — only L3 contracts with `enforcement_side: deterministic` carry that claim.
- Any future DCP surface that gates merges on a schema check must appear in this ADR's surface table before being wired.

---

## Alternatives Considered

**Single enforcement layer (CI-only)**: Rejected — pre-commit and PreToolUse hooks provide fast-feedback loops that reduce CI load and catch violations at the developer's workstation. The surface table allows all layers to coexist as long as the merge-blocking authority always rests on a deterministic surface.

**LLM-advisory promotion ladder**: Rejected — LLM evaluation of "is this contract REPO_CROSS_CHECKED?" is non-deterministic and ungatable. Promotion criteria must be testable with a `pytest` assertion.

**Merging `schema_version` and `contract_version` into one field**: Rejected — `schema_version` is owned by the schema file author and changes only at stability milestones; `contract_version` is owned by the manifest maintainer and tracks operational metadata. Merging them would couple two independent change frequencies.
