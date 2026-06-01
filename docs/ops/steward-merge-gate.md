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

## Remediation Wiring

TP-DMX-MERGE-REMEDIATION-202 wires `steward_gate(REMEDIATION)` into the
remediation mutation seams in `dopemux_pr_merge_specialist.queue_drain`:

- review-thread implementation, rationale replies, and agentic thread fixes
- mechanical conflict recovery after rebase failure
- local validation and reproduced remote-check AI remediation
- shared global-fix PR creation policy

Remediation requires fresh local `MERGE_READINESS.json` and `PROOF.json`
artifacts for the exact PR head SHA. The PR Steward readiness must be
`NEEDS_IMPLEMENTER`, both embedded-audit statuses must be `PASS` or
`PASS_WITH_RISKS`, and `MERGE_READINESS.json.blockers` must contain at least one
implementer-owned blocker such as `UNRESOLVED_REVIEW_THREAD`, `FAILED_CHECK`,
`REQUEST_CHANGES`, or `REVIEW_ITEM_MUST_FIX`.

When the remediation gate denies, queue drain records
`STEWARD_REMEDIATION_GATE.json`, sets `operator_state` to
`steward_remediation_blocked`, and does not launch Gemini, apply review-thread
changes, create shared global-fix PRs, or perform conflict auto-recovery.

Thread resolution remains outside TP-DMX-MERGE-REMEDIATION-202. Remediation may
reply and push verified fixes, but resolving review threads is deferred to the
finalization packet.

Shared global-fix PR creation is disabled when `steward_gate` policy is present
unless `steward_gate.allow_global_fix_prs` is explicitly `true`.

TP-DMX-STEWARD-GATE-201 only added the guard library. TP202 wires remediation
seams only; finalization, merge execution, governed automerge, and review-thread
resolution remain separate packet work.

## Finalization Wiring

TP-DMX-MERGE-FINALIZATION-203 wires `steward_gate(FINALIZATION)` into the
merge execution path. A live merge attempt through `_merge_prepared_result`
must find fresh local `MERGE_READINESS.json` and `PROOF.json` artifacts for the
exact PR head SHA, PR Steward readiness `READY`, and strict independent
embedded-audit status `PASS` in both artifacts. `PASS_WITH_RISKS` remains
acceptable for remediation and general acceptance evidence, but does not grant
finalization authority.

When the finalization gate denies, queue drain writes
`STEWARD_FINALIZATION_GATE.json` and stops before merge execution. Direct merge
uses GitHub GraphQL `mergePullRequest` with `expectedHeadOid`; if the head SHA
or GraphQL merge authority is unavailable, the merge result is blocked with
`UNKNOWN` evidence and does not fall back to ungated `gh pr merge`.

Governed automerge remains disabled by default with
`merge.allow_governed_automerge: false`. Admin-bypass squash remains blocked
unless a later supervised packet adds explicit authorization and proof handling.
