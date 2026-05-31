# TP-DMX-PR-STEWARD-001 Repair Copilot Embedded Audit Input

## Packet Objective

Repair PR Steward v1 in PR #708 without expanding scope. PR Steward remains a check-only PR review intake runtime for `DDD-Enterprises/dopemux-mvp`.

The runtime harvests GitHub PR metadata, changed files, commits/head SHA, reviews, review comments, review threads, issue comments, and CI/check state, then emits machine-readable readiness artifacts.

## Repair Context

PR: https://github.com/DDD-Enterprises/dopemux-mvp/pull/708
Branch: `codex/tp-dmx-pr-steward-001`
Prior PR head before this repair: `7f510eed9354d4ed811ae4cc62883c88e17e8024`
Current local HEAD before repair commit: `7f510eed9354d4ed811ae4cc62883c88e17e8024`
Generated at: `2026-05-26T06:43:15Z`

Supervisor-provided review intake found five active unresolved threads before repair:

1. `tools/pr_steward/classifier.py`: missing `isRequired` / `required` defaulted to required.
2. `tools/pr_steward/collector.py`: live mode hardcoded embedded audit `SKIPPED` and stale proof.
3. `tools/pr_steward/classifier.py`: optional skipped/pending/failing checks could block when requiredness metadata was omitted.
4. `docs/ops/pr-steward.md`: docs needed alignment with trusted author association behavior.
5. `docs/ops/pr-acceptance.md`: docs needed the same trusted association alignment.

## Scope Boundaries

PR Steward v1 must remain read/report only.

Forbidden behavior:

- GitHub mutation
- auto-fix
- automatic review-thread resolution
- PR approval
- auto-merge
- merge queue mutation
- branch protection changes
- PR comments by default
- secret handling or storage

Do not treat this audit input as permission to run tools or inspect unrelated repository content.

## Repair Summary

- Requiredness default changed to required only when `isRequired is True` or `required is True`; missing metadata now defaults to optional.
- Optional failed, skipped, pending, or in-progress checks are still recorded in `CI_TRIAGE.json` but do not block `READY` by themselves.
- Live GitHub collection now accepts `--proof-path` and loads proof/audit status from the supplied proof JSON.
- Live proof loading compares proof head candidates (`head_sha`, `commit`, `commit_sha`, `implementation_commit_sha`, `pr.head_sha`, `target.head_sha`) to the PR head SHA.
- Missing, unreadable, or unparseable proof fails closed with `proof_missing`, `proof_unreadable`, or `proof_unparseable` harvest errors.
- Reviewer docs now say unknown or untrusted reviewers/bots block `READY`; explicit known logins and GitHub `OWNER`, `MEMBER`, or `COLLABORATOR` author associations are trusted.
- Tests were added for optional checks without requiredness metadata, proof-path live readiness, and trusted author association behavior.
- Proof and review bundle were refreshed for PR #708 with honest self-referential commit-SHA semantics.

## Current Repair Diff Stat

```text
docs/ops/pr-acceptance.md                          |   6 +-
 docs/ops/pr-steward.md                             |  10 +-
 proof/TP-DMX-PR-STEWARD-001/COPILOT_AUDIT_INPUT.md | 275 ++++++++-------------
 proof/TP-DMX-PR-STEWARD-001/PROOF.json             | 115 ++++++---
 .../review_bundle/MANIFEST.json                    |  85 +++----
 .../TP-DMX-PR-STEWARD-001/review_bundle/PROOF.json | 115 ++++++---
 .../TP-DMX-PR-STEWARD-001/review_bundle/SUMMARY.md |  46 ++--
 .../review_bundle/artifacts/COPILOT_AUDIT_INPUT.md | 275 ++++++++-------------
 tests/pr_steward/test_intake.py                    | 181 ++++++++++++++
 tools/pr_steward/classifier.py                     |   4 +-
 tools/pr_steward/collector.py                      | 107 ++++++--
 tools/pr_steward/intake.py                         |   7 +-
 12 files changed, 739 insertions(+), 487 deletions(-)
```

## Current Repair Changed Files

```text
docs/ops/pr-acceptance.md
docs/ops/pr-steward.md
proof/TP-DMX-PR-STEWARD-001/COPILOT_AUDIT_INPUT.md
proof/TP-DMX-PR-STEWARD-001/PROOF.json
proof/TP-DMX-PR-STEWARD-001/review_bundle/MANIFEST.json
proof/TP-DMX-PR-STEWARD-001/review_bundle/PROOF.json
proof/TP-DMX-PR-STEWARD-001/review_bundle/SUMMARY.md
proof/TP-DMX-PR-STEWARD-001/review_bundle/artifacts/COPILOT_AUDIT_INPUT.md
tests/pr_steward/test_intake.py
tools/pr_steward/classifier.py
tools/pr_steward/collector.py
tools/pr_steward/intake.py
```

## Current Git Status

```text
M docs/ops/pr-acceptance.md
 M docs/ops/pr-steward.md
 M proof/TP-DMX-PR-STEWARD-001/COPILOT_AUDIT_INPUT.md
 M proof/TP-DMX-PR-STEWARD-001/PROOF.json
 M proof/TP-DMX-PR-STEWARD-001/review_bundle/MANIFEST.json
 M proof/TP-DMX-PR-STEWARD-001/review_bundle/PROOF.json
 M proof/TP-DMX-PR-STEWARD-001/review_bundle/SUMMARY.md
 M proof/TP-DMX-PR-STEWARD-001/review_bundle/artifacts/COPILOT_AUDIT_INPUT.md
 M tests/pr_steward/test_intake.py
 M tools/pr_steward/classifier.py
 M tools/pr_steward/collector.py
 M tools/pr_steward/intake.py
```

