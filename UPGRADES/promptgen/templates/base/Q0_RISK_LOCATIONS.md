---
id: Q0_RISK_LOCATIONS
title: Q0 Risk Locations
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Q0 Risk Locations (explanation) for dopemux documentation and developer workflows.
---
You are extracting facts from a repository snapshot.

TASK
Identify risk locations: determinism risks, idempotency risks, concurrency risks, and failure-prone execution surfaces.

OUTPUT
Return JSON only.
Top-level JSON must be:
{
  "artifacts": [
    {"artifact_name": "Q0_RISK_LOCATIONS.json", "payload": <payload>}
  ]
}

PAYLOAD SHAPE
{"items":[
  {
    "id":"<stable-id>",
    "path":"<repo-relative-path>",
    "kind":"<determinism|idempotency|concurrency|error_handling|other>",
    "evidence":[{"path":"...","lines":"Lx-Ly","quote":"<=20w"}]
  }
]}

RULES
- Use only provided files as evidence.
- If unknown, use "" or [] without inventing.
- Stable ordering: sort items by path, then kind, then id.
- Deterministic IDs: derive from (kind + path + symbol/name if present).

FILES:

