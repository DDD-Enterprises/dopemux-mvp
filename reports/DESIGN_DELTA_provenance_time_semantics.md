# DESIGN DELTA: Provenance + Time Semantics Repair

**Author:** Claude Opus 4.6 (Principal Systems Architect — Packet D)
**Date:** 2026-02-09
**Status:** BINDING ARCHITECTURAL LAW
**Scope:** Event identity, provenance chains, time authority, promotion semantics, replay ordering
**Constraint:** No code. No topology changes. No capture path changes. Schema proposals are design-only.
**Authoritative Inputs:** `HANDOFF_packetC_to_packetD.md`, `DESIGN_DELTA_memory_stack_deep_audit.md`, Dope-Memory v1 specs, current implementation state (post Packet C)

---

## 1. Executive Summary

The Dope-Memory stack has a correctly designed capture topology (post Packet C) but **lacks meaning at the semantic layer**. Specifically:

1. **Event identity is ambiguous.** The `event_id` conflates capture-instance identity with real-world-occurrence identity by including adapter-specific fields (`source`) in the fingerprint, while simultaneously claiming cross-adapter convergence.

2. **Provenance is broken.** Promoted memories (`work_log_entries`) cannot be traced to their source raw events. After the 7-day TTL expires, every promoted memory becomes unexplainable. This is not a future risk — it is a present-tense defect that accumulates irreversible damage daily.

3. **Time semantics are confused.** Promotion writes `datetime.now()` as `ts_utc` instead of the original event time. The memory system answers "what happened at time T" with "what was promoted at time T" — a different question. Replay is therefore non-deterministic with respect to real-world chronology.

4. **Promotion is irreversible and opaque.** There is no mechanism to explain, supersede, or invalidate a promoted memory. There is no record of *which rule* promoted an event or *why*.

This document makes **binding decisions** on all four. Implementation may follow mechanically from these definitions.

**Stop conditions encountered:**

- ⚠️ **Two incompatible notions of "event"** — The spec claims event_id is "content-based (hash of event_type + payload + ts_utc), mode-independent" (`02_derived_memory_pipeline.md:46`), but the implementation includes `source` and `project_id` in the hash (`capture_client.py:253-262`). These are contradictory definitions. **Decision forced in §3.**
- ⚠️ **Memory that cannot be explained after TTL expiry** — Every `work_log_entry` created today will be unexplainable in 8 days due to missing `source_event_id`. **Contract defined in §4.**
- ⚠️ **Promotion that irreversibly destroys meaning** — Summary truncation and timestamp substitution are lossy transformations with no recovery path. **Constraints defined in §6.**

---

## 2. Frozen Truth Model

### 2.1 Ontological Categories

The memory system contains exactly four categories of data. These categories are **mutually exclusive** and **exhaustive**.

| Category | Table | Durability | Mutability | Authority |
|---|---|---|---|---|
| **Raw Event** | `raw_activity_events` | Ephemeral (TTL) | Append-only, immutable after write | Authoritative for "what was captured" |
| **Promoted Memory** | `work_log_entries` | Durable (indefinite) | Immutable after write (new: must never update) | Authoritative for "what the system decided happened" — NOT for "what actually happened" |
| **Derived Artifact** | `reflection_cards`, `trajectory_state` | Durable but regenerable | May be regenerated from promoted memories | Never authoritative; always derived |
| **Global Pointer** | `promoted_pointers` (global rollup) | Durable but regenerable | May be rebuilt from project ledgers | Never authoritative; index only |

### 2.2 Semantic Definitions

**Raw Event:** A timestamped, redacted record of something an adapter observed. It is a *capture instance* — a record of the act of observing. It may be duplicated (same real-world occurrence captured by multiple adapters), and its values are frozen at write time.

**Promoted Memory:** A durable interpretation of one or more raw events, created by applying deterministic promotion rules. A promoted memory is an *assertion*: "the system concluded that X happened, based on evidence Y, using rule Z." It is NOT a fact. It is a judgment. This distinction is load-bearing for trust.

**Derived Artifact:** A computation over a window of promoted memories. Derived artifacts summarize, but they are regenerable from their inputs and carry no independent authority.

**Global Pointer:** A bounded copy of promoted memory metadata for cross-project lookup. Read-only, reconstructible, never authoritative.

### 2.3 Invariants (Frozen)

1. A promoted memory may outlive its source raw events (by design — TTL expiry is intentional).
2. A promoted memory must NEVER outlive its *explainability* — meaning it must carry enough metadata to answer "why does this exist?" without the raw event being present.
3. No data in the memory system is *ground truth* about the real world. All data is *observation + interpretation* with explicit provenance.
4. The only objects that are truly immutable are raw events and promoted memories. Everything else may be regenerated.

