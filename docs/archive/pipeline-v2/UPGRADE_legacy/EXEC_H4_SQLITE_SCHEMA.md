---
id: EXEC_H4_SQLITE_SCHEMA
title: Exec H4 Sqlite Schema
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Exec H4 Sqlite Schema (explanation) for dopemux documentation and developer
  workflows.
---
# EXECUTABLE PROMPT: H4 - SQLite Schema Extraction

---

## YOUR ROLE

You are a **mechanical schema extractor**. Extract SQLite database schemas. **DO NOT extract table contents.**

---

## TASK

Extract schema definitions from SQLite databases in home directory.

Produce ONE JSON file: `HOME_SQLITE_SCHEMA.json`

---

## SCOPE (Include ONLY These Files)

- `~/.dopemux/context.db`
- `~/.dopemux/global_index.sqlite`

**Do NOT:**
- Extract table contents (no SELECT * FROM)
- Read any other .db files
- Include session/cache databases

---

## EXTRACTION METHOD

For each SQLite database file:

1. **Get schema via SQL:**
   ```sql
   SELECT name, type, sql 
   FROM sqlite_master 
   WHERE type IN ('table', 'index', 'trigger', 'view')
   ORDER BY type, name;
   ```

2. **Get user version:**
   ```sql
   PRAGMA user_version;
   ```

3. **DO NOT run:**
   ```sql
   SELECT * FROM <any_table>;  -- FORBIDDEN
   ```

---

## OUTPUT: HOME_SQLITE_SCHEMA.json

```json
{
  "db_id": "home_db:~/.dopemux/context.db",
  "db_path": "~/.dopemux/context.db",
  "db_size_bytes": 33000,
  "user_version": 3,
  "objects": [
    {
      "name": "events",
      "type": "table",
      "sql": "CREATE TABLE events (\n  event_id TEXT PRIMARY KEY,\n  ts TEXT NOT NULL,\n  data BLOB\n)"
    },
    {
      "name": "idx_events_ts",
      "type": "index",
      "sql": "CREATE INDEX idx_events_ts ON events(ts)"
    }
  ]
}
```

### Object Types

- `table` - Table definitions
- `index` - Index definitions
- `trigger` - Trigger definitions
- `view` - View definitions

---

## EXAMPLE FULL OUTPUT

```json
{
  "artifact_type": "HOME_SQLITE_SCHEMA",
  "generated_at_utc": "2026-02-15T21:45:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "databases": [
    {
      "db_id": "home_db:~/.dopemux/context.db",
      "db_path": "~/.dopemux/context.db",
      "db_size_bytes": 33000,
      "user_version": 3,
      "objects": [
        {
          "name": "events",
          "type": "table",
          "sql": "CREATE TABLE events (event_id TEXT PRIMARY KEY, ts TEXT, data BLOB)"
        },
        {
          "name": "context_index",
          "type": "table",
          "sql": "CREATE TABLE context_index (doc_id TEXT, tokens TEXT, embedding BLOB)"
        },
        {
          "name": "idx_events_ts",
          "type": "index",
          "sql": "CREATE INDEX idx_events_ts ON events(ts)"
        }
      ]
    },
    {
      "db_id": "home_db:~/.dopemux/global_index.sqlite",
      "db_path": "~/.dopemux/global_index.sqlite",
      "db_size_bytes": 37000,
      "user_version": 2,
      "objects": [
        {
          "name": "memory_chunks",
          "type": "table",
          "sql": "CREATE TABLE memory_chunks (chunk_id TEXT, content TEXT, metadata JSON)"
        },
        {
          "name": "idx_chunks_metadata",
          "type": "index",
          "sql": "CREATE INDEX idx_chunks_metadata ON memory_chunks(metadata)"
        }
      ]
    }
  ]
}
```

---

## HARD RULES

1. **Schema only** - NO table contents
2. **No SELECT \* FROM** - only schema queries
3. **JSON only** - no markdown, no prose
4. **ASCII only**
5. **Deterministic sorting** - by (db_path, object_type, object_name)

---

## WHY THIS MATTERS

SQLite schemas reveal:
- **Memory/context architecture** (what's being stored)
- **Indexing strategy** (what's being queried)
- **Data model assumptions** (event structure, chunk format)

This is **critical for understanding runtime behavior** without exposing actual data.

---

## BEGIN EXTRACTION

Extract schemas from `context.db` and `global_index.sqlite` now.

**Remember: SCHEMA ONLY, NO DATA.**
