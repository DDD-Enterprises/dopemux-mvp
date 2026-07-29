# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0007A` · DCP · Trusted Adapter Registry and Derivation Policy

## Packet metadata

```text
packet_id: DMX-DCP-MODEL-ROUTING-MVP-0007A
project: dopemux-mvp
repo: DDD-Enterprises/dopemux-mvp
series: DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001
parent_packet: DMX-DCP-MODEL-ROUTING-MVP-0007T
base_branch: main
observed_main_sha_at_authoring: eb212dcaa73c407c271e0ddc60e38bdd2b7e4661
execution_branch: dcp/model-routing-0007a-adapter-registry
status: PLAN_ONLY
risk: HIGH
task_class: architecture-sensitive / security-sensitive / schema
primary_executor: Claude Code Sonnet
embedded_auditor: Claude Code Opus + secaudit / Claude Opus
final_supervisor: GPT-5.5 Pro
merge_authority: NONE
```

## Objective

Define a strict, fail-closed trusted-adapter registry and derivation policy without enabling any adapter for mutating execution.

## Why this packet exists now

The capability implementation needs an explicit registry boundary before future adapters can mint trust. Current agent and adapter authority is not globally proven, so the initial registry must be conservative.

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

- Add registry schema and config.
- Add pure registry model/validation code.
- Represent candidate adapters and evidence requirements.
- Default all mutation eligibility to disabled.
- Add tests for unknown adapters, malformed config, trust-raising fields, duplicates, and disabled entries.
- Connect 0007I minting to a validated in-memory registry object without file I/O in core.

## Scope OUT

- No adapter becomes mutation-enabled.
- No filesystem/config loader inside pure DCP core.
- No operator, agent, bridge, retrieval, MCP, GitHub, or runner identity is trusted by name alone.
- No live proof lookup.
- No execution or connector wiring.

## Invariants

- Registry entries can only constrain or deny trust.
- Unknown, missing, duplicate, stale, disabled, or malformed entries fail closed.
- Bridge/proxy and retrieval-derived sources cannot be mutation-authoritative.
- Agent identity alone is insufficient.
- The initial checked-in registry has zero mutation-enabled adapters.
- File loading remains outside pure decision logic.
- Registry data is schema-validated and deterministic.

## Files allowed to change

```text
schemas/dcp/trusted_input_adapter_registry.schema.json
config/dcp/trusted_input_adapters.json
src/dopemux/dcp/trusted_adapter_registry.py
src/dopemux/dcp/input_adapters.py
src/dopemux/dcp/__init__.py
tests/unit/dcp/test_trusted_adapter_registry.py
tests/unit/dcp/test_input_adapters.py
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0007A.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/**
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
mcp_catalog.yaml
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

1. Read source-authority and system-boundary docs.
2. Define registry schema with conservative enums and evidence requirements.
3. Challenge whether any current adapter is actually eligible.
4. Check in a registry with zero mutation-enabled entries.
5. Implement pure registry model validation.
6. Integrate capability minting with a validated registry object.
7. Add schema, model, and integration tests.
8. Run security audit and prove zero active adapters.

## Exact commands

```bash
git worktree add "../dopemux-0007a" -b dcp/model-routing-0007a-adapter-registry origin/main
cd "../dopemux-0007a"

python -m json.tool config/dcp/trusted_input_adapters.json
python - <<'PY'
import json
from jsonschema import Draft7Validator

schema = json.load(open("schemas/dcp/trusted_input_adapter_registry.schema.json"))
data = json.load(open("config/dcp/trusted_input_adapters.json"))
Draft7Validator.check_schema(schema)
errors = sorted(Draft7Validator(schema).iter_errors(data), key=lambda e: list(e.path))
if errors:
    for error in errors:
        print(error.message)
    raise SystemExit(1)
PY

python -m pytest -q   tests/unit/dcp/test_trusted_adapter_registry.py   tests/unit/dcp/test_input_adapters.py   tests/unit/dcp/test_input_adapters_adversarial.py

python -m pytest -q tests/unit/dcp
ruff check   src/dopemux/dcp/trusted_adapter_registry.py   src/dopemux/dcp/input_adapters.py   tests/unit/dcp/test_trusted_adapter_registry.py
python -m compileall -q src/dopemux/dcp
git diff --check
```

## Validation gates

- JSON Schema is Draft 7 valid.
- Checked-in config validates.
- Active mutation-enabled adapter count equals zero.
- Unknown/disabled/stale/malformed adapters cannot mint capability.
- Bridge/proxy and retrieval-derived candidates cannot be marked canonical.
- Registry order does not change decisions.
- Pure core performs no filesystem I/O.
- Full DCP tests pass.
- Independent security audit passes or returns only explicit non-blocking risks.

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
TRUSTED_ADAPTER_REGISTRY_REVIEW.md
REGISTRY_VALIDATION.json
AUTHORITY_DISPOSITION_MATRIX.json
```

Each candidate must record:

```text
adapter_id
authority_slice
canonical_writer
source_type
status
mutation_eligible
required_evidence
forbidden_capabilities
reason
evidence_refs
```

Initial invariant:

```text
mutation_enabled_adapter_count: 0
```

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
git restore src/dopemux/dcp/input_adapters.py src/dopemux/dcp/__init__.py 2>/dev/null || true
rm -f src/dopemux/dcp/trusted_adapter_registry.py
rm -f schemas/dcp/trusted_input_adapter_registry.schema.json
rm -f config/dcp/trusted_input_adapters.json
rm -f tests/unit/dcp/test_trusted_adapter_registry.py
rm -rf proof/DMX-DCP-MODEL-ROUTING-MVP-0007A
```

## Stop conditions

- Any adapter must be enabled based only on product name, branch name, agent identity, or documentation.
- A bridge/proxy is proposed as canonical authority.
- Registry loading requires impurity inside routing decision functions.
- Unknown or malformed entries do not fail closed.
- Mutation-enabled adapter count is nonzero without separate supervisor authorization.

## Expected output

```text
status: IMPLEMENTATION_COMPLETE
validation_state: PASSED
mutation_enabled_adapter_count: 0
next_packet: DMX-DCP-MODEL-ROUTING-MVP-0008
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
