# /research:report
Generate a formatted report from a completed `/research:deep` run. Writes the result to `claudedocs/research/<slug>-<date>.md` so it survives the session.

**Usage**
- `/research:report` — uses the most recent `research_id` saved in ConPort active context.
- `/research:report abc-123-def` — explicit `research_id` (e.g., to format an older run).

**What you do**
1) Resolve the `research_id`:
   - If an argument was passed, use it.
   - Otherwise read `last_research.id` from ConPort active context:
     ```
     ctx = mcp__conport__get_active_context(workspace_id="$(git rev-parse --show-toplevel)")
     research_id = ctx.last_research.id
     ```
   - If neither is available, tell me to run `/research:deep "..."` first and stop.
2) Verify the MCP server is reachable (`docker ps --filter name=dopemux-mcp-gptr-mcp`). If not, ask me to start it.
3) Call `mcp__gpt-researcher__write_report` with the resolved `research_id`. Optionally pass a `custom_prompt` if I included guidance like "focus on cost trade-offs."
4) Compute the output path:
   - Slugify the original query from ConPort (or use the first 60 chars of the report title if no query is saved).
   - Path: `claudedocs/research/<slug>-<YYYY-MM-DD>.md`.
   - Ensure `claudedocs/research/` exists; create if missing.
5) Write the report Markdown to that path. Prepend YAML frontmatter:
   ```yaml
   ---
   research_id: <id>
   query: <original query if known>
   generated_at: <ISO timestamp>
   sources_consulted: <count from report metadata>
   ---
   ```
6) Print the absolute path of the written file plus a 3-line synthesis preview (first paragraph of the report) so I don't have to open the file to know what's in it.

**Notes**
- Output goes under `claudedocs/research/` per the project's file-organization rules — analyses live in `claudedocs/`, not in source dirs.
- If `mcp__gpt-researcher__write_report` accepts a format flag, default to Markdown (`format=markdown`). Don't generate PDF unless I explicitly ask.
- Reports include citations inline. Don't post-process them away.
- This command is idempotent: running it twice on the same `research_id` overwrites the file with a fresh formatting pass.
