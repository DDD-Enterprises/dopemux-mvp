---
id: OPUS-CLI-INT-02_INTEGRATION_BLUEPRINT
title: Opus Cli Int 02 Integration Blueprint
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-05-12'
prelude: Opus Cli Int 02 Integration Blueprint (explanation) for dopemux documentation
  and developer workflows.
---
# OPUS-CLI-INT-02: Dopemux CLI Integration Blueprint

**Date**: 2026-02-11
**Model**: Claude Code (Opus 4.6)
**Status**: DRAFT — Pending human review
**Prerequisite**: DR-CLI-INT-01 findings embedded inline (no separate artifact found)

---

## 0. Evidence Base (Inlined DR-CLI-INT-01 Capability Matrix)

### Current Implementation Truth (Code-Verified)

| Component | Path | Status | Notes |
|-----------|------|--------|-------|
| **Capture Client** | `src/dopemux/memory/capture_client.py` | ACTIVE | Deterministic event_id (SHA-256), redaction, dual-mode (plugin/cli/mcp/auto) |
| **Chronicle Schema** | `services/working-memory-assistant/chronicle/schema.sql` | ACTIVE | 5 tables: raw_activity_events, work_log_entries, issue_links, reflection_cards, trajectory_state |
| **Promotion Engine** | `services/working-memory-assistant/promotion/promotion.py` | ACTIVE | 7 promotable event types, deterministic scoring, provenance injection |
| **Redactor** | `services/working-memory-assistant/promotion/redactor.py` | ACTIVE | Denylist paths, sensitive keys, regex patterns, 64KB cap |
| **EventBus Consumer** | `services/working-memory-assistant/eventbus_consumer.py` | ACTIVE | Redis Streams (activity.events.v1 -> memory.derived.v1), Phase 2 reflection/trajectory |
| **Global Rollup** | `src/dopemux/memory/global_rollup.py` | ACTIVE | Read-only cross-project index at ~/.dopemux/global_index.sqlite |
| **Event Bus** | `src/dopemux/event_bus.py` | ACTIVE | InMemory + RedisStreams adapters, namespace pattern matching |
| **Claude Code Hooks** | `src/dopemux/hooks/claude_code_hooks.py` | PARTIAL | Shell hooks generate, daemon monitoring, calls `dopemux capture emit --mode plugin` |
| **Canonical Ledger** | `services/working-memory-assistant/canonical_ledger.py` | ACTIVE | ADR-213 single ledger resolution |
| **Chronicle Store** | `services/working-memory-assistant/chronicle/store.py` | ACTIVE | SQLite CRUD for all chronicle tables |
| **Reflection Generator** | `services/working-memory-assistant/reflection/reflection.py` | ACTIVE | Phase 2 idle/session-end reflection cards |
| **Trajectory Manager** | `services/working-memory-assistant/trajectory/manager.py` | ACTIVE | Phase 2 current-stream/goal tracking |

### Capture Modes (from `capture_client.py:27-36`)

```
CAPTURE_MODE_PLUGIN = "plugin"   # Claude Code hook adapter
CAPTURE_MODE_CLI    = "cli"      # Manual CLI invocation
CAPTURE_MODE_MCP    = "mcp"      # MCP server adapter
CAPTURE_MODE_AUTO   = "auto"     # Auto-detect from env
```

### Resolution Chain (from `capture_client.py:101-134`)

```
explicit arg -> DOPEMUX_CAPTURE_MODE env -> .dopemux/config.yaml ->
DOPEMUX_CAPTURE_CONTEXT env -> CLAUDE_SESSION_ID/CLAUDECODE env -> default "cli"
```

### Existing Surfaces

