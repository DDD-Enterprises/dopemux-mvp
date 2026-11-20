---
id: TP-LTAIP-POST-012
title: Tp Ltaip Post 012
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Ltaip Post 012 (explanation) for dopemux documentation and developer workflows.
---
# Macro Packet: TP-LTAIP-POST-012

## Status

`CONDITIONAL_NOT_AUTHORIZED_UNTIL_BASE_SELECTION`

## Claim posture

- **OBSERVED:** Generic upstream work may reduce long-term drift.
- **PROPOSED:** Contribution preparation can be separated from external submission.
- **UNKNOWN:** Maintainer interest and acceptance.
- **CONFLICTING:** The best local workaround may be too product-specific for upstream.

## Objective

Prepare bounded, generic, maintainer-aligned upstream contribution bundles for exposure manifests, permission tests, documentation, or transaction-aware event primitives proven by H0, while preserving a bounded local fallback and avoiding a fork.

## Why this packet exists now

Private-only changes accumulate upgrade tax. Upstream work should proceed in parallel after selection, but cannot block delivery or leak product-specific policy.

## Risk and authorization

- Risk: `MEDIUM`
- Task class: `upstream contribution preparation`
- Authorization: `CONDITIONAL_AFTER_BASE_SELECTION`
- Series: `LTAIP-POST-SELECTION-001`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Supervisor review: mandatory

## Repository binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Repository snapshot used while authoring: `d844d71d9ec9b55905dbb545662fc5c0f989e87c`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `upstream/TP-LTAIP-POST-012-contribution-stream`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-POST-012`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-008`

## Scope IN

- Selected-base upstream issue/PR research.
- Generic tests, schemas, docs, and proven event primitive patches.
- Compatibility against upstream suite.
- Submission-ready bundle and operator approval plan.

## Scope OUT

- Automatic upstream issue or PR creation.
- Product-specific secret or routing policy.
- Blocking local delivery indefinitely.
- Long-lived fork.

## Invariants

- Packet 008 selects a base.
- Every contribution is generic and maintainer-aligned.
- No sensitive fixture or secret.
- External submission requires explicit operator approval.
- Local fallback remains bounded and documented.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-POST-012.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-POST-012.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/MERGE_READINESS.json`
- `scripts/leantime-ai-parity/upstream/materialize_upstream_sources.py`
- `scripts/leantime-ai-parity/upstream/build_contribution_bundle.py`
- `scripts/leantime-ai-parity/upstream/run_compatibility.py`
- `tests/prototypes/leantime-ai-parity/upstream/test_contribution_scope.py`
- `reports/leantime-ai-parity/upstream/patches/`
- `reports/leantime-ai-parity/upstream/contribution-register.json`
- `reports/leantime-ai-parity/upstream/compatibility-results.json`
- `reports/leantime-ai-parity/upstream/submission-readiness.json`
- `reports/leantime-ai-parity/upstream/manifest.json`
- `docs/06-research/leantime-ai-parity/upstream/contribution-strategy.md`
- `docs/06-research/leantime-ai-parity/upstream/maintainer-alignment.md`
- `docs/92-runbooks/leantime-ai-parity/upstream-submission.md`

No other path may be changed. Additional paths require a supervisor-approved packet revision.

## Worktree and dependency preflight

```bash
set -euo pipefail

test -f .dopetaskroot
test -s .repo_id
test -f pyproject.toml
git remote get-url origin | grep -Eq 'DDD-Enterprises/dopemux-mvp(\.git)?$'
test "$(git branch --show-current)" = "main"
test -z "$(git status --porcelain)"

git fetch origin main
git worktree add "../dopemux-mvp-wt-TP-LTAIP-POST-012" -b "upstream/TP-LTAIP-POST-012-contribution-stream" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-POST-012"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "upstream/TP-LTAIP-POST-012-contribution-stream"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-POST-012/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Research current upstream process and align scope

**Objective:** Materialize selected upstream source in tmp and document current contribution, security, and support expectations.

**Requirements**

- Use current official upstream docs.
- No external write.

**Commands**

```bash
python scripts/leantime-ai-parity/upstream/materialize_upstream_sources.py --decision reports/leantime-ai-parity/h0/base-selection/decision.json --output tmp/ltaip-upstream
python -m json.tool reports/leantime-ai-parity/upstream/contribution-register.json >/dev/null
```

**Expected artifacts**

- `reports/leantime-ai-parity/upstream/contribution-register.json`
- `docs/06-research/leantime-ai-parity/upstream/contribution-strategy.md`
- `docs/06-research/leantime-ai-parity/upstream/maintainer-alignment.md`

**Exit conditions**

- Each candidate contribution has maintainer-aligned rationale and rejected alternatives.
### Slice 2: Build generic contribution bundles

**Objective:** Create bounded patches/tests/docs for approved generic contribution candidates.

**Requirements**

- No product-specific secrets or policy.
- Patch applies to pinned upstream source.

**Commands**

```bash
python scripts/leantime-ai-parity/upstream/build_contribution_bundle.py --register reports/leantime-ai-parity/upstream/contribution-register.json --source tmp/ltaip-upstream --output reports/leantime-ai-parity/upstream/patches
```

**Expected artifacts**

- `reports/leantime-ai-parity/upstream/patches/`
- `docs/92-runbooks/leantime-ai-parity/upstream-submission.md`

**Exit conditions**

- Every patch has purpose, test, compatibility, rollback, and local fallback.
### Slice 3: Run upstream compatibility and review

**Objective:** Run upstream suites where available and produce submission readiness without posting externally.

**Requirements**

- Failures remain visible.
- No issue/PR creation.

**Commands**

```bash
python scripts/leantime-ai-parity/upstream/run_compatibility.py --source tmp/ltaip-upstream --patches reports/leantime-ai-parity/upstream/patches --output reports/leantime-ai-parity/upstream/compatibility-results.json
python -m pytest -q tests/prototypes/leantime-ai-parity/upstream
```

**Expected artifacts**

- `reports/leantime-ai-parity/upstream/compatibility-results.json`
- `reports/leantime-ai-parity/upstream/submission-readiness.json`

**Exit conditions**

- Submission readiness is PASS, NEEDS_REWORK, or REJECTED with evidence.
### Slice 4: Audit, proof, and operator submission gate

**Objective:** Run independent review and produce an operator-approved external submission plan.

**Requirements**

- No external mutation in this packet.
- Explicit approval required for later submission.

**Commands**

```bash
rm -rf tmp/ltaip-upstream
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-012.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/upstream
python -m json.tool reports/leantime-ai-parity/upstream/contribution-register.json >/dev/null
python -m json.tool reports/leantime-ai-parity/upstream/compatibility-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/upstream/submission-readiness.json >/dev/null
python -m json.tool reports/leantime-ai-parity/upstream/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/upstream/contribution-strategy.md docs/06-research/leantime-ai-parity/upstream/maintainer-alignment.md docs/92-runbooks/leantime-ai-parity/upstream-submission.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-012/PROOF.json
git diff --check
```

**Expected artifacts**

- `reports/leantime-ai-parity/upstream/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-012/AUDITOR_REPORT.md`

**Exit conditions**

- Contribution bundle is reviewed and no external write occurred.


## Required PAL chain

`apilookup -> analyze -> thinkdeep -> challenge -> planner -> consensus -> challenge -> implement -> testgen -> codereview -> precommit -> challenge`

Escalation rules:

- Use `apilookup` for current contributing rules.
- Use `consensus` for contribution versus local fallback.
- Use `secaudit` if permission or event code is involved.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Upstream scope mismatch.
- Hidden product policy.
- Sensitive fixtures.
- Unbounded fork fallback.
- External submission without approval.

## Validation gates

### Understanding gate

Pass only when all authority boundaries, candidate versions, dependency artifacts, and failure modes relevant to this packet are identified with at least `HIGH` confidence.

### Plan gate

Pass only when every slice has exact files, commands, output capture, rollback, and a measurable exit condition.

### Implementation gate

After each slice, run the smallest relevant checks, inspect the diff, and stop on unexplained drift.

### Diff gate

All material review findings must be resolved, accepted with evidence, or escalated. Scope escape is blocking.

### Final gate

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-012.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/upstream
python -m json.tool reports/leantime-ai-parity/upstream/contribution-register.json >/dev/null
python -m json.tool reports/leantime-ai-parity/upstream/compatibility-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/upstream/submission-readiness.json >/dev/null
python -m json.tool reports/leantime-ai-parity/upstream/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/upstream/contribution-strategy.md docs/06-research/leantime-ai-parity/upstream/maintainer-alignment.md docs/92-runbooks/leantime-ai-parity/upstream-submission.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-012/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-POST-012/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-POST-012/PRECOMMIT.txt
git diff --check
```

## Proof requirements

The committed proof must contain:

- git status before and after;
- start and end SHA;
- complete diff and diff stat;
- command, cwd, stdout, stderr, and exit code for every command;
- generated artifacts and their SHA-256 hashes;
- assumptions, contradictions, unknowns, and residual risks;
- embedded audit tool, model, invocation, exit code, findings, fixes, and remaining risks;
- PR URL, PR number, latest head SHA, checks, reviews, comments, threads, and bots;
- PR Steward `MERGE_READINESS.json` current to the latest head.

Completion cannot be `VERIFIED` when proof, audit, or checks are stale.

## PR Steward gate

PR Steward must classify every review item and block on unknown reviewers/bots, unresolved blocking threads, failed or pending required checks, stale proof, unclassified items, or allowlist escape.

A second GPT-5.6 supervisor adjudication is mandatory before merge.

## Rollback

- Discard or rescope unsubmitted contribution.
- Close a later submitted contribution only with operator approval.
- Do not create a fork as rollback.

## Stop conditions

Stop immediately when:

- Base selection is absent.
- Contribution is product-specific or sensitive.
- Patch cannot pass upstream tests.
- Maintainer process is unclear.
- External write would occur without approval.
- Audit blocks.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Contribution candidates, patches, compatibility, and submission-readiness.
- Explicit confirmation that no upstream write occurred.
