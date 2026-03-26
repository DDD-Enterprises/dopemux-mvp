---
id: PROMPT_D_DB_SURFACE
title: Prompt D Db Surface
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt D Db Surface (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt D (v2): DB Surface (SQLite + Postgres + migrations + DAOs)

**Outputs:** `DB_SURFACE.json`, `MIGRATIONS.json`, `DAO_SURFACE.json`

---

## TASK

Produce THREE JSON files: `DB_SURFACE.json`, `MIGRATIONS.json`, `DAO_SURFACE.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` WORKING TREE.

## DB_SURFACE.json

- Extract CREATE TABLE / INDEX / TRIGGER statements from `.sql` files and inline SQL strings.
- Emit one item per db object:
  - `domain=code_db`
  - `kind=db_table|db_index|db_trigger`
  - `name=<object name>`
  - `strings` include: `["engine:sqlite"]` or `["engine:postgres"]` when identifiable.
  - `excerpt` include first 2 lines of the CREATE statement.

## MIGRATIONS.json

- Identify migration runners, schema version tables, migration directories.
- Emit items:
  - `domain=code_db`
  - `kind=migration`
  - `name=<migration id or filename>`
  - `symbol=<apply function if any>`

## DAO_SURFACE.json

- Identify modules that perform DB writes/reads (DAOs/repositories/stores).
- Emit items:
  - `domain=code_db`
  - `kind=dao`
  - `name=<module or class/function>`
  - `strings` include: `["op:INSERT", "op:UPDATE", "op:DELETE"]` if literal SQL contains those.

## RULES

- No inference about data model meaning.
- Universal schema, deterministic sorting.
