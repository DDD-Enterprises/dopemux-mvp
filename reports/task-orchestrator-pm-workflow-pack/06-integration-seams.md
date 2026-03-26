# 06 Integration Seams

## MCP server surfaces (primary external control surface)
- MCP server exposes tools through SDK `Server.addTool` adapter registration. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/McpToolAdapter.kt:46)
- Registered tool set (13) is declared in server bootstrap and includes all write/read PM surfaces. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:89, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:220)
- Transport seam:
  - STDIO (`StdioServerTransport`) for local MCP clients. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:135)
  - HTTP streamable MCP endpoint (`mcpStreamableHttp`) selectable by env. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:115, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:170)

## Configuration/control seams
- Runtime env control seam for persistence and behavior: `DATABASE_PATH`, `USE_FLYWAY`, `MCP_TRANSPORT`, `MCP_HTTP_PORT`, `AGENT_CONFIG_DIR`, `FLYWAY_REPAIR`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseConfig.kt:14, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseConfig.kt:22, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:115, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:165, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/config/YamlNoteSchemaService.kt:86, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/management/FlywayDatabaseSchemaManager.kt:19)
- Note-schema contract seam via `.taskorchestrator/config.yaml` consumed by `YamlNoteSchemaService`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/config/YamlNoteSchemaService.kt:13, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/config/YamlNoteSchemaService.kt:59)

## Container/orchestration seams
- Docker image exposes runtime target(s) and default env vars consumed by app. (Dockerfile:63, Dockerfile:64, Dockerfile:66, Dockerfile:89)
- Compose defines runnable service profiles for v3 stdio/http and legacy v2. (docker-compose.yml:2, docker-compose.yml:36, docker-compose.yml:68)

## Plugin/hook seams (repo-local adjunct)
- Claude plugin package declares skills/hooks/output styles. (claude-plugins/task-orchestrator/.claude-plugin/plugin.json:5, claude-plugins/task-orchestrator/.claude-plugin/plugin.json:6)
- Hook config injects automatic context on session start, plan mode boundaries, and subagent start. (claude-plugins/task-orchestrator/hooks/hooks-config.json:3, claude-plugins/task-orchestrator/hooks/hooks-config.json:15, claude-plugins/task-orchestrator/hooks/hooks-config.json:39)
- Hook content directly instructs clients to use workflow tools (`advance_item`, `get_context`, etc.), shaping external usage discipline. (claude-plugins/task-orchestrator/hooks/session-start.mjs:8, claude-plugins/task-orchestrator/hooks/subagent-start.mjs:12)

## Absent/no evidence found
- No non-MCP REST controller surface found in current implementation scope.
- No webhook/event-bus/export-import API seam found in current implementation scope.
- Negative evidence command results (zero counts) recorded in `99-evidence-index.md`.
