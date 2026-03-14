# 00 Scan Scope and Method

## Scope searched
- Primary implementation scope (authoritative candidate):
  - `current/src/main/kotlin`
  - `current/src/main/resources`
- Runtime/build/config selectors and exposure surfaces:
  - `current/build.gradle.kts`
  - `settings.gradle.kts`
  - `Dockerfile`
  - `docker-compose.yml`
  - `README.md`
- Local variant/legacy risk scope:
  - `clockwork/DEPRECATED.md`
  - `clockwork/src/main/kotlin/Main.kt`
  - `clockwork/build.gradle.kts`
- External-control seam adjunct (repo-local plugin integration files):
  - `claude-plugins/task-orchestrator/.claude-plugin/plugin.json`
  - `claude-plugins/task-orchestrator/hooks/*`

## Commands used
- Repository and file discovery:
  - `ls -la`, `find . -maxdepth ...`, `rg --files`, `wc -l`
- Code and config evidence extraction:
  - `rg -n "..." <paths>`
  - `nl -ba <file> | sed -n '<start>,<end>p'`
- Negative-evidence checks (count-based and zero-hit scans):
  - `rg -n "..." <scope> | wc -l`
  - `rg -n "..." <scope> || true`

## Search terms used
- Workflow/state legality: `Role`, `role`, `statusLabel`, `previousRole`, `resolveTransition`, `validateTransition`, `applyTransition`, `trigger`
- Gates/blocking: `Dependency`, `BLOCKS`, `IS_BLOCKED_BY`, `unblockAt`, `findUnblockedItems`, `get_blocked_items`, `get_next_item`
- Notes/gating: `note_schemas`, `required`, `getSchemaForTags`, `canAdvance`, `missing`
- Audit/history: `RoleTransition`, `role_transitions`, `findSince`, `audit`, `history`, `chronicle`
- Runtime/exposure: `MCP_TRANSPORT`, `MCP_HTTP_PORT`, `USE_FLYWAY`, `DATABASE_PATH`, `AGENT_CONFIG_DIR`, `addTool`, `mcpStreamableHttp`, `StdioServerTransport`
- Variant/split-brain: `clockwork`, `DEPRECATED`, `runtime-v2`, `runtime-current`, `include(":clockwork")`

## File types inspected
- Kotlin source (`.kt`)
- SQL migrations (`.sql`)
- Build/config (`.kts`, `Dockerfile`, `docker-compose.yml`)
- Markdown docs (used as secondary evidence only when code/config did not directly encode a claim)
- Plugin JSON/Node hook scripts (`.json`, `.mjs`)

## Runtime/config selectors inspected
- Server transport selectors and network binding (`MCP_TRANSPORT`, `MCP_HTTP_HOST`, `MCP_HTTP_PORT`) (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:115, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:163, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:165)
- DB path and schema manager mode selectors (`DATABASE_PATH`, `USE_FLYWAY`, `FLYWAY_REPAIR`) (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseConfig.kt:14, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseConfig.kt:22, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/management/FlywayDatabaseSchemaManager.kt:19)
- Config directory selector (`AGENT_CONFIG_DIR`) (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/config/YamlNoteSchemaService.kt:86)
- Module/runtime variant selectors (`:current`, `:clockwork`, `runtime-v2`, `runtime-current`) (settings.gradle.kts:7, settings.gradle.kts:11, Dockerfile:82, Dockerfile:89)

## Negative-evidence method
- For absence claims, searches were run over explicit scopes and recorded with zero counts.
- Example zero-count checks (full details in `99-evidence-index.md`):
  - Decision model symbols in `current/src/main/kotlin` + `current/src/main/resources`: `0`
  - Event-stream/webhook symbols in same scope: `0`
  - Non-MCP REST route symbols in same scope: `0`
  - Import/export tool symbols in `current/.../application/tools`: `0`
  - Decision/event tables in `current/src/main/resources/db/migration`: `0`

## Limitations
- This pass is static/repo-local only; no runtime execution traces were used.
- Legacy `clockwork/` was sampled for variant risk, not exhaustively reverse-engineered.
- Documentation was treated as non-authoritative unless corroborated by code/config/schema.
