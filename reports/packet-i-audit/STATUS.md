# Packet I-AUDIT — STATUS
Date: 2026-02-12
Auditor: Claude Opus 4.6 (Skeptical Systems Auditor)
Branch/Commit: codex/pm-plane/rails-telemetry / 2a3002818ea5f588009039dcf917a2999ec3fe65
Execution Mode: Path A (Fresh init canonical — schema.sql is source of truth)

## Verdict
- **Overall: PASS**
- Stop Conditions Triggered: **NONE**

---

## Stop Condition Assessment

| Stop Condition | Status | Evidence |
|---|---|---|
| STOP-A1: Required semantics only in migrations, not schema.sql | NOT TRIGGERED | schema.sql contains all provenance fields (L69-74), scoped index (L96-98), reflection provenance (L143) |
| STOP-1: event_id fingerprint includes source or project_id | NOT TRIGGERED | `_deterministic_event_id` excludes both; project_id injected AFTER event_id generation (capture_client.py:406-420) |
| STOP-2: promoted ts_utc is wall clock | NOT TRIGGERED | `ts_utc = source_event_ts_utc` (store.py:411); test_time_semantics.py verifies |
| STOP-3: supersession uniqueness not scoped | NOT TRIGGERED | schema.sql:96-98: `(workspace_id, instance_id, supersedes_entry_id)` |
| STOP-4: MCP responses inconsistent/missing success | NOT TRIGGERED | All 7 tools return `success` field; test_all_mcp_tools_return_success_field verifies |
| STOP-5: correction idempotency declared but not enforced | NOT TRIGGERED | store.py:542-551 enforces lookup-before-insert; test_memory_correct_idempotency verifies |

---

## A) Packet D/E — Identity + Provenance + Time

### A1 — Event ID Fingerprint Normalization
Status: **PASS**
Claim: `event_id` fingerprint excludes adapter metadata (`source`) and machine-local metadata (`project_id`).
Evidence:
- [x] src/dopemux/memory/capture_client.py:291-320 (fingerprint formula: event_type|session_id|ts_bucket|payload)
- [x] src/dopemux/memory/capture_client.py:406-420 (project_id injected AFTER event_id generation)
- [x] tests/unit/test_event_id_convergence.py:6-34 (cross-adapter convergence verified)

Notes: `source` is not a parameter of `_deterministic_event_id`. `project_id` is injected into payload at line 420, after event_id is already computed at line 408-417.

### A2 — Mandatory Provenance Fields on work_log_entries
Status: **PASS**
Claim: `work_log_entries` has NOT NULL: source_event_id, source_event_type, source_adapter, source_event_ts_utc, promotion_rule, promotion_ts_utc.
Evidence:
- [x] services/working-memory-assistant/chronicle/schema.sql:69-74

Notes: All six provenance fields are `TEXT NOT NULL` in schema.sql. For Path A (fresh init), this is the runtime definition. Application layer also validates at store.py:366-371.

### A3 — Time Authority
Status: **PASS**
Claim: promoted `ts_utc` equals event time authority (`source_event_ts_utc`), not promotion wall-clock.
Evidence:
- [x] services/working-memory-assistant/chronicle/store.py:411 (`ts_utc = source_event_ts_utc`)
- [x] services/working-memory-assistant/chronicle/store.py:412 (`promotion_ts_utc = datetime.now(...)` — separate field)
- [x] services/working-memory-assistant/tests/unit/test_time_semantics.py:7-42

Notes: Line 411 comment: "Event time (authoritative for chronology)". Line 412: promotion_ts_utc is wall clock but stored separately. Test asserts `row["ts_utc"] == past_ts`.

### A4 — Deterministic Promoted Entry IDs
Status: **PASS**
Claim: promoted entry id is deterministic (sha256), not uuid4.
Evidence:
- [x] services/working-memory-assistant/chronicle/store.py:407-408 (`sha256(source_event_id|promotion_rule|source_event_ts_utc)`)
- [x] services/working-memory-assistant/tests/unit/test_deterministic_entry_id.py:7-38
- [x] uuid4 in store.py only at line 275 (raw events, NOT promoted path) and line 857 (issue links, NOT promoted path)

