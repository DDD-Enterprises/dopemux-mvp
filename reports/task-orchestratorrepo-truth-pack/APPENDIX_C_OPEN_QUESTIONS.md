# Appendix C — Open Questions

## Unresified Items

### 1. Test Count Verification
- **Claim**: README states "1,600+ tests"
- **Status**: `DOCS_CLAIM_UNVERIFIED_FROM_CODE`
- **Reason**: 35 test files found in `:current`. Count includes `:clockwork` tests (not analyzed). Would require `./gradlew test` to verify exact count.
- **Priority**: Low — does not affect integration decisions

### 2. Claude Code Plugin Source
- **Claim**: README references a plugin with 7 skills, 3 hooks, and an output style
- **Status**: `DOCS_CLAIM_PARTIALLY_VERIFIED`
- **Reason**: Plugin installation uses `https://github.com/jpicklyk/task-orchestrator` as marketplace source. Plugin files (YAML skill definitions, hooks, output style) were not inspected in this extraction — they are outside the `:current` module scope.
- **Priority**: Medium — relevant for full integration if plugin is adopted

### 3. `:clockwork` Module Analysis
- **Status**: Not analyzed
- **Reason**: Deprecated module (v2). Extraction focused on active `:current` (v3) module.
- **Priority**: Low — deprecated, not recommended for new integration

### 4. HTTP Transport Security
- **Observation**: HTTP transport binds to `0.0.0.0:3001` with no authentication layer visible in code
- **Status**: `CODE_VERIFIED_NO_AUTH`
- **Implication**: If exposed on a network, any client can call MCP tools. Suitable for localhost/Docker-internal-only deployment without additional security.
- **Priority**: Medium — relevant for network deployment scenarios

### 5. SQLite Concurrency Under Load
- **Observation**: WAL mode + TRANSACTION_SERIALIZABLE + busy_timeout=5000ms
- **Status**: `CODE_VERIFIED`
- **Question**: How does this perform under concurrent multi-agent access via HTTP transport?
- **Priority**: Low — relevant only for multi-process HTTP deployment

### 6. Response Schema Documentation
- **Observation**: Full response shapes are defined in tool `description` strings but not in machine-readable schema format
- **Status**: `CODE_VERIFIED`
- **Implication**: Response schemas must be inferred from description text and `successResponse()` calls in each tool. No `outputSchema` is registered via MCP SDK.
- **Priority**: Medium — relevant for contract validation tooling
