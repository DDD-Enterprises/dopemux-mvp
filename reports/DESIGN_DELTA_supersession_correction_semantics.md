# DESIGN DELTA: Supersession & Correction Semantics

**Author:** Antigravity (Principal Systems Architect — Packet F)
**Date:** 2026-02-09
**Status:** BINDING ARCHITECTURAL LAW
**Scope:** Supersession chains, correction taxonomy, retraction, retrieval filtering, replay impact, trust preservation
**Constraint:** No code. Packet D semantics are law. Schema proposals are design-only.
**Authoritative Inputs:** `DESIGN_DELTA_provenance_time_semantics.md` (Packet D), `HANDOFF_packetC_to_packetD.md`, `DESIGN_DELTA_memory_stack_deep_audit.md`, `chronicle/schema.sql` (current), `chronicle/store.py` (current), Dope-Memory v1 specs

---

## 1. Executive Summary

Packet D established that promoted memories are **immutable** and that corrections happen via **supersession**: a new entry with `supersedes_entry_id` pointing to the old. This was correct as a policy statement but **semantically incomplete**. The following questions were left unanswered:

1. **What is a supersession chain?** Can entry C supersede B which supersedes A? Is the relationship linear or branching? What is the maximum depth?
2. **How do consumers filter superseded entries?** When `memory_search` returns results, does it include superseded entries? How does a consumer distinguish "current truth" from "historical record"?
3. **What correction types exist?** A tag fix is not the same as a factual retraction. Are they modeled the same way?
4. **Who may create superseding entries?** Only the promotion engine? Manual correction via MCP? Both?
5. **What happens to downstream dependents?** If entry A is superseded, what happens to reflection cards that reference A? Issue links? Global rollup pointers?
6. **How does supersession interact with deterministic entry_id?** If `entry_id = sha256(source_event_id | promotion_rule | source_event_ts_utc)`, how does a superseding entry avoid colliding with the original?

This document makes **binding decisions** on all six. Three stop conditions were encountered during design.

**Stop conditions encountered:**

- ⚠️ **Supersession chains can grow unbounded** — No depth limit was defined. A buggy correction loop could produce infinite chains. **Depth limit forced in §3.4.**
- ⚠️ **Ambiguity between `parent_entry_id` and `supersedes_entry_id`** — The schema has both fields. Their semantics overlap without clear separation. **Distinction forced in §4.**
- ⚠️ **Manual corrections create provenance paradox** — A human correcting a promoted memory needs a `source_event_id`, but there is no raw event to reference. The provenance contract (Packet D §4.5) says `source_event_id` MUST NOT be null. **Resolution forced in §6.**

---

## 2. What Packet D Established (Law — Not Renegotiable)

The following constraints from `DESIGN_DELTA_provenance_time_semantics.md` are treated as immutable inputs:

| #   | Constraint                                                                                                   | Reference   |
| --- | ------------------------------------------------------------------------------------------------------------ | ----------- |
| L1  | Promoted memories are immutable. No UPDATE, no DELETE.                                                       | §6.2, §10.4 |
| L2  | Supersession is represented only by `supersedes_entry_id` on the newer entry. No UPDATE on older entry.      | §6.2 rule   |
| L3  | Supersession, not correction — old entry remains, new entry supersedes. Summary should explain what changed. | §6.3        |
| L4  | Tags are mutable via supersession only.                                                                      | §6.4        |
| L5  | `source_event_id` MUST NOT be nullable. Fail-closed if unavailable.                                          | §4.5 rule 1 |
| L6  | `entry_id = sha256(source_event_id \| promotion_rule \| source_event_ts_utc)` — deterministic.               | §7.7        |
| L7  | `INSERT OR IGNORE` semantics on `work_log_entries`.                                                          | §7.7        |
| L8  | No memory may outlive its explainability.                                                                    | §10.5       |

These are the walls within which Packet F operates. Every decision below is compatible with — and extends — these constraints.

---

## 3. Supersession Chain Semantics

### 3.1 Definition

A **supersession chain** is a linked list of `work_log_entries` connected via `supersedes_entry_id`, where each entry supersedes at most one predecessor.

```
A ← B ← C
│         │
oldest    newest (head)
```

Entry A is the **origin**. Entry C is the **head** (current active version). Entries A and B are **superseded** (historical).

