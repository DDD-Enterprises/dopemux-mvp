---
title: "Cross-Plane Authority & Determinism Audit"
plane: "pm"
component: "dopemux"
status: "delivered"
audit_date: "2026-02-13"
audit_model: "Opus 4.6"
---

# Cross-Plane Authority & Determinism Audit

**Purpose**: Identify authority overlaps, mutation ambiguities, and determinism leaks across TaskX, task-orchestrator, dope-memory, ConPort, MCP servers, and the Investigation CLI (planned).

**Scope**: Complete analysis of which services can mutate shared state, who can promote facts, and where replay guarantees can break.

---

## SECTION 1 — Authority Map

| Component | Can Mutate Code | Can Mutate Memory | Can Promote Facts | Can Emit Artifacts | Can Execute Packets | Deterministic? |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|
| **TaskX** | YES (via runners) | NO | NO | YES (RUN_REPORT, REFUSAL_REPORT, ARTIFACT_INDEX) | YES (sole executor) | YES (INV-TX-002) |
| **task-orchestrator** | NO | YES (Redis cache, sync state) | NO (design intent) | NO | NO | NO (event-driven, async queues) |
| **dope-memory** | NO | YES (chronicle.sqlite, reflection cards, trajectory) | YES (PromotionEngine promotes raw events to work_log_entries) | NO | NO | PARTIALLY (promotion rules are deterministic; timing/ordering is not) |
| **ConPort** | NO | YES (PostgreSQL AGE: decisions, progress, patterns, custom_data, knowledge graph) | YES (log_decision creates authority records) | NO | NO | YES (PostgreSQL ACID) |
| **dopecon-bridge** | NO | YES (PostgreSQL AGE graph writes, Redis event streaming, Qdrant vectors) | UNKNOWN (pattern detection may create AGE nodes) | NO | NO | NO (event-driven, pattern detection heuristics) |
| **MCP servers (PAL, Serena, Dope-Context, etc.)** | NO (read-only analysis) | PARTIALLY (Serena: Redis cache; Dope-Context: Qdrant vectors) | NO | NO | NO | YES (stateless per-request) |
| **Investigation CLI (planned)** | NO (design: read-only meta-layer) | UNKNOWN (not yet implemented) | NO (design intent) | UNKNOWN | NO | N/A (not implemented) |
| **Supervisor (Claude Code / dmux)** | YES (via TaskX) | YES (via ConPort MCP, dope-memory MCP) | YES (decides what to promote via INV-MEM-004) | YES (creates packets) | NO (delegates to TaskX) | NO (LLM-based decisions) |

---

## SECTION 2 — Mutation Surface Analysis

### 2.1 Shared State Mutation Points

| # | Service | Target | Mutation Path | Classification |
|---|---------|--------|---------------|----------------|
| M1 | task-orchestrator | Redis (db 0 + db 4) | `RedisManager.cache_set()`, sync engine health writes, conflict resolution writes, coordination metrics | **RISK** — Multiple Redis DBs written without transactional guarantees |
| M2 | task-orchestrator | ConPort (via HTTP adapter) | `ConPortEventAdapter` logs decisions, progress, patterns to ConPort port 3004 | **RISK** — task-orchestrator can write decisions to ConPort, potentially bypassing Supervisor authority |
| M3 | task-orchestrator | Leantime (via JSON-RPC) | `LeantimeClient.update_ticket_status()`, sync engine writes | **SAFE** — Mechanical sync, no policy decisions |
| M4 | dope-memory | chronicle.sqlite | `ChronicleStore.insert_work_log_entry()`, `insert_corrected_work_log_entry()`, `insert_reflection_card()` | **SAFE** — Append-only with supersession chain, not UPDATE/DELETE |
| M5 | dope-memory | chronicle.sqlite | `cleanup_expired_raw_events()` in retention job | **RISK** — DELETE operation on raw events violates spirit of INV-MEM-003 (though technically on "raw" not "promoted" entries) |
| M6 | ConPort | PostgreSQL AGE | `log_decision`, `log_progress`, `log_system_pattern`, `update_active_context`, `link_conport_items` | **SAFE** — Designed as authority store |
| M7 | dopecon-bridge | PostgreSQL AGE + Qdrant + Redis | Event processing, pattern detection, graph node creation | **CRITICAL** — Can create nodes/edges in the same PostgreSQL AGE database as ConPort without going through ConPort's API. Shared database = shared mutation surface |
| M8 | dope-memory EventBus consumer | chronicle.sqlite | Automatically promotes events from `activity.events.v1` Redis stream | **RISK** — Autonomous promotion without Supervisor oversight |
| M9 | dope-memory | Postgres (mirror sync) | `PostgresMirrorSync` writes chronicle data to PostgreSQL when `ENABLE_MIRROR_SYNC=true` | **RISK** — Writes to shared PostgreSQL, potential collision with ConPort tables |
| M10 | task-orchestrator | ConPort (via sync engine) | `_sync_leantime_to_conport()` calls `conport_client.log_progress()` | **CRITICAL** — Mechanical sync process autonomously creates ConPort progress entries |

