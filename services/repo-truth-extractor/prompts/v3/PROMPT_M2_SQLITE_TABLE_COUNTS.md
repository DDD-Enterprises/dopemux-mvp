Goal: M2_SQLITE_TABLE_COUNTS.json

Prompt:
- Task: for each sqlite table discovered in M1, export count(*) only.
- Include:
  - db path
  - table name
  - row_count
  - status/error when count cannot be computed
- Hard rules:
  - No row-level exports.
  - No text/blob fields.
  - Keep output bounded and deterministic.
