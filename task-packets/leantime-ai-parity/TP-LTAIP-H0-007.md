# Macro Packet: TP-LTAIP-H0-007

## Status

`BLOCKED_BY_DEPENDENCIES`

## Claim posture

- **OBSERVED:** Prior TCO assumptions were insufficient for architecture selection.
- **PROPOSED:** A deterministic seeded simulation can expose uncertainty and downside.
- **UNKNOWN:** Future quotes, staffing, and upstream acceptance.
- **CONFLICTING:** Lowest expected cost may have the worst downside or staffing risk.

## Objective

Produce equivalent-scope expected and downside TCO distributions plus a named-skill, ownership, on-call, and bus-factor operating model using actual prototype evidence and explicit uncertainty.

## Why this packet exists now

Prior point ranges and weighted winners could not select a base. Cost is useful only after hard gates and with failure branches.

## Risk and authorization

- Risk: `HIGH`
- Task class: `economic and operating-model analysis`
- Authorization: `HORIZON_0_ANALYSIS`
- Series: `LTAIP-H0-VALIDATION-001`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Supervisor review: conditional

## Repository binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Repository snapshot used while authoring: `d844d71d9ec9b55905dbb545662fc5c0f989e87c`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `analysis/TP-LTAIP-H0-007-tco-team-model`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-H0-007`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-002`
- `TP-LTAIP-H0-003`
- `TP-LTAIP-H0-004`
- `TP-LTAIP-H0-006`

## Scope IN

- Actual prototype hours, defects, support events, infrastructure, package quotes, migration, upgrade, security, and failure branches.
- Expected, P50, P80, and P95 outcomes.
- Named role coverage, ownership, on-call, and bus factor.

## Scope OUT

- Procurement.
- Calendar commitment.
- Unfunded staffing assumptions.
- Using cost to rescue P0 product or security failure.

## Invariants

- Equivalent scope across candidates.
- Every estimate has evidence and assumption.
- Hard gates run before cost ranking.
- Random simulation is seeded and reproducible.
- Missing role coverage blocks implementation.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-007.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-007.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/MERGE_READINESS.json`
- `config/leantime-ai-parity/h0/tco-model.json`
- `scripts/leantime-ai-parity/h0/tco/collect_prototype_evidence.py`
- `scripts/leantime-ai-parity/h0/tco/run_simulation.py`
- `scripts/leantime-ai-parity/h0/tco/run_sensitivity.py`
- `scripts/leantime-ai-parity/h0/tco/validate_role_coverage.py`
- `tests/prototypes/leantime-ai-parity/h0/tco/test_model_determinism.py`
- `tests/prototypes/leantime-ai-parity/h0/tco/test_distribution_bounds.py`
- `tests/prototypes/leantime-ai-parity/h0/tco/test_failure_branches.py`
- `docs/06-research/leantime-ai-parity/h0/tco/model-method.md`
- `docs/06-research/leantime-ai-parity/h0/tco/team-operating-model.md`
- `docs/06-research/leantime-ai-parity/h0/tco/tco-disposition.md`
- `config/leantime-ai-parity/h0/tco-model.json`
- `reports/leantime-ai-parity/h0/tco/evidence-inputs.json`
- `reports/leantime-ai-parity/h0/tco/simulation-results.json`
- `reports/leantime-ai-parity/h0/tco/sensitivity.json`
- `reports/leantime-ai-parity/h0/tco/capacity-gaps.json`
- `reports/leantime-ai-parity/h0/tco/manifest.json`
- `reports/leantime-ai-parity/h0/tco/scenario-summary.csv`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-007" -b "analysis/TP-LTAIP-H0-007-tco-team-model" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-007"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "analysis/TP-LTAIP-H0-007-tco-team-model"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-H0-007/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Collect evidence and define distributions

**Objective:** Collect prototype evidence and define source-linked distributions, correlations, and failure branches.

**Requirements**

- Actual observed hours are separated from estimates.
- Quotes have date and scope.
- Unknowns have distributions or remain unscored.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/tco/collect_prototype_evidence.py --output reports/leantime-ai-parity/h0/tco/evidence-inputs.json
python -m json.tool config/leantime-ai-parity/h0/tco-model.json >/dev/null
```

**Expected artifacts**

- `config/leantime-ai-parity/h0/tco-model.json`
- `reports/leantime-ai-parity/h0/tco/evidence-inputs.json`
- `docs/06-research/leantime-ai-parity/h0/tco/model-method.md`

