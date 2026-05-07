# /research-quick
Run a fast multi-engine search via the gpt-researcher MCP server. Synthesis is light; this is for fact-finding before implementing, not for deep investigation.

**Usage**
- `/research-quick "current latest stable fastmcp version on PyPI"`
- `/research-quick "Next.js App Router data fetching patterns"`
- `/research-quick "what does Starlette's Route() take as arguments"`

**What you do**
1) Verify the MCP server is reachable. If `docker ps --filter name=dopemux-mcp-gptr-mcp --format '{{.Status}}'` doesn't show `Up ... (healthy)`, tell me to run `docker compose -f compose.yml up -d gptr-mcp` and stop.
2) Call `mcp__gpt-researcher__quick_search` with `query=<the quoted argument>`.
3) Print the results inline. No file is written, no `research_id` is saved. Lead with a 1–2 sentence synthesis, then list sources as a bullet list of `[title](url)` — most relevant first.
4) End with a one-line nudge: if the answer needs depth or comparison, suggest `/research-deep` with a refined query.

**Notes**
- Target: < 30s end-to-end. If the MCP server stalls, kill the call and recommend a narrower query.
- Do NOT save anything to ConPort — this is the lightweight path. Use `/research-deep` when the work is worth persisting.
- Cost: a few cents in OpenAI tokens. If `OPENAI_API_KEY` is unset in `.env`, the call will fail; tell me to fill it in and restart `gptr-mcp`.
