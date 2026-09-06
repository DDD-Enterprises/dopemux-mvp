---
id: ops-pr-steward
title: PR Steward V1
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Check-only PR review intake and packaged CLI reference for PR Steward v1.
---
# PR Steward V1

## Purpose

PR Steward v1 is a check-only review-intake gate. It does not mutate GitHub, apply fixes, resolve threads, enqueue merges, approve PRs, or merge PRs.

**Evidence economy:** Steward still requires current exact-head gates and a current independent audit when the risk lane or packet requires one (L2/L3 / embedded-audit policy). Draft may be the only expected blocker before operator mark-ready. Proof-only successors must bind to the audited content head; path-escape or stale-head proofs fail closed. See `docs/03-reference/governance/evidence-economy.md`.

The v1 GitHub Actions workflow is advisory. It may emit `NOT_READY`, `NEEDS_IMPLEMENTER`, `NEEDS_SUPERVISOR`, or `BLOCKED` while other checks are still running, but it does not fail the workflow job for those readiness states and must not be configured as a required branch-protection check until the pending-check race is solved.

## Inputs

PR Steward must harvest:

- PR metadata
- changed files
- commits and head SHA
- reviews
- review comments
- review threads
- issue comments
- status checks and CI state
- current proof bundle and embedded audit status

## Required Outputs

| Output | Schema |
| --- | --- |
| `MERGE_READINESS.json` | `schemas/pr_steward/merge_readiness.schema.json` |
| `REVIEW_ITEM_LEDGER.json` | `schemas/pr_steward/review_item_ledger.schema.json` |
| `THREAD_DISPOSITIONS.json` | `schemas/pr_steward/thread_dispositions.schema.json` |
| `CI_TRIAGE.json` | `schemas/pr_steward/ci_triage.schema.json` |
| `PR_STATE_SNAPSHOT.json` | `schemas/pr_steward/pr_state_snapshot.schema.json` |

## Dispositions

Allowed review item dispositions:

- `AUTO_APPLIED`
- `MUST_FIX`
- `OPTIONAL_DEFERRED`
- `OUT_OF_SCOPE_FOLLOWUP`
- `REJECTED_WITH_REASON`
- `NEEDS_SUPERVISOR`
- `UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION`

`AUTO_APPLIED` is a status value only in this packet. It does not authorize automatic code edits.

## Fail-Closed Rules

Return `NOT_READY` or `NEEDS_SUPERVISOR` when:

- any reviewer, bot, review item, or check cannot be classified
- any blocking review thread is unresolved
- required CI failed, was cancelled, or is missing
- proof is stale, missing, or lacks a valid supervisor-accepted self-reference exception
- embedded audit is absent, failed, stale, or ordinarily skipped
- GitHub auth or API state cannot be proven
- any requested action would mutate GitHub state

Return `BLOCKED` when the harvest is incomplete, the PR is draft, or the PR is closed without explicit `--allow-closed`. Return `NEEDS_IMPLEMENTER` when concrete implementation work is required, such as unresolved threads or failed checks. Unknown or untrusted reviewers and bots always block `READY`.

One exact `SKIPPED` audit is nonblocking: `required=false` with
`skip_reason=AUDIT_NOT_REQUIRED_BY_TRUSTED_CHANGE_CONTRACT`. This records that
trusted change-contract classification did not require model audit; it is not a
`PASS` verdict and waives no other readiness gate. `MERGE_READINESS.json`
preserves `embedded_audit.required` and `embedded_audit.skip_reason`, and its
schema independently rejects `READY` with any other `SKIPPED` shape.

Explicit known reviewer logins are trusted. GitHub `authorAssociation` values `OWNER`, `MEMBER`, and `COLLABORATOR` are also trusted unless a future policy overrides that rule. External unknown actors and unclassified bots block `READY`.

Resolved and outdated review threads are historical evidence, not active blockers. When a raw review comment is linked to a resolved or outdated thread, PR Steward clears the stale `MUST_FIX` classification instead of keeping a false active blocker behind.

Proof freshness is fail-closed by default. A proof may be treated as current either by exact PR head match or by an explicit `CURRENT_WITH_SELF_REFERENCE_EXCEPTION` record that includes supervisor acceptance and proof-only changed-file evidence under `proof/`.

## Review Adjudication Receipts

TP-DMX-PR-STEWARD-COMMENTED-REVIEW-ADJUDICATION-001 adds one narrow,
exact-head trusted-adjudication mechanism: a top-level PR issue/conversation
comment, posted by a login in `trusted_security_release_approvers`
(`tools/pr_steward/known_reviewers.json`), may reclassify one existing
review's ledger disposition to `REJECTED_WITH_REASON` (nonblocking) using a
literal receipt body:

```text
PR_STEWARD_REVIEW_ADJUDICATION_V1
review_id=<exact GitHub review node id, e.g. PRR_...>
head_sha=<full 40-character current PR head SHA>
disposition=REJECTED_WITH_REASON
reason=<non-empty reason>
```

A receipt only clears a review when **all** of the following hold; any
failure fails closed and leaves the review's ordinary classification
(including any `MUST_FIX` from a `P1`/`P2` body marker) active:

- the review's own GitHub review state is exactly `COMMENTED` (never
  `CHANGES_REQUESTED` / `REQUEST_CHANGES` — that state is classified before
  a receipt is ever consulted, so it can never be adjudicated away);
- `review_id` names that exact review;
- `head_sha` exactly equals the PR's current head SHA (a receipt bound to a
  stale head never clears a review at a newer head, and vice versa);
- the comment author's login is in `trusted_security_release_approvers`;
- the receipt is well-formed (all four fields present, `disposition` is
  exactly `REJECTED_WITH_REASON`, `reason` non-empty, `head_sha` is a
  40-character hex string);
- exactly one distinct eligible receipt comment body exists for that
  `(review_id, head_sha)` pair, regardless of which trusted approver posted
  it — comparison is on the raw comment body byte-for-byte, not on the
  parsed fields, so two comments that parse to the same fields but differ
  in surrounding text still conflict, and clear nothing.

A valid receipt preserves the original review's ledger entry (same `id`,
unchanged `body`) and only changes `disposition`, `blocking`, and
`rationale` — it never deletes or rewrites historical review text, and it
never changes the review-item ledger's item count. The receipt comment
itself is always classified `REJECTED_WITH_REASON` / nonblocking when it is
well-formed and trusted, even when its `reason=` text quotes a `P1`/`P2`
token from the review it adjudicates — a receipt can never manufacture a
new blocker out of describing the finding it clears.

This mechanism never touches `CHANGES_REQUESTED` reviews, unresolved review
threads, CI, embedded-audit, proof, or security-release blockers — those
gates are unaffected and remain independently fail-closed.

## CLI

Repo-local invocation:

```bash
python -m tools.pr_steward.intake --repo DDD-Enterprises/dopemux-mvp --pr 704 --out /tmp/pr-steward-704 --strict --proof-path proof/TP-DMX-PR-STEWARD-001/PROOF.json
scripts/pr-steward --repo DDD-Enterprises/dopemux-mvp --pr 704 --out /tmp/pr-steward-704 --strict --proof-path proof/TP-DMX-PR-STEWARD-001/PROOF.json
```

Live mode fails closed when `--proof-path` is absent, unreadable, unparseable, or stale relative to the PR head SHA. Fixture mode may include proof state directly in `harvest.json`.

Fixture mode is the offline validation lane and must not require live GitHub:

```bash
python -m tools.pr_steward.intake --fixture-dir tests/fixtures/pr_steward/ready_all_green --repo DDD-Enterprises/dopemux-mvp --pr 704 --out /tmp/pr-steward-ready --strict
```

## Packaged Dopemux Command

TP-DMX-STEWARD-PACKAGE-301 adds the packaged operator surface:

```bash
dopemux pr-steward
```

The packaged command exposes `intake`, `bridge`, `gate`, `audit`, and a
fail-closed `doctor` placeholder. It is intentionally a single Dopemux CLI
surface and does not add new console scripts or scaffold repository files.

`steward_gate` logic ships in Python package code and must not be generated
into scaffold YAML.

## Packaged Command Boundaries

- No PR mutation is performed by `intake`, `bridge`, `gate`, or `audit`.
- `doctor` is report-only and currently exits blocked until TP303 implements
  scaffold/config skew checks.
- The command wraps existing engines; it does not change PR Steward classifier,
  Action Bridge compiler, or merge-specialist gate semantics.

## Review Bundle

For PR Steward packets, `proof/<PACKET_ID>/review_bundle/` is the single supervisor upload unit. The generated PR Steward outputs from fixture or live smoke runs must be copied into `review_bundle/artifacts/`, or listed in `review_bundle/MANIFEST.json` as excluded with a reason.

## Two Implementations, Two Schema Families — Not Interchangeable

There are **two separate PR Steward implementations** in this repository. They
are not variants of each other, do not share code, and their identically- or
similarly-named schema files are **not interchangeable**:

| | Dopemux PR Steward | PCP-Core readiness evaluator |
| --- | --- | --- |
| Code | `tools/pr_steward/*.py` (this document) | `src/dopemux/pcp/pr_steward.py` |
| Schemas | `schemas/pr_steward/*.json` | `schemas/project_control_plane/*.json` |
| Wired into | `.github/workflows/pr-steward.yml` | Not wired into any GitHub Actions workflow |
| Scope | Dopemux-specific: known-reviewer roster, security/release approval gate, embedded-audit binding, thread/comment ledger conservation (this document, in full) | Generic, project-agnostic PCP Core: advisory `MERGE_READINESS` signal from harvested PR intake, no Dopemux-specific classification |
| Nature | The gate this repository's branch protection is intended to enforce | A specialisable core that Dopemux's own gate co-exists with, per `src/dopemux/pcp/pr_steward.py`'s own module docstring — it does not replace it |

**Collision to watch**: both families ship a `merge_readiness.schema.json`
(`schemas/pr_steward/merge_readiness.schema.json` vs
`schemas/project_control_plane/merge_readiness.schema.json`). They describe
different `MERGE_READINESS.json` shapes produced by different code paths.
Validating one implementation's output against the other family's schema is
a bug, not a compatible substitution — always match code to its own schema
directory (`tools/pr_steward/*` → `schemas/pr_steward/*`; `src/dopemux/pcp/*`
→ `schemas/project_control_plane/*`).
