Search **ConPort** for decisions, progress and caveats by project/slice/tag (Memory Trinity plane 1).

`search_content` searches decisions and progress entries only. Caveats live in custom_data (category `caveats`) and are read with `get_custom_data`.

Examples:
```
mcp__conport__search_content {"workspace_id":"<repo-root>","query":"open decisions"}
mcp__conport__get_custom_data {"workspace_id":"<repo-root>","category":"caveats"}
mcp__conport__get_custom_data {"workspace_id":"<repo-root>","category":"caveats","key":"<caveat-key>"}
```

`search_content` has no `limit`: read only the top 5 results.

For semantic code/docs retrieval use `/ctx:search-here` (dope-context plane 3).
