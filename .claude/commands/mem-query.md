Query **ConPort** decisions, progress and caveats by topic (Memory Trinity plane 1).

Primary (decisions and progress): `mcp__conport__search_content`
```json
{"workspace_id": "<repo-root>", "query": "<topic>"}
```

Read only the top 5 results (`search_content` has no `limit`).

Fallback (caveats, which `search_content` does not cover): `mcp__conport__get_custom_data`
```json
{"workspace_id": "<repo-root>", "category": "caveats"}
```

Optionally add `"key": "<caveat-key>"` to read one caveat.

For code/docs meaning (plane 3): use `/ctx:search-here` (dope-context), not this command.
