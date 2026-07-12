---
id: merge-integrity-implementation-series-plan
title: Merge Integrity Implementation Series Plan
type: reference
owner: '@hu3mann'
author: Codex
date: '2026-07-11'
status: proposed
last_review: '2026-07-11'
next_review: '2026-10-09'
prelude: Merge Integrity Implementation Series Plan (reference) for dopemux documentation
  and developer workflows.
---
# Merge Integrity Implementation Series Plan

This plan does not author full implementation packets. It orders the packet series needed after supervisor review of `ADR-DMX-MERGE-INTEGRITY-0001` and `DMX-MIA-0001`.

## Packet Order

| Packet | Objective | Dependency | Risk | Allowed surface | Implementer route | Auditor route | Rollout | Rollback boundary |
|---|---|---|---|---|---|---|---|---|
| `TP-DMX-MERGE-INTEGRITY-0002` | Deletion-aware complete enumeration and destructive-diff visibility | ADR review | High | tests, schemas, steward/merge-specialist enumeration | Codex or Claude Code | independent Sonnet/Gemini | observe-only | revert enumeration package |
| `TP-DMX-MERGE-INTEGRITY-0003` | Change Intent and Protected Surface policy contracts | 0002 | High | schemas, policy config, docs | Codex | independent Sonnet | advisory | revert policy contract |
| `TP-DMX-MERGE-INTEGRITY-0004` | Audit-proof correction and two-stage PR Steward | 0002, 0003 | High | scripts/audit, tools/pr_steward, workflows, schemas | Codex or Claude Code | independent Sonnet plus targeted Gemini | advisory then required dry-run | revert steward/audit changes |
| `TP-DMX-MERGE-INTEGRITY-0005` | Fresh-base Candidate Sanitizer and provenance binding | 0002, 0003, 0004 | Critical | new sanitizer module, tests, proof schemas | Claude Code with Codex review | Sonnet/Opus architecture audit | dry-run candidate PRs | delete sanitizer gate |
| `TP-DMX-MERGE-INTEGRITY-0006` | Transactional merge executor and exact base/parent/head/tree revalidation | 0005 | Critical | merge-specialist executor, GitHub workflow, schemas | Claude Code with Codex review | Sonnet plus GitHub-state review | protected-surface required gate | disable executor check |
| `TP-DMX-MERGE-INTEGRITY-0007` | Post-merge sentinel, historical replay, and worktree hygiene reporting | 0006 | High | sentinel, replay fixtures, hygiene reporter | Codex | Gemini broad contradiction review | report-only then required sentinel | disable sentinel enforcement |

## Packet Details

### TP-DMX-MERGE-INTEGRITY-0002

Objective: Replace deletion-blind authoritative changed-file inventory with complete enumeration.

Validation gates:

- Unit tests for deleted, renamed, copied, type-changed, executable-bit, symlink, submodule, and binary cases.
- Replay #932 and #1025 manifests include the deleted protected paths.
- Existing scoped lint commands may still use filtered inputs if clearly non-authoritative.

Proof requirements:

- `CHANGE_MANIFEST.json`
- before/after command log
- historical replay output

Stop conditions:

- Any required GitHub file enumeration cannot be paginated completely.
- Any complete local git enumeration disagrees with expected fixture data.

### TP-DMX-MERGE-INTEGRITY-0003

Objective: Add machine-readable Change Intent and Protected Surface policy contracts.

Validation gates:

- JSON schema validation.
- Policy fixtures for #932, #1025, #1038, and legitimate mass deletion.
- Unknown provenance and missing intent block.

Proof requirements:

- schema validation
- policy match matrix
- supervisor override examples

Stop conditions:

- Policy tries to infer authorization from PR title/body alone.
- Protected surfaces cannot represent proof, workflow, schema, and MCP runtime paths.

### TP-DMX-MERGE-INTEGRITY-0004

Objective: Correct audit proof semantics and split PR Steward into intake and final readiness.

Validation gates:

- Dry-run and skipped audits cannot produce `PASS`.
- PR Steward read-only mutation invariant test.
- Final readiness blocks on stale proof, unresolved threads, missing proof, unknown reviewer, failed/pending required checks, incomplete harvest.
- No self-deadlock on final readiness check.

Proof requirements:

