# ConPort — Data Model

**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Source of Truth**: `docker/mcp-servers-source/conport/schema.sql` (291 lines)
**Migrations**: `migrations/001..004, 007`

---

## 1. Base Schema Tables (from `schema.sql`)

### 1.1 `workspace_contexts`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL, UNIQUE INDEX | — |
| `active_context` | TEXT | — | — |
| `last_activity` | TEXT | — | — |
| `session_time` | VARCHAR(50) | — | — |
| `focus_state` | VARCHAR(50) | — | — |
| `session_milestone` | TEXT | — | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `updated_at` | TIMESTAMPTZ | — | `NOW()` |

**Migration 003 adds**: `user_id VARCHAR(100) DEFAULT 'default'`
**Migration 007 adds**: `instance_id VARCHAR(255)` (via `_ensure_schema`, `enhanced_server.py` line 480)

**Indexes**: `idx_workspace_contexts_workspace_id` (UNIQUE), `idx_workspace_contexts_updated_at`
**Triggers**: `update_workspace_contexts_modtime` (auto-update `updated_at`)
**Source**: `schema.sql` lines 12-25

### 1.2 `decisions`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `summary` | TEXT | NOT NULL | — |
| `rationale` | TEXT | NOT NULL | — |
| `alternatives` | JSONB | — | `'[]'` |
| `tags` | TEXT[] | — | `'{}'` |
| `confidence_level` | VARCHAR(20) | — | `'medium'` |
| `decision_type` | VARCHAR(50) | — | `'implementation'` |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `updated_at` | TIMESTAMPTZ | — | `NOW()` |

**Migration 001 adds 14 columns**:
- `impact_score` DECIMAL(3,2) CHECK 0.0–1.0
- `reversibility` VARCHAR(20) CHECK ('easy','moderate','difficult','irreversible')
- `alternatives_considered` JSONB DEFAULT '[]'
- `success_criteria` JSONB DEFAULT '[]'
- `review_date` TIMESTAMPTZ
- `outcome_status` VARCHAR(20) CHECK ('pending','successful','failed','mixed','abandoned')
- `outcome_notes` TEXT
- `outcome_date` TIMESTAMPTZ
- `lessons_learned` JSONB DEFAULT '[]'
- `cognitive_load` DECIMAL(3,2) CHECK 0.0–1.0
- `decision_time_minutes` DECIMAL(6,2) CHECK >0
- `energy_level` VARCHAR(10) CHECK ('low','medium','high')
- `requires_followup` BOOLEAN DEFAULT FALSE

**Migration 003 adds**: `user_id VARCHAR(100) DEFAULT 'default'`
**Migration 007 adds**: `instance_id VARCHAR(255)` (via `_ensure_schema`, `enhanced_server.py` line 481)

**Indexes**: workspace_id, created_at DESC, decision_type, tags (GIN), full-text search GIN(summary || rationale)
**Triggers**: `update_decisions_modtime`
**Source**: `schema.sql` lines 31-52; `migrations/001_enhanced_decision_model.sql`

### 1.3 `progress_entries`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `description` | TEXT | NOT NULL | — |
| `status` | VARCHAR(20) | NOT NULL, CHECK | — |
| `percentage` | INTEGER | CHECK 0–100 | `0` |
| `linked_decision_id` | UUID | FK → decisions(id) | — |
| `priority` | VARCHAR(10) | CHECK | `'medium'` |
| `estimated_hours` | DECIMAL(5,2) | — | — |
| `actual_hours` | DECIMAL(5,2) | — | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `updated_at` | TIMESTAMPTZ | — | `NOW()` |
| `completed_at` | TIMESTAMPTZ | — | — |

**Status values**: `'PLANNED'`, `'IN_PROGRESS'`, `'COMPLETED'`, `'BLOCKED'`, `'CANCELLED'`
**Priority values**: `'low'`, `'medium'`, `'high'`, `'urgent'`

**Migration 003 adds**: `user_id VARCHAR(100) DEFAULT 'default'`
**Migration 007 adds**: `instance_id VARCHAR(255)`

