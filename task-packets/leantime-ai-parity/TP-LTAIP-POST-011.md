---
id: TP-LTAIP-POST-011
title: Tp Ltaip Post 011
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Ltaip Post 011 (explanation) for dopemux documentation and developer workflows.
---
# Macro Packet: TP-LTAIP-POST-011

## Status

`CONDITIONAL_NOT_AUTHORIZED_UNTIL_ALL_GATES`

## Claim posture

- **OBSERVED:** Stage 03 permits bounded assist roles; Stage 07 rejects broad authority.
- **PROPOSED:** Two task-specific read/draft features can test value safely.
- **UNKNOWN:** Which features meet evaluation and cost gates.
- **CONFLICTING:** Provider capability and privacy/cost constraints may select different routes.

## Objective

Implement exactly two selected read/draft AI features with cited outputs, human approval, deterministic fallback, data-class routing, redaction, budget ceilings, task-specific evaluation, and instant disablement.

## Why this packet exists now

AI is legitimate only after deterministic workflows, read authorization, and synthetic retrieval controls are proven.

## Risk and authorization

- Risk: `CRITICAL`
- Task class: `AI, privacy, and security-sensitive pilot`
- Authorization: `CONDITIONAL_AFTER_DETERMINISTIC_AND_RETRIEVAL_GATES`
- Series: `LTAIP-POST-SELECTION-001`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Supervisor review: mandatory

## Repository binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Repository snapshot used while authoring: `d844d71d9ec9b55905dbb545662fc5c0f989e87c`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `feat/TP-LTAIP-POST-011-bounded-ai-pilot`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-POST-011`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-POST-009`
- `TP-LTAIP-POST-010`
- `TP-LTAIP-H0-005`

## Scope IN

- Exactly two selected read/draft features.
- External model gateway, policy, citations, budget, evaluation, human review, and kill switch.
- Golden, adversarial, privacy, failure, and cost tests.

## Scope OUT

- Any canonical write.
- Autonomous agent action.
- Permission administration.
- MCP writes.
- Recurring scheduler.
- Uncited material claims.

## Invariants

- Read-only gateway is the sole product data path.
- Every material output is cited or explicitly uncertain.
- Human approves drafts before use.
- Data-class route policy and redaction enforced.
- Deterministic fallback exists.
- Kill switch destroys or disables derived data.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-POST-011.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-POST-011.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/MERGE_READINESS.json`
- `services/ltaip-ai-pilot/pyproject.toml`
- `services/ltaip-ai-pilot/Dockerfile`
- `services/ltaip-ai-pilot/src/ltaip_ai/__init__.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/app.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/gateway.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/policy.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/citations.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/budget.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/features/`
- `services/ltaip-ai-pilot/tests/`
- `compose/leantime-ai-parity/h2/compose.ai-pilot.yml`
- `docs/03-reference/leantime-ai-parity/ai-pilot-contract.md`
- `docs/06-research/leantime-ai-parity/h2/ai-pilot/evaluation-plan.md`
- `docs/92-runbooks/leantime-ai-parity/ai-pilot-kill-switch.md`
- `config/leantime-ai-parity/h2/ai-pilot.json`
- `contracts/leantime-ai-parity/ai-draft.schema.json`
- `reports/leantime-ai-parity/h2/ai-pilot/golden-results.json`
- `reports/leantime-ai-parity/h2/ai-pilot/adversarial-results.json`
- `reports/leantime-ai-parity/h2/ai-pilot/cost-usage.json`
- `reports/leantime-ai-parity/h2/ai-pilot/manifest.json`
- `tests/fixtures/leantime-ai-parity/h2/ai-pilot/golden-set.jsonl`
- `tests/fixtures/leantime-ai-parity/h2/ai-pilot/adversarial-set.jsonl`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-POST-011" -b "feat/TP-LTAIP-POST-011-bounded-ai-pilot" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-POST-011"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "feat/TP-LTAIP-POST-011-bounded-ai-pilot"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-POST-009/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-009/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-POST-010/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-010/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-POST-011/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Select two features and freeze evaluation contract

**Objective:** Select exactly two read/draft features from accepted evidence and pre-register golden/adversarial thresholds.

**Requirements**

- No feature selected for novelty alone.
- Each has deterministic baseline and human review.

**Commands**

```bash
python -m json.tool config/leantime-ai-parity/h2/ai-pilot.json >/dev/null
python -m json.tool contracts/leantime-ai-parity/ai-draft.schema.json >/dev/null
```

**Expected artifacts**

- `config/leantime-ai-parity/h2/ai-pilot.json`
- `contracts/leantime-ai-parity/ai-draft.schema.json`
- `docs/03-reference/leantime-ai-parity/ai-pilot-contract.md`
- `docs/06-research/leantime-ai-parity/h2/ai-pilot/evaluation-plan.md`

**Exit conditions**

- Exactly two features.
- Thresholds, costs, privacy classes, and rollback are pre-registered.
### Slice 2: Implement read/draft gateway and citations

**Objective:** Implement external model gateway, policy, citations, budgets, feature flags, and human-review surfaces.

**Requirements**

- No write credentials.
- No arbitrary tools.
- All context comes through Packet 009 gateway.

**Commands**

```bash
python -m pytest -q services/ltaip-ai-pilot/tests
docker compose -f compose/leantime-ai-parity/h2/compose.ai-pilot.yml up -d --build
```

**Expected artifacts**

- `services/ltaip-ai-pilot/src/ltaip_ai/app.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/gateway.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/policy.py`
- `services/ltaip-ai-pilot/src/ltaip_ai/citations.py`

**Exit conditions**

- Writes are structurally impossible.
- Citations and uncertainty are schema-required.
### Slice 3: Run golden, adversarial, privacy, failure, and cost evaluation

**Objective:** Run task-specific evaluation with overrides, denial, injection, provider failure, and budget tests.

**Requirements**

- Zero authorization failure.
- Material claims cited.
- Costs below pre-registered budget.

**Commands**

```bash
python -m pytest -q services/ltaip-ai-pilot/tests
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/golden-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/adversarial-results.json >/dev/null
```

**Expected artifacts**

- `reports/leantime-ai-parity/h2/ai-pilot/golden-results.json`
- `reports/leantime-ai-parity/h2/ai-pilot/adversarial-results.json`
- `reports/leantime-ai-parity/h2/ai-pilot/cost-usage.json`

**Exit conditions**

- Task thresholds pass.
- Zero authorization failures.
- Provider failure falls back deterministically.
### Slice 4: Security audit, kill-switch drill, proof, and PR

**Objective:** Exercise kill switch and data destruction, run independent security audit, and request supervisor adjudication.

**Requirements**

- No derived data survives disablement beyond declared retention.

**Commands**

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-011.json")), json.load(open("dopetask-cannonical-spec.json")))'
docker compose -f compose/leantime-ai-parity/h2/compose.ai-pilot.yml config --quiet
python -m pytest -q services/ltaip-ai-pilot/tests
python -m json.tool config/leantime-ai-parity/h2/ai-pilot.json >/dev/null
python -m json.tool contracts/leantime-ai-parity/ai-draft.schema.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/golden-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/adversarial-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/cost-usage.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/manifest.json >/dev/null
python scripts/docs_validator.py docs/03-reference/leantime-ai-parity/ai-pilot-contract.md docs/06-research/leantime-ai-parity/h2/ai-pilot/evaluation-plan.md docs/92-runbooks/leantime-ai-parity/ai-pilot-kill-switch.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-011/PROOF.json
git diff --check
```

