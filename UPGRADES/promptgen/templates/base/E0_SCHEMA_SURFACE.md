---
id: E0_SCHEMA_SURFACE
title: E0 Schema Surface
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: E0 Schema Surface (explanation) for dopemux documentation and developer workflows.
---
You are extracting facts from a repository snapshot.

TASK
Identify schema and contract surfaces: database schemas, migrations, API schemas, and event/message schemas.

OUTPUT
Return JSON only.
Top-level JSON must be:
{
  "artifacts": [
    {"artifact_name": "E0_SCHEMA_SURFACE.json", "payload": <payload>}
  ]
}

PAYLOAD SHAPE
{"items":[
  {
    "id":"<stable-id>",
    "path":"<repo-relative-path>",
    "kind":"<db_schema|migration|api_schema|event_schema|other>",
    "evidence":[{"path":"...","lines":"Lx-Ly","quote":"<=20w"}]
  }
]}

RULES
- Use only provided files as evidence.
- If unknown, use "" or [] without inventing.
- Stable ordering: sort items by path, then kind, then id.
- Deterministic IDs: derive from (kind + path + symbol/name if present).

FILES:

