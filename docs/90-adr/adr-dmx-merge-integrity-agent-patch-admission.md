---
id: ADR-DMX-MERGE-INTEGRITY-0001
title: Adopt Fresh-Base Patch Sanitization and Exact-Candidate Merge Admission for Agent-Produced Changes
type: adr
owner: '@hu3mann'
author: Codex
date: '2026-07-11'
last_review: '2026-07-11'
next_review: '2026-10-09'
prelude: Proposed merge-integrity decision for treating agent-produced branches as untrusted patch sources and admitting only exact audited candidate trees.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - merge-integrity-investigation
    - DMX-MIA-0001
---

# ADR-DMX-MERGE-INTEGRITY-0001: Adopt Fresh-Base Patch Sanitization and Exact-Candidate Merge Admission for Agent-Produced Changes

## Status

Proposed.

## Context

OBSERVED: PR #932 and PR #1025 landed destructive unrelated deletions while presenting as narrow UI or feature changes. PR #1025 removed 137 files and 27,676 lines, including the MCP runtime stack, tests, proofs, and docs. PR #932 removed ConPort migration-foundation proof and source surfaces. CONFLICTING: The reported #720 clobber was not reproduced as a destructive landed delta from current evidence.

OBSERVED: Current repository controls contain deletion-blind changed-file collectors, advisory PR Steward workflow behavior, dry-run audit proof that can emit `embedded_audit.status: PASS` while `executed: false`, and branch rules that do not bind PR intent to exact file scope.

OBSERVED: `.github/CODEOWNERS` exists, but its listed repository surfaces resolve to `@hu3mann`. It is a useful ownership declaration, not independent review for a PR authored under that account.

OBSERVED: The merge-specialist has a GraphQL `mergePullRequest` path with `expectedHeadOid` and an `execute=True` queue-drain seam. Head binding is useful, but it does not bind candidate base, parent, tree, intent, protected-surface policy, or fresh-base sanitization.

OBSERVED: Branch protection and rulesets exist, strict status checks and conversation resolution are configured, force pushes and branch deletion are blocked, but required approval count is 0, stale reviews are not dismissed, last-push approval is not required, and PR Steward final readiness is not an observed required check.

## Decision

Agent-produced and unknown-provenance branches are untrusted patch sources rather than direct merge candidates. Their authorized changes are transplanted onto a fresh candidate from current main, validated against explicit intent and protected surfaces, audited and proven against the exact candidate tree, and admitted only through a qualified expected-base, parent, head, and tree revalidation path.

Binding invariants:

- Runtime code, Git history, GitHub state, checks, and captured evidence outrank design inputs.
- PR titles, bodies, labels, branch names, and agent claims never authorize file scope by themselves.
- Deletions, renames, copies, executable-bit changes, symlinks, submodules, binary files, and type changes are first-class change operations.
- File-count and line-count thresholds are secondary risk signals, not authorization.
- Agent branches are patch sources. They are not merge candidates unless explicitly reclassified by policy.
- Sanitization starts from current `main`.
- Sanitization applies only an authorized patch to current `main`; it does not import an agent branch's tree.
- Same-file concurrent conflicts block for adjudication.
- PR Steward remains read-only and split between early intake and final readiness.
- Dry-run or skipped audits cannot produce passing embedded-audit status.
- Audit, proof, review, readiness, and merge bind to the exact candidate head SHA, tree SHA, and diff hash.
- Candidate construction, validation, audit, and final readiness use trusted workflow logic and never execute candidate-branch workflow logic.
- Candidate parent equals expected `main`; protected reference update uses `force=false` and is disabled until controlled race and permission qualification pass.
- Normal GitHub PR merge is not an exact-admission fallback for agent or unknown-provenance candidates because it does not bind expected base or tree.
- A human-managed or dependency-automation candidate may use a separately documented GitHub PR merge path only after the same intent, enumeration, protected-surface, audit, proof, and required-check evidence is current and an operator authorizes that class. Ambiguous provenance resolves to `unknown`, not to this residual path.
- Post-merge verification compares the landed tree and freezes/report mismatches instead of blindly reverting.
- Worktree hygiene is report-only by default and never substitutes for merge authority.
- Intentional mass deletion remains possible only through explicit intent, protected-surface review, and additional gates.
- Any unresolved authority, enumeration, or evidence conflict fails closed.

Non-goals:

- This ADR does not implement runtime code, workflows, branch rules, CODEOWNERS, or GitHub settings.
- This ADR does not fix PR #1038.
- This ADR does not fix the reserved-singleton port allocator regression.
- This ADR does not author full implementation packets.

## Alternatives Considered

### Alternative A: Branch Protection Alone

Benefits: Uses native GitHub enforcement and required checks.

Limitations: Does not bind PR intent to path scope, does not sanitize source trees, and cannot distinguish authorized versus unrelated deletion.

Failure modes: A destructive patch can still pass configured checks when checks are deletion-blind or advisory.

Solo-operator implications: Avoids review deadlock but leaves merge-integrity responsibility manual.

Reversibility: Easy to tune, insufficient as primary control.

Decision: Rejected as primary boundary.

### Alternative B: Deletion Counts And Deletion-Line Thresholds Only

Benefits: Simple signal for large destructive PRs.

Limitations: Legitimate mass deletion must remain possible, and small protected-surface deletion can still be critical.

Failure modes: Threshold gaming and false positives.

Solo-operator implications: Low overhead but weak authorization.

Reversibility: Easy.