- `MERGE_READINESS.json`
- audit proof schema validation
- canary PR #1038 read-only run

Stop conditions:

- Required-check list cannot be determined without self-reference.
- Proof freshness cannot bind to head SHA and tree/diff hash.

### TP-DMX-MERGE-INTEGRITY-0005

Objective: Build fresh-base Candidate Sanitizer and provenance binding.

Validation gates:

- Candidate starts from current `main`.
- Authorized patch application preserves current-base unrelated files.
- Same-file conflicts block.
- Binary, submodule, symlink, executable-bit, generated lockfile, and proof-only cases are classified.
- #932 and #1025 block without explicit destructive intent.

Proof requirements:

- `CANDIDATE_WITNESS.json`
- candidate diff hash
- provenance classification ledger

Stop conditions:

- Sanitizer imports source branch tree wholesale.
- Any protected-surface deletion is allowed by heuristic only.

### TP-DMX-MERGE-INTEGRITY-0006

Objective: Add transactional merge executor, expected-base revalidation, and protected-reference capability qualification.

Validation gates:

- Expected base, candidate parent, head, or tree mismatch refuses merge.
- Non-forced protected-reference update is the only proposed atomic primitive for agent and unknown provenance; normal PR merge is forbidden as their fallback.
- Controlled race advances `main` after readiness and proves stale candidate refusal.
- Qualification proves token permissions, protection, checks, and PR semantics before enablement.
- Candidate construction, validation, and readiness run from trusted source only.
- Changed reviews, review threads, checks, policy, labels, or base SHA invalidate readiness.
- Executor cannot mutate existing source PR.
- Every existing merge-specialist and workflow mutation path is classified and either bound to sanitized admission or rejected for agent and unknown provenance.
- Human-managed and dependency-automation residual merge paths are explicitly policy-bound; ambiguous provenance fails closed.

Proof requirements:

- `MERGE_EXECUTION.json`
- expected-base/head recheck log
- dry-run, controlled race fixture, and protected-reference qualification record

Stop conditions:

- Protected reference cannot advance under repository rules, or race behavior differs from documented non-fast-forward semantics.
- Executor needs broad write scope beyond merge and status reporting.

### TP-DMX-MERGE-INTEGRITY-0007

Objective: Add post-merge sentinel, historical replay, and worktree hygiene reporting.

Validation gates:

- Sentinel detects landed tree mismatch.
- Sentinel reports without automatic broad revert.
- Historical replay proves #932/#1025 block and legitimate mass deletion can pass.
- Worktree hygiene reporter is report-only by default.

Proof requirements:

- `POST_MERGE_SENTINEL.json`
- replay matrix
- hygiene report

Stop conditions:

- Sentinel tries to reset or revert `main` automatically.
- Hygiene reporter becomes merge authority.

## Separate Remediation Packet

Documentation remediation for this draft PR is `TP-DMX-MERGE-INTEGRITY-0001R-PR1040-SUPERVISOR-REMEDIATION`. It is not a numbered implementation-series packet and must not consume `0004`.

**Series-ID custody note (OBSERVED after PR #1042):** the trusted-audit foundation that landed on `main` as PR #1042 used packet id `TP-DMX-MERGE-INTEGRITY-0004-TRUSTED-AUDIT-FOUNDATION`. That is a foundation/remediation identity, not completion of the full series-plan objective for `0004` (audit-proof correction and two-stage PR Steward). Remaining series-plan `0004` work must:

1. treat the landed foundation as a dependency, not as already-finished two-stage Steward;
2. avoid a second competing packet id that reuses `0004` for unrelated scope;
3. keep remediation suffixes (`0001R`, `0004-TRUSTED-AUDIT-FOUNDATION`) distinct from future implementation slices.

PR #1040 remediation uses `0001R` only and does not claim series `0002`–`0007` implementation.

Proposed packet: `TP-DMX-MCP-RUNTIME-RESERVED-SINGLETON-PORT-REPAIR-001`

Objective: Fix the observed reserved-singleton port allocator regression from PR #1037 review without mixing it into merge-integrity architecture work.

Dependency: none on merge-integrity series, but it should respect MCP runtime packet governance.

Stop condition: any attempt to treat runtime repair as proof that merge-integrity controls are implemented.
