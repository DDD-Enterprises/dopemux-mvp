---
id: TP-LTAIP-H0-002
title: Tp Ltaip H0 002
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Ltaip H0 002 (explanation) for dopemux documentation and developer workflows.
---
# Macro Packet: TP-LTAIP-H0-002

## Status

`BLOCKED_BY_DEPENDENCY` until `TP-LTAIP-H0-001` is merged and its lock artifact hash is recorded.

## Claim posture

- **OBSERVED:** Stage 08 makes Leantime Community and OpenProject Community co-primary Horizon 0 candidates.
- **OBSERVED:** Equivalent-edition, same-workflow, same-role testing is required.
- **PROPOSED:** This packet uses digest-pinned disposable containers and product-neutral fixtures.
- **UNKNOWN:** The exact OpenProject Community release and image digest at execution time.
- **CONFLICTING:** OpenProject has stronger documented integration primitives; Leantime may have a calmer target experience. Feature counts cannot adjudicate this.

## Objective

Produce reproducible, equivalent-scope evidence for the three locked workflows across Leantime Community 3.9.8 and a release-pinned OpenProject Community candidate, including completion, error, cognitive-load, accessibility, mobile, external-collaborator, administration, backup, restore, and resource evidence.

## Risk and authorization

- Risk: `HIGH`
- Task class: API-sensitive, deployment-sensitive, UX/accessibility-sensitive
- Authorization: `HORIZON_0_PROTOTYPE`
- No base selection
- No production deployment
- No paid features
- No production credentials

## Repo and worktree

- Repository: `DDD-Enterprises/dopemux-mvp`
- Base: `main`
- Branch: `prototype/TP-LTAIP-H0-002-equivalent-edition-trial`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-H0-002`

## Scope

### IN

- Release and image resolution from official sources
- Immutable candidate lock file
- Isolated disposable compose stack
- Product-neutral fixtures and role mapping
- Automated provisioning, fixture load, measurement, and teardown
- Manual workflow, keyboard, VoiceOver, mobile, onboarding, admin, backup, and restore evidence
- Comparative evidence and dissent
- Proof, audit, PR, PR Steward

### OUT

- Base adoption
- Migration
- Production deployment or data
- Paid plugins or enterprise features
- Performance tuning beyond measurement
- Product code modification
- Plane trial unless a later trigger authorizes it
- AI features

## P0 gates

A candidate receives a P0 failure when any of the following occurs:

- a must-win workflow cannot be completed using Community surfaces;
- cross-project or role isolation fails;
- a critical workflow cannot be completed by keyboard;
- a screen-reader blocker prevents critical completion;
- essential mobile capture/update/status/comment behavior fails;
- backup and restore fail to recover the synthetic fixture and role semantics;
- the candidate requires paid/enterprise functionality for the baseline;
- an independent observer cannot reproduce the result.

A weighted score cannot rescue a P0 failure.

## Authorized files

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-002.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-002.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `compose/leantime-ai-parity/h0/compose.workflow-trial.yml`
- `config/leantime-ai-parity/h0/candidate-images.lock.json`
- `config/leantime-ai-parity/h0/trial.env.example`
- `scripts/leantime-ai-parity/h0/resolve_candidate_images.py`
- `scripts/leantime-ai-parity/h0/bootstrap_candidates.sh`
- `scripts/leantime-ai-parity/h0/load_fixtures.py`
- `scripts/leantime-ai-parity/h0/run_trial.py`
- `scripts/leantime-ai-parity/h0/destroy_candidates.sh`
- `tests/fixtures/leantime-ai-parity/h0/workflow-fixture.json`
- `tests/fixtures/leantime-ai-parity/h0/role-matrix.json`
- `tests/fixtures/leantime-ai-parity/h0/workflow-scenarios.json`
- `tests/prototypes/leantime-ai-parity/h0/test_candidate_lock.py`
- `tests/prototypes/leantime-ai-parity/h0/test_fixture_equivalence.py`
- `tests/prototypes/leantime-ai-parity/h0/test_trial_manifest.py`
- `docs/06-research/leantime-ai-parity/h0/workflow-trial/trial-protocol.md`
- `docs/06-research/leantime-ai-parity/h0/workflow-trial/accessibility-mobile-checklist.md`
- `docs/06-research/leantime-ai-parity/h0/workflow-trial/admin-backup-restore-checklist.md`
- `reports/leantime-ai-parity/h0/workflow-trial/version-lock.json`
- `reports/leantime-ai-parity/h0/workflow-trial/trial-run-manifest.json`
- `reports/leantime-ai-parity/h0/workflow-trial/observations.jsonl`
- `reports/leantime-ai-parity/h0/workflow-trial/issues.json`
- `reports/leantime-ai-parity/h0/workflow-trial/candidate-results.json`
- `reports/leantime-ai-parity/h0/workflow-trial/dissent.md`
- `reports/leantime-ai-parity/h0/workflow-trial/screenshots/`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-002/MERGE_READINESS.json`

## Worktree preflight

```bash
set -euo pipefail

test -f .dopetaskroot
test -s .repo_id
test -f pyproject.toml
git remote get-url origin | grep -Eq 'DDD-Enterprises/dopemux-mvp(\.git)?$'
test "$(git branch --show-current)" = "main"
test -z "$(git status --porcelain)"

git fetch origin main
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-002" -b "prototype/TP-LTAIP-H0-002-equivalent-edition-trial" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-002"

test -f .dopetaskroot
test -s .repo_id
git remote get-url origin | grep -Eq 'DDD-Enterprises/dopemux-mvp(\.git)?$'
test "$(git branch --show-current)" = "prototype/TP-LTAIP-H0-002-equivalent-edition-trial"
test -z "$(git status --porcelain)"

git status --short
git rev-parse HEAD
git remote get-url origin
```

Additionally verify Packet 001:

```bash
test -f reports/leantime-ai-parity/h0/segment-lock/segment-workflow-lock.json
test -f reports/leantime-ai-parity/h0/segment-lock/manifest.json
python -m json.tool reports/leantime-ai-parity/h0/segment-lock/segment-workflow-lock.json >/dev/null
```

Stop if Packet 001 is absent, unmerged, superseded, or below its evidence threshold.

## Exact execution sequence

### Slice 1: Resolve and pin candidates

Use current official sources. Do not guess the OpenProject version or image.

```bash
python scripts/leantime-ai-parity/h0/resolve_candidate_images.py   --leantime-version 3.9.8   --openproject-channel community   --output config/leantime-ai-parity/h0/candidate-images.lock.json

python -m json.tool   config/leantime-ai-parity/h0/candidate-images.lock.json >/dev/null

docker compose   -f compose/leantime-ai-parity/h0/compose.workflow-trial.yml   config --quiet
```

The lock must record version, source URL, retrieval timestamp, image reference, digest, edition, and license boundary.

### Slice 2: Build fixtures and harness

```bash
python -m pytest -q   tests/prototypes/leantime-ai-parity/h0/test_candidate_lock.py   tests/prototypes/leantime-ai-parity/h0/test_fixture_equivalence.py   tests/prototypes/leantime-ai-parity/h0/test_trial_manifest.py

bash scripts/leantime-ai-parity/h0/bootstrap_candidates.sh

python scripts/leantime-ai-parity/h0/load_fixtures.py   --lock config/leantime-ai-parity/h0/candidate-images.lock.json   --fixture tests/fixtures/leantime-ai-parity/h0/workflow-fixture.json   --roles tests/fixtures/leantime-ai-parity/h0/role-matrix.json
```

Stop if record semantics or role semantics cannot be made equivalent without paid features.

### Slice 3: Run the trial

```bash
python scripts/leantime-ai-parity/h0/run_trial.py   --lock config/leantime-ai-parity/h0/candidate-images.lock.json   --scenarios tests/fixtures/leantime-ai-parity/h0/workflow-scenarios.json   --output reports/leantime-ai-parity/h0/workflow-trial

python -m json.tool   reports/leantime-ai-parity/h0/workflow-trial/candidate-results.json >/dev/null
```

Perform the manual keyboard, VoiceOver, mobile, external-collaborator, admin, backup, and restore checklists. Store only redacted screenshots and structured observations.

### Slice 4: Destroy disposable environment

```bash
bash scripts/leantime-ai-parity/h0/destroy_candidates.sh --volumes
docker ps --format '{.Names}' | grep -E 'ltaip|leantime|openproject' && exit 1 || true
```

Destruction evidence is required. Do not leave instances or volumes running.

### Slice 5: Audit and proof

Run the required validators, embedded audit, PR, and PR Steward.

## PAL chain

`apilookup -> analyze -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> challenge`

`apilookup` is mandatory because current release and image facts affect correctness.


## Embedded audit

An embedded audit is mandatory.

Route order:

1. AGY / Google Antigravity with Sonnet, when available.
2. Claude Code CLI with Sonnet.
3. Claude Code CLI with Opus when depth or security risk requires it.
4. Gemini CLI as an independent broad-context fallback.

