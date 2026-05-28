# ctx/index-search
Use the **Claude-Context** MCP to (1) index a path, then (2) search it.

**Args**: `$ARGUMENTS` = `<PATH> :: <QUERY>`  
If no path is provided, use `.`.

**Steps**
1) Ensure **Claude-Context** is connected. If not, stop and tell me which env is missing (OPENAI_API_KEY, MILVUS_ADDRESS, MILVUS_TOKEN or local Milvus/Ollama).
2) Index `<PATH>` (incremental if index exists).
3) Run semantic search for `<QUERY>`, return top 10 as `file:line — score — 1-2 sentence snippet`. Prefer source over generated files; group duplicates.
4) If indexing/search fails, show the exact error plus the next fix command.

**Tools**: Claude-Context only.

> Token thrift:
- **Claude-Context**: cap results to ≤ **5** and refine the query before widening.
