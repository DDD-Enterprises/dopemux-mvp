---
id: SYSTEM_DopeMemory
title: System Dopememory
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: System Dopememory (reference) for dopemux documentation and developer workflows.
---
### 1. Purpose

dope-memory is the active chronicle service in this repository: it accepts manual and promoted activity inputs, writes curated chronological records into the canonical SQLite chronicle ledger, and serves chronicle-oriented tools over HTTP from `services/working-memory-assistant/dope_memory_main.py`. Its canonical authority slice is chronicle storage and chronicle-derived operations such as replay, recap, correction/supersession, reflections, and trajectory derived from that ledger. It is not the whole memory layer: it does not own PM truth, it does not own ConPort's structured decision/relationship memory, it does not own dope-context retrieval authority, and it does not make upstream event producers or the optional Postgres mirror authoritative. Evidence: `repo-truth-pack/dope-memory/DISCOVERY_NOTES.md`, `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/chronicle/store.py`, `services/working-memory-assistant/canonical_ledger.py`.

### 1.1 Runtime Reality

- The active dope-memory HTTP runtime is `services/working-memory-assistant/dope_memory_main.py`.
- The active service port is `3020` in `compose.yml`, `services/registry.yaml`, and `Dockerfile.dope-memory`.
- The canonical chronicle ledger resolves to `.dopemux/chronicle.sqlite` unless `DOPEMUX_CAPTURE_LEDGER_PATH` overrides it.

### 1.2 Intended / Historical

- The same tree still contains the older `working-memory-assistant` FastAPI service in `services/working-memory-assistant/main.py`, which runs on `8096` by default.
- Some adapter and client surfaces still assume the older `8096` WMA transport instead of the active dope-memory runtime.

### 1.3 Ports

- Primary API: `3020`
- Legacy adapter target: `8096` (deprecated, stale)
- Legacy WMA service default: `8096`

### 2. Core Responsibilities

- Canonical chronicle storage. `ChronicleStore` is the SQLite canonical store for dope-memory chronicle data, and `resolve_canonical_ledger()` resolves the single ledger path with fail-closed behavior. Evidence: `services/working-memory-assistant/chronicle/store.py`, `services/working-memory-assistant/canonical_ledger.py`.
- Work-log and issue-link storage. The SQLite store owns durable `work_log_entries` and `issue_links`, and the HTTP tools call into that store for append, replay, correction, issue marking, and issue-resolution linking. Evidence: `services/working-memory-assistant/chronicle/store.py`, `services/working-memory-assistant/dope_memory_main.py`.
- Raw activity ingestion as operational input. `EventBusConsumer` reads Redis stream `activity.events.v1`, stores raw activity events with TTL, promotes eligible events, and publishes derived events. This is an operational ingest path, not upstream event-source authority. Evidence: `services/working-memory-assistant/eventbus_consumer.py`, `repo-truth-pack/dope-memory/TRANSPORT_AND_RUNBOOK.md`.
- Reflection and trajectory derivation. Reflection cards and trajectory state are derived from chronicle data and stored alongside it; they are implemented by `ReflectionGenerator`, `TrajectoryManager`, and the related `/tools/*` endpoints. Evidence: `services/working-memory-assistant/reflection/reflection.py`, `services/working-memory-assistant/trajectory/manager.py`, `services/working-memory-assistant/dope_memory_main.py`.
- Optional Postgres mirror sync. `PostgresMirrorSync` performs one-way replication from SQLite to Postgres when enabled. The worker and schema explicitly describe Postgres as a mirror, not source truth. Evidence: `services/working-memory-assistant/postgres_mirror_sync.py`, `services/working-memory-assistant/chronicle/postgres_mirror.sql`.
- Tool-serving HTTP runtime. The canonical runtime entrypoint is the FastAPI app in `dope_memory_main.py`, which serves the memory tool routes on port `3020`. Evidence: `services/working-memory-assistant/dope_memory_main.py`, `repo-truth-pack/dope-memory/TRANSPORT_AND_RUNBOOK.md`.

