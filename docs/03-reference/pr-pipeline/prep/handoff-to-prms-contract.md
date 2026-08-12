---
id: HANDOFF_TO_PRMS_CONTRACT
title: Handoff To Prms Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Handoff To Prms Contract (explanation) for dopemux documentation and developer
  workflows.
---
# PR-PREP-SPECIALIST to PR-MERGE-SPECIALIST Handoff Contract

Superseded by [`operator-contract.md`](./operator-contract.md) §9 (Handoff V2).

The fixed `TP-PRPS-<number>-HANDOFF-<sequence>` id format, the
`GO_DRAFT_FIRST|GO_DIRECT|AWAIT_REVIEW` posture enum, the
`AWAIT_REVIEW|MERGE_READY|BLOCKED` next-step enum, and the fixed
seven-artifact `authoritative_artifacts` list previously documented here have
been replaced by the `schema_version: "2.0.0"` handoff bundle in the
canonical contract, which carries `risk_lane`, exact `heads`, `drift`
classification, and `pr_steward` status instead of a fixed artifact count.
The receiving side of this contract is
[`../merge/handoff-from-prps-contract.md`](../merge/handoff-from-prps-contract.md).

This stub is kept only so existing links into this filename keep resolving.