Decision: Rejected as authorization; retained as secondary risk signal.

### Alternative C: Mandatory Rebase Before Merge

Benefits: Reduces obvious stale-base risk.

Limitations: Rebase does not prove intent, protected-surface authorization, or audit freshness.

Failure modes: A rebased malicious or wrong patch remains destructive.

Solo-operator implications: Operationally tolerable but not sufficient.

Reversibility: Easy.

Decision: Rejected as sufficient boundary.

### Alternative D: CODEOWNERS And Required Approval Only

Benefits: Brings human ownership review into protected paths.

Limitations: Can deadlock a solo-maintainer repository and still lacks exact-candidate proof binding.

Failure modes: Stale approval, broad ownership, bot review confusion, and insufficient coverage for generated/proof surfaces.

Solo-operator implications: High deadlock risk without supervisor override model.

Reversibility: Moderate.

Decision: Rejected as sole mechanism; usable as a protected-surface input.

### Alternative E: PR Steward As One Monolithic Required Workflow

Benefits: Centralizes intake, review, and readiness.

Limitations: Current Steward is advisory, proof-path-dependent, and not an exact-candidate merge executor.

Failure modes: Event-loop deadlocks, pending-check races, and stale proof.

Solo-operator implications: Can block indefinitely if it waits on itself or uncertain required checks.

Reversibility: Moderate.

Decision: Rejected. Split into early intake and final readiness.

### Alternative F: Direct Agent PR Merge With Stronger CI

Benefits: Preserves current low-friction flow.

Limitations: Stronger CI still runs on an agent-provided tree and does not transplant onto current `main`.

Failure modes: Unrelated tree state or stale branch can still become the merge candidate.

Solo-operator implications: Convenient but unsafe for agent provenance classes.

Reversibility: Easy.

Decision: Rejected.

### Alternative G: Automatic Broad Revert After Post-Merge Failure

Benefits: Fast rollback after mismatch.

Limitations: A broad automatic revert is itself destructive and can erase legitimate follow-on work.

Failure modes: Revert cascades, race with new merges, and unclear operator intent.

Solo-operator implications: High operational risk.

Reversibility: Hard under active development.

Decision: Rejected. Post-merge sentinel must freeze/report by default.

### Alternative H: Worktree Cleanup As Primary Prevention

Benefits: Reduces stale local branch accumulation.

Limitations: Does not govern GitHub source branches, PR patches, reviews, or final merge.

Failure modes: Clean local worktrees can still merge bad remote patches.

Solo-operator implications: Useful hygiene, not authority.

Reversibility: Easy.

Decision: Rejected as primary mechanism; retained as report-only support.

### Alternative I: Fresh-Base Patch Transplantation With Exact-Candidate Admission

Benefits: Separates untrusted source from candidate tree, preserves current `main`, binds intent/scope/audit/proof to one exact tree, and supports controlled legitimate mass deletion.

Limitations: Requires new policy contracts, sanitizer, final readiness, merge executor, and post-merge witness.

Failure modes: Same-file conflicts and ambiguous provenance block until adjudicated.

Solo-operator implications: Requires explicit supervisor override model for emergency and independent review constraints.

Reversibility: High before merge; after merge, revert is focused to the sanitized candidate.

Decision: Accepted as the proposed architecture.

## Consequences

PROPOSED: Merge integrity becomes an admission pipeline rather than a collection of advisory checks. Agent-created branches cannot be merged by trust in source tree, title, or actor. Protected surfaces get explicit policy and intent gates. Audit proof becomes tree-bound and cannot be laundered from dry-run results.

Operational cost increases: every agent PR needs intake classification, candidate construction, exact proof, and final readiness. The benefit is deterministic failure visibility and replayable evidence.

## Migration Strategy

1. Add deletion-aware complete enumeration and destructive-diff visibility.
2. Add Change Intent and Protected Surface policy contracts.
3. Correct audit-proof semantics and split PR Steward into intake and final readiness.
4. Add fresh-base Candidate Sanitizer and provenance binding.
5. Add transactional merge executor with expected-base, parent, head, and tree revalidation.
6. Add post-merge sentinel, historical replay, and worktree hygiene reporting.

Rollback approach: before adoption, remove the new gates and leave PR Steward advisory. After adoption, rollback must be a focused revert PR for the affected policy/runtime slice.

## Verification

Implementation must prove:

- Complete changed-file manifests include deletions, renames, copies, type changes, binaries, executable-bit changes, symlinks, submodules, and generated files.
- PRs #932 and #1025 replay as blocked unless their destructive surfaces have explicit authorized intent.
- PR #1038 can be classified without trusting its title or source branch.
- A legitimate mass deletion can pass only with explicit intent and protected-surface approval.
- Dry-run and skipped audits cannot produce passing status.
- Final readiness fails closed on stale head SHA, changed tree SHA, changed diff hash, unresolved review thread, missing proof, unknown reviewer, pending required check, and incomplete harvest.
- Merge execution refuses if expected head differs.
- Post-merge sentinel reports landed-tree mismatch without automatic broad revert.

## Notes And Linked Implementation Series

Linked architecture: `docs/03-reference/merge-integrity/merge-integrity-architecture.md`

Linked investigation: `docs/03-reference/merge-integrity/merge-integrity-investigation.md`

Implementation plan: `docs/03-reference/merge-integrity/implementation-series-plan.md`

Reserved-singleton runtime regression remains separate from this ADR and should be handled by a follow-on remediation packet.
