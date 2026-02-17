---
id: EXEC_D_DB_SURFACE
title: Exec D Db Surface
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Exec D Db Surface (explanation) for dopemux documentation and developer workflows.
---
# EXECUTABLE PROMPT: D - DB Surface (DDL + Migrations + DAOs)

---

## YOUR ROLE

You are a **mechanical extractor**. Extract database object definitions, migration logic, and data access patterns. No inference about data model meaning.

---

## TASK

Scan the provided files and produce THREE JSON files:
1. `DB_SURFACE.json`
2. `MIGRATIONS.json`
3. `DAO_SURFACE.json`

---

## OUTPUT 1: DB_SURFACE.json

Find CREATE TABLE / INDEX / TRIGGER statements in `.sql` files and inline SQL strings in Python.

```json
{
  "path": "services/chronicle/db/schema.py",
  "line_range": [15, 25],
  "domain": "code_db",
  "kind": "db_table",
  "name": "events",
  "engine": "sqlite",
  "columns": ["event_id TEXT PRIMARY KEY", "event_type TEXT NOT NULL", "ts REAL", "payload TEXT"],
  "excerpt": "CREATE TABLE IF NOT EXISTS events (\n  event_id TEXT PRIMARY KEY,\n  event_type TEXT NOT NULL"
}
```

### kind Classification

| SQL Pattern                            | kind         |
| -------------------------------------- | ------------ |
| `CREATE TABLE`                         | `db_table`   |
| `CREATE INDEX` / `CREATE UNIQUE INDEX` | `db_index`   |
| `CREATE TRIGGER`                       | `db_trigger` |
| `CREATE VIEW`                          | `db_view`    |

### engine Detection

- `sqlite3.connect` / `aiosqlite` → `sqlite`
- `asyncpg` / `psycopg` / `sqlalchemy+postgresql` → `postgres`
- If unclear → `unknown`

### Where to Look

- `.sql` files
- Python strings containing `CREATE` (triple-quoted or f-strings)
- SQLAlchemy `Table(...)` / `Column(...)` definitions
- Pydantic model → DB mappings if explicit

---

## OUTPUT 2: MIGRATIONS.json

Find migration files, migration runners, and schema version tracking.

```json
{
  "path": "services/chronicle/db/migrate.py",
  "line_range": [30, 45],
  "domain": "code_db",
  "kind": "migration",
  "name": "001_initial_schema",
  "migration_type": "inline",
  "direction": "up",
  "tables_affected": ["events", "sessions"],
  "symbol": "apply_migrations",
  "excerpt": "def apply_migrations(conn):\n    conn.execute(\"CREATE TABLE IF NOT EXISTS...\")"
}
```

### migration_type

- `inline` — SQL embedded in Python
- `file` — separate .sql migration file
- `alembic` — Alembic migration
- `custom` — custom migration runner

---

## OUTPUT 3: DAO_SURFACE.json

Find modules/classes that perform database reads and writes.

```json
{
  "path": "services/chronicle/db/store.py",
  "line_range": [50, 65],
  "domain": "code_db",
  "kind": "dao",
  "name": "EventStore.insert_event",
  "operations": ["INSERT"],
  "tables_referenced": ["events"],
  "is_transactional": true,
  "symbol": "insert_event",
  "excerpt": "async def insert_event(self, event):\n    await self.db.execute(\"INSERT INTO events...\")"
}
```

### operations

Extract from literal SQL: `INSERT`, `UPDATE`, `DELETE`, `SELECT`, `UPSERT` / `ON CONFLICT`.

---

## HARD RULES

1. **No inference** — extract literal SQL and function names only
2. **JSON only** — no markdown, no prose
3. **ASCII only**
4. **Deterministic sorting** — by path, then line_range
5. **path + line_range required** on every item
6. **excerpt ≤ 3 lines** — exact text, truncated

---

## OUTPUT FORMAT

Each file wrapper:

```json
{
  "artifact_type": "DB_SURFACE",
  "generated_at_utc": "2026-02-15T22:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```

---

## BEGIN EXTRACTION

Process the provided context files and produce the three JSON outputs now.
