# Macro Packet: TP-LTAIP-H0-005

## Status

`BLOCKED_BY_DEPENDENCY`

## Claim posture

- **OBSERVED:** Production derived indexing is blocked.
- **PROPOSED:** A synthetic, destroyable lab can test lineage and revocation without production exposure.
- **UNKNOWN:** Whether acceptable revocation latency is achievable.
- **CONFLICTING:** Retrieval usefulness and strict authorization may impose different caching choices.

## Objective

Prove that a destroyable derived-data index can preserve project authorization, deletion, freshness, citations, and hostile-content isolation under synthetic multi-project changes.

## Why this packet exists now

Stage 07 blocks production indexing because a derived store can become a shadow authorization and retention system.

## Risk and authorization

- Risk: `CRITICAL`
- Task class: `security-sensitive synthetic laboratory`
- Authorization: `HORIZON_0_SYNTHETIC_ONLY`
- Series: `LTAIP-H0-VALIDATION-001`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Supervisor review: mandatory

## Repository binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Repository snapshot used while authoring: `d844d71d9ec9b55905dbb545662fc5c0f989e87c`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `security/TP-LTAIP-H0-005-derived-data-lab`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-H0-005`

Runtime repository truth outranks this packet. If paths or entrypoints drift before execution, stop and return the exact mismatch rather than adapting silently.

## Dependencies

- `TP-LTAIP-H0-003`

## Scope IN

- Synthetic projects, users, ACL changes, revisions, tombstones, and hostile content.
- Ingest, retrieval, generation-context, citation, and cache filtering.
- Deletion and revocation latency measurement.
- Destroy/rebuild recovery.

## Scope OUT

- Production or client data.
- Global cross-tenant index.
- Write tools or autonomous agents.
- Production model calls unless explicitly mocked or approved.

## Invariants

- Canonical source always wins.
- Authorization is enforced at ingest, retrieval, context assembly, citation, and cache.
- Retrieved content is data, never executable instruction.
- Zero cross-project leakage.
- The entire derived store remains destroyable and rebuildable.

## Authorized file allowlist

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-005.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-005.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/MERGE_READINESS.json`
- `config/leantime-ai-parity/h0/derived-data-lab.json`
- `compose/leantime-ai-parity/h0/compose.derived-data-lab.yml`
- `scripts/leantime-ai-parity/h0/derived-data/resolve_lab_images.py`
- `scripts/leantime-ai-parity/h0/derived-data/generate_corpus.py`
- `scripts/leantime-ai-parity/h0/derived-data/build_index.py`
- `scripts/leantime-ai-parity/h0/derived-data/run_acl_matrix.py`
- `scripts/leantime-ai-parity/h0/derived-data/run_deletion_matrix.py`
- `scripts/leantime-ai-parity/h0/derived-data/run_injection_suite.py`
- `scripts/leantime-ai-parity/h0/derived-data/destroy_lab.sh`
- `tests/prototypes/leantime-ai-parity/h0/derived-data/test_acl_transitions.py`
- `tests/prototypes/leantime-ai-parity/h0/derived-data/test_deletion_tombstones.py`
- `tests/prototypes/leantime-ai-parity/h0/derived-data/test_cache_invalidation.py`
- `tests/prototypes/leantime-ai-parity/h0/derived-data/test_prompt_injection.py`
- `tests/fixtures/leantime-ai-parity/h0/derived-data/synthetic-corpus.jsonl`
- `tests/fixtures/leantime-ai-parity/h0/derived-data/hostile-content.jsonl`
- `docs/06-research/leantime-ai-parity/h0/derived-data/authorization-model.md`
- `docs/06-research/leantime-ai-parity/h0/derived-data/injection-threat-model.md`
- `docs/06-research/leantime-ai-parity/h0/derived-data/lab-disposition.md`
- `reports/leantime-ai-parity/h0/derived-data/corpus-manifest.json`
- `reports/leantime-ai-parity/h0/derived-data/acl-transition-results.json`
- `reports/leantime-ai-parity/h0/derived-data/deletion-results.json`
- `reports/leantime-ai-parity/h0/derived-data/injection-results.json`
- `reports/leantime-ai-parity/h0/derived-data/retrieval-traces.jsonl`
- `reports/leantime-ai-parity/h0/derived-data/manifest.json`

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-005" -b "security/TP-LTAIP-H0-005-derived-data-lab" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-005"

test -f .dopetaskroot
test -s .repo_id
test "$(git branch --show-current)" = "security/TP-LTAIP-H0-005-derived-data-lab"
test -z "$(git status --porcelain)"

test -f proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-003/PROOF.json

git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_STATUS_BEFORE.txt
git rev-parse HEAD | tee proof/leantime-ai-parity/TP-LTAIP-H0-005/START_HEAD_SHA.txt
```

