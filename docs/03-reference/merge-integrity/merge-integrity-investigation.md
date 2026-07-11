---
id: merge-integrity-investigation
title: Merge Integrity Investigation
type: reference
owner: '@hu3mann'
author: Codex
date: '2026-07-11'
status: proposed
last_review: '2026-07-11'
next_review: '2026-10-09'
prelude: Merge Integrity Investigation (reference) for dopemux documentation and developer
  workflows.
---
# Merge Integrity Investigation

Packet: `TP-DMX-MERGE-INTEGRITY-0001`

## Executive Verdict

OBSERVED: `origin/main` for this run is `b176747b339685e781de04268c46b7ae123abfbf`, matching the supervisor-reported restoration baseline. The latest confirmed clobber, PR #1025, removed 137 files with 27,676 deletions, including the MCP runtime stack, tests, proofs, and docs. PR #1037 restored that stack at the execution base.

OBSERVED: PR #932 removed the ConPort migration foundation and proof artifacts; PR #936 restored them. CONFLICTING: Current Git and GitHub evidence does not reproduce PR #720 as a destructive deletion clobber. PR #720 landed one UI file change, while PR #734 later added the reported Task Orchestrator Claude command surface and protocols. The #720 causal story remains unresolved in this packet.

PROPOSED: Agent-produced branches must be treated as untrusted patch sources, not direct merge candidates. The durable fix is a fresh-base candidate sanitizer plus exact-candidate readiness and merge admission.

## Execution Base

OBSERVED:

- supervisor_reported_base_sha: `b176747b339685e781de04268c46b7ae123abfbf`
- actual_execution_base_sha: `b176747b339685e781de04268c46b7ae123abfbf`
- difference_if_any: none observed
- worktree: `/Users/hue/code/dopemux-merge-integrity-0001`
- branch: `codex/tp-dmx-merge-integrity-0001-investigation-adr`

## Evidence Sources

OBSERVED evidence is stored under `proof/TP-DMX-MERGE-INTEGRITY-0001/raw/`.

- GitHub repository settings: `repository-settings.json`, `repository-rest.json`
- Branch protection and rulesets: `main-protection.json`, `rulesets.json`, `ruleset-details.json`
- PR metadata, files, diffs, and local landed deltas: `raw/pr-720`, `raw/pr-734`, `raw/pr-917`, `raw/pr-932`, `raw/pr-936`, `raw/pr-1025`, `raw/pr-1037`, `raw/pr-1038`
- PR #1038 review threads: `raw/pr-1038/review-threads.json`
- PR Steward read-only run for #1038: `raw/pr-steward-1038/`
- Governance searches and copied source files: `raw/governance-pattern-search.txt`, `raw/files/`

## Incident Timeline

OBSERVED:

| Incident | Clobber PR | Repair PR | Landed effect |
|---|---:|---:|---|
| A | #720 | #734 | CONFLICTING: #720 landed one UI file delta; #734 added the reported Task Orchestrator Claude command surface. |
| B | #932 | #936 | Removed ConPort migration gate source, proof, and packet artifacts. |
| C | #1025 | #1037 | Removed MCP runtime modules, tests, proofs, docs, and configuration surfaces. |

## Incident Mechanics

### PR #720 / #734

OBSERVED: PR #720 metadata shows base `74455398397305d3f630ac4c4b8b8f8f36b5a683`, head `4869ea3c56094543e67720138a5d079afb4e5327`, merge `fbcae03d61ea87018467dba24d93f5fadef98105`, and one changed file.

OBSERVED: The landed delta for PR #720 is `ui-dashboard/src/App.tsx` with 13 insertions and 11 deletions. No landed deletion of the Task Orchestrator Claude surface was observed in this packet.

CONFLICTING: PR #734 title and contents indicate restoration of the Task Orchestrator Claude surface, but current evidence does not prove that PR #720 caused the loss. Additional historical evidence is needed before treating #720 as the same class of stale-branch clobber as #932 and #1025.

### PR #932 / #936

OBSERVED: PR #932 metadata shows base `c45b2c8e7a995b3d47537367d909fafaa7ac12cf`, head `92ba9980b51b0d22b3859042343c652fa9eb46dc`, merge `559d7e2fa6ba5335763a57a1fe0dbe79b0e1dfa1`, 19 changed files, 105 additions, and 2,523 deletions.

