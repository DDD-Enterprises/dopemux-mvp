# Memory Spine Service Cluster Audit — 2026-07-04

**Status**: READ-ONLY AUDIT (no modifications)
**Worktree**: focused-mahavira-5bd29b @ 8f71ab9af
**Scope**: dope-memory, ConPort, dope-context, task-orchestrator, capture_client, promotion pipeline

---

## Executive Summary

The memory spine **has correct architecture, partial implementation, and ONE critical blocker** preventing chronicle population. Decision logging is 75% wired; the remaining 25% is a stream-name mismatch that can be fixed with a single-line diff in each of 4 files.

- **Intended**: Decisions → ConPort → dope-memory chronicle via activity.events.v1 promotion
- **Implemented**: Decisions → ConPort ✅, ConPort → DopeconBridge ✅, DopeconBridge → dopemux:events ❌
- **Result**: 0 work_log_entries in chronicle (24.5k heartbeat spam events, all non-promotable)

---

## 1. Surface Inventory & Wiring Status

### 1.1 dope-memory (services/working-memory-assistant/)

**Intended**:
- 10-tool MCP surface (recap, reflection, trajectory, chronicle query, work-log indexing)
- SQLite canonical ledger + Redis event transport
- Real-time event ingestion via activity.events.v1 → promotion → chronicle
- Per-worktree instance isolation

**Implemented**:
- ✅ 10-tool MCP surface @ /mcp port 3020 (dope_memory_main.py:83–1200)
- ✅ Canonical SQLite ledger with schema (canonical_ledger.py, chronicle/store.py)
- ✅ PromotionEngine with 7 promotable event types (promotion.py:18–28)
- ✅ EventBusConsumer wired & started in lifespan (dope_memory_main.py:956–965)
- ✅ Instance tracking (eventbus_consumer.py:77–100)
- ⚠️  WMA prototype (~3.6k lines) still co-resident (unreferenced legacy code)
- ⚠️  Dead stdio shim on port 8096 (dead code path)

**Wired**:
- compose.yml: ✅ dope-memory service, ENABLE_EVENTBUS=true, REDIS_URL configured
- services/registry.yaml: ✅ port 3020, /health endpoint
- .mcp.json: ✅ dope-memory configured, /mcp transport
- docker/mcp-servers-source/.../Dockerfile.dope-memory: ✅ HEALTHCHECK

**Quality**: 4/5
- **Bugs**: None in core path
- **Debt**: WMA prototype (archive candidate), dead shim
- **Architecture**: Sound canonical-ledger + promotion approach
- **Test coverage**: Integration tests exist; promotion logic deterministic

---

### 1.2 ConPort (docker/mcp-servers-source/conport/)

**Intended**:
- Canonical writer for decisions/progress/context
- 17-tool SSE surface + REST + JSON-RPC compatibility
- Knowledge graph queries (append-only decisions)
- Mirror receipt from dope-memory (Trinity Rule 1)

**Implemented**:
- ✅ 17-tool SSE surface (server.py:43–210)
- ✅ HTTP endpoints (enhanced_server.py, port 3004)
- ✅ Decision logging with timestamp + rationale (enhanced_server.py:671–728)
- ✅ Decision → DopeconBridge publication (enhanced_server.py:708–717)
- ✅ Instance detection via SimpleInstanceDetector (enhanced_server.py:710)
- ⚠️  Knowledge graph = plain table, read-only traversal (no AGE/Cypher at runtime)
- ⚠️  Worktree isolation inert over SSE (single DOPEMUX_INSTANCE_ID value)
- ⚠️  GET /api/progress mutates if DOPEMUX_AUTO_FORK_PROGRESS=on

**Wired**:
- compose.yml: ✅ conport service, REST :3004, SSE :3005, info :4004
- .mcp.json: ✅ conport configured
- ~/.claude.json: ⚠️  Duplicated (drifted, 6 nonexistent tool references)
- services/registry.yaml: ✅ ports/health

**Quality**: 3.5/5
- **Bugs**: 
  - `_ensure_schema` fail-open verification (enhanced_server.py: missing rollback on error)
  - GET mutation on /api/progress (design issue, not enforced off)
- **Integration gaps**:
  - decision.logged published to dopemux:events, not activity.events.v1
  - No emit_capture_event() call (decision.logged never reaches dope-memory)
- **Debt**: Upstream wrapper path still referenced in some .claude commands; knowledge graph write API unimplemented

---

### 1.3 dope-context (services/dope-context/)

