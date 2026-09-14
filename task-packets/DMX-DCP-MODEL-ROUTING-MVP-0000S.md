# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000S` · DCP · Series, Numbering, Lineage, and Authority Reconciliation

## Packet metadata

```text
packet_id: DMX-DCP-MODEL-ROUTING-MVP-0000S
project: dopemux-mvp
repo: DDD-Enterprises/dopemux-mvp
series: DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001
parent_packet: DMX-DCP-MODEL-ROUTING-MVP-0000R
base_branch: main
observed_main_sha_at_authoring: eb212dcaa73c407c271e0ddc60e38bdd2b7e4661
execution_branch: dcp/model-routing-0000s-series-reconcile
status: PLAN_ONLY
risk: MEDIUM
task_class: architecture-sensitive / documentation-sensitive
primary_executor: Claude Code Sonnet
embedded_auditor: Claude Code Opus / Claude Opus
final_supervisor: GPT-5.5 Pro
merge_authority: NONE
```

## Objective

Create the canonical current-main map of DCP routing packets, merged implementations, closed duplicates, superseded branches, active blockers, and the next collision-free packet sequence.

## Why this packet exists now

The routing program used overlapping numbering and multiple carve/repair PRs. The next implementation tranche must not rely on PR titles or stale packet intent when current runtime code has moved further.

## Governing truth order

Use this order when evidence conflicts:

