Summarize the current task in ≤5 bullets.
Then:
1) Use **dope-context**: `/ctx:search-here` for hot files likely impacted by the task query.
2) Use **Exa** or **gpt-researcher**: fetch docs for mentioned libs at exact versions; quote relied-on sections.
3) Query **ConPort**: `search_decisions_fts` + `search_custom_data_value_fts` for open decisions & caveats (limit 5).
4) Confirm constraints (lint/types/tests ≥60% coverage; RFC-7807; interface contracts).
5) Propose a tiny test-first plan (≤5 steps), no edits yet; await "OK".

> Token thrift:
- **dope-context**: cap results to ≤5; refine query before widening.
- **Exa**: include specific lib, function, or exact error text.
- **ConPort**: `limit` 3–5 on all searches.