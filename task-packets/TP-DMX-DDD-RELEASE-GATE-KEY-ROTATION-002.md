---
id: TP-DMX-DDD-RELEASE-GATE-KEY-ROTATION-002
title: DDD Release Gate Key Rotation Reconciliation
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-28'
last_review: '2026-08-28'
next_review: '2026-11-26'
prelude: Verification-first reconciliation for disclosed ddd-release-gate GitHub App key.
---
# TP-DMX-DDD-RELEASE-GATE-KEY-ROTATION-002

Status: ACTIVE

Risk lane: L3

Subject: DDD release-gate key-rotation state reconciliation and completion

## Objective

Determine whether compromised GitHub App key was already rotated. Perform new rotation only if current evidence proves rotation remains incomplete. Unknown state stops without mutation.

## Authority

- GitHub App: `ddd-release-gate`
- Organization: `DDD-Enterprises`
- Repository: `DDD-Enterprises/dopemux-mvp`
- Predecessor: `TP-DMX-DDD-RELEASE-GATE-KEY-ROTATION-001`
- Known compromised public fingerprint: `SHA256:Q5UQVn6HD0PCE0NvPSFugsydKz1beC3RpVvIUm3eicg=`
- Merge, release, deployment, and PR approval: not authorized

## Anti-double-rotation invariant

Verify before mutate. If compromised fingerprint is absent and current secret-backed App authentication works, use `ALREADY_ROTATED_VERIFIED`. Do not generate another key, rewrite healthy secret, or delete another key. Unknown state stops.

## Allowed outcomes

- `ALREADY_ROTATED_VERIFIED`
- `ROTATION_REQUIRED_AND_COMPLETED`
- `BLOCKED_ROTATION_STATE_UNKNOWN`
- `FAIL`

## Materialized outcome

`ALREADY_ROTATED_VERIFIED`

No key generation, secret rewrite, App-key deletion, approval, permission change, installation-scope change, workflow change, merge, release, or deployment was performed by this packet.

Canonical machine-readable packet: `task-packets/TP-DMX-DDD-RELEASE-GATE-KEY-ROTATION-002.json`.
