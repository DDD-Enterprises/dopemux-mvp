---
id: DMX-DCP-MODEL-ROUTING-MVP-0007T
title: Dmx Dcp Model Routing Mvp 0007T
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-24'
last_review: '2026-08-24'
next_review: '2026-11-22'
prelude: Dmx Dcp Model Routing Mvp 0007T (explanation) for dopemux documentation and developer workflows.
---
# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0007T` · DCP · Trusted Input Adversarial and Regression Test Corpus

## Packet metadata

```text
packet_id: DMX-DCP-MODEL-ROUTING-MVP-0007T
project: dopemux-mvp
repo: DDD-Enterprises/dopemux-mvp
series: DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001
parent_packet: DMX-DCP-MODEL-ROUTING-MVP-0007I
base_branch: main
observed_main_sha_at_authoring: eb212dcaa73c407c271e0ddc60e38bdd2b7e4661
execution_branch: dcp/model-routing-0007t-adversarial-tests
status: PLAN_ONLY
risk: HIGH
task_class: security-sensitive / test hardening
primary_executor: Claude Code Sonnet
embedded_auditor: Claude Code Opus + secaudit / Claude Opus
final_supervisor: GPT-5.5 Pro
merge_authority: NONE
```

## Objective

Build an adversarial test corpus that demonstrates raw, serialized, restored, malformed, and caller-controlled inputs cannot forge trusted execution eligibility.

## Why this packet exists now

A capability boundary is only credible when hostile construction and restoration paths are tested independently of the initial implementation packet.

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

- Add adversarial tests and fixtures for the 0007I public surface.
- Test dict/JSON injection, unknown fields, dataclass replacement, copy, pickle, subclassing, constructor misuse, and unregistered adapter IDs where applicable.
- Test that classification remains available for untrusted input while execution eligibility remains false.
- Permit minimal fixes to `input_adapters.py` only when an adversarial test exposes a real defect.

## Scope OUT

- No new trusted adapters.
- No registry population.
- No runner or CLI implementation.
- No expansion of packet 0007I public API without supervisor justification.
- No unrelated DCP refactor.

## Invariants

- Tests must attack actual supported construction paths, not theatrical impossible paths.
- Every test names the threat and expected fail-closed outcome.
- Tests do not mutate global process state or require network.
- Any implementation fix remains within 0007I's authority boundary.
- Full DCP behavior remains compatible.

## Files allowed to change

```text
tests/unit/dcp/test_input_adapters_adversarial.py
tests/fixtures/dcp/trusted_input/**
src/dopemux/dcp/input_adapters.py
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0007T.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0007T/**
```

## Files forbidden

```text
.github/**
src/dopemux/commands/**
src/dopemux/cli.py
src/dopemux/dcp/routing_model.py
src/dopemux/dcp/routing_classifier.py
src/dopemux/dcp/routing_backend_policy.py
src/dopemux/dcp/lane_engine.py
services/**
docker/**
compose.yml
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

1. Read 0007I implementation and proof.
2. Build a threat model limited to actual Python/public-API attack surfaces.
3. Use testgen to propose cases; challenge and remove theatrical cases.
4. Write failing adversarial tests.
5. Apply only minimal capability-boundary fixes.
6. Run focused, full DCP, and serialization/static scans.
7. Run independent security audit.
8. Emit a machine-readable threat/test matrix.

## Exact commands

```bash
git worktree add "../dopemux-0007t" -b dcp/model-routing-0007t-adversarial-tests origin/main
cd "../dopemux-0007t"

test -f src/dopemux/dcp/input_adapters.py
python -m pytest -q tests/unit/dcp/test_input_adapters.py

python -m pytest -q tests/unit/dcp/test_input_adapters_adversarial.py
python -m pytest -q tests/unit/dcp
python -m pytest -q tests/dcp/test_dcp_model_routing_0001_domain.py

ruff check   src/dopemux/dcp/input_adapters.py   tests/unit/dcp/test_input_adapters_adversarial.py

python -m compileall -q src/dopemux/dcp tests/unit/dcp
git diff --check
```

## Validation gates

At minimum, test:

- JSON/dict `attested=true` injection
- fake `adapter_id`
- raw `RoutingClassificationInput`
- restored `RouteDecision`
- constructor misuse
- `copy.copy` and `copy.deepcopy`
- pickle or explicit serialization attempt
- dataclass replacement where applicable
- subclassing or proxy-object misuse where applicable
- malformed provenance metadata
- unknown adapter
- stale/missing evidence
- mutation of frozen evidence
- regression: read-only classification still works

Every bypass test must fail closed.

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

Required artifacts:

```text
ADVERSARIAL_THREAT_MATRIX.json
ADVERSARIAL_TEST_REPORT.md
FIXES_APPLIED_FROM_TESTS.md
```

For each case record:

```text
threat_id
construction_path
attacker_control
expected_result
observed_result
test_name
status
fix_commit if applicable
```

`auditor_verdict` must be independent from test `validation_state`.

## Embedded audit

```text
auditor_tool: Claude Code Opus + secaudit
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
git restore src/dopemux/dcp/input_adapters.py 2>/dev/null || true
rm -f tests/unit/dcp/test_input_adapters_adversarial.py
rm -rf tests/fixtures/dcp/trusted_input
rm -rf proof/DMX-DCP-MODEL-ROUTING-MVP-0007T
```

## Stop conditions

- A bypass remains reproducible.
- A proposed test requires enabling runtime execution.
- The fix requires changing classifier/lane semantics outside the capability boundary.
- Full DCP regressions appear.
- Independent auditor returns `FAIL` or `NEEDS_SUPERVISOR`.

## Expected output

```text
status: IMPLEMENTATION_COMPLETE
validation_state: PASSED
adversarial_bypasses_open: 0
next_packet: DMX-DCP-MODEL-ROUTING-MVP-0007A
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
