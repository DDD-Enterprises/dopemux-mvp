---
id: DMX-MIA-0001
title: Merge Integrity Architecture
type: reference
owner: '@hu3mann'
author: Codex
date: '2026-07-11'
status: proposed
last_review: '2026-07-11'
next_review: '2026-10-09'
prelude: Merge Integrity Architecture (reference) for dopemux documentation and developer
  workflows.
---
# DMX-MIA-0001: Merge Integrity Architecture

## Goals

PROPOSED:

- Prevent stale-branch and cross-scope clobbers from reaching `main`.
- Treat agent-produced branches as untrusted patch sources.
- Preserve current `main` by constructing merge candidates from a fresh base.
- Bind intent, protected-surface policy, audit, proof, review, readiness, and merge to the exact candidate tree.
- Preserve legitimate mass deletion through explicit intent and additional gates.
- Keep worktree cleanup and reporting separate from merge authority.

## Non-Goals

PROPOSED:

- No runtime implementation in `TP-DMX-MERGE-INTEGRITY-0001`.
- No GitHub branch protection, ruleset, PR, label, comment, review, or merge mutation in this packet.
- No automatic broad revert after post-merge mismatch.
- No conversion of PR Steward into a mutating actor.
- No reserved-singleton port allocator fix in this architecture packet.

## Authority Boundaries

OBSERVED: Runtime code, Git history, GitHub state, checks, rulesets, branch protection, and tests outrank design docs. Task packets constrain execution scope but do not make runtime behavior claims true.

PROPOSED:

- Change Intent Registry owns allowed purpose and scope.
- Protected Surface Registry owns risk classification and extra gates for sensitive paths.
- Merge Integrity Engine owns deterministic classification and candidate construction.
- PR Steward Intake owns read-only early harvest and advisory blockers.
- Final Readiness Gate owns exact-candidate admission.
- Transactional Merge Executor owns qualified expected-base fast-forward admission.
- Post-Merge Sentinel owns landed-tree comparison and reporting.

## Trust Model

PROPOSED: Agent branches are untrusted. Candidate construction, validation, audit, and final readiness execute only from trusted default-branch or pinned trusted workflow logic; they never execute candidate-branch workflow logic. A candidate becomes merge-eligible only when reconstructed from current `main`, intent-bound, protected-surface validated, and proven against an exact tree.

OBSERVED Phase B boundary: PR #1042 implements trusted-source embedded-audit and artifact-bound final-Steward foundations; PR #1044 corrects their package-module runner invocation. They provide fail-closed audit/readiness evidence only. The sanitizer, exact admission executor, and protected-reference capability qualification described here remain proposed and disabled.

## Provenance Classes

PROPOSED:

- `managed_agent`: an agent operating from a Dopemux-created worktree with recorded source base, task packet, allowlist, identity, and proof. Codex and Claude Code may qualify when those receipts exist.
- `external_agent`: an externally managed branch, including Jules/Palette, hosted agents, and any source whose lifecycle Dopemux cannot prove.
- `dependency_automation`: a dependency update constrained to declared manifests, lockfiles, and generated dependency artifacts.
- `human_managed`: a human-created branch with a valid Task Packet or bounded micro-change intent.
- `unknown`: missing or conflicting signals.

Classification considers source-base receipt, packet provenance, branch and commit metadata, GitHub App identity, co-author trailers, runner session, and file markers such as `.Jules/*`. PR author alone is never sufficient. `managed_agent`, `external_agent`, and `unknown` require fresh-base sanitization. `unknown` fails closed until classified or explicitly authorized for bounded investigation.

## Change Intent Registry

PROPOSED: Every candidate must map to a machine-readable intent record.

Minimum fields:

- `intent_id`
- `pr_number`
- `provenance_class`
- `allowed_paths`
- `allowed_operations`
- `protected_surface_exceptions`
- `mass_deletion_intent`
- `same_file_conflict_policy`
- `proof_requirements`
- `review_requirements`
- `operator_override_ref`

PR text can propose intent but cannot authorize it.

## Protected Surface Registry

PROPOSED: Protected status is a path-and-authority decision, not a file-count heuristic. The first registry is tiered so routine documentation does not inherit the same friction as runtime admission controls.

