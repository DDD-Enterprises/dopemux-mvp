---
title: dopeTask Integration
plane: pm
component: dopemux
status: proposed
id: 07_DOPETASK_INTEGRATION
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: dopeTask Integration (explanation) for dopemux documentation and developer workflows.
---
# dopeTask Integration Contract

## Purpose
The seam between deterministic engine and stateful runtime. This defines the API between Supervisor (Brain) and dopeTask (Muscle).

## Scope
- The command-line interface to dopeTask.
- The artifact directory structure and schema.
- The separation of concerns (Policy vs Execution).
- The boundary between task-orchestrator (coordination layer) and dopeTask (deterministic engine).

---

## Non-negotiable invariants

### INV-DT-001: One-Way Call Direction

**INV-ID**: INV-DT-001
**Statement**: Supervisor calls dopeTask. dopeTask NEVER calls Supervisor API. The call direction is strictly Supervisor → dopeTask. dopeTask communicates back ONLY via file artifacts.
**Scope**: per-run
**Owner**: Architecture (boundary contract)
**Enforcement Surface**:
- `scripts/dopetask` is a shell wrapper that `exec dopetask "$@"` — it accepts arguments, it does not make HTTP calls back.
- dopeTask is invoked as a subprocess. It has no knowledge of Supervisor endpoints.
- No Supervisor URL or callback endpoint is passed to dopeTask in any argument or environment variable.
**Violation Mode**: Bidirectional coupling — dopeTask starts making decisions that belong to Supervisor (policy leak).
**Detection Method**:
- Code audit: dopeTask codebase must contain zero HTTP client calls to Supervisor or task-orchestrator endpoints.
- `grep -r "localhost:8000\|SUPERVISOR_URL\|callback" .dopetask_venv/` must return zero matches in dopeTask code.
**Recovery Strategy**: If bidirectional call detected, it is a design violation. Remove the call path. dopeTask must communicate only via artifacts.
**Evidence**:
- `scripts/dopetask` (lines 1-23): Pure wrapper. Activates venv, execs `dopetask` binary. No callbacks.
- `.dopetask-pin`: `install=pip dep=dopetask version=0.1.4` — pip package, separate codebase.

---

### INV-TX-002: Stateless Execution

**INV-ID**: INV-TX-002
**Statement**: TaskX execution result depends ONLY on the input packet and the current file system state. TaskX has NO internal persistent memory across runs. Each invocation is a clean-slate execution.
**Scope**: per-run
**Owner**: TaskX
**Enforcement Surface**:
- TaskX uses a virtualenv (`.taskx_venv/`) with no persistent state files.
- No database, no cache, no session file within TaskX.
- The only inputs are: (1) the packet JSON, (2) the output directory, (3) the filesystem being operated on.
**Violation Mode**: Non-determinism — same packet on same filesystem produces different results because TaskX remembers something from a previous run.
**Detection Method**:
- Determinism test: Run same packet twice on identical filesystem state. Artifacts must be byte-identical (ignoring timestamps in metadata).
- Check for state files: `find .taskx_venv/ -name "*.db" -o -name "*.json" -o -name "*.cache"` should find no state persistence.
**Recovery Strategy**: If state leakage detected, delete `.taskx_venv/` and reinstall from `.taskx-pin`. TaskX is always rebuildable from pin.
**Evidence**:
- `.taskx-pin`: `install=git` — installed from git, no local state mechanism.
- `scripts/taskx` (line 16): Venv is at `.taskx_venv/` — a Python virtualenv, not a state store.
- No database URL or Redis connection passed to TaskX in `scripts/taskx`.

---

### INV-TX-003: Artifact-Only Communication

