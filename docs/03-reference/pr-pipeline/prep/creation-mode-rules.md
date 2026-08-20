---
id: CREATION_MODE_RULES
title: Creation Mode Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Rules defining the PR creation modes for pr-prep-specialist.
---
# Creation Mode Rules

Superseded by [`operator-contract.md`](./operator-contract.md) §5
(S4 - Draft or verify PR metadata).

This file previously defined four creation modes (`PACKAGE_ONLY`,
`CREATE_DRAFT_PR`, `CREATE_FINAL_PR`, `BLOCKED_NO_CREATE`), including a
`CREATE_FINAL_PR` mode that created a non-draft PR whenever the final prep
decision was `CREATE_READY`. That mode and its triggering `CREATE_READY`
decision are retired: PR Prep has no autonomous non-draft-creation path.
The V2 contract's single default posture is `DRAFT_ONLY`; creating or
updating a non-draft PR always requires explicit operator or Task Packet
authorization, never a locally computed readiness decision.

This stub is kept only so existing links into this filename keep resolving.
