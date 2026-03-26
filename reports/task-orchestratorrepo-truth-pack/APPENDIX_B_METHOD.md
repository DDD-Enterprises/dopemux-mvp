# Appendix B — Method

## Extraction Methodology

### Operating Mode
- **Code-first**: All claims verified against source code before inclusion
- **Evidence-first**: Line-number citations provided for critical assertions
- **Fail-closed**: No guessing; unverifiable claims marked as such
- **Deterministic output**: Stable ordering of fields, sections, and tools

### Pass 1: Discovery
1. Cloned repository, recorded HEAD commit SHA
2. Enumerated all source files (47 main, 35 test)
3. Located MCP tool registration surface (`CurrentMcpServer.kt:89-108`)
4. Inspected all 13 tool definitions (outlines and parametrSchema)
5. Inspected all domain models, services, and infrastructure
6. Produced 5 discovery deliverables: COMMAND_LOG, SEARCH_PATTERNS, INSPECTED_FILES, APPENDIX_A, DISCOVERY_NOTES

### Pass 2: Full Extraction
1. Read all 13 tool implementations in full
2. Extracted parameter schemas from `parameterSchema` code
3. Traced response shapes from `successResponse()`/`errorResponse()` calls
4. Mapped workflow state machine from `RoleTransitionHandler`
5. Documented cascade logic from `CascadeDetector`
6. Extracted data model from Flyway SQL migrations
7. Cross-referenced README/docs against code for drift report
8. Produced 12 deliverables

### Evidence Sources (ordered by priority)
1. Source code (`.kt` files) — authoritative
2. Build files (`build.gradle.kts`, `version.properties`) — authoritative
3. Flyway SQL migrations — authoritative for schema
4. Dockerfile and docker-compose.yml — authoritative for deployment
5. README.md — cross-referenced against code; drift noted
6. Docs (`api-reference.md`, `workflow-guide.md`) — cross-referenced against code

### Tools Used
- `view_file` / `view_file_outline` — code inspection
- `find_by_name` — file enumeration
- `list_dir` — directory structure
- `grep_search` — pattern matching (where needed)
- `run_command` — git metadata

### Non-Actions
- No code was executed (safety constraint)
- No tests were run
- No Docker images were built
- No external API calls were made