**INV-ID**: INV-TX-003
**Statement**: TaskX communicates results back to Supervisor ONLY via files (JSON artifacts) written to the specified output directory. No stdout parsing for logic. No stderr parsing for state. No exit code semantics beyond success (0) / failure (non-zero).
**Scope**: per-run
**Owner**: Contract (Supervisor ↔ TaskX)
**Enforcement Surface**:
- CLI interface: `taskx orchestrate --packet <path> --output <dir> --mode auto`.
- Supervisor reads artifacts from `--output` directory after TaskX exits.
- Supervisor MUST NOT parse TaskX stdout/stderr for decision-making.
**Violation Mode**: Fragile coupling — Supervisor breaks when TaskX changes its log format.
**Detection Method**:
- Code audit: Supervisor code that calls TaskX must not use `subprocess.PIPE` for logic extraction from stdout.
- Artifact presence check: After TaskX exits, `RUN_REPORT.json` must exist in output directory.
**Recovery Strategy**: If artifact is missing, treat as failure. Do not attempt to reconstruct state from logs.
**Evidence**:
- Design contract (this document): "Artifact Only" invariant.
- Interface specification: `--output ./packets/current/artifacts/` defines the communication channel.

**Artifact Schema**:

| Artifact | Direction | Required | Schema |
|----------|-----------|----------|--------|
| `ROUTE_PLAN.json` | Supervisor → TaskX | Yes | Input packet with steps, runner selection, constraints |
| `RUN_REPORT.json` \| TaskX → Supervisor \| Yes \| `{status, steps[], cost}` |
| `ARTIFACT_INDEX.json` | TaskX → Supervisor | Yes | List of all files created/modified |
| `REFUSAL_REPORT.json` | TaskX → Supervisor | Conditional | Generated when TaskX refuses a step |

`RUN_REPORT.json` schema:
```json
{
  "status": "success | failure | refusal",
  "steps": [
    {
      "step_id": "string",
      "exit_code": 0,
      "stdout_snippet": "first 500 chars",
      "stderr_snippet": "first 500 chars",
      "duration_ms": 1234
    }
  ],
  "cost": {
    "tokens_input": 0,
    "tokens_output": 0,
    "model": "string"
  }
}
```

---

### INV-TX-004: No History Mutation

**INV-ID**: INV-TX-004
**Statement**: Dopemux NEVER edits a past packet. If a run fails, Dopemux creates a NEW packet referenced as a child of the failed one. History is an append-only DAG of packets.
**Scope**: per-packet
**Owner**: Supervisor
**Enforcement Surface**:
- File naming convention: `packet.json`, `packet_v2.json`, `packet_v3.json` with parent references.
- Supervisor code must use `open(path, 'w')` only for NEW files, never overwrite existing packet files.
- Parent-child linking via `parent_packet_id` field in packet JSON.
**Violation Mode**: History rewriting — the record of what was attempted is altered, breaking audit trail.
**Detection Method**:
- Git history: packet files should only appear in `git log` as additions, never modifications.
- File mtime audit: packet file mtime should equal ctime (never modified after creation).
**Recovery Strategy**: If a packet was modified, the git history preserves the original. Restore from git.
**Evidence**:
- Design contract (this document): "No editing history" section.
- Aligns with INV-MEM-003 (append-only ledger) — packets are part of the ledger.

---

### INV-TX-005: Refusal Contract

**INV-ID**: INV-TX-005
**Statement**: When TaskX encounters an invalid step, guardrail violation, or unrecoverable error, it MUST produce a `REFUSAL_REPORT.json` artifact and exit with non-zero status. It MUST NOT crash, hang, or produce partial results without a report.
**Scope**: per-run
**Owner**: TaskX
**Enforcement Surface**:
- TaskX error handling: catch exceptions → write `REFUSAL_REPORT.json` → exit non-zero.
- Supervisor checks for `REFUSAL_REPORT.json` on non-zero exit.
**Violation Mode**: Silent failure — TaskX crashes without producing any artifact. Supervisor has no information about what happened.
**Detection Method**:
- After non-zero exit: check for `REFUSAL_REPORT.json` in output directory. If missing → TaskX violated this contract.
- Crash detection: if neither `RUN_REPORT.json` nor `REFUSAL_REPORT.json` exists after exit, log "TaskX contract violation: no artifact produced."
**Recovery Strategy**: Treat missing artifact as S1 failure. Log raw exit code and any stderr captured. Create a synthetic failure record in the ledger.
**Evidence**:
- Design contract: "Refusal" section — "produce REFUSAL_REPORT.json".
- TaskX responsibilities: "If a step fails or violates a local guardrail, produce REFUSAL_REPORT.json."

