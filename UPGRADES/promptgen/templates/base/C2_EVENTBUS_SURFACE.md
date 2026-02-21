You are extracting facts from a repository snapshot.

TASK
Identify event bus surface facts: event producers, event consumers, event handler registration points, and bus abstractions.

OUTPUT
Return JSON only.
Top-level JSON must be:
{
  "artifacts": [
    {"artifact_name": "EVENTBUS_SURFACE.json", "payload": <payload>}
  ]
}

PAYLOAD SHAPE
{"items":[
  {
    "id":"<stable-id>",
    "path":"<repo-relative-path>",
    "kind":"<producer|consumer|handler|bus_abstraction|topic|other>",
    "evidence":[{"path":"...","lines":"Lx-Ly","quote":"<=20w"}]
  }
]}

RULES
- Use only provided files as evidence.
- If unknown, use "" or [] without inventing.
- Stable ordering: sort items by path, then kind, then id.
- Deterministic IDs: derive from (kind + path + symbol/name if present).

FILES:

