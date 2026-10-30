Log a caveat/constraint to **ConPort** as durable custom data (Memory Trinity plane 1).

Call: `mcp__conport__save_custom_data`

```json
{
  "workspace_id": "<repo-root>",
  "category": "caveats",
  "key": "<short-slug>",
  "value": {"text": "<constraint>", "tags": ["project:<name>", "slice:<name>", "caveat"]}
}
```

Search later: `mcp__conport__get_custom_data` with `workspace_id` and `category: "caveats"` (optionally with `key`).

> OpenMemory/Mem0 is **deprecated** — do not use.
