# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000R` · DCP · Current-Main Runtime and Toolchain Reconciliation

## Packet metadata

```text
packet_id: DMX-DCP-MODEL-ROUTING-MVP-0000R
project: dopemux-mvp
repo: DDD-Enterprises/dopemux-mvp
series: DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001
parent_packet: NONE
base_branch: main
observed_main_sha_at_authoring: eb212dcaa73c407c271e0ddc60e38bdd2b7e4661
execution_branch: dcp/model-routing-0000r-runtime-reconcile
status: PLAN_ONLY
risk: MEDIUM
task_class: runtime reconciliation / architecture-sensitive / read-only
primary_executor: Claude Code Sonnet
embedded_auditor: Claude Code Opus / Claude Opus
final_supervisor: GPT-5.5 Pro
merge_authority: NONE
```

## Objective

Produce a fresh, current-main evidence bundle for DCP routing, PAL, OpenCode, LiteLLM, runner availability, MCP wiring, proof contracts, and current GitHub control-plane state without changing runtime behavior.

## Why this packet exists now

The prior 0000C–0000I evidence was gathered in June 2026. Main has since absorbed the routing model, classifier, lane engine, provenance hardening, PAL model refresh, and unrelated infrastructure changes. Old health and inventory claims are stale.

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

- Inspect current `origin/main` runtime code, config, Compose output, tests, and active entrypoints.
- Verify which DCP CLI commands exist.
- Capture current PAL/OpenCode configuration and static wiring.
- Capture installed runner CLIs and versions without making paid inference calls.
- Determine the canonical PAL route and classify the stdio proxy.
- Capture LiteLLM/PAL container and health state from discovered configuration.
- Capture current proof, handoff, PR Steward, and audit contracts.
- Write reconciliation artifacts only.

## Scope OUT

- No source/config/runtime edits.
- No container publication.
- No model inference calls unless the operator separately authorizes a no-write live probe.
- No secrets, API keys, credential output, or `.env` contents.
- No Task Orchestrator, ConPort, dope-memory, GitHub, or external-service writes.
- No routing implementation.

## Invariants

- Runtime and current GitHub state outrank packet history.
- Missing tools or services are `UNKNOWN` or `UNAVAILABLE`, never inferred healthy.
- OpenCode/PAL wiring is not called functional merely because files exist.
- `pal_stdio_proxy.py` must be classified as canonical, legacy, experimental, or unused based on active references.
- Model inventory and runner support remain untrusted until observed.
- The packet remains read-only except its own proof/task-packet artifacts.

## Files allowed to change

```text
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000R.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/**
docs/03-reference/dcp/current-main-runtime-reconciliation.md
docs/03-reference/dcp/current-main-runtime-reconciliation.json
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
.env*
**/*secret*
**/*credential*
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

1. Lock a clean worktree to current `origin/main`.
2. Inventory DCP source files, CLI entrypoints, task packets, and tests.
3. Run deterministic DCP compilation and focused tests.
4. Resolve Compose and MCP configuration without exposing secrets.
5. Run `verify-pal.sh`; capture its exact semantics and limitations.
6. Inventory local CLIs and versions.
7. Inspect active containers and health only through discovered ports/endpoints.
8. Classify direct PAL stdio versus proxy routes.
9. Inspect current GitHub PR/control-plane state relevant to DCP.
10. Produce the machine-readable reconciliation and human summary.
11. Run independent audit of the evidence and non-claims.

## Exact commands

```bash
git worktree add "../dopemux-0000r" -b dcp/model-routing-0000r-runtime-reconcile origin/main
cd "../dopemux-0000r"

mkdir -p proof/DMX-DCP-MODEL-ROUTING-MVP-0000R

git rev-parse HEAD
git status --short --branch

find src/dopemux/dcp -maxdepth 2 -type f -print | sort
find task-packets -maxdepth 2 -type f -iname '*MODEL-ROUTING*' -print | sort
find tests -type f -path '*dcp*' -print | sort

python -m compileall -q src/dopemux/dcp src/dopemux/commands
python -m pytest -q tests/unit/dcp tests/dcp/test_dcp_model_routing_0001_domain.py

python -m dopemux.cli --help > proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/dopemux-help.txt 2>&1 || true
python -m dopemux.cli dcp --help > proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/dcp-help.txt 2>&1 || true

bash scripts/opencode/verify-pal.sh   > proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/verify-pal.log 2>&1 || true

opencode debug config   > proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/opencode-resolved-config.txt 2>&1 || true

docker compose config --format json   > proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/compose-resolved.json

docker ps --format '{{json .}}'   > proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/docker-ps.jsonl || true

for bin in codex claude opencode gemini agy grok; do
  {
    printf '%s=' "$bin"
    command -v "$bin" || true
    "$bin" --version 2>/dev/null || true
  } >> proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/runner-cli-inventory.txt
done

grep -RIn --exclude-dir=.git   -E 'pal_stdio_proxy|pal-stdio|start-pal|PAL_HTTP_URL|litellm|model-routing'   opencode.jsonc compose.yml mcp_catalog.yaml config scripts docker src services   > proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/reference-scan.txt || true
```

## Validation gates

- DCP compileall exits 0.
- Focused DCP test suites exit 0, or failures are classified with exact reproduction.
- `compose-resolved.json` parses.
- No proof artifact contains secret values.
- Every runtime claim names the command and artifact.
- The summary distinguishes static wiring from live behavior.
- Current main SHA is recorded.
- The diff contains only the packet allowlist.

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
CURRENT_MAIN_RUNTIME_RECONCILIATION.json
CURRENT_MAIN_RUNTIME_RECONCILIATION.md
```

Required machine fields:

```text
main_sha
dcp_components
dcp_cli_surface
pal_route
pal_proxy_disposition
opencode_wiring
litellm_state
pal_state
runner_inventory
mcp_registry_state
proof_contract_state
pr_steward_state
unknowns
contradictions
next_packet_inputs
```

Do not store environment-variable values.

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
rm -rf proof/DMX-DCP-MODEL-ROUTING-MVP-0000R
git worktree remove "../dopemux-0000r" --force
git branch -D dcp/model-routing-0000r-runtime-reconcile
```

## Stop conditions

- A command would expose a secret.
- Runtime identity or repository identity is ambiguous.
- Current main cannot be fetched.
- Required runtime truth can only be obtained through a write.
- Docker or a required local service is wedged and cannot be inspected safely.
- Evidence conflicts cannot be preserved cleanly.

## Expected output

```text
status: READY_FOR_REVIEW | BLOCKED
validation_state: PASSED | PARTIAL | FAILED
runtime_truth_freshness: CURRENT_TO_SUBJECT_SHA
merge_readiness: BLOCKED_NOT_REQUESTED
recommended_next_packet: DMX-DCP-MODEL-ROUTING-MVP-0000S
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
