# DMX-DCP-MODEL-ROUTING-MVP-0000 — MCP_INVENTORY.md

## MCP Server Inventory

| Server | Tool | Path | Read/write | Side effects | Safe automation class | Startup owner | Evidence | Unknowns |
|--------|------|------|------------|--------------|-----------------------|---------------|----------|----------|
| conport | Knowledge graph, decisions, progress | compose.yml:conport + .mcp.json | Read + write (claimed) | Decision append, progress update | Write (ConPort contract) | Docker compose | compose.yml + registry.yaml | Write contract enforcement UNKNOWN |
| pal | Multi-model reasoning | compose.yml:pal + mcp-proxy-config | Read | Model calls | Read | Docker compose | compose.yml | No side effects observed |
| litellm | Model router/proxy | compose.yml:litellm + litellm.config.yaml | Read | Proxy routing | Read | Docker compose | compose.yml + litellm.config.yaml | Fallback behavior per config |
| dope-context | Semantic code/docs search | compose.yml:dope-context + mcp-proxy-config | Read | Search index query | Read | Docker compose | compose.yml + registry.yaml | Indexing posture UNKNOWN |
| serena | ADHD accommodation (LSP) | mcp-proxy-config + registry.yaml | Read | LSP navigation | Read | uvx mcp-proxy | mcp-proxy-config | Complexity scoring UNKNOWN |
| gpt-researcher | Deep web research | mcp-proxy-config + registry.yaml | Read | Web search + synthesis | Read | uvx mcp-proxy | mcp-proxy-config | Search volume limits UNKNOWN |
| exa | Neural web search | mcp-proxy-config + registry.yaml | Read | Neural search | Read | uvx mcp-proxy | mcp-proxy-config | No side effects observed |
| desktop-commander | Terminal/process control | registry.yaml | Read + write (claimed) | Process spawn, FS ops | Write (terminal) | uvx mcp-proxy | registry.yaml | Mutation surface UNKNOWN |
| task-orchestrator | 13-tool MCP runtime | services/task-orchestrator/ + mcp-proxy-config | Read + write (claimed) | Task state, transitions | Write (task state) | python server.py | server.py + mcp-proxy-config | Write authority UNKNOWN |
| dope-memory | Temporal chronicle | .mcp.json + registry.yaml | Read + write (claimed) | Chronicle append | Write (memory) | Docker compose | .mcp.json | Append/reflection writes forbidden in hard blocks |
| leantime-bridge | PM bridge | registry.yaml + mcp-proxy-config | Read | PM queries | Read | uvx mcp-proxy | registry.yaml | Token auth UNKNOWN |
| mas-sequential-thinking | Sequential reasoning | mcp-proxy-config | Read | Reasoning chain | Read | docker exec | mcp-proxy-config | No side effects observed |

**Total MCP Servers**: 12
**Read-Only Posture**: 8
**Write-Claimed Posture**: 4 (conport, desktop-commander, task-orchestrator, dope-memory)
**Unknown Write Enforcement**: 4