### 2.2 TaskX Bypass Paths

| # | Bypass Path | Classification |
|---|-------------|----------------|
| B1 | task-orchestrator `/api/tools/{tool_name}` endpoint executes any of 37 MCP tools directly | **CRITICAL** — 37 MCP tools executable via HTTP, bypassing TaskX entirely |
| B2 | task-orchestrator `/api/decompose` calls PAL planner (LLM) directly | **RISK** — LLM call from coordination layer without TaskX packet |
| B3 | dope-memory EventBus consumer processes events autonomously | **SAFE** — Memory ingestion, not code execution |
| B4 | genetic-agent calls PAL and ConPort directly | **RISK** — AI code repair without TaskX mediation |
| B5 | Any service with ConPort URL can `log_decision` directly | **RISK** — No gatekeeper on who creates authority records |

### 2.3 Memory Write Paths (Who Can Write Where)

| Writer | ConPort (PostgreSQL AGE) | chronicle.sqlite | Redis | Qdrant |
|--------|:-:|:-:|:-:|:-:|
| Supervisor (Claude Code) | YES (via MCP) | NO (no direct access) | NO | NO |
| task-orchestrator | YES (via adapter) | NO | YES (3 DBs) | NO |
| dope-memory | NO | YES (sole writer) | YES (EventBus) | NO |
| ConPort server | YES (sole API) | NO | YES (cache) | YES (semantic) |
| dopecon-bridge | YES (direct DB!) | NO | YES (EventBus) | YES (vectors) |
| genetic-agent | YES (via ConPort) | NO | NO | NO |
| adhd-engine | NO | NO | YES (session) | NO |

### 2.4 Promotion Trigger Analysis

| # | Who Triggers | What Is Promoted | Classification |
|---|-------------|-----------------|----------------|
| P1 | dope-memory EventBus consumer | Raw events → work_log_entries via PromotionEngine | **RISK** — Autonomous, deterministic rules but no Supervisor approval |
| P2 | dope-memory `memory_store` (manual) | Direct MCP call creates work_log_entry | **SAFE** — Explicit user/Supervisor action |
| P3 | dope-memory `memory_correct` | Supersession creates new entry marking old as superseded | **SAFE** — Append-only correction chain |
| P4 | ConPort `log_decision` | Creates authoritative decision record | **SAFE** — Designed purpose |
| P5 | task-orchestrator sync engine → ConPort | Syncs Leantime data as ConPort progress entries | **CRITICAL** — Mechanical sync creates authority records without human review |

---

## SECTION 3 — Determinism Leak Analysis