### 3.2 Decision: Linear Chains Only (No Branching)

**A superseded entry MAY be superseded at most once.** If entry A is superseded by B, no other entry C may also supersede A.

| Model            | Meaning                                                    | Decision       |
| ---------------- | ---------------------------------------------------------- | -------------- |
| **Linear chain** | A ← B ← C (each entry has exactly one supersessor or none) | ✅ **CHOSEN**   |
| **Branching**    | A ← B, A ← C (one entry superseded by multiple)            | ❌ **REJECTED** |
| **Diamond**      | A ← B, A ← C, B+C merge into D                             | ❌ **REJECTED** |

**Rationale:** Branching creates ambiguity about which entry is "current." If A is superseded by both B and C, a consumer must choose between two competing corrections — which requires conflict resolution logic that is out of scope for Phase 1. Linear chains have exactly one head, which is unambiguously the "current version."

**Enforcement:** The write path MUST check that `supersedes_entry_id` is not already referenced by another entry. If it is, the supersession MUST fail-closed. The check is:

```
SELECT COUNT(*) FROM work_log_entries 
WHERE supersedes_entry_id = :target_id
```

If count > 0, reject the insert. This is a uniqueness constraint on `supersedes_entry_id` (excluding NULL).

> [!IMPORTANT]
> **Schema consequence:** Add `UNIQUE` constraint on `supersedes_entry_id` (partial index, NULLs excluded). This enforces linearity at the database level. SQLite allows UNIQUE indexes where NULL is not treated as a value, so multiple NULL entries are permitted.

### 3.3 Chain Traversal

**Head resolution:** To find the current active version of any entry in a chain, traverse `supersedes_entry_id` forward (from older to newer) until reaching an entry that is not itself superseded.

```sql
-- Find head of chain containing entry :id
-- This is a recursive CTE (SQLite supports WITH RECURSIVE since 3.8.3)
WITH RECURSIVE chain(id) AS (
  SELECT id FROM work_log_entries WHERE supersedes_entry_id = :id
  UNION ALL
  SELECT w.id FROM work_log_entries w 
  JOIN chain c ON w.supersedes_entry_id = c.id
)
SELECT id FROM chain ORDER BY rowid DESC LIMIT 1;
```

If no rows returned, the entry IS the head (not superseded).

**Tail resolution:** To find the origin of a chain containing any entry, traverse `supersedes_entry_id` backward (from newer to older).

### 3.4 Decision: Maximum Chain Depth = 10

**A supersession chain MUST NOT exceed 10 entries (origin + 9 supersessions).**

| Limit    | Rationale                                                                                                      |
| -------- | -------------------------------------------------------------------------------------------------------------- |
| No limit | Risks unbounded chains from correction loops (bug-driven or adversarial)                                       |
| 3        | Too restrictive — legitimate iterative corrections (tag fix → summary fix → outcome correction) could hit this |
| 10       | Generous enough for legitimate use; tight enough to catch loops                                                |
| 100      | Effectively unlimited; loses protection value                                                                  |

**Enforcement:** Before inserting a superseding entry, traverse the chain backward from the target. If the chain already has 10 members, reject the supersession with a descriptive error.

**Edge case:** If a correction loop is detected (entry A supersedes B which supersedes A), this is caught by the chain depth traversal (the recursive CTE would loop). The implementation MUST use a cycle-detection guard (e.g., visited-set) in the traversal.

### 3.5 What "Superseded" Means

A superseded entry has the following properties:

| Property                                     | Value                                        |
| -------------------------------------------- | -------------------------------------------- |
| Still in the ledger                          | Yes — immutable, never deleted (L1)          |
| Visible in raw query results                 | Yes — still a row in `work_log_entries`      |
| Visible in filtered search results (default) | **No** — excluded by default (§5.1)          |
| Visible in replay                            | **Configurable** — two modes defined in §5.3 |
| Counts towards `more_count`                  | No — superseded entries excluded from count  |
| Referenced by reflection cards               | Entries become stale pointers (§7.1)         |

---

## 4. Disambiguating `parent_entry_id` vs `supersedes_entry_id`

### 4.1 The Confusion

The schema has two fields that create hierarchical relationships:

