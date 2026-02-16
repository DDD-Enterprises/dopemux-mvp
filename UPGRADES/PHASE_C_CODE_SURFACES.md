Phase C goal
Extract implemented truth surfaces from code:
Service boundaries and entrypoints
EventBus producers/consumers wiring
Dope-Memory implementation surface (schemas, writes, replay, sync)
Trinity boundary enforcement locations
TaskX integration points
Multi-service workflow runners (scripts, orchestrators)
Outputs are evidence indexes only.
Preferred model
Primary: Grok-code-fast-1
Fallback: Gemini Flash 3 (still ok)
Hard rules
JSON only, ASCII only.
No interpretation, no “seems”.
Every item includes path and line_range.
Deterministic ordering.
Never output secrets (same redaction policy as Phase H).
C0 (optional): Code inventory + scope narrowing (fast preflight)
Use this only if you don’t already have fresh *_SURFACE.json artifacts.
Outputs

CODE_INVENTORY.json
CODE_SCOPE_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

TARGET ROOT: dopemux-mvp repo working tree.

SCOPE INCLUDE:
- src/**
- services/**
- shared/**
- plugins/**
- ui-dashboard-backend/**
- dashboard/** (if python)
- scripts/**
- tools/**

OUTPUT 1: CODE_INVENTORY.json
For each file under scope:
- path
- size_bytes
- last_modified (if available)
- language by extension (py|ts|js|sh|sql|yaml|toml|md|other)
- first_nonempty_line (scan first 60 lines)
- imports_hint: list of top 5 import lines (py/ts/js) found in first 120 lines

OUTPUT 2: CODE_SCOPE_PLAN.json
Create deterministic partitions:
C1_SERVICE_ENTRYPOINTS
C2_EVENTBUS_WIRING
C3_DOPE_MEMORY_SURFACE
C4_TRINITY_BOUNDARIES
C5_TASKX_INTEGRATION
C6_WORKFLOWS_AND_RUNNERS

For each partition list candidate paths using simple path heuristics only:
- services/** for service entrypoints
- files containing "event" in name for eventbus wiring
- paths containing "memory" for memory surface
- paths containing "trinity" for boundary enforcement
- paths containing "taskx" for TaskX integration
- scripts/tools/compose runners for workflows

RULES:
- No content interpretation.
- JSON only.
C1: Service entrypoints + service graph (implemented)
Outputs
SERVICE_ENTRYPOINTS.json
SERVICE_API_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE:
- services/**
- src/**
- shared/**

TASK 1: SERVICE_ENTRYPOINTS.json
Extract:
- docker entrypoints from Dockerfiles if present (repo root or docker/*)
- python entrypoints: if __main__ blocks, typer/click apps, fastapi apps, flask apps
- node entrypoints: package.json scripts, server.ts/js, express apps
For each item:
- service_name (if inferable from folder name only)
- entry_kind = docker|python|node|shell|other
- path, line_range, excerpt <= 8 lines
- command_line if explicit (string), else null

TASK 2: SERVICE_API_HINTS.json
Extract any explicit network listeners:
- host/port constants
- uvicorn/gunicorn args
- express listen(...)
- compose ports mapping references if present in code comments/config
Emit:
- path, line_range, excerpt <= 6 lines, port if parseable

RULES:
- No inference beyond folder name for service_name.
- JSON only.
C2: EventBus wiring (producers, consumers, topics)
Outputs
EVENTBUS_SURFACE.json
EVENT_PRODUCERS.json
EVENT_CONSUMERS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE:
- src/**
- services/**
- shared/**

MATCH PATTERNS (case-insensitive, literal):
- "eventbus"
- "publish("
- "emit("
- "produce"
- "consume"
- "subscribe"
- "topic"
- "queue"
- "broker"
- "kafka"
- "redis"
- "nats"
- "rabbit"
- "sns"
- "sqs"

OUTPUT 1: EVENTBUS_SURFACE.json
For each match:
- match_type (publish|subscribe|topic|queue|broker|eventbus|other)
- path, line_range, excerpt <= 8 lines

OUTPUT 2: EVENT_PRODUCERS.json
Identify call sites that look like production:
- function calls where verb is publish/emit/produce/send
Emit:
- producer_id (path:line)
- path, line_range, excerpt <= 8 lines
- event_name/topic if present as literal string, else null

OUTPUT 3: EVENT_CONSUMERS.json
Identify call sites that look like consumption:
- subscribe/consume/handler registration
Emit:
- consumer_id (path:line)
- path, line_range, excerpt <= 10 lines
- event_name/topic if present as literal string, else null

RULES:
- Do not infer semantics of event names.
- JSON only.
C3: Dope-Memory implementation surface (schemas, writes, replay)
Outputs
DOPE_MEMORY_CODE_SURFACE.json
DOPE_MEMORY_DB_WRITES.json
DOPE_MEMORY_SCHEMAS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE:
- services/**/working-memory*/**
- services/**/dope*memory*/**
- docs/spec/dope-memory/** (include only for code-referenced file paths)
- src/** where "memory" modules exist
- shared/**

TASK 1: DOPE_MEMORY_CODE_SURFACE.json
Extract:
- store initialization code
- schema initialization/migrations code
- any "mirror", "sync", "ttl", "retention", "replay", "append-only" mentions
Emit:
- surface_type = init|migration|schema|replay|sync|ttl|retention|append_only|other
- path, line_range, excerpt <= 10 lines

TASK 2: DOPE_MEMORY_DB_WRITES.json
Scan for SQL write operations:
- INSERT, UPDATE, DELETE, REPLACE, UPSERT
Emit:
- write_kind (insert|update|delete|upsert|other)
- path, line_range
- excerpt <= 10 lines
- table_name if parseable as literal token else null

TASK 3: DOPE_MEMORY_SCHEMAS.json
Extract SQL DDL sources used by memory:
- .sql files in scope and inline CREATE TABLE/INDEX/TRIGGER strings
Emit:
- object_type table|index|trigger|view
- object_name if parseable
- path, line_range
- ddl_excerpt <= 30 lines OR full statement if <= 2000 chars

RULES:
- No inference of correctness.
- JSON only.
C4: Trinity boundary enforcement (where it is checked, not what it “means”)
Outputs
TRINITY_ENFORCEMENT_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE:
- src/**
- services/**
- shared/**
- .taskx/** (if relevant for enforcement)
- config/** (if enforcement config exists)

MATCH TOKENS (case-insensitive):
- "trinity"
- "boundary"
- "authority"
- "plane"
- "source of truth"
- "deny"
- "allow"
- "gate"
- "refuse"
- "policy"
- "enforce"

Extract:
- checks/guards: if-statements, assertions, exceptions, refusals, validation calls
- config keys named trinity/boundary/authority
Emit items:
- enforcement_kind = check|refusal|validation|config|other
- path, line_range, excerpt <= 10 lines

RULES:
- Do not infer policy intent.
- JSON only.
C5: TaskX integration points (invocations, packet formats, runner coupling)
Outputs
TASKX_INTEGRATION_SURFACE.json
TASKX_PACKET_IO_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE:
- .taskx/**
- src/**
- services/**
- scripts/**
- tools/**
- docs/task-packets/** (include only for file paths referenced by code/scripts)

MATCH TOKENS:
- "taskx"
- "task packet"
- "packet"
- "route plan"
- "runner"
- "jawbone" (if present)
- "ops compile"
- "ops apply"
- "taskx run"
- "taskx route"

OUTPUT 1: TASKX_INTEGRATION_SURFACE.json
Extract:
- subprocess calls invoking taskx
- imports or modules named taskx
- references to task packet paths and output directories
Emit:
- path, line_range, excerpt <= 10 lines

OUTPUT 2: TASKX_PACKET_IO_HINTS.json
Extract any JSON/YAML structures that look like packet IO:
- fields like objective, scope, invariants, plan, acceptance criteria
Emit:
- path, line_range, excerpt <= 20 lines
- detected_fields[] (field names only)

RULES:
- No inference.
- JSON only.
C6: Workflows and multi-service runners (what ties everything together)
Outputs
WORKFLOW_RUNNER_SURFACE.json
ORCHESTRATION_FILES.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE:
- scripts/**
- tools/**
- docker-compose*.yml
- compose/**
- start-mcp-servers.sh
- run_all_multi_workspace_tests.sh
- verify_dopecon_bridge.sh
- tmux-dopemux-orchestrator.yaml
- any files with "orchestrator" in name under docs/systems or src (code only)

OUTPUT 1: WORKFLOW_RUNNER_SURFACE.json
Extract:
- command sequences
- service startup orders
- pipeline steps and dependencies
Emit:
- runner_kind = shell|make|compose|tmux|python|node|other
- path, line_range, excerpt <= 10 lines

OUTPUT 2: ORCHESTRATION_FILES.json
List orchestration-relevant files:
- path, kind, sha256 if available
- referenced services/tools (as literals only)

RULES:
- JSON only.
- No inference.
C7: Merge + QA coverage
Outputs
CODE_SURFACES_MERGED.json
CODE_SURFACES_COVERAGE_REPORT.json
ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS:
- all outputs from C1..C6
- (optional) CODE_INVENTORY.json and CODE_SCOPE_PLAN.json

MERGE:
- concatenate items
- dedupe by (path, line_range, hash(excerpt))
- stable sort by path then line_range

QA OUTPUT:
- counts per artifact
- files_processed count
- top_paths_by_hits (top 25)
- missing_expected: list of expected artifacts not provided

RULES:
- JSON only.
Phase C success signals
You are done when you have:
service entrypoints surface
eventbus producer/consumer surfaces
dope-memory write + schema surfaces
trinity enforcement surface locations
taskx integration surface
workflow runner surface
No decisions yet.
