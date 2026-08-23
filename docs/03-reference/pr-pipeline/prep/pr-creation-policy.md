---
id: PR_CREATION_POLICY
title: PR Creation Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: PR Creation Policy for pr-prep-specialist.
---
# PR Creation Policy

Superseded by [`operator-contract.md`](./operator-contract.md) §5 (S4 - Draft or verify PR metadata).

The `CREATE_READY` / `DRAFT_RECOMMENDED` / `BLOCKED_*` / `PACKAGE_ONLY`
decision vocabulary previously documented here has been replaced by a
single default posture: PR creation is `DRAFT_ONLY` unless the Task Packet
or operator explicitly authorizes a non-draft creation or update. PR
creation or update is always a mutation and must be authorized — there is
no autonomous final-PR-creation path. Deterministic blockers (§S3), missing
obligations (§S2), and audit status (§S6) all gate whether a draft can even
be produced, but none of them unlock non-draft creation on their own.

This stub is kept only so existing links into this filename keep resolving.
