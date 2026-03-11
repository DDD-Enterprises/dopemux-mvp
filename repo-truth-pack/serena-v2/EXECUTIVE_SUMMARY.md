# EXECUTIVE_SUMMARY.md — Serena v2 Truth Pack

**Analyzed ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Branch**: `codex/main-drain-20260306`
**Date**: Phase 2 extraction
**Target**: `services/serena/` within `<REPO_ROOT>`

## What Is Serena v2?

Serena v2 is an ADHD-optimized code intelligence system implemented as an MCP server. It provides 33 tools across 4 tiers (navigation, ADHD intelligence, advanced, utility) over a stdio transport, backed by PostgreSQL for code graph intelligence, Redis for navigation caching, and ConPort for state persistence. It comprises ~54K lines of Python across 122 files including a 27-module intelligence engine.

## Key Findings

### Tool Surface
- **33 MCP tools** registered and dispatched (not the 21+ or 24 claimed in code comments/logs)
- **4 dead handler methods** exist with complete implementations but no registration:
  - `detect_untracked_work_enhanced_tool` (F1 enhancements E1-E4)
  - `initialize_session_tool` (F002 multi-session)
  - `get_multi_session_dashboard_tool` (F002)
  - `get_session_info_tool` (F002)
- **10 of 33 tools** support multi-workspace queries
- **8 tools** integrate with ConPort for persistent state

### Architecture
- **Entry point**: `mcp_server.py` (5,378 lines), `SerenaV2MCPServer` class
- **Transport**: stdio primary (via `mcp.server.stdio.stdio_server()`)
- **Intelligence engine**: 27 modules (~27K lines) for adaptive learning, pattern recognition, effectiveness tracking, cognitive load management
- **Lazy loading**: Components load on first use (database, LSP, tree-sitter, ConPort, Redis cache, ADHD features)
- **Fallback strategy**: Every tool has degraded-mode operation (LSP → grep, tree-sitter → line counting, ConPort → defaults, Redis → no cache)

### Critical Architectural Issue: Dual Codebase
**`services/serena/`** (this analysis): 54K lines, 33 tools, intelligence engine, ConPort integration
**`docker/mcp-servers-source/serena/`**: 135-line wrapper around upstream `pip install git+https://github.com/oraios/serena.git@f561204840eb4a96c6956d5cd98712f8ed52d0cb`

The `compose.yml` builds from the Docker wrapper (upstream code), NOT from `services/serena/`. There is **no Docker deployment path** for the 33-tool dopemux Serena implementation. This is the most significant architectural finding.

### Data Model
| Store | Type | Purpose |
|-------|------|---------|
| PostgreSQL (intelligence) | 6 tables | Code elements, relationships, navigation patterns, learning profiles, strategies, ConPort links |
| PostgreSQL (ConPort) | Remote | Decisions (read), progress entries (write), custom data (read/write) |
| Redis (db_index=1) | Ephemeral cache | Navigation results, focus state, session tracking |
| In-memory | Process lifetime | Focus mode, component state, pattern cache |

### Drift Summary
- Tool count: 33 actual vs 20-24 claimed (documentation lag)
- Dead code: 4 complete handlers (F002 + F1-enhanced) not wired
- Dual codebase: compose.yml deploys upstream, not dopemux code
- Version: `2.0.0` (module) vs `0.1.0` (PKG-INFO)
- Compose path: `./docker/mcp-servers/serena` referenced but doesn't exist

## Truth Pack Contents

| Artifact | Purpose |
|----------|---------|
| `REPO_IDENTITY.md` | Package identity, versions, source statistics |
| `TOOL_MANIFEST.json` | All 33 tools + 4 dead handlers with schemas |
| `CONTRACT_SCHEMAS/` | JSON Schema Draft 2020-12 per tool (33 files) |
| `ARCHITECTURE_AND_INTENDED_USES.md` | System architecture, intelligence engine, integration model |
| `WORKFLOW_AND_GATES.md` | Session lifecycle, ADHD flow, cognitive load, gates |
| `DATA_MODEL.md` | PostgreSQL schema, Redis cache, ConPort operations, in-memory state |
| `TRANSPORT_AND_RUNBOOK.md` | Transport details, startup commands, env vars, health checks |
| `DRIFT_REPORT.md` | All discrepancies between docs/comments and actual code |
| `INTEGRATION_NOTES.md` | Dopemux integration status, recommendations, authority model |
| `EXECUTIVE_SUMMARY.md` | This file |

## Recommendations (Priority Order)

1. **HIGH: Fix Docker deployment** — Create Dockerfile for `services/serena/`, update compose.yml
2. **MEDIUM: Register dead handlers** — Wire F002 session tools and F1-enhanced detection
3. **MEDIUM: Database migration** — Add automatic schema migration at startup
4. **LOW: Update tool counts** — Fix stale docstrings and log output
5. **LOW: Version alignment** — Reconcile `2.0.0` vs `0.1.0`

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Tool count (33) | HIGH | Verified against both list_tools and call_tool |
| Dead handlers (4) | HIGH | Verified not in dispatch chain |
| Input schemas | HIGH | Extracted from Tool() definitions |
| Response shapes | MEDIUM | Extracted from handler code, not runtime tested |
| Intelligence engine modules | MEDIUM | Listed from imports, not all may be actively used |
| ConPort authority boundary | HIGH | Verified from read/write method calls |
| Dual codebase divergence | HIGH | Verified from compose.yml and Dockerfile |
| Database schema | HIGH | Extracted from schema.sql verbatim |
