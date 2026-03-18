# Preferred Surface Decision

Preferred canonical PM-plane integration surface: **REST `/api/*`**

## Role split

- `REST /api/*`
  - canonical service-to-service contract
- `FastMCP SSE / stdio`
  - agent-facing wrapper over the REST contract
- `JSON-RPC /mcp`
  - compatibility-only until parity and discovery gaps close

## Why this surface won

- broadest operational coverage
- easiest payload/default auditing
- least wrapper drift
- direct resource-route visibility
