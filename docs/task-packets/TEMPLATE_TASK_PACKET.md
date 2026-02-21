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