### Leak 1: Out-of-Order Event Processing
**Component**: task-orchestrator event processor + dope-memory EventBus consumer
**Scenario**: Both consume from Redis streams. Event A (decision made) and Event B (task completed) arrive. task-orchestrator processes B before A due to async queue ordering. dope-memory processes A before B. ConPort and chronicle.sqlite now have different event orderings.
**Impact**: Replay divergence — replaying ConPort gives different narrative than replaying chronicle.sqlite.
**Classification**: **CONFIRMED LEAK**

### Leak 2: Double-Promotion via Parallel Paths
**Component**: dope-memory EventBus consumer + task-orchestrator sync engine
**Scenario**: A `task.completed` event fires on the EventBus. Simultaneously:
1. dope-memory consumer promotes it to a work_log_entry in chronicle.sqlite
2. task-orchestrator's sync engine detects the Leantime status change and creates a ConPort progress entry

Result: The same logical event creates two separate authority records in two different stores, with no cross-reference.
**Impact**: Double-counting in reports, divergent state between memory systems.
**Classification**: **CONFIRMED LEAK**

### Leak 3: Non-Idempotent Sync Writes
**Component**: task-orchestrator `MultiDirectionalSyncEngine`
**Scenario**: Sync operation fails, gets retried via `_delayed_retry()`. Between failure and retry, the target system processed a different update. The retry applies stale data over fresh data.
**Evidence**: `sync.py:296-301` — retry re-queues the original `SyncOperation` with original `source_data`, not refreshed data.
**Impact**: Data regression — fresher state overwritten by stale retry.
**Classification**: **CONFIRMED LEAK**

### Leak 4: Retention Job Violates Append-Only
**Component**: dope-memory `run_retention_job()`
**Scenario**: `cleanup_expired_raw_events()` DELETEs rows from the chronicle database. If a promotion was in-flight referencing a raw event ID, the provenance chain breaks.
**Evidence**: `dope_memory_main.py:887-910` — deletes expired raw events on a timer.
**Impact**: Broken provenance chain (INV-MEM-004 violation) — promoted entries reference deleted source events.
**Classification**: **CONFIRMED LEAK** (partial — only raw events, not promoted entries)

### Leak 5: DopeconBridge Direct Database Access
**Component**: dopecon-bridge
**Scenario**: DopeconBridge writes directly to PostgreSQL AGE using `POSTGRES_URL`. ConPort also writes to the same database. Neither coordinates with the other. A dopecon-bridge pattern detection creates an AGE graph node at the same moment ConPort creates a conflicting node.
**Evidence**: `compose.yml:356-359` — dopecon-bridge has `POSTGRES_URL` pointing to same `dopemux_knowledge_graph` database.
**Impact**: Graph corruption, inconsistent knowledge graph state.
**Classification**: **CONFIRMED LEAK**

### Leak 6: Event Queue Overflow Drops Events
**Component**: task-orchestrator `PlaneCoordinator`
**Scenario**: `event_queue` has `maxsize=10`. When more than 10 events arrive before processing, `put_nowait()` raises `QueueFull` and the event is silently dropped.
**Evidence**: `coordinator.py:320` — `logger.warning("Event queue full, dropping event")`.
**Impact**: Lost coordination events, divergent state between planes.
**Classification**: **CONFIRMED LEAK**

---

## SECTION 4 — Boundary Violations

### Q1: Could task-orchestrator become an accidental executor?

**ANSWER: YES — IT ALREADY HAS**

**Evidence**:
1. `task_orchestrator/app.py:113-134` — `/api/tools/{tool_name}` endpoint executes any of 37 MCP tools via HTTP. This is direct tool execution, not coordination.
2. `task_orchestrator/app.py:137-188` — `/api/decompose` endpoint calls PAL planner (LLM) to decompose tasks and persists results to ConPort and Leantime. This is policy execution (deciding how to break down tasks).
3. `coordinator.py:239-248` — `coordinate_operation()` handles `create_task`, `update_progress`, `log_decision`. The "coordination" operations actually CREATE state (new tasks, new decisions), not just route events.
4. `core.py:228` — `get_pal_client()` creates a direct connection to PAL (LLM reasoning). A "coordination-only" layer should not have an LLM client.

