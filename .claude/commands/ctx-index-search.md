# ctx-index-search
You are Claude Code with MCP. Run these steps **in order** using the **Claude-Context** MCP:

**Arguments format:** `$ARGUMENTS` = `<PATH> :: <QUERY>`
- If only one part is provided, treat it as `<QUERY>` and use `.` for `<PATH>`.
- Examples:
  - `/ctx-index-search . :: rate limiter`
  - `/ctx-index-search ./packages/api :: JWT cookie refresh`
  - `/ctx-index-search login flow`

**Steps:**
1) Ensure the **Claude-Context** MCP server is connected. If not, tell me exactly what env var(s) are missing and stop.
2) Index `<PATH>` with incremental update if an index exists. If `<PATH>` doesn’t exist, stop and tell me.
3) After indexing finishes, run a semantic search for `<QUERY>`.
4) Return a concise list of the **top 10** matches as:  
   `file:line — score — 1–2 sentence snippet`  
   Group duplicates; prefer primary source files over generated code.
5) If indexing/search fails, show the error **and** the next command I should run to fix it (e.g., missing MILVUS_TOKEN or OPENAI_API_KEY).

**Tooling rules:**
- Use **Claude-Context** for indexing & search. Do **not** use web search tools for this command.
- If results are huge, summarize first, then ask if I want the full list.

> Token thrift:
- **Claude-Context**: cap results to ≤ **5** and refine the query before widening.
