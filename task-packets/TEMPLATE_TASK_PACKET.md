---
id: TEMPLATE_TASK_PACKET
title: Template Task Packet
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Template Task Packet (explanation) for dopemux documentation and developer
  workflows.
---
# Task Packet: <ID> · <Subsystem> · <Short Title>

════════════════════════════════════════════════════════════

## Objective

One sentence. What outcome is required?

────────────────────────────────────────────────────────────

## Scope

IN:

* <explicit in-scope items>

OUT:

* <explicit out-of-scope items>

────────────────────────────────────────────────────────────

## Invariants (Must Remain True)

* <Invariant 1>
* <Invariant 2>
* <Invariant 3>

If an invariant appears impossible, stop and report.

────────────────────────────────────────────────────────────

## Plan (Numbered)

1. <Step 1>
1. <Step 2>
1. <Step 3>

Keep steps mechanical and verifiable.

────────────────────────────────────────────────────────────

## Files to Touch

* <path>
* <path>

If additional files are needed, stop and request approval.

────────────────────────────────────────────────────────────

## Exact Commands to Run

List commands exactly, one per line.

Example:

* rg -n "<pattern>" -S .
* python -m pytest -q <path>
* python -m compileall -q src services

────────────────────────────────────────────────────────────

## Output Capture Rules (Verbatim)

Implementer must return:

* git diff --stat
* git diff
* Command outputs verbatim
* Exit codes
* Any requested logs/artifacts

────────────────────────────────────────────────────────────

## Embedded Audit

Required when the packet touches governance, process, schema, prompt, proof, security, authority-boundary, or high-risk runtime surfaces.

Record:

* auditor tool and model
* exact invocation
* exit code
* report path
* findings
* fixes applied
* remaining risks
* skip reason when skipped

If no supported auditor executable is available or invocation cannot be proven from local help output, record `SKIPPED` and escalate instead of claiming READY.

────────────────────────────────────────────────────────────

## PR Steward Readiness

If a PR is opened, PR Steward must be the check-only review-intake gate.

Record:

* PR metadata, changed files, commits, and head SHA
* reviews, review comments, review threads, and issue comments
* check/CI state
* review item ledger
* thread dispositions
* `MERGE_READINESS` verdict

Stop if reviewers, bots, review items, threads, or checks cannot be classified. Do not mutate GitHub state from this packet template.

────────────────────────────────────────────────────────────

## Proof Bundle Expectations

Proof must include:

* repo identity and branch
* git status before and after
* files changed
* command outputs and exit codes
* validation results
* embedded audit object when required
* PR Steward readiness when a PR exists
* UNKNOWNs, blockers, and NOT_RUN items
* rollback plan

────────────────────────────────────────────────────────────

## Supervisor Review Skip Rule

Skip the second GPT-5.5 supervisor review only when embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS` and PR Steward readiness is `READY`.

Any `FAIL`, `NEEDS_SUPERVISOR`, `SKIPPED`, missing proof, unknown reviewer/bot, unclassified review item, unresolved blocking thread, failed required check, or stale proof requires escalation.

────────────────────────────────────────────────────────────

## Acceptance Criteria

* <Criterion 1>
* <Criterion 2>
* <Criterion 3>

Each criterion should be testable.

────────────────────────────────────────────────────────────

## Rollback Steps

* <Rollback 1>
* <Rollback 2>

Keep rollback explicit.

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stop immediately if:

* <stop condition>
* <stop condition>

If stopped, return:

* What you attempted
* Evidence collected
* What output is needed next
