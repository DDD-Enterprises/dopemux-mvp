---
id: PR_REPAIR_PACKET
title: Pr Repair Packet
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Pr Repair Packet (explanation) for dopemux documentation and developer workflows.
---
<!--
GOVERNANCE — READ BEFORE USE

This template is a READ-ONLY scaffold for presenting implementer-role repair
items to GitHub Copilot. The following operations are PROHIBITED:

  1. Copilot MUST NOT post this content as a PR comment.
  2. Copilot MUST NOT approve the PR.
  3. Copilot MUST NOT merge the PR or enqueue it in a merge queue.
  4. Copilot MUST NOT alter readiness state or check status.
  5. Copilot MUST NOT import or invoke tools/pr_merge.
  6. Copilot MUST NOT act on supervisor-role items (harvest-incomplete,
     pr-is-draft, pr-closed, mixed-sha, unknown-reviewer, proof-stale,
     proof-missing, unknown-pr-author, unknown-check, needs-supervisor,
     embedded-audit-failed).
  7. Copilot MUST NOT act on ci-role items (pending-check).

Copilot authority: implementer-only (L1-L2 code changes only).
Supervisor actions require human operator intervention.
-->

# PR Repair Packet

**Repo**: DDD-Enterprises/dopemux-mvp
**PR**: #704
**Generated**: 2026-01-01T00:00:00Z
**Copilot authority**: implementer-only

---

## Governance

Copilot is a **bounded implementer** for this repair packet.

| Operation | Permitted |
|---|---|
| Read this packet | YES |
| Propose code changes locally | YES |
| Post PR comment | **NO** |
| Approve PR | **NO** |
| Merge PR or enqueue merge queue | **NO** |
| Alter readiness / check status | **NO** |
| Import tools/pr_merge | **NO** |
| Act on supervisor-role items | **NO** |
| Act on ci-role items | **NO** |

Supervisor-role and CI-role blockers are out of scope. Only the
implementer-role items below are presented.

---

## Repair Items


### repair-0001 — `failed-check`

- **Blocker**: `FAILED_CHECK`

- **Source item**: `unit`

- **Rationale**: CI check failed; implementer must investigate and fix.
- **Suggested action**: Fix the failing CI check locally, then rerun the relevant focused validation.
