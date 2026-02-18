Goal: HOME_SQLITE_SCHEMA.json

Prompt:
- Identify sqlite db files (ex: context.db, global_index.sqlite).
- Extract only:
  - file presence, size, mtime
  - schema metadata if available via sidecar or documented schema files (no table dumps).
  - If you do query schema, output only table names + columns, not row data.