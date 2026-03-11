# ConPort Phase 1 Discovery — Command Log

**Target**: docker/mcp-servers-source/conport/
**Analyzed Ref**: fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2
**Branch**: codex/main-drain-20260306
**Started**: 2026-03-09T21:04:19Z

---

## Commands Executed

| # | Command / Action | Purpose |
|---|------------------|---------|
| 1 | `git rev-parse HEAD` | Confirm analyzed ref = fe48c0a8 |
| 2 | `git branch --show-current` | Confirm branch = codex/main-drain-20260306 |
| 3 | `ls docker/mcp-servers-source/conport/` | Enumerate target directory (20 entries) |
| 4 | `view server.py` (full) | Read MCP FastMCP thin-client surface |
| 5 | `view conport_mcp_stdio.py` (full) | Read stdio-only MCP admin surface |
| 6 | `view enhanced_server.py` (2149 lines, 5 chunks) | Read primary HTTP+JSON-RPC server |
| 7 | `view unified_queries.py` (full) | Read cross-workspace query layer |
| 8 | `view instance_detector.py` (full) | Read worktree instance detector |
| 9 | `view shared_monitoring.py` (full) | Read Prometheus monitoring module |
| 10 | `view shared_monitoring_init.py` (full) | Read monitoring __init__ |
| 11 | `view schema.sql` (full, 291 lines) | Read base PostgreSQL schema |
| 12 | `view schema.sql.bak` (head) | Confirm identical to schema.sql |
| 13 | `view Dockerfile` (full) | Read container build spec |
| 14 | `view direct_server.py` (full) | Read mock/prototype HTTP server |
| 15 | `view info_server.py` (full) | Read service discovery sidecar |
| 16 | `view start_with_info.sh` (full) | Read multi-process entrypoint |
| 17 | `view integration_bridge_client.py` (full) | Read DopeconBridge event client |
| 18 | `view simple_metrics_server.py` (full) | Read standalone metrics server |
| 19 | `cat migrations/*.sql` (all 5 files) | Read all migration SQL |
| 20 | `cat migrations/README.md` | Read migration docs |
| 21 | `cat tests/*.py` + `test_*.py` (all) | Read all test files |
| 22 | `grep conport compose.yml` | Locate compose service definition |
| 23 | `grep conport services/registry.yaml` | Locate registry entries |
| 24 | `grep conport docker-compose.smoke.yml` | Locate smoke stack ref |
| 25 | `grep conport .claude.json` | Locate MCP client config |
| 26 | `grep conport .claude/` | Locate docs/backup refs |
| 27 | `grep INV-MEM, append.only, promote, SSoT, dedup` | Search for invariant/authority patterns in code |
| 28 | `sed -n services/registry.yaml` (lines 78-120) | Read full registry entries for conport-http and conport-mcp |
| 29 | `sed -n compose.yml` (lines 226-260) | Read compose definition for conport service |