OBSERVED: The landed delta deleted `docker/mcp-servers-source/conport/migrations/conport_migration_gate.py`, ConPort migration proof files, and `task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json`.

OBSERVED: PR #936 restored the migration gate source and proof artifacts. Current evidence supports repair status `COMPLETE` for the lost surfaces inspected in this packet.

### PR #1025 / #1037

OBSERVED: PR #1025 metadata shows base `7f904d78e01702d2d21b0ac953eb3b8611dda971`, head `9e06272c6934007bfb82677973d39a2b381e622a`, merge `8af764b142587ea4421b5a361c5892e804537793`, 137 changed files, 394 additions, and 27,676 deletions.

OBSERVED: The landed delta deleted MCP runtime files under `src/dopemux/mcp/`, corresponding unit tests under `tests/unit/test_mcp_*`, proof bundles under `proofs/mcp-runtime/`, and MCP runtime docs.

OBSERVED: GitHub refused the patch endpoint for PR #1025 with a 20,000 line limit. Local git diffs are therefore required evidence for this incident.

OBSERVED: PR #1037 restored 132 files with 27,517 insertions. Current evidence supports repair status `COMPLETE` for the deleted MCP runtime stack, with one reserved-singleton regression remaining open and out of scope for this packet.

## Repair Completeness

OBSERVED:

- #936 restored the ConPort migration gate and proof surfaces deleted by #932.
- #1037 restored the MCP runtime stack deleted by #1025.

UNKNOWN:

- #720/#734 causality is not proven from current PR and git evidence.
- No integration execution was performed for restored MCP runtime behavior in this packet.

## Current Controls Inventory

OBSERVED:

- Classic branch protection exists for `main`.
- Required status checks are configured: security review, documentation check, identity check, unit tests, CodeQL analyses, and CI summary.
- Strict up-to-date status is enabled in classic branch protection.
- Conversation resolution is required.
- Force pushes and branch deletion are blocked.
- Required approving review count is 0.
- Code owner review is not required.
- Stale reviews are not dismissed on push.
- Last-push approval is not required.
- Administrators are not enforced by classic protection.
- Ruleset `Default branch protection (restored after history rewrite)` is active for the default branch and allows squash and rebase merge methods.

CONFLICTING:

- Repository settings report merge commits, squash, and rebase as allowed, while the active default-branch ruleset pull request rule lists squash and rebase. Enforcement interaction should be treated as GitHub-policy-specific unless verified at merge time.

## Controls Failure Analysis

OBSERVED: `.github/workflows/ci-complete.yml` uses `git diff --name-only --diff-filter=ACMR` for root hygiene input. This excludes deletions.

OBSERVED: `src/dopemux_pr_merge_specialist/validation.py` and the vendored skill copy use `--diff-filter=ACMR` to collect changed files for validation. This excludes deletions.

OBSERVED: `.github/workflows/pr-steward.yml` runs the steward with `continue-on-error: true`, captures the exit code, and exits `0`, making the workflow advisory.

OBSERVED: The same workflow first refreshes audit proof with `scripts.audit.pr_audit_router --dry-run`. The router writes `executed: false` but still emits `embedded_audit.status: PASS`.

INFERRED: Deletion-blind validation plus advisory readiness lets destructive regressions present as narrow UI work, especially when intent is expressed only in PR title/body text.

## Branch Protection And Ruleset Posture

OBSERVED: Branch protection and rulesets reduce some merge risk but are insufficient for merge-integrity admission. They do not bind PR intent to machine-enforced path scope, do not classify agent provenance, and do not prove exact candidate trees after audit.

UNKNOWN: Merge queue posture was not proven from captured repository settings.

## PR Steward Race And Failure Modes

OBSERVED: The steward harvests PR state and review threads read-only, but review thread pagination is capped at the first 100 threads and first 50 comments per thread.

OBSERVED: A strict read-only run against PR #1038 exited `2` with readiness `BLOCKED`, mutation_performed `false`, and blockers including `HARVEST_INCOMPLETE`, `UNRESOLVED_REVIEW_THREAD`, `EMBEDDED_AUDIT_SKIPPED`, and `PROOF_MISSING`.

INFERRED: PR Steward is useful as intake but cannot be the final merge-admission authority while it is advisory, proof-file-dependent, and not bound to an exact sanitized candidate tree.

## Audit-Proof Integrity

OBSERVED: `scripts/audit/pr_audit_router.py` is dry-run by default. Its proof builder sets `executed: false` while also setting `embedded_audit.status: PASS`.