| Surface | Type | Evidence |
|---------|------|----------|
| `dopemux capture emit` | CLI | Referenced in hooks (`claude_code_hooks.py:254-262`) |
| `dopemux memory rollup build/list/search` | CLI | Documented in `docs/03-reference/memory-capture-cli.md` |
| Redis `activity.events.v1` stream | Event bus | EventBus consumer subscribes (`eventbus_consumer.py:36`) |
| Redis `memory.derived.v1` stream | Event bus | Consumer publishes derived events (`eventbus_consumer.py:37`) |
| Chronicle SQLite | Storage | Per-project at `.dopemux/chronicle.sqlite` |
| Global rollup SQLite | Storage | At `~/.dopemux/global_index.sqlite` |

### Invariants Already Enforced (from ADR-213, Packet D)

1. **Content-addressed event_id**: SHA-256 of `event_type|session_id|ts_bucket|payload` (capture_client.py:248-271)
2. **Redaction before storage**: Always (capture_client.py:331)
3. **INSERT OR IGNORE**: Idempotent writes (capture_client.py:362)
4. **Provenance on promotion**: source_event_id, source_event_type, source_adapter, source_event_ts_utc, promotion_rule (schema.sql:69-74)
5. **Sentinel ban**: Runtime rejects `pre_migration`, `unknown`, `""` in event_id/source (promotion.py:140-145)
6. **Read-only rollup**: Project ledgers opened `?mode=ro` (global_rollup.py:194)
7. **Fail-closed capture**: CaptureError if no repo root (capture_client.py:67-70)

---

## 1. Architecture Blueprint

```
                         ┌─────────────────────────────────────┐
                         │       CLI TOOL CAPTURE SURFACE       │
                         │                                     │
                         │  ┌───────────┐   ┌───────────────┐ │
                         │  │ Claude    │   │ Codex/Copilot │ │
                         │  │ Code      │   │ (future)      │ │
                         │  │ Plugin    │   │ MCP Server    │ │
                         │  └─────┬─────┘   └──────┬────────┘ │
                         │        │                 │          │
                         │  mode=plugin       mode=mcp        │
                         │        │                 │          │
                         └────────┼─────────────────┼──────────┘
                                  │                 │
                                  ▼                 ▼
                    ┌─────────────────────────────────────────┐
                    │         CAPTURE ADAPTER LAYER            │
                    │                                         │
                    │   src/dopemux/memory/capture_client.py  │
                    │                                         │
                    │   1. Resolve repo_root (fail-closed)    │
                    │   2. Resolve capture mode                │
                    │   3. Load + apply redactor               │
                    │   4. Generate deterministic event_id     │
                    │   5. INSERT OR IGNORE into ledger        │
                    │   6. Optional: fan-out to Redis stream   │
                    │                                         │
                    └──────────────┬───────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
    ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
    │    CHRONICLE      │  │ Redis Stream │  │   (future)       │
    │    (per-project)  │  │ activity.    │  │   Postgres       │
    │                   │  │ events.v1    │  │   Mirror         │
    │ .dopemux/         │  │              │  │                  │
    │ chronicle.sqlite  │  │ (best-effort │  │ (ENABLE_MIRROR_  │
    │                   │  │  fan-out)    │  │  SYNC=true)      │
    │ Tables:           │  └──────┬───────┘  └──────────────────┘
    │  raw_activity_    │         │
    │    events (7d)    │         │
    │  work_log_        │         ▼
    │    entries         │  ┌──────────────────────────────────┐
    │  reflection_      │  │   DERIVED PIPELINE                │
    │    cards           │  │   (EventBus Consumer)             │
    │  trajectory_      │  │                                    │
    │    state           │  │   1. Parse event envelope          │
    │  issue_links      │  │   2. Track session (Phase 2)       │
    └────────┬──────────┘  │   3. Redact payload                │
             │             │   4. Store raw event in chronicle   │
             │             │   5. Promote eligible events        │
             │             │   6. Update trajectory              │
             │             │   7. Publish to memory.derived.v1   │
             │             │   8. Generate reflections           │
             │             └───────────────┬────────────────────┘
             │                             │
             │                             ▼
             │               ┌────────────────────────┐
             │               │ memory.derived.v1       │
             │               │ (downstream consumers)  │
             │               │                        │
             │               │ - worklog.created       │
             │               │ - memory.pulse          │
             │               │ - reflection.created    │
             │               └────────────────────────┘
             │
             ▼
    ┌───────────────────────────────────────────────┐
    │         RETRIEVAL SURFACES                     │
    │                                               │
    │  ┌─────────────────┐  ┌────────────────────┐ │
    │  │ Global Rollup    │  │ WMA MCP Server     │ │
    │  │ (read-only)      │  │ (future surface)   │ │
    │  │                  │  │                    │ │
    │  │ CLI:             │  │ MCP tools:         │ │
    │  │  dopemux memory  │  │  memory/search     │ │
    │  │  rollup search   │  │  memory/recent     │ │
    │  │  rollup list     │  │  memory/reflect    │ │
    │  │  rollup build    │  │                    │ │
    │  └─────────────────┘  └────────────────────┘ │
    │                                               │
    │  ┌─────────────────┐  ┌────────────────────┐ │
    │  │ DopeContext      │  │ ConPort KG         │ │
    │  │ Index            │  │ (decision/pattern  │ │
    │  │ (best-effort     │  │  authority)        │ │
    │  │  vector index)   │  │                    │ │
    │  └─────────────────┘  └────────────────────┘ │
    └───────────────────────────────────────────────┘

  PLANE SUBSCRIPTIONS (event bus → derived views):

    PM Plane:      subscribes memory.derived.v1 → task state, Leantime sync
    ADHD Plane:    subscribes memory.derived.v1 → energy/attention/break signals
    Search Plane:  subscribes memory.derived.v1 → DopeContext incremental index
```

