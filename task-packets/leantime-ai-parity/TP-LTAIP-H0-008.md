---
id: TP-LTAIP-H0-008
title: Tp Ltaip H0 008
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Ltaip H0 008 (explanation) for dopemux documentation and developer workflows.
---
# Macro Packet: TP-LTAIP-H0-008

## Status

`BLOCKED_BY_ALL_H0_EVIDENCE`

## Claim posture

- **OBSERVED:** Stage 07 rejection remains binding.
- **PROPOSED:** Hard veto gates and complete traceability can support a decision.
- **UNKNOWN:** Whether any candidate survives.
- **CONFLICTING:** Experience, security, maintenance, and cost evidence may point to different candidates; P0 gates outrank scores.

## Objective

Independently adjudicate all Horizon 0 evidence and emit one evidence-current result: select one release-pinned base/variant, reject all candidates, or return to prototype with named missing evidence.

## Why this packet exists now

Stage 08 authorizes validation, not adoption. No post-selection packet can start until this gate resolves every binding correction without weighted rescue.

## Risk and authorization

- Risk: `CRITICAL`
- Task class: `independent architecture decision gate`
- Authorization: `HORIZON_0_DECISION_GATE`
- Series: `LTAIP-H0-VALIDATION-001`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Supervisor review: mandatory

## Repository binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Repository snapshot used while authoring: `d844d71d9ec9b55905dbb545662fc5c0f989e87c`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `decision/TP-LTAIP-H0-008-base-selection`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-H0-008`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-001`
- `TP-LTAIP-H0-002`
- `TP-LTAIP-H0-003`
- `TP-LTAIP-H0-004`
- `TP-LTAIP-H0-005`
- `TP-LTAIP-H0-006`
- `TP-LTAIP-H0-007`

## Scope IN

- Evidence harvest and hash verification for Packets 001-007.
- P0/P1 classification and every RC07 correction.
- Leantime/OpenProject comparison and Plane trigger evaluation.
- Independent review, decision ADR, readiness JSON, and proof.

## Scope OUT

- Implementation before decision.
- Weighted rescue.
- Silent scope expansion.
- Production authority.
- Migration execution.

## Invariants

- All Packets 001-007 are merged and evidence-current.
- Security, workflow, accessibility, mobile, backup, and admin P0 failures are vetoes.
- Stage 07 corrections are resolved or remain blockers.
- Reviewer is independent from prototype implementers.
- One base/variant is selected or all are rejected.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-008.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-008.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/MERGE_READINESS.json`
- `scripts/leantime-ai-parity/h0/base-selection/harvest_evidence.py`
- `scripts/leantime-ai-parity/h0/base-selection/adjudicate_gates.py`
- `scripts/leantime-ai-parity/h0/base-selection/validate_traceability.py`
- `tests/prototypes/leantime-ai-parity/h0/base-selection/test_gate_vetoes.py`
- `tests/prototypes/leantime-ai-parity/h0/base-selection/test_traceability.py`
- `reports/leantime-ai-parity/h0/base-selection/p0-p1-disposition.csv`
- `docs/06-research/leantime-ai-parity/h0/base-selection/evidence-adjudication.md`
- `docs/90-adr/adr-ltaip-h0-008-base-selection.md`
- `reports/leantime-ai-parity/h0/base-selection/evidence-inventory.json`
- `reports/leantime-ai-parity/h0/base-selection/correction-disposition.json`
- `reports/leantime-ai-parity/h0/base-selection/base-selection-readiness.json`
- `reports/leantime-ai-parity/h0/base-selection/decision.json`
- `reports/leantime-ai-parity/h0/base-selection/manifest.json`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-008" -b "decision/TP-LTAIP-H0-008-base-selection" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-008"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "decision/TP-LTAIP-H0-008-base-selection"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-001/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-001/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-002/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-004/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-007/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-007/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-H0-008/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Harvest and verify H0 evidence

**Objective:** Collect content-addressed evidence from Packets 001-007 and fail closed on stale or missing proof.

**Requirements**

- Latest merged head and proof hash for every packet.
- No narrative-only substitution.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/base-selection/harvest_evidence.py --output reports/leantime-ai-parity/h0/base-selection/evidence-inventory.json
python scripts/leantime-ai-parity/h0/base-selection/validate_traceability.py --inventory reports/leantime-ai-parity/h0/base-selection/evidence-inventory.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/base-selection/evidence-inventory.json`
- `docs/06-research/leantime-ai-parity/h0/base-selection/evidence-adjudication.md`