**Expected artifacts**

- `docs/92-runbooks/leantime-ai-parity/ai-pilot-kill-switch.md`
- `reports/leantime-ai-parity/h2/ai-pilot/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-011/AUDITOR_REPORT.md`

**Exit conditions**

- Kill switch and deletion pass.
- No P0/P1 audit finding.
- Supervisor approves.


## Required PAL chain

`apilookup -> analyze -> tracer -> thinkdeep -> challenge -> planner -> consensus -> challenge -> implement -> testgen -> secaudit -> codereview -> precommit -> challenge`

Escalation rules:

- Use `apilookup` for provider API behavior.
- Use `consensus` for provider/route choice after policy filters.
- Use `secaudit` for injection, privacy, and authorization.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Hidden write path.
- Uncited claims.
- Retrieved instruction execution.
- Privacy route mismatch.
- Budget bypass.
- Weak kill switch.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-011.json")), json.load(open("dopetask-cannonical-spec.json")))'
docker compose -f compose/leantime-ai-parity/h2/compose.ai-pilot.yml config --quiet
python -m pytest -q services/ltaip-ai-pilot/tests
python -m json.tool config/leantime-ai-parity/h2/ai-pilot.json >/dev/null
python -m json.tool contracts/leantime-ai-parity/ai-draft.schema.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/golden-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/adversarial-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/cost-usage.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h2/ai-pilot/manifest.json >/dev/null
python scripts/docs_validator.py docs/03-reference/leantime-ai-parity/ai-pilot-contract.md docs/06-research/leantime-ai-parity/h2/ai-pilot/evaluation-plan.md docs/92-runbooks/leantime-ai-parity/ai-pilot-kill-switch.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-011/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-POST-011/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-POST-011/PRECOMMIT.txt
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

- Disable both feature flags.
- Revoke provider credentials.
- Destroy derived data and containers.
- Revert commit.

## Stop conditions

Stop immediately when:

- Any dependency gate is stale.
- More or fewer than two features.
- A write path exists.
- Authorization or citation failure occurs.
- Retrieved text influences tool or policy behavior.
- Budget ceiling can be bypassed.
- Kill switch fails.
- Audit or supervisor blocks.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Feature-specific evaluation, citation, privacy, and cost results.
- Human override and kill-switch evidence.
