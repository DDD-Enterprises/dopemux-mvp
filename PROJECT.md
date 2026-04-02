# PROJECT

## 1. Purpose

This repository is a multi-system operator and runtime workspace for dopemux development.

It is centered on the `dopemux` CLI as the operator entrypoint, but the repository is not just a CLI package. The inspected code, compose wiring, and service registry show a wider development-control stack that includes external task execution handoff, PM-plane coordination, structured context and decision storage, chronicle-style memory, retrieval/indexing, bridge/proxy routing, ADHD-oriented operator support, and repo-truth extraction.

This document is a repo-truth project description, not a design brief. It describes the repository as observed in runtime code, config, tests, and current truth-aligned reference docs. It does not assume a clean unified platform where the repo shows fragmentation, drift, or split authority.

## 2. What This Project Is

In this checkout, the project is best described as a composed workspace of cooperating systems rather than a single application.

The strongest project-level pattern is:

- `dopemux` is the operator control surface
- `dopetask` is the external execution engine reached through repo wrappers
- PM behavior is composed across Leantime, task-orchestrator, ConPort, dope-memory mirrors, and dopemux PM adapters
- memory and retrieval are split across dope-memory, ConPort, and dope-context rather than unified
- dopecon-bridge is an operational connector and compatibility layer, not a truth owner
- repo-truth-extractor is a separate audit and extraction subsystem, not the primary operator control surface

This means the repository supports real operational workflows, but it does not prove a single integrated architecture with one canonical owner for PM, memory, retrieval, execution, and agents.

## 3. Project Scope

The scope proven by the inspected repository includes:

- operator control and local startup through the `dopemux` package and CLI entrypoints in `pyproject.toml` and `src/dopemux/cli.py`
- execution handoff through `scripts/taskx` to `scripts/dopetask`, which installs and executes the pinned external `dopetask` CLI
- PM-plane read/write normalization through `src/dopemux/pm/*` and workflow-serving runtime surfaces in `services/task-orchestrator/app/*`
- PM metadata and project snapshot integration through Leantime-facing adapters and JSON-RPC clients
- structured decision, progress, context, and custom-data surfaces through ConPort runtime and clients
- chronicle and evidence-preserving history through dope-memory under `services/working-memory-assistant/dope_memory_main.py`
- retrieval and indexing for code and documents through dope-context under `services/dope-context/src/mcp/server.py`
- bridge, proxy, and compatibility routing through dopecon-bridge under `services/dopecon-bridge/dopecon_bridge`
- ADHD/operator support through `services/adhd_engine`
- repo-truth extraction and auditing through `services/repo-truth-extractor`, with `run_extraction_v5.py` as the strongest extraction runtime authority in this repo

The repository does not prove that all of those scopes are fully aligned, consistently packaged, or cleanly bounded. It does prove that they coexist and interact.

## 4. Major Systems

### dopemux

`dopemux` is the main operator-facing control layer. It owns command registration, startup behavior, MCP/server coordination, routing mode management, workspace configuration updates, and delegation into downstream systems.

It does not own canonical PM truth, durable memory truth, retrieval source truth, or a unified agent runtime.

### dopetask

`dopetask` is the external execution engine reached through `scripts/taskx` and then `scripts/dopetask`. In this repository the wrapper chain is local; the execution engine itself is not implemented here as repo source.

It does not own PM metadata, PM workflow legality, memory authority, retrieval authority, or CLI orchestration.

### task-orchestrator

task-orchestrator is the workflow-coordination and PM-transition service surface. It serves workflow queue, blockers, workflow state, transitions, workflow CRUD-like surfaces for ideas and epics, and PM write routes that call the shared dopemux PM logic.

Its authority slice is narrow. It does not own passive PM metadata, ConPort decision/progress truth, dope-memory chronicle truth, or a task-orchestrator-local workflow database in the inspected path.

### Leantime

Leantime is the strongest observed PM metadata and project/ticket snapshot target in the dopemux PM layer. Passive work-item metadata updates and sprint/project snapshot reads route there through adapters and JSON-RPC clients.

The repo does not prove Leantime as the owner of workflow legality, ConPort-style decision/progress context, or chronicle history.

### ConPort

ConPort is the structured context, decision, progress, and custom-data surface. In the PM layer it is used for project context and decision/progress logging. More broadly it is a structured memory and query surface with its own runtime under the Docker ConPort sources.

It does not own passive PM metadata, canonical workflow transition legality, dope-memory chronology, or dope-context retrieval authority.

### dope-memory

dope-memory is the durable chronicle and evidence-preserving memory sink. The active runtime is `services/working-memory-assistant/dope_memory_main.py`, and the strongest storage authority is the SQLite chronicle ledger.

It does not own PM entity truth, workflow legality, or ConPort’s structured decision/progress domain.

### dope-context

dope-context is the code-and-document retrieval and indexing service. It creates derived indexes and serves retrieval over MCP and HTTP.

It does not own PM truth, memory truth, chronicle truth, or the source truth of the code and documents it returns.

### dopecon-bridge

dopecon-bridge is an adapter, proxy, and routing layer. It exposes PM-safe routing, ConPort proxy routes, event publication, and compatibility surfaces used by multiple systems.

It does not own canonical task, workflow, decision, or progress authority, even where it proxies or stores PM-adjacent data.

### ADHD Engine

The ADHD Engine is an operator-support and cognitive-state service with API and MCP-style surfaces related to workload, accommodation, context, and task support.

It does not own PM truth, dope-memory chronicle truth, or ConPort authority.

### Repo-Truth-Extractor

