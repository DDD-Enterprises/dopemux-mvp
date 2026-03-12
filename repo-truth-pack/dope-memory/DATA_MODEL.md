# DATA MODEL — dope-memory

## 1. Entities

### 1.1 raw_activity_events (ephemeral, 7-day TTL)

Source: `chronicle/schema.sql:5`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | TEXT | NOT NULL | — | PK, UUID or provided |
| `workspace_id` | TEXT | NOT NULL | — | Workspace scope |
| `instance_id` | TEXT | NOT NULL | — | Instance scope |
| `session_id` | TEXT | nullable | — | Session scope |
| `ts_utc` | TEXT | NOT NULL | — | Event timestamp (ISO-8601) |
| `event_type` | TEXT | NOT NULL | — | Dotted event type |
| `source` | TEXT | NOT NULL | — | Source service/component |
| `payload_json` | TEXT | NOT NULL | — | Redacted event payload (JSON) |
| `redaction_level` | TEXT | NOT NULL | `'strict'` | Level of redaction applied |
| `ttl_days` | INTEGER | NOT NULL | `7` | Days before automatic cleanup |
| `created_at_utc` | TEXT | NOT NULL | — | Physical write time |

Indexes:
- `idx_raw_events_ws_ts` ON `(workspace_id, instance_id, ts_utc DESC)`
- `idx_raw_events_type_ts` ON `(event_type, ts_utc DESC)`

### 1.2 work_log_entries (durable)

Source: `chronicle/schema.sql:29`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | TEXT | NOT NULL | — | PK, deterministic SHA-256 |
| `workspace_id` | TEXT | NOT NULL | — | |
| `instance_id` | TEXT | NOT NULL | — | |
| `session_id` | TEXT | nullable | — | |
| `ts_utc` | TEXT | NOT NULL | — | Event time (not promotion time) |
| `duration_sec` | INTEGER | nullable | — | |
| `category` | TEXT | NOT NULL | — | CHECK: 8 values |
| `entry_type` | TEXT | NOT NULL | — | CHECK: 8 values |
| `workflow_phase` | TEXT | nullable | — | CHECK: 6 values or NULL |
| `summary` | TEXT | NOT NULL | — | Max 500 chars (app-enforced) |
| `details_json` | TEXT | nullable | — | Redacted JSON |
| `reasoning` | TEXT | nullable | — | Max 2000 chars (app-enforced) |
| `outcome` | TEXT | NOT NULL | `'in_progress'` | CHECK: 6 values |
| `importance_score` | INTEGER | NOT NULL | `5` | CHECK: 1-10 |
| `tags_json` | TEXT | NOT NULL | `'[]'` | JSON array, max 12 tags |
| `linked_decisions_json` | TEXT | nullable | — | JSON array of decision IDs |
| `linked_files_json` | TEXT | nullable | — | JSON array of file objects |
| `linked_commits_json` | TEXT | nullable | — | JSON array of commit SHAs |
| `linked_chat_range_json` | TEXT | nullable | — | JSON object |
| `parent_entry_id` | TEXT | nullable | — | Hierarchical parent |
| `source_event_id` | TEXT | NOT NULL | — | Provenance: originating event ID |
| `source_event_type` | TEXT | NOT NULL | — | Provenance: originating event type |
| `source_adapter` | TEXT | NOT NULL | — | Provenance: capture adapter name |
| `source_event_ts_utc` | TEXT | NOT NULL | — | Provenance: event timestamp |
| `promotion_rule` | TEXT | NOT NULL | — | Provenance: which rule promoted |
| `promotion_ts_utc` | TEXT | NOT NULL | — | Processing timestamp |
| `supersedes_entry_id` | TEXT | nullable | — | Supersession: ID of superseded entry |
| `created_at_utc` | TEXT | NOT NULL | — | Physical write time |
| `updated_at_utc` | TEXT | NOT NULL | — | = created_at_utc (immutable entries) |

Indexes:
- `idx_worklog_ws_ts` ON `(workspace_id, instance_id, ts_utc DESC)`
- `idx_worklog_cat_type` ON `(category, entry_type)`
- `idx_worklog_phase` ON `(workflow_phase)`
- `idx_worklog_importance` ON `(importance_score DESC, ts_utc DESC)`
- `idx_worklog_supersedes_unique_scoped` UNIQUE ON `(workspace_id, instance_id, supersedes_entry_id)` WHERE NOT NULL

