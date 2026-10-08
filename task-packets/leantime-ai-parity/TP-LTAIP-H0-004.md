---
id: TP-LTAIP-H0-004
title: Tp Ltaip H0 004
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Ltaip H0 004 (explanation) for dopemux documentation and developer workflows.
---
# Macro Packet: TP-LTAIP-H0-004

## Status

`BLOCKED_BY_DEPENDENCY`

## Claim posture

- **OBSERVED:** Stage 07 rejected the assumed atomic outbox invariant.
- **PROPOSED:** A thin disposable probe plugin and explicit patch variant can test the boundary.
- **UNKNOWN:** Whether a supported plugin hook participates in the canonical transaction.
- **CONFLICTING:** Synchronous hooks exist, but durable atomic delivery is unproven.

## Objective

Prove or disprove atomic event capture for representative Leantime mutations, document honest fallback semantics, and measure the maintenance tax of any core-patch alternative.

## Why this packet exists now

The Stage 05 hybrid architecture was rejected because atomic outbox insertion was assumed rather than proven. No later event-driven design is legitimate until this uncertainty is closed.

## Risk and authorization

- Risk: `CRITICAL`
- Task class: `architecture-sensitive runtime spike`
- Authorization: `HORIZON_0_PROTOTYPE`
- Series: `LTAIP-H0-VALIDATION-001`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Supervisor review: mandatory

## Repository binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Repository snapshot used while authoring: `d844d71d9ec9b55905dbb545662fc5c0f989e87c`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `prototype/TP-LTAIP-H0-004-atomicity-event-path`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-H0-004`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-003`

## Scope IN

- Release-pinned Leantime 3.9.8 source trace.
- Representative create/update/delete/comment/time mutation paths.
- Plugin probe, listener failures, duplicates, reordering, crash recovery, and polling reconciliation.
- One explicit core-patch/upstream event variant with two-version rebase measurement.

## Scope OUT

- Production outbox or event bus.
- External writes inside canonical transactions.
- Long-lived fork.
- Direct database integration from Dopemux.
- Base-product selection.

## Invariants

- All work uses disposable synthetic instances.
- No user-visible success is credited before canonical commit.
- Polling is labeled non-atomic and reconciliatory.
- Core changes remain patch artifacts, not a fork.
- No weighted score rescues lost or duplicated canonical events.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-004.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-004.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/MERGE_READINESS.json`
- `config/leantime-ai-parity/h0/atomicity-spike.json`
- `compose/leantime-ai-parity/h0/compose.atomicity-spike.yml`
- `plugins/leantime-ai-parity-h0-atomicity-spike/README.md`
- `plugins/leantime-ai-parity-h0-atomicity-spike/app/Listeners/OutboxProbe.php`
- `plugins/leantime-ai-parity-h0-atomicity-spike/app/Services/OutboxProbe.php`
- `plugins/leantime-ai-parity-h0-atomicity-spike/database/migrations/2026_01_01_000001_create_ltaip_probe_outbox.php`
- `scripts/leantime-ai-parity/h0/atomicity/materialize_source.py`
- `scripts/leantime-ai-parity/h0/atomicity/trace_mutations.py`
- `scripts/leantime-ai-parity/h0/atomicity/run_failure_matrix.py`
- `scripts/leantime-ai-parity/h0/atomicity/run_polling_reconciliation.py`
- `scripts/leantime-ai-parity/h0/atomicity/measure_rebase_tax.py`
- `scripts/leantime-ai-parity/h0/atomicity/destroy_spike.sh`
- `tests/prototypes/leantime-ai-parity/h0/atomicity/test_commit_rollback.py`
- `tests/prototypes/leantime-ai-parity/h0/atomicity/test_listener_failure.py`
- `tests/prototypes/leantime-ai-parity/h0/atomicity/test_duplicate_reorder.py`
- `tests/prototypes/leantime-ai-parity/h0/atomicity/test_crash_recovery.py`
- `docs/06-research/leantime-ai-parity/h0/atomicity/event-path-protocol.md`
- `docs/06-research/leantime-ai-parity/h0/atomicity/mutation-semantics.md`
- `docs/06-research/leantime-ai-parity/h0/atomicity/architecture-disposition.md`
- `reports/leantime-ai-parity/h0/atomicity/mutation-paths.json`
- `reports/leantime-ai-parity/h0/atomicity/failure-matrix.json`
- `reports/leantime-ai-parity/h0/atomicity/reconciliation-results.json`
- `reports/leantime-ai-parity/h0/atomicity/core-patch/leantime-v3.9.8.patch`
- `reports/leantime-ai-parity/h0/atomicity/core-patch/next-release.patch`
- `reports/leantime-ai-parity/h0/atomicity/rebase-tax.json`
- `reports/leantime-ai-parity/h0/atomicity/manifest.json`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-004" -b "prototype/TP-LTAIP-H0-004-atomicity-event-path" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-004"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "prototype/TP-LTAIP-H0-004-atomicity-event-path"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-H0-004/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Pin source and trace mutation paths

**Objective:** Materialize Leantime 3.9.8 source in tmp and produce call/transaction traces for representative mutations.

**Requirements**

- Use candidate lock from Packet 002 and exposure manifest from Packet 003.
- Temporary upstream source is never committed.
- Trace transaction entry, repository write, event dispatch, listener invocation, and response timing.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/atomicity/materialize_source.py --lock config/leantime-ai-parity/h0/candidate-images.lock.json --output tmp/ltaip-h0-004
python scripts/leantime-ai-parity/h0/atomicity/trace_mutations.py --source tmp/ltaip-h0-004/leantime --output reports/leantime-ai-parity/h0/atomicity/mutation-paths.json
```

**Expected artifacts**

