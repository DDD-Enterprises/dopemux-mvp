# WORKFLOW AND GATES — dope-memory

## 1. Promotion Gating

### Event Promotion Pipeline

```
Raw Event (Redis / manual)
  │
  ▼
Redactor.redact_payload()
  │   Drops sensitive keys, applies regex patterns, enforces 64KB size cap
  │   Fail-closed: returns minimal safe payload on error
  │
  ▼
normalize_event_type()
  │   underscore → dot, lowercase, whitespace trim, empty → "unknown"
  │
  ▼
PromotionEngine.is_promotable()
  │   Check against PROMOTABLE_EVENT_TYPES frozenset
  │
  ├── NOT promotable → discard (return None)
  │
  ▼
PromotionEngine.promote()
  │   1. Validate provenance fields (event_id, event_type, source, ts_utc)
  │   2. Sentinel ban: reject "pre_migration", "unknown", ""
  │   3. Dispatch to handler: _promote_{normalized_type}()
  │   4. Inject provenance into PromotedEntry
  │
  ▼
ChronicleStore.insert_work_log_entry()
  │   1. Validate provenance (fail-closed)
  │   2. Sentinel ban (fail-closed)
  │   3. Supersession chain validation (if supersedes_entry_id)
  │   4. Deterministic entry_id: sha256(source_event_id|promotion_rule|source_event_ts_utc)
  │   5. INSERT OR IGNORE (idempotent)
  │
  ▼
Durable work_log_entry in SQLite canonical ledger
```

### Promotable Event Types (allowlist)

Source: `promotion/promotion.py:14` — `PROMOTABLE_EVENT_TYPES`

| Event Type | Default Importance | Handler |
|-----------|-------------------|---------|
| `decision.logged` | 7 | `_promote_decision_logged` |
| `task.completed` | 5 | `_promote_task_completed` |
| `task.failed` | 7 | `_promote_task_failed` |
| `task.blocked` | 7 | `_promote_task_blocked` |
| `error.encountered` | 6 | `_promote_error_encountered` |
| `workflow.phase_changed` | 5 | `_promote_workflow_phase_changed` |
| `manual.memory_store` | 6 | `_promote_manual_memory_store` |

### Provenance Requirements (Packet D §4.3)

All promoted entries MUST carry:

| Field | Type | Sentinel Allowed | Evidence |
|-------|------|-----------------|----------|
| `source_event_id` | TEXT NOT NULL | No (banned at runtime) | `chronicle/store.py:386` |
| `source_event_type` | TEXT NOT NULL | No | `chronicle/store.py:378` |
| `source_adapter` | TEXT NOT NULL | No (banned at runtime) | `chronicle/store.py:387` |
| `source_event_ts_utc` | TEXT NOT NULL | — | `chronicle/store.py:378` |
| `promotion_rule` | TEXT NOT NULL | No (banned at runtime) | `chronicle/store.py:388` |
| `promotion_ts_utc` | TEXT NOT NULL | — | `chronicle/store.py:424` |

Banned sentinel values: `{'pre_migration', 'unknown', ''}`

Pre-migration entries have sentinels (backfilled by `v1_1_0_add_provenance_fields.sql`) but runtime rejects them.

## 2. Supersession / Correction Gating

Source: `chronicle/store.py`

### Constants

| Constant | Value | Evidence |
|----------|-------|----------|
| `MAX_CHAIN_DEPTH` | 10 | `chronicle/store.py:37` |

### Correction Types (closed taxonomy)

Source: `chronicle/store.py:1178`

| Type | Semantics |
|------|-----------|
| `summary` | Corrects summary text |
| `tags` | Replaces tags |
| `category` | Changes category and/or entry_type |
| `outcome` | Changes outcome status |
| `retraction` | Tombstone — marks `[RETRACTED]`, outcome→`abandoned`, importance≤3 |

### Validation Rules

1. **Target must exist**: `get_entry_by_id()` check — `ValueError` if not found
2. **Target must be chain head**: `_is_entry_superseded()` check — `ValueError` with head redirect if superseded
3. **Chain depth limit**: `_get_chain_depth()` ≤ `MAX_CHAIN_DEPTH` (10) — `ValueError` if exceeded
4. **Fork prevention**: `UNIQUE INDEX idx_worklog_supersedes_unique_scoped ON (workspace_id, instance_id, supersedes_entry_id)` — `ValueError` on duplicate
5. **Cycle detection**: Visited-set traversal in `_get_chain_depth()` — `ValueError` on cycle