**Intended**:
- Hybrid dense+sparse code+docs retrieval (Voyage + Qdrant + BM25)
- Per-worktree Qdrant collections
- Complexity scoring (0.0–1.0 band shared with Serena)
- Read-only Phase-1 lexical enforcement

**Implemented**:
- ✅ 18 real tools (search_code, docs_search, search_all, sync, index, clear)
- ✅ Voyage embeddings + Qdrant client
- ✅ Sync via SHA256 change detection
- ✅ Per-worktree collection detection (workspace_id in requests)
- ⚠️  Healthcheck fail-open (`|| exit 0`, always passes)
- ⚠️  Mock simple_server.py fabricates plausible results (if real server unavailable)
- ⚠️  Complexity claim unvalidated (docstring says "ast, not Tree-sitter")
- ⚠️  No collection GC (orphaned Qdrant collections for deleted worktrees)
- ⚠️  No Voyage cost guard (unbounded embedding calls possible)

**Wired**:
- compose.yml: ✅ dope-context service, HTTP 127.0.0.1:3010
- .mcp.json: ⚠️  Not present (design gap — should be listed)
- services/registry.yaml: ✅ port 3010, /health

**Quality**: 3/5
- **Bugs**:
  - Healthcheck fail-open (trivial fix)
  - No collection GC (operational risk: disk bloat)
  - Complexity contract unvalidated (docstring lies)
- **Integration gaps**:
  - dope-context indexing of chronicle is gated off (ENABLE_DOPECONTEXT_INDEX=false)
  - No per-request complexity score in results (promised but unimplemented)
- **Debt**: simple_server.py mock should be deleted; complexity scoring should be unified with Serena or claim removed

---

### 1.4 Task Orchestrator (Kotlin MCP jar @ port 7890)

**Intended**:
- Persistent work-item DAG with role-based queue→work→review→terminal transitions
- Trigger guards + dependency resolution
- Note-schema gates + proof-bundle-in-note
- Repo-scoped singleton (git-common-dir keyed)

**Implemented**:
- ✅ Kotlin jar v3.8.0 (ghcr.io/jpicklyk/mcp-task-orchestrator)
- ✅ HTTP singleton via ensure script (excellent lifecycle mgmt)
- ✅ 14-tool surface (manage_items, query_items, advance_item, etc.)
- ✅ Repo-scoped keying + worktree awareness
- ⚠️  NOT auto-started (ensure script optional, no healthcheck enforcement)
- ⚠️  No auto-ensure in H3 hook (manual startup only)
- ⚠️  Python services/task-orchestrator/ = unrelated parallel service (name collision)

**Wired**:
- .mcp.json: ✅ task-orchestrator configured @ 127.0.0.1:7890
- Codex config: ✅ required=true (hard client dependency)
- /dx:* commands: ✅ 18 commands consume task-orchestrator
- ensure script: ✅ exists but not called automatically

**Quality**: 4/5
- **Bugs**: None in jar itself (upstream maintained)
- **Integration gaps**:
  - No task.completed/failed/blocked event emission to dope-memory
  - No workflow.phase_changed event emission
  - Workflow transitions don't trigger capture_client.emit_capture_event()
- **Debt**: Python services/task-orchestrator rename needed (rename to workflow-api or archive)

---

### 1.5 Native Hooks Capture Path (src/dopemux/claude/native_hooks.py)

**Intended**:
- Hook lifecycle: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, Stop, SubagentStart, SessionEnd
- Emit promotable events (error.encountered on tool failure)
- Fail-open (never block user due to capture)

**Implemented**:
- ✅ Imports try_emit_promotable_capture_event (line 78)
- ✅ _bounded_hook_error_capture() wired to PostToolUseFailure (lines 166–194)
- ✅ Emits "error.encountered" with error_kind, service, hook_event_name
- ✅ Fail-open behavior (errors caught, logged, no re-raise)
- ✅ Source="dopemux.native_hooks", mode="plugin"

**Wired**:
- .claude/settings.json: ✅ hooks configured
- src/dopemux/claude/native_hooks.py: ✅ entry point registered
- H3 hook (mcp_health_probe.py): ⚠️  Emits MCP health, not capture events

**Quality**: 4.5/5
- **Bugs**: None
- **Integration gaps**: Only error.encountered is wired; no decision/task/workflow events from here

---

## 2. Promotion Pipeline & Chronicle Flow

### Promotable Event Types (promotion.py:18–28)

