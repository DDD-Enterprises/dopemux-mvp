# PROMPT_H7_SQLITE___STATE_DB_METADATA
Goal: extract HOME sqlite/state DB metadata + schema hints without dumping DB contents (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
From allowlisted roots:
- ~/.dopemux/*.sqlite, ~/.dopemux/*.db, ~/.dopemux/**.sqlite, ~/.dopemux/**.db
- ~/.config/dopemux/** (only if it references sqlite/db)
- ~/.config/taskx/** (only if it references sqlite/db)
- any text docs that mention schema/migrations under ~/.dopemux/**

Extract:
1) DB file catalog (path, size, mtime)
2) DB role hints (what each db is for) ONLY if explicitly referenced by config/docs
3) Schema metadata ONLY if present in text files (like .sql migrations, schema docs, or printed schema JSON)
4) Safety posture: whether DB is treated append-only, TTL/caps, locking, WAL settings if explicit in configs
5) Reference edges: config -> db file

## Hard rules
- Do NOT open sqlite binary content.
- Do NOT attempt to query sqlite.
- Only extract schema/table names if they exist in text files.
- Evidence per claim.
- If a db appears but no references explain it, mark UNKNOWN role.

## Outputs (JSON only)
Produce:
1) HOME_SQLITE_STATE_INDEX.json
2) HOME_SQLITE_SCHEMA_HINTS.json
3) HOME_SQLITE_REFERENCE_GRAPH.json

### 1) HOME_SQLITE_STATE_INDEX.json
{
  "artifact": "HOME_SQLITE_STATE_INDEX",
  "generated_at": "<iso8601>",
  "db_files": [
    {
      "path": "<db_path>",
      "size": <int_bytes>,
      "mtime": "<iso8601>",
      "role_hint": "<literal_or_UNKNOWN>",
      "evidence": ["HOMECTRL: <path>"]
    }
  ],
  "largest": [{"path":"...","size":0}],
  "unknowns": [{"path":"...", "reason":"No config references found"}]
}

### 2) HOME_SQLITE_SCHEMA_HINTS.json
{
  "artifact": "HOME_SQLITE_SCHEMA_HINTS",
  "generated_at": "<iso8601>",
  "schema_sources": [
    {
      "source_path": "<text_file_path>",
      "db_target": "<db_path_or_UNKNOWN>",
      "tables": ["<table_name>"],
      "indexes": ["<index_name>"],
      "triggers": ["<trigger_name>"],
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "notes": [
    "Schema extracted only from text sources; sqlite binaries not queried."
  ]
}

### 3) HOME_SQLITE_REFERENCE_GRAPH.json
{
  "artifact": "HOME_SQLITE_REFERENCE_GRAPH",
  "generated_at": "<iso8601>",
  "edges": [
    {
      "from_config": "<file>",
      "to_db": "<db_path>",
      "ref_type": "path_ref|dsn_ref|unknown",
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "orphans": [{"db":"<db_path>", "reason":"No referencing config found"}]
}

## Determinism
- Sort db_files by path.
- Sort schema_sources by source_path.
- Sort edges by (from_config, to_db).

## Finish
Emit ONLY the three JSON artifacts.
No prose.
No markdown fences.
