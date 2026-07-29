# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0007I` · DCP · Trusted Input Capability Implementation

## Packet metadata

```text
packet_id: DMX-DCP-MODEL-ROUTING-MVP-0007I
project: dopemux-mvp
repo: DDD-Enterprises/dopemux-mvp
series: DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001
parent_packet: DMX-DCP-MODEL-ROUTING-MVP-0000S
base_branch: main
observed_main_sha_at_authoring: eb212dcaa73c407c271e0ddc60e38bdd2b7e4661
execution_branch: dcp/model-routing-0007i-trusted-input
status: PLAN_ONLY
risk: HIGH
task_class: architecture-sensitive / security-sensitive
primary_executor: Claude Code Sonnet
embedded_auditor: Claude Code Opus + secaudit / Claude Opus
final_supervisor: GPT-5.5 Pro
merge_authority: NONE
```

## Objective

Implement a non-serializable, fail-closed trusted-input capability boundary so raw or restored routing inputs cannot confer mutation eligibility.

## Why this packet exists now

The merged 0007 design requires execution eligibility to be minted in-process by a trusted adapter. Current main has provenance flags but no `input_adapters.py` capability implementation. No runner execution should be introduced before this gap closes.

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

- Add the trusted-input capability model.
- Add a pure, auditable execution-eligibility gate.
- Make raw `RoutingClassificationInput`, dict, JSON, and restored values non-eligible by default.
- Add focused tests for capability construction, immutability, serialization refusal, and fail-closed behavior.
- Export only the minimal public API.
- Update the 0007 task-packet implementation note and proof.

## Scope OUT

- No real trusted adapter is enabled.
- No generic `attested=true` field.
- No caller-supplied adapter ID may raise trust.
- No subprocess, network, runner, connector, MCP, GitHub, Dopetask, or Task Orchestrator calls.
- No CLI execution command.
- No lane-engine widening.
- No persistence of live capabilities.

## Invariants

- The capability is not reconstructible from JSON or a public boolean.
- Raw input remains safe for classification but cannot become execution-eligible.
- Restored/pickled capability objects must not silently remain authoritative.
- Trust can only be minted through a private/internal constructor controlled by registered adapter code.
- No adapter is active until 0007A supplies an explicit registry and evidence.
- Existing classify/recommend/lane behavior remains regression-compatible.
- Python privacy is not overstated as cryptographic security; the boundary is auditable code authority.

## Files allowed to change

```text
src/dopemux/dcp/input_adapters.py
src/dopemux/dcp/__init__.py
tests/unit/dcp/test_input_adapters.py
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0007I.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/**
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

1. Inspect current 0007 design, routing types, classifier, lane engine, and tests.
2. Trace every current construction path for `RoutingClassificationInput`.
3. Design the smallest capability object and public gate.
4. Challenge the design for JSON, dataclass, copy, pickle, subclass, and direct-constructor bypasses.
5. Write failing tests.
6. Implement the capability without enabling any adapter.
7. Run the focused and full DCP suites.
8. Run a security audit and diff review.
9. Emit proof with explicit non-claims.

## Exact commands

```bash
git worktree add "../dopemux-0007i" -b dcp/model-routing-0007i-trusted-input origin/main
cd "../dopemux-0007i"

grep -RIn --exclude-dir=.git   -E 'RoutingClassificationInput\(|_input_from_dict|decide_lane\(|is_executable|AttestedInput|input_adapters'   src tests task-packets

python -m pytest -q tests/unit/dcp
python -m compileall -q src/dopemux/dcp

# After RED tests are authored:
python -m pytest -q tests/unit/dcp/test_input_adapters.py

# After implementation:
python -m pytest -q tests/unit/dcp/test_input_adapters.py
python -m pytest -q tests/unit/dcp
python -m pytest -q tests/dcp/test_dcp_model_routing_0001_domain.py
python -m compileall -q src/dopemux/dcp
ruff check   src/dopemux/dcp/input_adapters.py   src/dopemux/dcp/__init__.py   tests/unit/dcp/test_input_adapters.py
git diff --check
```

## Validation gates

- Focused tests prove raw input is never execution-eligible.
- A serialized `attested`, `trusted`, `adapter_id`, or equivalent field cannot mint capability.
- Direct public construction is rejected or impossible through the supported API.
- Copy/pickle/restore behavior fails closed.
- The capability and evidence metadata are immutable.
- No active trusted adapter exists.
- Full DCP tests pass.
- Static scan finds no I/O, shell, network, connector, MCP, or runner imports.
- Independent security audit returns no blocking finding.

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

Required authoritative artifacts:

```text
TRUSTED_INPUT_DESIGN.md
TRUSTED_INPUT_TEST_MATRIX.json
SECURITY_BOUNDARY_REVIEW.md
```

`PROOF.json` must explicitly record:

```text
active_trusted_adapters: []
serialized_trust_supported: false
raw_input_execution_eligible: false
runtime_execution_added: false
```

Do not claim that Python module privacy is cryptographic isolation.

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
git restore   src/dopemux/dcp/__init__.py   2>/dev/null || true
rm -f src/dopemux/dcp/input_adapters.py
rm -f tests/unit/dcp/test_input_adapters.py
rm -rf proof/DMX-DCP-MODEL-ROUTING-MVP-0007I
```

## Stop conditions

- The capability requires a serializable trust flag.
- Existing lane or classifier behavior must be weakened.
- A real adapter must be enabled to make tests pass.
- Public construction cannot be made fail-closed without invasive unrelated changes.
- The security auditor reports `FAIL` or `NEEDS_SUPERVISOR`.
- Any executor or live-write path appears in the diff.

## Expected output

```text
status: IMPLEMENTATION_COMPLETE
validation_state: PASSED
active_trusted_adapters: 0
execution_surface_added: false
next_packet: DMX-DCP-MODEL-ROUTING-MVP-0007T
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
