---
id: CHECKPOINT_SEQUENCE
title: Checkpoint Sequence
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Checkpoint Sequence (explanation) for dopemux documentation and developer
  workflows.
---
# Vibe Adapter Checkpoint Sequence

Superseded by [`operator-contract.md`](../../operator-contract.md) §5
(Conditional workflow).

This file previously defined a fixed seven-checkpoint sequence
(`PLAN_COMPLETE` → `INTAKE_CHECKPOINT` → ... → `CREATION_CHECKPOINT`), a
mandatory artifact per checkpoint (`BRANCH_STATE.json`,
`PR_HANDOFF_BUNDLE.json`, etc.), `Draft Posture:
{CREATE_READY/DRAFT_RECOMMENDED/BLOCKED}`, and `Risk Hint:
{LOW/MEDIUM/HIGH}` as current governing states. That fixed ceremony and
risk vocabulary are retired.

Vibe's actual workflow is the conditional S0-S8 sequence in
`operator-contract.md` §5: custody, scope/drift/overlap, obligations and
`L0-L3` risk, deterministic pre-push gate, draft-or-verify PR metadata
(default `DRAFT_ONLY`), freeze content, independent audit when required,
proof-only successor, and CI/PR Steward handoff. It does not manufacture a
fixed artifact count to satisfy ceremony, and it never emits `CREATE_READY`
or a `risk_hint` LOW/MEDIUM/HIGH value as a current governing state.

This stub is kept only so existing links into this filename keep resolving.