### Key Architectural Properties

1. **Single canonical ledger per project** (ADR-213) — chronicle.sqlite is the authority
2. **Capture adapter layer is mode-agnostic** — same `emit_capture_event()` function for all modes
3. **Content-addressed event_id** — cross-adapter convergence without UUID non-determinism
4. **Planes are consumers, not writers** — PM/ADHD/Search subscribe to derived stream, never write to chronicle
5. **Best-effort fan-out** — Redis stream emission is optional and non-blocking
6. **Fail-closed capture** — no silent degradation on missing repo root

---

## 2. Adapter Strategy Decision

### Decision: Plugin-first for Claude Code, MCP for Codex/Copilot, CLI as universal fallback

**Rationale**:

Claude Code has a mature hook integration model (`.claude/settings.json` hooks, shell preexec/precmd) that is already partially implemented (`hooks/claude_code_hooks.py`). The plugin path fires via `dopemux capture emit --mode plugin` which is a synchronous, auditable shell call.

Codex CLI and GitHub Copilot CLI do not support hooks natively. Their extension model is MCP servers. An MCP capture server can expose a `capture/emit` tool that writes directly to the chronicle via `emit_capture_event(mode="mcp")`.

**Mode Matrix**:

| CLI Tool | Capture Mode | Adapter Implementation | Status |
|----------|-------------|----------------------|--------|
| Claude Code | `plugin` | Shell hook → `dopemux capture emit --mode plugin` | PARTIAL (hooks exist, need hardening) |
| Codex CLI | `mcp` | MCP server exposes `capture/emit` tool | NOT STARTED |
| Copilot CLI | `mcp` | Same MCP server as Codex | NOT STARTED |
| Manual / scripts | `cli` | Direct `dopemux capture emit --mode cli` | WORKING |
| Any (auto-detect) | `auto` | Resolution chain in capture_client.py | WORKING |

**Failure Modes**:

| Failure | Behavior | Recovery |
|---------|----------|----------|
| `dopemux` CLI not installed | Hook silently skips (2s timeout in hooks) | Install dopemux |
| Redis unavailable | Capture succeeds (SQLite), fan-out skipped | Derived pipeline offline until Redis recovers |
| MCP server crash | Codex/Copilot capture fails, events lost | Events not captured; MCP restart via supervisor |
| SQLite lock contention | `INSERT OR IGNORE` with WAL mode handles concurrent access | Retry at next event |
| No repo root | `CaptureError` raised, capture fails closed | User must be in a git/dopemux workspace |
| Auth/permission fail | File system permissions on `.dopemux/` | Fix directory permissions |
| Offline / no network | Capture to local SQLite succeeds; no Redis, no remote | Full local operation, fan-out resumes when online |

**Why not "both" simultaneously?**

Both modes already converge to the same `emit_capture_event()` function. Running both simultaneously is safe due to content-addressed event_id dedup. However, for simplicity:
- Claude Code: plugin only (hooks are native)
- Codex/Copilot: MCP only (their extension model)
- The "auto" mode handles edge cases where both might fire

---

## 3. Implementation Backlog

### Ticket Numbering: CLI-INT-001 through CLI-INT-016

---

#### CLI-INT-001: Harden Claude Code Hook Adapter

**Scope**: `src/dopemux/hooks/claude_code_hooks.py`, `.claude/settings.json`

**Acceptance Criteria**:
- Hook fires on Claude Code tool use events (file write, bash exec, commit)
- Hook is non-blocking (async subprocess, 2s timeout)
- Hook captures: event_type, timestamp, file paths (redacted), command summary
- Failed hooks never block Claude Code operation
- Shell hook scripts (bash/zsh) are installable via `dopemux hooks install`

**Tests Required**:
- Unit: Hook fires correct `dopemux capture emit` command for each event type
- Unit: Timeout at 2s does not propagate error
- Integration: Event appears in chronicle.sqlite after hook fires
- Determinism: Same event fired twice produces identical event_id

**Evidence Capture**:
```bash
dopemux capture emit --mode plugin --event '{"event_type":"file.written","payload":{"path":"src/app.py"}}'
sqlite3 .dopemux/chronicle.sqlite "SELECT id, event_type, source FROM raw_activity_events ORDER BY ts_utc DESC LIMIT 5;"
```

---

#### CLI-INT-002: Build MCP Capture Server for Codex/Copilot

**Scope**: New service `services/capture-mcp/` or tool in WMA MCP server

**Acceptance Criteria**:
- MCP server exposes `capture/emit` tool
- Tool accepts: event_type, payload, optional session_id
- Tool calls `emit_capture_event(mode="mcp")` internally
- Response includes event_id and inserted boolean
- Server can be configured in Codex/Copilot MCP settings

**Tests Required**:
- Unit: MCP tool invocation writes to chronicle
- Unit: Deterministic event_id matches CLI-generated event_id for same payload
- Integration: Codex MCP config file includes capture server
- Cross-adapter: Same event via CLI and MCP produces one row (dedup)

**Evidence Capture**:
```bash
# Simulate MCP tool call
echo '{"event_type":"task.completed","payload":{"task_id":"T-001","title":"Auth fix"}}' | \
  python -m services.capture_mcp.server --test-emit
sqlite3 .dopemux/chronicle.sqlite "SELECT COUNT(*) FROM raw_activity_events WHERE source='mcp';"
```

---

#### CLI-INT-003: Implement `dopemux capture emit` CLI Command

**Scope**: `src/dopemux/cli.py` (capture subcommand group)

**Acceptance Criteria**:
- `dopemux capture emit --event JSON [--mode MODE] [--quiet]` writes to chronicle
- `--mode` accepts: plugin, cli, mcp, auto (default: auto)
- `--quiet` suppresses output (for hook usage)
- Exit code 0 on success, 1 on error
- JSON event envelope validated before processing

**Tests Required**:
- CLI: `dopemux capture emit` with valid JSON succeeds
- CLI: Invalid JSON returns exit code 1
- CLI: `--quiet` suppresses stdout
- CLI: `--mode plugin` sets source correctly

**Evidence Capture**:
```bash
dopemux capture emit --event '{"event_type":"manual.memory_store","payload":{"category":"debugging","entry_type":"manual_note","summary":"Test note"}}' --mode cli
echo $?  # expect 0
sqlite3 .dopemux/chronicle.sqlite "SELECT id, event_type, source FROM raw_activity_events ORDER BY created_at_utc DESC LIMIT 1;"
```

---

#### CLI-INT-004: Capture Mode Config in `.dopemux/config.yaml`

**Scope**: `.dopemux/config.yaml`, `capture_client.py`

**Acceptance Criteria**:
- `.dopemux/config.yaml` supports `capture.mode: plugin|cli|mcp|auto`
- `.dopemux/config.yaml` supports `capture.lanes` for per-lane opt-in (see Policy §4)
- Config is validated at load time
- Invalid mode raises `CaptureError`

**Tests Required**:
- Unit: Config with valid mode resolves correctly
- Unit: Config with invalid mode raises CaptureError
- Unit: Missing config falls through to env/auto
- Integration: Config change takes effect without restart

**Evidence Capture**:
```bash
cat .dopemux/config.yaml  # show capture.mode setting
dopemux capture emit --event '...' --mode auto  # should resolve to config value
```

---

#### CLI-INT-005: Opt-In Lane Injection Policy (Config Keys)

**Scope**: `.dopemux/config.yaml`, `capture_client.py`, new `lane_policy.py`

**Acceptance Criteria**:
- Each tmux lane (orchestrator, agent:primary, agent:secondary, sandbox) can opt in/out of capture
- Default: ALL lanes DISABLED (opt-in, never opt-out)
- Config key: `capture.lanes.<lane_name>.enabled: true|false`
- Config key: `capture.lanes.<lane_name>.event_types: [list]` (allowlist)
- Audit log written to `.dopemux/capture_audit.log` on every enable/disable change

**Tests Required**:
- Unit: Disabled lane silently skips capture
- Unit: Enabled lane with event_type filter only captures matching types
- Unit: Default (no config) = all lanes disabled
- Integration: Audit log records lane policy changes with timestamp

**Evidence Capture**:
```bash
cat .dopemux/config.yaml  # show lane config
dopemux capture emit --event '...' --lane agent:primary  # should succeed if enabled
cat .dopemux/capture_audit.log  # verify audit entry
```

---

#### CLI-INT-006: Event Type Registry and Validation

**Scope**: New `src/dopemux/memory/event_types.py`

**Acceptance Criteria**:
- Canonical event type registry with dotted names (e.g., `decision.logged`, `task.completed`)
- Validation function rejects unknown event types (fail-closed)
- Normalization handles underscore/dot variants
- Registry is a frozen set, not a mutable config

**Tests Required**:
- Unit: All 7 promotable types accepted
- Unit: Unknown types rejected with clear error
- Unit: Normalization converts `decision_logged` -> `decision.logged`
- Unit: Empty/whitespace types rejected

**Evidence Capture**:
```bash
python -c "from dopemux.memory.event_types import validate_event_type; print(validate_event_type('decision.logged'))"
```

---

#### CLI-INT-007: Redis Stream Fan-Out Hardening

**Scope**: `capture_client.py:_emit_to_event_stream()`

**Acceptance Criteria**:
- Fan-out is opt-in via `DOPEMUX_CAPTURE_EMIT_EVENTBUS=true` or config
- Connection failure does not block capture
- Stream name configurable via `DOPE_MEMORY_INPUT_STREAM`
- Redis password support via `REDIS_PASSWORD`
- Envelope matches EventBus consumer expected format exactly

**Tests Required**:
- Unit: Fan-out succeeds when Redis available
- Unit: Fan-out silently skips when Redis unavailable
- Unit: Envelope format matches consumer parser expectations
- Integration: Event flows from capture -> Redis -> consumer -> promoted entry

**Evidence Capture**:
```bash
DOPEMUX_CAPTURE_EMIT_EVENTBUS=true dopemux capture emit --event '{"event_type":"decision.logged","payload":{"decision_id":"D-100","title":"Test","choice":"A","rationale":"Because"}}'
redis-cli XRANGE activity.events.v1 - + COUNT 1
```

---

#### CLI-INT-008: Chronicle Schema Migration Runner

**Scope**: `services/working-memory-assistant/migration_runner.py`

**Acceptance Criteria**:
- Migrations in `chronicle/migrations/` applied in version order
- `schema_migrations` table tracks applied versions
- Idempotent: re-running skips already-applied migrations
- CLI command: `dopemux memory migrate`
- Fails closed if migration SQL is invalid

**Tests Required**:
- Unit: Fresh DB gets base schema + all migrations
- Unit: Existing DB with v1.0.0 gets only newer migrations
- Unit: Re-running produces no changes
- Integration: `dopemux memory migrate` exits 0 on success

**Evidence Capture**:
```bash
dopemux memory migrate
sqlite3 .dopemux/chronicle.sqlite "SELECT * FROM schema_migrations ORDER BY version;"
```

---

#### CLI-INT-009: Promotion Pipeline End-to-End Test

**Scope**: `tests/integration/test_capture_to_promotion.py`

**Acceptance Criteria**:
- Test captures a raw event via CLI adapter
- Event flows through promotion engine
- Promoted entry appears in work_log_entries with correct provenance
- Deterministic event_id verified
- Redaction verified (no secrets in stored payload)

**Tests Required**:
- Integration: capture -> chronicle -> promote -> work_log_entries
- Determinism: Same input produces same output
- Provenance: source_event_id, source_adapter, promotion_rule all populated
- Redaction: Injected API key is removed from stored payload

**Evidence Capture**:
```bash
pytest tests/integration/test_capture_to_promotion.py -v
```

---

#### CLI-INT-010: WMA MCP Server Retrieval Tools

**Scope**: `services/working-memory-assistant/mcp/server.py`

**Acceptance Criteria**:
- MCP tool `memory/search` searches work_log_entries by query
- MCP tool `memory/recent` returns N most recent entries
- MCP tool `memory/reflect` returns latest reflection card
- All tools include provenance in responses
- Results capped at configurable limit (default 10)

**Tests Required**:
- Unit: Each tool returns correct data shape
- Unit: Empty DB returns empty results (not error)
- Unit: Provenance fields present in every result
- Integration: MCP tools callable from Claude Code

**Evidence Capture**:
```bash
# Via MCP test harness
echo '{"method":"tools/call","params":{"name":"memory/recent","arguments":{"limit":5}}}' | python -m services.working_memory_assistant.mcp.server
```

---

#### CLI-INT-011: Global Rollup Incremental Build

**Scope**: `src/dopemux/memory/global_rollup.py`

**Acceptance Criteria**:
- `dopemux memory rollup build` only processes entries newer than last build
- Uses `last_seen_at` timestamp to avoid re-scanning
- Performance: < 2s for 1000 new entries
- Unchanged projects skipped

**Tests Required**:
- Unit: Incremental build only adds new entries
- Unit: Unchanged project produces 0 upserts
- Performance: Benchmark with 5000 entries < 10s

**Evidence Capture**:
```bash
time dopemux memory rollup build --projects-file ~/projects.txt
# Second run should be faster (incremental)
time dopemux memory rollup build --projects-file ~/projects.txt
```

---

#### CLI-INT-012: Capture Audit Log

**Scope**: New `src/dopemux/memory/audit_log.py`

**Acceptance Criteria**:
- Every capture write logged to `.dopemux/capture_audit.log`
- Log format: `ISO_TIMESTAMP | MODE | SOURCE | EVENT_TYPE | EVENT_ID | INSERTED`
- Log rotation: Max 10MB, 3 rotated files
- Lane policy changes logged separately
- Log is append-only (no overwrites)