## Commit-slice plan

### Slice 1: Define policy and synthetic corpus

**Objective:** Create the lineage, ACL, tombstone, citation, and hostile-data model plus deterministic synthetic corpus.

**Requirements**

- All identities and content are synthetic.
- Every record has project, source version, ACL, deletion state, and lineage.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/derived-data/resolve_lab_images.py --output config/leantime-ai-parity/h0/derived-data-lab.json
python scripts/leantime-ai-parity/h0/derived-data/generate_corpus.py --output tests/fixtures/leantime-ai-parity/h0/derived-data/synthetic-corpus.jsonl --manifest reports/leantime-ai-parity/h0/derived-data/corpus-manifest.json
```

**Expected artifacts**

- `config/leantime-ai-parity/h0/derived-data-lab.json`
- `tests/fixtures/leantime-ai-parity/h0/derived-data/synthetic-corpus.jsonl`
- `tests/fixtures/leantime-ai-parity/h0/derived-data/hostile-content.jsonl`
- `reports/leantime-ai-parity/h0/derived-data/corpus-manifest.json`
- `docs/06-research/leantime-ai-parity/h0/derived-data/authorization-model.md`
- `docs/06-research/leantime-ai-parity/h0/derived-data/injection-threat-model.md`

**Exit conditions**

- Corpus is deterministic and contains positive and negative ACL transitions.
- No real data or secrets are present.
### Slice 2: Build ephemeral index and run ACL/deletion matrix

**Objective:** Build the disposable index and test grant, revoke, move, delete, restore, cache, and citation behavior.

**Requirements**

- Authorization checks occur at every stage.
- Deleted or revoked content becomes unreachable inside the pre-registered SLO.

**Commands**

```bash
docker compose -f compose/leantime-ai-parity/h0/compose.derived-data-lab.yml up -d
python scripts/leantime-ai-parity/h0/derived-data/build_index.py --config config/leantime-ai-parity/h0/derived-data-lab.json --corpus tests/fixtures/leantime-ai-parity/h0/derived-data/synthetic-corpus.jsonl
python scripts/leantime-ai-parity/h0/derived-data/run_acl_matrix.py --output reports/leantime-ai-parity/h0/derived-data/acl-transition-results.json
python scripts/leantime-ai-parity/h0/derived-data/run_deletion_matrix.py --output reports/leantime-ai-parity/h0/derived-data/deletion-results.json
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/derived-data/acl-transition-results.json`
- `reports/leantime-ai-parity/h0/derived-data/deletion-results.json`
- `reports/leantime-ai-parity/h0/derived-data/retrieval-traces.jsonl`

**Exit conditions**

- Zero cross-project leakage.
- Deletion/revocation SLO is measured, not assumed.
- Citations resolve only to current authorized sources.
### Slice 3: Run hostile-content and instruction-boundary suite

**Objective:** Test hostile source instructions, retrieval poisoning, citation spoofing, and cache replay.

**Requirements**

- Retrieved text cannot invoke tools or alter policy.
- No external side effect is allowed.

**Commands**

```bash
python scripts/leantime-ai-parity/h0/derived-data/run_injection_suite.py --corpus tests/fixtures/leantime-ai-parity/h0/derived-data/hostile-content.jsonl --output reports/leantime-ai-parity/h0/derived-data/injection-results.json
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/derived-data
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/derived-data/injection-results.json`
- `docs/06-research/leantime-ai-parity/h0/derived-data/lab-disposition.md`

**Exit conditions**

- No policy or tool boundary bypass.
- All failures are reproducible and classified.
### Slice 4: Destroy, audit, and prove

**Objective:** Destroy the derived store, prove rebuildability, run security audit, and obtain PR Steward output.

**Requirements**

- No derived data survives teardown.
- Supervisor review is mandatory.

**Commands**

```bash
bash scripts/leantime-ai-parity/h0/derived-data/destroy_lab.sh --volumes
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-005.json")), json.load(open("dopetask-cannonical-spec.json")))' 
docker compose -f compose/leantime-ai-parity/h0/compose.derived-data-lab.yml config --quiet
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/derived-data
python -m json.tool config/leantime-ai-parity/h0/derived-data-lab.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/corpus-manifest.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/acl-transition-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/deletion-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/injection-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/derived-data/authorization-model.md docs/06-research/leantime-ai-parity/h0/derived-data/injection-threat-model.md docs/06-research/leantime-ai-parity/h0/derived-data/lab-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json
git diff --check
```

**Expected artifacts**

- `reports/leantime-ai-parity/h0/derived-data/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-005/AUDITOR_REPORT.md`

**Exit conditions**

- Destroy/rebuild evidence exists.
- Security audit has no open P0/P1 finding.


## Required PAL chain

`analyze -> tracer -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> secaudit -> codereview -> precommit -> challenge`

Escalation rules:

- Use `tracer` for lineage and cache paths.
- Use `secaudit` for every ACL or injection claim.
- Use `debug` on any leakage or stale-cache contradiction.

## Embedded audit

Run the auditor after implementation stabilizes and before final proof. Route order:

1. AGY / Google Antigravity with Sonnet when available.
2. Claude Code CLI Sonnet.
3. Claude Code CLI Opus for depth, security, or unresolved conflict.
4. Gemini CLI for broad-context contradiction hunting.

The normalized `embedded_audit` object must use the canonical fields and enums from `docs/ops/embedded-audit-proof.md`. Required-audit `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks completion.