**Exit conditions**

- Every parameter has source, date, unit, range, and confidence.
### Slice 2: Run expected and downside simulation

**Objective:** Run seeded simulations for surviving candidate/package variants and explicit failure branches.

**Requirements**

- At least 10,000 seeded draws.
- P50/P80/P95 and tail drivers reported.
- No failed hard-gate scenario receives a rank.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/tco/run_simulation.py --config config/leantime-ai-parity/h0/tco-model.json --seed 20260722 --draws 10000 --output reports/leantime-ai-parity/h0/tco/simulation-results.json
python scripts/leantime-ai-parity/h0/tco/run_sensitivity.py --results reports/leantime-ai-parity/h0/tco/simulation-results.json --output reports/leantime-ai-parity/h0/tco/sensitivity.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/tco/simulation-results.json`
- `reports/leantime-ai-parity/h0/tco/sensitivity.json`
- `reports/leantime-ai-parity/h0/tco/scenario-summary.csv`

**Exit conditions**

- Repeated runs with same seed are byte-stable.
- Failure branches and downside are visible.
### Slice 3: Validate team operating model

**Objective:** Map required skills, named ownership, on-call, support load, bus factor, and unresolved capacity gaps.

**Requirements**

- Security/SRE and accessibility ownership explicit.
- No role is filled by “AI”.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/tco/validate_role_coverage.py --config config/leantime-ai-parity/h0/tco-model.json --output reports/leantime-ai-parity/h0/tco/capacity-gaps.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/tco/capacity-gaps.json`
- `docs/06-research/leantime-ai-parity/h0/tco/team-operating-model.md`
- `docs/06-research/leantime-ai-parity/h0/tco/tco-disposition.md`

**Exit conditions**

- Named ownership exists or implementation is BLOCKED_CAPACITY.
### Slice 4: Independent model challenge and proof

**Objective:** Run independent economic/model challenge, finalize proof, and obtain PR Steward readiness.

**Requirements**

- Auditor can reproduce key percentiles and challenge assumptions.

**Commands**

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-007.json")), json.load(open("dopetask-cannonical-spec.json")))' 
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/tco
python -m json.tool config/leantime-ai-parity/h0/tco-model.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/evidence-inputs.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/simulation-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/sensitivity.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/capacity-gaps.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/tco/model-method.md docs/06-research/leantime-ai-parity/h0/tco/team-operating-model.md docs/06-research/leantime-ai-parity/h0/tco/tco-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-007/PROOF.json
git diff --check
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/tco/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-007/AUDITOR_REPORT.md`

**Exit conditions**

- Model audit is non-blocking.
- Uncertainty remains visible.


## Required PAL chain

`analyze -> thinkdeep -> challenge -> planner -> consensus -> challenge -> implement -> testgen -> codereview -> precommit -> challenge`

Escalation rules:

- Use `consensus` to compare genuinely different cost models.
- Use `challenge` on every optimistic assumption.
- Use `debug` if simulation determinism fails.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Scope mismatch.
- Double counting or omitted failure branches.
- Fake precision.
- Unfunded staffing.
- Cost overriding hard gates.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-007.json")), json.load(open("dopetask-cannonical-spec.json")))' 
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/tco
python -m json.tool config/leantime-ai-parity/h0/tco-model.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/evidence-inputs.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/simulation-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/sensitivity.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/capacity-gaps.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/tco/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/tco/model-method.md docs/06-research/leantime-ai-parity/h0/tco/team-operating-model.md docs/06-research/leantime-ai-parity/h0/tco/tco-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-007/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-H0-007/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-H0-007/PRECOMMIT.txt
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

A second supervisor review may be skipped only when embedded audit and PR Steward are both current and non-blocking.

## Rollback

- Supersede the model when assumptions change.
- Preserve prior results and evidence hashes.
- Revert commit if calculations are invalid.

## Stop conditions

Stop immediately when:

- Required prototype evidence is missing.
- Scopes are not equivalent.
- A parameter lacks evidence or an explicit UNKNOWN.
- Simulation is nondeterministic.
- Role coverage is fictional.
- Cost ranking attempts to rescue a hard-gate failure.
- Audit blocks.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Expected/P80/P95 TCO and top downside drivers.
- Named role coverage and capacity blockers.