**Tests Required**:
- Unit: Capture event produces audit log entry
- Unit: Log rotation triggers at 10MB
- Unit: Audit log parseable by standard tools (grep, awk)

**Evidence Capture**:
```bash
dopemux capture emit --event '...'
tail -1 .dopemux/capture_audit.log
```

---

#### CLI-INT-013: Codex/Copilot MCP Config Generator

**Scope**: `dopemux init --mcp codex` and `dopemux init --mcp copilot`

**Acceptance Criteria**:
- Generates MCP proxy config for Codex CLI integration
- Generates MCP proxy config for Copilot CLI integration
- Includes capture-mcp server in generated config
- Validates generated config against MCP schema

**Tests Required**:
- Unit: Generated Codex config is valid YAML
- Unit: Generated Copilot config is valid JSON
- Unit: Capture server endpoint present in config

**Evidence Capture**:
```bash
dopemux init --mcp codex
cat mcp-proxy-config.copilot.yaml  # verify capture server present
```

---

#### CLI-INT-014: Health Check for Memory Stack

**Scope**: `dopemux health` command enhancement

**Acceptance Criteria**:
- `dopemux health` reports chronicle status (exists, row counts, last event)
- Reports Redis stream status (connected, consumer group, lag)
- Reports global rollup status (projects count, last build)
- Reports capture mode and lane policy

**Tests Required**:
- Unit: Health check succeeds with minimal stack (SQLite only)
- Unit: Health check degrades gracefully when Redis offline
- Integration: `dopemux health` exit code 0 when healthy

**Evidence Capture**:
```bash
dopemux health
```

---

#### CLI-INT-015: Determinism Test Suite

**Scope**: `tests/unit/test_determinism.py`

**Acceptance Criteria**:
- Tests that event_id is deterministic (same input -> same hash)
- Tests that event_id excludes mode-specific metadata (source, project_id)
- Tests that timestamp bucketing to second precision works
- Tests that two adapters capturing same event produce identical event_id
- Tests that sentinel values are rejected at runtime

**Tests Required**:
- 10+ test cases covering all edge cases documented in Packet D
- No UUID usage in event_id generation
- No wallclock substitution (ts must come from event envelope)

**Evidence Capture**:
```bash
pytest tests/unit/test_determinism.py -v --tb=short
```

---

#### CLI-INT-016: Documentation — Capture Integration Guide

**Scope**: `docs/02-how-to/capture-integration-guide.md`

**Acceptance Criteria**:
- Documents all three capture modes (plugin, CLI, MCP)
- Includes setup instructions for Claude Code, Codex, Copilot
- Documents lane opt-in policy config
- Includes troubleshooting section
- References ADR-213 and this blueprint

**Tests Required**:
- Doc validation passes (`python scripts/docs_validator.py`)
- All code examples verified runnable

**Evidence Capture**:
```bash
python scripts/docs_validator.py docs/02-how-to/capture-integration-guide.md
```

---

## 4. Policy: Opt-In Injection Per Lane

### Contract

**Principle**: Capture is DISABLED by default for all lanes. Enabling capture for a lane is an explicit, auditable action.

### Config Keys

```yaml
# .dopemux/config.yaml
capture:
  # Global capture mode (default: auto)
  mode: auto

  # Per-lane opt-in (ALL disabled by default)
  lanes:
    "orchestrator:control":
      enabled: false           # DEFAULT
      event_types: []          # Empty = all types when enabled

    "agent:primary":
      enabled: true            # OPT-IN: explicitly enabled
      event_types:             # ALLOWLIST: only these types captured
        - "decision.logged"
        - "task.completed"
        - "task.failed"
        - "error.encountered"
        - "workflow.phase_changed"

    "agent:secondary":
      enabled: false           # DEFAULT
      event_types: []

    "sandbox:shell":
      enabled: false           # DEFAULT — sandbox is experimental, never capture
      event_types: []

  # Audit logging
  audit:
    enabled: true              # DEFAULT: audit logging on
    path: ".dopemux/capture_audit.log"
    max_bytes: 10485760        # 10MB
    backup_count: 3
```

### Defaults

| Config Key | Default | Justification |
|-----------|---------|---------------|
| `capture.mode` | `auto` | Resolution chain picks best mode |
| `capture.lanes.<any>.enabled` | `false` | Opt-in, not opt-out |
| `capture.lanes.<any>.event_types` | `[]` (all when enabled) | Allowlist, not denylist |
| `capture.audit.enabled` | `true` | Always audit by default |
| `capture.audit.path` | `.dopemux/capture_audit.log` | Project-local |
| `capture.audit.max_bytes` | 10MB | Prevent disk exhaustion |
| `capture.audit.backup_count` | 3 | 40MB max total audit storage |

### Audit Log Format

```
2026-02-11T21:30:00Z | CAPTURE | mode=plugin | lane=agent:primary | type=decision.logged | id=a1b2c3... | inserted=true
2026-02-11T21:30:01Z | POLICY  | lane=agent:primary | enabled=true | event_types=[decision.logged,task.completed]
2026-02-11T21:30:02Z | SKIP    | lane=sandbox:shell | reason=lane_disabled
```

### Enforcement Rules

1. **No implicit injection**: Capture NEVER happens unless explicitly enabled per lane
2. **Audit everything**: Every capture attempt (success or skip) logged
3. **Policy changes audited**: Enabling/disabling a lane produces an audit entry
4. **Fail-closed on config error**: Invalid config disables capture, does not silently enable
5. **Lane identity required**: Capture without lane identity logs as `lane=unknown` and SKIPS

### Runtime Validation

```python
def should_capture(lane: str, event_type: str, config: CaptureConfig) -> bool:
    """Determine if capture should proceed for this lane + event_type."""
    lane_config = config.lanes.get(lane)

    if lane_config is None:
        # Unknown lane = disabled (fail-closed)
        audit_log("SKIP", lane=lane, reason="unknown_lane")
        return False

    if not lane_config.enabled:
        audit_log("SKIP", lane=lane, reason="lane_disabled")
        return False

    if lane_config.event_types and event_type not in lane_config.event_types:
        audit_log("SKIP", lane=lane, reason="event_type_not_in_allowlist")
        return False

    return True
```

---

## 5. Stop Conditions

Any of these REJECT the design:

1. **Non-determinism in event_id**: If any path introduces UUID-based IDs or wallclock substitution for event identity, reject.
2. **Mutable updates to chronicle**: If any path updates (rather than inserts) raw_activity_events, reject.
3. **Implicit capture**: If any lane captures without explicit opt-in config, reject.
4. **Rollup writes to project ledger**: If global rollup writes to any project's chronicle.sqlite, reject.
5. **Unaudited policy changes**: If lane enable/disable happens without audit log entry, reject.

---

## 6. Recommended Execution Order

```
Phase 1 (Foundation):
  CLI-INT-006 → CLI-INT-003 → CLI-INT-004 → CLI-INT-015

Phase 2 (Claude Code Integration):
  CLI-INT-001 → CLI-INT-005 → CLI-INT-012 → CLI-INT-007

Phase 3 (Cross-Adapter):
  CLI-INT-002 → CLI-INT-009 → CLI-INT-013

Phase 4 (Retrieval + Polish):
  CLI-INT-010 → CLI-INT-011 → CLI-INT-014 → CLI-INT-008

Phase 5 (Documentation):
  CLI-INT-016
```

Dependencies: 006 → 003 → 004 → 001 → 005 (serial).
Parallelizable: 007 || 012, 010 || 011 || 014, 002 || 013.
