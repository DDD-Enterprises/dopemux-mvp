---
id: ADR-213-dual-capture-canonical-ledger
title: ADR-213 Dual Capture Canonical Ledger
type: adr
owner: '@hu3mann'
last_review: '2026-02-08'
next_review: '2026-05-08'
author: '@hu3mann'
date: '2026-02-08'
prelude: ADR-213 Dual Capture Canonical Ledger (adr) defining convergent capture paths and read-only global rollup
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to: []
---
# ADR-213: Dual-Capture Canonical Ledger Design

**Date**: 2026-02-08
**Status**: Accepted
**Decision Makers**: Claude Sonnet 4.5 (Implementation)
**Tags**: [memory, capture, architecture, dual-capture, canonical-ledger]

---

## Context

Dopemux memory capture operates in multiple modes:
- **plugin**: Claude Code hook-based capture
- **cli**: Direct CLI command capture
- **mcp**: MCP server bridge capture

Prior to this ADR, the design lacked explicit guarantees about:
1. Where each mode writes capture events
2. Whether plugin vs MCP produce identical event_id for same events
3. How global rollup interacts with per-project truth

This created ambiguity about the "authoritative" capture path and potential for divergent ledgers.

---

## Decision

**All capture modes write to the same canonical per-project ledger**: `repo_root/.dopemux/chronicle.sqlite`

**Global rollup is a read-only index**, not a second authority for project truth.

---

## Design Principles

### 1. Canonical Ledger (Single Source of Truth)

**Location**: `repo_root/.dopemux/chronicle.sqlite`

**Writers**:
- plugin mode capture
- cli mode capture
- mcp mode capture
- All write through shared `emit_capture_event()` client

**Guarantees**:
- Deterministic repo root resolution (`.git` or `.dopemux` marker)
- Capture fails closed if repo root cannot be resolved
- Duplicate-safe inserts via deterministic `event_id` (INSERT OR IGNORE)

### 2. Convergent Event Identity

**Same event from different modes produces identical `event_id`**:

```python
# Plugin mode capture
plugin_result = emit_capture_event(
    {"event_type": "shell.command", "payload": {"command": "pytest"}},
    mode="plugin",
    repo_root=repo_root
)

# MCP mode capture (same event)
mcp_result = emit_capture_event(
    {"event_type": "shell.command", "payload": {"command": "pytest"}},
    mode="mcp",
    repo_root=repo_root
)

# Guarantee: plugin_result.event_id == mcp_result.event_id
```

**Implementation**:
- `event_id` derived from content hash (event_type + payload + ts_utc)
- Mode does not influence event_id generation
- Enables idempotent retry across capture paths

### 3. Global Rollup (Read-Only Index)

**Purpose**: Cross-project lookup over project-owned chronicle ledgers

**Location**: `~/.dopemux/global_index.sqlite`

**Operations**:
- ✅ **READ**: Project ledgers opened in read-only mode
- ✅ **INDEX**: Stores pointers and bounded summaries
- ❌ **NEVER WRITES**: To project ledgers
- ❌ **NEVER OVERRIDES**: Per-project truth

**Tables**:
- `projects`: Registry of known project repo roots
- `promoted_pointers`: Metadata pointers to project ledger entries

**Guarantees**:
- Global rollup never writes to `repo_root/.dopemux/chronicle.sqlite`
- Global rollup only reads promoted events, never modifies them
- Project ledger remains authoritative source of truth

---

## Capture Mode Matrix

| Mode | Trigger | Ledger Path | Event ID | Use Case |
|------|---------|-------------|----------|----------|
| **plugin** | Claude Code hooks | `repo_root/.dopemux/chronicle.sqlite` | Content hash | Auto-capture during Claude sessions |
| **cli** | `dopemux memory capture` | `repo_root/.dopemux/chronicle.sqlite` | Content hash | Manual/scripted capture |
| **mcp** | MCP tool calls | `repo_root/.dopemux/chronicle.sqlite` | Content hash | Bridge from external tools |
| **auto** | Context-driven selection | `repo_root/.dopemux/chronicle.sqlite` | Content hash | Smart mode resolution |

**Key Properties**:
- All modes write to **same ledger**
- All modes produce **identical event_id** for same content
- All modes share **single schema** and redaction pipeline

---

## Consequences

### Positive

✅ **Single Source of Truth**: No ambiguity about authoritative capture location
✅ **Idempotent Retry**: Same event from different modes dedupes correctly
✅ **Mode Transparency**: Client code doesn't need to know capture mode
✅ **Safe Rollup**: Global index cannot corrupt project data
✅ **Testable**: Convergence properties are unit-testable

### Negative

⚠️ **Repo Requirement**: Capture requires valid repo root (fails closed otherwise)
⚠️ **No Global-First**: Cannot capture to global index directly
⚠️ **Mode Coupling**: All modes must use shared capture client

### Mitigations

- Fail-closed behavior provides clear user feedback for missing repo
- Global rollup build command makes cross-project search explicit
- Shared capture client ensures consistent behavior

---

## Verification

Tests landing with this ADR:

1. **Dual Capture Convergence**:
   - `test_plugin_and_mcp_modes_produce_identical_event_id()`
   - Verifies same event → same event_id across modes

2. **Capture Failure Modes**:
   - `test_capture_fails_closed_without_repo_root()`
   - Verifies deterministic failure outside repo

3. **Global Rollup Safety**:
   - `test_global_rollup_never_writes_to_project_ledger()`
   - Verifies read-only guarantee

4. **Existing Unit Tests**:
   - `test_plugin_and_cli_modes_share_single_ledger()` (already exists)
   - `test_duplicate_retry_is_ignored()` (already exists)

---

## Implementation Notes

**No Code Changes Required**: Current implementation already satisfies this design.

**This ADR documents observed behavior** to harden guarantees and enable future refactoring with confidence.

**Critical Invariants**:
1. `emit_capture_event()` is the only write path to project ledgers
2. `event_id` generation is content-based, mode-independent
3. Global rollup uses read-only SQLite connections

---

## References

- **Architecture Doc**: `docs/spec/dope-memory/v1/01_architecture.md`
- **Pipeline Doc**: `docs/spec/dope-memory/v1/02_derived_memory_pipeline.md`
- **Capture Client**: `src/dopemux/memory/capture_client.py`
- **Global Rollup**: `src/dopemux/memory/global_rollup.py`
- **Unit Tests**: `tests/unit/test_memory_capture_client.py`
- **Integration Tests**: `tests/integration/test_dual_capture_convergence.py`

---

## Alternatives Considered

### Alt 1: Mode-Specific Ledgers

**Rejected**: Would create divergent truth, violate single-source principle

### Alt 2: Global-First Capture

**Rejected**: Would make global index authoritative, violate project ownership

### Alt 3: Mode-Dependent Event IDs

**Rejected**: Would break idempotent retry across capture modes

---

## Decision Authority

This design is **deterministic and testable**, not subject to future debate.

Any change must:
1. Preserve canonical ledger location
2. Preserve convergent event_id semantics
3. Preserve global rollup read-only guarantee
4. Pass all verification tests

---

**Status**: ✅ Accepted and Implemented