Repo-Truth-Extractor is the extraction and audit subsystem. `services/repo-truth-extractor/run_extraction_v5.py` is the strongest runtime authority for that family in this checkout.

It does not own the operator runtime or the PM plane. It owns extraction and evidence generation for repo-truth work.

## 5. Current Operating Model

The observed operating model is split rather than unified.

Operators enter through `dopemux`. That CLI handles startup, routing, MCP/server coordination, environment export, and other local control behavior. When the kernel execution path is used, `dopemux` delegates to `scripts/taskx`, which is only a compatibility shim, and execution continues through `scripts/dopetask` into the external `dopetask` binary.

PM behavior is split by concern. `src/dopemux/pm/writes.py` routes passive PM metadata to Leantime, workflow-significant transitions to task-orchestrator, and structured decision/progress logging to ConPort, with dope-memory receiving mirrored historical receipts. `src/dopemux/pm/reads.py` also splits read authority by concern rather than treating PM as one backend. `docs/03-reference/planes/PM_PLANE.md` should be read as a project-level constraint, not a subsystem detail.

Memory and retrieval are also split. ConPort is the structured decision/progress/context surface. dope-memory is the chronicle and evidence sink. dope-context is the retrieval/indexing surface. They interact, but the repo does not prove a single memory or context owner that collapses them into one layer.

Bridge and adapter layers connect the systems but are not canonical owners. dopecon-bridge is operationally important and task-orchestrator itself depends on bridge-mediated storage for workflow records, yet the bridge is still not the owner of PM truth.

## 6. Authority Split

Project-level authority is distributed by function:

- operator control and startup behavior: `dopemux`
- execution after handoff: external `dopetask` via `scripts/dopetask`
- PM metadata and project/ticket snapshot surfaces: Leantime, via repo adapters and JSON-RPC clients
- PM workflow-significant transitions and workflow views: task-orchestrator
- structured decisions, progress, project context, and custom data: ConPort
- historical receipts and chronology: dope-memory
- retrieval and indexing: dope-context
- routing, transport, proxying, and compatibility glue: dopecon-bridge
- cognitive/operator support: ADHD Engine
- repo-truth extraction and audit artifacts: Repo-Truth-Extractor

Some authority remains unresolved:

- task-orchestrator runtime packaging and startup authority are split between `app/main.py`, the hard-failing legacy runtime path, and Docker wiring
- ConPort access in the PM layer is split across `3004` and `3005` contracts
- the broader memory owner outside the dope-memory chronicle slice remains `UNKNOWN`
- agent authority across the repo remains `UNKNOWN`

## 7. Repo Shape

In practical terms, the repository is shaped as a mixed workspace:

- root-level operator and control files such as `AGENTS.md`, `PROJECT.md`, compose files, the service registry, and truth artifacts
- `src/dopemux` for the main CLI package, PM normalization helpers, routing/configuration, MCP control, and operator tooling
- `services/*` for the major service families, including task-orchestrator, dopecon-bridge, dope-context, working-memory-assistant/dope-memory, ADHD Engine, and repo-truth-extractor
- `docker/*` for compose support and container build/runtime sources, including active MCP server source trees
- `docs/03-reference/*` for current reference documents
- `docs/03-reference/truth/*`, `tmp/dmx-chatgpt-project-truth-extraction-002/*`, and related generated truth artifacts for prior extraction outputs

This is not a single-package codebase and not a single-service repo. It is a mixed CLI, services, compose, adapters, and generated-artifact workspace.

## 8. Known Drift / Issues

- PM authority is intentionally split. That is current reality, but it also means the repo does not offer one PM owner.
- task-orchestrator runtime authority is conflicted. `services/task-orchestrator/app/main.py` is the strongest runtime code authority, while Docker and legacy runtime paths still disagree on launch path and effective port.
- dopecon-bridge exposes broad PM, KG, and coordination surfaces, which makes it easy to mistake for an authority layer even though the active runtime explicitly rejects that role.
- dope-memory and working-memory-assistant naming and transport surfaces overlap. The active dope-memory runtime lives under the working-memory-assistant tree and older surfaces still remain beside it.
- ConPort runtime and access patterns are split across at least HTTP and MCP-facing ports and multiple client assumptions. The PM layer itself uses more than one ConPort contract.
- TaskX versus dopetask naming drift remains in scripts, command labels, tests, and older docs even though `scripts/taskx` is only a shim.
- repo-truth extraction has a legacy-versus-current split. The extractor service and command family point to the v5 runner, but `dopemux` still exposes legacy `PipelineRunner`-based truth flows.
- authority docs are present but pathing is still uneven. The exact `docs/03-reference/SYSTEM_BOUNDARIES.md` path requested in earlier packets is absent, while `docs/03-reference/systems/system-boundaries.md` and bundled boundary docs exist.
- agent authority remains unresolved across multiple agent families in the repo.

## 9. Working Rules

- Trust runtime code, config, tests, compose wiring, and active entrypoints over older prose.
- Describe the repository as a composed workspace, not as a clean unified platform.
- Do not treat bridge, proxy, adapter, wrapper, or mirror layers as canonical authority unless runtime code explicitly makes them so.
- Preserve `UNKNOWN` where the repository does not resolve ownership cleanly.
- Do not collapse PM, memory, retrieval, execution, and agents into one system.
- When reasoning about execution, trace the actual delegation path: `dopemux` to `scripts/taskx` to `scripts/dopetask` to the external `dopetask` binary.
- When reasoning about PM, classify the read or write type first, then locate the authority for that slice.
- When reasoning about memory or retrieval, keep ConPort, dope-memory, and dope-context distinct unless the specific code path proves otherwise.
