---
id: D0_DOC_INDEX
title: D0 Doc Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: D0 Doc Index (explanation) for dopemux documentation and developer workflows.
---
You are extracting facts from a repository snapshot.

TASK
Build a documentation index: key docs, contract docs, architecture docs, and operational docs with stable classification.

OUTPUT
Return JSON only.
Top-level JSON must be:
{
  "artifacts": [
    {"artifact_name": "DOC_INDEX.json", "payload": <payload>}
  ]
}

PAYLOAD SHAPE
{"items":[
  {
    "id":"<stable-id>",
    "path":"<repo-relative-path>",
    "kind":"<contract|architecture|operational|tutorial|reference|other>",
    "evidence":[{"path":"...","lines":"Lx-Ly","quote":"<=20w"}]
  }
]}

RULES
- Use only provided files as evidence.
- If unknown, use "" or [] without inventing.
- Stable ordering: sort items by path, then kind, then id.
- Deterministic IDs: derive from (kind + path + symbol/name if present).

FILES:

