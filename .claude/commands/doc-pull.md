# /doc:pull
Given a query like a ticket ID, file path, or feature name:
1) Use available MCP servers to gather context:
   - **dope-context**: top passages from docs/ and src/ (`search_all` or `docs_search`, top_k ≤5)
   - **ConPort**: relevant ADRs & active decisions (`search_decisions_fts`, limit 5)
   - **Context7**: symbol-level API/library references for changed files
   - **ConPort custom_data**: naming/style preferences (category `preferences`)
2) De-duplicate & rank (prefer ADRs + How-tos for implementation).
3) Reply with a "Context Header" of 6–10 items (id, why included).
4) Attach those files to the session so I can proceed.
If something is missing, propose creating it with `/adr:new` or `/doc:new`.