- `config/leantime-ai-parity/h0/atomicity-spike.json`
- `docs/06-research/leantime-ai-parity/h0/atomicity/event-path-protocol.md`
- `reports/leantime-ai-parity/h0/atomicity/mutation-paths.json`

**Exit conditions**

- Every representative mutation has a complete call-order record.
- Transaction boundaries and UNKNOWN segments are explicit.
### Slice 2: Probe plugin boundary and failure modes

**Objective:** Install the disposable probe plugin and execute commit, rollback, listener failure, duplicate, reorder, and crash tests.

**Requirements**

- No external HTTP in listeners.
- All records carry transaction/correlation IDs.
- Synthetic data only.

**Commands**

```bash
docker compose -f compose/leantime-ai-parity/h0/compose.atomicity-spike.yml up -d --build
python scripts/leantime-ai-parity/h0/atomicity/run_failure_matrix.py --config config/leantime-ai-parity/h0/atomicity-spike.json --output reports/leantime-ai-parity/h0/atomicity/failure-matrix.json
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/atomicity
```

**Expected artifacts**

- `plugins/leantime-ai-parity-h0-atomicity-spike/app/Listeners/OutboxProbe.php`
- `plugins/leantime-ai-parity-h0-atomicity-spike/app/Services/OutboxProbe.php`
- `reports/leantime-ai-parity/h0/atomicity/failure-matrix.json`

**Exit conditions**

- Atomicity is proven with failure evidence or explicitly disproven.
- Lost, duplicate, and reordered events are counted.
### Slice 3: Evaluate reconciliation and core-patch alternatives

**Objective:** Prototype bounded polling/reconciliation and measure one transaction-aware core-patch variant across two source versions.

**Requirements**

- Polling never claims atomicity.
- Core patch is stored only as a report artifact.
- Rebase work is measured, not narrated.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/atomicity/run_polling_reconciliation.py --config config/leantime-ai-parity/h0/atomicity-spike.json --output reports/leantime-ai-parity/h0/atomicity/reconciliation-results.json
python scripts/leantime-ai-parity/h0/atomicity/measure_rebase_tax.py --source tmp/ltaip-h0-004/leantime --output reports/leantime-ai-parity/h0/atomicity/rebase-tax.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/atomicity/reconciliation-results.json`
- `reports/leantime-ai-parity/h0/atomicity/core-patch/leantime-v3.9.8.patch`
- `reports/leantime-ai-parity/h0/atomicity/core-patch/next-release.patch`
- `reports/leantime-ai-parity/h0/atomicity/rebase-tax.json`
- `docs/06-research/leantime-ai-parity/h0/atomicity/architecture-disposition.md`

**Exit conditions**

- Each alternative has explicit semantics, loss window, recovery path, and maintenance cost.
- No architecture is selected when a P0 correctness failure remains.
### Slice 4: Teardown, audit, proof, and PR

**Objective:** Destroy the spike, run independent audit, finalize proof, and obtain PR Steward readiness.

**Requirements**

- No containers, volumes, or tmp source remain.
- Security/authority supervisor review is mandatory.

**Commands**

```bash
bash scripts/leantime-ai-parity/h0/atomicity/destroy_spike.sh --volumes
rm -rf tmp/ltaip-h0-004
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-004.json")), json.load(open("dopetask-cannonical-spec.json")))'
docker compose -f compose/leantime-ai-parity/h0/compose.atomicity-spike.yml config --quiet
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/atomicity
python -m json.tool config/leantime-ai-parity/h0/atomicity-spike.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/mutation-paths.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/failure-matrix.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/reconciliation-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/rebase-tax.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/atomicity/event-path-protocol.md docs/06-research/leantime-ai-parity/h0/atomicity/mutation-semantics.md docs/06-research/leantime-ai-parity/h0/atomicity/architecture-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json
git diff --check
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/atomicity/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-004/MERGE_READINESS.json`

**Exit conditions**

- Teardown evidence passes.
- Independent audit is non-blocking.
- Supervisor adjudicates before merge.


## Required PAL chain

`apilookup -> analyze -> tracer -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> secaudit -> codereview -> precommit -> challenge`

Escalation rules:

- Use `tracer` to prove mutation and event call order.
- Use `debug` on any commit/rollback contradiction.
- Use `secaudit` because event loss can corrupt authority.
- Use `consensus` only if two fallback semantics remain equally defensible.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- False atomicity claims.
- Listener failure and rollback gaps.
- Duplicate/reorder handling.
- Polling reconciliation blind spots.
- Hidden core-fork maintenance tax.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-004.json")), json.load(open("dopetask-cannonical-spec.json")))'
docker compose -f compose/leantime-ai-parity/h0/compose.atomicity-spike.yml config --quiet
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/atomicity
python -m json.tool config/leantime-ai-parity/h0/atomicity-spike.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/mutation-paths.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/failure-matrix.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/reconciliation-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/rebase-tax.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/atomicity/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/atomicity/event-path-protocol.md docs/06-research/leantime-ai-parity/h0/atomicity/mutation-semantics.md docs/06-research/leantime-ai-parity/h0/atomicity/architecture-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-H0-004/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-H0-004/PRECOMMIT.txt
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

- Destroy candidate containers and volumes.
- Remove probe plugin bind mount and temporary source.
- Revert packet commit if evidence is invalidated.
- Preserve superseded evidence rather than rewriting it.

## Stop conditions

Stop immediately when:

- Packet 003 proof is missing or stale.
- Leantime source/image identity is unresolved.
- Production data or credentials appear.
- A listener performs external I/O inside a canonical transaction.
- Atomicity cannot be tested deterministically.
- Auditor or supervisor blocks.
- Diff escapes the allowlist.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Mutation-path disposition and atomicity verdict.
- Failure matrix, reconciliation semantics, and measured rebase tax.
