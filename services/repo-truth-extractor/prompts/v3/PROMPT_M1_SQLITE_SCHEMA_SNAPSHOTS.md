Goal: M1_SQLITE_SCHEMA_SNAPSHOTS.json

Prompt:
- Task: for each sqlite/db discovered in M0, export schema-only metadata.
- Include:
  - table names
  - index names
  - trigger names
  - PRAGMA user_version
  - PRAGMA foreign_keys
  - sqlite_version when available
- Hard rules:
  - No row dumps.
  - No blob/text content export.
  - Report per-db failures as status/error without guessing.
