# Phase R: Arbitration (GPT-5.2 Extended Thinking)

## Phase R goal
Produce evidence-linked truth maps for the system areas you named:
Dope-Memory implementation truth
EventBus + producers wiring truth
Trinity boundary enforcement truth
TaskX integration truth
Workflows truth
And a conflict + risk ledger that separates:
Implemented vs Planned vs Unknown
Repo control plane vs Home control plane vs Code vs Docs

## Model
GPT-5.2 Extended Thinking (this chat)

## Hard rules
Do not rescan the repo. Reason ONLY from input artifacts.
Every non-trivial claim must cite one of:
CODE: reference from Phase C outputs (path + line_range)
REPOCTRL: reference from Phase A outputs
HOMECTRL: reference from Phase H outputs
DOC: reference from Phase D outputs
If not evidenced: write UNKNOWN and list what artifact is missing.
No refactors. No implementation. Only truth + bounded recommendations.

## Required inputs (must exist)
From Phase A:
REPO_INSTRUCTION_SURFACE.json
REPO_INSTRUCTION_REFERENCES.json
REPO_MCP_SERVER_DEFS.json
REPO_MCP_PROXY_SURFACE.json
REPO_ROUTER_SURFACE.json
REPO_HOOKS_SURFACE.json
REPO_IMPLICIT_BEHAVIOR_HINTS.json
REPO_COMPOSE_SERVICE_GRAPH.json
REPO_LITELLM_SURFACE.json
REPO_TASKX_SURFACE.json
From Phase H:
HOME_MCP_SURFACE.json
HOME_ROUTER_SURFACE.json
HOME_PROVIDER_LADDER_HINTS.json
HOME_LITELLM_SURFACE.json
HOME_PROFILES_SURFACE.json
HOME_TMUX_WORKFLOW_SURFACE.json
HOME_SQLITE_SCHEMA.json
From Phase D (docs):
DOC_TOPIC_CLUSTERS.json
DOC_SUPERSESSION.json
DOC_CONTRACT_CLAIMS.json
DUPLICATE_DRIFT_REPORT.json (docs)
DOC_INDEX.json (or equivalent index from D)
From Phase C (code):
SERVICE_ENTRYPOINTS.json
EVENTBUS_SURFACE.json
EVENT_PRODUCERS.json
EVENT_CONSUMERS.json
DOPE_MEMORY_CODE_SURFACE.json
DOPE_MEMORY_SCHEMAS.json
DOPE_MEMORY_DB_WRITES.json
TRINITY_ENFORCEMENT_SURFACE.json
REFUSAL_AND_GUARDRAILS_SURFACE.json
TASKX_INTEGRATION_SURFACE.json
WORKFLOW_RUNNER_SURFACE.json
risk scans: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json

## Phase R deliverables (files to produce)
R0: CONTROL_PLANE_TRUTH_MAP.md
What behavior is controlled by instruction/config/hooks/compose rather than code.
R1: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
What the memory system actually does today:
stores, schemas, ingestion, retention, replay surfaces
sqlite/postgres usage split
triggers and append-only enforcement (or gaps)
where TTL/caps are enforced
R2: EVENTBUS_WIRING_TRUTH.md
Actual event names/topics, producers, consumers, dispatch paths.
include a table: event -> producers -> consumers -> adapters
R3: TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
Where boundaries are enforced:
checks, guardrails, refusal rails
bypass paths (if any) supported by evidence
R4: TASKX_INTEGRATION_TRUTH.md
Where TaskX touches:
packet i/o
operator instruction compilation/injection
orchestrator bridging
scripts or hooks calling taskx
R5: WORKFLOWS_TRUTH_GRAPH.md
Workflow catalog from code + control plane:
start scripts, tmux, compose, runners
ordered step sequences, inputs/outputs, services involved
R6: PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
Home vs repo dependency risks:
what is required from ~/.dopemux or ~/.config to run
which env vars are required
where MCP -> hooks migration will break or simplify
R7: CONFLICT_LEDGER.md
Contradictions across docs vs code vs control planes:
show both claims and citations, no resolution without evidence hierarchy
include recency weighting as a tie-breaker only when docs conflict
R8: RISK_REGISTER_TOP20.md
Top 20 risks (determinism/idempotency/concurrency/boundary) with severity + evidence

## Arbitration procedure (must follow)
Step 1: Build an evidence hierarchy per topic
For each topic (memory, eventbus, trinity, taskx, workflows):
Code surfaces (Phase C) define “implemented”.
Repo control plane (Phase A) defines “how it’s invoked”.
Home control plane (Phase H) defines “what local state it depends on”.
Docs (Phase D) define “planned/intended”, unless explicitly marked ACTIVE and matches code.
If docs conflict, consult:
DOC_SUPERSESSION.json first
then doc timestamps (recency) as tie-breaker
never override code reality with docs
Step 2: Separate statements into 3 bins
Every claim in every truth map must be labeled:
IMPLEMENTED (with CODE evidence)
PLANNED (with DOC evidence)
UNKNOWN (missing evidence)
Step 3: Control plane surfacing
Any behavior modulated by:
instruction files
mcp configs
router/provider configs
hooks
compose graphs
must be shown explicitly in CONTROL_PLANE_TRUTH_MAP with citations.

## The actual GPT-5.2 prompts (copy/paste)

### Prompt R0: Control plane truth map
ROLE: Supervisor/Auditor. Evidence-first.
TASK: Produce CONTROL_PLANE_TRUTH_MAP.md.