| Field                 | Current spec meaning                                                   | Current implementation meaning                                          |
| --------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `parent_entry_id`     | Original v1 spec (02_data_model_sqlite.md line 83) — undefined purpose | Exists in schema, accepted in `insert_work_log_entry`, no documentation |
| `supersedes_entry_id` | Packet D §6.2 — correction chain                                       | Added by v1.1.0 migration, documented                                   |

### 4.2 Decision: Separate Semantics

| Field                 | Meaning                                                                     | Relationship Type                    | Example                                                        |
| --------------------- | --------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------- |
| `parent_entry_id`     | **Containment hierarchy** — entry B is a sub-task or elaboration of entry A | Parent → child (one-to-many)         | "Fix auth bug" → "Fix token validation", "Fix session cleanup" |
| `supersedes_entry_id` | **Correction chain** — entry B replaces the meaning of entry A              | Predecessor → successor (one-to-one) | "Decided: use JWT" → "Corrected: decided to use OAuth"         |

**These are orthogonal relationships.** An entry MAY have both a `parent_entry_id` (it belongs to a task group) AND a `supersedes_entry_id` (it corrects a prior entry). They serve different purposes and must not be conflated.

**Rule:** `parent_entry_id` has NO filtering implications. A child entry is not a "supersession" of its parent. Consumers must not confuse hierarchical nesting with correction semantics.

---

## 5. Retrieval Behavior for Superseded Entries

### 5.1 Decision: Search Excludes Superseded by Default

**`memory_search` (and the underlying `search_work_log`) MUST exclude superseded entries by default.**

A superseded entry is one whose `id` appears as `supersedes_entry_id` in another entry. The easiest implementation is a `NOT IN` subquery or `LEFT JOIN`:

```sql
WHERE w.id NOT IN (
  SELECT supersedes_entry_id FROM work_log_entries 
  WHERE supersedes_entry_id IS NOT NULL
)
```

**Opt-in for history:** A new optional parameter `include_superseded: bool = false` on search tools allows consumers to explicitly request the full history. When `true`, superseded entries are included with a `superseded_by: <entry_id>` annotation in the response.

### 5.2 Decision: New Annotations on Search Results

When a search result includes an entry that participates in a supersession chain, the response MUST include:

| Annotation       | When present                  | Value                                                      |
| ---------------- | ----------------------------- | ---------------------------------------------------------- |
| `superseded_by`  | The entry has been superseded | `entry_id` of the superseding entry                        |
| `supersedes`     | The entry supersedes another  | `entry_id` of the superseded entry                         |
| `chain_position` | The entry is part of a chain  | `{position: N, depth: M}` where N is 1-indexed from origin |
| `is_head`        | Always present                | `true` if this is the current active version               |

These annotations are computed at read time, never stored. They are derived from the existing `supersedes_entry_id` column.

### 5.3 Replay Behavior

**Two replay modes:**

| Mode                       | Ordering                          | Includes superseded?         | Use case                                                                    |
| -------------------------- | --------------------------------- | ---------------------------- | --------------------------------------------------------------------------- |
| `replay_current` (default) | `source_event_ts_utc ASC, id ASC` | No — only chain heads        | "What really happened?" — reconstructs the corrected narrative              |
| `replay_full`              | `source_event_ts_utc ASC, id ASC` | Yes — all entries, annotated | "What was the sequence of understanding?" — shows how understanding evolved |

**`replay_current`** answers: "Give me the chronological narrative, incorporating all corrections."
**`replay_full`** answers: "Show me everything that was ever believed, including the mistakes."

Both modes use event-time ordering (Packet D §5.4). The difference is only inclusion/exclusion.

### 5.4 Recap Behavior

**`memory_recap` MUST reject superseded entries from reflection card inputs.** If a reflection card's `source_entry_ids_json` contains an entry that has since been superseded, the reflection card is **stale** and should be regenerated from the current heads.

This is the one place where supersession triggers a re-computation of a derived artifact. Reflection cards are regenerable by definition (Packet D §2.1). This is not a violation of immutability — the old reflection card persists; a new one is generated.

### 5.5 Global Rollup Behavior

**Global rollup MUST exclude superseded entries from `promoted_pointers`.**

On rollup build, the check is:

```sql
SELECT * FROM work_log_entries 
WHERE id NOT IN (
  SELECT supersedes_entry_id FROM work_log_entries 
  WHERE supersedes_entry_id IS NOT NULL
)
```

