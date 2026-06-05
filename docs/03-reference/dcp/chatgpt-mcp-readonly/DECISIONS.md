# Decisions

## Accepted Decisions
- Use MCP protocol for ChatGPT loopback.
- Enforce strict `project_id` requirements on all non-discovery tools.
- Implement explicit registry-based exposure.

## Rejected Alternatives
- **Global search / `search_all`**: Rejected due to high risk of cross-project context pollution.
- **Live Writes**: Rejected for Phase 1 to maintain strict safety boundary.
