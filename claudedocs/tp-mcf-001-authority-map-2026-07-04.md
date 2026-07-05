# TP-MCF-001 — Memory Capture Repo-Truth Authority Map

**Packet**: TP-MCF-001 (Memory Context Fabric, phase 001) · **Status**: DONE (no runtime change) · **Date**: 2026-07-04
**Goal**: the current-runtime authority map for memory capture / promotion / ConPort writes / dope-context indexing / hooks / bridge, with exact paths and dead surfaces marked — and the exact TP-MCF-002/003 packet specs it produces.
**Method**: 3 read-only recon agents (Haiku) over the six domains; every row file:line-cited. No Fabric code; no runtime change.
**Spec**: `claudedocs/memory-context-fabric-design-2026-07-04.md` (v3).

---

## 1. Authority map (current runtime truth)

| Domain | Canonical writer / path | Status | Evidence |
|---|---|---|---|
| **A. Raw capture** | `capture_client.emit_capture_event()` → `raw_activity_events` (SQLite) | **REAL** | `capture_client.py:382-415`, INSERT `:535-556` |
| — redaction | `redactor.redact_payload()` | **REAL, strip-minimal-on-fail** (stores `{redaction_error, original_keys}`, leaks key names) | `capture_client.py:500-501`; `redactor.py:123-125` |
| — event_id | deterministic SHA256(type\|session\|ts_bucket\|payload) | **REAL** — but **falls back to `datetime.now()` on missing ts** | `capture_client.py:310-339`, `:493` |
| — Redis fan-out | `_emit_to_event_stream` → `activity.events.v1` | **REAL** | `capture_client.py:342-379`, `:351` |
| **B. Promotion** | `eventbus_consumer` (Redis `xreadgroup`) → `store.insert_promoted_entry` → `work_log_entries` | **REAL, event-triggered ONLY** (no ledger-polling path) | `eventbus_consumer.py:36,311-340,427-432` |
| — trigger gate | reads `activity.events.v1`, group `dope-memory-ingestor`; needs `REDIS_URL` + `ENABLE_EVENTBUS` | **REAL** | `eventbus_consumer.py:34,38` |
| — allowlist | `{decision.logged, task.completed, task.failed, task.blocked, error.encountered, workflow.phase_changed, manual.memory_store}` — **duplicated in two files, must stay synced** | **REAL** | `promotion.py:18-28` **and** `capture_client.py:39` |
| — trust field | **NONE** — `work_log_entries` has no `trust` column; provenance via `source_adapter`/`promotion_rule`/`source_event_id` | **UNWIRED** | `schema.sql:29-81` |
| **C. ConPort decision write** | `conport_log_decision` (MCP) / `POST /api/decisions` on active Docker ConPort | **REAL** | `enhanced_server.py:1760` (dispatch 1757-1774) |
| — relationship traversal | `GET /api/workspace-relationships` → `get_related_decisions()` | **REAL (HTTP)** | `enhanced_server.py:266,2125` |
| — graph MCP (`graph.neighbors`, genealogy) | — | **DEAD** — not in the 14-tool dispatch map; only in dead `memory_server.py` (`:875,909,936,962`, header declares dead `:1-5`) + quarantined `conport_kg` (`QUARANTINE.md`) | — |
| **D. dope-context** | `get_collection_names()` → `code_{hash}`, `docs_{hash}` only; Voyage (**external**) embeddings; FastMCP | **REAL (code/docs only)** | `workspace.py:164-182`; `indexing_pipeline.py:285-300,580`; `server.py:100` |
| — `memory_{hash}` / `index_memory` / `/index` route | — | **DEAD** — no such collection, tool, or REST route | grep 0 |
| — `_index_in_dopecontext` (dope-memory side) | POSTs `:3010/index` collection `worklog_index` | **PAINTED SOCKET** — no matching route/collection; POST silently fails (logged) | `eventbus_consumer.py:49,732,745,753-755` |
| **E. Native hooks** | `native_hooks.py` → stream `dopemux:events`; content-free pings | **REAL but NOT chronicle input** | `:83,124-137` |
| — SessionStart injection | injects MCP health + orchestrator + workflow context | **REAL** (extend here for recap) | `:335-351` |
| — PostToolUseFailure | `try_emit_promotable_capture_event(error)` | **REAL** (the memory-spine fix) | `:533-545` |
| — UserPromptSubmit | records truncated (400-char) prompt to workflow state + `dopemux:events` | **REAL but not raw-ledger capture** | `:365-380` |
| **F. dopecon-bridge** | emits `decision.logged`/`progress.updated` to `dopemux:events` **after** successful ConPort write, `source="conport"` | **REAL, mirror/receipt (non-authority)** | `routes.py:556-569,600-614` |

---

## 2. Dead-surface register (marked dead — do not target)

- `src/conport/memory_server.py` — declares itself dead (`:1-5`); the `mem.*`/`graph.*` tools live here, **not** in the active runtime.
- `services/conport_kg/` — quarantined (`QUARANTINE.md`: "Do not route runtime traffic").
- dope-context `/index` route + `worklog_index` collection — do not exist.
- `_index_in_dopecontext` (dope-memory) — a painted socket posting to the above.
- Ledger-polling promotion — does not exist; promotion is Redis-stream-triggered only.

## 3. Gap register (wires terminating in painted sockets)

1. **Hook → chronicle stream gap** — hooks/bridge publish to `dopemux:events`; the consumer reads `activity.events.v1`; nothing bridges them, and hook payloads are content-free. → hook-event capture does **not** feed the chronicle today.
2. **Promotion is stream-only** — an event that never reaches `activity.events.v1` is never promoted; there is no ledger-scan safety net.
3. **No `trust` column** — candidate-decision trust must live in `details_json`, not a schema field.
4. **`PROMOTABLE_EVENT_TYPES` duplicated** (`capture_client.py:39` + `promotion.py:18`) — any new type must be added to **both** (raw-side rejects unknown; promote-side ignores unknown).
5. **dope-context semantic memory absent** — no `memory_{hash}`/`index_memory`; embeddings are external (Voyage) → the privacy gate on TP-MCF-005 is real.
6. **ConPort graph MCP absent** — only HTTP relationship traversal exists; `graph.neighbors` is dead code.

---

## 4. Produced packets

### TP-MCF-002 — Transcript ingest → raw ledger only (CONDITIONAL-GO, now specified)

**Scope**: a transcript-file watcher/ingestor that parses harness session JSONL into turn events and writes **only** to `raw_activity_events` via `capture_client.emit_capture_event()` — **direct call, structured content** (not the `dopemux:events` ping path, not a naive stream-bridge).

**Hard invariants (all test-gated):**
- **Wiring**: call `emit_capture_event()` directly with a structured envelope (`type`, redacted `payload`, `session_id`, `workspace_id`, `source="transcript"`). Do **not** route through `dopemux:events`.
- **Stable timestamp**: use the transcript turn's own timestamp; **fail/quarantine any turn lacking a source timestamp** — never let `emit_capture_event` fall back to `datetime.now()` (`capture_client.py:493`). This is what makes re-ingest idempotent.
- **Redaction → hold/quarantine**: on redaction failure for a transcript turn, write only redacted metadata + a withheld payload reference to a **named local safety artifact** — decide `.dopemux/quarantine/` path vs a dope-memory non-queryable table — **not** the queryable ledger. Quarantine is not memory truth: never searched/promoted/mirrored/projected. Writer = this ingest adapter.
- **No side effects**: **no ConPort writes, no dope-context writes** in this slice.
- **Fail-open for the session**: capture failure never breaks the user's turn.
- **Idempotent**: deterministic content-hash `event_id` + `INSERT OR IGNORE` → re-reading a transcript file is safe.

**Spike (do first)**: verify the JSONL schema + on-disk path per harness (Claude Code vs Codex).
**Reconcile with**: the in-flight memory-spine roadmap work (do not fork the capture spine).
**Proof gates**: git status/diff, redaction test (no secret reaches ledger; failure → quarantine), replay test (re-ingest idempotent + rejects missing source ts), no-ConPort/no-dope-context-write test, embedded audit.

### TP-MCF-003 — Deterministic promotion + candidate-decision schema (NO-GO until schema defined → this specifies it, unblocking)

**Scope**: promote transcript-derived events for **deterministic** classes only (explicit user decision markers, task completions, errors/blockers, workflow transitions). **No LLM summarization; no auto ConPort writes.**

**Candidate-decision schema (the blocker):**
- New event type **`conversation.decision_candidate`** — added to `PROMOTABLE_EVENT_TYPES` in **both** `capture_client.py:39` **and** `promotion.py:18-28` (they must stay synced).
- Trust encoded in payload (no schema column exists): `details_json.trust = "conversation-derived"`, `promotion_rule = "conversation_candidate_v1"`.
- A candidate is **never** `decision.logged` (which the bridge emits only after a real ConPort write) and **never** auto-writes ConPort. Promotion to a canonical decision requires an explicit gate (operator confirm or deterministic high-confidence rule) — out of this packet's scope.

**Proof gates**: promotion test for each deterministic class; test that `conversation.decision_candidate` is accepted on both the raw and promote sides; test that no ConPort write occurs; authority-label assertion; embedded audit.

---

## 5. Governance footer

**Authority used**: 3 read-only recon passes (file:line cited above) over the active runtime; the v3 design spec; Memory Trinity ADRs. **Validation**: analysis only — **no code changed, live behavior NOT_RUN** (static code truth; recon did not exercise Docker/Redis). **Confidence**: high on the cited paths; the "painted socket" and "graph MCP absent" findings are grep-negative (absence-of-evidence, marked as such). **Next**: TP-MCF-002 (with the spike) then TP-MCF-003; both reconcile with the in-flight memory-spine work. **Rollback**: delete this file.