**Severity**: INV-TX-006 VIOLATED. task-orchestrator is both coordinator AND executor.

### Q2: Could MCP servers become hidden execution paths?

**ANSWER: PARTIALLY — THROUGH TASK-ORCHESTRATOR**

**Evidence**:
1. task-orchestrator's `/api/tools/{tool_name}` endpoint makes any MCP tool callable over HTTP without going through TaskX. Any service that can reach port 8000 can execute MCP tools.
2. genetic-agent directly calls PAL (port 3003) and ConPort (port 3004) for "AI code repair" — this is code mutation via MCP without TaskX.
3. However, pure MCP servers (Serena, Dope-Context, PAL) are read-only analyzers and cannot mutate code on their own.

**Severity**: MODERATE. The MCP servers themselves are not execution paths, but the HTTP facades (especially task-orchestrator) create indirect execution paths.

### Q3: Could dope-memory elevate unverified state?

**ANSWER: YES**

**Evidence**:
1. `eventbus_consumer.py:58-66` — `HIGH_SIGNAL_EVENTS` are automatically promoted without verification. The PromotionEngine applies deterministic rules but does not verify that the event actually happened (e.g., a `task.completed` event could be fabricated by any Redis publisher).
2. `dope_memory_main.py:887-910` — Retention job deletes the raw events that serve as provenance for promoted entries. After deletion, there's no way to verify whether a promoted entry was legitimate.
3. No authentication on the EventBus — any service connected to `redis-events:6379` can publish to `activity.events.v1` stream and have events promoted into the chronicle.

**Severity**: HIGH. dope-memory trusts all EventBus publishers implicitly.

### Q4: Could Investigation CLI bypass deterministic execution?

**ANSWER: CANNOT ASSESS — NOT IMPLEMENTED**

The Investigation CLI is described as a "CLI-only meta-layer" in design documents. Since no code exists, the boundary cannot be verified. The risk depends entirely on implementation.

**Recommended Constraint**: Investigation CLI MUST be read-only. It MUST NOT write to any shared store (ConPort, chronicle.sqlite, Redis streams). It MAY write only to its own isolated analysis files.

---

## SECTION 5 — Required Invariants

### INV-CROSS-001: Single Authority Writer per Store

**Statement**: Each persistent store MUST have exactly ONE service authorized to write to it. No shared database access across service boundaries.
**Scope**: system-wide
**Enforcement Surface**: Docker network policies, database user permissions, connection string audits.
**Failure Mode**: Graph corruption when dopecon-bridge and ConPort both write to `dopemux_knowledge_graph`. Data inconsistency when dope-memory mirror-sync writes to shared PostgreSQL.
**Detection**: `SELECT DISTINCT application_name FROM pg_stat_activity WHERE datname='dopemux_knowledge_graph'` — should show exactly one writer service.
**Recovery**: Designate ConPort as sole writer to PostgreSQL AGE. DopeconBridge must write via ConPort API, not direct DB access.

### INV-CROSS-002: Coordination Layer Purity

**Statement**: task-orchestrator MUST NOT execute MCP tools, call LLMs, or create authority records. It MAY only route events, present conflicts, and expose coordination state.
**Scope**: task-orchestrator service
**Enforcement Surface**: Code audit — no imports of PAL client, no `/api/tools/` execution endpoint, no `log_decision` calls.
**Failure Mode**: Policy leak (INV-TX-006 violation). Coordination layer makes decisions that should belong to Supervisor.
**Detection**: `grep -r "pal_client\|log_decision\|handle_tool_call" services/task-orchestrator/` — must return zero matches outside test files.
**Recovery**: Extract tool execution, LLM calls, and decision logging into Supervisor layer. task-orchestrator retains only event routing and sync.

### INV-CROSS-003: EventBus Publisher Authentication

**Statement**: Only authenticated services MAY publish to `activity.events.v1` Redis stream. Each event MUST carry a `source_service` field matching the publisher's registered identity.
**Scope**: redis-events
**Enforcement Surface**: Redis ACL per-service, event schema validation in consumers.
**Failure Mode**: Fabricated events promoted into chronicle, creating hallucinated history.
**Detection**: Consumer validates `source_service` against allowlist. Unknown publishers trigger alert.
**Recovery**: Reject events from unknown publishers. Quarantine promoted entries whose source events fail validation.

### INV-CROSS-004: Idempotent Sync Operations

**Statement**: Every sync operation MUST be idempotent. Re-executing a sync operation with the same `operation.id` MUST produce the same result. Retry MUST refresh source data before application.
**Scope**: task-orchestrator sync engine
**Enforcement Surface**: Idempotency key in every `SyncOperation`. Target system checks for existing operation ID before applying.
**Failure Mode**: Stale retries overwrite fresh data (Leak 3).
**Detection**: Monitor for sync operations where `source_data` timestamp is older than target's `last_modified`.
**Recovery**: Abort stale retry. Re-fetch source data. Apply only if still newer than target.

### INV-CROSS-005: Promotion Requires Source Existence

**Statement**: A promoted entry MUST NOT exist without a corresponding verifiable source event. If the raw event is deleted (retention), the promoted entry MUST retain sufficient provenance metadata to stand alone.
**Scope**: dope-memory
**Enforcement Surface**: `PromotedEntry` dataclass requires non-null `source_event_id`, `source_event_type`, `source_adapter`, `source_event_ts_utc`, `promotion_rule` fields.
**Failure Mode**: Orphaned promoted entries with no traceable origin (INV-MEM-004 violation after retention).
**Detection**: Query: `SELECT id FROM work_log_entries WHERE source_event_id IS NULL OR source_event_type IS NULL` — must return zero rows.
**Recovery**: Backfill provenance from EventBus stream history (if retained) or mark entries as `provenance_degraded`.

### INV-CROSS-006: No Cross-Plane Event Loops

**Statement**: An event handler MUST NOT emit an event that can trigger itself (directly or through a chain of handlers). The coordination event graph MUST be a DAG.
**Scope**: task-orchestrator event processing
**Enforcement Surface**: Event correlation IDs. Handler checks if `correlation_id` already processed. Max event chain depth of 5.
**Failure Mode**: Infinite event loop — handler A emits event → handler B processes → emits event → handler A processes again.
**Detection**: `coordinator.py:374-384` — `_process_coordination_event` emits a `SYNC_COMPLETED` event after processing any event. If a handler listens for `SYNC_COMPLETED`, it creates a loop. **This is a live risk.**
**Recovery**: Add cycle detection in `_emit_event()`. Track `correlation_id` history. Refuse to process if same correlation_id seen more than 5 times.

### INV-CROSS-007: Worktree-Scoped Memory Access

**Statement**: dope-memory workspace_id MUST be validated against the caller's actual worktree. A caller in worktree A MUST NOT be able to read or write worktree B's chronicle.
**Scope**: dope-memory
**Enforcement Surface**: `workspace_id` parameter validation against request origin. `canonical_ledger.py` resolves workspace-specific DB path.
**Failure Mode**: Cross-worktree contamination (INV-MEM-001 violation via the memory plane).
**Detection**: Audit dope-memory requests — `workspace_id` must match the service's `DOPE_MEMORY_WORKSPACE_ID` or be validated against the request's origin workspace.
**Recovery**: Reject requests with mismatched workspace_id. Log violation.

### INV-CROSS-008: Redis Stream Separation

**Statement**: Event streams (`activity.events.v1`, `memory.derived.v1`) MUST use dedicated Redis instance (`redis-events:6379`). Caching operations MUST use separate Redis instance (`redis-primary`). No service may cross-read between event and cache Redis instances for state derivation.
**Scope**: system-wide
**Enforcement Surface**: Service environment variables — `REDIS_URL` for events vs cache must point to different instances.
**Failure Mode**: Cache expiry causes event loss, or event stream pollution affects cache behavior.
**Detection**: Audit service configs — verify `redis-events` used only for streams, `redis-primary` only for caching.
**Recovery**: Already enforced by compose.yml (two Redis instances). Validate no service connects to both for the same purpose.

### INV-CROSS-009: Deterministic Promotion Rules Only

**Statement**: dope-memory Phase 1 promotion MUST use only deterministic rules (pattern matching, threshold comparison). No LLM calls in the promotion path. LLM-assisted promotion is deferred to Phase 2+ with explicit Supervisor approval.
**Scope**: dope-memory PromotionEngine
**Enforcement Surface**: `promotion.py` imports — no LLM client imports. `PROMOTABLE_EVENT_TYPES` is a frozen set. `IMPORTANCE_SCORES` is a static dict.
**Failure Mode**: Non-deterministic promotion — same event promoted differently on different runs.
**Detection**: Code audit — `grep -r "openai\|anthropic\|litellm" services/working-memory-assistant/promotion/` must return zero.
**Recovery**: Strip any LLM calls from promotion path. Gate LLM-assisted promotion behind explicit feature flag with Supervisor approval.

### INV-CROSS-010: Packet Execution Exclusivity

**Statement**: TaskX is the SOLE service that may execute code-modifying operations. No other service (task-orchestrator, genetic-agent, MCP servers) may modify source code files in the workspace.
**Scope**: system-wide
**Enforcement Surface**: File system permissions — only TaskX's runner process has write access to workspace source files. Docker volume mounts — only TaskX container mounts the workspace as read-write.
**Failure Mode**: Unaudited code changes — genetic-agent or task-orchestrator modifies files without a packet, breaking audit trail.
**Detection**: File change monitoring — any workspace file modification not associated with an active TaskX packet is flagged.
**Recovery**: Revert unauthorized modifications via git. Investigate which service made the change. Restrict volume mount permissions.

---

## SECTION 6 — Architectural Simplification Opportunities

### S1: Merge dopecon-bridge INTO ConPort

**Current state**: dopecon-bridge writes directly to the same PostgreSQL AGE database as ConPort. It also reads from Redis events and writes to Qdrant.
**Problem**: Two writers to one database (INV-CROSS-001 violation). Pattern detection logic is tightly coupled to the knowledge graph schema.
**Proposal**: Make dopecon-bridge's pattern detection a module WITHIN ConPort. ConPort becomes the sole writer to PostgreSQL AGE.
**Impact**: Eliminates Leak 5 (shared database writes). Reduces one Docker container. Simplifies dependency graph.
**Effort**: MEDIUM — Extract dopecon-bridge pattern detection into ConPort module.

### S2: Strip Execution from task-orchestrator

**Current state**: task-orchestrator has 37 MCP tools, PAL client, ConPort adapter, task decomposition. It is both coordinator and executor.
**Problem**: INV-TX-006 violation. Policy leak. Hidden execution path.
**Proposal**: Remove `/api/tools/{tool_name}`, `/api/decompose`, PAL client, and direct ConPort writes. task-orchestrator becomes a pure event router and sync engine.
**Impact**: Enforces INV-TX-006 and INV-CROSS-002. Clarifies authority boundaries.
**Effort**: HIGH — Significant code extraction. Decompose endpoint needs new home (Supervisor or separate service).

### S3: Make ConPort the SOLE Decision Authority Writer

**Current state**: task-orchestrator, genetic-agent, dopecon-bridge, and Supervisor all write decisions/progress to ConPort.
**Problem**: Multiple writers can create conflicting or duplicate authority records.
**Proposal**: Only Supervisor may call `log_decision`. Other services submit decision PROPOSALS to a queue; Supervisor reviews and persists.
**Impact**: Single-owner authority (INV-CROSS-001). Cleaner audit trail.
**Effort**: MEDIUM — Add proposal queue, modify service adapters.