### 3. Non-Responsibilities

- PM truth. dope-memory may hold chronicle records about PM activity, but it is not canonical for PM entities, PM status, workflow legality, or decision authority.
- WMA operational snapshot and recovery surfaces. The co-located `main.py` WMA service owns snapshot/recovery-style routes; those surfaces are not part of active dope-memory authority.
- ConPort structured decision and relationship memory. ConPort remains the structured durable context, decision, and relationship surface; dope-memory is not its replacement.
- dope-context retrieval and indexing authority. dope-memory is not the canonical code/docs retrieval or indexing plane.
- Upstream event-source authority. Redis input events are ingested as operational input; the producers of those events remain upstream authorities for what they emitted.
- Postgres mirror as source truth. The Postgres mirror is downstream replication from SQLite and must not be treated as canonical.

### 4. Key Surfaces

- Canonical runtime entrypoint. `services/working-memory-assistant/dope_memory_main.py` is the active dope-memory HTTP runtime on port `3020`. This is the runtime authority for tool serving.
- Chronicle SQLite ledger. `services/working-memory-assistant/canonical_ledger.py` resolves the canonical ledger path, and `services/working-memory-assistant/chronicle/store.py` writes and reads the authoritative SQLite chronicle store. This is the storage authority.
- HTTP `/tools/*` surface. `dope_memory_main.py` exposes `POST /tools/memory_search`, `memory_store`, `memory_recap`, `memory_mark_issue`, `memory_link_resolution`, `memory_replay_session`, `memory_correct`, `memory_generate_reflection`, `memory_reflections`, and `memory_trajectory`. This is transport, not a separate store.
- Redis stream consumption and publication. `eventbus_consumer.py` consumes `activity.events.v1` and emits `memory.derived.v1`. This is transport and operational ingestion, not storage authority.
- Postgres mirror sync. `postgres_mirror_sync.py` replicates SQLite chronicle data into Postgres mirror tables. This is a mirror, not source truth.
- Adapter and proxy surfaces. `services/dope-memory/mcp_stdio_adapter.py` is a thin adapter surface, and `src/dopemux/pm/adapters/dope_memory.py` is a client adapter to the HTTP tool surface. These are adapters, not authorities.
- Cache. No repo-proven durable cache owns dope-memory truth. Redis is used here as transport; any broader cache role for memory ownership is not established by the dope-memory runtime evidence.

### 5. System Boundaries

- working-memory-assistant. dope-memory receives co-location, shared modules, and file-system placement under `services/working-memory-assistant`, but it does not inherit WMA snapshot/recovery authority from that tree. dope-memory emits chronicle writes, replay/recap/reflection responses, and optional mirror updates. It does not control WMA `main.py` routes, WMA auth, or WMA recovery persistence.
- dopemux. dope-memory receives manual and programmatic chronicle calls from dopemux-side adapters such as `src/dopemux/pm/adapters/dope_memory.py` and capture paths that resolve the same canonical ledger. It emits chronicle receipts and chronicle query results. It does not control higher-level PM routing, workflow adjudication, or operator policy in dopemux.
- ConPort. dope-memory can record chronicle events about decisions or work, but it does not control ConPort's structured memory or relationship graph. The repo does not prove an active canonical write path from dope-memory into ConPort for authority transfer.
- dope-context. dope-memory may have aspirational or optional downstream indexing hooks, but the repo evidence does not show dope-memory controlling dope-context indexing authority. dope-memory emits chronicle-derived material at most; it does not own retrieval indexing outcomes.
- Upstream event streams. dope-memory receives raw activity envelopes from Redis streams and promotes eligible events into chronicle entries. It emits derived events on `memory.derived.v1`. It does not control upstream producers, event semantics before ingestion, or upstream source-of-truth state.
- Adapters and MCP surfaces. HTTP `/tools/*` is the active served tool surface. The stdio adapter is only an adapter layer and currently mismatches the active runtime target. Repo evidence does not prove a native `/mcp` transport in dope-memory, so operators should not treat transport assumptions as authority.