Do not guess an unavailable CLI syntax. Before invocation, run the selected tool's local `--help`, write the exact intended invocation into `COMMAND_LOG.md`, and then execute it. The normalized proof must contain:

- `required`
- `status`: `PASS`, `PASS_WITH_RISKS`, `FAIL`, `NEEDS_SUPERVISOR`, or `SKIPPED`
- `auditor_tool`
- `auditor_model`
- exact `invocation`
- `exit_code`
- `report_path`
- structured findings
- fixes applied
- remaining risks
- `skip_reason`

`FAIL`, `NEEDS_SUPERVISOR`, conflicting findings, or a skipped required audit blocks completion.


The audit must attack:

- edition contamination;
- non-equivalent role semantics;
- fixture product bias;
- accessibility theatre;
- mobile evidence weakness;
- backup/restore incompleteness;
- hidden admin and support burden;
- premature base selection.

## Validation commands

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-002.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/test_candidate_lock.py tests/prototypes/leantime-ai-parity/h0/test_fixture_equivalence.py tests/prototypes/leantime-ai-parity/h0/test_trial_manifest.py
docker compose -f compose/leantime-ai-parity/h0/compose.workflow-trial.yml config --quiet
python -m json.tool config/leantime-ai-parity/h0/candidate-images.lock.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/workflow-trial/version-lock.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/workflow-trial/trial-run-manifest.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/workflow-trial/candidate-results.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/workflow-trial/trial-protocol.md docs/06-research/leantime-ai-parity/h0/workflow-trial/accessibility-mobile-checklist.md docs/06-research/leantime-ai-parity/h0/workflow-trial/admin-backup-restore-checklist.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json
git diff --check
```

## Proof contract


The implementer must return and commit a proof bundle containing:

- `git status` before and after
- starting and ending commit SHA
- `git diff --stat`
- full `git diff`
- every command, stdout, stderr, and exit code
- validation artifacts and logs
- assumptions and unresolved unknowns
- exact files created or modified
- rollback evidence where exercised
- embedded-audit report and normalized `embedded_audit` object
- PR URL, PR number, head SHA, checks, review items, and PR Steward output
- `MERGE_READINESS.json` current to the latest PR head

The proof status cannot be `VERIFIED` unless the final pre-commit gate, embedded audit, and evidence-ledger checks pass.


## Final capture

```bash
set -euo pipefail

git status --short | tee "proof/leantime-ai-parity/TP-LTAIP-H0-002/GIT_STATUS_AFTER.txt"
git diff --stat | tee "proof/leantime-ai-parity/TP-LTAIP-H0-002/GIT_DIFF_STAT.txt"
git diff | tee "proof/leantime-ai-parity/TP-LTAIP-H0-002/GIT_DIFF.patch"
git diff --check

python scripts/audit/validate_audit_proof.py   "proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json"

pre-commit run --all-files | tee   "proof/leantime-ai-parity/TP-LTAIP-H0-002/PRECOMMIT.txt"

git status --short
```


## PR Steward gate

After the PR is opened, PR Steward must harvest:

- PR metadata and latest head SHA
- changed files and commits
- reviews, review comments, threads, issue comments, and bot comments
- required and optional checks
- proof freshness relative to the latest head

Every review item must be classified. Unknown reviewers or bots, unresolved blocking threads, stale proof, failed checks, unclassified review items, or scope escape block `READY`.

Packets 001 and 002 may skip a second supervisor review only when the embedded audit is non-blocking, PR Steward returns `READY`, proof is current, and the diff remains inside the allowlist. Packet 003 always requires supervisor adjudication because it touches security and authority boundaries.


## Rollback

- Run `destroy_candidates.sh --volumes`.
- Remove only packet-created containers, networks, volumes, generated credentials, and temporary source material.
- Close PR and remove worktree if pre-merge.
- Revert the packet commit if merged evidence is later invalidated.
- Preserve the prior result as superseded evidence rather than rewriting history.

## Stop conditions

Stop when:

- Packet 001 is not current;
- candidate versions cannot be pinned from official sources;
- Community-edition equivalence is impossible;
- paid or enterprise capability contaminates the trial;
- production credentials or data are detected;
- disposable isolation fails;
- P0 security or privacy failure occurs;
- the same fixtures cannot be loaded;
- the manual evidence is missing or fabricated;
- the auditor blocks;
- PR Steward is not READY;
- diff escapes the allowlist.

## Final return

Return candidate locks, fixture hashes, trial results, P0/P1 issues, evidence limitations, destruction proof, git evidence, embedded audit, PR head SHA, checks, review classifications, and PR Steward readiness.

Do not select a base product.
