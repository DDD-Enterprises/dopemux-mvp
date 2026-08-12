---
id: TP-DMX-PR-PREP-SPECIALIST-V2-001
title: Tp Dmx Pr Prep Specialist V2 001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Tp Dmx Pr Prep Specialist V2 001 (explanation) for dopemux documentation
  and developer workflows.
---
# Task Packet: TP-DMX-PR-PREP-SPECIALIST-V2-001 · PR Prep Specialist V2 Governance Migration

## Packet Identity

- **Packet**: TP-DMX-PR-PREP-SPECIALIST-V2-001 (R1)
- **Series**: DMX-PR-PREP-V2 (final packet)
- **Repository**: DDD-Enterprises/dopemux-mvp
- **Base branch**: main
- **Branch**: feat/pr-prep-specialist-v2-contract (continuation authorized, not recreated)
- **Execution agent**: codex (executed here by Claude, per operator instruction)
- **Provenance**: supervisor-generated in an external workspace; never previously
  committed to this repository prior to this packet's installation. Confirmed by
  full-repo grep and task-orchestrator FTS returning zero hits before installation.

## Objective

Migrate the active `pr-prep-specialist` governance contract from the stale
March seven-step / LOW-MEDIUM-HIGH / MERGE_READY model to the current
Dopemux L0-L3, resilient-drift, frozen-content-audit, proof-only-successor,
CI, PR Steward, and explicit-operator-gate model. Do not merge.

## Canonicality ruling (R1)

`docs/03-reference/pr-pipeline/prep/**` and `docs/03-reference/pr-pipeline/merge/**`
are the canonical PR-pipeline reference-contract surfaces. `docs/pr_prep/**`
and `docs/pr_merge/**` are compatibility-only. This is a supervisor ruling,
not a rediscovered repository fact — see `docs/03-reference/pr-pipeline/prep/operator-contract.md`
§10 for the full record.

## R1 amendment over the original (unfiled) proposal

- adds `docs/pr_merge/handoff-from-prps-contract.md` to the allowlist (the
  compatibility receiver must stay consistent with the canonical receiver);
- does **not** authorize `docs/pr_prep/contract-v2.md` — that file's
  creation was outside the original allowlist; it is removed via forward
  repair commit (not history rewrite) and its substance moved into
  `docs/03-reference/pr-pipeline/prep/operator-contract.md`.

## Execution record

See `proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/` for the S0-S3 evidence trail
(`BASELINE.json`, `CONSUMER_INVENTORY.md`, `DUPLICATE_PATH_MAP.json`,
`CONTRACT_DECISIONS.md`, `VALIDATION.json`, `CONTENT_HEAD.txt`).

**Stop point**: this packet freezes the repaired substantive content head
`C1` and stops. No independent audit, no PR creation, per explicit
instruction — those are S4+ and require a separate go-ahead.