**Indexes**: workspace_id, status, created_at DESC, linked_decision_id
**Triggers**: `update_progress_modtime`, `auto_complete_progress_trigger` (percentage=100 → COMPLETED)
**Source**: `schema.sql` lines 58-77

### 1.4 `session_snapshots`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `session_start` | TIMESTAMPTZ | NOT NULL | — |
| `session_end` | TIMESTAMPTZ | — | — |
| `focus_duration_minutes` | INTEGER | — | — |
| `interruption_count` | INTEGER | — | `0` |
| `tasks_completed` | INTEGER | — | `0` |
| `context_switches` | INTEGER | — | `0` |
| `session_quality` | VARCHAR(20) | CHECK | — |
| `notes` | TEXT | — | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |

**Session quality values**: `'poor'`, `'fair'`, `'good'`, `'excellent'`

**Migration 003 adds**: `user_id VARCHAR(100) DEFAULT 'default'`

**Note**: No API endpoints write to this table. It exists in schema only.
**Source**: `schema.sql` lines 82-97

### 1.5 `custom_data`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `category` | VARCHAR(100) | NOT NULL | — |
| `key` | VARCHAR(255) | NOT NULL | — |
| `value` | JSONB | NOT NULL | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `updated_at` | TIMESTAMPTZ | — | `NOW()` |

**Unique constraint**: `(workspace_id, category, key)`

**Migration 003 adds**: `user_id VARCHAR(100) DEFAULT 'default'`

**Source**: `schema.sql` lines 103-117

### 1.6 `entity_relationships`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `source_type` | VARCHAR(50) | NOT NULL | — |
| `source_id` | UUID | NOT NULL | — |
| `target_type` | VARCHAR(50) | NOT NULL | — |
| `target_id` | UUID | NOT NULL | — |
| `relationship_type` | VARCHAR(50) | NOT NULL | — |
| `strength` | DECIMAL(3,2) | CHECK 0.0–1.0 | `1.0` |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |

**Source/target types**: `'decision'`, `'progress'`, `'context'`
**Relationship types**: `'implements'`, `'blocks'`, `'relates_to'`, `'caused_by'`
**Note**: Uses relational SQL, NOT Apache AGE/Cypher despite `ag_catalog` schema reference in `unified_queries.py`
**Source**: `schema.sql` lines 123-138

### 1.7 `search_cache`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `query_text` | TEXT | NOT NULL | — |
| `query_hash` | VARCHAR(64) | NOT NULL | — |
| `results` | JSONB | NOT NULL | — |
| `result_count` | INTEGER | NOT NULL | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `expires_at` | TIMESTAMPTZ | — | `NOW() + INTERVAL '1 hour'` |

**Source**: `schema.sql` lines 144-156

---

## 2. Migration-Added Tables

### 2.1 `decision_relationships` (Migration 001)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `source_decision_id` | UUID | FK → decisions(id) ON DELETE CASCADE | — |
| `target_decision_id` | UUID | FK → decisions(id) ON DELETE CASCADE | — |
| `relationship_type` | VARCHAR(30) | CHECK | — |
| `notes` | TEXT | — | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |

**Relationship types**: `'builds_upon'`, `'supersedes'`, `'conflicts_with'`, `'validates'`, `'implements'`, `'questions'`
**Unique**: `(source_decision_id, target_decision_id, relationship_type)`

### 2.2 `adhd_metrics` (Migration 001)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `user_session_id` | VARCHAR(100) | — | — |
| `metric_type` | VARCHAR(30) | CHECK | — |
| `value` | DECIMAL(5,2) | NOT NULL | — |
| `level` | VARCHAR(10) | — | — |
| `context_note` | TEXT | — | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |

**Metric types**: `'energy'`, `'focus'`, `'attention'`, `'interruption'`, `'context_switch'`

