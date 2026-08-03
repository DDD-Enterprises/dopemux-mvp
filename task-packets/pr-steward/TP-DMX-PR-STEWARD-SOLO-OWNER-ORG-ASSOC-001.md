---
id: tp-dmx-pr-steward-solo-owner-org-assoc-001
title: TP-DMX-PR-STEWARD-SOLO-OWNER-ORG-ASSOC-001
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-03'
last_review: '2026-08-03'
next_review: '2026-11-01'
prelude: Org-repo association fix for solo-owner security-release path after PR #1188 MEMBER/COLLABORATOR reject.
---

# TP-DMX-PR-STEWARD-SOLO-OWNER-ORG-ASSOC-001

## Objective

Make the solo-owner PR Steward security-release path reachable on organization-owned
repositories where GitHub emits `MEMBER` / `COLLABORATOR` for the sole trusted
operator, not `OWNER`.

## Incident

PR #1188 at head `b1bab98b7e88b558a990efbe47b5ca3a7dbfa7ea`:

- Undrafted; exact solo-owner phrase posted by `hu3mann`
- Steward run `30785732366` harvested phrase
- Blocker remained `SECURITY_RELEASE_APPROVAL_REQUIRED`
- UNKNOWN: `solo_owner:SOLO_OWNER_PHRASE_OPERATOR_NOT_OWNER`
- Live associations: MEMBER (user GraphQL) / COLLABORATOR (Steward harvest)

## ADR

`ADR-DMX-PRSTEWARD-SOLOOWNER-001` amendment 2026-08-03 — association policy.

## Decision

Accept `OWNER` | `MEMBER` | `COLLABORATOR` for PR-author and phrase-comment
associations on the solo path, aligned with ordinary human security-release
approval associations. Reject `CONTRIBUTOR`, `NONE`, and missing dual trust.

## Non-goals

- Do not change phrase format, head binding, or receipt code.
- Do not waive non-`SECURITY_RELEASE_*` blockers.
- Do not enable auto-merge.
- Do not invent a second trusted approver.
- Do not modify PR #1188 content in this packet (only unlock after this lands on main).

## Allowlist

- `tools/pr_steward/solo_owner_security_release.py`
- `tests/pr_steward/test_solo_owner_security_release.py`
- `tests/pr_steward/test_classifier_solo_owner.py`
- `docs/90-adr/adr-dmx-prsteward-soloowner-001.md`
- `docs/90-adr/adr-index.md`
- `task-packets/pr-steward/TP-DMX-PR-STEWARD-SOLO-OWNER-ORG-ASSOC-001.md`
- `task-packets/pr-steward/TP-DMX-PR-STEWARD-SOLO-OWNER-ORG-ASSOC-001.json`

## Bootstrap note

This PR touches `tools/pr_steward/**` (trust root). Steward on **main** still
runs the pre-fix association check until this merges. Expect this PR itself to
need operator bootstrap/admin merge path (same trust-root recursion as the
original solo-owner bootstrap). After merge to main, re-run Steward on #1188
without head movement.

## Terminal stop

`READY_FOR_OPERATOR_BOOTSTRAP_MERGE_OF_ORG_ASSOC_GATE_FIX` then, after main has
the fix, re-dispatch Steward for PR #1188.
