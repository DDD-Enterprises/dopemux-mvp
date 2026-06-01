Summarize the current task in ≤5 bullets.
Then:
1) Use Claude-Context: list hot files & TODOs likely impacted.
2) Use Exa: fetch docs for mentioned libs/frameworks at the exact versions; quote the sections we’ll rely on.
3) Query openmemory (Mem0): “open decisions & caveats” for this project/slice.
4) Confirm constraints (lint/types/tests ≥60% coverage; RFC-7807; interface contracts).
5) Propose a tiny test-first plan (≤5 steps), no edits yet; await my “OK”.

> Token thrift:
- **Claude-Context**: cap results to ≤ **5** and refine the query before widening.
- **Exa**: avoid broad/generic queries; include specific lib, function, or exact error text.
