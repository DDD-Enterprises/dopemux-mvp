# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0009` · DCP · Runner Capability Registry and Static Probe Matrix

## Packet metadata

```text
packet_id: DMX-DCP-MODEL-ROUTING-MVP-0009
project: dopemux-mvp
repo: DDD-Enterprises/dopemux-mvp
series: DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001
parent_packet: DMX-DCP-MODEL-ROUTING-MVP-0008
base_branch: main
observed_main_sha_at_authoring: eb212dcaa73c407c271e0ddc60e38bdd2b7e4661
execution_branch: dcp/model-routing-0009-runner-capabilities
status: PLAN_ONLY
risk: HIGH
task_class: runtime reconciliation / architecture-sensitive / security-sensitive
primary_executor: Claude Code Sonnet
embedded_auditor: Claude Code Opus + secaudit / Claude Opus
final_supervisor: GPT-5.5 Pro
merge_authority: NONE
```

## Objective

Create an evidence-backed, non-authoritative runner capability registry for installed Codex, Claude Code, OpenCode, Gemini CLI, AGY, Grok, and other observed backends, with every invocation permission disabled.

## Why this packet exists now

The runner contract needs observed capability data before any concrete adapter packet is authorized. Product names, local installation, and configuration presence do not prove safe execution support.

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

- Reuse the 0000R runner inventory.
- Add strict registry schema and checked-in capability records.
- Add pure model/validation code.
- Record installation, version, interface type, dry-run support, structured output, worktree support, audit suitability, network requirements, proof support, and evidence.
- Permit bounded static CLI help/version probes.
- Mark authentication and paid-call support `UNKNOWN` unless directly observed without exposing secrets.
- Keep all invocation authorization disabled.

## Scope OUT

- No model inference calls by default.
- No paid API calls.
- No runner adapter implementation.
- No subprocess execution from DCP core.
- No credentials or authentication state disclosure.
- No automatic routing to a runner.
- No mutation eligibility or live writes.

## Invariants

- Installed does not mean authorized.
- Configured does not mean authenticated.
- Authenticated does not mean safe for mutation.
- Capability data cannot authorize execution.
- Unknown fields fail closed.
- Evidence is exact-command and current-main bound.
- Every runner has `invocation_authorized: false`.
- Agent/model/provider identity claims remain separate.
- OpenCode remains backend-only.
- The registry is advisory input to later adapter packets.

## Files allowed to change

```text
schemas/dcp/runner_capability_registry.schema.json
config/dcp/runner_capabilities.json
src/dopemux/dcp/runner_capability_registry.py
src/dopemux/dcp/__init__.py
tests/unit/dcp/test_runner_capability_registry.py
docs/03-reference/dcp/runner-capability-matrix.md
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0009.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0009/**
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
opencode.jsonc
mcp_catalog.yaml
scripts/**
.env*
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

1. Read 0000R evidence and 0008 contract.
2. Define strict capability schema.
3. Probe only installed CLI version/help surfaces.
4. Record evidence and UNKNOWN values honestly.
5. Challenge provider/model/auth/capability conflation.
6. Check in registry with invocation disabled for all records.
7. Implement pure validation and lookup.
8. Add schema and fail-closed tests.
9. Run security and architecture audit.
10. Stop for GPT-5.5 supervisor gate after proof/PR Steward.

## Exact commands

```bash
git worktree add "../dopemux-0009" -b dcp/model-routing-0009-runner-capabilities origin/main
cd "../dopemux-0009"

mkdir -p proof/DMX-DCP-MODEL-ROUTING-MVP-0009/probes

for bin in codex claude opencode gemini agy grok; do
  {
    echo "binary=$bin"
    command -v "$bin" || true
    "$bin" --version 2>&1 || true
    "$bin" --help 2>&1 | head -n 160 || true
  } > "proof/DMX-DCP-MODEL-ROUTING-MVP-0009/probes/${bin}.txt"
done

python -m json.tool config/dcp/runner_capabilities.json
python - <<'PY'
import json
from jsonschema import Draft7Validator

schema = json.load(open("schemas/dcp/runner_capability_registry.schema.json"))
data = json.load(open("config/dcp/runner_capabilities.json"))
Draft7Validator.check_schema(schema)
errors = sorted(Draft7Validator(schema).iter_errors(data), key=lambda e: list(e.path))
if errors:
    for error in errors:
        print(error.message)
    raise SystemExit(1)

bad = [r["runner_id"] for r in data["runners"] if r.get("invocation_authorized") is not False]
if bad:
    raise SystemExit(f"authorized runners forbidden in 0009: {bad}")
PY

python -m pytest -q tests/unit/dcp/test_runner_capability_registry.py
python -m pytest -q tests/unit/dcp
ruff check   src/dopemux/dcp/runner_capability_registry.py   tests/unit/dcp/test_runner_capability_registry.py
python -m compileall -q src/dopemux/dcp
git diff --check
```

## Validation gates

- Registry schema and config validate.
- Every runner has `invocation_authorized: false`.
- No secret values are captured.
- Unknown CLI, version, authentication, provider, or capability remains UNKNOWN.
- Runner and model/provider identities are not conflated.
- Unknown runner lookup fails closed.
- Duplicate IDs and stale evidence fail validation.
- Full DCP tests pass.
- Independent security/architecture audit completes.
- PR Steward reviews exact head.
- Series returns to GPT-5.5 supervisor; no 0010 implementation begins automatically.

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
RUNNER_CAPABILITY_MATRIX.json
RUNNER_CAPABILITY_MATRIX.md
STATIC_PROBE_INVENTORY.json
SUPERVISOR_GATE_BRIEF.md
```

Each runner record must include:

```text
runner_id
tool_name
observed_binary
observed_version
interface_type
provider_identity
model_identity
installation_state
authentication_state
supports_readonly
supports_dry_run
supports_worktree
supports_structured_output
supports_embedded_audit
network_required
proof_contract_support
invocation_authorized
evidence_refs
observed_at
subject_sha
status
unknowns
```

Required global invariant:

```text
authorized_runner_count: 0
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
git restore src/dopemux/dcp/__init__.py 2>/dev/null || true
rm -f src/dopemux/dcp/runner_capability_registry.py
rm -f schemas/dcp/runner_capability_registry.schema.json
rm -f config/dcp/runner_capabilities.json
rm -f tests/unit/dcp/test_runner_capability_registry.py
rm -f docs/03-reference/dcp/runner-capability-matrix.md
rm -rf proof/DMX-DCP-MODEL-ROUTING-MVP-0009
```

## Stop conditions

- A probe would perform model inference or spend credits without explicit operator approval.
- A secret or authentication token would be displayed.
- Any runner is proposed as invocation-authorized.
- Product, provider, model, and runner identities cannot be distinguished.
- Capability claims are based only on docs or names.
- Evidence is stale to another commit.
- PR Steward is stale or blocked.
- Supervisor gate cannot be prepared.

## Expected output

```text
status: READY_FOR_REVIEW
validation_state: PASSED
authorized_runner_count: 0
series_gate: NEEDS_SUPERVISOR
next_packet: NONE_UNTIL_SUPERVISOR_AUTHORIZATION
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
