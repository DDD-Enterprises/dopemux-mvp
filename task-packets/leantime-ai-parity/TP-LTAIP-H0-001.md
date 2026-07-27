# Macro Packet: TP-LTAIP-H0-001

## Status

`READY_FOR_EXECUTION`

## Claim posture

- **OBSERVED:** Stage 08 authorizes prototype validation only and names segment/workflow lock as the first milestone.
- **OBSERVED:** The provisional buyer and personas remain hypotheses.
- **PROPOSED:** This packet's qualitative pilot thresholds make the research executable without claiming statistical market proof.
- **UNKNOWN:** Qualified participant availability and whether the provisional personas survive.
- **CONFLICTING:** Stage 05 selected a hybrid architecture; Stage 07 rejected it. The rejection remains binding.

## Objective

Produce a consent-safe, evidence-backed lock containing exactly one economic-buyer archetype, exactly two primary personas, exactly three must-win workflows, explicit non-targets, product-neutral fixtures, and reversal criteria.

## Why this packet exists now

Every later prototype depends on knowing who is being served and which workflows must be identical across candidates. Running candidate trials before this lock would produce expensive, polished ambiguity.

## Risk and task class

- Risk: `HIGH`
- Task class: research-sensitive, decision-sensitive, privacy-sensitive
- Authorization: `HORIZON_0_PROTOTYPE`
- Primary implementer: Codex in a dedicated worktree
- Embedded auditor: mandatory
- Merge authority: PR Steward, with supervisor escalation on conflict

## Repo binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- Base branch: `main`
- Required marker: `.dopetaskroot`
- Branch: `research/TP-LTAIP-H0-001-segment-workflow-lock`
- Worktree: `../dopemux-mvp-wt-TP-LTAIP-H0-001`

## Authority inputs

1. Runtime repository rules and hygiene policy.
2. Stage 08 executive decision and EPIC-08-001.
3. Stage 07 corrections carried through Stage 08.
4. This packet's pre-registered protocol.

Stage 08 artifacts are planning authority only. They do not outrank runtime repository policy.

## Scope

### IN

- Research protocol, recruitment criteria, consent and redaction rules
- Structured session-evidence schema
- Buyer and persona criteria ranking
- Product-neutral workflow fixtures
- Segment/persona/workflow decision record
- Dissent and reversal register
- Proof, embedded audit, PR, and PR Steward intake

### OUT

- Product implementation
- Candidate deployment
- Base-product selection
- Purchase or paid-plugin access
- Production data or credentials
- Raw transcript or recording storage in git
- Marketing claims
- Migration or release

## Invariants

1. No base product is preferred in the research protocol or fixture wording.
2. No raw personal data enters the repository.
3. Exactly one buyer, two personas, and three workflows are selected or the packet blocks.
4. Contradictions remain visible.
5. The lock is a Horizon 0 hypothesis supported by qualitative evidence, not a market-size claim.
6. Packet 002 cannot start until this packet merges.

## Proposed minimum evidence gate

The packet may complete only when:

- at least five distinct qualified participants are represented;
- at least three sessions include budget ownership, purchase influence, or self-host operating responsibility;
- each selected primary persona has support from at least three independent sessions, with overlap allowed;
- each selected workflow is supported by at least three sessions;
- each selected workflow is top-five in buyer importance and user frequency/pain;
- no unresolved P0 contradiction remains.

Failure returns `BLOCKED_INSUFFICIENT_SEGMENT_EVIDENCE`.

## Authorized files

- `task-packets/leantime-ai-parity/TP-LTAIP-H0-001.json`
- `task-packets/leantime-ai-parity/TP-LTAIP-H0-001.md`
- `task-packets/INDEX.md`
- `docs/INDEX.md`
- `docs/docs_index.yaml`
- `docs/06-research/leantime-ai-parity/h0/segment-lock/research-protocol.md`
- `docs/06-research/leantime-ai-parity/h0/segment-lock/recruitment-and-consent.md`
- `docs/06-research/leantime-ai-parity/h0/segment-lock/interview-guide.md`
- `docs/06-research/leantime-ai-parity/h0/segment-lock/workflow-fixture-spec.md`
- `docs/06-research/leantime-ai-parity/h0/segment-lock/segment-workflow-lock.md`
- `docs/06-research/leantime-ai-parity/h0/segment-lock/assumptions-and-dissent.md`
- `docs/90-adr/adr-ltaip-h0-001-segment-workflow-lock.md`
- `reports/leantime-ai-parity/h0/segment-lock/participant-register.redacted.json`
- `reports/leantime-ai-parity/h0/segment-lock/session-evidence.jsonl`
- `reports/leantime-ai-parity/h0/segment-lock/criteria-ranking.csv`
- `reports/leantime-ai-parity/h0/segment-lock/segment-workflow-lock.json`
- `reports/leantime-ai-parity/h0/segment-lock/manifest.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/PROOF.json`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/COMMAND_LOG.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/AUDITOR_REPORT.md`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_STATUS_BEFORE.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_STATUS_AFTER.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_DIFF_STAT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_DIFF.patch`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/PRECOMMIT.txt`
- `proof/leantime-ai-parity/TP-LTAIP-H0-001/MERGE_READINESS.json`

No other file may be modified. Additional files require a supervisor-approved packet revision.

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
git worktree add "../dopemux-mvp-wt-TP-LTAIP-H0-001" -b "research/TP-LTAIP-H0-001-segment-workflow-lock" origin/main
cd "../dopemux-mvp-wt-TP-LTAIP-H0-001"

test -f .dopetaskroot
test -s .repo_id
git remote get-url origin | grep -Eq 'DDD-Enterprises/dopemux-mvp(\.git)?$'
test "$(git branch --show-current)" = "research/TP-LTAIP-H0-001-segment-workflow-lock"
test -z "$(git status --porcelain)"

git status --short
git rev-parse HEAD
git remote get-url origin
```

