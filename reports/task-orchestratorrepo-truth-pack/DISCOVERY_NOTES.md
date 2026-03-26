# DISCOVERY NOTES — Pass 1

## Analysis Identity
- **Repo**: https://github.com/jpicklyk/task-orchestrator
- **Ref**: `99023a9740e3ea310c31c5e80991670aa010fb2f` (HEAD-at-time-of-analysis)
- **Branch**: `main`
- **Version**: 2.2.0
- **Latest Tag**: v2.2.0
- **Timestamp**: 2026-03-06T18:42:14-08:00

---

## 1. MCP Registration — LOCATED

**Authoritative location**: `CurrentMcpServer.kt` lines 89–108

Registration mechanism: `McpToolAdapter.registerToolsWithServer(server, tools, toolContext)` iterates each `ToolDefinition` and calls `server.addTool(name, description, inputSchema)` via the MCP SDK.

**13 tools registered (exact order from code)**:
1. `ManageItemsTool()` → `"manage_items"`
2. `QueryItemsTool()` → `"query_items"`
3. `ManageNotesTool()` → `"manage_notes"`
4. `QueryNotesTool()` → `"query_notes"`
5. `ManageDependenciesTool()` → `"manage_dependencies"`
6. `QueryDependenciesTool()` → `"query_dependencies"`
7. `AdvanceItemTool()` → `"advance_item"`
8. `GetNextStatusTool()` → `"get_next_status"`
9. `GetNextItemTool()` → `"get_next_item"`
10. `GetBlockedItemsTool()` → `"get_blocked_items"`
11. `CompleteTreeTool()` → `"complete_tree"`
12. `CreateWorkTreeTool()` → `"create_work_tree"`
13. `GetContextTool()` → `"get_context"`

**Cross-check**: README claims "13 tools" and lists identical tool names. The `instructions` field in `configureServer()` line 220 lists the same 13 names. **docs say = code does**.

**FAILURE_REPORT.md**: NOT needed. Registration located authoritatively.

---

## 2. Architecture Summary (from code, not docs)

### Layer Structure (traced from entrypoint inward)
```
CurrentMainKt.main()
  └── CurrentMcpServer(version, shutdownCoordinator)
        ├── DatabaseManager.initialize(dbPath)
        ├── DatabaseManager.updateSchema() [Flyway or direct]
        ├── DefaultRepositoryProvider(databaseManager)
        ├── YamlNoteSchemaService()
        ├── ToolExecutionContext(repositoryProvider, noteSchemaService)
        ├── McpToolAdapter.registerToolsWithServer(server, tools, context)
        └── Transport dispatch:
              ├── "stdio" → StdioServerTransport
              └── "http"  → embeddedServer(CIO) + mcpStreamableHttp
```

### Dependency Direction (imports confirm)
```
interfaces/mcp/ → application/tools/ → application/service/ → domain/
                                     → infrastructure/repository/ → domain/
                                     → infrastructure/config/ → domain/
infrastructure/database/ ← used by infrastructure/repository/
```

Clean Architecture confirmed from code imports — domain has zero outward dependencies.

### Transport
- **stdio** (default): `StdioServerTransport` from MCP SDK
- **HTTP**: Ktor CIO server on `MCP_HTTP_HOST:MCP_HTTP_PORT` (default 0.0.0.0:3001), using `mcpStreamableHttp`
- Selected via `MCP_TRANSPORT` env var

### Persistence
- **Backend**: SQLite via Exposed ORM
- **Default path**: `data/current-tasks.db` (overridden by `DATABASE_PATH` env var)
- **Migrations**: Flyway (2 migrations: V1 initial, V2 field updates)
- **WAL mode**: enabled at connection setup
- **Foreign keys**: enabled at connection setup
- **Busy timeout**: 5000ms
- **Isolation**: TRANSACTION_SERIALIZABLE
- **Schema manager**: Flyway by default, direct SQL fallback via `USE_FLYWAY` env var

---

## 3. Domain Model (from code)

### Entities
| Entity         | Table              | PK          | Unique Constraints                 |
| -------------- | ------------------ | ----------- | ---------------------------------- |
| WorkItem       | `work_items`       | `id` (UUID) | none                               |
| Note           | `notes`            | `id` (UUID) | `(work_item_id, key)`              |
| Dependency     | `dependencies`     | `id` (UUID) | `(from_item_id, to_item_id, type)` |
| RoleTransition | `role_transitions` | `id` (UUID) | none                               |

### Enums (from code)
| Enum             | Values                                 |
| ---------------- | -------------------------------------- |
| `Role`           | QUEUE, WORK, REVIEW, BLOCKED, TERMINAL |
| `Priority`       | HIGH, MEDIUM, LOW                      |
| `DependencyType` | BLOCKS, IS_BLOCKED_BY, RELATES_TO      |

### Triggers (from `RoleTransition.VALID_TRIGGERS`)
`start`, `complete`, `block`, `hold`, `resume`, `cancel`

---

## 4. Workflow Logic (from code — `RoleTransitionHandler`)

### Transition Table (code-authoritative)
| From                      | Trigger    | To           | Condition                              |
| ------------------------- | ---------- | ------------ | -------------------------------------- |
| QUEUE                     | start      | WORK         | dependency gate                        |
| WORK                      | start      | REVIEW       | hasReviewPhase=true + dependency gate  |
| WORK                      | start      | TERMINAL     | hasReviewPhase=false + dependency gate |
| REVIEW                    | start      | TERMINAL     | dependency gate                        |
| QUEUE/WORK/REVIEW         | complete   | TERMINAL     | none (force-close)                     |
| QUEUE/WORK/REVIEW         | block/hold | BLOCKED      | none (always allowed)                  |
| BLOCKED                   | resume     | previousRole | previousRole must exist                |
| QUEUE/WORK/REVIEW/BLOCKED | cancel     | TERMINAL     | statusLabel="cancelled"                |
| TERMINAL                  | any        | —            | rejected                               |
| BLOCKED                   | start      | —            | rejected (must resume first)           |
| BLOCKED                   | complete   | —            | rejected (must resume first)           |
| BLOCKED                   | block      | —            | rejected (already blocked)             |