### S4: Eliminate Dual Memory Systems

**Current state**: ConPort stores decisions/progress in PostgreSQL AGE. dope-memory stores work_log_entries in chronicle.sqlite. Both represent "what happened" with different schemas and semantics.
**Problem**: Double-promotion (Leak 2). Divergent state. Confusion about which is authoritative for what.
**Proposal**: Define clear boundary:
- **ConPort**: Authority records (decisions, formal progress, knowledge graph relationships). Written by Supervisor only.
- **dope-memory**: Temporal chronicle (session replay, working context, ADHD accommodations). Written by EventBus consumer and MCP tools.
- **Rule**: dope-memory NEVER creates ConPort-equivalent records. ConPort NEVER stores raw event streams.
**Impact**: Eliminates double-promotion. Clear authority boundaries.
**Effort**: LOW — Mostly documentation and constraint enforcement, minimal code change.

### S5: Collapse Two Redis Instances into One with Logical Separation

**Current state**: `redis-events` (EventBus streaming) and `redis-primary` (caching) are separate containers.
**Problem**: Operational overhead of two Redis instances. Some services connect to both.
**Proposal**: Use a single Redis instance with database number separation (db 0 = cache, db 1 = events, db 4 = sync). Use Redis ACLs for access control.
**Impact**: Simpler infrastructure. One less container. Still maintains logical separation.
**Effort**: LOW — Change `REDIS_URL` environment variables. Add ACLs.
**Risk**: Single point of failure for both cache and events. Keep if isolation is critical.

### S6: Remove genetic-agent from Core Stack

**Current state**: genetic-agent is an "AI Code Repair" service that directly calls PAL and ConPort. It operates outside TaskX's execution model.
**Problem**: Violates INV-TX-008 (no self-directed LLM calls for code mutation) and INV-CROSS-010 (packet execution exclusivity).
**Proposal**: If genetic-agent is needed, it must operate AS a TaskX runner, not as an independent service. Supervisor creates a packet specifying genetic repair; TaskX executes the genetic-agent as a runner.
**Impact**: Brings genetic repair under audit trail. Enforces packet-based execution.
**Effort**: MEDIUM — Refactor genetic-agent as a TaskX runner plugin.

---

## Summary of Critical Findings

| Finding | Severity | Invariant Violated |
|---------|----------|-------------------|
| task-orchestrator executes MCP tools and calls LLMs | CRITICAL | INV-TX-006 |
| dopecon-bridge writes directly to ConPort's PostgreSQL | CRITICAL | INV-CROSS-001 (new) |
| task-orchestrator sync engine creates ConPort authority records autonomously | CRITICAL | INV-CROSS-002 (new) |
| Double-promotion of events to both chronicle.sqlite and ConPort | HIGH | INV-CROSS-005 (new) |
| Non-idempotent sync retries can overwrite fresh data | HIGH | INV-CROSS-004 (new) |
| Event queue drops events silently at capacity | HIGH | INV-CROSS-006 (new) |
| No EventBus publisher authentication | HIGH | INV-CROSS-003 (new) |
| Retention job deletes raw events, breaking provenance chains | MEDIUM | INV-MEM-003 / INV-MEM-004 |
| `\|\| exit 0` healthchecks mask server failures | MEDIUM | INV-MCP-006 |
| genetic-agent operates outside packet model | MEDIUM | INV-TX-008, INV-CROSS-010 |

---

## Audit Completion

**Audit Date**: 2026-02-13
**Audit Model**: Opus 4.6
**Scope**: Full codebase analysis (compose.yml, task-orchestrator, dope-memory, dopecon-bridge, documentation)
**Status**: DELIVERED

This audit identified 10 critical/high-severity invariant violations across the cross-plane architecture. Immediate action required on Sections 2.1, 3.0, and 4.1.

Next steps: Review findings, prioritize fixes per severity, and implement INV-CROSS-001 through INV-CROSS-010 enforcement.