### 1.3 issue_links

Source: `chronicle/schema.sql:101`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | TEXT | NOT NULL | — | PK, UUID |
| `workspace_id` | TEXT | NOT NULL | — | |
| `instance_id` | TEXT | NOT NULL | — | |
| `issue_entry_id` | TEXT | NOT NULL | — | FK → work_log_entries(id) |
| `resolution_entry_id` | TEXT | NOT NULL | — | FK → work_log_entries(id) |
| `confidence` | REAL | NOT NULL | `0.7` | 0.0-1.0 |
| `evidence_window_min` | INTEGER | NOT NULL | `30` | Minutes |
| `created_at_utc` | TEXT | NOT NULL | — | |

### 1.4 reflection_cards (Phase 2)

Source: `chronicle/schema.sql:125`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | TEXT | NOT NULL | — | PK, UUID |
| `workspace_id` | TEXT | NOT NULL | — | |
| `instance_id` | TEXT | NOT NULL | — | |
| `session_id` | TEXT | nullable | — | |
| `ts_utc` | TEXT | NOT NULL | — | Generation time |
| `window_start_utc` | TEXT | NOT NULL | — | Reflection window start |
| `window_end_utc` | TEXT | NOT NULL | — | Reflection window end |
| `trajectory` | TEXT | NOT NULL | — | 1-sentence trajectory summary |
| `top_decisions_json` | TEXT | NOT NULL | `'[]'` | Top 3 decisions |
| `top_blockers_json` | TEXT | NOT NULL | `'[]'` | Top 3 blockers/errors |
| `progress_json` | TEXT | NOT NULL | `'{}'` | Progress summary by category |
| `next_suggested_json` | TEXT | NOT NULL | `'[]'` | Suggested next steps |
| `source_entry_ids_json` | TEXT | NOT NULL | `'[]'` | Provenance: which entries used |
| `promotion_candidates_json` | TEXT | NOT NULL | `'[]'` | Candidates for ConPort promotion |
| `created_at_utc` | TEXT | NOT NULL | — | |

### 1.5 trajectory_state (Phase 2)

Source: `chronicle/schema.sql:153`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `workspace_id` | TEXT | NOT NULL | — | PK (composite) |
| `instance_id` | TEXT | NOT NULL | — | PK (composite) |
| `session_id` | TEXT | nullable | — | |
| `updated_at_utc` | TEXT | NOT NULL | — | |
| `current_stream` | TEXT | NOT NULL | `''` | e.g. "Active in debugging" |
| `current_goal_json` | TEXT | NOT NULL | `'{}'` | Current goal context |
| `last_steps_json` | TEXT | NOT NULL | `'[]'` | Last 3 high-signal steps |

### 1.6 schema_migrations

Source: `chronicle/schema.sql:168`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `version` | TEXT | NOT NULL | — | PK |
| `applied_at_utc` | TEXT | NOT NULL | — |

## 2. Relationships

```
raw_activity_events  ──(promoted by PromotionEngine)──▶  work_log_entries
work_log_entries     ──(supersedes_entry_id)───────────▶  work_log_entries (self-ref, linear chain)
work_log_entries     ◀──(issue_entry_id)───────────────── issue_links
work_log_entries     ◀──(resolution_entry_id)──────────── issue_links
work_log_entries     ──(source_entry_ids_json)──────────▶ reflection_cards (many-to-many via JSON)
trajectory_state     ──(workspace_id, instance_id)──────▶ (logical: most recent work_log_entries)
```

## 3. ID Generation

| Entity | Strategy | Evidence |
|--------|----------|----------|
| `raw_activity_events.id` | UUID v4 (or provided) | `chronicle/store.py:287` |
| `work_log_entries.id` | Deterministic SHA-256 of `{source_event_id}\|{promotion_rule}\|{source_event_ts_utc}` | `chronicle/store.py:419` |
| `issue_links.id` | UUID v4 | `chronicle/store.py:869` |
| `reflection_cards.id` | UUID v4 | `reflection/reflection.py:95` |
| ULID fallback | Timestamp+random hex when `ulid-py` not installed | `chronicle/store.py:31` |

## 4. Persistence Backend

