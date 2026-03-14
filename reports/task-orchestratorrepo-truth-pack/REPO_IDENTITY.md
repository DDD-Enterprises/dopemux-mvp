# Repository Identity

## Coordinates
| Field              | Value                                         | Source                            |
| ------------------ | --------------------------------------------- | --------------------------------- |
| **GitHub URL**     | https://github.com/jpicklyk/task-orchestrator | repo origin                       |
| **Default Branch** | `main`                                        | `git rev-parse --abbrev-ref HEAD` |
| **Analyzed Ref**   | `99023a9740e3ea310c31c5e80991670aa010fb2f`    | `git log -1`                      |
| **Ref Label**      | HEAD-at-time-of-analysis                      | policy                            |
| **Version**        | 2.2.0                                         | `version.properties`              |
| **Latest Tag**     | v2.2.0                                        | `git tag --sort=-creatordate`     |
| **License**        | MIT                                           | `LICENSE` file                    |

## Build System
| Field              | Value                    | Source                             |
| ------------------ | ------------------------ | ---------------------------------- |
| **Build Tool**     | Gradle (Kotlin DSL)      | `build.gradle.kts`                 |
| **Gradle Wrapper** | distributed in `gradle/` | `gradlew`                          |
| **Group**          | `io.github.jpicklyk`     | root `build.gradle.kts`            |
| **JVM Toolchain**  | 21                       | `current/build.gradle.kts`         |
| **Kotlin Version** | 2.2.0                    | README (confirmed by build plugin) |

## Modules
| Module    | Gradle Path  | Status     | Description                           |
| --------- | ------------ | ---------- | ------------------------------------- |
| current   | `:current`   | **Active** | v3 MCP Task Orchestrator              |
| clockwork | `:clockwork` | Deprecated | v2, archived, not built by default CI |

## Dependencies (`:current` module, from `build.gradle.kts`)
| Dependency                                         | Version  | Purpose            |
| -------------------------------------------------- | -------- | ------------------ |
| `io.modelcontextprotocol:kotlin-sdk`               | 0.8.4    | MCP protocol       |
| `org.jetbrains.kotlinx:kotlinx-coroutines-core`    | 1.10.2   | Async              |
| `org.jetbrains.exposed:exposed-*`                  | 0.61.0   | SQLite ORM         |
| `org.xerial:sqlite-jdbc`                           | 3.49.1.0 | SQLite JDBC driver |
| `org.flywaydb:flyway-core`                         | 11.4.0   | Schema migrations  |
| `io.ktor:ktor-server-cio`                          | 3.1.3    | HTTP transport     |
| `org.slf4j:slf4j-api`                              | 2.0.x    | Logging facade     |
| `ch.qos.logback:logback-classic`                   | —        | Logging impl       |
| `org.jetbrains.kotlinx:kotlinx-serialization-json` | —        | JSON               |
| `org.yaml:snakeyaml`                               | 2.4      | YAML config        |

## Runtime Entrypoints
| Entrypoint | Class                                              | Method    | Source                |
| ---------- | -------------------------------------------------- | --------- | --------------------- |
| JVM main   | `io.github.jpicklyk.mcptask.current.CurrentMainKt` | `main()`  | `CurrentMain.kt`      |
| MCP Server | `CurrentMcpServer`                                 | `start()` | `CurrentMcpServer.kt` |

## Docker
| Field               | Value                                       | Source          |
| ------------------- | ------------------------------------------- | --------------- |
| **Builder Image**   | `eclipse-temurin:23-jdk`                    | `Dockerfile:6`  |
| **Runtime Image**   | `amazoncorretto:25-al2023-headless`         | `Dockerfile:36` |
| **Published Image** | `ghcr.io/jpicklyk/task-orchestrator:latest` | README          |
| **Default Target**  | `runtime-current`                           | `Dockerfile:90` |
| **Exposed Port**    | 3001 (HTTP transport)                       | `Dockerfile:70` |
| **Volume**          | `/app/data` (SQLite DB)                     | `Dockerfile:60` |
| **User**            | `appuser:1001`                              | `Dockerfile:56` |
| **Stop Signal**     | SIGTERM                                     | `Dockerfile:76` |

## Environment Variables
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
| `CI_BUILD_NUMBER`          | null                            | `CurrentMcpServer.kt:77`  |

## Transports
| Transport           | Implementation                   | Selection             |
| ------------------- | -------------------------------- | --------------------- |
| **stdio** (default) | `StdioServerTransport` (MCP SDK) | `MCP_TRANSPORT=stdio` |
| **HTTP**            | Ktor CIO + `mcpStreamableHttp`   | `MCP_TRANSPORT=http`  |
