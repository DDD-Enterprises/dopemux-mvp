Summarize the current task in ≤5 bullets.
Then:
1) Use **dope-context**: `/ctx:search-here` for hot files likely impacted by the task query.
2) Use **gpt-researcher** or **WebSearch**: fetch docs for mentioned libs at exact versions; quote relied-on sections.
3) Query **ConPort**: `mcp__conport__conport_search_content` for open decisions & caveats (read the top 5 hits).
4) Confirm constraints (lint/types/tests ≥90% coverage on touched code, as tdd-loop and testgen enforce; RFC-7807; interface contracts).
5) Propose a tiny test-first plan (≤5 steps), no edits yet; await "OK".

> Token thrift:
- **dope-context**: cap results to ≤5; refine query before widening.
- **WebSearch**: include specific lib, function, or exact error text.
- **ConPort**: `limit` 3–5 on all searches.