---

## 3. Event Identity Decision

### 3.1 The Question

What does `event_id` represent?

Three possible definitions:

| Definition | Meaning | Consequence |
|---|---|---|
| **A. Capture instance** | "This specific write to this specific database from this specific adapter" | Two adapters capturing the same thing get different IDs. No dedup across adapters. |
| **B. Real-world occurrence** | "The actual thing that happened in the real world" | Requires normalizing away all adapter-specific metadata from the fingerprint. Hard to define precisely. |
| **C. Normalized semantic action** | "The content of the event, independent of how or where it was captured" | Content-addressed. Two adapters capturing the same content converge to one ID. |

### 3.2 Decision: C — Normalized Semantic Action

**`event_id` represents the semantic content of the event, independent of capture adapter, mode, or deployment location.**

This is the only definition compatible with ADR-213's convergence guarantee and INSERT OR IGNORE dedup semantics.

### 3.3 Consequences: What Must Change

**Fields that MUST be excluded from the event_id fingerprint:**

| Field | Why exclude |
|---|---|
| `source` | Varies by adapter mode (`claude_hook`, `mcp`, `cli`). Including it makes convergence conditional on explicit source setting. Currently included — **must be removed.** |
| `project_id` (absolute path) | Varies by machine. Same event on developer laptop vs CI server produces different IDs. Currently included (injected post-redaction at `capture_client.py:325`) — **must be removed.** |

**Fields that MUST remain in the event_id fingerprint:**

| Field | Why include |
|---|---|
| `event_type` | Core semantic identity. Different event types are different events. |
| `ts_utc` (second-bucketed) | Temporal identity. Same content at different times = different events. |
| `payload` (redacted, stable JSON) | Content identity. The substance of what happened. |
| `session_id` | Session scoping. Same content in different sessions = different events. |

**New fingerprint formula:**

Normalization: session_id_or_empty MUST be the empty string ("") when session_id is missing. Do not substitute sentinel text. This keeps event_id stable across adapters and environments.

```
fingerprint = event_type | session_id_or_empty | ts_bucket_19chars | stable_json(redacted_payload)
event_id = sha256(fingerprint)
```



### 3.4 Consequences of Rejecting Alternatives

**If we had chosen A (capture instance):** Cross-adapter dedup would not work. INSERT OR IGNORE across capture paths would never deduplicate. Two writes of the same real event produce two rows. The ledger grows unbounded with duplicates. ADR-213 convergence guarantee becomes meaningless.

**If we had chosen B (real-world occurrence):** We would need to define a "real world event" independently of the system's observations. This is philosophically impossible for a software tool — we can only observe capture instances. Any attempt at B degenerates into C (content-addressed identity) or introduces heuristic matching.

### 3.5 Known Limitation — Second-Precision Bucketing

The `ts_bucket = ts_utc[:19]` truncation means two genuinely different events within the same second, with the same event_type, session_id, and payload, will collide. This is acceptable for the use case (human developer events). It MUST be documented as a known semantic boundary.

### 3.6 Migration Risk

Changing the fingerprint formula **invalidates all existing event_ids**. This means:

- Future captures of previously-captured events will produce new IDs (no dedup against old rows).
- Raw events currently in the ledger will have IDs computed with the old formula.
- This is acceptable because raw events expire in 7 days. After one TTL cycle, all old-formula IDs are gone.
- During the transition window (≤7 days), some duplicate rows may exist. This is benign — INSERT OR IGNORE handles it for new-formula IDs, and old rows expire.

**Mitigation:** No migration script needed. Deploy new fingerprint formula. Wait 7 days. Old IDs age out naturally.

---

## 4. Provenance Contract

### 4.1 The Problem

Today, when a raw event is promoted to a `work_log_entry`, no link is stored. After the raw event expires (7 days), the promoted memory exists but cannot answer:

- *Which raw event caused me to exist?*
- *What did the original event actually say?*
- *Was this a direct capture or a derived interpretation?*

### 4.2 Decision: Mandatory Source Provenance

**Every promoted memory MUST carry sufficient metadata to explain its existence without the raw event being present.**

This means the provenance metadata must survive raw event expiry. It is NOT a pointer that gets dereferenced — it is a self-contained explanation.

### 4.3 Required Provenance Fields on `work_log_entries`