If a pointer exists for a superseded entry, it must be deleted on the next rollup rebuild. This is safe because pointers are regenerable (Packet D §2.1).

### 5.6 Issue Link Behavior

**Issue links referencing superseded entries are NOT automatically invalidated.**

Rationale: An issue link says "entry A described a blocker, entry B described its resolution." If entry A is superseded by A', perhaps the blocker description was refined. The link should still be valid — the resolution didn't change. If the resolution itself is superseded, the link still documents the historical resolution.

**Rule:** Issue links reference specific entries, not chain heads. Consumers querying issue links should resolve chain heads if they want current versions.

---

## 6. Manual Corrections and the Provenance Paradox

### 6.1 The Problem

Packet D §4.5 states: "`source_event_id` MUST NOT be nullable. A promoted memory without provenance is a trust violation."

But manual corrections — a human correcting a tag, fixing a summary, retracting a memory — have no raw event in `raw_activity_events`. There is no `source_event_id` to reference.

Three possible solutions:

| Solution                                                   | Mechanism                                                                       | Rejected because                                                                                                                 |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| A. Allow NULL `source_event_id` for manual corrections     | Nullable field                                                                  | Violates L5. Erodes trust model. Every NULL becomes "maybe manual, maybe bug."                                                   |
| B. Create a synthetic raw event for each manual correction | Write to `raw_activity_events` then promote                                     | Semantically dishonest — a human correction is not a "raw activity event." Pollutes the raw events table with synthetic entries. |
| **C. Use a self-referential `source_event_id` convention** | `source_event_id = "manual:<ulid>"` with `source_adapter = "manual_correction"` | ✅ **CHOSEN**                                                                                                                     |

### 6.2 Decision: Manual Correction Provenance Convention

Manual corrections use the following provenance values:

| Field                 | Value                                                       | Rationale                                                                                                                                                     |
| --------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source_event_id`     | `manual:<ULID>` (e.g., `manual:01JARW1ZVMQVXT4D8HZKN5D8WC`) | Unique, non-colliding with SHA-256 hex event_ids. The `manual:` prefix makes it machine-distinguishable. ULID provides temporal ordering.                     |
| `source_event_type`   | `manual.correction`                                         | New event type in the taxonomy. NOT promotable (raw-only event types list, not Phase 1 promoted). This event type exists solely for provenance documentation. |
| `source_adapter`      | `manual_correction`                                         | Distinguishes human corrections from automated promotions.                                                                                                    |
| `source_event_ts_utc` | Time of the correction action                               | When the human initiated the correction.                                                                                                                      |
| `promotion_rule`      | One of the correction types defined in §6.3                 | Explains *what kind* of correction was applied.                                                                                                               |

**Rule:** The `manual:` prefix MUST be checked by the sentinel ban. It is NOT a sentinel value — it is a legitimate provenance convention. The sentinel ban (Packet D §7.8) applies only to `pre_migration`, `unknown`, and empty string.

### 6.3 Correction Taxonomy

| Correction Type (`promotion_rule`) | When used                                            | What changes                          |
| ---------------------------------- | ---------------------------------------------------- | ------------------------------------- |
| `correction.summary`               | Human corrects factual content in the summary        | `summary` field differs from original |
| `correction.tags`                  | Human fixes tags                                     | `tags_json` differs from original     |
| `correction.category`              | Human reclassifies the entry                         | `category` and/or `entry_type` differ |
| `correction.outcome`               | Human updates outcome (e.g., in_progress → success)  | `outcome` field differs               |
| `correction.retraction`            | Human determines the entry should never have existed | See §6.4                              |

### 6.4 Retraction Semantics

A retraction is a special supersession where the superseding entry asserts: "the original entry was wrong and should not be considered part of the narrative."

**Retracted entries:**

| Property              | Value                                                          |
| --------------------- | -------------------------------------------------------------- |
| `category`            | Same as original (preserved for audit)                         |
| `entry_type`          | Same as original (preserved for audit)                         |
| `outcome`             | `abandoned`                                                    |
| `importance_score`    | `1` (minimum — deprioritized in any ranking)                   |
| `summary`             | `[RETRACTED] {original_summary} — Reason: {retraction_reason}` |
| `promotion_rule`      | `correction.retraction`                                        |
| `supersedes_entry_id` | Points to the retracted entry                                  |

**Retracted entries (the superseding entry with `correction.retraction` rule) are included in default search results.** They serve as tombstones — a consumer sees "[RETRACTED]" and understands the original was invalidated.

**The retracted entry (the original, now superseded) is excluded from default search results** per §5.1 (it has been superseded).

> [!WARNING]
> Retraction is the most trust-sensitive operation in the system. A retraction asserts that a prior observation was *wrong*, not just *outdated*. This is a strong claim. The `summary` MUST include the reason for retraction.

### 6.5 MCP Tool Contract for Manual Corrections

A new MCP tool `memory_correct` is needed (schema proposal only — no code):

```json
{
  "name": "memory_correct",
  "description": "Supersede an existing work log entry with a corrected version. The original entry is preserved immutably; a new entry replaces it.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "workspace_id": {"type": "string"},
      "instance_id": {"type": "string"},
      "entry_id": {"type": "string", "description": "ID of the entry to supersede"},
      "correction_type": {"type": "string", "enum": ["summary", "tags", "category", "outcome", "retraction"]},
      "corrected_summary": {"type": "string", "description": "New summary (required for summary corrections, retraction reason for retractions)"},
      "corrected_tags": {"type": "array", "items": {"type": "string"}, "description": "New tags (for tag corrections)"},
      "corrected_category": {"type": "string", "description": "New category (for category corrections)"},
      "corrected_entry_type": {"type": "string", "description": "New entry_type (for category corrections)"},
      "corrected_outcome": {"type": "string", "description": "New outcome (for outcome corrections)"}
    },
    "required": ["workspace_id", "instance_id", "entry_id", "correction_type"]
  }
}
```

**Behavior:** The tool:
1. Reads the existing entry by `entry_id`.
2. Validates the entry exists and is not already superseded (if it is, the consumer must supersede the head, not the tail).
3. Validates chain depth < 10 (§3.4).
4. Creates a new entry that copies all fields from the original except those being corrected.
5. Sets `supersedes_entry_id = entry_id` on the new entry.
6. Sets provenance fields per §6.2.
7. Returns the new entry's ID.

> [!IMPORTANT]
> **Rule:** `memory_correct` MUST NOT allow correcting a superseded entry directly. The consumer must target the chain head. This prevents forks in the chain (§3.2).

### 6.6 Entry ID for Manual Corrections

Packet D defines `entry_id = sha256(source_event_id | promotion_rule | source_event_ts_utc)`.

For manual corrections:
- `source_event_id = "manual:<ULID>"` — unique per correction
- `promotion_rule = "correction.{type}"` — varies by correction type
- `source_event_ts_utc` — time of correction

This combination is unique per correction action. The deterministic `entry_id` formula works without modification. The ULID ensures uniqueness; the formula ensures determinism for the same input.

---

## 7. Impact on Downstream Consumers

### 7.1 Reflection Cards

| Scenario                           | Before supersession                     | After supersession                                                                                                 |
| ---------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Reflection card references entry A | Card cites A in `source_entry_ids_json` | If A is superseded by A', the card is **stale**                                                                    |
| Stale detection                    | Not possible (no supersession existed)  | Compare `source_entry_ids_json` against superseded entry set                                                       |
| Regeneration                       | N/A                                     | When a stale card is detected, a new reflection card MAY be generated covering the same window using current heads |

**Rule:** Stale reflection cards are NOT automatically regenerated. They are flagged on retrieval. The response includes:

```json
{
  "stale_entries": ["entry_id_A"],
  "stale_reason": "superseded",
  "regeneration_recommended": true
}
```

Automatic regeneration would violate the principle that derived artifacts are on-demand, not background-computed.

### 7.2 Postgres Mirror

The Postgres mirror (`postgres_mirror_sync.py`) mirrors `work_log_entries` as-is. Superseded entries are present in the mirror. Filtering happens at query time, not at mirror time.

**Rule:** The mirror sync does not need modification. Filtering of superseded entries is a retrieval concern, handled by the query layer.

### 7.3 Search Result Count (`more_count`)

`count_work_log` MUST exclude superseded entries from its count. This ensures `more_count` accurately reflects the number of *current* entries matching the query, not the total including historical corrections.

### 7.4 Trajectory State

Trajectory state (`trajectory_state.last_steps_json`) may reference superseded entry IDs. When the trajectory manager reads `last_steps`, it SHOULD resolve each ID to its chain head. If the head differs from the stored ID, the trajectory is stale and should be updated on the next trajectory update cycle.

This is a best-effort update, not a hard constraint. Trajectory state is ephemeral by design (Packet D §2.1).

---

## 8. Deterministic Entry ID Under Supersession

### 8.1 The Non-Collision Argument

For automated promotions:
```
entry_id = sha256(source_event_id | promotion_rule | source_event_ts_utc)
```

For a superseding entry created by manual correction:
```
source_event_id = "manual:<ULID>"  # unique per correction
promotion_rule = "correction.{type}"  # different from any automated rule
```

These values are different from the original entry's provenance, so the `entry_id` is different. No collision.

For a re-promotion of the same raw event (e.g., promotion engine runs twice):
```
source_event_id = same
promotion_rule = same
source_event_ts_utc = same
→ entry_id = same → INSERT OR IGNORE dedup → idempotent
```

This is correct. The same raw event promoted by the same rule produces the same entry, which deduplicates.

### 8.2 Edge Case: Same Event, Different Rule

If a raw event `E` is promoted by rule `R1` (producing entry `P1`) and later by rule `R2` (producing entry `P2`), these are **different entries** with different `entry_id` values. This is correct — they represent different interpretations of the same observation.

This is NOT a supersession. `P2` does not supersede `P1`. They coexist as independent promoted memories with different promotion rules.

**Important:** If this is undesirable (i.e., one event should produce at most one promoted entry), the constraint must be enforced in the promotion engine, NOT in the entry ID formula or supersession model. This is out of scope for Packet F.

---

## 9. Schema Delta Proposal

### 9.1 Index Addition

```sql
-- Enforce linear supersession chains (no branching)
-- NULLs are excluded from UNIQUE in SQLite
CREATE UNIQUE INDEX IF NOT EXISTS idx_worklog_supersedes_unique
  ON work_log_entries(supersedes_entry_id) 
  WHERE supersedes_entry_id IS NOT NULL;
