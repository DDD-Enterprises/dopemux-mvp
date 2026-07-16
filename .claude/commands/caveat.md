Log a caveat/constraint to **ConPort** as durable custom data (Memory Trinity plane 1).

Call: `mcp__conport__conport_save_custom_data`

```json
{
  "workspace_id": "<repo-root>",
  "category": "caveats",
  "key": "<short-slug>",
  "value": {"text": "<constraint>", "tags": ["project:<name>", "slice:<name>", "caveat"]}
}
```

Search later: `mcp__conport__conport_search_content` with query `caveat: <term>`.

> OpenMemory/Mem0 is **deprecated** — do not use.
