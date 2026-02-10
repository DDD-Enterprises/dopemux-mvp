# HANDOFF: Packet C -> Packet D

**Status**: BINDING CONTRACT
**Author**: Claude Opus 4.6 (Packet C executor)
**Date**: 2026-02-08
**Purpose**: Opus 4.6 (Packet D) must treat this document as law.

---

## 1. Canonical Ledger Invariant

**Exact path**: `repo_root/.dopemux/chronicle.sqlite`

**Override**: `DOPEMUX_CAPTURE_LEDGER_PATH` environment variable (used by tests, Docker).

**Confirmation**: No other writable ledger exists. Specifically:

| Former path | Status | Evidence |
|---|---|---|
| `~/.dope-memory/{workspace_id}/chronicle.db` | **ELIMINATED** | `Path.home() / ".dope-memory"` removed from all Python write paths |
| `mcp/server.py:25` `DEFAULT_DATA_DIR` | **REMOVED** | Replaced by `resolve_canonical_ledger()` import |
| `dope_memory_main.py:54` `DATA_DIR` | **REMOVED** | Replaced by `resolve_canonical_ledger()` at call site |
| `eventbus_consumer.py:38` `DATA_DIR` | **REMOVED** | Replaced by `resolve_canonical_ledger()` at call site |
| `postgres_mirror_sync.py:53` `self.data_dir` | **REMOVED** | Replaced by `resolve_canonical_ledger()` at call site |

**Resolution module**: `services/working-memory-assistant/canonical_ledger.py`
**Resolution logic**: Mirrors `src/dopemux/memory/capture_client.py` lines 56-70, 185-189.

---

## 2. Capture Convergence Proof

### Test names and evidence

| Test | File | What it proves |
|---|---|---|
| `test_capture_client_writes_to_canonical_path` | `test_canonical_ledger_convergence.py` | capture_client uses canonical ledger |
| `test_wma_store_writes_to_canonical_path` | `test_canonical_ledger_convergence.py` | WMA resolves to same canonical path |
| `test_capture_client_and_wma_store_share_ledger` | `test_canonical_ledger_convergence.py` | Both resolve to identical file |
| `test_wma_store_reads_capture_client_writes` | `test_canonical_ledger_convergence.py` | Cross-adapter read/write verified |
| `test_all_capture_modes_write_to_same_ledger` | `test_canonical_ledger_convergence.py` | plugin/cli/mcp all converge |
| `test_no_chronicle_db_files_created` | `test_canonical_ledger_convergence.py` | No legacy .db files |
| `test_canonical_ledger_fails_closed_without_markers` | `test_canonical_ledger_convergence.py` | Fail-closed verified |
| `test_store_insert_raw_event_is_idempotent` | `test_canonical_ledger_convergence.py` | INSERT OR IGNORE dedup |
| `test_plugin_and_mcp_modes_produce_identical_event_id` | `test_dual_capture_convergence.py` | ADR-213 event_id convergence |
| `test_global_rollup_never_writes_to_project_ledger` | `test_dual_capture_convergence.py` | Read-only global rollup |

**Test results**: 18/18 passed (10 new + 8 existing ADR-213 tests).
**WMA service tests**: 94/94 passed.

### Additional fix: store.py INSERT OR IGNORE

`chronicle/store.py:100` changed from `INSERT INTO` to `INSERT OR IGNORE INTO` for `raw_activity_events`. This is required for convergence: when two write paths (capture_client + EventBus consumer) hit the same database with the same event_id, the second must be silently deduplicated, not crash.

---

## 3. Known Unresolved Issues

These were **acknowledged but NOT fixed** in Packet C per scope constraints.

### 3.1 Provenance gap (F3 from DESIGN_DELTA)

- `PromotedEntry` dataclass has no `source_event_id` field
- `work_log_entries` table has no `source_event_id` column
- Promoted memories cannot be traced back to raw events
- **Packet D must address this**

### 3.2 Timestamp semantics (D2 from DESIGN_DELTA)

- `store.py:172` uses wall-clock `datetime.now(timezone.utc)` for promotion timestamps
- `trajectory/manager.py:50,77` uses wall-clock for trajectory updates
- Replay ordering depends on event time, but promotion metadata uses wall-clock
- **Packet D must define which timestamps are authoritative**

### 3.3 Conditional convergence (T2 from DESIGN_DELTA)

- Event_id fingerprint includes `source` field
- `_default_source_for_mode()` returns different values per mode: `claude_hook`, `mcp`, `cli`
- Same event captured by different adapters will produce DIFFERENT event_ids unless `source` is explicit
- Integration test masks this by setting `"source": "test"` explicitly
- **Packet D must decide: normalize source out of fingerprint, or accept mode-specific IDs**

### 3.4 Dead code in reflection (F9 from DESIGN_DELTA)

- `reflection.py:196-222` contains three confused sort attempts with inline comments
- Final sort is correct (stable multi-key sort) but dead code remains
- **Not a correctness issue, but a trust issue**