Audit focus:

- Cross-project leakage.
- Deletion and cache invalidation gaps.
- Citation to stale or unauthorized source.
- Prompt-injection policy bypass.
- Hidden production coupling.

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
python -c 'import json,jsonschema; jsonschema.validate(json.load(open("task-packets/leantime-ai-parity/TP-LTAIP-H0-005.json")), json.load(open("dopetask-cannonical-spec.json")))' 
docker compose -f compose/leantime-ai-parity/h0/compose.derived-data-lab.yml config --quiet
python -m pytest -q tests/prototypes/leantime-ai-parity/h0/derived-data
python -m json.tool config/leantime-ai-parity/h0/derived-data-lab.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/corpus-manifest.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/acl-transition-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/deletion-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/injection-results.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/derived-data/manifest.json >/dev/null
python scripts/docs_validator.py docs/06-research/leantime-ai-parity/h0/derived-data/authorization-model.md docs/06-research/leantime-ai-parity/h0/derived-data/injection-threat-model.md docs/06-research/leantime-ai-parity/h0/derived-data/lab-disposition.md
python scripts/check_docs_hygiene.py
python scripts/check_docs_filename_hygiene.py
python scripts/check_root_hygiene.py
python scripts/audit/validate_audit_proof.py proof/leantime-ai-parity/TP-LTAIP-H0-005/PROOF.json
git diff --check
```

Then run:

```bash
git status --short | tee proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_STATUS_AFTER.txt
git diff --stat | tee proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_DIFF_STAT.txt
git diff | tee proof/leantime-ai-parity/TP-LTAIP-H0-005/GIT_DIFF.patch
pre-commit run --all-files | tee proof/leantime-ai-parity/TP-LTAIP-H0-005/PRECOMMIT.txt
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

- Destroy the index, containers, volumes, and caches.
- Disable all lab configuration.
- Revert packet commit if invalidated.

## Stop conditions

Stop immediately when:

- Packet 003 proof is stale.
- Any production data or credential appears.
- Any cross-project leak occurs.
- Deletion or revocation cannot be measured.
- Retrieved data triggers a tool or policy change.
- Audit or supervisor blocks.

## Required final return

- Objective status and authorization posture.
- Exact files changed and commands with exit codes.
- Git status before and after, start/end SHA, diff stat, and full diff.
- Artifact hashes and validation summary.
- Embedded audit record and residual risks.
- PR URL, latest head SHA, checks, review classification, and PR Steward readiness.
- ACL/deletion latency and leakage result.
- Injection-suite result and destruction proof.
