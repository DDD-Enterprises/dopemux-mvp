Log a caveat/constraint to **ConPort** as durable custom data (Memory Trinity plane 1).

Call: `mcp__conport__log_custom_data`

```json
{
  "workspace_id": "<repo-root>",
  "category": "caveats",
  "key": "<short-slug>",
  "value": {"text": "<constraint>", "tags": ["project:<name>", "slice:<name>", "caveat"]}
}
```

Search later: `mcp__conport__search_custom_data_value_fts` with query `caveat: <term>`.

> OpenMemory/Mem0 is **deprecated** — do not use.