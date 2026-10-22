Summarize the current task in ≤5 bullets.
Then:
1) Use **dope-context**: `/ctx:search-here` for hot files likely impacted by the task query.
2) Use **gpt-researcher** or **WebSearch**: fetch docs for mentioned libs at exact versions; quote relied-on sections.
3) Query **ConPort**: `search_content` (`workspace_id`, `query`) for open decisions; read the top 5 results. Query caveats separately via `get_custom_data` (`workspace_id`, `category: "caveats"`), since caveats are stored under category `caveats` (see caveat.md) and `search_content` does not cover custom data.
4) Confirm constraints (lint/types/tests ≥60% coverage; RFC-7807; interface contracts).
5) Propose a tiny test-first plan (≤5 steps), no edits yet; await "OK".

> Token thrift:
- **dope-context**: cap results to ≤5; refine query before widening.
- **WebSearch**: include specific lib, function, or exact error text.
- **ConPort**: `search_content` has no `limit`; read only the top 3–5 results of each search.