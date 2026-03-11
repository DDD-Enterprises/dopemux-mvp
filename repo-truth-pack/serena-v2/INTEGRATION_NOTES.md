# INTEGRATION_NOTES.md — Serena v2

Analyzed ref: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

## 1. Dopemux Integration Status

### Current State
Serena v2 (`services/serena/`) is a large, feature-rich MCP server that is:
- ✅ Code-complete: 33 MCP tools with full handler implementations
- ✅ ConPort-integrated: Reads decisions, writes progress entries and custom data
- ✅ Multi-workspace aware: 10 of 33 tools support workspace_path/workspace_paths
- ⚠️ Not Docker-deployed: No Dockerfile or compose integration for services/serena/
- ⚠️ Dead code: 4 fully-implemented handlers (F002 session, F1-enhanced) not registered
- ❌ Broken compose reference: compose.yml builds upstream oraios/serena, not this code

### Integration Points

| Integration | Mechanism | Status |
|-------------|-----------|--------|
| ConPort (decisions) | Read via `conport_client_unified.py` | Active |
| ConPort (progress) | Write via `log_progress()` | Active |
| ConPort (custom data) | Read/write via `log_custom_data()` / `get_custom_data()` | Active |
| Redis cache | Navigation cache on db_index=1 | Active |
| ADHD Engine | Dynamic result limits via import | Active (fails silently) |
| Dope-Context | Semantic search via direct import | Active (fails silently) |
| dopecon-bridge | Event consumption via Redis streams | Passive (eventbus_consumer.py) |
| PostgreSQL (intelligence) | asyncpg for learning/graph data | Active (requires separate DB) |
| LSP (pylsp) | Code navigation | Active (with grep fallback) |
| tree-sitter | AST complexity analysis | Active (with line-count fallback) |

## 2. Recommendations

### R1: Fix Docker Deployment (Priority: HIGH)
The `compose.yml` references `./docker/mcp-servers/serena` which doesn't exist and builds the upstream oraios/serena. To deploy the actual services/serena/ code:

1. Create `services/serena/Dockerfile`
2. Create `services/serena/requirements.txt`
3. Update `compose.yml` to build from `services/serena/`
4. Or create a new compose service (e.g., `serena-v2`) alongside the existing one

### R2: Register Dead Handlers (Priority: MEDIUM)
4 complete handler implementations are unreachable. To activate:

1. Add Tool() definitions to `list_tools()` for:
   - `detect_untracked_work_enhanced`
   - `initialize_session`
   - `get_multi_session_dashboard`
   - `get_session_info`
2. Add dispatch branches to `call_tool()`
3. Fix duplicate `except ImportError` in `detect_untracked_work_enhanced_tool`

### R3: Update Tool Count Claims (Priority: LOW)
Update these stale references:
- `mcp_server.py` line 10: "21+" → "33"
- `mcp_server.py` line 5330: "24 tools" → "33 tools"
- `get_workspace_status_tool` response: `total_available: 20` → `33`

### R4: Database Migration Automation (Priority: MEDIUM)
- `intelligence/schema.sql` defines 6 tables but no automatic migration
- Add startup migration check in `_ensure_component("database")`
- Or document manual migration prerequisite

### R5: Version Alignment (Priority: LOW)
Align `__init__.py:__version__` (2.0.0) with PKG-INFO (0.1.0)

## 3. ConPort Authority Model

### Serena's Authority Boundary
Serena is a **consumer and contributor** to the ConPort knowledge graph, NOT an authority:

**Serena READS from ConPort:**
- Decisions (to match untracked work against known tasks)
- Progress entries (to check if work is already tracked)
- Custom data (metrics history, user config)

**Serena WRITES to ConPort:**
- Progress entries (when tracking untracked work)
- Custom data categories:
  - `untracked_work_links` — metadata linking tasks to detected work
  - `metrics_history` — daily metric snapshots (90-day retention)
  - `untracked_work_config` — user configuration
  - `untracked_work_status` — snooze/abandon status

**Serena does NOT write:**
- Decisions (those belong to the operator/supervisor)
- System patterns (those belong to ConPort)
- Active context (that belongs to the workspace session)

### ConPort Integration Links
The intelligence PostgreSQL database (`conport_integration_links` table) stores links between Serena's code elements and ConPort items. These are NOT stored in ConPort itself — they're Serena's internal mapping.

## 4. Multi-Workspace Architecture

10 of 33 tools support multi-workspace via `workspace_path` / `workspace_paths` parameters:

| Tool | Multi-Workspace Support |
|------|------------------------|
| find_symbol | ✅ via SerenaMultiWorkspace |
| get_context | ✅ via SerenaMultiWorkspace |
| find_references | ✅ via SerenaMultiWorkspace |
| analyze_complexity | ✅ via SerenaMultiWorkspace |
| get_reading_order | ✅ via SerenaMultiWorkspace |
| find_relationships | ✅ via SerenaMultiWorkspace |
| get_navigation_patterns | ✅ via SerenaMultiWorkspace |
| find_similar_code | ✅ via SerenaMultiWorkspace |
| find_test_file | ✅ via SerenaMultiWorkspace |
| get_unified_complexity | ✅ via SerenaMultiWorkspace |

Multi-workspace routing: When `workspace_paths` or `workspace_path` is provided, the tool creates a `SerenaMultiWorkspace` instance and delegates to the `*_multi()` method.

## 5. Dependency Matrix

| Dependency | Required | Fallback | Impact if Missing |
|------------|----------|----------|-------------------|
| Python 3.11+ | Yes | None | Server won't start |
| mcp SDK | Yes | None | Server won't start |
| asyncpg | No | Skip intelligence DB | No learning/graph features |
| redis | No | Skip navigation cache | Slower navigation (no cache) |
| ConPort (port 5455) | No | Skip ConPort features | No work tracking, metrics persistence |
| pylsp | No | Grep-based fallback | Slower, less accurate navigation |
| tree-sitter | No | Line-count heuristic | Less accurate complexity analysis |
| ADHD Engine | No | Default limits (10) | No dynamic ADHD adjustment |
| Dope-Context | No | Error response | No semantic search |
| dopecon-bridge | No | No event consumption | No event-driven updates |

## 6. Event-Driven Integration

### Redis Streams (eventbus_consumer.py)
- Consumes events from dopecon-bridge
- `DecisionCache`: Caches decisions for quick lookup
- Passive listener — does not publish events

### File Watcher (file_watcher.py)
- Started at server initialization
- Monitors workspace for file changes
- Can trigger cache invalidation
- Background process, no MCP tool exposure

## 7. Security Considerations

- ConPort password hardcoded as default (`dopemux_age_dev_password`)
- No authentication on MCP stdio transport (standard for local stdio)
- Docker info server has no auth on HTTP endpoints
- ConPort client uses `localhost:5455` — network boundary assumed
- No input sanitization beyond schema validation in tool handlers