### Chain Annotations (read-time, never stored)

Source: `chronicle/store.py:184`

| Annotation | Type | Description |
|-----------|------|-------------|
| `is_head` | bool | True if entry is not superseded by any other |
| `superseded_by` | str\|null | ID of the superseding entry |
| `supersedes` | str\|null | ID of the entry this one supersedes |
| `chain_position` | {position: int, depth: int}\|null | 1-indexed position from origin |

## 3. Session Tracking / Idle Detection

Source: `eventbus_consumer.py`

### Configuration

| Parameter | Env Var | Default | Unit |
|-----------|---------|---------|------|
| Idle timeout | `DOPE_MEMORY_IDLE_MINUTES` | 20 | minutes |
| Pulse interval | `DOPE_MEMORY_PULSE_INTERVAL_SECONDS` | 2700 | seconds (45 min) |
| Pulse jitter | `DOPE_MEMORY_PULSE_JITTER_SECONDS` | 300 | seconds (5 min) |
| Min reflection window | `DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES` | 30 | minutes |
| Max reflection window | `DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS` | 2 | hours |

### High-Signal Events (reset idle timer AND trigger reflections)

Source: `eventbus_consumer.py:58`

```python
HIGH_SIGNAL_EVENTS = {
    "decision.logged", "task.completed", "task.failed",
    "task.blocked", "error.encountered", "manual.memory_store",
    "workflow.phase_changed",
}
```

### Heartbeat Events (reset idle timer only)

Source: `eventbus_consumer.py:70`

```python
HEARTBEAT_EVENTS = {"message.sent", "file.opened", "git.commit.created"}
```

### Reflection Triggers

1. **Session end**: Explicit session termination
2. **Idle end**: No activity for `DOPE_MEMORY_IDLE_MINUTES`
3. **Pulse boundary**: Every `DOPE_MEMORY_PULSE_INTERVAL_SECONDS`

## 4. Retention Gating

Source: `dope_memory_main.py:895`

| Parameter | Env Var | Default |
|-----------|---------|---------|
| Enabled | `ENABLE_RETENTION_JOB` | `true` |
| Interval | `RETENTION_INTERVAL_SEC` | 3600 (1 hour) |
| TTL for raw events | Stored per-row in `ttl_days` column | 7 days |

Retention applies only to `raw_activity_events` table. `work_log_entries` are durable and never auto-deleted.

## 5. Search Ordering / Ranking

### Base Ordering (ChronicleStore)

`importance_score DESC, ts_utc DESC, id ASC` — deterministic, stable

### Trajectory Boost (DopeMemoryMCPServer.memory_search)

Source: `dope_memory_main.py:191`

Boost applied after base query, before top-k truncation:

| Condition | Boost |
|-----------|-------|
| Entry category matches trajectory stream | +0.5 |
| Tag overlap with trajectory goal | +0.2 |
| File overlap with trajectory steps | +0.1 |
| No trajectory or no match | +0.0 |
| **Cap** | **0.5** |

Re-sort after boost: `(-boosted_score, -ts_utc_timestamp, id_asc)`

### Top-K Boundary

All search/recap tools: `top_k` default=3, min=1, max=10 (search/replay), max=20 (search Pydantic model allows up to 20 in request).

## 6. Schema Enums (CHECK constraints)

Source: `chronicle/schema.sql`

### `category`
`planning`, `implementation`, `review`, `debugging`, `research`, `deployment`, `architecture`, `documentation`

### `entry_type`
`decision`, `blocker`, `resolution`, `milestone`, `error`, `workflow_transition`, `manual_note`, `task_event`

### `workflow_phase`
`planning`, `implementation`, `review`, `audit`, `deployment`, `maintenance` (or NULL)

### `outcome`
`success`, `partial`, `blocked`, `abandoned`, `in_progress`, `failed`

### `importance_score`
INTEGER 1–10

### `correction_type` (application-level)
`summary`, `tags`, `category`, `outcome`, `retraction`

### `replay mode` (application-level)
`replay_current`, `replay_full`

### `scope` (memory_recap)
`session`, `today`, `last_2_hours`
