---
id: tp-dmx-pr-steward-solo-owner-bootstrap-001
title: TP-DMX-PR-STEWARD-SOLO-OWNER-BOOTSTRAP-001
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-27'
last_review: '2026-07-27'
next_review: '2026-10-25'
prelude: Decision-first bootstrap packet for solo-owner PR Steward security-release authorization.
---

# TP-DMX-PR-STEWARD-SOLO-OWNER-BOOTSTRAP-001

## Objective

Resolve the solo-owner PR Steward security-release deadlock without inventing a second reviewer, without weakening multi-reviewer enforcement, and without silently bypassing the trust-root bootstrap problem.

## ADR

`ADR-DMX-PRSTEWARD-SOLOOWNER-001` — Option B accepted.

## Non-goals

- Do not modify PR #1128.
- Do not start dNh CRM or adOps.
- Do not merge this policy PR without the one-time bootstrap authorization phrase.
- Do not enable auto-merge.

## Implementation summary

- `tools/pr_steward/solo_owner_security_release.py`
- classifier wiring after ordinary approval evaluation
- `schemas/pr_steward/merge_readiness.schema.json` fields for solo override receipt
- unit + classifier negatives

## Terminal stop for this packet

`READY_FOR_ONE_TIME_BOOTSTRAP_MERGE_AUTHORIZATION`
