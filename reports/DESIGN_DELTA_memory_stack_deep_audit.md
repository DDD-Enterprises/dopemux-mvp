# DESIGN DELTA: Memory Stack Deep Audit

**Author:** Claude Opus 4.6 (Principal Systems Architect / Skeptical Auditor)
**Date:** 2026-02-08
**Scope:** End-to-end Dope-Memory stack: capture through global rollup
**Constraint:** Inspection and analysis only. No code changes.
**Method:** Independent line-by-line code review of all 8 implementation files, schema, tests, and specs.

---

## 1. Memory Stack Diagram

```
                    ┌─────────────────────────────────────────┐
                    │           EVENT PRODUCERS               │
                    │  Claude hooks · CLI · MCP · Git watcher │
                    │  TaskMaster · Test runner · CI reporter  │
                    └────────────┬────────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────────┐
                    │   STAGE 0: CAPTURE                      │
                    │   src/dopemux/memory/capture_client.py   │
                    │                                          │
                    │   Mode resolution (plugin/cli/mcp/auto)  │
                    │   Repo root resolution (.git/.dopemux)   │
                    │   Redaction (fail-closed)                │
                    │   Deterministic event_id (SHA-256)       │
                    │   INSERT OR IGNORE (idempotent)          │
                    │                                          │
                    │   ► repo_root/.dopemux/chronicle.sqlite  │
                    │     table: raw_activity_events            │
                    │     TTL: 7 days                          │
                    └─────┬────────────────────────────────────┘
                          │
            ┌─────────────▼───────────────────────────┐
            │  OPTIONAL: Redis Streams fan-out          │
            │  stream: activity.events.v1               │
            │  (best-effort, skipped if redis absent)   │
            └─────────────┬───────────────────────────┘
                          │
            ┌─────────────▼───────────────────────────┐
            │  STAGE 1: NORMALIZE                      │
            │  (in-memory, deterministic transforms)    │
            │  No probabilistic ranking or mutation     │
            └─────────────┬───────────────────────────┘
                          │
            ┌─────────────▼───────────────────────────┐
            │  STAGE 2: PROMOTE                        │
            │  services/wma/promotion/promotion.py      │
            │                                           │
            │  Allowlist: 7 event types                 │
            │  Redaction: second pass (fail-closed)     │
            │  Importance: deterministic mapping         │
            │  Tags: explicit first, inferred sorted     │
            │                                           │
            │  ► chronicle.sqlite                       │
            │    table: work_log_entries (durable)       │
            └───┬───────────────────┬──────────────────┘
                │                   │
    ┌───────────▼────┐   ┌─────────▼─────────────┐
    │ STAGE 3: DERIVE│   │ POSTGRES MIRROR (async)│
    │                │   │ postgres_mirror_sync.py │
    │ Reflection     │   │ dm_* tables            │
    │ Trajectory     │   │ Idempotent upserts     │
    │ Issue links    │   └────────────────────────┘
    │                │
    │ reflection/    │
    │   reflection.py│
    │ trajectory/    │
    │   manager.py   │
    └───────┬────────┘
            │
    ┌───────▼────────────────────────────────────┐
    │  MCP SERVER                                 │
    │  services/wma/mcp/server.py                  │
    │                                              │
    │  ⚠ WRITES TO DIFFERENT DB:                  │
    │  ~/.dope-memory/{workspace_id}/chronicle.db  │
    │  NOT to repo_root/.dopemux/chronicle.sqlite  │
    │                                              │
    │  memory_search    (keyword + filters, Top-3) │
    │  memory_store     (manual entry)             │
    │  memory_recap     (deterministic cards)      │
    │  memory_mark_issue (STUB - returns true)     │
    │  memory_link_resolution                      │
    │  memory_replay_session (WRONG ORDER)         │
    └───────┬────────────────────────────────────┘
            │
    ┌───────▼────────────────────────────────────┐
    │  STAGE 4: GLOBAL ROLLUP (read-only)        │
    │  src/dopemux/memory/global_rollup.py        │
    │                                              │
    │  ~/.dopemux/global_index.sqlite              │
    │  tables: projects, promoted_pointers         │
    │  CLI: dopemux memory rollup build/list/search│
    │  NEVER writes to project ledgers             │
    └────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Evidence Matrix

### Stage 0: Capture

| Question | Answer | Evidence |
|----------|--------|----------|
| What data enters? | Event envelope: id, ts_utc, workspace_id, instance_id, session_id, event_type, source, payload | `capture_client.py:295-408` |
| What transforms? | Redaction (deterministic regex + denylist), event_id generation (SHA-256 of fingerprint) | `capture_client.py:242-263, 323-324` |
| Where stored? | `repo_root/.dopemux/chronicle.sqlite` table `raw_activity_events` | `capture_client.py:340, 352-373` |
| Who reads it? | Promotion engine, EventBus consumer, retention cleanup job | `promotion.py`, `eventbus_consumer.py` |
| Can it be replayed? | Yes - INSERT OR IGNORE semantics, deterministic event_id | `capture_client.py:352` |
| Can it be audited? | Yes - append-only with created_at_utc, deterministic IDs | Schema design |
| Can it drift silently? | **RISK: Yes** - see Finding F1, N1, N2 below | See Failure Mode Matrix |

### Stage 2: Promote

| Question | Answer | Evidence |
|----------|--------|----------|
| What data enters? | Normalized events from Stage 1 (7 promotable types) | `promotion.py:14-24` |
| What transforms? | Deterministic mapping: event_type -> (category, entry_type, outcome, importance_score) | `promotion.py:27-35, 161-391` |
| Where stored? | `chronicle.sqlite` table `work_log_entries` | `store.py:144-214` |
| Who reads it? | MCP tools, reflection generator, trajectory manager, global rollup | Multiple consumers |
| Can it be replayed? | Partially - promotion is deterministic but entry_id is uuid4() (non-deterministic) | `store.py:171` -- **Finding F2** |
| Can it be audited? | **No** - no provenance pointer from work_log_entry back to raw event | **Finding F3 (CRITICAL)** |
| Can it drift silently? | **RISK: Yes** - summary truncation is lossy, no hash of original | `promotion.py:181,205,238,268` |

### Stage 3: Derive

| Question | Answer | Evidence |
|----------|--------|----------|
| What data enters? | Curated work_log_entries in time window | `reflection.py:60-66` |
| What transforms? | Deterministic rule-based: top decisions, blockers, progress, trajectory | `reflection.py:86-106` |
| Where stored? | `chronicle.sqlite` tables: reflection_cards, trajectory_state | `store.py:410-583` |
| Who reads it? | MCP tools (memory_recap), trajectory manager | `server.py:312-443` |
| Can it be replayed? | Yes with idempotency check (5-min window dedup) | `reflection.py:54-55` |
| Can it be audited? | Partially - source_entry_ids tracked in memory but not stored in DB | `reflection.py:186-187` -- **Finding F4** |
| Can it drift silently? | **RISK: Yes** - trajectory summary is lossy 1-sentence | `reflection.py:324-336` |

### Stage 4: Global Rollup

| Question | Answer | Evidence |
|----------|--------|----------|
| What data enters? | work_log_entries from all registered project ledgers (read-only) | `global_rollup.py:238-283` |
| What transforms? | Summary truncation to 500 chars, pointer materialization | `global_rollup.py:16, 264-266` |
| Where stored? | `~/.dopemux/global_index.sqlite` tables: projects, promoted_pointers | `global_rollup.py:200-235` |
| Who reads it? | CLI `dopemux memory rollup search`, future cross-project tools | `global_rollup.py:379-429` |
| Can it be replayed? | Yes - idempotent upserts, read-only source access | `global_rollup.py:194, 316-344` |
| Can it be audited? | Yes - project_id + event_id form provenance | Schema design |
| Can it drift silently? | **RISK: Yes** - summaries truncated, no staleness detection | **Finding F5** |

---

## 3. Failure Mode Matrix (Likelihood x Impact)

### Confirmed (independently verified against code)

| ID | Failure Mode | Likelihood | Impact | Risk | Evidence |
|----|-------------|-----------|--------|------|----------|
| **N1** | **CRITICAL: MCP server writes to wrong database**: server.py creates DBs at `~/.dope-memory/{workspace_id}/chronicle.db` while capture_client writes to `repo_root/.dopemux/chronicle.sqlite`. Two separate truth stores. | CERTAIN | CRITICAL | **CRITICAL** | `server.py:82` -- `db_path = self.data_dir / workspace_id / "chronicle.db"` vs `capture_client.py:189` -- `repo_root / ".dopemux" / "chronicle.sqlite"` |
| **N2** | **store.py insert_raw_event uses plain INSERT (no OR IGNORE)**: capture_client.py uses `INSERT OR IGNORE` for idempotent dedup. store.py uses plain `INSERT INTO` which will throw IntegrityError on duplicate IDs. Different failure modes on same table. | HIGH | HIGH | **CRITICAL** | `store.py:98` -- `INSERT INTO raw_activity_events` vs `capture_client.py:354` -- `INSERT OR IGNORE INTO raw_activity_events` |
| **N3** | **Convergent event_id depends on explicit source field**: event_id fingerprint includes `source`. If source is auto-derived from mode (plugin->"claude_hook", mcp->"mcp", cli->"cli"), different modes produce different event_ids. ADR-213 convergence only works when source is explicitly provided. | HIGH | HIGH | **CRITICAL** | `capture_client.py:253,305` -- source is in fingerprint AND defaults differ by mode. Test passes only because it sets `"source": "test"` explicitly. |
| F3 | **Missing provenance chain**: No pointer from work_log_entry back to the raw_activity_event that caused it | CERTAIN | HIGH | **CRITICAL** | Promotion writes entry but never stores `source_event_id`. Cannot answer "why does this memory exist?" |
| F6 | **Dead sorting code in reflection.py**: Lines 196-222 contain three confused sorting attempts with inline "Actually, that's still wrong" comments. Final sort at 214-222 is correct but dead attempts remain. | CERTAIN | MEDIUM | **HIGH** | `reflection.py:196-222` -- This erodes trust in correctness. |
| F7 | **memory_replay_session sorts by importance, not time**: Delegates to memory_search which orders by `importance_score DESC`, not chronological | CERTAIN | MEDIUM | **HIGH** | `server.py:534-541` -- A "replay" tool that doesn't replay in order |
| F9 | **memory_mark_issue is a stub**: Returns `issue_marked: True` but does not actually update tags or create an issue record | CERTAIN | MEDIUM | **HIGH** | `server.py:473-475` -- "For now, we just verify it exists and return success" |
| F1 | **Capture path divergence**: capture_client.py and chronicle/store.py implement raw_activity_events INSERT independently with different connection patterns and different dedup behavior | HIGH | MEDIUM | **HIGH** | `capture_client.py:343-377` vs `store.py:63-121` -- Two codepaths, one with INSERT OR IGNORE, one without |
| F2 | **Non-deterministic entry IDs in promotion**: work_log_entries get uuid4() IDs, making replay produce different IDs for the same logical entry | CERTAIN | LOW | **MEDIUM** | `store.py:171` -- `entry_id = str(uuid.uuid4())` |
| F4 | **Reflection source_entry_ids lost on retrieval**: `_check_existing_reflection` returns empty source_entry_ids | CERTAIN | MEDIUM | **MEDIUM** | `reflection.py:186-187` -- "Not stored separately, would need to reconstruct" |
| F5 | **Global rollup staleness**: No mechanism to detect when a project ledger has been modified since last rollup build | HIGH | MEDIUM | **MEDIUM** | `global_rollup.py` has no checksum or last_synced_ts comparison |
| **N4** | **store.py uses uuid4() for raw event IDs when no ID provided**: `insert_raw_event()` generates random IDs, breaking idempotency if capture_client isn't the caller | HIGH | MEDIUM | **MEDIUM** | `store.py:94` -- `final_event_id = event_id or str(uuid.uuid4())` |
| F8 | **Trajectory stream format leaks implementation**: Stream stored as "Active in {category}" display string, not semantic identifier | CERTAIN | LOW | **MEDIUM** | `trajectory/manager.py:126,192-193` -- Mixing presentation and data |
| F10 | **Capture redactor loaded via importlib from filesystem**: Dynamic import of redactor module from hardcoded relative path | HIGH | LOW | **MEDIUM** | `capture_client.py:158-182` -- Fragile cross-layer coupling |
| F12 | **more_count calculation is approximate**: count_work_log uses different filters than search_work_log (missing tags_any and time_range) | HIGH | LOW | **MEDIUM** | `store.py:323-349` vs `store.py:216-321` |

### Previously reported as F11 -- REFUTED

| ID | Claim | Status | Evidence |
|----|-------|--------|----------|
| ~~F11~~ | "No WAL mode in capture client connection" | **REFUTED** | `capture_client.py:346` explicitly sets `PRAGMA journal_mode = WAL`. Both paths set WAL. |

---

## 4. Determinism Leak List

### Confirmed Determinism Leaks

| # | Location | Leak | Severity |
|---|----------|------|----------|
| D1 | `store.py:171` | `uuid.uuid4()` for work_log_entry IDs -- replay produces different IDs | LOW (IDs are internal, not used for dedup) |
| **D2** | **`store.py:172`** | **`datetime.now(timezone.utc)` for ts_utc -- promotion time is wall clock, not event time** | **CRITICAL** -- The curated entry timestamp is when it was promoted, not when the event occurred. This silently changes chronological ordering. |
| D3 | `reflection.py:46` | `datetime.now(timezone.utc)` for default window_end -- reflections generated at different times produce different windows | LOW (by design) |
| D4 | `capture_client.py:316` | `datetime.now(timezone.utc)` as fallback ts_utc -- if event lacks timestamp, capture time is used | MEDIUM -- acceptable fallback but breaks replay determinism |
| D5 | `trajectory/manager.py:50,77` | `datetime.now()` for trajectory updates -- not derived from event timestamps | LOW (trajectory is ephemeral) |
| D6 | `server.py:209` | `more_count` uses count_work_log with incomplete filters -- may return different count than actual | LOW (cosmetic) |
| **D7** | **`capture_client.py:325`** | **project_id (absolute path) injected into payload AFTER redaction, BEFORE fingerprint** | MEDIUM -- Same event on different machines (different abs paths) produces different event_ids. Not portable. |

### Most Critical: D2

The promotion engine stores `datetime.now()` as the work log entry's `ts_utc` instead of the original event timestamp. This means:
- If there's EventBus lag, the curated entry appears to have happened later than it did.
- Replay of events produces different chronological ordering.
- The "Where was I?" recap answers with promotion-time, not activity-time.

**Evidence:** `store.py:172` -- `now_utc = datetime.now(timezone.utc).isoformat()` is used as both `ts_utc` and `created_at_utc`.

The original event timestamp from the EventBus envelope (`event.ts`) is available but never propagated to the work_log_entry.

---

## 5. Trust Boundary Violations

### T0: CRITICAL -- Two Separate Truth Stores (NEW)

**What's broken:** The MCP server (`server.py:82`) creates databases at `~/.dope-memory/{workspace_id}/chronicle.db`. The capture client (`capture_client.py:189`) writes to `repo_root/.dopemux/chronicle.sqlite`. These are **different files in different locations with different names**.

**Consequence:** ADR-213 asserts "All capture modes write to the same canonical per-project ledger." This is true for the capture client, but the MCP server bypasses the capture client entirely. Any call to `memory_store`, `memory_link_resolution`, or other MCP write tools goes to a separate database that:
- Is never read by the global rollup (which reads `repo_root/.dopemux/chronicle.sqlite`)
- Is never seen by the capture client
- Has no connection to the per-project chronicle

**Who is affected:** Any MCP consumer that calls `memory_store` believes they're writing to the canonical ledger. They're not. Their data is invisible to global rollup, to replay, and to any tool reading from the capture client's ledger.

**Severity:** This is the single most critical finding. It means there are **two separate databases** that both claim to be "the memory" for a workspace. The spec says one source of truth; the implementation has two.

### T1: CRITICAL -- No Provenance from Curated to Raw (F3)

**What's broken:** A work_log_entry has no `source_event_id` field linking it to the raw_activity_event that generated it.

**Consequence:** You cannot answer "why does this memory exist?" without searching raw events by approximate timestamp. Three months from now, those raw events will have been purged (7-day TTL). The memory becomes unexplainable.

**Who is affected:** Any human or agent trying to debug memory contents. Any future audit tool. Any "explain this decision" workflow.

### T2: CRITICAL -- Convergent Event Identity is Conditional (NEW)

**What's broken:** The event_id fingerprint at `capture_client.py:253-262` includes `source`. The `source` field defaults to mode-specific values when not explicitly provided (`capture_client.py:305`):
- plugin -> "claude_hook"
- mcp -> "mcp"
- cli -> "cli"

**Consequence:** ADR-213 claims "Same event from different modes produces identical event_id." This is only true when the event explicitly includes `source`. If source is auto-derived from mode (the common case for automated capture), convergence breaks silently. The integration test passes only because it explicitly sets `"source": "test"`.

**Who is affected:** Any automated capture path that doesn't explicitly set source. In practice, this means most captures from hooks and bridges will NOT converge.

### T3: MEDIUM -- Injection is Explicit but Unprovenienced

**What's designed correctly:** The spec states "Injection is explicit only through tool/command calls" (02_derived_memory_pipeline.md:116). This is correct.

**What's missing:** When an MCP tool returns a memory item, it includes `id`, `summary`, `tags`, `links` -- but not:
- When the memory was captured (vs when it was promoted)
- What raw event caused it
- What capture adapter created it
- What redaction was applied

A consuming agent receives memory that appears authoritative but has no chain of custody.

### T4: MEDIUM -- Reflection Cards Claim Trajectory Without Evidence

Reflection cards generate a 1-sentence `trajectory_summary` like "Active in debugging" (`reflection.py:324-336`). This is derived from category frequency counts -- not from semantic analysis of what happened.

If a session has 3 debugging entries and 2 architecture entries, the trajectory says "Active in debugging" even if the architecture work was the actual focus. The trajectory is a lossy compression that becomes the "what happened" narrative.

### T5: MEDIUM -- Global Rollup Copies Summaries Without Freshness

The global rollup stores summaries (truncated to 500 chars) in `promoted_pointers`. If the source work_log_entry is later corrected or annotated, the rollup copy is stale. There is no `last_modified_utc` comparison or checksum-based invalidation.

---

## 6. Chronicle Integrity Audit

### Is the chronicle truly a ledger?

**Answer: Mostly yes, with gaps.**

The raw_activity_events table is append-only by design (INSERT OR IGNORE). Events have deterministic IDs (SHA-256 of fingerprint). The schema supports this well.

**Gap 1:** There is no UPDATE restriction on raw_activity_events. Nothing prevents a buggy future consumer from modifying payloads in place. The spec says "append-only" but the schema doesn't enforce it (no trigger, no view-based isolation).

**Gap 2:** The `store.py:insert_raw_event()` method does not use INSERT OR IGNORE. It uses plain INSERT, which means the "two write path" problem (F1) also has a "two dedup behavior" problem. Code using `store.py` directly doesn't get idempotent writes.

### Dedupe correctness

**Finding:** The deterministic event_id in capture_client.py uses second-precision timestamp bucketing (`ts_bucket = ts_utc[:19]`). Two genuinely different events within the same second from the same source with the same payload will collide. This is probably fine for the use case (human developer events are unlikely to collide at 1-second granularity) but should be documented as a known limitation.

**Finding:** The event_id fingerprint includes `source`, which breaks convergence across modes unless source is explicitly provided (see T2).

### Are events "too raw" to be useful later?

**Answer: They're at the right granularity for Phase 1.** The event envelope (id, ts, type, source, payload_json) captures enough to reconstruct what happened. The redaction is appropriate -- fail-closed with typed replacements.

### Are events "too interpreted" to remain neutral?

**Answer: No, raw events are genuinely raw.** The interpretation happens only in the promotion layer. Raw events store the original event type and payload without transformation (beyond redaction). This is correct.

---

## 7. Promotion Logic Audit

### Can you explain why a memory exists 3 months later?

**Answer: No.** This is the most critical finding (after T0).

The promotion path is: raw event -> promotion engine -> work_log_entry. But:
1. The work_log_entry has no `source_event_id` (F3).
2. The raw event will be deleted after 7 days.
3. Three months later, the work_log_entry exists but its provenance is gone.

You can see *what* was decided, but not *what event triggered the memory*. For decisions, you can follow `linked_decisions_json` back to ConPort. For errors and tasks, there's no backlink at all.

### Is promotion deterministic across runs?

**Answer: Almost, but not quite.** Given the same raw event:
- The category, entry_type, outcome, and importance_score are deterministic.
- The tags are deterministic (explicit preserved, inferred sorted, capped at 12).
- The summary is deterministic (template-based with truncation).
- **But:** The entry_id is uuid4() (D1) and the ts_utc is wall-clock time (D2).

So two runs processing the same event will produce entries with different IDs and different timestamps. The content is deterministic; the metadata is not.

### Are there irreversible decisions?

**Yes -- promotion itself is irreversible.** Once an event is promoted to a work_log_entry, there is no "un-promote" mechanism. The work_log_entry table has no `deleted_at` or `status` field for soft deletion. If a bad promotion rule creates garbage entries, they persist forever.

---

## 8. Plugin vs MCP Asymmetry Analysis

### What Claude plugin can capture that MCP cannot

| Signal | Plugin | MCP | Gap |
|--------|--------|-----|-----|
| Shell command execution (pre/post) | Yes (hooks) | No (requires explicit call) | Plugin sees all commands; MCP only sees what's reported |
| File edit events | Yes (file watcher hook) | No | Plugin has OS-level visibility |
| Test run results (automatic) | Yes (post-command hook) | Manual | Plugin captures without user action |
| Session lifecycle (start/end) | Yes (session hooks) | Partial | Plugin knows exact session boundaries |
| Tool invocation context | Yes (pre-tool hook) | No | Plugin sees which tools are called |
| Latency/timing | Exact (hook fires synchronously) | Approximate (async call) | Plugin has true timestamps |

### What MCP captures that plugin cannot

| Signal | MCP | Plugin | Gap |
|--------|-----|--------|-----|
| Cross-editor events (Codex, Copilot) | Yes | No | Plugin is Claude-specific |
| CI/CD pipeline events | Yes (webhook bridge) | No | Plugin only runs in Claude Code |
| External service events | Yes (bridge adapters) | No | Plugin scope is local shell |
| Explicit memory_store with structured data | Yes (tool contract) | Indirect (hook extracts from output) | MCP has richer structured input |

### Where normalization must occur

1. **Timestamp normalization**: Plugin timestamps are exact (hook fires at event time). MCP timestamps are approximate (async call may lag). Normalization must use event-time, not capture-time. **Currently broken** (D2).

2. **Source normalization**: Plugin source is "claude_hook", MCP source varies. For convergent event_id, source must be normalized to a mode-independent value. **Currently broken** (T2).

3. **Payload normalization**: Plugin payloads come from hook output (may be raw stdout). MCP payloads come from structured tool arguments. Both go through the same redactor, but the input shapes differ. Normalization must happen BEFORE event_id generation.

4. **Event type normalization**: The promotion engine handles underscore-to-dot conversion (`normalize_event_type()`). This works but should be documented as a contract.

---

## 9. Derived Memory Semantics

### What does "memory" mean in Dopemux?

The spec is clear:
- **Memory** = temporal narrative ("What am I doing right now?")
- **Log** = raw activity events (short-lived, 7-day TTL)
- **Decision** = structured truth (owned by DopeQuery/ConPort)
- **Artifact** = derived summary (reflection cards, trajectory)

**Where the system risks confusion:**

1. **Recaps feel authoritative but are lossy.** The `memory_recap` tool returns 3 cards generated by rule: highest decision, highest blocker, suggested next. This is useful but hides other entries that might matter more. A human receiving "here's what happened" does not know what was omitted.

2. **Trajectory summaries assert causality they don't have.** "Active in debugging" implies the developer was debugging. They might have been doing architecture work that happened to trigger error entries. The trajectory is derived from entry_type frequency, not semantic understanding.

3. **Issue links imply causation with confidence scores.** The `issue_links` table stores `confidence` (default 0.7) and `evidence_window_min` (default 30). These numbers feel precise but are currently arbitrary (the MCP tool accepts any float). There's no validation that the confidence score was actually computed from evidence.

### At what scale does the memory stack stop helping?

| Project Size | Chronicle Entries | Risk | Notes |
|-------------|-------------------|------|-------|
| Small (1-3 months) | <500 | LOW | Everything fits in Top-3, recall is high |
| Medium (6-12 months) | 500-5000 | MEDIUM | Keyword search becomes noisy; importance_score flatlines at 5-7 |
| Large (1-3 years) | 5000-50000 | HIGH | Top-3 always returns recent; old critical decisions buried |
| Multi-year multi-project | 50000+ | CRITICAL | Global rollup LIKE search is O(n); no semantic ranking |

The inflection point is around **2000 curated entries per project**. At that scale:
- Keyword search returns 50+ hits for common terms ("auth", "deploy", "fix")
- Top-3 boundary means you see only the 3 most important, which are all importance 7
- The importance_score range (5-7 for Phase 1) provides almost no discrimination
- Reflection cards capture a 2-hour window, which is too small for multi-day investigations

---

## 10. Architectural Cliff Report

### A. What Must Be Frozen Now (Memory Stack Freeze List)

These components are load-bearing and should not change without a major version bump:

1. **raw_activity_events schema** -- The chronicle ledger is the foundation. Any schema change requires migration of every project's `.dopemux/chronicle.sqlite`.

2. **MCP tool contracts** -- Consumers depend on response shapes. Breaking changes here break all downstream tooling.

3. **Redaction patterns and denylist** -- Adding new patterns is safe. Removing or modifying existing ones could expose previously-redacted data on re-processing.

4. **Deterministic event_id generation algorithm** -- The SHA-256 fingerprint algorithm is the dedup key. Changing it breaks idempotency for all in-flight events.

5. **Capture mode resolution order** -- The priority chain (explicit -> env -> config -> context -> default) is a contract. Changing it silently changes which adapter writes.

6. **Canonical ledger location** -- `repo_root/.dopemux/chronicle.sqlite` is the single source of truth per ADR-213. This path must not change.

7. **Global rollup read-only guarantee** -- Global rollup opens project ledgers with `?mode=ro`. This is an architectural invariant.

### B. What Can Still Evolve Safely

1. **work_log_entries schema** -- Can ADD columns (source_event_id, original_ts_utc) without breaking existing readers.

2. **Promotion allowlist** -- Can add new event types to the promotable set without affecting existing entries.

3. **Reflection card generation rules** -- Internal logic, not exposed as a contract. Can change sorting, trajectory computation, etc.

4. **Global rollup search** -- Can upgrade from LIKE to FTS or semantic search without changing the schema contract.

5. **Trajectory state** -- Ephemeral by design. Can restructure without migration.

6. **Postgres mirror** -- No production consumer reads from it. Can be deferred or redesigned freely.

### C. What Is Over-Engineered

1. **Postgres mirror** -- For a single-developer ADHD tool, mirroring SQLite to Postgres adds operational complexity with no clear consumer. The MCP server reads from SQLite directly.

2. **AGE graph edges (Phase 3 spec)** -- The spec includes edge types with confidence and evidence windows. This is a knowledge graph inside a temporal log. Defer until Phase 2 proves value.

3. **Phase 4 ADHD Engine focus-state gating** -- The memory system doesn't proactively surface anything -- it responds to explicit tool calls. This phase has no triggering mechanism.

4. **Bridge adapter + predictive context restoration** -- `bridge_adapter.py` and `predictive_context_restoration.py` (TF-IDF + KNN) are complex ML systems alongside deterministic chronicle operations. Add cognitive overhead without clear Phase 1 integration.

### D. What Is Under-Engineered

1. **CRITICAL: MCP server database path** -- Must be fixed to use the canonical ledger path (`repo_root/.dopemux/chronicle.sqlite`), not a separate `~/.dope-memory/` path. This is the most urgent fix.

2. **CRITICAL: Source event provenance** -- No `source_event_id` on work_log_entries. Without this, the entire audit trail collapses after raw event TTL expires (7 days).

3. **CRITICAL: Convergent source normalization** -- The event_id fingerprint includes `source`, which varies by mode. Source must either be excluded from the fingerprint or normalized before inclusion.

4. **CRITICAL: Timestamp semantics** -- Promotion uses wall-clock time, not event time. This silently corrupts chronological ordering when there's any processing lag.

5. **HIGH: store.py dedup behavior** -- `insert_raw_event()` uses plain INSERT, not INSERT OR IGNORE. Must match capture_client's behavior.

6. **HIGH: Sorting code quality in reflection.py** -- Lines 196-222 contain dead code and confused sorting attempts. Must be correct and obviously correct.

7. **HIGH: memory_replay_session ordering** -- Advertises chronological replay but sorts by importance. A replay that doesn't respect time order is misleading.

8. **MEDIUM: memory_mark_issue stub** -- Returns success without doing anything. Must either be implemented or explicitly marked as unimplemented in the tool response.

---

## 11. Stop-Condition Findings

The packet specified four stop conditions. Here is the assessment:

### "Discovery of irreversible memory loss"

**FOUND: F3 (provenance gap).** Promotion is irreversible (no un-promote) AND loses the source_event_id. After 7 days, the raw event is purged. The transformation is irreversible without audit trail.

### "Silent injection paths"

**NOT FOUND.** The spec correctly states injection is explicit-only. The MCP server only serves data on request. There is no background process that silently injects memory into prompts.

However: the `_emit_to_event_stream` function in capture_client.py is "best-effort" (it silently fails if Redis is unavailable). This means the EventBus consumer might never see events that were written to SQLite. This is by design (SQLite is canonical) but could be confusing.

### "Dual sources of truth"

**FOUND: T0 (CRITICAL).** The MCP server writes to `~/.dope-memory/{workspace_id}/chronicle.db`. The capture client writes to `repo_root/.dopemux/chronicle.sqlite`. These are different files. The spec says one ledger; the implementation has two.

**FOUND: F1 (HIGH).** capture_client.py and store.py both write to raw_activity_events through independent codepaths with different dedup behavior.

### "Any place where memory cannot be explained to a human six months later"

**FOUND: F3 + T4.** A work_log_entry cannot be traced to its source event. A reflection card's trajectory_summary is a lossy 1-sentence compression that cannot be unpacked. Both become unexplainable after raw TTL expiry.

---

## 12. Next Strategic Packets (Recommendations)

Based on this audit, the next packets should be prioritized by risk:

### Packet C: Database Path Unification + Source Normalization (URGENT)

**Intent:** Fix T0 and T2 -- the two most critical architectural violations.

1. **MCP server must use the canonical ledger path** (`repo_root/.dopemux/chronicle.sqlite`), not `~/.dope-memory/`. The `_get_store()` method in server.py must resolve the ledger path the same way capture_client.py does.

2. **Source field must be excluded from event_id fingerprint** OR normalized to a mode-independent value. The current implementation breaks ADR-213's convergence guarantee for any automated capture.

3. **store.py:insert_raw_event must use INSERT OR IGNORE** to match capture_client behavior.

**Why now:** T0 means the memory stack has two separate truth stores. Every write through MCP tools goes to a database that nothing else reads. This invalidates the entire architecture.

### Packet D: Schema Freeze + Provenance Fix

**Intent:** Add `source_event_id` to work_log_entries. Fix D2 (use event timestamp, not wall clock). Freeze the chronicle schema with a version marker. Add schema migration tooling. Write the test that ensures raw_activity_events is never UPDATEd.

**Why now:** Every day without provenance is a day of unexplainable memories accumulating.

### Packet E: Replay Correctness + Dead Code Cleanup

**Intent:** Fix memory_replay_session to sort chronologically. Clean dead sorting code in reflection.py. Label memory_mark_issue as unimplemented. Unify the two SQLite write paths (capture_client.py and store.py) or document their intentional divergence.

**Why now:** These are trust-eroding bugs that a user will hit on first real use.

### Packet F: Scale Readiness Assessment (Optional)

**Intent:** Seed a test database with 5000 curated entries across 3 simulated months. Run MCP tools against it. Measure actual inflection points.

**Why now:** The system is designed for small scale. Knowing actual breaking points informs Phase 2 urgency.

---

## 13. "Do Not Build Yet" List

1. **LLM-based importance scoring** -- The flat 5-7 distribution is a known limitation but introducing LLM scoring before the chronicle is proven adds non-determinism risk.

2. **Embedding-based global semantic retrieval** -- The spec explicitly excludes this. Keep it that way until LIKE search proves insufficient with real data.

3. **Implicit prompt enrichment** -- The spec says "No default auto-injection." This is a load-bearing design decision. Do not introduce auto-injection at any layer.

4. **Cross-project causal edges** -- Cross-project causality requires trust guarantees that don't exist yet.

5. **Memory compaction / garbage collection** -- Compaction is lossy and irreversible. Build archival/export first.

---

*No filler. No optimism bias. The memory stack has a well-designed spec but the implementation has a critical database path divergence (T0) that violates its own ADR, plus provenance gaps that will erode developer trust within weeks of real adoption. Fix T0 first, then F3, then everything else.*