Immediately capture the initial status and SHA in `proof/leantime-ai-parity/TP-LTAIP-H0-001/`.

## Commit-slice plan

### Slice 1: Protocol and schemas

Create the research protocol, consent rules, interview guide, opaque participant register, and empty evidence ledger.

Validation:

```bash
python -m json.tool reports/leantime-ai-parity/h0/segment-lock/participant-register.redacted.json >/dev/null
python -c 'import json; [json.loads(line) for line in open("reports/leantime-ai-parity/h0/segment-lock/session-evidence.jsonl") if line.strip()]'
python scripts/docs_validator.py   docs/06-research/leantime-ai-parity/h0/segment-lock/research-protocol.md   docs/06-research/leantime-ai-parity/h0/segment-lock/recruitment-and-consent.md   docs/06-research/leantime-ai-parity/h0/segment-lock/interview-guide.md
git diff --check
```

Exit only when the protocol is pre-registered before scoring evidence.

### Slice 2: Evidence ingestion and ranking

Ingest consented summaries, not raw transcripts. Keep buyer and user rankings separate. Preserve dissent.

Validation:

```bash
python -m json.tool reports/leantime-ai-parity/h0/segment-lock/participant-register.redacted.json >/dev/null
python -c 'import json; [json.loads(line) for line in open("reports/leantime-ai-parity/h0/segment-lock/session-evidence.jsonl") if line.strip()]'
test -s reports/leantime-ai-parity/h0/segment-lock/criteria-ranking.csv
git diff --check
```

Stop if the minimum evidence gate is not met.

### Slice 3: Decision and fixtures

Create the exact buyer/persona/workflow lock, fixture specification, ADR, dissent register, and content-addressed manifest.

Validation:

```bash
python -m json.tool reports/leantime-ai-parity/h0/segment-lock/segment-workflow-lock.json >/dev/null
python -m json.tool reports/leantime-ai-parity/h0/segment-lock/manifest.json >/dev/null
python scripts/docs_validator.py   docs/06-research/leantime-ai-parity/h0/segment-lock/workflow-fixture-spec.md   docs/06-research/leantime-ai-parity/h0/segment-lock/segment-workflow-lock.md   docs/06-research/leantime-ai-parity/h0/segment-lock/assumptions-and-dissent.md   docs/90-adr/adr-ltaip-h0-001-segment-workflow-lock.md
git diff --check
```

### Slice 4: Independent audit, proof, and PR

Run the embedded audit and resolve every blocking finding. Then run final validation, commit, push, open the PR, and run PR Steward.

## Required PAL chain

`analyze -> thinkdeep -> challenge -> planner -> challenge -> implement -> codereview -> precommit -> challenge`

Use `consensus` only if two defensible segment locks remain after evidence scoring. Use `secaudit` if any sensitive-data handling concern appears.


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


## Validation gates

### Understanding gate

Pass when the implementer can name:

- the economic-buyer hypothesis;
- provisional personas;
- candidate-neutral workflow taxonomy;
- privacy and redaction boundary;
- evidence threshold and reversal rule.

Minimum confidence: `HIGH`.

### Plan gate

Pass when the protocol is pre-registered before evidence scoring and every artifact has an exact path and validator.

### Evidence gate

Pass only when the proposed minimum evidence gate is met. Internal opinion is not evidence.

### Diff gate

Pass when docs, JSON, CSV, manifest, proof, and indexes agree and the diff stays inside the allowlist.

### Final gate

Pass only when all commands in `commit.verify` pass, embedded audit is non-blocking, and PR Steward is `READY`.

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


## Final evidence capture

```bash
set -euo pipefail

git status --short | tee "proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_STATUS_AFTER.txt"
git diff --stat | tee "proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_DIFF_STAT.txt"
git diff | tee "proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_DIFF.patch"
git diff --check

python scripts/audit/validate_audit_proof.py   "proof/leantime-ai-parity/TP-LTAIP-H0-001/PROOF.json"

pre-commit run --all-files | tee   "proof/leantime-ai-parity/TP-LTAIP-H0-001/PRECOMMIT.txt"

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

- Before merge: close the PR and remove the dedicated worktree and branch.
- After merge but before Packet 002: revert the packet commit and mark the lock superseded.
- Participant withdrawal: remove or supersede the participant's redacted evidence, recompute rankings, and invalidate the lock if thresholds no longer pass.
- Never delete historical decision evidence silently. Use a superseding record.

## Stop conditions

Stop immediately when:

- repo or worktree identity fails;
- the worktree is dirty before execution;
- raw personal data is found in the diff;
- participant evidence is insufficient;
- exactly one buyer, two personas, and three workflows cannot be defended;
- the fixture favors a specific product;
- the auditor returns `FAIL` or `NEEDS_SUPERVISOR`;
- the diff escapes the allowlist;
- proof or PR Steward output is stale.

## Required final return

Return:

1. objective status;
2. selected buyer, personas, and workflows;
3. evidence counts and dissent;
4. exact files changed;
5. commands and exit codes;
6. git status before and after;
7. diff stat and full diff;
8. embedded audit record;
9. proof hash;
10. PR URL and latest head SHA;
11. PR Steward `MERGE_READINESS.json`;
12. residual risks and next evidence needed.
