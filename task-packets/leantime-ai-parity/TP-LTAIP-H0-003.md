---
id: TP-LTAIP-H0-003
title: Tp Ltaip H0 003
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Ltaip H0 003 (explanation) for dopemux documentation and developer workflows.
---
# Macro Packet: TP-LTAIP-H0-003

## Status

`BLOCKED_BY_DEPENDENCY` until `TP-LTAIP-H0-002` is merged and candidate version locks are current.

## Claim posture

- **OBSERVED:** Stage 07 requires complete exposure classification and blocking authorization evidence.
- **OBSERVED:** Leantime permission enforcement has an audit-only default in the reviewed source path.
- **OBSERVED:** MCP exposes write-capable operations but remains beta/plugin territory.
- **PROPOSED:** This packet generates fresh-install and upgrade manifests plus adversarial negative tests.
- **UNKNOWN:** Whether either candidate achieves complete blocking coverage without unacceptable modification.
- **CONFLICTING:** Technical surface presence does not equal safe, supported, Community-accessible operation.

## Objective

Generate release-pinned, content-addressed API/plugin/MCP exposure manifests and prove effective blocking authorization, project isolation, object-level checks, response-field filtering, upgrade drift behavior, and kill-switch operation for both disposable candidates.

## Risk and authority

- Risk: `CRITICAL`
- Task class: security-sensitive, authority-sensitive, API-sensitive
- Authorization: `HORIZON_0_PROTOTYPE`
- Production authority: none
- MCP writes: disabled
- Merge: supervisor adjudication required

## Scope

### IN

- Release-pinned static and runtime surface discovery
- Read/write and scope classification
- Effective enforcement-mode verification
- Cross-project, object, field, token, upgrade, and kill-switch tests
- Synthetic writes inside disposable candidates only
- Security disposition, proof, audit, PR Steward, supervisor handoff

### OUT

- Production writes
- Production credentials or data
- Enabling MCP writes
- Core permission redesign
- Broad dynamic dispatch
- Direct database access
- Candidate adoption
- Weighted security scoring

## Non-negotiable gates

- 100 percent discovered write-surface classification
- zero unclassified surface accepted
- zero P0/P1 authorization bypasses
- blocking enforcement on fresh install and upgraded state
- final-object authorization
- response-field filtering
- working kill switch
- independent security audit
- supervisor adjudication

## Authorized files

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-003.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-003.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `config/leantime-ai-parity/h0/exposure-policy.yaml`
- `scripts/leantime-ai-parity/h0/exposure/materialize_candidate_sources.py`
- `scripts/leantime-ai-parity/h0/exposure/generate_exposure_manifest.py`
- `scripts/leantime-ai-parity/h0/exposure/probe_authorization.py`
- `scripts/leantime-ai-parity/h0/exposure/diff_exposure_manifests.py`
- `scripts/leantime-ai-parity/h0/exposure/run_security_matrix.sh`
- `tests/prototypes/leantime-ai-parity/h0/exposure/test_manifest_coverage.py`
- `tests/prototypes/leantime-ai-parity/h0/exposure/test_cross_project_denials.py`
- `tests/prototypes/leantime-ai-parity/h0/exposure/test_response_field_filtering.py`
- `tests/prototypes/leantime-ai-parity/h0/exposure/test_upgrade_drift.py`
- `tests/prototypes/leantime-ai-parity/h0/exposure/test_kill_switch.py`
- `docs/06-research/leantime-ai-parity/h0/exposure-authorization/exposure-authorization-protocol.md`
- `docs/06-research/leantime-ai-parity/h0/exposure-authorization/threat-model.md`
- `reports/leantime-ai-parity/h0/exposure-authorization/leantime-community-exposure.fresh.json`
- `reports/leantime-ai-parity/h0/exposure-authorization/leantime-community-exposure.upgraded.json`
- `reports/leantime-ai-parity/h0/exposure-authorization/openproject-community-exposure.fresh.json`
- `reports/leantime-ai-parity/h0/exposure-authorization/openproject-community-exposure.upgraded.json`
- `reports/leantime-ai-parity/h0/exposure-authorization/authorization-matrix.csv`
- `reports/leantime-ai-parity/h0/exposure-authorization/negative-test-results.json`
- `reports/leantime-ai-parity/h0/exposure-authorization/manifest-diff.json`
- `reports/leantime-ai-parity/h0/exposure-authorization/security-disposition.md`
- `reports/leantime-ai-parity/h0/exposure-authorization/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-003/MERGE_READINESS.json`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-003" -b "security/TP-LTAIP-H0-003-exposure-authorization-manifests" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-003"

test -f .dopetaskroot
test -s .repo_id
git remote get-url origin | grep -Eq 'DDD-Enterprises/dopemux-mvp(\.git)?$'
test "$(git branch --show-current)" = "security/TP-LTAIP-H0-003-exposure-authorization-manifests"
test -z "$(git status --porcelain)"

git status --short
git rev-parse HEAD
git remote get-url origin
```

Dependency checks:

```bash
test -f config/leantime-ai-parity/h0/candidate-images.lock.json
test -f reports/leantime-ai-parity/h0/workflow-trial/version-lock.json
test -f reports/leantime-ai-parity/h0/workflow-trial/candidate-results.json
python -m json.tool config/leantime-ai-parity/h0/candidate-images.lock.json >/dev/null
```

Stop if Packet 002 evidence is stale or candidates cannot be reproduced.

## Execution plan

### Slice 1: Policy and source custody

```bash
python scripts/leantime-ai-parity/h0/exposure/materialize_candidate_sources.py   --lock config/leantime-ai-parity/h0/candidate-images.lock.json   --output tmp/ltaip-h0-003