```

### 9.2 Index for Efficient Superseded-Entry Filtering

```sql
-- Efficient lookup: "is this entry superseded?"
CREATE INDEX IF NOT EXISTS idx_worklog_supersedes_target
  ON work_log_entries(supersedes_entry_id)
  WHERE supersedes_entry_id IS NOT NULL;
```

Note: The unique index in §9.1 already serves as this index. A single index satisfies both uniqueness enforcement and lookup performance.

### 9.3 No New Tables

No new tables required. The `supersedes_entry_id` column (already present from v1.1.0 migration) plus the unique index fully implements the supersession model.

### 9.4 No New Columns

No new columns required. The correction taxonomy is encoded in `promotion_rule` (existing column). The manual correction provenance convention uses `source_event_id`, `source_adapter`, and `source_event_type` (all existing columns).

### 9.5 Migration

```sql
-- v1.2.0: Enforce linear supersession chains
CREATE UNIQUE INDEX IF NOT EXISTS idx_worklog_supersedes_unique
  ON work_log_entries(supersedes_entry_id) 
  WHERE supersedes_entry_id IS NOT NULL;

INSERT OR IGNORE INTO schema_migrations (version, applied_at_utc)
VALUES ('v1.2.0', datetime('now'));
```

---

## 10. Stress Tests

### 10.1 Correction Loop

**Scenario:** Entry A is created. Corrected to B. Corrected to C. Corrected to D. ... Corrected to K (11th in chain).

**Expected behavior:** The 11th correction (K) is rejected at the write path with error: "Supersession chain depth limit exceeded (max 10)."

**Chain state:** A ← B ← C ← D ← E ← F ← G ← H ← I ← J. J is the head. 10 entries, no more allowed.

### 10.2 Fork Attempt

**Scenario:** Entry A is superseded by B. A third party attempts to supersede A with C.

**Expected behavior:** Insert of C fails due to UNIQUE constraint on `supersedes_entry_id`. Error: "Entry A is already superseded by B."

**Correct action:** The third party should supersede B (the head), not A.

### 10.3 Retraction of a Retraction

**Scenario:** Entry A is retracted (superseded by B with `correction.retraction`). Then B is itself superseded by C.

**Expected behavior:** This is allowed. C is a correction of the retraction. It can be:
- Another retraction (confirming the retraction with updated reason) — unusual but valid
- A reinstatement — C has normal category/outcome, effectively un-retracting A

**Trust preservation:** The full chain is: A (original) ← B (retracted) ← C (reinstated or re-retracted). All three entries persist. The audit trail shows the full decision history.

### 10.4 Supersession of Entry with Issue Links

**Scenario:** Entry A (blocker) is linked to entry B (resolution) via `issue_links`. Entry A is then superseded by A' (corrections to the blocker description).

**Expected behavior:** The issue link still references A by `issue_entry_id`. The link is NOT invalidated. When a consumer queries the link, they get A's ID. If they want the current version, they must resolve A's chain head (A').

**This is correct behavior.** The issue link documents a historical fact: "entry A was linked to resolution B at time T." The fact that A's description was later refined does not change the link.

### 10.5 Search with include_superseded=true

**Scenario:** Chain A ← B ← C exists. Consumer searches with `include_superseded=true`.

**Expected results:**

| Entry | `is_head` | `superseded_by` | `supersedes` | `chain_position`        |
| ----- | --------- | --------------- | ------------ | ----------------------- |
| A     | false     | B               | null         | {position: 1, depth: 3} |
| B     | false     | C               | A            | {position: 2, depth: 3} |
| C     | true      | null            | B            | {position: 3, depth: 3} |

All three entries appear. Annotations allow the consumer to reconstruct the chain.

### 10.6 Reflection Card Staleness

**Scenario:** Reflection card R was generated from entries [A, B, C]. Entry B is later superseded by B'. Consumer requests `memory_recap`.

**Expected behavior:** When R is retrieved, the system checks `source_entry_ids_json` against the superseded set. B is superseded → R is stale. Response includes `stale_entries: ["B"]` and `regeneration_recommended: true`.

The consumer (or MCP tool) may then trigger regeneration of R using the current heads [A, B', C].

### 10.7 Concurrent Correction Race

**Scenario:** Two agents simultaneously attempt to supersede entry A. Agent 1 creates B (superseding A). Agent 2 creates C (also superseding A).

**Expected behavior:** Exactly one succeeds. The UNIQUE index on `supersedes_entry_id` ensures that the second INSERT is rejected with a constraint violation. The losing agent must retry by targeting the new head (B), not A.

### 10.8 Global Rollup Consistency

**Scenario:** Global rollup was built when A was the head. A is then superseded by B. Next rollup build runs.

**Expected behavior:** The rollup builder excludes A from `promoted_pointers` (it is now superseded). B is added as a new pointer. The rollup is eventually consistent — it reflects the correction on the next rebuild, not immediately.

---

## 11. Decisions Forced by This Document

| #   | Decision                                                                       | Alternatives Rejected                                                                     | Rationale                                                                            |
| --- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| F1  | Supersession chains are linear (no branching)                                  | Branching (ambiguous heads), Diamond merges (conflict resolution needed)                  | Unambiguous "current version" without conflict resolution                            |
| F2  | Maximum chain depth = 10                                                       | Unlimited (loop risk), 3 (too restrictive)                                                | Protects against loops while allowing legitimate iterative correction                |
| F3  | Search excludes superseded by default                                          | Include all with annotations (noisy), Exclude all permanently (loses history)             | Default is "current truth"; opt-in for history                                       |
| F4  | `parent_entry_id` ≠ `supersedes_entry_id`                                      | Merge into one field (conflates hierarchy and correction)                                 | Orthogonal concepts that serve different purposes                                    |
| F5  | Manual corrections use `manual:<ULID>` provenance convention                   | Allow NULL `source_event_id` (violates L5), Synthetic raw events (dishonest)              | Preserves NOT NULL contract while being semantically honest                          |
| F6  | Retractions use `correction.retraction` rule with `outcome=abandoned, score=1` | Soft delete flag (violates immutability), Status column (overlaps outcome)                | Works within existing schema; retracted entries appear as tombstones                 |
| F7  | `memory_correct` tool must target chain head, not superseded entries           | Allow targeting any entry (creates forks)                                                 | Enforces linear chain invariant                                                      |
| F8  | Issue links reference specific entries, not chain heads                        | Auto-update links on supersession (violates immutability of links)                        | Links document historical facts; consumers can resolve heads if needed               |
| F9  | Stale reflection cards are flagged, not auto-regenerated                       | Auto-regenerate (background computation), Ignore staleness (lose trust)                   | On-demand regeneration preserves the principle that derived artifacts are pull-based |
| F10 | UNIQUE index on `supersedes_entry_id` enforces linearity at DB level           | Application-level check only (race conditions), CHECK constraint (limited expressiveness) | Database-level enforcement is corruption-proof against application bugs              |

---

## 12. Non-Negotiables (Post-Packet F)

These invariants are established by this document and MUST NOT be violated by any future packet.

### 12.1 Chain Structure

1. **Supersession chains are linear.** No branching, no diamonds. Enforced by UNIQUE index on `supersedes_entry_id`.

2. **Maximum chain depth is 10.** Enforced at the write path before insert.

3. **Supersession targets must be chain heads.** Targeting a superseded entry is rejected. Consumers must resolve the head first.

### 12.2 Retrieval

4. **Default search excludes superseded entries.** Opt-in via `include_superseded` parameter.

5. **Default replay excludes superseded entries.** `replay_full` mode includes them with annotations.

6. **Supersession annotations are computed at read time, never stored.**

### 12.3 Corrections

7. **Manual corrections use `manual:<ULID>` provenance convention.** The `manual:` prefix is machine-distinguishable from SHA-256 event IDs.

8. **The correction taxonomy is closed.** Only the five types in §6.3 are permitted. Adding new types requires a new packet.

9. **Retractions produce tombstone entries that appear in default search.** The superseded original is excluded; the retraction annotation is visible.

### 12.4 Downstream

10. **Stale reflection cards are flagged, not auto-regenerated.** Regeneration is on-demand.

11. **Issue links are never invalidated by supersession.** They document historical relationships.

12. **Global rollup excludes superseded entries on rebuild.** Eventually consistent.

---

## Appendix A: Supersession State Machine

```
            ┌─────────────────────────────────────┐
            │         ENTRY LIFECYCLE              │
            └─────────────────────────────────────┘

          ┌──────────┐
          │ CREATED  │ ← Entry is written via INSERT OR IGNORE
          │ (Active) │   May be auto-promoted or manually created
          └────┬─────┘
               │
               │ Another entry sets supersedes_entry_id = this.id
               │ (Exactly one supersessor allowed)
               ▼
          ┌──────────────┐
          │  SUPERSEDED  │ ← Entry is no longer "current"
          │ (Historical) │   Still in ledger, excluded from default search/replay
          └──────────────┘

