# Macro Packet: TP-LTAIP-POST-010

## Status

`CONDITIONAL_NOT_AUTHORIZED_UNTIL_BASE_SELECTION`

## Claim posture

- **OBSERVED:** AI cannot receive parity credit for missing deterministic machinery.
- **PROPOSED:** A controller packet can generate exact selected-base child packets.
- **UNKNOWN:** Which gaps and implementation surfaces survive Packet 008.
- **CONFLICTING:** Build, official package, configuration, and upstream paths may differ per gap.

## Objective

Select at most three deterministic must-win gaps proven by H0, resolve configure/buy/upstream/build disposition, and generate exact base-specific implementation child packets with permission, accessibility, mobile, upgrade, rollback, and proof gates.

## Why this packet exists now

A single generic packet cannot honestly implement base-specific gaps before selection. The correct macro action is to generate bounded child packets after the decision.

## Risk and authorization

- Risk: `HIGH`
- Task class: `selected-base implementation series planning`
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
- Branch: `plan/TP-LTAIP-POST-010-parity-child-series`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-POST-010`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-008`
- `TP-LTAIP-H0-006`

## Scope IN

- Selected-base capability map.
- At most three must-win gaps.
- Disposition per gap: configure, buy, upstream, build, defer, or reject.
- Strict dopeTask child packets and dependency DAG.

## Scope OUT

- Feature implementation in this controller packet.
- Unselected base paths.
- AI substitute.
- Enterprise feature-count expansion.

## Invariants

- Packet 008 decision and Packet 006 package evidence are current.
- At most three gaps.
- One canonical writer per capability.
- Each child packet has exact code paths after selected-base inspection.
- No child packet is executable until supervisor review.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-POST-010.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-POST-010.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/MERGE_READINESS.json`
- `scripts/leantime-ai-parity/h1/generate_parity_child_packets.py`
- `scripts/leantime-ai-parity/h1/validate_selected_gaps.py`
- `tests/prototypes/leantime-ai-parity/h1/test_selected_gap_plan.py`
- `tests/prototypes/leantime-ai-parity/h1/test_generated_child_packets.py`
- `task-packets/leantime-ai-parity/generated/parity-foundation/`
- `docs/06-research/leantime-ai-parity/h1/parity-foundation/selected-gap-plan.md`
- `docs/06-research/leantime-ai-parity/h1/parity-foundation/child-packet-review.md`
- `config/leantime-ai-parity/h1/selected-gap-plan.json`
- `reports/leantime-ai-parity/h1/parity-foundation/capability-map.json`
- `reports/leantime-ai-parity/h1/parity-foundation/child-packet-manifest.json`
- `reports/leantime-ai-parity/h1/parity-foundation/manifest.json`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-POST-010" -b "plan/TP-LTAIP-POST-010-parity-child-series" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-POST-010"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "plan/TP-LTAIP-POST-010-parity-child-series"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-008/PROOF.json
test -f proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-006/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-POST-010/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Select and disposition deterministic gaps

**Objective:** Map H0 workflow failures to at most three deterministic gaps and choose evidence-backed disposition.

**Requirements**

- Hard-gate failures first.
- No feature-count selection.
- Package qualification considered.

**Commands**

```bash
python scripts/leantime-ai-parity/h1/validate_selected_gaps.py --decision reports/leantime-ai-parity/h0/base-selection/decision.json --output config/leantime-ai-parity/h1/selected-gap-plan.json
```

**Expected artifacts**

- `config/leantime-ai-parity/h1/selected-gap-plan.json`
- `reports/leantime-ai-parity/h1/parity-foundation/capability-map.json`
- `docs/06-research/leantime-ai-parity/h1/parity-foundation/selected-gap-plan.md`

**Exit conditions**

- At most three gaps.
- Each has canonical writer, evidence, disposition, and acceptance target.
### Slice 2: Generate base-specific child packet series

**Objective:** Inspect selected-base runtime and generate exact per-gap packets under the strict schema.

**Requirements**

- No wildcard runtime allowlists.
- Each child packet commit-sized.
- Permission, accessibility, mobile, upgrade, rollback, audit, and proof included.

**Commands**

```bash
python scripts/leantime-ai-parity/h1/generate_parity_child_packets.py --plan config/leantime-ai-parity/h1/selected-gap-plan.json --output task-packets/leantime-ai-parity/generated/parity-foundation --manifest reports/leantime-ai-parity/h1/parity-foundation/child-packet-manifest.json
python -m pytest -q tests/prototypes/leantime-ai-parity/h1/test_generated_child_packets.py
```

**Expected artifacts**

- `task-packets/leantime-ai-parity/generated/parity-foundation/`
- `reports/leantime-ai-parity/h1/parity-foundation/child-packet-manifest.json`
- `docs/06-research/leantime-ai-parity/h1/parity-foundation/child-packet-review.md`

**Exit conditions**

- Every child packet validates.
- Dependencies are acyclic.
- No implementation performed.
### Slice 3: Audit generated series and hand off

**Objective:** Run independent packet audit, finalize proof, and request supervisor approval for child execution.

**Requirements**

- Auditor reads selected-base runtime paths.
- Supervisor approval required.

**Commands**

```bash
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-010.json")), json.load(open("dopetask-cannonical-spec.json")))' 
python -m pytest -q tests/prototypes/leantime-ai-parity/h1/test_selected_gap_plan.py tests/prototypes/leantime-ai-parity/h1/test_generated_child_packets.py
python -m json.tool config/leantime-ai-parity/h1/selected-gap-plan.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/parity-foundation/capability-map.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/parity-foundation/child-packet-manifest.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/parity-foundation/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h1/parity-foundation/selected-gap-plan.md docs/06-research/leantime-ai-parity/h1/parity-foundation/child-packet-review.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-010/PROOF.json
git diff --check
```

**Expected artifacts**

- `reports/leantime-ai-parity/h1/parity-foundation/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-POST-010/AUDITOR_REPORT.md`

**Exit conditions**

- Generated series is exact, bounded, and non-executing.


## Required PAL chain

`analyze -> thinkdeep -> challenge -> planner -> consensus -> challenge -> implement -> codereview -> precommit -> challenge`

Escalation rules:

- Use `consensus` for genuine build/buy/upstream alternatives.
- Use `apilookup` inside child packet authoring for current selected-base APIs.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Too many gaps.
- Generic paths invented before inspection.
- AI substitution.
- Duplicate authority.
- Package evidence ignored.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-POST-010.json")), json.load(open("dopetask-cannonical-spec.json")))' 
python -m pytest -q tests/prototypes/leantime-ai-parity/h1/test_selected_gap_plan.py tests/prototypes/leantime-ai-parity/h1/test_generated_child_packets.py
python -m json.tool config/leantime-ai-parity/h1/selected-gap-plan.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/parity-foundation/capability-map.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/parity-foundation/child-packet-manifest.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h1/parity-foundation/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h1/parity-foundation/selected-gap-plan.md docs/06-research/leantime-ai-parity/h1/parity-foundation/child-packet-review.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-POST-010/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-POST-010/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-POST-010/PRECOMMIT.txt
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

- Delete unexecuted generated child packets.
- Supersede selected-gap plan if base decision changes.

## Stop conditions

Stop immediately when:

- Packet 008 decision absent or ambiguous.
- More than three gaps proposed.
- Exact selected-base code paths cannot be proven.
- A child packet uses wildcard runtime scope.
- AI substitutes for deterministic machinery.
- Supervisor blocks.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- Selected gaps and dispositions.
- Generated child packet IDs, DAG, and validation.