`REFUSAL_REPORT.json` schema:
```json
{
  "status": "refusal",
  "reason": "string describing why the step was refused",
  "step_id": "string identifying the failed step",
  "guardrail": "string identifying which guardrail was triggered",
  "timestamp": "ISO 8601"
}
```

---

### INV-TX-006: Coordination Layer Non-Authority

**INV-ID**: INV-TX-006
**Statement**: The task-orchestrator is a COORDINATION LAYER only. It routes, syncs, and monitors. It does NOT make policy decisions about which runner to use, whether to proceed after failure, or how to interpret results. Those are Supervisor responsibilities.
**Scope**: system architecture
**Owner**: Architecture
**Enforcement Surface**:
- task-orchestrator's `main.py`: exposes coordination endpoints (`/api/coordination/*`), health, metrics, WebSocket streaming. No runner selection logic.
- task-orchestrator's `sync.py`: `MultiDirectionalSyncEngine` syncs state between Leantime, ConPort, and local systems. Sync is mechanical, not policy.
- Conflict resolution in sync.py: strategies include `ASK_USER` — the coordination layer presents options but doesn't decide.
**Violation Mode**: Policy leak — coordination layer starts making decisions that belong to Supervisor (runner selection, cost optimization, go/no-go).
**Detection Method**:
- Code audit: task-orchestrator should not import or reference TaskX, runner APIs, or model selection logic.
- API audit: `/api/coordination/*` endpoints should handle events and conflicts, not execution commands.
**Recovery Strategy**: If policy logic is found in task-orchestrator, extract it to Supervisor layer.
**Evidence**:
- `services/task-orchestrator/app/main.py`: FastAPI app titled "Dopemux Plane Coordination API". Endpoints are: health, info, metrics, coordination operations, events, conflicts, WebSocket.
- `sync.py`: `ConflictResolution` enum includes `ASK_USER` — defers decisions, doesn't make them.
- `/info` endpoint (line 306): describes itself as "Advanced task orchestration and dependency management with 37 tools."
- The 37 tools are coordination tools, not execution tools.

---

### INV-TX-007: Manual Handoff Chunk

**INV-ID**: INV-TX-007
**Statement**: TaskX execution MUST be chunked into discrete steps. Each step is independently reportable, independently refusable, and independently auditable. TaskX MUST NOT execute monolithic operations that cannot be inspected at step boundaries.
**Scope**: per-run
**Owner**: TaskX
**Enforcement Surface**:
- Packet structure: `ROUTE_PLAN.json` contains a `steps[]` array. Each step has an ID, runner, and constraints.
- `RUN_REPORT.json` reports per-step results with exit codes and stdout/stderr snippets.
- Step boundaries are the "handoff chunks" where Supervisor can inspect progress.
**Violation Mode**: Opaque execution — TaskX runs everything as one blob, making it impossible to identify which step failed or audit individual actions.
**Detection Method**:
- `RUN_REPORT.json` must contain a `steps[]` array with at least as many entries as `ROUTE_PLAN.json` steps.
- Each step must have an `exit_code` and `step_id`.
**Recovery Strategy**: If report lacks step granularity, the run is treated as non-auditable. Supervisor logs a warning and flags the packet for manual review.
**Evidence**:
- Interface specification (this document): `steps` array in both ROUTE_PLAN and RUN_REPORT.
- TaskX responsibilities: "Run steps 1, 2, 3 in order."

---

### INV-TX-008: No Self-Directed LLM Calls

