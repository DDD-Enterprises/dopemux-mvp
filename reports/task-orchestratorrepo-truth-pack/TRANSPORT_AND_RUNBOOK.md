# Transport and Runbook

## Transports

### stdio (default)
- **Selection**: `MCP_TRANSPORT=stdio` (default)
- **Implementation**: `StdioServerTransport` from MCP Kotlin SDK
- **Usage**: Docker `run -i` with stdin_open, or local process
- **Graceful shutdown**: SIGTERM → `ShutdownCoordinator` → close transport → `DatabaseManager.shutdown()`

### HTTP
- **Selection**: `MCP_TRANSPORT=http`
- **Implementation**: Ktor CIO embedded server + MCP SDK `mcpStreamableHttp`
- **Host/Port**: `MCP_HTTP_HOST` (default `0.0.0.0`) : `MCP_HTTP_PORT` (default `3001`)
- **Endpoint**: `/mcp` (streamable HTTP transport)
- **Graceful shutdown**: SIGTERM → Ktor server stop → same shutdown path

## Docker Deployment

### Quick Start (stdio)
```bash
docker pull ghcr.io/jpicklyk/task-orchestrator:latest

docker run --rm -i \
  -v mcp-task-data:/app/data \
  ghcr.io/jpicklyk/task-orchestrator:latest
```

### HTTP Mode
```bash
docker run --rm -d \
  -v mcp-task-data:/app/data \
  -e MCP_TRANSPORT=http \
  -e MCP_HTTP_HOST=0.0.0.0 \
  -e MCP_HTTP_PORT=3001 \
  -p 3001:3001 \
  ghcr.io/jpicklyk/task-orchestrator:latest
```

### With Note Schema Config
```bash
docker run --rm -i \
  -v mcp-task-data:/app/data \
  -v /path/to/project/.taskorchestrator:/project/.taskorchestrator:ro \
  -e AGENT_CONFIG_DIR=/project \
  ghcr.io/jpicklyk/task-orchestrator:latest
```

### Per-Project Data Isolation
Change the volume name:
```bash
-v my-project-data:/app/data
```

## Docker Compose Services (from `docker-compose.yml`)

| Service                              | Target            | Transport | Profile        | Port |
| ------------------------------------ | ----------------- | --------- | -------------- | ---- |
| `mcp-task-orchestrator`              | `runtime-v2`      | stdio     | default        | —    |
| `mcp-task-orchestrator-current`      | `runtime-current` | stdio     | `current`      | —    |
| `mcp-task-orchestrator-current-http` | `runtime-current` | HTTP      | `current-http` | 3001 |

### Resource Limits
| Resource | Limit | Reservation |
| -------- | ----- | ----------- |
| Memory   | 512M  | 256M        |
| CPUs     | 1.0   | 0.25        |

## MCP Client Configuration

### Claude Code (CLI)
```bash
claude mcp add-json mcp-task-orchestrator '{
  "command": "docker",
  "args": ["run", "--rm", "-i", "-v", "mcp-task-data:/app/data",
           "ghcr.io/jpicklyk/task-orchestrator:latest"]
}'
```

### Project `.mcp.json`
```json
{
  "mcpServers": {
    "mcp-task-orchestrator": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "mcp-task-data:/app/data",
        "ghcr.io/jpicklyk/task-orchestrator:latest"
      ]
    }
  }
}
```

## Environment Variables Reference

| Variable                   | Default                         | Purpose                   |
| -------------------------- | ------------------------------- | ------------------------- |
| `DATABASE_PATH`            | `data/current-tasks.db`         | SQLite file path          |
| `USE_FLYWAY`               | `true`                          | Use Flyway for migrations |
| `LOG_LEVEL`                | `INFO`                          | Logging verbosity         |
| `AGENT_CONFIG_DIR`         | null → `user.dir`               | Config search root        |
| `DATABASE_MAX_CONNECTIONS` | `10`                            | Connection pool size      |
| `DATABASE_SHOW_SQL`        | `false`                         | Log SQL statements        |
| `MCP_TRANSPORT`            | `stdio`                         | Transport: stdio or http  |
| `MCP_HTTP_HOST`            | `0.0.0.0`                       | HTTP bind host            |
| `MCP_HTTP_PORT`            | `3001`                          | HTTP port                 |
| `MCP_SERVER_NAME`          | `mcp-task-orchestrator-current` | Server identity           |
| `CI_BUILD_NUMBER`          | null                            | Appended to version in CI |

## Database Configuration

| Setting        | Value                         | Source                  |
| -------------- | ----------------------------- | ----------------------- |
| Driver         | `org.sqlite.JDBC`             | `DatabaseManager.kt:63` |
| Journal mode   | `WAL`                         | `DatabaseManager.kt:75` |
| Foreign keys   | `ON`                          | `DatabaseManager.kt:72` |
| Busy timeout   | `5000ms`                      | `DatabaseManager.kt:77` |
| Isolation      | `TRANSACTION_SERIALIZABLE`    | `DatabaseManager.kt:81` |
| Schema manager | Flyway (default) / Direct SQL | `SchemaManagerFactory`  |

## Shutdown Sequence (from `ShutdownCoordinator` + `CurrentMcpServer`)

1. SIGTERM/SIGINT received
2. `ShutdownCoordinator.initiateShutdown()` called
3. MCP server closes transport
4. `DatabaseManager.shutdown()` — closes and unregisters DB connection
5. JVM exits

## Startup Sequence (from `CurrentMcpServer.start()`)

1. Read `MCP_TRANSPORT` env var
2. `DatabaseManager.initialize(databasePath)`
3. `DatabaseManager.updateSchema()` (Flyway or direct)
4. Post-migration `checkParentCycleIntegrity()` (warns, doesn't fail)
5. Create `DefaultRepositoryProvider`
6. Create `YamlNoteSchemaService` (lazy load)
7. Create `ToolExecutionContext`
8. Configure MCP SDK `Server` with name, version, instructions
9. Register 13 tools via `McpToolAdapter`
10. Start transport (stdio or HTTP)

## Troubleshooting

| Symptom                      | Cause                  | Fix                                      |
| ---------------------------- | ---------------------- | ---------------------------------------- |
| "AI can't find tools"        | Server not connected   | Restart client or `/mcp reconnect`       |
| "Schema in progress" error   | SQLite busy            | Increase `PRAGMA busy_timeout`           |
| Note gates blocking          | Missing required notes | `get_context(itemId=...)` to see missing |
| Self-loop warning at startup | Data integrity issue   | Inspect item where `id = parent_id`      |