### 2.3 `review_reminders` (Migration 001)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `decision_id` | UUID | FK → decisions(id) ON DELETE CASCADE | — |
| `scheduled_for` | TIMESTAMPTZ | NOT NULL | — |
| `reminder_type` | VARCHAR(30) | CHECK | — |
| `completed` | BOOLEAN | — | `FALSE` |
| `completed_at` | TIMESTAMPTZ | — | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |

**Reminder types**: `'implementation'`, `'outcome'`, `'periodic'`, `'low_confidence'`

### 2.4 `decision_patterns` (Migration 002)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `uuid_generate_v4()` |
| `workspace_id` | VARCHAR(255) | NOT NULL | — |
| `pattern_type` | VARCHAR(30) | CHECK | — |
| `pattern_signature` | JSONB | NOT NULL | — |
| `pattern_name` | VARCHAR(255) | — | — |
| `occurrence_count` | INT | — | `1` |
| `success_count` | INT | — | `0` |
| `failure_count` | INT | — | `0` |
| `mixed_count` | INT | — | `0` |
| `avg_confidence` | DECIMAL(3,2) | — | — |
| `avg_decision_time_minutes` | DECIMAL(6,2) | — | — |
| `avg_implementation_time_days` | DECIMAL(6,2) | — | — |
| `avg_cognitive_load` | DECIMAL(3,2) | — | — |
| `first_seen` | TIMESTAMPTZ | — | `NOW()` |
| `last_seen` | TIMESTAMPTZ | — | `NOW()` |
| `pattern_confidence` | DECIMAL(3,2) | CHECK 0.0–1.0 | — |
| `recommendations` | JSONB | — | `'[]'` |
| `adhd_insights` | JSONB | — | `'{}'` |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `updated_at` | TIMESTAMPTZ | — | `NOW()` |

**Pattern types**: `'tag_cluster'`, `'decision_chain'`, `'timing_pattern'`, `'energy_correlation'`
**Unique**: `(workspace_id, pattern_type, pattern_signature)`

### 2.5 `users` (Migration 003)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | VARCHAR(100) | PRIMARY KEY | — |
| `email` | VARCHAR(255) | UNIQUE | — |
| `display_name` | VARCHAR(255) | NOT NULL | — |
| `settings` | JSONB | — | `'{}'` |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `updated_at` | TIMESTAMPTZ | — | `NOW()` |

### 2.6 `workspaces` (Migration 003)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | VARCHAR(255) | PRIMARY KEY | — |
| `owner_user_id` | VARCHAR(100) | FK → users(id) | — |
| `name` | VARCHAR(255) | NOT NULL | — |
| `description` | TEXT | — | — |
| `path` | VARCHAR(500) | — | — |
| `created_at` | TIMESTAMPTZ | — | `NOW()` |
| `updated_at` | TIMESTAMPTZ | — | `NOW()` |

### 2.7 `user_workspace_access` (Migration 003)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `user_id` | VARCHAR(100) | FK → users(id) ON DELETE CASCADE | — |
| `workspace_id` | VARCHAR(255) | FK → workspaces(id) ON DELETE CASCADE | — |
| `role` | VARCHAR(20) | CHECK ('owner','write','read') | `'write'` |
| `granted_at` | TIMESTAMPTZ | — | `NOW()` |

**Primary key**: `(user_id, workspace_id)`

---

## 3. Views

### 3.1 `recent_activity`

UNION of decisions + progress_entries sorted by created_at DESC. Used by `get_recent_activity` handler.

**Source**: `schema.sql` lines 207-230 (overridden by migration 001 with enhanced fields)

### 3.2 `active_work`

IN_PROGRESS/PLANNED progress entries with linked decision context, ordered by priority.

**Source**: `schema.sql` lines 233-254

### 3.3 `decisions_needing_review` (Migration 001)

Decisions needing review based on age, tags, or outcome status.

### 3.4 `pattern_statistics` (Migration 002)

Aggregated pattern stats by workspace and type (only high-confidence patterns >0.7).

---

## 4. Triggers