- **Tier 1: hard protected.** `src/dopemux/mcp/**`, ConPort migration/schema paths, `.github/workflows/**`, `scripts/audit/**`, `tools/pr_steward/**`, `src/dopemux_pr_merge_specialist/**`, `schemas/**`, and active catalog or compose configuration. Deletion is blocked by default and mutation requires explicit intent plus the registry-defined tests and audit.
- **Tier 2: governance protected.** `task-packets/**`, selected proof and proof-schema contracts, `docs/90-adr/**`, and the merge-integrity policy itself. Mutation requires declared intent, review evidence, and a custody-preserving proof update; it does not require a runtime-style deletion exception unless the registry entry says so.
- **Tier 3: advisory risk surfaces.** General reference and how-to documentation, including most of `docs/03-reference/**`. These changes remain in complete enumeration and intent checks, but their risk is a signal rather than a default hard block.

Registry entries define path patterns, authority tier, allowed operations, required tests or reviewers, deletion policy, rollback expectation, and the policy version that governed the candidate. Registry changes are themselves Tier 2.

## Merge Integrity Engine

PROPOSED: The engine consumes source PR data, intent, protected-surface policy, and current `main`. It emits a deterministic admission record:

- complete change manifest
- provenance classification
- intent match results
- protected-surface hits
- destructive operation inventory
- same-file conflict report
- candidate construction plan
- blocking-code taxonomy

The engine never mutates an existing PR.

## Complete Change Enumeration

PROPOSED: Authoritative enumeration uses git object data, not `--diff-filter=ACMR`.

Required operations:

- added
- modified
- deleted
- renamed
- copied
- type changed
- unmerged
- unknown
- broken pairing
- executable-bit change
- symlink change
- submodule pointer change
- binary change

GitHub file lists may supplement enumeration but are not sufficient for large or complex diffs.

## Aggregate And Per-Commit Analysis

PROPOSED: The engine analyzes both:

- aggregate candidate diff against current `main`
- per-commit source diffs when source branch history is available

Per-commit analysis is evidence for transient destructive states, but final admission binds to the candidate tree.

## Current-Base Preservation Witness

PROPOSED: Candidate construction records:

- current `main` SHA
- expected base SHA and candidate parent SHA
- source PR base SHA
- source PR head SHA
- candidate branch SHA
- candidate tree SHA
- candidate diff SHA256
- files changed from current `main`

If current `main` changes before final readiness, the candidate is stale. If it changes after readiness, a non-forced reference update must reject a candidate whose parent is no longer the `main` tip.

## Candidate Sanitizer

PROPOSED: The sanitizer creates a fresh candidate from current `main`, applies only authorized patch hunks or file operations, and refuses:

- unauthorized deletions
- unauthorized protected-surface changes
- same-file conflicts
- unclassified binary/submodule/symlink/executable-bit changes
- generated lockfile changes outside declared intent
- source-branch tree import

For mass deletion, explicit intent and protected-surface gates are mandatory.

## Two-Stage PR Steward

PROPOSED:

- Intake Steward: read-only, early, advisory, harvests PR state, review threads, changed files, checks, provenance signals, and proof state. It may emit `INTAKE_CLEAR`, `NEEDS_IMPLEMENTER`, `NEEDS_SUPERVISOR`, `BLOCKED`, or `CHECKS_PENDING`; it never emits final `READY`.
- Final Readiness Steward: read-only, event-driven required gate after expected checks are terminal or a merge-group candidate exists. It re-harvests the exact candidate and emits `READY`, `NEEDS_IMPLEMENTER`, `NEEDS_SUPERVISOR`, `BLOCKED`, or `STALE`.

PR Steward remains read-only in both stages. Until this ADR is accepted and the final gate is implemented, `docs/03-reference/development-factory/pr-steward-and-readiness.md` remains the current contract: Steward is advisory and its readiness artifact is not merge authority. This proposal changes neither that runtime posture nor the DCP red merge seam.

## Relationship To Existing Proof And Merge Contracts

OBSERVED: `docs/03-reference/development-factory/evidence-and-proof-flow.md` requires packet identity, head binding, validation states, review/precommit status, residual risks, and cleanup state. Merge-integrity packets use that proof envelope plus candidate-specific base, parent, tree, diff, intent, policy, audit, and review fingerprints. A repository-committed proof cannot attest to its own final commit SHA; a trusted post-commit workflow must emit the final-head receipt.

OBSERVED: `src/dopemux_pr_merge_specialist/merge.py` already uses `expectedHeadOid`, and `queue_drain.py` has an execution seam. They remain separate mutation-capable code surfaces. This architecture does not create a second merge authority: GitHub remains the merge authority, and any future executor must explicitly gate or reject non-sanitized paths for agent and unknown provenance classes.

## Required-Check Manifest

PROPOSED: Required checks are declared in repository policy and compared with GitHub check state. Unknown, pending, missing, or failed required checks block final readiness.

The final gate must avoid waiting on itself. Its own status is excluded from the input set it waits to become terminal.

## Audit-Proof Requirements

PROPOSED: Audit proof includes:

- auditor tool, provider, model, and runner
- exact invocation
- exit code
- candidate head SHA
- candidate tree SHA
- candidate diff SHA256
- executed status
- verdict
- findings
- remaining risks

Dry-run, skipped, route-unavailable, runner-error, malformed, stale, or wrong-head audits cannot be `PASS`. The strict canonical `embedded_audit` object expresses non-execution as `status: SKIPPED`; a top-level audit receipt records `executed: false` and any execution results without extending that compatibility-sensitive nested schema. Required audit absence blocks readiness. Final-head proof is a trusted workflow artifact emitted after the commit exists; a committed proof does not claim its own SHA.

## Transactional Merge Executor

PROPOSED: Exact admission for `managed_agent`, `external_agent`, and `unknown` uses a preconstructed sanitized candidate commit whose parent equals expected `main`, followed by a protected Git reference update with `force=false`. An intervening base advance makes that update non-fast-forward and must fail. This primitive is disabled until controlled race, permission, branch-protection, required-check, and PR-semantics qualification passes. The existing expected-head GraphQL merge is evidence of a useful primitive, not a substitute for expected base, parent, tree, scope, or sanitizer provenance.

The executor accepts only:

- candidate PR number
- expected base SHA, candidate parent SHA, and candidate commit SHA
- expected tree SHA
- exact readiness artifact reference
- operator approval or supervisor override reference

It refuses base, head, parent, tree, qualification, or fast-forward mismatch and never force-updates or falls back to normal PR merge for an agent or unknown-provenance candidate.

For `human_managed` and explicitly constrained `dependency_automation`, a normal GitHub PR merge remains a residual path only when its provenance is unambiguous, all non-transactional evidence is current, and an operator authorizes that class. It is not an exact-admission claim, cannot be silently selected after sanitizer failure, and must be reclassified to `unknown` if provenance or scope conflicts.

## Exact-Candidate Revalidation

PROPOSED: Every final action re-reads GitHub state. Base SHA, candidate parent, head SHA, tree SHA, checks, reviews, threads, labels, intent, policy, audit, proof, or ruleset-relevant changes invalidate readiness. The qualified final reference update, not a post-read normal PR merge, is the agent-candidate base-race boundary.

## Post-Merge Sentinel

PROPOSED: After merge, sentinel compares the landed tree against the expected candidate tree and reports:

- exact landed commit
- expected tree
- actual tree
- changed paths
- mismatch status
- rollback recommendation

It freezes/report mismatches and does not automatically broad-revert.

## Worktree Hygiene Reporter

PROPOSED: Worktree hygiene reports stale local worktrees, dirty branches, merged branches, absent paths, and accumulated proof directories. It is advisory by default and cannot authorize, block, or perform merge by itself.

## State Machine

```text
SOURCE_PR
  -> INTAKE_HARVESTED
  -> PROVENANCE_CLASSIFIED
  -> INTENT_BOUND
  -> PROTECTED_SURFACES_EVALUATED
  -> CANDIDATE_BUILT_FROM_CURRENT_MAIN
  -> CANDIDATE_VALIDATED
  -> CANDIDATE_AUDITED
  -> PROTECTED_REFERENCE_CAPABILITY_QUALIFIED
  -> FINAL_READINESS_READY
  -> EXPECTED_BASE_PARENT_HEAD_TREE_RECHECKED
  -> MERGED
  -> LANDED_TREE_VERIFIED
```

Blocking states:

- `BLOCKED_HARVEST_INCOMPLETE`
- `BLOCKED_UNKNOWN_PROVENANCE`
- `BLOCKED_INTENT_MISSING`
- `BLOCKED_UNAUTHORIZED_SCOPE`
- `BLOCKED_DESTRUCTIVE_DIFF`
- `BLOCKED_CONFLICT`
- `BLOCKED_AUDIT_MISSING`
- `BLOCKED_AUDIT_FAILED`
- `BLOCKED_REQUIRED_CHECK`
- `BLOCKED_REVIEW_THREAD`
- `BLOCKED_STALE_CANDIDATE`
- `BLOCKED_EXPECTED_HEAD_MISMATCH`
- `BLOCKED_EXPECTED_BASE_MISMATCH`
- `BLOCKED_REFERENCE_CAPABILITY_UNQUALIFIED`
- `BLOCKED_POST_MERGE_MISMATCH`

## Invalidating Events

PROPOSED: Invalidate readiness on:

- source PR head change
- candidate PR head change
- base branch change
- intent registry change
- protected surface registry change
- required check manifest change
- audit proof change
- review thread change
- relevant label/policy change
- workflow/ruleset posture change

## Override Contract

PROPOSED: Supervisor override must be explicit, recorded, scoped, time-bound, single-use, and linked to the exact candidate base, head, and tree. It records blocked codes, authorized path scope, reason, approver, independent-audit reference when required, and expiry. Overrides cannot bypass complete enumeration, candidate identity, protected-reference qualification, or post-merge sentinel; they never launder a failed gate into `PASS`.

## Proof And Readiness Schemas

PROPOSED:

- `CHANGE_MANIFEST.json`
- `INTENT_MATCH.json`
- `PROTECTED_SURFACE_HITS.json`
- `CANDIDATE_WITNESS.json`
- `MERGE_READINESS.json`
- `MERGE_EXECUTION.json`
- `POST_MERGE_SENTINEL.json`

All schemas include `schema_version`, `created_at`, `repo`, `base_branch`, `candidate_head_sha`, and `candidate_tree_sha` where applicable. `MERGE_READINESS.json` additionally binds source base/head, candidate base/parent/head/tree/diff, intent and policy hashes, audit execution and tree hash, complete required-check state, review-thread state, proof freshness, and any override receipt.

## GitHub Enforcement Posture

PROPOSED: GitHub branch protection remains necessary but not sufficient. The repository should add final readiness as a required check only after the final gate is implemented, its expected-check manifest is reconciled with GitHub policy, and self-deadlock behavior is proven. CODEOWNERS can add routing requirements but cannot substitute for independent review in the current single-owner topology.

## Historical Replay Requirements

PROPOSED: Replay cases:

- #932 must block without explicit ConPort migration/proof deletion intent.
- #1025 must block without explicit MCP runtime/proof/test deletion intent.
- #1038 must classify as Palette/Jules source and block on unresolved review threads and missing exact proof.
- A legitimate #1026-style mass deletion must pass only with explicit mass-deletion intent and protected-surface gates.

PR #720/#734 remains a conflicting historical report rather than a must-block fixture until an immutable replay demonstrates a destructive landed delta or a source-history operation that the candidate model must detect.

## Rollout Stages

1. Observe only.
2. Advisory intake.
3. Candidate sanitizer dry-run.
4. Required final readiness on protected surfaces.
5. Required final readiness on all agent and unknown provenance classes.
6. Protected-reference qualification and controlled race test.
7. Transactional merge executor.
8. Post-merge sentinel enforcement.

## Acceptance Criteria

PROPOSED: The architecture is implemented only when historical replay, canary classification, trusted audit, final readiness, protected-reference qualification with controlled base-race test, and post-merge sentinel all pass. Local audit cannot replace trusted current-head evidence.

## Failure Behavior

PROPOSED: Unknowns block. Conflicts block. Missing proof blocks. Stale candidate blocks. Unauthorized destructive operations block. Post-merge mismatch freezes/report for supervisor action.

## Residual Risks

UNKNOWN: GitHub merge queue tree-SHA binding and solo-operator emergency bypass require implementation-time validation.

OBSERVED: Reserved-singleton port allocator behavior remains an open runtime regression outside this architecture packet.

## Explicit Implementation Seams

- `tools/pr_steward/*`
- `src/dopemux_pr_merge_specialist/*`
- `.github/workflows/*`
- `scripts/audit/*`
- `schemas/pr_steward/*`
- `schemas/project_control_plane/*`
- future `tools/merge_integrity/*` or equivalent package chosen by implementation packet

Before the executor packet can be complete, every existing merge-specialist or workflow mutation path must be classified and either bound to sanitized candidate admission for agent/unknown provenance or explicitly rejected for those classes.