**Exit conditions**

- All required evidence hashes resolve and are current.
### Slice 2: Apply P0/P1 vetoes and correction ledger

**Objective:** Classify every finding and Stage 07 correction without aggregate-score rescue.

**Requirements**

- All RC07-001 through RC07-012 resolved or explicit blocker.
- Plane is triggered only by documented criteria.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/base-selection/adjudicate_gates.py --inventory reports/leantime-ai-parity/h0/base-selection/evidence-inventory.json --output reports/leantime-ai-parity/h0/base-selection/base-selection-readiness.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/base-selection/p0-p1-disposition.csv`
- `reports/leantime-ai-parity/h0/base-selection/correction-disposition.json`
- `reports/leantime-ai-parity/h0/base-selection/base-selection-readiness.json`

**Exit conditions**

- No vetoed candidate remains selectable.
- Unresolved evidence remains blocking.
### Slice 3: Emit independent decision ADR

**Objective:** Select one release-pinned base/variant, reject all, or return to prototype with exact evidence requests.

**Requirements**

- Reversal evidence explicit.
- Post-selection packets remain conditional until merge.

**Commands**

```bash
python -m json.tool reports/leantime-ai-parity/h0/base-selection/decision.json >/dev/null
python scripts/docs_validator.py docs/90-adr/adr-ltaip-h0-008-base-selection.md
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/base-selection/decision.json`
- `docs/90-adr/adr-ltaip-h0-008-base-selection.md`
- `reports/leantime-ai-parity/h0/base-selection/manifest.json`

**Exit conditions**

- Decision and ADR agree.
- Exactly one terminal outcome is emitted.
### Slice 4: Independent audit, proof, and supervisor gate

**Objective:** Run a fresh adversarial audit, finalize proof, PR Steward intake, and GPT-5.6 supervisor adjudication.

**Requirements**

- Same implementer cannot be final auditor.
- Supervisor approval mandatory.

**Commands**

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-008.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/base-selection
python -m json.tool reports/leantime-ai-parity/h0/base-selection/evidence-inventory.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/correction-disposition.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/base-selection-readiness.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/decision.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/base-selection/evidence-adjudication.md docs/90-adr/adr-ltaip-h0-008-base-selection.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json
git diff --check
```

**Expected artifacts**

- `proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-008/MERGE_READINESS.json`

**Exit conditions**

- Independent audit and supervisor agree or packet remains NEEDS_SUPERVISOR.


## Required PAL chain

`analyze -> thinkdeep -> challenge -> planner -> consensus -> challenge -> implement -> codereview -> precommit -> challenge`

Escalation rules:

- Use `consensus` only for surviving candidates after vetoes.
- Use a fresh independent reviewer.
- Escalate any evidence contradiction to GPT-5.6.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Evidence freshness and custody.
- Weighted rescue.
- Unresolved Stage 07 corrections.
- Experience/admin evidence treated as footnote.
- Premature implementation authorization.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-008.json")), json.load(open("dopetask-cannonical-spec.json")))'
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/base-selection
python -m json.tool reports/leantime-ai-parity/h0/base-selection/evidence-inventory.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/correction-disposition.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/base-selection-readiness.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/decision.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/base-selection/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/base-selection/evidence-adjudication.md docs/90-adr/adr-ltaip-h0-008-base-selection.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-H0-008/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-H0-008/PRECOMMIT.txt
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

- Return to prototype with named evidence gaps.
- Supersede, never erase, a later-invalidated decision.
- Keep post-selection packets blocked until a replacement gate merges.

## Stop conditions

Stop immediately when:

- Any dependency proof is missing or stale.
- Any P0/P1 disposition is unclassified.
- Any Stage 07 correction is silently ignored.
- Reviewer independence fails.
- A weighted score overrides a veto.
- Supervisor does not approve.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Terminal decision, candidate disposition, and reversal evidence.
- Complete Stage 07 correction ledger.