| Trigger | Table | Action |
|---|---|---|
| `update_workspace_contexts_modtime` | `workspace_contexts` | Auto-update `updated_at` on UPDATE |
| `update_decisions_modtime` | `decisions` | Auto-update `updated_at` on UPDATE |
| `update_progress_modtime` | `progress_entries` | Auto-update `updated_at` on UPDATE |
| `auto_complete_progress_trigger` | `progress_entries` | percentage=100 → status=COMPLETED; percentage<100 AND status=COMPLETED → status=IN_PROGRESS |
| `update_patterns_modtime` | `decision_patterns` | Auto-update `updated_at` on UPDATE |

**Source**: `schema.sql` lines 162-200; `migrations/002_decision_patterns_table.sql`

---

## 5. Extensions

| Extension | Purpose |
|---|---|
| `uuid-ossp` | UUID generation (`uuid_generate_v4()`) |
| `pg_trgm` | Trigram similarity for text search |

**Source**: `schema.sql` lines 5-6

---

## 6. ID Scheme

All primary keys use UUID v4 (`uuid_generate_v4()`) except:
- `users.id`: VARCHAR(100) (user-defined, e.g., `'default'`)
- `workspaces.id`: VARCHAR(255) (workspace path)
- `user_workspace_access`: Composite PK `(user_id, workspace_id)`

UUIDs are generated server-side by PostgreSQL (schema default) or application-side via `uuid.uuid4()` (e.g., `enhanced_server.py` line 669).

---

## 7. Redis Cache Patterns

| Key Pattern | TTL | Written By | Invalidated By |
|---|---|---|---|
| `context:{workspace_id}:{instance_id}` | 300s | `_get_context` | `_update_context` |
| `query:context:{workspace_id}:{instance_id}` | 180s | `_get_context` | `_update_context` |
| `decisions:{workspace_id}:{limit}` | 300s | `_get_decisions` | `_log_decision` |
| `query:decisions:{workspace_id}:{limit}` | 180s | `_get_decisions` | — |
| `progress:{workspace_id}:{status}:{limit}` | 300s | `_get_progress` | `_log_progress` |
| `recent_activity:{workspace_id}:{hours}` | 180s | `_get_recent_activity` | `_log_decision`, `_log_progress` |
| `active_work:{workspace_id}` | 180s | `_get_active_work` | `_log_progress`, `_update_progress` |
| `search:{query_hash}` | 300s | `search_content` | — |
| `custom_data:{workspace_id}:{category}:{key}` | — | — | `save_custom_data`, `delete_custom_data` |
| `unified_search:{user_id}:{query}:{workspaces}` | 60s | `search_across_workspaces` | — |
| `relationships:{decision_id}:{user_id}:{...}:{depth}` | 1800s | `get_related_decisions` | — |
| `workspace_summary:{user_id}` | 300s | `get_workspace_summary` | — |
| `user_workspaces:{user_id}` | 300s | `_get_user_workspaces` | — |

**Source**: `enhanced_server.py` and `unified_queries.py`

---

## 8. Migration Sequencing

| # | File | Description | Tables/Columns |
|---|---|---|---|
| 001 | `001_enhanced_decision_model.sql` | Enhanced decision metadata | +14 cols on decisions, +decision_relationships, +adhd_metrics, +review_reminders |
| 002 | `002_decision_patterns_table.sql` | Decision patterns | +decision_patterns, +pattern_statistics view |
| 003 | `003_multi_tenancy_foundation.sql` | Multi-tenancy | +user_id on 5 tables, +users, +workspaces, +user_workspace_access |
| 004 | `004_unified_query_indexes.sql` | Cross-workspace indexes | Composite indexes for unified queries |
| — | 005, 006 | **MISSING** | Gap in migration numbering |
| 007 | `007_worktree_support_simple.sql` | Worktree isolation | +instance_id on progress_entries, +created_by_instance on decisions |

**Note**: `enhanced_server.py` `_ensure_schema()` also adds `instance_id` columns directly (lines 478-483), providing redundancy with migration 007.
