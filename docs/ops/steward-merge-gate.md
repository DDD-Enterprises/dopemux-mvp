---
id: steward-merge-gate
title: Steward Merge Gate
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Steward Merge Gate reference for PR Steward guarded merge specialist workflows.
---
# Steward Merge Gate

`dopemux_pr_merge_specialist.steward_gate.steward_gate` is a pure, local-only
guard over PR Steward artifacts. It does not call GitHub, mutate branches,
resolve threads, merge PRs, or enable governed automerge.

## Inputs

- `head_sha`: expected PR head SHA.
- `required_class`: `REMEDIATION` or `FINALIZATION`.
- `MERGE_READINESS.json`: emitted by PR Steward intake.
- independent embedded-audit `PROOF.json`.

## Fail-Closed Rules

The gate denies when:

- either artifact is missing or invalid JSON
- `required_class` is unsupported
- `head_sha` is absent
- requested head SHA, PR Steward `pr.head_sha`, PR Steward `proof.proof_head_sha`,
  and embedded-audit proof `head_sha` do not all match
- PR Steward readiness does not match the requested class
- PR Steward embedded-audit status or independent proof embedded-audit status is
  not `PASS` or `PASS_WITH_RISKS`
- either artifact timestamp is missing, invalid, future-dated, or older than TTL

## Readiness Classes

| Required class | Required PR Steward readiness |
|---|---|
| `REMEDIATION` | `NEEDS_IMPLEMENTER` |
| `FINALIZATION` | `READY` |

TP-DMX-STEWARD-GATE-201 only adds the guard library. It is not wired into
remediation, finalization, merge, thread-resolution, or GitHub mutation seams.
Those integrations are separate packets.
