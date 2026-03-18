# ConPort Surface Inventory

## Active callable surfaces

| Surface | Count | Role |
|---|---:|---|
| REST `/api/*` | 21 logical operations | canonical backend contract |
| FastMCP SSE / stdio | 13 tools | agent-facing wrapper over REST |
| JSON-RPC `/mcp` | 13 methods | compatibility surface with parity gaps |

## Inventory summary

- REST includes all core PM operations, custom data routes, and current Phase 2 routes.
- FastMCP covers core PM operations plus `workspace_summary`, but does not expose search or custom data directly.
- JSON-RPC exposes core operations, but `workspace_summary` is missing from parity and `search_content` is undiscoverable.