### Gating Logic (from `AdvanceItemTool` + `NoteSchemaService`)
- `advance_item(trigger="start")`: checks note schema gates for the current phase's required notes
- `advance_item(trigger="complete")`: checks ALL required notes across ALL phases
- No schema config → schema-free mode → no gates enforced
- `hasReviewPhase`: determined by whether the matched schema has any `role="review"` entries

### Cascade Logic (from `CascadeDetector`)
- **Completion cascade**: When a child reaches TERMINAL, if ALL siblings are TERMINAL, parent auto-advances to TERMINAL (recursive up ancestor chain)
- **Start cascade**: When a child enters WORK, if parent is QUEUE, parent auto-advances to WORK
- **Unblock detection**: After transition, checks outgoing BLOCKS deps; targets whose ALL incoming blocking deps are satisfied are reported as "unblockedItems"

---

## 5. Config System (from code — `YamlNoteSchemaService`)

- Path: `.taskorchestrator/config.yaml`
- Resolved from: `AGENT_CONFIG_DIR` env var → `user.dir` system property
- Parsed by: SnakeYAML
- Key: `note_schemas.<tag-name>` → list of `NoteSchemaEntry`
- Schema-free mode when: file missing OR no tags match

---

## 6. Environment Variables (from `DatabaseConfig` + `CurrentMcpServer`)

| Variable                   | Default                         | Source                    |
| -------------------------- | ------------------------------- | ------------------------- |
| `DATABASE_PATH`            | `data/current-tasks.db`         | `DatabaseConfig.kt:14`    |
| `USE_FLYWAY`               | `true`                          | `DatabaseConfig.kt:22`    |
| `LOG_LEVEL`                | `INFO`                          | `DatabaseConfig.kt:29`    |
| `AGENT_CONFIG_DIR`         | null (→ `user.dir`)             | `DatabaseConfig.kt:37`    |
| `DATABASE_MAX_CONNECTIONS` | `10`                            | `DatabaseConfig.kt:44`    |
| `DATABASE_SHOW_SQL`        | `false`                         | `DatabaseConfig.kt:51`    |
| `MCP_TRANSPORT`            | `stdio`                         | `CurrentMcpServer.kt:115` |
| `MCP_HTTP_HOST`            | `0.0.0.0`                       | `CurrentMcpServer.kt:164` |
| `MCP_HTTP_PORT`            | `3001`                          | `CurrentMcpServer.kt:165` |
| `MCP_SERVER_NAME`          | `mcp-task-orchestrator-current` | `CurrentMcpServer.kt:83`  |

---

## 7. Docker (from Dockerfile + docker-compose.yml)

- **Builder**: `eclipse-temurin:23-jdk`
- **Runtime**: `amazoncorretto:25-al2023-headless`
- **JVM**: `--enable-native-access=ALL-UNNAMED` (required for SQLite JDBC on Java 25+)
- **Volume**: `/app/data` (SQLite DB persistence)
- **User**: appuser:1001
- **Compose services**: 3 (v2-stdio, v3-stdio, v3-http profile)

---

## 8. Preliminary Drift Notes

| Area                           | Status                                                                                                                                             |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tool count: docs vs code       | **Match** — README says 13, code registers 13                                                                                                      |
| Tool names: docs vs code       | **Match** — Same 13 names                                                                                                                          |
| README claims vs code behavior | **Mostly aligned** — need to verify "hold" trigger in README table (code maps `hold` → same as `block`)                                            |
| Docker default DATABASE_PATH   | **Discrepancy**: Dockerfile `runtime-base` sets `tasks.db`, `runtime-current` overrides to `current-tasks.db`. Code default is `current-tasks.db`. |
| README "1,600+ tests" claim    | Need verification via test count — 35 test files found in `:current`, plus `:clockwork` tests not counted                                          |
| `complexity` default           | V1 migration: `NOT NULL DEFAULT 5`. V2 migration: nullable. Code model: `complexity: Int? = null`. V2 is authoritative.                            |
| `hold` vs `block` trigger      | README lists `hold` not in trigger table but mentions it in text. Code treats `hold` as alias for `block` in `RoleTransitionHandler.kt:85,111`.    |

---

## 9. Pass 1 Verdict

| Criterion                     | Status                                                       |
| ----------------------------- | ------------------------------------------------------------ |
| MCP tool registration located | ✅ Authoritative (`CurrentMcpServer.kt:89-108`)               |
| Tool list confirmed from code | ✅ 13 tools, exact names                                      |
| Schema extraction feasible    | ✅ `parameterSchema` defined inline per tool via `ToolSchema` |
| Workflow logic recoverable    | ✅ `RoleTransitionHandler` is complete and testable           |
| Architecture traceable        | ✅ Clean Architecture, imports confirm layer boundaries       |
| Persistence understood        | ✅ SQLite + Exposed + Flyway                                  |
| Config system understood      | ✅ YAML + env vars, well-documented in code                   |
| Test coverage mappable        | ✅ 35 test files, 1:1 with tools and repos                    |
| FAILURE_REPORT needed         | ❌ Not needed                                                 |

**Pass 1 is clean. Ready for Pass 2 full extraction.**
