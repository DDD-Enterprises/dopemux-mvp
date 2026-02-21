---
id: C1_SERVICE_ENTRYPOINTS
title: C1 Service Entrypoints
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: C1 Service Entrypoints (explanation) for dopemux documentation and developer
  workflows.
---
You are extracting facts from a repository snapshot.

TASK
Identify service entrypoints: CLI entrypoints, main modules, web server startup, worker startup, and container entrypoints.

OUTPUT
Return JSON only.
Top-level JSON must be:
{
  "artifacts": [
    {"artifact_name": "SERVICE_ENTRYPOINTS.json", "payload": <payload>}
  ]
}

PAYLOAD SHAPE
{"items":[
  {
    "id":"<stable-id>",
    "path":"<repo-relative-path>",
    "kind":"<cli|web|worker|lambda|script|container>",
    "evidence":[{"path":"...","lines":"Lx-Ly","quote":"<=20w"}]
  }
]}

RULES
- Use only provided files as evidence.
- If unknown, use "" or [] without inventing.
- Stable ordering: sort items by path, then kind, then id.
- Deterministic IDs: derive from (kind + path + symbol/name if present).

FILES:

