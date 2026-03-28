---
id: pr-merge-queue-orchestration
title: PR Merge Queue Orchestration
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-27'
next_review: '2026-06-20'
prelude: Design rationale for speculative train handling, validation-first states, and global CI remediation in the PR Merge Specialist.
---
# PR Merge Queue Orchestration

The PR Merge Specialist now separates three concerns that previously blurred together in the operator loop:

1. local validation readiness
1. GitHub queue and check lag
1. shared CI failure remediation

## Why Validation and Queue State Are Separate

The dashboard distinguishes `validation_pending`, `approval_required`, and `queued` because those states imply different operator actions:

- `validation_pending` means the branch still needs local proof before it can be treated as merge-ready.
- `approval_required` means code is otherwise ready, but policy still requires reviewer consent.
- `queued` means local work is done and the branch is waiting on GitHub's merge machinery.

This separation prevents auto-merge branches from looking idle when they still require local verification, and it avoids showing validation-only work as if it were blocked by unrelated policy failures.

The inverse also matters: a local validation pass must not erase a failing required GitHub check. Required remote check failures stay blocking until GitHub reports them green. Local proof and provider truth remain separate authorities.

## Why the Speculative Train Rebases onto `origin/main`

Earlier speculative chaining rebased later PRs on top of earlier candidate branches. That increases throughput in a purely local stack model, but it interacts poorly with GitHub's native merge queue because each rebased head becomes dependent on another non-canonical branch state.

The current train behavior instead rebases every candidate against the latest `origin/main`:

- every speculative attempt starts from the canonical integration base
- one failing candidate does not invalidate the rest of the train
- GitHub's own queue remains the authority for final ordering and merge execution

This makes the train advisory and throughput-oriented rather than a second merge authority.

## Why Global CI Remediation Exists

When multiple PRs fail on the same CI signature, per-branch remediation duplicates work and increases conflict pressure. The orchestrator now computes a stable failure fingerprint from the failing validation step and its error output, then uses that fingerprint to:

- detect repeated failures across the queue
- look for an existing `global-ci-fix` PR
- create one fix PR against `main` when the failure is systemic

Blocked PRs remain branch-local records, but the actual systemic repair is centralized in one remediation branch and one PR.

When the shared failure lives in `main` or in branch-protection workflows, the correct remediation target is still `main`; branch-local queue artifacts must remain blocked until the shared fix lands and the PR branch is updated onto that new base.

## Why the Specialist Uses a Strict Runbook

The `ci-remediation-specialist` is intentionally constrained:

1. reproduce the failure first
1. prefer ecosystem auto-fixers
1. make a surgical edit only when needed
1. re-run the failing command

That constraint keeps the remediation path auditable and reduces the chance that queue automation mutates unrelated code while trying to fix CI opportunistically.

## Operational Consequence

In this design:

- GitHub remains the merge authority
- local validation remains the readiness proof
- the dashboard remains an operator surface, not a source of merge truth
- the global remediation path exists only for failures that are demonstrably shared across multiple PRs
- bounded execute runs (`--max-prs`, `--max-passes`) are operator safety rails and must be honored exactly