Notes: `uuid4` does NOT appear on the promoted entry path. Manual corrections use `_generate_ulid()` for source_event_id which then feeds into the deterministic sha256 for entry_id.

### A5 — Reflection provenance persisted
Status: **PASS**
Claim: reflection cards persist and return source_entry_ids_json.
Evidence:
- [x] services/working-memory-assistant/chronicle/schema.sql:143 (`source_entry_ids_json TEXT NOT NULL DEFAULT '[]'`)
- [x] services/working-memory-assistant/chronicle/store.py:905 (insert stores field)
- [x] services/working-memory-assistant/chronicle/store.py:983-984 (retrieval parses field)
- [x] services/working-memory-assistant/tests/unit/test_reflection_provenance.py:7-68

Notes: Both persistence and retrieval verified. Staleness detection (Packet F §7.1) also works — see test_supersession_semantics.py:300-348.

### A6 — Replay Ordering Contract
Status: **PASS**
Claim: replay ordering is event-time ascending, with deterministic tie-break.
Evidence:
- [x] services/working-memory-assistant/chronicle/store.py:654 (`ORDER BY source_event_ts_utc ASC, id ASC`)
- [x] services/working-memory-assistant/tests/unit/test_replay_ordering.py:6-38

Notes: Out-of-order insertion verified to produce event-time-ordered replay. Pagination also tested (lines 40-67).

---

## B) Packet F/G — Supersession + Scoping

### B1 — DB Enforces Linearity
Status: **PASS**
Claim: DB prevents branching supersession chains.
Evidence:
- [x] services/working-memory-assistant/chronicle/schema.sql:96-98 (UNIQUE partial index on supersedes_entry_id)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:74-84 (fork prevention verified)
- [x] services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py:68-75 (IntegrityError on duplicate)

Notes: The scoped UNIQUE index `idx_worklog_supersedes_unique_scoped` prevents two entries from superseding the same entry within the same workspace/instance. Application layer also validates before hitting the DB constraint (store.py:392-397).

### B2 — Supersession Scoped to workspace/instance
Status: **PASS**
Claim: supersession uniqueness and helper queries are scoped to workspace_id and instance_id.
Evidence:
- [x] services/working-memory-assistant/chronicle/schema.sql:96-98 (`ON work_log_entries(workspace_id, instance_id, supersedes_entry_id)`)
- [x] services/working-memory-assistant/chronicle/store.py:100-106 (`_get_superseded_entry_ids` — WHERE workspace_id = ? AND instance_id = ?)
- [x] services/working-memory-assistant/chronicle/store.py:109-137 (`_get_chain_depth` — scoped)
- [x] services/working-memory-assistant/chronicle/store.py:139-161 (`_resolve_chain_head` — scoped)
- [x] services/working-memory-assistant/chronicle/store.py:163-170 (`_is_entry_superseded` — scoped)
- [x] services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py:44-75 (cross-scope reuse allowed)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:353-397 (scoping verified)

Notes: ALL five supersession helper methods include workspace_id and instance_id in their WHERE clauses. DB index is scoped. Tests verify cross-workspace isolation.

### B3 — Write-path Guardrails
Status: **PASS**
Claim: corrections can only target chain head; depth limit enforced; tombstone semantics present.
Evidence:
- [x] services/working-memory-assistant/chronicle/store.py:384-404 (target existence, head-only, depth limit)
- [x] services/working-memory-assistant/chronicle/store.py:36 (MAX_CHAIN_DEPTH = 10)
- [x] services/working-memory-assistant/chronicle/store.py:586-590 (retraction tombstone: [RETRACTED], outcome=abandoned)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:89-107 (depth limit test)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:246-265 (retraction semantics test)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:269-276 (must-target-head test)

Notes: Three guardrails verified: (1) target must exist (store.py:386-389), (2) target must be chain head (store.py:392-397), (3) chain depth <= 10 (store.py:399-404). Retraction tombstone sets `[RETRACTED]` prefix, `outcome=abandoned`, `importance_score` capped at 3.

### B4 — Default Filtering Hides Superseded
Status: **PASS**
Claim: search/count/replay hide superseded by default; optional include path exists.
Evidence:
- [x] services/working-memory-assistant/chronicle/store.py:708-714 (search_work_log: excludes superseded unless include_superseded=True)
- [x] services/working-memory-assistant/chronicle/store.py:642-646 (replay_work_log: excludes in replay_current mode)
- [x] services/working-memory-assistant/chronicle/store.py:806-811 (count_work_log: excludes superseded)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:129-140 (search exclusion)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:145-168 (include_superseded with annotations)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:173-185 (replay_current hides)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:190-208 (replay_full shows with annotations)
- [x] services/working-memory-assistant/tests/unit/test_supersession_semantics.py:213-221 (count exclusion)

Notes: All three query paths (search, replay, count) exclude superseded entries by default. include_superseded flag provides chain annotations. replay_full mode shows all entries with chain metadata.

---

## C) Packet H — Hardening

### C1 — Schema and migrations aligned
Status: **PASS**
Claim: schema.sql matches migration end-state; no drift.
Evidence:
- [x] schema.sql declares v1.2.1 (line 174: `VALUES ('v1.2.1', datetime('now'))`)
- [x] All migration end-state features present in schema.sql:
  - Provenance NOT NULL (lines 69-74) — from v1.1.0
  - source_entry_ids_json (line 143) — from v1.1.0
  - Scoped unique index (lines 96-98) — from v1.2.1
- [x] Legacy unscoped index (v1.1.1/v1.2.0) correctly absent from schema.sql
- [x] Path A init: schema.sql runs via executescript (store.py:77-78), then migrations skip (sqlite_migrations.py:111-115: version_tuple <= current_max)

Notes: For Path A, `initialize_schema()` runs schema.sql (creating all tables with v1.2.1), then `apply_chronicle_migrations()` finds all migrations already at or below v1.2.1 and skips them. Schema.sql is the complete, authoritative end-state.

### C2 — MCP response envelopes include success
Status: **PASS**
Claim: all MCP tools return consistent envelope with `success: true/false`.
Evidence:
- [x] services/working-memory-assistant/mcp/server.py: Lines 249, 322, 456, 488, 492, 519, 531, 600, 648, 650 — all return `success` field
- [x] docs/spec/dope-memory/v1/07_mcp_contracts.md:3 ("All responses include a `success: boolean` field")
- [x] services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py:226-273 (test_all_mcp_tools_return_success_field)

Notes: All 7 MCP tools (memory_search, memory_store, memory_recap, memory_mark_issue, memory_link_resolution, memory_replay_session, memory_correct) return `success` on both success and failure paths. Test covers all tools.

### C3 — Correction idempotency (retries safe)
Status: **PASS**
Claim: memory_correct supports idempotency_key to prevent duplicates.
Evidence:
- [x] services/working-memory-assistant/chronicle/store.py:542-551 (lookup-before-insert with idempotency_key)
- [x] services/working-memory-assistant/mcp/server.py:621 (idempotency_key parameter accepted)
- [x] services/working-memory-assistant/mcp/server.py:646-647 (passed through to store)
- [x] services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py:171-223 (test_memory_correct_idempotency)

Notes: When `idempotency_key` is provided, store constructs `source_event_id = f"manual:{idempotency_key}"` and queries for existing correction with matching source_event_id + supersedes_entry_id. If found, returns existing entry_id without inserting. Test verifies same key → same entry_id and count == 1 in DB. The key is optional — callers who don't provide it accept non-idempotent behavior, which is documented.
