---
id: adr-dmx-prsteward-soloowner-001
title: 'PR Steward Solo-Owner Security-Release Authorization'
type: adr
owner: '@hu3mann'
author: 'Grok Build, for operator decision'
date: '2026-07-27'
last_review: '2026-07-27'
next_review: '2026-10-25'
status: accepted
prelude: Resolves solo-owner PR Steward security-release deadlock without inventing a second reviewer or weakening multi-reviewer enforcement. Org maintainers use MEMBER association.
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-mcpprof-001
---

# ADR-DMX-PRSTEWARD-SOLOOWNER-001: PR Steward Solo-Owner Security-Release Authorization

**Status:** Accepted
**Decision owner:** Operator
**Packet:** `TP-DMX-PR-STEWARD-SOLO-OWNER-BOOTSTRAP-001`

## Context

PR Steward requires an exact-head GitHub `APPROVED` review from a login in
`trusted_security_release_approvers` when a PR touches security-release
categories (CI workflows, schema/contract, CODEOWNERS, secrets-like paths,
`tools/pr_steward/**` trust root).

Observed solo-owner deadlock on `DDD-Enterprises/dopemux-mvp`:

- trusted roster on `origin/main` is exactly `hu3mann`;
- PR author is `hu3mann`;
- GitHub forbids author self-approval;
- no second independent human GitHub identity is established;
- inventing a cosmetic second account is not independent review;
- changing the gate itself touches `tools/pr_steward/**` and re-triggers the same gate (bootstrap problem).

Ordinary multi-reviewer enforcement must remain unchanged when a non-author
trusted approver exists.

## Options compared

### Option A — Real second human approver

**Valid only if** a concrete non-author GitHub account is identified with:

- repository review access;
- independent human control;
- explicit operator authorization to add it to `trusted_security_release_approvers` on trusted main;
- willingness to review exact-head evidence.

**Rejected for this decision cycle** because no such independent reviewer
identity has been established. This ADR does not authorize inventing bots or
second usernames controlled by the same implementation session.

Option A remains the preferred long-term path when a real second human becomes
available: add them to the roster on main; the ordinary non-author APPROVED
path already works and is not altered by this ADR.

### Option B — Solo-owner exact-head release authorization (chosen)

Provide a narrowly scoped override that activates **only** when all of the
following hold:

1. trusted security-release roster on trusted main contains exactly one human;
2. that identity is the PR author and the sole trusted security-release approver;
3. the PR author / authorizing-comment association is exactly `OWNER` (user-owned
   repositories) or `MEMBER` (organization-owned repositories); `COLLABORATOR`,
   `CONTRIBUTOR`, `FIRST_TIMER`, `FIRST_TIME_CONTRIBUTOR`, `NONE`, missing on both
   sides, and unknown values do **not** activate;
4. when both PR association and comment association are present, they must match
   (mismatch → `SOLO_OWNER_ASSOCIATION_MISMATCH`);
5. no eligible non-author trusted approver exists;
6. independent embedded audit is current to the exact PR head with
   `PASS` or non-blocking `PASS_WITH_RISKS`, and auditor tool/model/provider/
   runner/session fields are recorded when present;
7. all required CI checks are current and green (no failed/pending required);
8. proof is current to the exact PR head;
9. no unknown reviewers, unclassified review items, unresolved blocking threads,
   harvest incompleteness, draft/closed PR, or mixed-SHA artifact sets remain;
10. the operator posts an exact phrase as a PR issue comment:

```text
AUTHORIZE SOLO-OWNER SECURITY RELEASE FOR PR #<PR_NUMBER> AT HEAD <FULL_SHA>
```

## Decision

Adopt **Option B** as a durable fail-closed contract.

### Authorization properties

The solo-owner phrase must:

- be harvested from GitHub issue comments (not invented in local proof);
- bind repository, PR number, full 40-char head SHA, operator login, timestamp,
  and scope `security_release_only`;
- become stale immediately if the PR head changes;
- **never** count as an ordinary GitHub `APPROVED` review
  (`security_release.approval` remains null when only the override is used);
- emit receipt code `SOLO_OWNER_SECURITY_RELEASE_OVERRIDE_USED` on
  `MERGE_READINESS.json.security_release`;
- leave the ordinary non-author APPROVED path unchanged;
- never enable auto-merge;
- never waive CI, proof, audit, review-thread, reviewer-classification, harvest,
  or scope gates — those remain independent blockers.

### Bootstrap exception (out of band)

Because the implementing PR itself touches `tools/pr_steward/**`, it predictably
fails the *current* security-release gate before this policy exists on main.
That first merge requires an explicit one-time operator bootstrap phrase naming
the policy PR and full head SHA, scoped only to that administrative merge. It
does **not** authorize any other PR (including MCP profile PR #1128).

After the policy SHA is on `origin/main`, subsequent security-release PRs by
the solo owner use the in-band phrase above; the ordinary multi-reviewer path
remains mandatory whenever a non-author trusted approver exists.

## Invariants

1. Multi-reviewer enforcement is not weakened when ≥1 non-author trusted
   approver is configured.
2. Solo path never fabricates GitHub review objects.
3. Solo path never sets auto-merge.
4. Solo path never clears non-`SECURITY_RELEASE_*` blockers.
5. Head binding is exact (full SHA); partial SHAs and wrong PR numbers fail closed.
6. Phrase author must be the solo trusted identity; foreign logins are ignored.
7. Receipt is evidence, not a second catalog of authority.
8. Solo-operator associations are exactly `{OWNER, MEMBER}` — not the broader
   `trusted_author_associations` set (which includes `COLLABORATOR`).
9. Association acceptance never replaces the exact single-person trusted roster
   check; a second trusted human disables the solo path regardless of association.

## Amendment — org MEMBER association (TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001)

**Problem:** The initial implementation required GitHub `authorAssociation=OWNER`.
On organization-owned repositories such as `DDD-Enterprises/dopemux-mvp`, GitHub
reports the sole human maintainer as `MEMBER`, so a legitimate exact-head solo
authorization was rejected before remaining gates ran.

**Repair:** Accept `_SOLO_OPERATOR_ASSOCIATIONS = {OWNER, MEMBER}` for PR author
and authorization-comment association validation (and receipt generation). All
other security, proof, audit, review, CI, exact-head, and multi-approver gates
remain independently blocking. Auto-merge remains disabled. The solo-owner
receipt never becomes a fabricated GitHub review. The organization-owned GitHub
App approval path (PR #1133 / ADR companion) is unchanged.

## Consequences

### Positive

- Solo-owner repositories can complete security-release gates without fake
  second accounts.
- Evidence is explicit, exact-head-bound, and auditable.
- Ordinary team workflows remain unchanged.

### Costs

- Operators must post a precise phrase after every head change.
- Bootstrap of the policy itself still requires a one-time out-of-band merge
  authorization because of trust-root recursion.
- Schema for `MERGE_READINESS` gains optional solo-owner fields.

### Failure direction

When roster, ownership, phrase, head, audit, CI, proof, or classification truth
is incomplete, the path does not activate and
`SECURITY_RELEASE_APPROVAL_REQUIRED` (or other blockers) remain.

## Rollback

1. Revert the policy commits introducing `solo_owner_security_release.py` and
   classifier wiring.
2. Restore prior `merge_readiness.schema.json`.
3. Re-run PR Steward tests.
4. Do not delete historical receipts in already-merged PRs.
