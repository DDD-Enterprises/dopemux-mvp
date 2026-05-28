# ctx/search-here
Fast semantic search in the **current workspace** using **Claude-Context**.

**Args**: `$ARGUMENTS` = `<QUERY>`

**Steps**
1) Confirm Claude-Context is connected; if not, report the missing envs and stop.
2) Run search for `<QUERY>` across the current workspace (assume already indexed; if not, do a quick index first).
3) Show top 10 hits as `file:line — score — short snippet`. Offer to open files inline.

> Token thrift:
- **Claude-Context**: cap results to ≤ **5** and refine the query before widening.