### 6. Authority Model

- Canonical: the SQLite chronicle ledger resolved by `canonical_ledger.py` and operated through `ChronicleStore`. This is the authoritative store for chronicle records.
- Canonical: the active dope-memory runtime in `dope_memory_main.py` for serving chronicle tools against that ledger.
- Derived: reflection cards, trajectory state, recap output, replay views, and any promoted summaries derived from stored chronicle data.
- Derived: the Postgres mirror. It is downstream replication from SQLite.
- Operational: Redis stream ingestion from `activity.events.v1` and publication to `memory.derived.v1`.
- Operational: the `/tools/*` HTTP transport surface used to invoke chronicle operations.
- Unknown: full top-level ownership of the broader "memory domain" beyond the chronicle slice. The repo proves overlap with WMA surfaces but does not prove a unified memory authority.
- Unknown: any claimed native MCP `/mcp` transport for dope-memory. The configuration exists, but the active runtime evidence does not show that endpoint.
- Rule: dope-memory is canonical for chronicle storage, not canonical for the full memory domain. Derived surfaces remain derived, and transport surfaces do not define authority.

### 7. Known Drift / Issues

- Runtime identity lives under the `working-memory-assistant` tree. The active dope-memory runtime is `services/working-memory-assistant/dope_memory_main.py`, while the same tree also contains the legacy WMA service in `main.py`. This creates naming and operator-boundary confusion. Evidence: `repo-truth-pack/dope-memory/DISCOVERY_NOTES.md`, `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/main.py`.
- Duplicate `DopeMemoryMCPServer` implementations exist. `dope_memory_main.py` defines the runtime class with 10 tools, while `services/working-memory-assistant/mcp/server.py` exports a separate 7-tool class that is not the active server implementation. Evidence: `repo-truth-pack/dope-memory/DRIFT_REPORT.md`, `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/mcp/server.py`.
- Adapter target mismatch: `8096` vs `3020`. `services/dope-memory/mcp_stdio_adapter.py` proxies to `http://localhost:8096/tools`, but the active dope-memory runtime is on `3020`. Evidence: `services/dope-memory/mcp_stdio_adapter.py`, `repo-truth-pack/dope-memory/TRANSPORT_AND_RUNBOOK.md`.
- Route and tool count mismatch. The active runtime exposes 10 `/tools/*` routes, but the root `GET /` listing and the shadow MCP module still describe only 7 tools. Evidence: `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/mcp/server.py`, `repo-truth-pack/dope-memory/DRIFT_REPORT.md`.
- Missing `/mcp` runtime despite transport assumptions. Repo config points some clients at `http://localhost:3020/mcp`, but `dope_memory_main.py` only exposes `/`, `/health`, and `/tools/*`. Evidence: `.claude.json`, `services/working-memory-assistant/dope_memory_main.py`, `repo-truth-pack/dope-memory/TRANSPORT_AND_RUNBOOK.md`.
- Docs must not collapse `3020` and `8096` into one surface. `3020` is current dope-memory runtime reality; `8096` is older WMA transport reality.

### 8. Working Rules

- Treat the SQLite chronicle ledger as canonical.
- Do not treat Postgres mirrors, Redis streams, adapters, or proxies as truth.
- Do not collapse dope-memory into WMA because they share a directory tree.
- Trace transport failures separately from storage-authority questions.
- Preserve `UNKNOWN` where top-level memory ownership or native MCP transport is not proven.
- When debugging drift, start from `dope_memory_main.py`, `canonical_ledger.py`, and `chronicle/store.py`, then classify other surfaces as mirror, transport, adapter, or legacy unless runtime evidence proves otherwise.