OBSERVED: `.github/workflows/pr-steward.yml` refreshes that dry-run proof immediately before running PR Steward.

PROPOSED: Dry-run or skipped audits must never produce a passing embedded-audit status. Audit proof must be bound to head SHA, tree SHA, diff hash, route invocation, model/tool metadata, and auditor verdict.

## Changed-File Pagination

OBSERVED: GitHub file enumeration matched reported changed file counts for PRs #720, #734, #917, #932, #936, #1025, #1037, and #1038.

OBSERVED: GitHub patch retrieval for PR #1025 failed because the diff exceeded the maximum number of lines. Complete local git diff capture is necessary for large destructive changes.

## Required Check Determination

OBSERVED: Branch protection lists required checks by context, but PR Steward final readiness is not observed as a required check. `tools/pr_steward/classifier.py` treats check `isRequired` fields as input evidence, but does not itself enforce branch protection.

PROPOSED: Required checks for merge-integrity admission should be repository-declared in policy and consumed by a final readiness gate.

## Agent Provenance

OBSERVED: PR #1038 is an open Palette/Jules candidate with head `283d6667933f2fd161992088731b7a6f8024f001`, branch `palette-task-skip-soft-confirm-774176508838366537`, and changed files `.Jules/palette.md`, `TaskSequencer.tsx`, and its accessibility test.

OBSERVED: PR author alone is insufficient executor identity evidence. PR #1038 issue/comment harvest included `google-labs-jules`, and PR Steward classified that author as unknown.

PROPOSED: Provenance classes must be derived from multiple signals: branch naming, file markers, author/comment actors, commit metadata, explicit packet provenance, and trusted operator overrides.

## PR #1038 Canary

OBSERVED: PR #1038 has four unresolved review threads and no pagination overflow. The current P2 review identifies global skip-confirmation state in `TaskSequencer.tsx`, where confirmation for one task can be reused for another.

OBSERVED: PR #1038 can be evaluated read-only against intent and scope without trusting its title or source branch. It should remain blocked until review threads, proof, and exact candidate readiness are resolved.

## Reserved-Singleton Regression

OBSERVED_OPEN_REGRESSION: PR #1037 has an unresolved P2 review on `src/dopemux/mcp/port_allocator.py` line 382. Current code still blocks reserved-singleton port export when 7890 is occupied by an unknown process, and `tests/unit/test_mcp_port_allocator.py` asserts that blocked behavior.

OUT_OF_SCOPE: This packet must not fix the runtime regression. It should become a separate remediation packet.

## Root-Cause Model

OBSERVED / INFERRED:

| Layer | Classification |
|---|---|
| L1 source-branch staleness | CONTRIBUTING_CAUSE for #932/#1025 |
| L2 unauthorized destructive patch | PRIMARY_CAUSE for #932/#1025 |
| L3 missing machine-readable intent | CONTRIBUTING_CAUSE |
| L4 deletion-blind validation | DETECTION_FAILURE |
| L5 incomplete GitHub harvest | PROCESS_RISK, observed for patch-size limits |
| L6 advisory readiness enforcement | DETECTION_FAILURE |
| L7 synthetic or stale audit proof | DETECTION_FAILURE |
| L8 weak or bypassable branch rules | PROCESS_RISK |
| L9 review timing and stale approval | PROCESS_RISK |
| L10 missing exact-candidate transactional merge | PRIMARY_CAUSE |
| L11 missing post-merge tree witness | DETECTION_FAILURE |
| L12 local worktree accumulation | PROCESS_RISK |

## Remaining Risks

UNKNOWN: GitHub merge queue posture and complete bypass actor list were not fully proven beyond captured protection/ruleset payloads.

OBSERVED: Primary checkout remains dirty with unrelated local changes; the dedicated worktree used this packet's branch and marked `.claude/claude_config.json` skip-worktree locally after an automatic per-worktree MCP config rewrite.

OBSERVED: PR #1038 changed-head risk remains live while the PR is open. Any implementation packet using it as canary must refresh evidence immediately before mutation.

## Final Design Recommendation

PROPOSED: Adopt fresh-base patch sanitization and exact-candidate merge admission. Agent branches provide patch material only. Authorized changes are re-applied onto current `main`, checked against machine-readable intent and protected-surface policy, audited against the exact candidate tree, merged only if expected head matches, and verified after merge by a landed-tree witness.