| Field | Type | Nullable | Purpose |
|---|---|---|---|
| `source_event_id` | TEXT | NOT NULL | The `event_id` of the raw event that caused this promotion. If the raw event has expired, this field still documents *which* event was the cause. |
| `source_event_type` | TEXT | NOT NULL | The original `event_type` of the raw event (before any normalization). Preserves the *kind* of observation that triggered promotion. |
| `source_adapter` | TEXT | NOT NULL | The adapter that originally captured the event (`claude_hook`, `mcp`, `cli`). Documents *how* the observation entered the system. |
| `source_event_ts_utc` | TEXT | NOT NULL | The original timestamp from the raw event. Documents *when* the real-world activity occurred, independent of when it was promoted. |
| `promotion_rule` | TEXT | NOT NULL | The name of the promotion rule that was applied (e.g., `decision_logged`, `task_failed`). Documents *why* the system decided to promote this event. |
| `promotion_ts_utc` | TEXT | NOT NULL | When the promotion was executed. Independent of event time. Documents *when* the system made the judgment. |

### 4.4 Existing Fields: Reinterpretation

| Field | Current meaning | New meaning (Packet D) |
|---|---|---|
| `ts_utc` | Wall-clock time at promotion (`datetime.now()`) | **Original event time** (`source_event_ts_utc`). This field MUST be set to the event's occurrence time, NOT the promotion time. See §5. |
| `created_at_utc` | Same as `ts_utc` (both set to `datetime.now()`) | **System-generated write time.** When the row was physically written. Not semantically meaningful for replay. |
| `updated_at_utc` | Same as `ts_utc` | **Must equal `created_at_utc`** for initial writes. Promoted memories are immutable — this field should never change. If the immutability constraint is enforced, this field becomes redundant. Retained for backward compatibility. |

Invariant: For all post-migration rows, work_log_entries.ts_utc MUST equal work_log_entries.source_event_ts_utc. This is enforced by the write path and tests.

### 4.5 Rules

1. **`source_event_id` MUST NOT be nullable.** A promoted memory without provenance is a trust violation. If event_id is unavailable at promotion time (it always should be, but defensively), promotion MUST fail — fail-closed.

2. **`source_event_id` is NOT a foreign key.** It does not reference `raw_activity_events(id)` because the raw event may be expired. It is a *documentary reference*, not a relational constraint.

3. **Multi-event promotion is deferred.** In Phase 1, each promoted memory corresponds to exactly one raw event. Phase 2 reflection cards may reference multiple `work_log_entries` (via `source_entry_ids`), but this is a derivation, not a promotion.

4. **`promotion_rule` uses the normalized handler name**, e.g., `decision_logged`, `task_failed`, `manual_memory_store`. This enables future analysis of which rules produce which kinds of memories.

### 4.6 The Explainability Guarantee

After this contract is implemented, the following must be answerable for any promoted memory, **at any time, regardless of raw event expiry**:

| Question | Answered by |
|---|---|
| Why does this memory exist? | `promotion_rule` — which rule created it |
| What real-world event caused it? | `source_event_id` + `source_event_type` — the event's identity and kind |
| How did the observation enter the system? | `source_adapter` — the capture path |
| When did the real-world event occur? | `source_event_ts_utc` (and `ts_utc`, which MUST match) |
| When did the system process it? | `promotion_ts_utc` — the judgment timestamp |

---

## 5. Time Semantics Contract

### 5.1 Timestamp Taxonomy

The memory system has exactly **four** semantically distinct timestamps. Each has a defined authority and use.

| Timestamp | Field | Meaning | Authority | Mutable? |
|---|---|---|---|---|
| **Event Time** | `ts_utc` (raw), `source_event_ts_utc` (promoted) | When the real-world activity occurred | **Primary authority for chronology** | Never |
| **Capture Time** | `created_at_utc` (raw) | When the capture client wrote the row | System-generated, informational only | Never |
| **Promotion Time** | `promotion_ts_utc` (promoted) | When the promotion engine processed the event | System-generated, informational only | Never |
| **Write Time** | `created_at_utc` (promoted) | When the promoted row was physically written | System-generated, informational only | Never |

### 5.2 Authority Rules

1. **Event time is authoritative for chronological ordering.** When answering "what happened first?", use event time. Never promotion time.

2. **Event time is authoritative for replay.** When replaying a session, entries MUST be ordered by event time, not by write time or promotion time.

3. **Promotion time may NEVER substitute for event time.** This is the single most critical timestamp rule. The current implementation (`store.py:172`) violates this by using `datetime.now()` as `ts_utc`. This MUST be corrected.

4. **Event time may be approximate.** If the original event did not include a timestamp, the capture client uses `datetime.now(timezone.utc)` as a fallback (`capture_client.py:316`). This is acceptable as a best-effort timestamp, but it means the event time is actually a capture time in that case. This ambiguity is inherent and cannot be eliminated — it should be documented, not hidden.

5. **Clock skew is tolerated but documented.** Events from different machines may have clock drift. The system DOES NOT attempt to correct for clock skew. Events are ordered by their reported `ts_utc`, which may be slightly inaccurate. This is a known limitation.

