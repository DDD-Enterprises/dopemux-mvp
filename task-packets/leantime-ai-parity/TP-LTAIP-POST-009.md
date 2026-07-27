# Macro Packet: TP-LTAIP-POST-009

## Status

`CONDITIONAL_NOT_AUTHORIZED_UNTIL_BASE_SELECTION`

## Claim posture

- **OBSERVED:** This packet is unauthorized before Packet 008 selects a base.
- **PROPOSED:** A narrow read gateway can isolate product APIs from Dopemux consumers.
- **UNKNOWN:** Which adapter is selected.
- **CONFLICTING:** Both adapter files are allowlisted for authoring, but exactly one may be active.

## Objective

Implement one release-pinned, deny-by-default, read-only gateway for the selected base with project/identity allowlists, response filtering, audit receipts, rate limits, token rotation, and kill switch.

## Why this packet exists now

Only a selected and security-qualified base can support a durable integration boundary.

## Risk and authorization

- Risk: `HIGH`
- Task class: `security-sensitive read integration`
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
- Branch: `feat/TP-LTAIP-POST-009-read-gateway`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-POST-009`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-008`

## Scope IN

- Typed documented reads for the selected base.
- Project and identity allowlists.
- Response-field filtering, audit receipts, rate limits, token rotation, and kill switch.

## Scope OUT

- Writes of any kind.
- MCP tools.
- Direct database access.
- Dynamic arbitrary method dispatch.
- Running both adapters.

## Invariants

- Packet 008 selected one base and version.
- Exactly one adapter is active.
- Deny-by-default and least privilege.
- Zero cross-project leakage.
- Canonical candidate remains source truth.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-POST-009.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-POST-009.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/MERGE_READINESS.json`
- `services/ltaip-policy-gateway/pyproject.toml`
- `services/ltaip-policy-gateway/Dockerfile`
- `services/ltaip-policy-gateway/src/ltaip_gateway/__init__.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/app.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/policy.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/audit.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/kill_switch.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/adapters/base.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/adapters/leantime.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/adapters/openproject.py`
- `services/ltaip-policy-gateway/tests/test_contract.py`
- `services/ltaip-policy-gateway/tests/test_authorization.py`
- `services/ltaip-policy-gateway/tests/test_rate_limit.py`
- `services/ltaip-policy-gateway/tests/test_kill_switch.py`
- `compose/leantime-ai-parity/h1/compose.read-gateway.yml`
- `docs/03-reference/leantime-ai-parity/read-only-gateway-contract.md`
- `docs/92-runbooks/leantime-ai-parity/read-only-gateway.md`
- `config/leantime-ai-parity/h1/selected-base.json`
- `config/leantime-ai-parity/h1/read-policy.json`
- `contracts/leantime-ai-parity/read-gateway.schema.json`
- `reports/leantime-ai-parity/h1/read-gateway/contract-results.json`
- `reports/leantime-ai-parity/h1/read-gateway/manifest.json`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-POST-009" -b "feat/TP-LTAIP-POST-009-read-gateway" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-POST-009"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "feat/TP-LTAIP-POST-009-read-gateway"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-POST-009/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Bind selected base and API contract

**Objective:** Load Packet 008 decision and Packet 003 manifest, generate one selected-base contract, and fail if ambiguous.

**Requirements**

- Exact version and API surface.
- No fallback to unclassified methods.

**Commands**

```bash
python -m json.tool config/leantime-ai-parity/h1/selected-base.json >/dev/null
python -m json.tool contracts/leantime-ai-parity/read-gateway.schema.json >/dev/null
```

**Expected artifacts**

- `config/leantime-ai-parity/h1/selected-base.json`
- `config/leantime-ai-parity/h1/read-policy.json`
- `contracts/leantime-ai-parity/read-gateway.schema.json`
- `docs/03-reference/leantime-ai-parity/read-only-gateway-contract.md`

**Exit conditions**

- Exactly one base and adapter.
- Every read is classified.
### Slice 2: Implement typed read gateway

**Objective:** Implement selected adapter, policy, audit receipts, redaction, rate limits, and explicit denied states.

**Requirements**

- Unselected adapter is absent or disabled.
- No generic method string.
- No token in logs.

**Commands**

```bash
python -m pytest -q services/ltaip-policy-gateway/tests
docker compose -f compose/leantime-ai-parity/h1/compose.read-gateway.yml up -d --build
```

**Expected artifacts**

- `services/ltaip-policy-gateway/src/ltaip_gateway/app.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/policy.py`
- `services/ltaip-policy-gateway/src/ltaip_gateway/adapters/base.py`

**Exit conditions**

- Contract and authorization tests pass.
- Denied/unavailable states explicit.
### Slice 3: Run negative, rate-limit, failure, and upgrade-drift tests

**Objective:** Prove cross-project denial, response filtering, timeout behavior, token rotation, and kill switch on selected version and upgrade candidate.

**Requirements**

- Zero cross-project leak.
- Kill switch blocks all adapter calls.

**Commands**

```bash
python -m pytest -q services/ltaip-policy-gateway/tests
python -m json.tool reports/leantime-ai-parity/h1/read-gateway/contract-results.json >/dev/null
```

**Expected artifacts**

- `reports/leantime-ai-parity/h1/read-gateway/contract-results.json`
- `docs/92-runbooks/leantime-ai-parity/read-only-gateway.md`

**Exit conditions**

- Negative and drift tests pass.
### Slice 4: Security audit, proof, and PR

**Objective:** Run independent security audit and supervisor adjudication.

**Requirements**

- Supervisor review mandatory.

**Commands**

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-009.json")), json.load(open("dopetask-cannonical-spec.json")))' 
docker compose -f compose/leantime-ai-parity/h1/compose.read-gateway.yml config --quiet
python -m pytest -q services/ltaip-policy-gateway/tests
python -m json.tool config/leantime-ai-parity/h1/selected-base.json >/dev/null
python -m json.tool config/leantime-ai-parity/h1/read-policy.json >/dev/null
python -m json.tool contracts/leantime-ai-parity/read-gateway.schema.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/read-gateway/contract-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/read-gateway/manifest.json >/dev/null
python scripts/docs_validator.py docs/03-reference/leantime-ai-parity/read-only-gateway-contract.md docs/92-runbooks/leantime-ai-parity/read-only-gateway.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-009/PROOF.json
git diff --check
```

