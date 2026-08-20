---
id: WORKFLOW_SEQUENCE
title: Workflow Sequence
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Workflow Sequence (explanation) for dopemux documentation and developer workflows.
---
# PR-PREP-SPECIALIST Canonical Workflow Sequence

Superseded by [`operator-contract.md`](./operator-contract.md) §5 (Conditional workflow).

The mandatory exact-7-step sequence (`INSPECT_BRANCH_STATE` →
`AUDIT_ADJACENT_WORK` → `DETECT_OBLIGATIONS` → `DRAFT_PR_FROM_TEMPLATE` →
`RUN_DETERMINISTIC_VALIDATION` → `CREATE_PR_UNDER_POSTURE` →
`HANDOFF_TO_PRMS`) and its fixed seven-artifact bundle previously documented
here are no longer the contract. The current workflow is conditional
(S0-S8): steps are ordered but not all are mandatory ceremony for every
run, and the specialist must not manufacture artifacts merely to satisfy a
fixed step count. `GO_DIRECT` as a governing posture and a PRPS-produced
`MERGE_READY` recommendation are forbidden — see §3 (Hard boundaries) and §6
(Prep states) in the canonical contract.

This stub is kept only so existing links into this filename keep resolving.
