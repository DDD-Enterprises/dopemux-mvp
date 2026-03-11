# ConPort — Workflow and Gates

**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Source**: `docker/mcp-servers-source/conport/`

---

## 1. Progress Entry Lifecycle

### 1.1 Status State Machine

```
                 ┌──────────┐
                 │ PLANNED  │ ◄─── log_progress(status="PLANNED")
                 └────┬─────┘
                      │ update_progress(status="IN_PROGRESS")
                      ▼
                 ┌──────────────┐
                 │ IN_PROGRESS  │ ◄─── log_progress(status="IN_PROGRESS") [default]
                 └──┬──────┬───┘
    percentage=100  │      │  update_progress(status=...)
     (SQL trigger)  │      │
                    ▼      ├──────────────────────┐
              ┌───────────┐│                      │
              │ COMPLETED ││                      ▼
              └───────────┘│                 ┌─────────┐
                           │                 │ BLOCKED │
                           │                 └─────────┘
                           │
                           └──────────────────┐
                                              ▼
                                        ┌───────────┐
                                        │ CANCELLED │
                                        └───────────┘
```

**Valid statuses** (CHECK constraint, `schema.sql` line 62):
`'PLANNED'`, `'IN_PROGRESS'`, `'COMPLETED'`, `'BLOCKED'`, `'CANCELLED'`

**Auto-complete trigger** (`schema.sql` lines 184-200):
- percentage=100 AND old_percentage<100 → status=COMPLETED, completed_at=NOW()
- percentage<100 AND old_status=COMPLETED → status=IN_PROGRESS, completed_at=NULL

**Note**: No explicit validation prevents arbitrary status transitions in the API layer. The SQL trigger handles percentage-based transitions only. Any status→any status is allowed via `update_progress`.

### 1.2 Priority Values

`'low'`, `'medium'`, `'high'`, `'urgent'`

Default: `'medium'` (schema CHECK, `schema.sql` line 65)

---

## 2. Instance Isolation Gating

### 2.1 Isolation Rules

From `instance_detector.py` line 146:

| Status | Isolation | `instance_id` value | Visibility |
|---|---|---|---|
| `IN_PROGRESS` | Isolated | Current instance ID | Only in this worktree |
| `PLANNED` | Isolated | Current instance ID | Only in this worktree |
| `COMPLETED` | Shared | `NULL` | All worktrees |
| `BLOCKED` | Shared | `NULL` | All worktrees |
| `CANCELLED` | Shared | `NULL` | All worktrees |

### 2.2 Status Transition Instance Handling

When `update_progress` receives a status change (`enhanced_server.py` lines 1228-1237):

1. If new status is isolated (`IN_PROGRESS`/`PLANNED`): set `instance_id = current_instance_id`
2. If new status is shared (`COMPLETED`/`BLOCKED`/`CANCELLED`): set `instance_id = NULL`

This means completing a task automatically makes it visible to all worktrees.

### 2.3 Environment Variables

| Env Var | Purpose | Default |
|---|---|---|
| `DOPEMUX_INSTANCE_ID` | Current worktree instance identifier | `None` (single-worktree mode) |
| `DOPEMUX_WORKSPACE_ID` | Main workspace/repository root path | Current working directory |

**Source**: `instance_detector.py` lines 49-50

---

## 3. Fork/Promote Workflow

### 3.1 Fork (Shared → Instance)

**Purpose**: Copy PLANNED/IN_PROGRESS entries from shared (or source instance) to a new worktree instance.

**Handler**: `_fork_instance` (`enhanced_server.py` lines 974-1022)

**Flow**:
1. Read PLANNED/IN_PROGRESS entries from source (instance_id=NULL or source_instance)
2. For each entry, create a copy with new UUID and target instance_id
3. Original entries remain unchanged

**Auto-fork**: When `get_progress` returns empty and `DOPEMUX_AUTO_FORK_PROGRESS=1` (default: enabled), automatically forks from shared.
**Source**: `enhanced_server.py` lines 911-944, 146

### 3.2 Promote (Instance → Shared)

**Purpose**: Make instance-local progress entries visible to all worktrees by clearing `instance_id`.

**Single promote**: `_promote_progress` (`enhanced_server.py` lines 1039-1073)
- Sets `instance_id = NULL` on specific progress entry
- Publishes `progress_updated` event to DopeconBridge

**Bulk promote**: `_promote_all` (`enhanced_server.py` lines 1087-1127)
- Sets `instance_id = NULL` on all PLANNED/IN_PROGRESS entries for current instance in workspace
- Publishes event for each promoted entry

**⚠️ "Promotion" is NOT supervisor-validated truth elevation. It is purely an instance isolation transition.**

---

## 4. Decision Tracking

### 4.1 Decision Creation

**Handler**: `_log_decision` (`enhanced_server.py` lines 666-723)

