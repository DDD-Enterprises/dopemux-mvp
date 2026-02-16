# Phase C: Code Surfaces (Flash/Grok)

## Phase C goal
Mechanically extract runtime surfaces from code:
Service entrypoints and service graph from code (not only compose)
EventBus: topics/events, producers, consumers, adapters, dispatch paths
Dope-Memory: stores, schemas, migrations, write paths, triggers, retention/ttl, replay surfaces
Trinity boundary: enforcement points, guards, refusal rails, cross-plane access restrictions
TaskX integration: packet I/O, orchestrator bridge points, ops CLI, repo-instruction injection points
Workflow runners: scripts/CLIs that coordinate multi-service flows
Determinism / idempotency / concurrency risk location indices (location-only)
API surface and dashboard surfaces (if present)
Outputs are indices, not meaning.

## Hard rules
JSON only, ASCII only.
Every item includes path, line_range, symbol (if applicable), and excerpt.
No inferred “purpose”, no “this does X”, no authoritative decisions.
Prefer extraction with stable IDs.

## C0: Code inventory + partition plan (mandatory)
Outputs
CODE_INVENTORY.json
CODE_PARTITION_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

SCOPE:
- src/**
- services/**
- shared/**
- tools/**
- scripts/**
- dashboard/**, ui-dashboard-backend/** (if code)
- plugins/**, components/** (if code)

OUTPUT 1: CODE_INVENTORY.json
For each file:
- path
- size_bytes
- file_kind by extension (py|ts|js|sh|yaml|toml|md|sql|other)
- sha256 if <= 1MB else null
- first_nonempty_line
- contains_tokens[] match from:
  ["event","bus","publish","emit","consume","subscriber","producer",
   "dope-memory","chronicle","sqlite","postgres","mirror","schema","migration","trigger","ttl",
   "taskx","packet","orchestrator","runner","workflow","hook","mcp",
   "determinism","idempotent","uuid","random","async","thread","queue","retry",
   "trinity","boundary","refusal","guard","policy","allowlist","denylist",
   "typer","click","fastapi","flask","uvicorn","gunicorn"]

OUTPUT 2: CODE_PARTITION_PLAN.json
Create deterministic partitions with explicit path lists:
C1_SERVICE_ENTRYPOINTS
C2_EVENTBUS_WIRING
C3_DOPE_MEMORY_SURFACES
C4_TRINITY_ENFORCEMENT_SURFACES
C5_TASKX_INTEGRATION_SURFACES
C6_WORKFLOW_RUNNERS_AND_COORDINATION
C7_API_AND_UI_BACKENDS
C8_DETERMINISM_IDEMPOTENCY_CONCURRENCY_SCANS

JSON only.

## C1: Service entrypoints (code-level)
Outputs
SERVICE_ENTRYPOINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- services/**
- src/** where servers are started
- any __main__.py, main.py, app.py, server.py, cli.py
- any file invoking uvicorn/gunicorn/node start

Extract entrypoints:
- kind: python_module|cli_command|shell_script|node_script
- symbol (function/class) if present
- invocation patterns (if __name__ == "__main__", typer app, click group, fastapi app)
- host/port if literal (do not infer)
- env var keys referenced
- excerpt <= 40 lines

Each item:
- service_name (folder name or inferred from path only)
- path, line_range, symbol|null
- excerpt
- detected_tokens[] subset: ["fastapi","uvicorn","typer","click","sqlite","postgres","mcp","litellm"]

JSON only.

## C2: EventBus wiring truth surfaces
Outputs
EVENTBUS_SURFACE.json
EVENT_PRODUCERS.json
EVENT_CONSUMERS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- any file matching tokens "event", "bus", "publish", "emit", "dispatch", "subscriber"
- adapters in shared/** and services/**

TASK 1: EVENTBUS_SURFACE.json
Extract:
- event bus interfaces/classes
- registration points
- dispatch functions
- adapter implementations (e.g., in-proc, queue, db, http)
Each item:
- item_kind: interface|impl|adapter|dispatcher|registry
- path, line_range, symbol
- excerpt <= 30 lines
- referenced_event_names[]: literal strings that look like event names (no inference)

TASK 2: EVENT_PRODUCERS.json
Extract any call sites that emit/publish events:
- producer_id
- event_name literal (if string present, else null)
- path, line_range, symbol (caller function)
- excerpt <= 12 lines
- target_bus_symbol if explicit

TASK 3: EVENT_CONSUMERS.json
Extract any call sites that subscribe/consume:
- consumer_id
- event_name literal (if string present, else null)
- handler symbol
- path, line_range, excerpt <= 20 lines

RULES:
- If event name is computed, store null and capture excerpt.
- JSON only.

## C3: Dope-Memory surfaces
Outputs
DOPE_MEMORY_CODE_SURFACE.json
DOPE_MEMORY_SCHEMAS.json
DOPE_MEMORY_DB_WRITES.json
MIGRATIONS_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- services/**working-memory-assistant**/** (or any memory service folder)
- docs/spec/dope-memory is docs (handled in D), here is code only
- any module containing chronicle, mirror, sqlite, postgres, schema, migration, ttl

TASK 1: DOPE_MEMORY_CODE_SURFACE.json
Extract:
- store classes (SQLite/Postgres adapters)
- ingestion functions
- search/query functions
- mirror sync functions
- retention/ttl logic locations
Each item:
- item_kind: store|adapter|ingest|query|sync|retention|index
- path, line_range, symbol, excerpt <= 35 lines

TASK 2: DOPE_MEMORY_SCHEMAS.json
Extract schema definitions:
- .sql files: CREATE TABLE/INDEX/TRIGGER statements (full statement)
- inline SQL strings if they contain CREATE/ALTER
For each schema object:
- object_kind: table|index|trigger|view|migration
- name
- path, line_range
- statement (string)
JSON only.

TASK 3: DOPE_MEMORY_DB_WRITES.json
Extract write paths:
- INSERT/UPDATE/DELETE statements or ORM calls if detectable
- file path, line_range, symbol, excerpt <= 12 lines
- write_kind: insert|update|delete|upsert|unknown
- table_name if literal else null

TASK 4: MIGRATIONS_SURFACE.json
Extract migration runners and version tracking:
- path, line_range, symbol
- migration file lists if present
- schema_migrations table usage if present
JSON only.

## C4: Trinity boundary enforcement surfaces
Outputs
TRINITY_ENFORCEMENT_SURFACE.json
REFUSAL_AND_GUARDRAILS_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- any file containing tokens: "trinity", "boundary", "authority", "refusal", "guard", "policy"
- router/instruction injection code paths if present
- shared enforcement utilities (validators, gates)

TASK 1: TRINITY_ENFORCEMENT_SURFACE.json
Extract:
- boundary checks between planes (pm/memory/orchestrator/mcp/hooks/etc.)
- enforcement functions/classes
- any allowlist/denylist structures
Each item:
- path, line_range, symbol
- excerpt <= 35 lines
- referenced_planes[]: literal strings that look like plane names if present

TASK 2: REFUSAL_AND_GUARDRAILS_SURFACE.json
Extract:
- refusal artifacts creation
- policy evaluation
- schema validation calls
- sanitization/redaction calls
Each item:
- guard_kind: refusal|policy|validation|redaction|other
- path, line_range, symbol, excerpt <= 20 lines

JSON only.

## C5: TaskX integration surfaces
Outputs
TASKX_INTEGRATION_SURFACE.json
TASKX_PACKET_IO_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- src/** containing "taskx"
- docs are in D; here we only do code
- .taskx surfaces are Phase A/H; here link any references

TASK 1: TASKX_INTEGRATION_SURFACE.json
Extract:
- code that calls taskx CLI
- code that reads/writes task packets
- operator instruction injection/compilation calls (if present)
Each item:
- item_kind: cli_invocation|packet_read|packet_write|instruction_compile|other
- path, line_range, symbol
- excerpt <= 35 lines

TASK 2: TASKX_PACKET_IO_HINTS.json
Extract literal packet schema hints:
- json keys referenced (e.g., "objective","scope","acceptance_criteria")
- file naming conventions in code
For each hint:
- path, line_range, excerpt <= 12 lines
- keys[] or patterns[]

JSON only.

## C6: Workflow runners + multi-service coordination
Outputs
WORKFLOW_RUNNER_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- scripts/**
- tools/**
- run_all_multi_workspace_tests.sh
- verify_dopecon_bridge.sh
- start-mcp-servers.sh (also Phase A, but include call graph references here)
- tmux-dopemux-orchestrator.yaml
- any python CLIs that orchestrate services

Extract workflows:
- workflow_id
- workflow_kind: shell|python|make|tmux|compose|other
- steps[] literal commands or references
- inputs/outputs if explicitly mentioned (paths only)
- path, line_range, excerpt <= 60 lines

JSON only.

## C7: API + dashboards (backend surfaces)
Outputs
API_SURFACE.json (if not already present, regenerate deterministically)
DASHBOARD_BACKEND_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- src/**, services/**, ui-dashboard-backend/**, dashboard/**

Extract:
- http routes (FastAPI/Flask)
- request/response models referenced
- websocket endpoints
- CLI to dashboard bridges

Each route:
- method, path (literal)
- handler symbol
- path, line_range, excerpt <= 20 lines

JSON only.

## C8: Determinism / idempotency / concurrency location scans
Outputs
DETERMINISM_RISK_LOCATIONS.json
IDEMPOTENCY_RISK_LOCATIONS.json
CONCURRENCY_RISK_LOCATIONS.json
SECRETS_RISK_LOCATIONS.json (location-only)
ROLE: Mechanical scanner. No reasoning. JSON only. ASCII only.

Scan code for risk locations:

DETERMINISM:
- random, secrets, uuid
- datetime.now, time.time
- unordered iteration over dict/set without sorting
- implicit locale/timezone conversions

IDEMPOTENCY:
- UPDATE/DELETE on evidence/log tables
- retries without idempotency keys
- "upsert" behavior without stable keys
- side effects without ledger write

CONCURRENCY:
- async/await, threading, multiprocessing
- queue usage, background tasks
- locks, semaphores
- retries/backoff

SECRETS:
- reading env vars with token/key/secret names
- loading .env, secret files
- printing config values

For each hit:
- risk_type
- path, line_range
- excerpt <= 7 lines
- matched_token

JSON only.

## C9: Merge + normalize + QA
Outputs
all normalized *.json in C_code_surfaces/norm/
C_COVERAGE_REPORT.json
ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS: all raw outputs C0-C8.

MERGE RULES:
- dedupe by (path, line_range, sha256(excerpt))
- stable sort by path then start line
- ensure each normalized output includes:
  - artifact_type
  - generated_at_local
  - inputs[] (file list)
  - items[]

QA: C_COVERAGE_REPORT.json
Include:
- expected_artifacts
- present_artifacts
- missing_artifacts
- item_counts per artifact
- top_paths_by_items (top 25)

JSON only.