1. Runtime code, config, Compose wiring, tests, active entrypoints, and current GitHub state
2. `TRUTH_*.md` artifacts
3. `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, and `SERVICE_CATALOG.md`
4. `SYSTEM_*.md`
5. Task-packet, PAL, proof, handoff, and agent contracts
6. Current vendor documentation
7. Inference

Every material statement must be labelled `OBSERVED`, `INFERRED`, `PROPOSED`, `UNKNOWN`, `CONFLICTING`, or `CLAIMED`.

Do not promote dopecon-bridge, retrieval output, mirrors, wrappers, agents, or model output into canonical authority.


## System-boundary invariants

- `dopemux` owns operator CLI/startup/routing/MCP coordination.
- `dopetask` remains the external execution runtime reached through `scripts/dopetask`.
- task-orchestrator owns workflow-significant transitions and views.
- Leantime owns passive PM metadata and ticket/project snapshots.
- ConPort owns structured decisions, progress, context, and custom data.
- dope-memory owns chronicle and evidence-preserving historical receipts.
- dope-context owns code/docs indexing and retrieval.
- dopecon-bridge is an adapter/proxy/event transport only.
- ADHD Engine owns operator-support and cognitive-state surfaces only.
- Repo Truth Extractor owns extraction/audit artifacts about the repository.
- DCP routing outputs are decisions and policy data, not execution authority.


## Scope IN

- Enumerate current routing-related task packets and proof bundles.
- Map packet IDs to code, tests, merged PRs, closed duplicates, and current status.
- Record #851/#862 merged lineage and #854 closed-unmerged disposition.
- Reconcile 0001 through 0007 design/implementation status.
- Define the authoritative next-tranche dependency graph.
- Produce a machine-readable supersession and collision map.

## Scope OUT

- No runtime code or config changes.
- No packet deletion.
- No historical proof rewriting.
- No PR state changes.
- No interpretation of closed-unmerged branches as main truth.

## Invariants

- Current code and merged main history outrank packet titles.
- Closed-unmerged PRs remain historical context only.
- Duplicate packet numbers are preserved and explicitly reconciled.
- Design completion and implementation completion are separate.
- 0007 trusted-input design is complete; capability implementation remains absent until proven.
- Future packet IDs must be collision-free in current main and open PRs.

## Files allowed to change

```text
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000S.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0000S/**
docs/03-reference/dcp/model-routing-series-status.md
docs/03-reference/dcp/model-routing-series-map.json
```

## Files forbidden

```text
.github/**
src/**
services/**
docker/**
compose.yml
opencode.jsonc
mcp_catalog.yaml
config/**
scripts/**
```

## Mandatory preflight

Execute from a clean dedicated worktree. Do not use the primary checkout unless the packet explicitly authorizes it.

```bash
set -euo pipefail

git fetch origin --prune
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

test -f RULES.md
test "$(git remote get-url origin)" = "git@github.com:DDD-Enterprises/dopemux-mvp.git"   || test "$(git remote get-url origin)" = "https://github.com/DDD-Enterprises/dopemux-mvp.git"

git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
```

Stop if:

- repository identity does not match
- the worktree is dirty before packet-owned changes
- the branch is not the packet branch
- the packet base is not an ancestor of the branch
- unrelated changes are present


## PAL execution chain

Use the repository PAL doctrine. Tool output is evidence input, not proof.

Required chain:

```text
analyze
→ thinkdeep
→ challenge
→ planner
→ challenge
→ execute in commit-sized slices
→ codereview
→ precommit
→ final challenge
```

Escalate with:

- `tracer` for call-flow ambiguity
- `debug` for reproducible runtime contradictions
- `testgen` for uncovered regression surfaces
- `secaudit` for authority, secrets, process execution, network, or live-write risk
- `apilookup` for current external CLI/API semantics
- `consensus` only when at least two credible approaches remain

Every PAL stage artifact must record:

```text
stage
tool
model
invocation
exit_code if available
summary
evidence_ledger
assumptions
risks
confidence
verdict
next_action
```

Final completion confidence must be `VERIFIED`.


## Execution plan

1. Read the 0000R reconciliation.
2. Inventory current task-packet and proof paths.
3. Inventory current DCP source modules and tests.
4. Harvest merged/closed/open PR metadata for the routing program.
5. Build a packet-to-runtime matrix.
6. Mark duplicates, supersessions, gaps, and exact next dependencies.
7. Challenge the map against current main.
8. Publish the canonical status document and JSON map.

## Exact commands

```bash
git worktree add "../dopemux-0000s" -b dcp/model-routing-0000s-series-reconcile origin/main
cd "../dopemux-0000s"

find task-packets -type f -iname '*MODEL-ROUTING*' -print | sort   > /tmp/model-routing-packets.txt

find proof -maxdepth 3 -type f -path '*MODEL-ROUTING*' -print | sort   > /tmp/model-routing-proof.txt || true

find src/dopemux/dcp tests/unit/dcp tests/dcp -type f -print | sort   > /tmp/model-routing-runtime-files.txt

gh pr list --repo DDD-Enterprises/dopemux-mvp   --state all --limit 300   --json number,title,state,isDraft,mergedAt,closedAt,headRefName,baseRefName,headRefOid,url   > /tmp/model-routing-prs.json

python -m json.tool /tmp/model-routing-prs.json >/dev/null
```

## Validation gates

- Every packet ID found in the repo appears in the map.
- Every active DCP source module is mapped to at least one landed packet or marked `UNMAPPED`.
- Every duplicate or closed-unmerged lineage is explicit.
- #854 is not listed as merged authority.
- #862 is listed as the clean 0001 lineage.
- The next sequence has no collision with current task-packet IDs or open PR titles.
- JSON parses and the diff matches the allowlist.

## Proof bundle minimum

Create:

```text
proof/<PACKET_ID>/
  PROOF.json
  COMMAND_LOG.md
  EVIDENCE_LEDGER.md
  PAL_CHAIN.md
  AUDITOR_REPORT.md
  FINAL_STATUS_PORCELAIN.txt
  DIFF_NAME_ONLY.txt
  DIFF_STAT.txt
  HANDOFF.json
  HANDOFF.md
```

`PROOF.json` must include the canonical proof-bundle fields:

- `bundle_id`
- `run_id`
- `skill`
- `status`
- `validation_state`
- `created_at`
- `authoritative_artifacts`
- `supporting_artifacts`
- `handoff_refs`
- `parent_bundle_refs`
- `review_order_hint`
- `chain_of_custody`

Also include packet-specific:

- `packet_id`
- `repo`
- `branch`
- `base_sha`
- `subject_sha`
- `commands` with exit codes
- `embedded_audit`
- `remaining_risks`
- `merge_readiness`

Use:

```text
merge_readiness: BLOCKED_NOT_REQUESTED
```

until PR Steward inspects the latest PR head.


## Packet-specific proof requirements

Authoritative artifacts:

```text
MODEL_ROUTING_SERIES_MAP.json
MODEL_ROUTING_SERIES_STATUS.md
```

Each packet record must contain:

```text
packet_id
purpose
design_status
implementation_status
main_paths
tests
merged_prs
closed_unmerged_prs
supersedes
superseded_by
blockers
next_dependency
evidence_refs
```

The series map must identify the supervisor gate after `0009`.

## Embedded audit

```text
auditor_tool: Claude Code Opus
auditor_model: Claude Opus
auditor_verdict: PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR
```

The implementer may not act as the sole auditor. If the independent auditor is unavailable, record `SKIPPED` with the exact reason and return `NEEDS_SUPERVISOR`.

## Documentation

```text
docs_in_scope: Yes
```

Documentation must be checked against the final implementation, current paths, commands, failure modes, and non-claims.

## Commit, PR, and PR Steward

Before commit:

```bash
git diff --check
git diff --name-only
git diff --stat
git status --porcelain=v1
```

Run a diff allowlist check. Stop on any undeclared file.

After validation:

```bash
git add <packet allowlist>
git diff --cached --name-only
git diff --cached --stat
git commit -m "<packet commit message>"
git push -u origin <packet branch>
```

Open a draft PR. Do not merge.

PR Steward must harvest:

- PR metadata
- changed files
- commits and exact head SHA
- reviews
- review comments and threads
- issue comments
- bots
- checks and CI state
- embedded-audit artifact
- proof freshness

Unknown reviewers, unknown bots, unclassified items, stale proof, unresolved blocking threads, or failed checks block `READY`.


## Rollback

```bash
git restore --staged .
git restore .
rm -rf proof/DMX-DCP-MODEL-ROUTING-MVP-0000S
git worktree remove "../dopemux-0000s" --force
git branch -D dcp/model-routing-0000s-series-reconcile
```

## Stop conditions

- GitHub history cannot be retrieved.
- Current packet IDs conflict in a way that cannot be represented without silently choosing a winner.
- The 0000R reconciliation is missing or stale to a different main SHA.
- Runtime files exist with no discoverable packet/provenance and require supervisor classification.

## Expected output

```text
status: READY_FOR_REVIEW
canonical_next_sequence:
  - 0007I
  - 0007T
  - 0007A
  - 0008
  - 0009
supervisor_gate_after: 0009
merge_readiness: BLOCKED_NOT_REQUESTED
```

## Completion rule

Do not claim completion unless:

- every required validation has an exit code
- the diff matches the allowlist
- the embedded audit is current to the subject SHA
- the evidence ledger is complete
- the handoff preserves warnings and blockers
- final confidence is `VERIFIED`

This packet does not authorize merge or live execution.