INPUTS: Phase A + Phase H + Phase C entrypoints + Phase D claims.

OUTPUT FORMAT:
- Section 1: Repo control plane surfaces (instructions, hooks, compose, router, litellm, mcp)
- Section 2: Home control plane surfaces (configs, router, litellm, mcp, sqlite state)
- Section 3: Invocation graph (what starts what) with evidence
- Section 4: Control plane -> runtime coupling points (where control plane influences code paths)
- Section 5: Portability risks (things that prevent clean bootstrap)

RULES:
- Cite every bullet with REPOCTRL:/HOMECTRL:/CODE: references.
- No interpretation beyond “X references Y” or “X config defines keys A,B”.
- Label anything without evidence UNKNOWN.

### Prompt R1: Dope-Memory implementation truth
ROLE: Supervisor/Auditor.
TASK: Produce DOPE_MEMORY_IMPLEMENTATION_TRUTH.md.

MUST INCLUDE:
- Stores/adapters list (sqlite/postgres/other)
- Schema objects list (tables/indexes/triggers) from DOPE_MEMORY_SCHEMAS.json
- Write paths: where inserts/updates/deletes occur (from DOPE_MEMORY_DB_WRITES.json)
- Retention/ttl enforcement points (from DOPE_MEMORY_CODE_SURFACE.json + risk scans)
- Replay surfaces: how events/entries can be re-derived or re-ingested (if present)
- Control plane dependencies: env vars, compose wiring, home DBs

FORMAT:
1) IMPLEMENTED: numbered facts with CODE citations
2) PLANNED: doc claims with DOC citations (only if present)
3) GAPS/CONFLICTS: cite both sides
4) Minimal verification commands (suggestions only, no claims of having run them)

RULES:
- If you mention a table/trigger, cite its statement source.
- If docs disagree, show DOC_SUPERSESSION evidence and recency tie-breaker.

### Prompt R2: EventBus wiring truth
ROLE: Supervisor/Auditor.
TASK: Produce EVENTBUS_WIRING_TRUTH.md.

MUST INCLUDE:
- Event bus implementations/adapters
- Event names/topics discovered (literal strings only when evidenced)
- Producer mapping: event -> producers (function locations)
- Consumer mapping: event -> handlers/subscribers
- Dispatch path(s): where producer calls flow to consumer execution
- Control plane impacts: any configs/instructions that change event routing

OUTPUT TABLE:
Event | Producers (CODE refs) | Consumers (CODE refs) | Adapter/Bus (CODE refs)

RULES:
- If event name is computed/unknown, put "(computed)" and cite excerpt.
- No guessing of missing event names.

### Prompt R3: Trinity boundary enforcement trace
ROLE: Supervisor/Auditor.
TASK: Produce TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md.

MUST INCLUDE:
- Enumerate plane boundaries (pm/memory/orchestrator/mcp/hooks/etc.) ONLY when evidenced in code/docs
- Enforcement points: exact symbols and files
- Refusal rails: where refusals are created and how they propagate
- Bypass paths: only if evidenced by missing guards or alternate code paths

OUTPUT:
- Boundary list with enforcement check locations
- Guardrail pipeline diagram in text (steps with citations)
- "Known bypass risks" with evidence

RULES:
- Do not invent boundary rules; only extract.
- Separate PLANNED boundary rules (docs) from IMPLEMENTED checks (code).

### Prompt R4: TaskX integration truth
ROLE: Supervisor/Auditor.
TASK: Produce TASKX_INTEGRATION_TRUTH.md.

MUST INCLUDE:
- How taskx is invoked (scripts/hooks/ci) with citations
- Where packets are read/written (paths, schema hints)
- Where operator instructions are compiled/injected (repo control plane + code if present)
- Any coupling to ~/.config/taskx or repo .taskx surfaces

OUTPUT:
- IMPLEMENTED integration map
- PLANNED integration map (docs)
- GAPS/risks

RULES:
- Cite REPO_TASKX_SURFACE + TASKX_INTEGRATION_SURFACE.

### Prompt R5: Workflows truth graph
ROLE: Supervisor/Auditor.
TASK: Produce WORKFLOWS_TRUTH_GRAPH.md.

MUST INCLUDE:
- Bootstrap flows (tmux, compose, scripts)
- Multi-service workflows (what runs first, what depends on what)
- Inputs/outputs and artifacts if explicitly mentioned
- Identify where "instruction files" are part of the workflow (control plane)

OUTPUT:
- Workflow list (W1..Wn) with steps (literal commands) + citations
- Services involved per workflow
- Where evidence is missing: UNKNOWN

RULES:
- No inferred steps.
- Use WORKFLOW_RUNNER_SURFACE + HOME_TMUX_WORKFLOW_SURFACE + compose graph.

### Prompt R6-R8: Risk + conflict ledgers
ROLE: Supervisor/Auditor.
TASK: Produce:
- PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- CONFLICT_LEDGER.md
- RISK_REGISTER_TOP20.md

PORTABILITY ledger must include:
- home-only dependencies
- required env vars
- mcp dependencies vs hooks opportunities
- "what breaks if moved to hooks" (evidence-based)

CONFLICT ledger must include:
- doc claim vs code truth
- doc vs doc conflicts resolved using DOC_SUPERSESSION then recency tie-breaker
- never override code reality

RISK register uses:
- determinism/idempotency/concurrency scans
- boundary bypass risks
- severity and suggested bounding mechanisms (minimal, mechanical)

RULES:
- Cite everything.
- Do not propose large refactors.