**Flow**:
1. Generate UUID
2. INSERT into `decisions` table with workspace_id, summary, rationale, alternatives, tags, confidence_level, decision_type
3. Invalidate Redis caches for workspace
4. Publish `decision_logged` event to DopeconBridge
5. Return created decision

**Note**: No UPDATE endpoint for decisions. Decisions are effectively append-only via API (no PATCH/PUT route). However, the SQL schema allows updates (triggers exist for `updated_at`).

### 4.2 Decision Retrieval

**Handler**: `_get_decisions` (`enhanced_server.py` lines 802-857)

**Flow**:
1. Check Redis cache (`query:decisions:` and `decisions:` keys)
2. If miss, query PostgreSQL (ordered by created_at DESC, limited)
3. Apply token truncation (9000 token budget)
4. Cache result in Redis (180s + 300s)
5. Return with optional `truncation_stats`

---

## 5. Context Management

### 5.1 Context Get (with Instance Seeding)

**Handler**: `_get_context` (`enhanced_server.py` lines 497-578)

**Flow**:
1. Determine current instance_id from env
2. Check Redis cache
3. Query PostgreSQL for instance-specific context
4. If no instance-specific context found:
   a. Try to seed from shared context (instance_id=NULL)
   b. If no shared context, create default context
5. Cache result in Redis
6. Return context

### 5.2 Context Update

**Handler**: `_update_context` (`enhanced_server.py` lines 593-652)

**Flow**:
1. UPDATE workspace_contexts with COALESCE (only update non-null fields)
2. Read back updated row
3. Update Redis cache, invalidate query cache

### 5.3 Auto-Save Loop

**Handler**: `auto_save_loop` (`enhanced_server.py` lines 1497-1521)

**Interval**: 30 seconds (`self.auto_save_interval`, line 119)
**Action**: Touches `updated_at` on workspace_contexts modified in last 5 minutes

---

## 6. Custom Data CRUD

### 6.1 Save (Upsert)

**Handler**: `save_custom_data` (`enhanced_server.py` lines 1523-1560)
- INSERT ON CONFLICT DO UPDATE
- Invalidates Redis cache key

### 6.2 Get (Multi-level)

**Handler**: `get_custom_data` (`enhanced_server.py` lines 1562-1644)
- workspace_id + category + key → single item
- workspace_id + category → all items in category
- workspace_id only → all items

### 6.3 Delete

**Handler**: `delete_custom_data` (`enhanced_server.py` lines 1646-1679)
- Requires workspace_id + category + key
- Invalidates Redis cache

---

## 7. Search Workflows

### 7.1 Workspace Search

**Handler**: `search_content` (`enhanced_server.py` lines 1428-1495)
- Full-text search on decisions (GIN index with ts_rank)
- ILIKE search on progress_entries
- Results cached 300s

### 7.2 Cross-Workspace Search

**Handler**: `unified_search` → `unified_queries.py:search_across_workspaces`
- Requires `user_id` and `query`
- Searches across all user's workspaces (or specified subset)
- Performance target: <200ms

### 7.3 Relationship Traversal

**Handler**: `workspace_relationships` → `unified_queries.py:get_related_decisions`
- Recursive CTE traversal of entity_relationships
- Max depth: 3 (ADHD-safe default)
- Performance target: <500ms

---

## 8. Event Publishing Gates

Events are published to DopeconBridge on:

| Event | Trigger | Event Type |
|---|---|---|
| Decision logged | `_log_decision` completes | `decision_logged` |
| Progress logged | `_log_progress` completes | `progress_updated` |
| Progress updated | `_update_progress` completes | `progress_updated` |
| Progress promoted | `_promote_progress` completes | `progress_updated` |
| Bulk promote | `_promote_all` per-entry | `progress_updated` |

**Gate**: Publishing is best-effort. If DopeconBridge is unavailable (`_enabled=False`), events are silently dropped (non-blocking).

**Source**: `integration_bridge_client.py` lines 72-118

---

## 9. Token Truncation Gate

All list responses are truncated to a 9000-token budget:

- `_truncate_decisions` (`enhanced_server.py` lines 731-759)
- `_truncate_progress` (`enhanced_server.py` lines 761-787)
- Token estimation: 1 token ≈ 4 characters (conservative)
- 200 token overhead reserved for JSON structure

When truncation occurs, `truncation_stats` is included in the response:
```json
{
  "original_count": 50,
  "returned_count": 12,
  "estimated_tokens": 8950,
  "truncated": true
}
```

---

## 10. Multi-Tenancy Gates

### 10.1 Workspace-Level (Active)

All queries filter by `workspace_id`. This is the primary data isolation boundary.

### 10.2 Instance-Level (Active)

Progress entries filtered by `instance_id` for worktree isolation. Managed automatically on status transitions.

### 10.3 User-Level (Partial)

Migration 003 adds `user_id` columns, but most HTTP handlers do NOT filter by `user_id`. Only `unified_queries.py` queries use `user_id`.

**No authentication or authorization enforcement exists at the API layer.** All endpoints are unauthenticated.