**INV-ID**: INV-TX-008
**Statement**: TaskX MUST NOT autonomously query LLMs to "auto-fix" errors, expand scope, or make decisions. TaskX executes the runner specified in the packet. If the runner happens to be an LLM (e.g., Claude, Codex), that is the packet's instruction — not TaskX's initiative.
**Scope**: per-run
**Owner**: Architecture (boundary contract)
**Enforcement Surface**:
- TaskX does not have API keys in its environment (they are in the runner's environment, not TaskX's).
- TaskX's role is "runner sandboxing" — it invokes the specified runner, it doesn't decide to call additional models.
**Violation Mode**: Scope creep — TaskX starts "helping" by calling LLMs, burning tokens, and making unaudited decisions.
**Detection Method**:
- Environment audit: TaskX process should not have `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. in its environment.
- Network audit: TaskX should not make HTTP calls to model provider endpoints.
**Recovery Strategy**: If LLM calls detected in TaskX, it is a design violation. Strip API keys from TaskX environment. Refactor the auto-fix logic into Supervisor.
**Evidence**:
- `scripts/taskx`: Only activates venv and execs `taskx`. No API keys passed.
- Design contract: "Scope Creep: TaskX starts trying to auto-fix errors by querying an LLM itself. (STRICTLY FORBIDDEN)."

---

## FACT ANCHORS (Repo-derived)

- **OBSERVED: TaskX Wrapper**: `scripts/taskx` — 23-line bash wrapper. Checks `.taskxroot`, `.taskx-pin`, `.taskx_venv/` existence. Activates venv. Execs `taskx`.
- **OBSERVED: TaskX Pin**: `.taskx-pin` contains `install=git repo=https://github.com/hu3mann/taskX.git ref=v0.1.2`.
- **OBSERVED: TaskX Root**: `.taskxroot` exists (empty file — sentinel for repo identity).
- **OBSERVED: Task-Orchestrator**: `services/task-orchestrator/app/main.py` — FastAPI "Plane Coordination API" with coordination, conflict resolution, WebSocket streaming. NOT an execution engine.
- **OBSERVED: Sync Engine**: `services/task-orchestrator/app/core/sync.py` — `MultiDirectionalSyncEngine` with 7 sync directions and conflict resolution strategies.
- **OBSERVED: Coordination Events**: task-orchestrator handles `CoordinationEventType` including TASK_CREATED, TASK_UPDATED, DECISION_MADE, BREAK_RECOMMENDED.
- **OBSERVED: Workflow Service**: task-orchestrator exposes idea/epic CRUD via `/api/workflow/*` endpoints.
- **INFERRED: Virtualenv**: `.taskx_venv/` is a Python virtualenv for TaskX isolation.

---

## Failure modes

### 1. TaskX Crash Without Artifact
- **Invariant**: INV-TX-005
- **Trigger**: Unhandled exception, segfault, OOM kill.
- **Impact**: Supervisor has no artifact to read. Run state is unknown.
- **Severity**: S1 high.
- **Containment**: Supervisor checks for artifact presence. If missing after non-zero exit, creates synthetic failure record.
- **Detection**: Neither `RUN_REPORT.json` nor `REFUSAL_REPORT.json` in output directory.

### 2. Non-Deterministic Execution
- **Invariant**: INV-TX-002
- **Trigger**: TaskX uses `datetime.now()`, random seeds, or reads network state.
- **Impact**: Same packet produces different artifacts on different runs.
- **Severity**: S2 medium (testing reliability affected).
- **Containment**: Determinism test in CI — run same packet twice, diff artifacts.
- **Detection**: Byte-diff of artifacts from identical runs (ignoring timestamp metadata).

### 3. Scope Creep (Auto-Fix)
- **Invariant**: INV-TX-008
- **Trigger**: TaskX developer adds "helpful" auto-retry with LLM call.
- **Impact**: Unaudited token spend, uncontrolled decisions, broken boundary contract.
- **Severity**: S1 high (architectural violation).
- **Containment**: Code review. Environment audit (no API keys in TaskX env).
- **Detection**: `grep -r "openai\|anthropic\|litellm" .taskx_venv/lib/` excluding known runner packages.