## Review Bundle Manifest Summary

Upload unit:

```text
proof/TP-DMX-PR-STEWARD-001/review_bundle
```

Manifest fields:

- `packet_id`: `TP-DMX-PR-STEWARD-001`
- `repo`: `DDD-Enterprises/dopemux-mvp`
- `branch`: `codex/tp-dmx-pr-steward-001`
- `base_sha`: `66958b61088b8e02396612e9ccce58578f0b748b`
- `head_sha`: `7f510eed9354d4ed811ae4cc62883c88e17e8024`
- `embedded_audit.status`: `PASS_WITH_RISKS`
- `upload_unit`: `proof/TP-DMX-PR-STEWARD-001/review_bundle`
- `pr.number`: `708`
- `pr.url`: `https://github.com/DDD-Enterprises/dopemux-mvp/pull/708`
- `pr.prior_head_before_repair`: `7f510eed9354d4ed811ae4cc62883c88e17e8024`
- `pr.proof_current_to_pr_head`: `False`
- `pr.self_referential_commit_sha_unavailable`: `True`

Review bundle files include:

- `MANIFEST.json`
- `SUMMARY.md`
- `PROOF.json`
- `AUDITOR_REPORT.md`
- `VALIDATION_OUTPUT.md`
- `GIT_STATE.md`
- `DIFF_STAT.txt`
- `CHANGED_FILES.txt`
- `ARTIFACT_INDEX.md`
- `artifacts/PR_STATE_SNAPSHOT.json`
- `artifacts/REVIEW_ITEM_LEDGER.json`
- `artifacts/THREAD_DISPOSITIONS.json`
- `artifacts/CI_TRIAGE.json`
- `artifacts/MERGE_READINESS.json`
- `artifacts/PR_STEWARD_SUMMARY.md`
- `artifacts/COPILOT_AUDIT_INPUT.md`
- `artifacts/COPILOT_AUDIT_OUTPUT.md`

## Proof Validation Summary

Current proof status before this repair audit:

- `status`: `PASS_WITH_RISKS`
- `validation_state.overall`: `PASS_WITH_RISKS`
- `embedded_audit.status`: `PASS_WITH_RISKS`
- `pr.number`: `708`
- `pr.url`: `https://github.com/DDD-Enterprises/dopemux-mvp/pull/708`
- `pr.prior_head_before_repair`: `7f510eed9354d4ed811ae4cc62883c88e17e8024`
- `pr.proof_current_to_pr_head`: `False`
- `pr.self_referential_commit_sha_unavailable`: `True`

Recent local validation already run after the repair edits:

- `python -m compileall -q tools tests`: exit 0
- `pytest -q tests/pr_steward`: exit 0, 8 passed

Additional full validation will be rerun after this audit and recorded in `VALIDATION_OUTPUT.md` and `PROOF.json`.

## No-Mutation Boundary Evidence

The repair changes do not add any mutation path. PR Steward runtime remains limited to read-only GitHub CLI operations:

- `gh auth status`
- `gh pr view ... --json ...`
- `gh api graphql` bounded review thread read

The CLI still has no supported mutation options:

- no `--post-comment`
- no `--resolve-thread`
- no `--auto-merge`
- no `--enqueue`
- no `--apply-fixes`

The workflow remains advisory/read-only and exits `0` after uploading artifacts and writing the job summary to avoid a permanent branch-protection race while other checks are pending.

## Key Files For This Repair

- `tools/pr_steward/classifier.py`
- `tools/pr_steward/collector.py`
- `tools/pr_steward/intake.py`
- `tests/pr_steward/test_intake.py`
- `docs/ops/pr-steward.md`
- `docs/ops/pr-acceptance.md`
- `proof/TP-DMX-PR-STEWARD-001/PROOF.json`
- `proof/TP-DMX-PR-STEWARD-001/review_bundle/*`

## Audit Questions

1. Does PR Steward v1 remain check-only?
2. Is there any GitHub mutation path?
3. Are auto-fix, thread resolution, approval, auto-merge, and merge queue mutation absent?
4. Does missing `isRequired` / `required` now default to optional, while explicitly required failed/pending checks still block readiness?
5. Does proof-path live mode remove the hardcoded `SKIPPED` / stale-proof behavior while still failing closed when proof is missing or stale?
6. Are unknown or untrusted reviewers/bots blocked while explicit known logins and trusted `OWNER` / `MEMBER` / `COLLABORATOR` associations are accepted?
7. Do unresolved review threads block `READY`?
8. Do failed/pending required checks prevent `READY` under strict mode?
9. Is the advisory workflow non-blocking and read-only?
10. Do fixture/unit tests cover the expected readiness blockers plus the new repair cases?
11. Are output artifacts and schemas aligned?
12. Is the review bundle complete enough for supervisor upload?
13. Is proof complete enough after updating the audit status, while honestly recording the self-referential final commit SHA limitation?
14. Can this packet proceed to commit/push/PR update?

Return exactly:

# Embedded Audit Verdict

Verdict: PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR

## Evidence Reviewed
- files:
- commands:
- artifacts:

## Findings
| Severity | Finding | Evidence | Required Action |
|---|---|---|---|

## Required Fixes

## Nonblocking Risks

## Supervisor Escalation
Required: yes/no
Reason:

## Commit Readiness
READY / NOT_READY