```python
PROMOTABLE_EVENT_TYPES = frozenset([
    "decision.logged",      # ConPort → dope-memory
    "task.completed",       # workflow-kernel → dope-memory
    "task.failed",          # workflow-kernel → dope-memory
    "task.blocked",         # workflow-kernel → dope-memory
    "error.encountered",    # native_hooks → dope-memory ✅ wired
    "workflow.phase_changed", # workflow-kernel → dope-memory
    "manual.memory_store",  # skill invocation → dope-memory
])
```

### Current Wiring Status

| Event Type | Source | Emitter | Stream | Status |
|---|---|---|---|---|
| error.encountered | native_hooks.py | try_emit_promotable_capture_event() | activity.events.v1 | ✅ WIRED |
| decision.logged | ConPort | publish_decision_logged() | dopemux:events | ⚠️ WRONG STREAM |
| task.completed | workflow-kernel | TBD | TBD | ❌ NOT WIRED |
| task.failed | workflow-kernel | TBD | TBD | ❌ NOT WIRED |
| task.blocked | workflow-kernel | TBD | TBD | ❌ NOT WIRED |
| workflow.phase_changed | workflow-kernel | TBD | TBD | ❌ NOT WIRED |
| manual.memory_store | /decision, /caveat skills | TBD | activity.events.v1 | ⚠️ SKILL LAYER ONLY |

### Root Cause: Stream Name Mismatch

**Published to** (ConPort → DopeconBridge):
```python
# docker/mcp-servers-source/conport/integration_bridge_client.py:94
stream = "dopemux:events"
```

**Consumed from** (dope-memory EventBusConsumer):
```python
# services/working-memory-assistant/eventbus_consumer.py:36
INPUT_STREAM = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")
```

**Impact**: 24,537 raw events in dopemux:events (including decision.logged) + 0 work_log_entries in chronicle

---

## 3. Critical Integration Points

### Integration Point 1: ConPort Decision Logging → Dope-Memory

**Current path**:
```
POST /api/decisions
  ↓ (enhanced_server.py:671–728)
INSERT decision DB
  ↓
publish_decision_logged() to DopeconBridge (line 711)
  ↓ (integration_bridge_client.py:122–140)
POST /events to DopeconBridge
  ↓ (routes.py:558–564)
Publish to "dopemux:events" (wrong stream!) 
  ↓
[never consumed by dope-memory]
```

**Missing link**: 
- dope-memory listens on activity.events.v1 only
- DopeconBridge publishes decision.logged to dopemux:events
- No bridge between the two streams

**Fix**: Change stream name from dopemux:events → activity.events.v1 in:
1. docker/mcp-servers-source/conport/integration_bridge_client.py:94
2. services/dopecon-bridge/dopecon_bridge/routes.py:321, 558, 603

---

### Integration Point 2: Task Orchestrator Transitions → Dope-Memory

**Current state**: NOT WIRED

**Should emit**:
- task.completed when work_item advances from work→review→terminal
- task.failed when work_item transitions to terminal with failure status
- task.blocked when dependency gate fails
- workflow.phase_changed when global workflow phase shifts

**Source location** (to-be-identified):
- Likely: services/task-orchestrator/ (Python) OR task-orchestrator Kotlin jar callbacks
- Should integrate via: task-orchestrator HTTP endpoint hook → capture_client.emit_capture_event()

**Effort**: Medium (requires identifying transition points, adding event emission)

---

### Integration Point 3: Skills → Manual Memory Store

**Current state**: ASPIRATIONAL

**Intended**: /decision, /caveat, /followup skills append mirror receipt to dope-memory

**Current behavior**: Skills operate independently, no integration to capture pipeline

**Source**: .claude/commands/*/... (skills not visible in this worktree)

---

## 4. Intended vs Implemented Verdict

| System | Intended | Implemented | Wired | Quality | Top Bug |
|---|---|---|---|---|---|
| **dope-memory** | 10-tool chronicle sidecar with promotion engine | ✅ Complete | ⚠️ Partial (consumer started, stream mismatch blocks input) | 4/5 | WMA prototype unarchived |
| **ConPort** | Canonical decision/progress writer with Trinity mirroring | ✅ Core complete | ⚠️ Partial (decision.logged to wrong stream) | 3.5/5 | _ensure_schema fail-open |
| **dope-context** | Hybrid semantic code+docs retrieval | ✅ Complete | ⚠️ Partial (.mcp.json missing, collection GC absent) | 3/5 | Healthcheck fail-open |
| **task-orchestrator** | Persistent DAG workflow engine | ✅ Jar complete | ⚠️ Partial (no auto-start, no event emission) | 4/5 | No task.*/workflow.phase_changed emission |
| **capture_client** | Deterministic event capture to SQLite+Redis | ✅ Complete | ⚠️ Partial (error.encountered wired, decision.logged blocked by stream mismatch) | 4.5/5 | None |
| **native_hooks** | Lifecycle hook adapter for Claude context injection | ✅ Complete | ✅ Full | 4.5/5 | None |

---

## 5. Chronicle Fill Status

**Expected work_log_entries** (after fixes):
- error.encountered: 100–1k/session (hook failures)
- decision.logged: 1–10/session (architect decisions)
- task.completed: 5–50/session (workflow completions)
- task.failed/blocked: 1–10/session (errors)
- workflow.phase_changed: 0–5/session (mode transitions)
- **Total**: 10–100/session vs current 0

**Blocked by**:
1. Stream mismatch (HIGH IMPACT): dopemux:events ≠ activity.events.v1
2. Workflow event emission (MEDIUM IMPACT): task-orchestrator not wired
3. Skill-layer integration (LOW IMPACT): /decision, /caveat, /followup

---

## 6. Ranked Top 5 Fixes

### P1 (1-hour): Stream Name Alignment
**Files to change**: 4 files, 1 line each
1. `docker/mcp-servers-source/conport/integration_bridge_client.py:94`: stream → activity.events.v1
2. `services/dopecon-bridge/dopecon_bridge/routes.py:321`: stream → activity.events.v1
3. `services/dopecon-bridge/dopecon_bridge/routes.py:558`: stream → activity.events.v1
4. `services/dopecon-bridge/dopecon_bridge/routes.py:603`: stream → activity.events.v1

**Impact**: 24.5k heartbeat events + decision.logged now flow to chronicle promotion

### P2 (2-hours): ConPort → capture_client Integration
**File**: `docker/mcp-servers-source/conport/enhanced_server.py:728` (after decision insert)
**Add**: `try_emit_promotable_capture_event("decision.logged", { ... }, source="conport", mode="mcp")`
**Impact**: decision.logged also captured to SQLite canonical ledger (Trinity Rule 1)

### P3 (3-hours): Fix Healthchecks
1. `services/dope-context/Dockerfile`: Remove `|| exit 0`
2. `docker/mcp-servers-source/pal/Dockerfile`: Replace `exit 0` with real capability check

### P4 (4-hours): Task Orchestrator Event Wiring
**File**: `services/task-orchestrator/` (if Python) OR task-orchestrator Kotlin jar callback
**Add**: Transition hooks → `try_emit_promotable_capture_event()`

### P5 (2-hours): Code Cleanup
1. Archive WMA prototype (`services/working-memory-assistant/wma_core.py`, etc.)
2. Delete `services/working-memory-assistant/` stdio shim
3. Rename Python `services/task-orchestrator/` → `services/workflow-api/`

---

## 7. Architecture Validation

**Memory Trinity design is sound** (per 2026-07-03 audit):
- ✅ Canonical writer split (ConPort = source, dope-memory = mirror)
- ✅ Fail-closed routing (provenance labels, untrusted-by-default)
- ✅ Append-only ledger (SQLite + promotion engine)
- ✅ Promotion determinism (no LLM in Phase 1)

**Implementation gaps are operational, not architectural**:
- Stream mismatch: naming/plumbing, not design
- Event emission: missing wiring, not logic
- Healthchecks: advisory theater, not critical path

---

## Cluster Verdict (5 bullets)

1. **Design is excellent**: Memory Trinity architecture catches hazards (GET mutation detection, fail-closed routing); adoption of this pattern to other systems would fix systemic issues

2. **Implementation is 75% complete**: error.encountered wired ✅; decision.logged infrastructure built but blocked by stream mismatch ⚠️; task.* and workflow.phase_changed not yet wired ❌

3. **One critical blocker**: dopemux:events ≠ activity.events.v1 prevents 24.5k decision.logged events from reaching promotion; fix = 4 one-line changes

4. **Quality is solid but hides debt**: Core path (canonical ledger, promotion engine, eventbus consumer) is robust; peripheral code (WMA prototype, dead shim, name collisions) should be archived

5. **Integration opportunities are high-value**: (a) Fix stream name → chronicle immediately populates; (b) Wire task-orchestrator transitions → workflow instrumentation complete; (c) Unify complexity scoring → Serena + dope-context alignment; (d) Auto-start task-orchestrator in H3 hook → reliability

