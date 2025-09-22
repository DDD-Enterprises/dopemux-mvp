# /doc:pull
Given a query like a ticket ID, file path, or feature name:
1) Use available MCP servers to gather context:
   - claude-context: top passages from docs/ and src/ for the query
   - ConPort: relevant ADRs & active decisions
   - Context7: symbol-level API/library references for changed files
   - OpenMem: preferences/naming/style rules
2) De-duplicate & rank (prefer ADRs + How-tos for implementation).
3) Reply with a "Context Header" of 6–10 items (id, why included).
4) Attach those files to the session so I can proceed.
If something is missing, propose creating it with `/adr:new` or `/doc:new`.