python -m pytest -q   tests/prototypes/leantime-ai-parity/h0/exposure/test_manifest_coverage.py
```

The source workspace is temporary and must not be committed.

### Slice 2: Fresh and upgraded manifests

```bash
python scripts/leantime-ai-parity/h0/exposure/generate_exposure_manifest.py   --candidate leantime   --state fresh   --lock config/leantime-ai-parity/h0/candidate-images.lock.json   --source tmp/ltaip-h0-003/leantime   --output reports/leantime-ai-parity/h0/exposure-authorization/leantime-community-exposure.fresh.json

python scripts/leantime-ai-parity/h0/exposure/generate_exposure_manifest.py   --candidate openproject   --state fresh   --lock config/leantime-ai-parity/h0/candidate-images.lock.json   --source tmp/ltaip-h0-003/openproject   --output reports/leantime-ai-parity/h0/exposure-authorization/openproject-community-exposure.fresh.json

bash scripts/leantime-ai-parity/h0/exposure/run_security_matrix.sh   --phase upgrade-manifest
```

Every manifest entry must record:

- method or route;
- source file and source ref;
- runtime image digest;
- read/write class;
- object and project scope;
- authentication and token scope;
- response-field exposure;
- plugin/edition requirement;
- effective enforcement mode;
- classification status.

### Slice 3: Adversarial authorization

```bash
bash scripts/leantime-ai-parity/h0/exposure/run_security_matrix.sh   --phase authorization

python -m pytest -q tests/prototypes/leantime-ai-parity/h0/exposure
```

Synthetic test identities must include:

- same-project authorized;
- same-project underprivileged;
- cross-project;
- revoked;
- malformed or scope-missing token;
- upgrade-restored identity;
- response-field probe.

Any P0/P1 bypass blocks the packet.

### Slice 4: Security disposition and proof

Write an explicit per-candidate disposition:

- `PASS_TO_NEXT_H0_GATE`
- `FAIL_AUTHORIZATION_GATE`
- `BLOCKED_INCOMPLETE_EXPOSURE`
- `NEEDS_SUPERVISOR`

No aggregate score.

## PAL chain

`apilookup -> analyze -> tracer -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> secaudit -> codereview -> precommit -> challenge`

`tracer` is mandatory because authorization depends on call and dispatch paths. `secaudit` is mandatory.


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


For this packet, use Opus or an equivalently deep independent route when the default Sonnet audit cannot establish authorization coverage. Same-session self-audit is forbidden.

## Validation

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-003.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/exposure
python -m json.tool reports/leantime-ai-parity/h0/exposure-authorization/leantime-community-exposure.fresh.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/exposure-authorization/leantime-community-exposure.upgraded.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/exposure-authorization/openproject-community-exposure.fresh.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/exposure-authorization/openproject-community-exposure.upgraded.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/exposure-authorization/negative-test-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/exposure-authorization/manifest-diff.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/exposure-authorization/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/exposure-authorization/exposure-authorization-protocol.md docs/06-research/leantime-ai-parity/h0/exposure-authorization/threat-model.md reports/leantime-ai-parity/h0/exposure-authorization/security-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json
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


The proof must additionally include:

- source refs and image digests;
- manifest hashes;
- coverage counts;
- effective enforcement-mode evidence;
- complete negative-test matrix;
- P0/P1 finding disposition;
- kill-switch evidence;
- fresh versus upgraded drift;
- security auditor identity and independence;
- supervisor handoff status.

## Final capture

```bash
set -euo pipefail

git status --short | tee "proof/leantime-ai-parity/TP-LTAIP-H0-003/GIT_STATUS_AFTER.txt"
git diff --stat | tee "proof/leantime-ai-parity/TP-LTAIP-H0-003/GIT_DIFF_STAT.txt"
git diff | tee "proof/leantime-ai-parity/TP-LTAIP-H0-003/GIT_DIFF.patch"
git diff --check

python scripts/audit/validate_audit_proof.py   "proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json"

pre-commit run --all-files | tee   "proof/leantime-ai-parity/TP-LTAIP-H0-003/PRECOMMIT.txt"

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


PR Steward `READY` does not authorize merge. This packet must return to GPT-5.6 supervisor adjudication because it touches security and authority boundaries.

## Rollback

- Destroy disposable instances, volumes, networks, and synthetic credentials.
- Delete `tmp/ltaip-h0-003`.
- Disable all prototype adapters and MCP write surfaces.
- Close PR and remove worktree if pre-merge.
- Revert merged packet if evidence is invalidated.
- Preserve prior proof as superseded evidence.

## Stop conditions

Stop when:

- repo/worktree identity fails;
- dependency evidence is stale;
- source version or image digest is unresolved;
- a surface cannot be classified;
- effective authorization is audit-only or unknown;
- any P0/P1 bypass appears;
- response-field leakage appears;
- MCP writes become enabled;
- production data or credentials appear;
- source or logs contain secrets;
- audit independence fails;
- auditor returns FAIL or NEEDS_SUPERVISOR;
- PR Steward blocks;
- diff escapes the allowlist.

## Required final return

Return:

1. candidate/version/source custody;
2. discovered surface counts;
3. classified write coverage;
4. effective blocking-mode evidence;
5. negative-test matrix and exit codes;
6. P0/P1 findings;
7. fresh/upgrade drift;
8. kill-switch evidence;
9. git status and diffs;
10. embedded security audit;
11. proof hash;
12. PR URL and head SHA;
13. PR Steward output;
14. explicit supervisor escalation request.