| Backend | Technology | Purpose | Durability |
|---------|-----------|---------|------------|
| Primary | SQLite (WAL mode) | Canonical ledger | Durable |
| Mirror | PostgreSQL | Read replica / analytics | Durable (opt-in) |
| Transport | Redis Streams | Event ingestion | Ephemeral |

### Canonical Ledger Resolution

Source: `canonical_ledger.py:56`

Resolution order (first match wins):
1. `DOPEMUX_CAPTURE_LEDGER_PATH` env var (explicit override)
2. `workspace_id` as absolute path with `.git` or `.dopemux` marker
3. Walk upward from `cwd()` to find repo root → `{root}/.dopemux/chronicle.sqlite`
4. **Fail closed** — `CanonicalLedgerError`

### SQLite Configuration

| Setting | Env Var | Default | Evidence |
|---------|---------|---------|----------|
| Journal mode | `DOPEMUX_SQLITE_JOURNAL_MODE` | `WAL` | `chronicle/store.py:67` |
| Foreign keys | — | `ON` | `chronicle/store.py:66` |

## 5. Migration System

Source: `chronicle/sqlite_migrations.py`

- Filename pattern: `v{major}_{minor}_{patch}_*.sql`
- Applied in semantic version order
- Idempotent (checks `schema_migrations` table)
- Base schema always applied first via `schema.sql`

### Applied Migrations

| Version | File | Purpose |
|---------|------|---------|
| v1.0.0 | `schema.sql` (base) | Initial schema: 5 data tables + migrations |
| v1.1.0 | `v1_1_0_add_provenance_fields.sql` | Add provenance columns, backfill sentinels |
| v1.1.1 | `v1_1_1_add_supersession_unique_index.sql` | Global supersession unique index |
| v1.2.0 | `v1_2_0_enforce_linear_supersession.sql` | Duplicate of v1.1.1 (versioned separately) |
| v1.2.1 | `v1_2_1_scope_supersession_unique_index.sql` | Scope uniqueness to workspace+instance |

## 6. Environment Variables

| Variable | Default | Purpose | Used By |
|----------|---------|---------|---------|
| `PORT` | `3020` | HTTP server port | `dope_memory_main.py` |
| `DOPE_MEMORY_PORT` | `3020` | Alias for PORT | `dope_memory_main.py` |
| `DOPE_MEMORY_WORKSPACE_ID` | `default` | Default workspace | `dope_memory_main.py` |
| `DOPE_MEMORY_INSTANCE_ID` | `A` | Default instance | `dope_memory_main.py` |
| `DOPE_MEMORY_DATA_DIR` | `~/.dope-memory` | Data directory | `dope_memory_main.py` |
| `DOPEMUX_CAPTURE_LEDGER_PATH` | — | Explicit ledger path | `canonical_ledger.py` |
| `DOPEMUX_SQLITE_JOURNAL_MODE` | `WAL` | SQLite journal mode | `chronicle/store.py` |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection | `eventbus_consumer.py` |
| `ENABLE_EVENTBUS` | `false` | Enable Redis consumer | `dope_memory_main.py` |
| `ENABLE_MIRROR_SYNC` | `false` | Enable Postgres sync | `dope_memory_main.py` |
| `ENABLE_RETENTION_JOB` | `true` | Enable raw event cleanup | `dope_memory_main.py` |
| `RETENTION_INTERVAL_SEC` | `3600` | Cleanup interval | `dope_memory_main.py` |
| `POSTGRES_URL` | — | PostgreSQL connection | `dope_memory_main.py` |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | CORS origins | `dope_memory_main.py` |
| `LOG_LEVEL` | `INFO` | Logging level | `dope_memory_main.py` |
| `ENVIRONMENT` | `development` | Environment name | `dope_memory_main.py` |
| `SERVICE_NAME` | `dope-memory` | Service name for health | `dope_memory_main.py` |
| `DOPE_MEMORY_IDLE_MINUTES` | `20` | Session idle timeout | `eventbus_consumer.py` |
| `DOPE_MEMORY_PULSE_INTERVAL_SECONDS` | `2700` | Pulse interval | `eventbus_consumer.py` |
| `ENABLE_DOPECONTEXT_INDEX` | `false` | Cross-index to DopeContext | `eventbus_consumer.py` |
| `DOPECONTEXT_URL` | `http://localhost:3010` | DopeContext base URL | `eventbus_consumer.py` |
