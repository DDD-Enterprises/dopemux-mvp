# Dopemux Scripts

Operational and automation scripts organized by category for easy discovery.

## Quick Start (Root Level)

Essential entry point scripts:

- [`quickstart.sh`](file:///Users/hue/code/dopemux-mvp/scripts/quickstart.sh) - Fast start for development
- [`setup.sh`](file:///Users/hue/code/dopemux-mvp/scripts/setup.sh) - Initial system setup  
- [`install.py`](file:///Users/hue/code/dopemux-mvp/scripts/install.py) - Dependency installation

---

## Script Categories

### 📦 Deployment & Stack Management ([`deployment/`](file:///Users/hue/code/dopemux-mvp/scripts/deployment/))

Start, stop, and manage service stacks:

- `deploy-conport-kg.sh` - Deploy ConPort knowledge graph
- `deploy_serena_*.py` - Deploy Serena ADHD engine layers
- `launch-dopemux-*.sh` - Launch Dopemux variants
- `start-*.sh` / `stop-all.sh` - Service lifecycle
- `stack_*.sh` - Docker stack management

### 🔍 Indexing & Knowledge Graph ([`indexing/`](file:///Users/hue/code/dopemux-mvp/scripts/indexing/))

Code and documentation indexing:

- `index_codebase.py` - Index source code
- `index_docs.py` - Index documentation
- `autonomous-indexing-daemon.py` - Background indexing daemon
- `auto-sync-indexing.sh` - Auto-sync indexing
- See [`INDEXING_THE_TRUTH.md`](file:///Users/hue/code/dopemux-mvp/scripts/indexing/INDEXING_THE_TRUTH.md) for details

### ⚙️ Setup & Installation ([`setup/`](file:///Users/hue/code/dopemux-mvp/scripts/setup/))

System initialization and configuration:

- `setup-terminal-env.sh` - Terminal environment setup
- `install-mcp-servers.sh` - Install MCP servers
- `init-adhd-profile.sh` - Initialize ADHD profile
- `setup_production_monitoring.py` - Production monitoring setup
- `shell_integration.sh` - Shell integration hooks

### ✅ Testing & Validation ([`testing/`](file:///Users/hue/code/dopemux-mvp/scripts/testing/))

Integration tests and validation:

- `simple_integration_test.py` - Basic integration test
- `validate_production_targets.py` - Production readiness checks
- `verify_adhd_engine_integration.py` - ADHD engine validation
- `run_system_integration_validation.py` - Full system validation
- `test-workspace-events.py` - Workspace event testing

### 📊 Monitoring & Health ([`monitoring/`](file:///Users/hue/code/dopemux-mvp/scripts/monitoring/))

System monitoring and healthchecks:

- `mcp-health-check.py` - MCP service health
- `health-check-kg.sh` - Knowledge graph health
- `production_tracker.sh` - Production metrics
- `performance_profile.py` - Performance profiling
- `adhd-activity-logger.sh` - Activity logging

### 🔌 MCP Services ([`mcp/`](file:///Users/hue/code/dopemux-mvp/scripts/mcp/))

MCP server management and configuration:

- `manage-mcp-servers.sh` - MCP lifecycle management
- `metamcp_server.py` - MetaMCP broker server
- `wire_claude_mcp.py` - Wire Claude to MCP
- `check-mcp-updates.py` - Check for MCP updates
- See [`MCP_SCRIPTS_README.md`](file:///Users/hue/code/dopemux-mvp/scripts/mcp/MCP_SCRIPTS_README.md)

### ⏹️ TMUX & Dashboards ([`tmux/`](file:///Users/hue/code/dopemux-mvp/scripts/tmux/))

Terminal multiplexing and dashboard scripts:

- `orchestrator_dashboard.py` - Orchestrator dashboard
- `pm-dashboard.sh` - Project management dashboard
- `tmux_dopemux_dashboard.sh` - Main dopemux dashboard
- `set-profile.sh` - Profile switching
- `demo_serena_v2.py` - Serena demo

### 💾 Backup & Restore ([`backup/`](file:///Users/hue/code/dopemux-mvp/scripts/backup/))

Data backup and migration:

- `backup-conport-kg.sh` - Backup ConPort KG
- `restore-conport-kg.sh` - Restore ConPort KG
- `prepare_claude_migration.sh` - Migration preparation
- `migrate-docs-architecture.sh` - Documentation migration

### 🛠️ Utilities ([`utilities/`](file:///Users/hue/code/dopemux-mvp/scripts/utilities/))

General-purpose utilities:

- `slash_commands.py` - CLI slash commands
- `session_formatter.py` - Session formatting
- `adr_cleanup.py` - ADR cleanup
- `orphan_cleanup.py` - Orphan file cleanup
- `render_workspace_configs.py` - Workspace config rendering

### 📝 Documentation ([`docs_audit/`](file:///Users/hue/code/dopemux-mvp/scripts/docs_audit/))

Documentation automation and validation:

- [`docs_validator.py`](file:///Users/hue/code/dopemux-mvp/scripts/docs_validator.py) - Validate doc frontmatter (at root)
- [`docs_normalize.py`](file:///Users/hue/code/dopemux-mvp/scripts/docs_normalize.py) - Normalize doc filenames (at root)
- [`docs_frontmatter_guard.py`](file:///Users/hue/code/dopemux-mvp/scripts/docs_frontmatter_guard.py) - Ensure frontmatter (at root)
- `docs_audit/audit_docs.py` - Full documentation audit

### 💾 Database ([`sql/`](file:///Users/hue/code/dopemux-mvp/scripts/sql/) | [`migration/`](file:///Users/hue/code/dopemux-mvp/scripts/migration/))

SQL queries and database migrations:

- `sql/` - SQL query scripts
- `migration/` - Database migration scripts (27 files)

### 🔗 Other Organized Categories

- [`git-hooks/`](file:///Users/hue/code/dopemux-mvp/scripts/git-hooks/) - Git automation hooks
- [`mcp-wrappers/`](file:///Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/) - MCP service wrappers
- [`conport/`](file:///Users/hue/code/dopemux-mvp/scripts/conport/) - ConPort-specific scripts
- [`memory/`](file:///Users/hue/code/dopemux-mvp/scripts/memory/) - Memory management
- [`helpers/`](file:///Users/hue/code/dopemux-mvp/scripts/helpers/) - Helper utilities
- [`ui/`](file:///Users/hue/code/dopemux-mvp/scripts/ui/) - UI components
- [`neon_dashboard/`](file:///Users/hue/code/dopemux-mvp/scripts/neon_dashboard/) - Dashboard components (23 files)
- [`test_data/`](file:///Users/hue/code/dopemux-mvp/scripts/test_data/) - Test fixtures
- [`benchmarks/`](file:///Users/hue/code/dopemux-mvp/scripts/benchmarks/) - Performance benchmarks
- [`auto-start/`](file:///Users/hue/code/dopemux-mvp/scripts/auto-start/) - Auto-start scripts
- [`gpt-researcher/`](file:///Users/hue/code/dopemux-mvp/scripts/gpt-researcher/) - GPT Researcher integration

---

## Usage Patterns

### Common Workflows

**Full System Start:**
```bash
./scripts/quickstart.sh
```

**Deploy Services:**
```bash
./scripts/deployment/stack_up_all.sh
```

**Run Integration Tests:**
```bash
python scripts/testing/simple_integration_test.py
```

**Monitor System:**
```bash
python scripts/monitoring/mcp-health-check.py
```

**Backup Knowledge Graph:**
```bash
./scripts/backup/backup-conport-kg.sh
```

---

## Organization Principles

1. **Root level**: Only essential entry points (3 scripts)
2. **Categories**: Logical grouping by function
3. **README files**: Each major category has its own README
4. **Naming**: Descriptive with category prefix
5. **Documentation**: Inline comments and separate guides

---

## Contributing

When adding new scripts:

1. Place in appropriate category directory
2. Use descriptive naming: `{category}_{action}_{target}.{ext}`
3. Add executable permissions: `chmod +x script.sh`
4. Document in category README
5. Update this main README if creating new categories

---

**Total Scripts**: 205+ across all categories  
**Organization**: 26 subdirectories, 10 root-level files  
**Last Updated**: 2026-02-01
