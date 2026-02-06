---
id: mcp-scripts-reference
title: Mcp Scripts Reference
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Mcp Scripts Reference (reference) for dopemux documentation and developer
  workflows.
---
# MCP Management Scripts

Quick reference for Dopemux MCP service management.

## Health Monitoring

### `mcp-health-check.py`
**Purpose**: Verify all MCP services and infrastructure are running

**Usage**:
```bash
python3 scripts/mcp-health-check.py
```

**Checks**:
- ✅ All 8 MCP servers (Serena, ConPort, Zen, etc.)
- ✅ Infrastructure (PostgreSQL, Redis, Qdrant)
- ✅ Port availability
- ✅ Endpoint responsiveness

**Output**:
- Color-coded status (✅/❌)
- Port and endpoint status
- Troubleshooting tips

---

## Service Management

### `start-all-mcp.sh`
**Purpose**: Start all Dopemux services with health verification

**Usage**:
```bash
./scripts/start-all-mcp.sh
```

**Actions**:
1. Starts all Docker services (`docker-compose up -d`)
2. Waits 10 seconds for initialization
3. Runs health check
4. Reports status

**When to use**:
- After system restart
- When health check shows services down
- Initial project setup

---

## Configuration Fixes

### `fix-serena-config.py`
**Purpose**: Fix duplicate/incorrect Serena MCP configuration

**Usage**:
```bash
python3 scripts/fix-serena-config.py
```

**Actions**:
- Backs up `~/.claude.json`
- Ensures Serena uses SSE (not stdio)
- Validates configuration

**When to use**:
- Serena connection failures
- After manual config edits
- Migrating from stdio to SSE

---

## Autonomous Indexing

### `enable-autonomous-indexing.py`
**Purpose**: Enable zero-touch code/docs indexing

**Usage**:
```bash
python3 scripts/enable-autonomous-indexing.py
```

**What it does**:
- Starts file watching for code files (*.py,*.ts, *.js)
- Auto-reindexes on file changes (5s debounce)
- Enables autonomous docs indexing (*.md,*.pdf)

**ADHD Benefit**: Never manually reindex again!

### `autonomous-indexing-daemon.py`
**Purpose**: Background daemon for autonomous indexing

**Usage** (typically started by enable script):
```bash
python3 scripts/autonomous-indexing-daemon.py
```

---

## Quick Workflows

### Initial Setup
```bash
# 1. Start all services
./scripts/start-all-mcp.sh

# 2. Enable autonomous indexing
python3 scripts/enable-autonomous-indexing.py

# 3. Restart Claude Code
```

### Daily Health Check
```bash
# Quick status check
python3 scripts/mcp-health-check.py

# If services down, restart them
./scripts/start-all-mcp.sh
```

### Troubleshooting Serena
```bash
# 1. Check health
python3 scripts/mcp-health-check.py

# 2. If config issue, fix it
python3 scripts/fix-serena-config.py

# 3. Restart Claude Code
```

---

## Exit Codes

All scripts follow standard conventions:
- `0` = Success, all healthy
- `1` = Issues found, see output
- `130` = Interrupted (Ctrl+C)

---

## Dependencies

**Python scripts require**:
- Python 3.8+
- Standard library only (no pip installs)

**Shell scripts require**:
- Bash 4.0+
- Docker and docker-compose
- jq (optional, for JSON parsing)

---

## File Locations

```
scripts/
├── mcp-health-check.py          # Health verification
├── start-all-mcp.sh             # Service startup
├── fix-serena-config.py         # Config repair
├── enable-autonomous-indexing.py # Auto-indexing setup
├── autonomous-indexing-daemon.py # Background indexer
└── MCP_SCRIPTS_README.md        # This file
```

---

**Tip**: Add `scripts/` to your PATH for easy access:
```bash
export PATH="$PATH:/Users/hue/code/dopemux-mvp/scripts"
```
