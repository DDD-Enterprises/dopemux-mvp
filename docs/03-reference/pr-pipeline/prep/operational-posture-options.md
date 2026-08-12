---
id: OPERATIONAL_POSTURE_OPTIONS
title: Operational Posture Options
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Operational Posture Options (explanation) for dopemux documentation and developer
  workflows.
---
# Operational Posture Options

Superseded by [`operator-contract.md`](./operator-contract.md) §3 (Hard boundaries)
and §5 (S4 - Draft or verify PR metadata).

This file previously defined a five-posture ladder
(`GO_PACKAGE_ONLY`, `GO_DRAFT_FIRST`, `GO_SUPERVISED_FINAL_CREATION`,
`NO_GO_LIMIT_TO_ARTIFACTS_ONLY`, `ROLLBACK_TO_HUMAN_PREP`) with a
`GO_SUPERVISED_FINAL_CREATION` capability that authorized non-draft,
merge-ready PR creation once operational-evidence thresholds were met, and
graded risk using a `LOW/MODERATE/CALCULATED/MINIMAL/NONE` scale. That
ladder, its evidence-threshold escalation path, and its risk grading are
retired. Under the V2 contract, PR Prep has exactly one default creation
posture (`DRAFT_ONLY`); creating or updating a non-draft PR requires
explicit operator or Task Packet authorization every time, is never earned
through accumulated operational evidence, and PR Prep never grants
merge-ready authority. Risk is expressed via the `L0-L3` risk lanes (§4),
not a posture-specific risk word.

This stub is kept only so existing links into this filename keep resolving.
