# /research-deep
Run a comprehensive multi-source research job via the gpt-researcher MCP server. The MCP call blocks until research completes, then returns a `research_id` for report generation.

**Usage**
- `/research-deep "trade-offs of microservices vs monolith for a 10-person SaaS"`
- `/research-deep "best practices for postgres logical replication into a read replica"`
- `/research-deep "how do Linear, Asana, and Height handle real-time collaboration internals"`

**What you do**
1) Verify the MCP server is reachable. If `docker ps --filter name=dopemux-mcp-gptr-mcp --format '{{.Status}}'` doesn't show `Up ... (healthy)`, tell me to run `docker compose -f compose.yml up -d gptr-mcp` and stop.
2) Call `mcp__gpt-researcher__deep_research` with `query=<the quoted argument>` and wait for the tool response. Capture the `research_id` from the completed response.
3) Save the `research_id` and query to ConPort active context so I can resume later:
   ```
   mcp__conport__update_active_context(
     workspace_id="$(git rev-parse --show-toplevel)",
     patch_content={
       "last_research": {
         "id": "<research_id>",
         "query": "<original query>",
         "started_at": "<ISO timestamp>"
       }
     }
   )
   ```
4) Print a short status line: the `research_id`, source count if present, and three concrete next steps:
   - "Research completed; skim the synthesis preview first."
   - "When ready: `/research-report` (no args needed; pulls last research_id from ConPort)."
   - "Need raw context? `mcp__gpt-researcher__get_research_context` with the saved id."
5) Print the synthesis preview from the completed response when available, but still save the `research_id` so `/research-report` works.

**Notes**
- ADHD-friendly: the `research_id` is a durable handle after the MCP call returns. If the session is interrupted before the tool response, rerun `/research-deep` because no completed ID has been saved yet.
- Cost: typically $0.10–$1.00 in OpenAI tokens depending on depth. Watch for runaway "tell me everything about X" queries — narrow questions converge faster and cheaper.
- Required env: `OPENAI_API_KEY` (LLM synthesis), `TAVILY_API_KEY` (strongest search signal). `EXA_API_KEY` is recommended.
- If the user supplied a flag like `--exhaustive` or `--quick`, pass it through as a `report_type` or depth tweak the MCP supports; otherwise use defaults.