### 3.5 project_id injection after redaction (D7 from DESIGN_DELTA)

- `capture_client.py:325`: `redacted_payload["project_id"] = project_id`
- Absolute filesystem path injected into payload after redaction, before fingerprint
- Changes across machines will produce different event_ids for same logical event
- **Packet D must evaluate: is project_id in fingerprint intentional?**

### 3.6 Remaining non-Python legacy references

- `Dockerfile.dope-memory:47-48,53`: Creates `~/.dope-memory` dir and VOLUME
- `docker-compose.smoke.yml:192`: Mounts `dope_memory_data` volume
- These are deployment artifacts, not Python code paths
- **Must be updated when Docker deployment is reconfigured**

---

## 4. Non-Negotiables

These invariants were established by ADR-213 and reinforced by Packet C.

1. **Explicit-only injection**: No implicit writes to the chronicle. All captures go through `capture_client.emit_capture_event()` or `canonical_ledger.resolve_canonical_ledger()`.

2. **Append-only chronicle**: `INSERT OR IGNORE` semantics. No UPDATE, no DELETE (except TTL cleanup of `raw_activity_events`).

3. **Deterministic promotion**: Promotion engine produces identical output for identical input. Phase 1 allowlist: 7 event types with fixed importance scores.

4. **Global rollup read-only**: `global_rollup.py` uses `?mode=ro` SQLite connections. Global index NEVER writes to project ledgers.

5. **Fail-closed capture**: If repo root cannot be determined, capture raises `CaptureError` / `CanonicalLedgerError`. No fallback paths.

---

## 5. What Opus May Change (Packet D)

- **Schema**: Add columns (`source_event_id`, provenance fields). Propose migrations.
- **Semantics**: Define truth model (fact vs memory vs derived). Define timestamp authority.
- **Metadata**: Add fields to `PromotedEntry`, `ReflectionCard`. Propose tagging conventions.
- **Replay contract**: Define deterministic replay ordering rules.
- **Documentation**: Update ADRs and specs to reflect semantic corrections.

---

## 6. What Opus Must NOT Change (Packet D)

- **Ledger location**: `repo_root/.dopemux/chronicle.sqlite` — frozen.
- **Capture adapters**: `capture_client.py` write path — frozen.
- **Single-ledger rule**: All write paths converge to one file — frozen.
- **canonical_ledger.py resolution logic**: Shared by all WMA services — frozen.
- **INSERT OR IGNORE semantics**: Required for convergence — frozen.
- **Fail-closed behavior**: No fallback to `~/.dope-memory` — frozen.

---

## Files Changed in Packet C

### Created
| File | Purpose |
|---|---|
| `services/working-memory-assistant/canonical_ledger.py` | Canonical ledger path resolution (shared) |
| `tests/integration/test_canonical_ledger_convergence.py` | Convergence proof tests (10 tests) |

### Modified
| File | Change |
|---|---|
| `services/working-memory-assistant/mcp/server.py` | Remove `DEFAULT_DATA_DIR`, use `resolve_canonical_ledger()` |
| `services/working-memory-assistant/dope_memory_main.py` | Remove `DATA_DIR`, `data_dir` param; use `resolve_canonical_ledger()` |
| `services/working-memory-assistant/eventbus_consumer.py` | Remove `DATA_DIR`, `data_dir` param; use `resolve_canonical_ledger()` |
| `services/working-memory-assistant/postgres_mirror_sync.py` | Remove `data_dir` param; use `resolve_canonical_ledger()` |
| `services/working-memory-assistant/chronicle/store.py` | `INSERT` -> `INSERT OR IGNORE` for `raw_activity_events` |
| `services/working-memory-assistant/tests/test_eventbus_consumer.py` | Use `DOPEMUX_CAPTURE_LEDGER_PATH` env instead of `data_dir` |
| `services/working-memory-assistant/tests/test_phase2_reflection_trajectory.py` | Same |
| `services/working-memory-assistant/tests/test_trajectory_boost_in_ranking.py` | Same |

### Hard-Failed Legacy Paths
| File | Line | Former behavior | New behavior |
|---|---|---|---|
| `mcp/server.py:25` | `DEFAULT_DATA_DIR = Path.home() / ".dope-memory"` | **REMOVED** | `resolve_canonical_ledger()` |
| `dope_memory_main.py:54` | `DATA_DIR = Path(os.getenv(..., "~/.dope-memory"))` | **REMOVED** | `resolve_canonical_ledger()` |
| `eventbus_consumer.py:38` | `DATA_DIR = Path(os.getenv(..., "~/.dope-memory"))` | **REMOVED** | `resolve_canonical_ledger()` |
| `postgres_mirror_sync.py:53` | `self.data_dir = data_dir or Path.home() / ".dope-memory"` | **REMOVED** | `resolve_canonical_ledger()` |

---

*This handoff artifact is final. Opus 4.6 executing Packet D must not reinterpret these constraints.*