### 4. Coordination Layer Policy Leak
- **Invariant**: INV-TX-006
- **Trigger**: task-orchestrator starts selecting runners or deciding go/no-go.
- **Impact**: Policy logic split across two systems. Inconsistent decisions.
- **Severity**: S2 medium (architectural drift).
- **Containment**: Code review. API endpoint audit — no execution commands in coordination API.
- **Detection**: task-orchestrator importing TaskX modules or runner selection logic.

### 5. History Mutation
- **Invariant**: INV-TX-004
- **Trigger**: Code path overwrites an existing packet file instead of creating a new version.
- **Impact**: Audit trail corrupted. Cannot replay or understand what was actually attempted.
- **Severity**: S1 high.
- **Containment**: File creation mode (`open(path, 'x')` — exclusive create, fails if exists).
- **Detection**: Git shows modification (not addition) of packet files.

### 6. Bidirectional Call
- **Invariant**: INV-TX-001
- **Trigger**: TaskX makes HTTP call to Supervisor or task-orchestrator.
- **Impact**: Tight coupling, circular dependency, unpredictable behavior.
- **Severity**: S0 critical (architectural violation).
- **Containment**: No Supervisor URL in TaskX environment. Network isolation in Docker.
- **Detection**: Network audit of TaskX container — no outbound HTTP to port 8000.

---

## Enforcement surface summary

| Invariant | Enforcement Point | Mechanism | Automated? |
|-----------|-------------------|-----------|------------|
| INV-TX-001 | `scripts/taskx` | No callback args, no URLs | Yes (by absence) |
| INV-TX-002 | `.taskx_venv/` | No state files in venv | Partially (CI check) |
| INV-TX-003 | CLI interface | `--output` dir is the channel | By design |
| INV-TX-004 | File naming | Versioned packets, no overwrites | Partially (git audit) |
| INV-TX-005 | TaskX error handling | `REFUSAL_REPORT.json` on failure | By contract |
| INV-TX-006 | Architecture | task-orchestrator = coordination only | Code review |
| INV-TX-007 | Packet structure | `steps[]` array in plan and report | By contract |
| INV-TX-008 | Environment | No API keys in TaskX env | By design |

---

## Degradation ladder

| Level | Condition | Behavior |
|-------|-----------|----------|
| L0: Nominal | TaskX available, all runners healthy | Full execution capability |
| L1: Runner Degraded | Preferred runner unavailable | Supervisor selects alternative runner in new packet |
| L2: TaskX Slow | TaskX execution exceeds timeout | Supervisor marks packet as TIMEOUT, creates retry packet |
| L3: TaskX Down | `.taskx_venv/` corrupt or missing \| Supervisor refuses execution. `scripts/taskx` exits 2. Operator reinstalls from `.taskx-pin` |
| L4: Contract Violation | Artifact missing after execution | Supervisor creates synthetic failure record. Flags for manual review |

---

## Determinism guarantees

- **Input determinism**: Given identical `ROUTE_PLAN.json` and identical filesystem state, TaskX MUST produce identical `RUN_REPORT.json` (INV-TX-002). Exception: timestamp metadata fields in artifacts.
- **Step ordering**: Steps execute in array order as specified in `ROUTE_PLAN.json`. No parallel step execution unless explicitly specified in the packet.
- **Runner isolation**: Each runner invocation is sandboxed. Runner A's execution does not affect Runner B's environment.
- **Non-deterministic exceptions**: Timestamps, UUIDs in artifact metadata, network-dependent runner outputs (e.g., LLM responses). These are expected and excluded from byte-identical comparison.

---

## Contradiction analysis

