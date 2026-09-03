# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0008` · DCP · Backend Runner Interface and Proof Contract

## Packet metadata

```text
packet_id: DMX-DCP-MODEL-ROUTING-MVP-0008
project: dopemux-mvp
repo: DDD-Enterprises/dopemux-mvp
series: DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001
parent_packet: DMX-DCP-MODEL-ROUTING-MVP-0007A
base_branch: main
observed_main_sha_at_authoring: eb212dcaa73c407c271e0ddc60e38bdd2b7e4661
execution_branch: dcp/model-routing-0008-runner-contract
status: PLAN_ONLY
risk: HIGH
task_class: architecture-sensitive / interface contract
primary_executor: Claude Code Sonnet
embedded_auditor: Claude Code Opus + secaudit / Claude Opus
final_supervisor: GPT-5.5 Pro
merge_authority: NONE
```

## Objective

Define a pure backend-runner interface, invocation-plan model, result model, and proof envelope without implementing any subprocess, network, or model execution.

## Why this packet exists now

The routing plane needs one canonical contract before concrete Codex, Claude Code, OpenCode, Gemini, AGY, or Grok adapters can be written. Backend policy recommendations are currently inert and should remain so.

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

- Add immutable runner request, plan, result, capability, and proof-reference models.
- Add a `RunnerAdapter` protocol or equivalent interface.
- Require an in-memory trusted capability for any future mutation-capable plan.
- Make serialized/restored plans non-executable.
- Represent dry-run, read-only, audit, and bounded implementation modes.
- Add deterministic validation and serialization tests.
- Document explicit non-claims.

## Scope OUT

- No concrete runner adapter.
- No subprocess, shell, network, SDK, MCP, model, Docker, or external-service calls.
- No runner discovery.
- No environment-variable or credential handling.
- No automatic backend selection.
- No GitHub, Dopetask, Task Orchestrator, ConPort, dope-memory, or live writes.

## Invariants

- Interface data cannot authorize execution by itself.
- Backend recommendation remains advisory.
- Any mutation-capable plan requires an in-memory trusted capability.
- Serialized/restored requests lose execution eligibility.
- Allowed files, commands, network, secrets, and side effects are explicit fields.
- Unknown backend/mode/capability fails closed.
- Results distinguish process exit, validation, proof, and auditor verdict.
- Proof pointers preserve existing proof-family distinctions.

## Files allowed to change

```text
src/dopemux/dcp/runner_contract.py
src/dopemux/dcp/__init__.py
tests/unit/dcp/test_runner_contract.py
schemas/dcp/runner_contract.schema.json
docs/03-reference/dcp/backend-runner-contract.md
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0008.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0008/**
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

1. Read 0007 capability/registry and current backend policy.
2. Trace all current backend and lane data types.
3. Define interface modes and fail-closed invariants.
4. Challenge serialization, restoration, action widening, and proof flattening.
5. Write failing contract tests.
6. Implement immutable pure models and protocol.
7. Add JSON schema for persisted non-authoritative receipts.
8. Run full DCP regression and independent architecture/security audit.

## Exact commands

```bash
git worktree add "../dopemux-0008" -b dcp/model-routing-0008-runner-contract origin/main
cd "../dopemux-0008"

grep -RIn --exclude-dir=.git   -E 'BackendKind|BackendPolicyDecision|LaneDecision|AttestedInput|Runner'   src/dopemux/dcp tests/unit/dcp

python -m pytest -q tests/unit/dcp/test_runner_contract.py
python -m pytest -q tests/unit/dcp
python -m pytest -q tests/dcp/test_dcp_model_routing_0001_domain.py

python -m json.tool schemas/dcp/runner_contract.schema.json
ruff check   src/dopemux/dcp/runner_contract.py   tests/unit/dcp/test_runner_contract.py
python -m compileall -q src/dopemux/dcp
git diff --check

grep -RIn -E   'subprocess|os\.system|Popen|requests|httpx|socket|mcp|docker|github|dopetask|task.orchestrator'   src/dopemux/dcp/runner_contract.py && exit 1 || true
```

## Validation gates

- Models and schema are deterministic and strict.
- Mutation-capable plans cannot be created from serialized data alone.
- Unknown runner/mode/status fails closed.
- Allowed actions and paths cannot widen from route/lane decisions.
- No I/O or runner invocation exists.
- Audit verdict and validation state are separate.
- Proof references are additive and typed.
- Full DCP test suite passes.
- Independent audit confirms no execution path.

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
RUNNER_CONTRACT_MATRIX.json
SERIALIZATION_AND_RESTORE_REVIEW.md
NO_EXECUTION_STATIC_SCAN.txt
```

Required contract concepts:

```text
RunnerMode
RunnerIdentity
RunnerCapabilitySnapshot
RunnerInvocationPlan
RunnerResult
RunnerProofReference
RunnerAdapter Protocol
```

Use different names only with explicit audit-backed rationale.

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
git restore src/dopemux/dcp/__init__.py 2>/dev/null || true
rm -f src/dopemux/dcp/runner_contract.py
rm -f tests/unit/dcp/test_runner_contract.py
rm -f schemas/dcp/runner_contract.schema.json
rm -f docs/03-reference/dcp/backend-runner-contract.md
rm -rf proof/DMX-DCP-MODEL-ROUTING-MVP-0008
```

## Stop conditions

- The interface requires a concrete runner to validate.
- A serialized plan can authorize mutation.
- The design flattens proof and audit state.
- Any I/O, process, network, or credential code appears.
- Existing backend policy or lane safety must be weakened.
- Independent auditor finds an execution or authority leak.

## Expected output

```text
status: IMPLEMENTATION_COMPLETE
validation_state: PASSED
concrete_runner_adapters: 0
execution_calls: 0
next_packet: DMX-DCP-MODEL-ROUTING-MVP-0009
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
