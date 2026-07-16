Short-lived scratch notes in **ConPort** (Memory Trinity plane 1).

Call: `mcp__conport__conport_save_custom_data`
```json
{
  "workspace_id": "<repo-root>",
  "category": "scratch",
  "key": "session-<timestamp>",
  "value": {"notes": "<text>"}
}
```

Cleared on `/switch` by archiving scratch entries to decisions/runbooks if needed, then starting fresh context.

> Token thrift: prefer summaries/search with small `limit` (3–5) before full context.