| Claim | Source | Status |
|-------|--------|--------|
| TaskX is external repo | `.taskx-pin` \| CONFIRMED — `repo=https://github.com/hu3mann/taskX.git ref=v0.1.2` |
| `scripts/taskx` is wrapper only \| `scripts/taskx` | CONFIRMED — 23 lines, activates venv, execs binary |
| task-orchestrator is coordination layer | `main.py` | CONFIRMED — API is coordination/events/conflicts, not execution |
| task-orchestrator has "37 tools" | `/info` endpoint | CONFIRMED — but tools are coordination tools, not execution tools |
| `enhanced_orchestrator.py` exists | Earlier doc FACT ANCHOR | NOT FOUND — file not present in repo |
| `src/taskx/schema/artifacts.py` exists | Earlier doc FACT ANCHOR | NOT VERIFIED — external repo, not in this workspace |
| TaskX has no API keys | `scripts/taskx`, design contract | CONFIRMED — no keys passed in wrapper |
| Duplicate open question | Earlier doc version | CONFIRMED — "Live Output Streaming" was duplicated. Removed in this version. |

---

## TaskX responsibilities (Muscle)
- **Deterministic Orchestration**: Run steps 1, 2, 3 in order as specified in packet.
- **Runner Sandboxing**: Execute the specific runner (Claude, Codex) requested in the step.
- **Artifact Generation**: Produce `RUN_REPORT.json` faithfully recording what happened.
- **Refusal**: If a step fails or violates a local guardrail, produce `REFUSAL_REPORT.json`.

## Dopemux responsibilities (Brain)
- **Packet Generation**: Create the `ROUTE_PLAN.json` (The "Packet").
- **Policy Enforcement**: Decide *which* runner to use.
- **Memory Persistence**: Read `RUN_REPORT.json` and save relevant bits to ConPort (INV-MEM-002).
- **Cost Optimization**: Decide if we can afford to run the packet.
- **History Management**: Never edit past packets (INV-TX-004). Create new versions.

## Task-Orchestrator responsibilities (Coordination)
- **Event Routing**: Broadcast coordination events via WebSocket and Redis.
- **State Sync**: `MultiDirectionalSyncEngine` syncs between Leantime, ConPort, and local systems.
- **Conflict Presentation**: Detect sync conflicts, present resolution options (may include `ASK_USER`).
- **Health Monitoring**: Track plane health, expose metrics and status endpoints.
- **Workflow CRUD**: Idea and Epic management via `/api/workflow/*` endpoints.
- **NOT**: Runner selection, cost decisions, go/no-go decisions, TaskX invocation.

## Interface
**Command**:
```bash
taskx orchestrate \
  --packet ./packets/current/packet.json \
  --output ./packets/current/artifacts/ \
  --mode auto
```

## Key rule: no editing history
- Dopemux NEVER edits a past packet.
- If a run fails, Dopemux creates a **NEW** packet (e.g., `packet_v2.json`) referenced as a child of the failed one.
- History is an append-only DAG (Directed Acyclic Graph) of packets.

## Open questions
- **Live Output Streaming**: Can Supervisor stream TaskX stdout in real-time to UI?
- *Resolution*: Yes, via subprocess pipe reading in `Dispatch`. This is for display only — not for logic (INV-TX-003).

## Acceptance criteria
1. **Determinism Test**: Run the same Packet twice on the same file state. Resulting artifacts MUST be byte-identical (ignoring timestamps in artifact metadata).
1. **Refusal Test**: Give TaskX a packet with an invalid step. It MUST fail gracefully with a `REFUSAL_REPORT.json` and not crash.
1. **One-Way Test**: Audit TaskX codebase for any HTTP client calls to Supervisor endpoints. Must find zero.
1. **Artifact Presence Test**: Kill TaskX mid-execution. Supervisor must detect missing artifacts and create synthetic failure record.
1. **History Immutability Test**: Attempt to overwrite an existing packet file. System must refuse or create a new version instead.
1. **Coordination Boundary Test**: Audit task-orchestrator for runner selection or TaskX invocation logic. Must find zero.
