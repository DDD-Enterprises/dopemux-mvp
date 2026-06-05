# Audit for TP-DCP-MCP-RO-0002

## 1. Does the architecture accidentally make facade an authority?
No. `ARCHITECTURE.md` explicitly states: "The read-only MCP evidence facade provides a secure, loopback-only projection of repository truth, execution state, and structured context to ChatGPT via the MCP protocol. It does not possess any write authority."

## 2. Does any doc allow dopecon-bridge in Phase 1?
No. `TOOL_CONTRACT.md` and `ARCHITECTURE.md` both explicitly deny `dopecon-bridge` in Phase 1.

## 3. Does any doc allow generic search/fetch before source-label integrity is implemented?
No. `TOOL_CONTRACT.md` denies `search_all` and requires `project_id` for all queries.

## 4. Does registry design auto-expose initialized workspaces?
No. `MULTI_PROJECT_REGISTRY_CONTRACT.md` enforces that `dopemux init` provides eligibility only, while explicit approval is required for exposure via the facade.

## 5. Are stop conditions strong enough?
Yes. The explicit limits on reading unvalidated runtime files provide appropriate guardrails.
