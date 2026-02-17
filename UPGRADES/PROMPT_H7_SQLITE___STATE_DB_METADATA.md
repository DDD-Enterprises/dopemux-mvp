# Phase H7: Home SQLite + State DB Metadata

Goal:
- Detect references to sqlite DB files, schema files, migrations, or state directories in home control plane configs.
- If you have actual sqlite schema text in context, extract table/index names as metadata only (no secret contents).

Outputs:
- HOME_SQLITE_SCHEMA.json

HOME_SQLITE_SCHEMA.json:
{
  "surface_version": "H7.v1",
  "generated_at": "<iso8601>",
  "db_files": [
    {
      "path": "<path>",
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes":"<string>"
    }
  ],
  "schema_hints": [
    {
      "source_path": "<path>",
      "tables": ["<string>"],
      "indexes": ["<string>"],
      "triggers": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
