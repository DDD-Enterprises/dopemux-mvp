---
id: OPERATOR_REVIEW_FORM
title: Operator Review Form
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Operator Review Form (explanation) for dopemux documentation and developer
  workflows.
---
# Vibe Adapter Operator Review Form

Superseded by [`operator-contract.md`](../../operator-contract.md).

This file previously defined a per-checkpoint review form keyed to the
retired fixed checkpoint sequence: mandatory-artifact checklists
(`BRANCH_STATE.json (INTAKE)`, `PR_HANDOFF_BUNDLE.json (CREATION)`, and
siblings) and an `Ambiguity Level: [LOW / MEDIUM / HIGH]` field presented as
part of that same retired ceremony. That form and its checkpoint-bound
checklist are retired along with the checkpoint sequence it reviewed
(`checkpoint-sequence.md`).

An operator reviewing a Vibe-driven `pr-prep-specialist` run should verify
the current V2 handoff bundle (`operator-contract.md` §9) against its
`heads`, `scope`, `drift`, `validation`, `audit`, `proof`, `ci`, and
`pr_steward` fields, and record an explicit decision consistent with the
operator authority boundaries in §3. There is no separate Vibe-specific
review-form schema or ambiguity band that substitutes for that evidence.

The canonical top-level `operator-review-form.md` (not this adapter file)
separately documents a distinct, still-current `Severity of Override:
INFO|LOW|MEDIUM|HIGH|CRITICAL` scale for grading an operator's override of
an automated decision; that scale is unrelated to this retired
checkpoint-review form and is unaffected by this stub.

This stub is kept only so existing links into this filename keep resolving.