State transitions are ONE-WAY. A superseded entry can never become active again.
To "undo" a supersession, create a new entry that supersedes the supersessor.
```

---

## Appendix B: Interaction Matrix

| Consumer                                         | Sees superseded entries?     | Sees chain annotations? | Action on supersession               |
| ------------------------------------------------ | ---------------------------- | ----------------------- | ------------------------------------ |
| `memory_search` (default)                        | No                           | N/A (excluded)          | Only returns heads                   |
| `memory_search` (include_superseded)             | Yes                          | Yes                     | Returns all with annotations         |
| `memory_replay_session` (default=replay_current) | No                           | N/A                     | Chronological heads only             |
| `memory_replay_session` (replay_full)            | Yes                          | Yes                     | Full history with annotations        |
| `memory_recap`                                   | No                           | N/A                     | Uses heads for reflection generation |
| `memory_correct` (new tool)                      | N/A (write tool)             | N/A                     | Creates superseding entry            |
| Global rollup                                    | No (on rebuild)              | N/A                     | Excludes superseded pointers         |
| Issue links                                      | References specific IDs      | N/A                     | No auto-invalidation                 |
| Reflection cards                                 | May reference superseded IDs | Stale flag on retrieval | Flagged, not auto-regenerated        |
| Postgres mirror                                  | Yes (mirrors all)            | Not computed            | Raw mirror, no filtering             |
| Trajectory state                                 | May reference superseded IDs | N/A                     | Resolved on next update cycle        |

---

*This document is final. It defines the complete semantics of supersession and correction within the append-only chronicle. Implementation follows mechanically from these definitions. Any deviation must be justified as a new architectural decision with its own risk analysis.*