**Expected artifacts**

- `reports/leantime-ai-parity/h1/read-gateway/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-009/AUDITOR_REPORT.md`

**Exit conditions**

- No P0/P1 security finding.
- Supervisor approves.


## Required PAL chain

`apilookup -> analyze -> tracer -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> secaudit -> codereview -> precommit -> challenge`

Escalation rules:

- Use `apilookup` for selected API version.
- Use `tracer` for authorization and response filtering.
- Use `secaudit` before any external test.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Dual-base ambiguity.
- Read endpoint scope escape.
- Response-field leakage.
- Token and log secrets.
- Kill-switch bypass.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-009.json")), json.load(open("dopetask-cannonical-spec.json")))' 
docker compose -f compose/leantime-ai-parity/h1/compose.read-gateway.yml config --quiet
python -m pytest -q services/ltaip-policy-gateway/tests
python -m json.tool config/leantime-ai-parity/h1/selected-base.json >/dev/null
python -m json.tool config/leantime-ai-parity/h1/read-policy.json >/dev/null
python -m json.tool contracts/leantime-ai-parity/read-gateway.schema.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/read-gateway/contract-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/read-gateway/manifest.json >/dev/null
python scripts/docs_validator.py docs/03-reference/leantime-ai-parity/read-only-gateway-contract.md docs/92-runbooks/leantime-ai-parity/read-only-gateway.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-009/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-POST-009/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-POST-009/PRECOMMIT.txt
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

- Disable gateway feature flag and kill switch.
- Remove selected tokens.
- Destroy containers.
- Revert commit.

## Stop conditions

Stop immediately when:

- Packet 008 does not select exactly one base.
- Exposure manifest is stale.
- Any write or MCP surface appears.
- Both adapters are active.
- Cross-project leak or response-field leak occurs.
- Audit or supervisor blocks.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Selected base/version and read-contract inventory.
- Negative-test and kill-switch evidence.
