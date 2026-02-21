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

