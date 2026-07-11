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
- Transactional Merge Executor owns expected-head merge execution.
- Post-Merge Sentinel owns landed-tree comparison and reporting.

## Trust Model

PROPOSED: Agent branches are untrusted. GitHub PR metadata, titles, bodies, labels, and comments are claims. Source branches and generated proof are evidence only after validation. A candidate becomes merge-eligible only when it is reconstructed from current `main`, matches explicit intent, passes protected-surface rules, and has exact tree-bound proof.

## Provenance Classes

PROPOSED:

- `agent_palette_jules`: branches and files indicating Jules/Palette generation, including `.Jules/*`.
- `agent_codex`: Codex-generated source or review actions.
- `agent_claude_code`: Claude Code generated branches or handoffs.
- `agent_agy_antigravity`: AGY/Antigravity generated branches.
- `agent_gemini`: Gemini-generated branches or audit outputs.
- `dependency_automation`: dependency update tools.
- `human_manual`: manually authored human branch with evidence.
- `unknown`: insufficient or conflicting signals.

UNKNOWN provenance fails closed or routes to supervisor classification.

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

PROPOSED: Protected surfaces include:

- `src/dopemux/mcp/**`
- `tests/unit/test_mcp_*.py`
- `.github/workflows/**`
- `scripts/audit/**`
- `tools/pr_steward/**`
- `src/dopemux_pr_merge_specialist/**`
- `schemas/**`
- `mcp_catalog.yaml`
- `.mcp.json`
- `.pre-commit-config.yaml`
- `proof/**`
- `proofs/**`
- `task-packets/**`
- `docs/90-adr/**`
- `docs/03-reference/**`

Registry entries define owners, allowed operations, extra reviewers or auditors, whether deletion is normally allowed, and rollback expectations.

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
- source PR base SHA
- source PR head SHA
- candidate branch SHA
- candidate tree SHA
- candidate diff SHA256
- files changed from current `main`

If current `main` changes before final readiness, the candidate is stale.

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

- Intake Steward: read-only, early, advisory, harvests PR state, review threads, changed files, checks, provenance signals, and proof state.
- Final Readiness Steward: required gate, exact candidate only, refuses stale or incomplete evidence.

PR Steward remains read-only in both stages.

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

Dry-run and skipped audits cannot be `PASS`.

## Transactional Merge Executor

PROPOSED: Merge execution accepts only:

- candidate PR number
- expected head SHA
- expected tree SHA
- exact readiness artifact reference
- operator approval or supervisor override reference

It refuses if the candidate head or tree differs from readiness evidence.

## Expected-Head Enforcement

PROPOSED: Every final action re-reads GitHub state. If head SHA, tree SHA, checks, reviews, review threads, labels affecting policy, or ruleset-relevant state changed, readiness is invalidated and the merge is refused.

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
  -> FINAL_READINESS_READY
  -> EXPECTED_HEAD_RECHECKED
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

PROPOSED: Supervisor override must be explicit, recorded, scoped, time-bound, and linked to exact candidate SHA. Overrides cannot bypass complete enumeration, exact-head enforcement, or post-merge sentinel.

## Proof And Readiness Schemas

PROPOSED:

- `CHANGE_MANIFEST.json`
- `INTENT_MATCH.json`
- `PROTECTED_SURFACE_HITS.json`
- `CANDIDATE_WITNESS.json`
- `MERGE_READINESS.json`
- `MERGE_EXECUTION.json`
- `POST_MERGE_SENTINEL.json`

All schemas include `schema_version`, `created_at`, `repo`, `base_branch`, `candidate_head_sha`, and `candidate_tree_sha` where applicable.

## GitHub Enforcement Posture

PROPOSED: GitHub branch protection remains necessary but not sufficient. The repository should add final readiness as a required check only after the final gate is implemented and self-deadlock behavior is proven.

## Historical Replay Requirements

PROPOSED: Replay cases:

- #932 must block without explicit ConPort migration/proof deletion intent.
- #1025 must block without explicit MCP runtime/proof/test deletion intent.
- #1038 must classify as Palette/Jules source and block on unresolved review threads and missing exact proof.
- A legitimate #1026-style mass deletion must pass only with explicit mass-deletion intent and protected-surface gates.

## Rollout Stages

1. Observe only.
2. Advisory intake.
3. Candidate sanitizer dry-run.
4. Required final readiness on protected surfaces.
5. Required final readiness on all agent provenance classes.
6. Transactional merge executor.
7. Post-merge sentinel enforcement.

## Acceptance Criteria

PROPOSED: The architecture is implemented only when historical replay, canary classification, exact-candidate proof, final readiness, expected-head merge, and post-merge sentinel all pass in CI and local proof runs.

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
