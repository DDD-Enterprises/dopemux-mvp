---
id: TP-LTAIP-H0-006
title: Tp Ltaip H0 006
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Ltaip H0 006 (explanation) for dopemux documentation and developer workflows.
---
# Macro Packet: TP-LTAIP-H0-006

## Status

`BLOCKED_BY_DEPENDENCIES_AND_OPERATOR_INPUT`

## Claim posture

- **OBSERVED:** Official plugins are separate package and license boundaries.
- **PROPOSED:** Authorized package inputs can be inspected in a disposable clean-room workflow.
- **UNKNOWN:** Which packages the operator will authorize and supply.
- **CONFLICTING:** A feature may exist technically while remaining commercially or operationally unsuitable.

## Objective

Qualify authorized official plugin packages as distinct licensed components using exact hashes, license/support terms, workflow evidence, ACL tests, sequential upgrades, export, backup, restore, rollback, and equivalent-scope cost.

## Why this packet exists now

Official labels and marketplace pages do not prove the package properties required for architecture or parity credit.

## Risk and authorization

- Risk: `HIGH`
- Task class: `package, license, and upgrade qualification`
- Authorization: `HORIZON_0_PACKAGE_REVIEW`
- Series: `LTAIP-H0-VALIDATION-001`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Supervisor review: mandatory

## Repository binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Repository snapshot used while authoring: `d844d71d9ec9b55905dbb545662fc5c0f989e87c`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `research/TP-LTAIP-H0-006-plugin-qualification`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-H0-006`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-001`
- `TP-LTAIP-H0-002`

## Scope IN

- Operator-authorized package files supplied outside git.
- Hash, license, support, migration, ACL, export, rollback, and sequential-upgrade review.
- Workflow outcome and equivalent-scope TCO.

## Scope OUT

- Purchasing packages.
- Crediting paid capability to Community Edition.
- Committing proprietary package contents.
- Production installation.
- Bypassing package license or access controls.

## Invariants

- Raw package contents are never committed.
- Execution stops when authorized package input is absent.
- Every package is treated as a distinct licensed component.
- No package receives feature credit before workflow and permission tests.
- No secret-pattern file enters proof.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-006.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-006.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/MERGE_READINESS.json`
- `scripts/leantime-ai-parity/h0/plugin-qualification/register_packages.py`
- `scripts/leantime-ai-parity/h0/plugin-qualification/scan_packages.py`
- `scripts/leantime-ai-parity/h0/plugin-qualification/run_package_matrix.py`
- `scripts/leantime-ai-parity/h0/plugin-qualification/calculate_package_tco.py`
- `scripts/leantime-ai-parity/h0/plugin-qualification/destroy_lab.sh`
- `tests/prototypes/leantime-ai-parity/h0/plugin-qualification/test_package_manifest.py`
- `tests/prototypes/leantime-ai-parity/h0/plugin-qualification/test_license_boundaries.py`
- `tests/prototypes/leantime-ai-parity/h0/plugin-qualification/test_disposition_matrix.py`
- `docs/06-research/leantime-ai-parity/h0/plugin-qualification/qualification-protocol.md`
- `docs/06-research/leantime-ai-parity/h0/plugin-qualification/license-and-support-review.md`
- `docs/06-research/leantime-ai-parity/h0/plugin-qualification/package-disposition.md`
- `reports/leantime-ai-parity/h0/plugin-qualification/input-register.json`
- `reports/leantime-ai-parity/h0/plugin-qualification/package-manifest.json`
- `reports/leantime-ai-parity/h0/plugin-qualification/test-results.json`
- `reports/leantime-ai-parity/h0/plugin-qualification/disposition-matrix.json`
- `reports/leantime-ai-parity/h0/plugin-qualification/manifest.json`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-006" -b "research/TP-LTAIP-H0-006-plugin-qualification" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-006"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "research/TP-LTAIP-H0-006-plugin-qualification"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-001/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-001/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-H0-006/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Register authorized package inputs

**Objective:** Fail closed unless the operator supplies approved package files through an external input directory.

**Requirements**

- Require `LTAIP_PLUGIN_INPUT_DIR`.
- Record package hash, filename, source, authorization reference, and license document.
- Do not copy raw packages into tracked paths.

**Commands**

```bash
test -n "${LTAIP_PLUGIN_INPUT_DIR:-}" || { echo BLOCKED_AUTHORIZED_PACKAGE_INPUT_REQUIRED; exit 42; }
python scripts/leantime-ai-parity/h0/plugin-qualification/register_packages.py --input "$LTAIP_PLUGIN_INPUT_DIR" --output reports/leantime-ai-parity/h0/plugin-qualification/input-register.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/plugin-qualification/input-register.json`
- `docs/06-research/leantime-ai-parity/h0/plugin-qualification/qualification-protocol.md`
- `docs/06-research/leantime-ai-parity/h0/plugin-qualification/license-and-support-review.md`

**Exit conditions**

- Every package has operator authorization and SHA-256.
- No raw package is staged.
### Slice 2: Inspect package, license, migrations, and permissions

**Objective:** Scan authorized packages without executing them and classify migrations, permissions, external calls, bundled code, and license/support terms.

**Requirements**

- Extraction occurs in tmp.
- Secret findings are redacted.
- Unknown code paths remain UNKNOWN.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/plugin-qualification/scan_packages.py --register reports/leantime-ai-parity/h0/plugin-qualification/input-register.json --output reports/leantime-ai-parity/h0/plugin-qualification/package-manifest.json
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/plugin-qualification/test_package_manifest.py tests/prototypes/leantime-ai-parity/h0/plugin-qualification/test_license_boundaries.py
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/plugin-qualification/package-manifest.json`
- `docs/06-research/leantime-ai-parity/h0/plugin-qualification/license-and-support-review.md`

**Exit conditions**

- Migrations, permissions, external endpoints, export paths, and license boundaries are classified.
### Slice 3: Run install, upgrade, ACL, backup, export, and rollback matrix

**Objective:** Test each package in disposable Leantime instances and compare workflow outcome and three-year cost.

**Requirements**

- Two sequential upgrades.
- Backup/restore and uninstall rollback.
- Same workflow fixtures as Packet 002.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/plugin-qualification/run_package_matrix.py --register reports/leantime-ai-parity/h0/plugin-qualification/input-register.json --output reports/leantime-ai-parity/h0/plugin-qualification/test-results.json
python scripts/leantime-ai-parity/h0/plugin-qualification/calculate_package_tco.py --test-results reports/leantime-ai-parity/h0/plugin-qualification/test-results.json --output reports/leantime-ai-parity/h0/plugin-qualification/disposition-matrix.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/plugin-qualification/test-results.json`
- `reports/leantime-ai-parity/h0/plugin-qualification/disposition-matrix.json`
- `docs/06-research/leantime-ai-parity/h0/plugin-qualification/package-disposition.md`

**Exit conditions**

- ACL, export, upgrade, backup, restore, and rollback results are complete.
- Disposition is buy/build/defer/reject with evidence.
### Slice 4: Teardown, audit, and proof

**Objective:** Destroy disposable instances, audit package handling and claims, and obtain PR Steward readiness.

**Requirements**

- No package bytes or credentials remain in repo or logs.

**Commands**

```bash
bash scripts/leantime-ai-parity/h0/plugin-qualification/destroy_lab.sh --volumes
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-006.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/plugin-qualification
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/input-register.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/package-manifest.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/test-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/disposition-matrix.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/plugin-qualification/qualification-protocol.md docs/06-research/leantime-ai-parity/h0/plugin-qualification/license-and-support-review.md docs/06-research/leantime-ai-parity/h0/plugin-qualification/package-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json
git diff --check
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/plugin-qualification/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-006/AUDITOR_REPORT.md`

**Exit conditions**

- Supply-chain audit is non-blocking.
- Package custody is complete.


## Required PAL chain

`apilookup -> analyze -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> secaudit -> codereview -> precommit -> challenge`

Escalation rules:

- Use `apilookup` for current license/support facts.
- Use `secaudit` for supply-chain and permission review.
- Use `consensus` only for real buy/build/defer forks.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Unauthorized package handling.
- License misclassification.
- ACL gaps.
- Upgrade and rollback fragility.
- False Community feature credit.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-006.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/plugin-qualification
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/input-register.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/package-manifest.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/test-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/disposition-matrix.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/plugin-qualification/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/plugin-qualification/qualification-protocol.md docs/06-research/leantime-ai-parity/h0/plugin-qualification/license-and-support-review.md docs/06-research/leantime-ai-parity/h0/plugin-qualification/package-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-H0-006/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-H0-006/PRECOMMIT.txt
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

- Destroy disposable instances and extracted tmp files.
- Remove package input mount.
- Revert tracked reports if evidence is invalid.

## Stop conditions

Stop immediately when:

- Operator authorization or package input is absent.
- License forbids the planned inspection.
- Package hash changes.
- Secret or proprietary content would enter git.
- ACL, export, rollback, or upgrade gate fails.
- Audit blocks.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Package hashes, licenses, test matrix, and disposition.
- Explicit list of packages not reviewed and why.
