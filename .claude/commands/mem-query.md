Query **ConPort** decisions and caveats by topic (Memory Trinity plane 1).

Primary: `mcp__conport__semantic_search_conport`
```json
{"workspace_id": "<repo-root>", "query_text": "<topic>", "top_k": 5}
```

Fallback FTS: `mcp__conport__search_decisions_fts` / `search_custom_data_value_fts`

For code/docs meaning (plane 3): use `/ctx:search-here` (dope-context), not this command.