### 5.3 Handling Delayed Capture

When an event is captured significantly after it occurred (e.g., batch import, offline sync):

- **Event time** = when the event actually happened (from the event producer's clock).
- **Capture time** = when the capture client wrote it (from the capture machine's clock).
- The gap between these is informational. The system does not reject or flag large gaps.
- Replay uses event time. The large gap is invisible in replay, which is correct — replay reconstructs the real-world sequence, not the processing sequence.

### 5.4 Replay Ordering Contract

Replay MUST produce events in the following deterministic order:

Replay over promoted memories (work_log_entries):
```
ORDER BY source_event_ts_utc ASC, source_event_id ASC
```
Replay over raw events (raw_activity_events):
```
ORDER BY ts_utc ASC, event_id ASC
```
**Rationale:**
- Ascending event time = chronological order (what happened first appears first).
- `event_id` tiebreaker = deterministic ordering for events at the same second (SHA-256 hex strings sort deterministically).

Note: This differs from the *search* ordering (`importance_score DESC, ts_utc DESC, id ASC`) which is appropriate for "show me the most important things" queries. Replay is a different use case — it reconstructs narrative sequence, not importance hierarchy.

### 5.5 Fields That Must Never Be Mutated

| Table | Field | Reason |
|---|---|---|
| `raw_activity_events` | ALL fields | Append-only ledger. No UPDATE. No DELETE (except TTL cleanup). |
| `work_log_entries` | `ts_utc` | Event time is frozen at observation. |
| `work_log_entries` | `source_event_id` | Provenance is frozen at promotion. |
| `work_log_entries` | `source_event_ts_utc` | Original event time is frozen. |
| `work_log_entries` | `promotion_rule` | The rule that was applied is a historical fact. |
| `work_log_entries` | `created_at_utc` | Write time is a physical fact. |
| `work_log_entries` | `summary` | Content must not be silently revised. |

### 5.6 Updated `ts_utc` Semantics on `work_log_entries`

| Before (current) | After (Packet D) |
|---|---|
| `ts_utc = datetime.now(timezone.utc)` at promotion time | `ts_utc = event.ts_utc` from raw event |
| Represents "when was this promoted" | Represents "when did this actually happen" |
| Breaks chronological ordering if there's processing lag | Preserves real-world sequence regardless of lag |

---

## 6. Promotion Semantics

### 6.1 What Is Promotion?

**Promotion is interpretation, not fact elevation.**

A promoted memory is the system's *judgment* that a raw event represents something worth remembering durably. It is not a "higher-confidence" version of the raw event. The raw event is a factual capture; the promoted memory is a curated assertion derived from that capture.

This distinction matters because:
- Curated assertions can be wrong (bad promotion rule, misclassified event).
- Curated assertions can be incomplete (promotion truncates summaries to 500 chars).
- Curated assertions must be attributable (who/what decided this was worth keeping?).

### 6.2 Promotion Semantic Contract

1. **Promotion is irreversible in the ledger.** Once a `work_log_entry` is written, it is never deleted or modified. This is consistent with the append-only chronicle model.

2. **Promotion is reversible in meaning.** A promoted memory may be *superseded* by a later promoted memory. This is modeled as a new entry with supersedes_entry_id pointing to the entry being superseded. The original remains in the ledger as a historical record; the superseding entry represents the updated understanding.

Rule: Supersession is represented only by supersedes_entry_id on the newer entry. No UPDATE is allowed on the older entry.

3. **Supersession, not correction.** If a promotion is later determined to be incorrect, the system creates a new entry that supersedes it. The old entry is not modified. This preserves the audit trail. The superseding entry's `summary` should explain what changed.

4. **Tags are mutable via supersession only.** Tags on a promoted memory cannot be changed in place. If tags need correction, supersede the entry.

### 6.3 Information Lost at Promotion Time (Inventory)

| Lost information | Severity | Mitigation |
|---|---|---|
| Full event payload (only summary extracted) | HIGH | Store `source_event_id` so payload can be recovered while raw event exists. After TTL, loss is accepted — the promoted summary is the durable representation. |
| Payload fields not mapped to promoted schema | MEDIUM | `details_json` captures a redacted subset. Accept that this is lossy. |
| Raw event `payload_json` byte-for-byte content | LOW | `source_event_id` enables lookup during TTL window. |
| Multiple events that could have been correlated | HIGH (future) | Phase 1 is single-event promotion only. Multi-event correlation is a Phase 2+ concern. |

### 6.4 Required Metadata at Promotion Time

See §4.3 for the full list. The critical additions are:

- `source_event_id` — which event (MUST NOT be null)
- `source_event_type` — what kind of event
- `source_adapter` — how it was captured
- `source_event_ts_utc` — when the real event happened
- `promotion_rule` — which rule was applied
- `promotion_ts_utc` — when the system made the judgment

### 6.5 Whether Promotions May Reference Multiple Events

**Phase 1: No.** Each promotion corresponds to exactly one raw event. The `source_event_id` field is singular.

**Phase 2+: Deferred.** Multi-event promotion (e.g., "these three error events represent one debugging session") requires a different model (a promotion batch or correlation group). This is explicitly out of scope for Packet D. When needed, it should be modeled as a separate construct — not by making `source_event_id` into a JSON array.

### 6.6 Whether Promotions May Be Invalidated

**No.** Promoted memories are never deleted or marked invalid. They may be *superseded* (see §6.2). The distinction:

- **Invalidation** = "this should not exist" → removes from the ledger → breaks append-only
- **Supersession** = "a better version now exists" → adds to the ledger → preserves history

An engineer might ask: "What if a clearly wrong memory was promoted by a bug?" The answer is: supersede it with a corrected entry. The original entry, annotated with the supersession link, becomes part of the historical record: "we initially recorded X, but later corrected it to Y."

---

## 7. Schema Delta Proposal

### 7.1 New Fields on `work_log_entries`

| Field | Type | Nullable | Default | Purpose |
|---|---|---|---|---|
| `source_event_id` | TEXT | NOT NULL | — | Raw event that caused this promotion |
| `source_event_type` | TEXT | NOT NULL | — | Original event type from raw event |
| `source_adapter` | TEXT | NOT NULL | — | Capture adapter (`claude_hook`, `mcp`, `cli`) |
| `source_event_ts_utc` | TEXT | NOT NULL | — | Original event timestamp (real-world time) |
| `promotion_rule` | TEXT | NOT NULL | — | Name of the promotion rule applied |
| `promotion_ts_utc` | TEXT | NOT NULL | — | When the promotion engine ran |

### 7.2 Reinterpretation of Existing Fields

| Field | Current behavior | Required behavior |
|---|---|---|
| `ts_utc` | `datetime.now(timezone.utc)` at promotion | Source event's `ts_utc` (event time, not promotion time) |
| `created_at_utc` | `datetime.now(timezone.utc)` at promotion | Keep as-is (physical write time) |
| `updated_at_utc` | Same as `created_at_utc` | Keep as-is; should never differ from `created_at_utc` for promoted entries |

### 7.3 Deprecated Fields

None. No existing fields are removed.

### 7.4 Fields That Must Never Be Nullable

| Field | Reason |
|---|---|
| `source_event_id` | A promoted memory without provenance is a trust violation |
| `source_event_type` | Without the event type, you cannot reconstruct why promotion occurred |
| `source_adapter` | Without the adapter, you cannot trace the capture path |
| `source_event_ts_utc` | Without the event time, chronological ordering is meaningless |
| `promotion_rule` | Without the rule, you cannot explain the promotion decision |
| `promotion_ts_utc` | Without the promotion time, you cannot distinguish event time from processing time |
| `summary` | Already NOT NULL. Must remain so. |

### 7.5 New Field on `PromotedEntry` Dataclass

The `PromotedEntry` dataclass in `promotion.py` must gain matching fields:

| Field | Type |
|---|---|
| `source_event_id` | `str` |
| `source_event_type` | `str` |
| `source_adapter` | `str` |
| `source_event_ts_utc` | `str` |
| `promotion_rule` | `str` |

These fields must be populated by the promotion engine before calling `store.insert_work_log_entry()`.

### 7.6 Impact on `insert_work_log_entry`

The `insert_work_log_entry` method in `store.py` must:

1. Accept the six new provenance fields as required parameters (not optional).
2. Use `source_event_ts_utc` as `ts_utc` instead of `datetime.now()`.
3. Use `datetime.now()` only for `created_at_utc` and `updated_at_utc`.
4. Store `promotion_ts_utc` as `datetime.now()` (capture the moment of promotion).

### 7.7 Deterministic Entry IDs (New)

Currently, `store.py:171` generates `entry_id = str(uuid.uuid4())`. This makes replay non-deterministic (same input produces different IDs on repeated runs).

**Decision:** Replace `uuid4()` with a deterministic hash:

```
entry_id = sha256(source_event_id + promotion_rule + source_event_ts_utc)
```

This ensures:
- Same event promoted by the same rule at the same time always produces the same entry ID.
- Replay reproduces identical IDs.
- INSERT OR IGNORE can be added to `insert_work_log_entry` for idempotent re-promotion.

### 7.8 Migration Notes (Conceptual)

1. **Schema change is additive.** New columns can be added with `ALTER TABLE ADD COLUMN ... DEFAULT`. No data migration needed for existing rows.

2. **Existing promoted entries are orphaned.** Pre-migration `work_log_entries` will have NULL provenance fields. These cannot be backfilled because the relationship between promoted entries and raw events was never recorded.

3. **Handling orphaned entries:** Backfill legacy rows with sentinel placeholders to preserve schema constraints without lying:
source_event_id = 'pre_migration'
source_event_type = 'unknown'
source_adapter = 'unknown'
promotion_rule = 'unknown'
source_event_ts_utc = created_at_utc (documented approximation)
promotion_ts_utc = created_at_utc
Strict rule: These sentinel values are permitted only for rows created before the migration. All runtime promotion code paths MUST reject sentinel values and fail closed if provenance cannot be determined.

4. **Schema version:** Increment `schema_migrations` to `v1.1.0`.

5. **No rollback.** This migration is forward-only. The new fields add information; removing them would destroy provenance.

---

## 8. Replay & Determinism Guarantees

### 8.1 What "Replay" Means

Replay is the process of reconstructing the temporal narrative of a project by reading promoted memories in chronological order. It answers: "What happened, in what order, during this time period?"

### 8.2 Determinism Requirements

| Property | Status (current) | Status (post Packet D) | Notes |
|---|---|---|---|
| Same event → same `event_id` | ❌ Conditional (source in fingerprint) | ✅ Deterministic (source removed from fingerprint) | §3 |
| Same event → same `entry_id` | ❌ Non-deterministic (uuid4) | ✅ Deterministic (sha256 of provenance) | §7.7 |
| Same event → same `ts_utc` | ❌ Non-deterministic (wall clock) | ✅ Deterministic (event time) | §5 |
| Same event → same promotion output | ✅ Already deterministic | ✅ Unchanged | Category, entry_type, outcome, importance, summary, tags are all rule-based |
| Replay order is deterministic | ❌ No (importance-sorted, not time-sorted) | ✅ `source_event_ts_utc ASC, id ASC` | §5.4 |

### 8.3 Replay After Partial Data Loss

When raw events expire (TTL), replay loses the ability to:

- View original payloads
- Verify the promotion decision against source data

Replay retains the ability to:

- View the promoted summary, category, entry_type, outcome
- Know *which* raw event caused the promotion (`source_event_id`)
- Know *when* the real event occurred (`source_event_ts_utc`)
- Know *which adapter* captured it (`source_adapter`)
- Know *which rule* promoted it (`promotion_rule`)
- Know *when* the promotion occurred (`promotion_ts_utc`)

This is **acceptable degradation** — the system honestly acknowledges that raw data is gone, while preserving enough metadata to reconstruct the narrative and explain every entry.

### 8.4 Replay vs Search: Different Contracts

| Operation | Ordering | Purpose |
|---|---|---|
| **Replay** | `source_event_ts_utc ASC, id ASC` | Reconstruct chronological narrative |
| **Search** | `importance_score DESC, ts_utc DESC, id ASC` | Find most important items first |
| **Recap** | Most recent reflection card | "Where was I?" summary |

These are three different access patterns that must NOT share an ordering. The current bug where `memory_replay_session` delegates to `memory_search` (and thus sorts by importance, not time) violates this contract.

---

## 9. Risk Register

### 9.1 Event Identity Change (§3)

| Dimension | Assessment |
|---|---|
| **What breaks if we do nothing** | ADR-213 convergence continues to be violated for all automated captures. Different adapters produce different event_ids for the same event. INSERT OR IGNORE dedup is ineffective across adapters. The ledger silently accumulates duplicates. |
| **What breaks if we apply the fix** | Existing event_ids become orphaned for 7 days (until TTL expiry). During transition, same events may get both old-formula and new-formula IDs. Benign — old rows expire, new rows use correct formula. |
| **Future features enabled** | True cross-adapter dedup. Reliable convergence testing. CI and local captures of same event converge. |
| **Future features blocked** | None. |

### 9.2 Provenance Fields (§4)

| Dimension | Assessment |
|---|---|
| **What breaks if we do nothing** | Every promoted memory created from today forward becomes unexplainable in 8 days. The "why does this exist?" question becomes permanently unanswerable. Human trust erodes. Any future audit or compliance review fails. |
| **What breaks if we apply the fix** | Schema migration required (additive, low risk). Pre-existing promoted entries will have placeholder provenance values (`pre_migration`). The promotion code path gains six additional required parameters — slightly more verbose but strictly more correct. |
| **Future features enabled** | Audit trails. "Explain this memory." Promotion rule analytics. Trust verification. Post-hoc analysis of promotion effectiveness. |
| **Future features blocked** | None directly. |

### 9.3 Timestamp Reinterpretation (§5)

| Dimension | Assessment |
|---|---|
| **What breaks if we do nothing** | All promoted entries are backdated to promotion time instead of event time. Any processing lag (EventBus delay, batch promotion) causes entries to appear at the wrong time. Replay produces incorrect chronological ordering. "Where was I?" queries may return answers from the wrong time. |
| **What breaks if we apply the fix** | Existing promoted entries with wall-clock `ts_utc` cannot be corrected (the original event time was never recorded). New entries will have correct `ts_utc`. Mixed old/new entries will be in the same table with different `ts_utc` semantics — this is a known transition cost. |
| **Future features enabled** | Accurate chronological replay. Correct "Where was I?" answers. Time-windowed reflection cards based on real activity time. |
| **Future features blocked** | None. |

### 9.4 Deterministic Entry IDs (§7.7)

| Dimension | Assessment |
|---|---|
| **What breaks if we do nothing** | Replay produces different entry_ids each time. If promotion is idempotently re-run (e.g., after system recovery), duplicate entries accumulate because INSERT has no convergent key. Reflection cards that reference `source_entry_ids` point to IDs that may not exist on re-promotion. |
| **What breaks if we apply the fix** | Existing entry_ids (uuid4) cannot be regenerated. Any downstream system caching entry_ids from before migration will have stale references. In practice, entry_ids are internal — no known external consumer depends on them. |
| **Future features enabled** | Idempotent re-promotion. INSERT OR IGNORE on `work_log_entries`. Safe crash recovery for the promotion engine. |
| **Future features blocked** | None. |

### 9.5 Promotion Immutability (§6)

| Dimension | Assessment |
|---|---|
| **What breaks if we do nothing** | Nothing today — no code currently UPDATEs promoted entries. But without an explicit constraint, a future developer may add UPDATE logic, violating the append-only guarantee. The `updated_at_utc` field's existence *implies* that updates are expected. |
| **What breaks if we apply the fix** | If a promotion rule is broken and produces garbage, the garbage persists forever. Supersession adds complexity (new entry + parent_entry_id). Operators must understand that "delete the bad row" is not an option. |
| **Future features enabled** | Guaranteed audit trails. Safe for compliance. Predictable replay. |
| **Future features blocked** | Bulk correction of historical entries (must be done one-by-one via supersession). Acceptable tradeoff. |

### 9.6 Reflection Card Source Entry IDs (Finding F4)

| Dimension | Assessment |
|---|---|
| **What breaks if we do nothing** | Reflection cards already compute `source_entry_ids` in memory but do not persist them (they are lost on `_check_existing_reflection` retrieval). Returned reflections cannot explain which entries they summarize. |
| **What breaks if we apply the fix** | Requires either a new table (many-to-many between reflection_cards and work_log_entries) or storing as JSON. JSON storage is simpler, aligned with existing `*_json` pattern. |
| **Future features enabled** | Explainable reflection cards. "Show me the entries this reflection covers." |
| **Future features blocked** | None. |

---

## 10. Non-Negotiables (Post-Packet D)

These invariants are established by this document and MUST NOT be violated by any future packet.

### 10.1 Identity

1. **`event_id` is content-addressed.** Computed from `event_type`, `session_id`, `ts_bucket`, `payload`. Never from `source`, `project_id`, or adapter metadata.

2. **`entry_id` is provenance-addressed.** Computed from `source_event_id`, `promotion_rule`, `source_event_ts_utc`. Never from `uuid4()`.

### 10.2 Provenance

3. **Every promoted memory carries mandatory provenance.** The six fields defined in §4.3 (`source_event_id`, `source_event_type`, `source_adapter`, `source_event_ts_utc`, `promotion_rule`, `promotion_ts_utc`) are NOT NULL and never dropped.

4. **Provenance survives raw event expiry.** The provenance metadata is self-contained — it does not require the raw event to exist.

5. **`source_event_id` is a documentary reference, not a foreign key.** No cascading deletes. No referential integrity constraint.

### 10.3 Time

6. **`ts_utc` on promoted entries represents event time, not promotion time.** This is the fundamental time-authority rule.

7. **No timestamp on any table may ever be mutated after initial write.** This includes `ts_utc`, `created_at_utc`, `source_event_ts_utc`, `promotion_ts_utc`.

8. **Replay uses event-time ascending order.** Search may use any applicable ordering.

### 10.4 Promotion

9. **Promoted memories are immutable.** No UPDATE, no DELETE (except via future explicit "supersede" entries referencing `parent_entry_id`).

10. **Promotion is interpretation, not fact elevation.** This semantic distinction must be preserved in documentation, API naming, and tool responses.

### 10.5 Trust

11. **No memory may outlive its explainability.** If provenance fields are missing, the memory must not be served to consumers without a "provenance unknown (pre-migration)" annotation.

12. **Derived artifacts (reflection cards, trajectory) are always regenerable.** They carry no independent authority and may be rebuilt from promoted memories.

---

## Appendix A: Human Trust & Explainability Test

> **Scenario:** A human returns to the system after 6 months, with raw events expired.

### Test 1: "Why does this memory exist?"

**Current system:** ❌ FAILS. No `source_event_id`, no `promotion_rule`. The human sees a summary but cannot determine what triggered it.

**Post Packet D:** ✅ PASSES. `source_event_id` identifies the trigger event; `promotion_rule` identifies the decision logic; `source_event_type` identifies the kind of observation.

### Test 2: "What actually happened vs what was inferred?"

**Current system:** ❌ FAILS. `summary` is a lossy template-based truncation. No distinction between "the system observed X" (raw event) and "the system concluded Y" (promoted memory). Both look the same in the work log.

**Post Packet D:** ✅ PASSES (partially). `source_event_type` and `source_adapter` distinguish observation from judgment. The `promotion_rule` makes the inference explicit. However, the original payload is still lost after TTL — the summary remains the only content. This is acceptable degradation, but the human knows it's a summary, not a verbatim record.

### Test 3: "Can I reconstruct the sequence and intent?"

**Current system:** ❌ FAILS. `ts_utc` is promotion time, not event time. Sequence is wrong if there was any processing lag. No way to distinguish "this happened at 10:00" from "this was processed at 10:00."

**Post Packet D:** ✅ PASSES. `ts_utc` = event time. `promotion_ts_utc` = processing time. Both are available. Replay uses event time. Sequence is correct.

### Test 4: "Can I trust a reflection card?"

**Current system:** ⚠️ PARTIAL. Reflection cards are regenerable but `source_entry_ids` are lost on retrieval (F4). The trajectory summary ("Active in debugging") is lossy and cannot be unpacked.

**Post Packet D:** ✅ PASSES (with annotation). If `source_entry_ids` are persisted (see Risk Register §9.6), the human can trace from reflection → promoted entries → provenance metadata. The trajectory summary remains lossy (by design — it's a 1-sentence compression), but its inputs are now traceable.

### Test 5: "Can I trust a memory from before the migration?"

**Post Packet D:** ⚠️ PARTIAL. Pre-migration entries will have `source_event_id = 'pre_migration'` and placeholder provenance. The human can see that these are historical entries without full provenance. They are *honest* about their limitations rather than appearing falsely authoritative.

### Remaining Trust Gaps (NOT addressed by Packet D)

1. **Summary truncation is still lossy.** After TTL, the 500-char summary is all that remains. No fix — this is by design.
2. **Trajectory is still a frequency-based heuristic.** "Active in debugging" may misrepresent the session's actual focus. Not fixable without semantic analysis (out of scope).
3. **Reflection cards recompute but don't warn about partially missing windows.** If a reflection covers a period where some entries have since been superseded, it may not reflect the current understanding. This is a Phase 2+ concern.

---

## Appendix B: Decisions Forced by This Document

| # | Decision | Alternatives rejected | Rationale |
|---|---|---|---|
| D1 | `event_id` = content-addressed (exclude source/project_id) | Capture-instance ID; real-world-occurrence ID | Convergence requires mode-independent identity. |
| D2 | `source_event_id` NOT NULL on all promotions | Nullable; optional; deferred | A promoted memory without provenance is worse than no memory. |
| D3 | `ts_utc` on promoted entries = event time, not promotion time | Keep wall-clock; add separate field only | Replay must use event time. Making the existing field correct avoids two timestamps competing for authority. |
| D4 | Entry IDs are deterministic (sha256), not uuid4 | Keep uuid4; use sortable ULID | Determinism enables idempotent re-promotion and replay reproducibility. |
| D5 | Promotions are immutable (supersede, never update/delete) | Allow soft delete; allow UPDATE for corrections | Append-only is the only model compatible with the ledger metaphor and trust guarantees. |
| D6 | `source` excluded from event_id fingerprint | Keep source in fingerprint with normalization | Normalization still requires knowing the "right" source. Exclusion is simpler and less error-prone. |
| D7 | `project_id` excluded from event_id fingerprint | Keep project_id with hash instead of path | Hash still varies across repo relocations. Exclusion is the only portable option. |

---

*This document is final. It defines meaning. It does not offer choices. Implementation follows mechanically. Any deviation from these semantics must be justified as a new architectural decision with its own risk analysis.*
