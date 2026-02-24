This repository is governed by .claude/PROJECT_INSTRUCTIONS.md.
Investigations and redesigns must follow .claude/PRIMER.md

# Dopemux-MVP AI Agent Guide

This document helps AI assistants quickly orient themselves to the dopemux-mvp codebase.

## Quick Stats
- **Root Files**: 4 essential docs (README, INSTALL, QUICK_START, CHANGELOG) + 2 Python scripts
- **Services**: 51 services in `services/`
- **Documentation**: Organized Diátaxis structure in `docs/`
- **Core Package**: `src/dopemux/`

## Repository Structure

```
dopemux-mvp/
├── README.md               # Main project overview
├── QUICK_START.md          # Fast onboarding guide
├── INSTALL.md              # Installation instructions
├── CHANGELOG.md            # Version history
│
├── docs/                   # All documentation (Diátaxis structure)
│   ├── docs_index.yaml     # Machine-readable doc index
│   ├── 00-MASTER-INDEX.md  # Human-readable navigation
│   ├── 01-tutorials/       # Learning-oriented guides
│   ├── 02-how-to/          # Problem-solving guides
│   ├── 03-reference/       # Technical specifications
│   ├── 04-explanation/     # Understanding-oriented docs
│   ├── 90-adr/             # Architecture Decision Records
│   ├── 91-rfc/             # Request for Comments
│   ├── archive/            # Historical documents
│   └── systems/            # Component-specific doc hubs
│
├── src/                    # Core dopemux Python package
│   └── dopemux/
│       ├── __init__.py
│       ├── cli.py
│       ├── event_bus.py
│       ├── mcp/            # MCP tooling
│       └── utils/          # Utility modules
│
├── services/               # Microservices (51 services)
│   ├── registry.yaml       # Service registry (ports, health endpoints)
│   ├── task-orchestrator/  # ADHD-aware task coordination
│   ├── dopecon-bridge/     # Event routing layer
│   ├── orchestrator/       # Tmux layout management
│   ├── adhd_engine/        # Serena - ADHD accommodations
│   └── conport/            # Knowledge graph (in docker/)
│
├── docker/                 # Docker services and compose files
│   ├── mcp-servers/        # MCP server containers
│   │   ├── conport/        # Knowledge graph MCP
│   │   ├── zen/            # Code analysis MCP
│   │   └── ...
│   └── docker-compose.*.yml
│
├── scripts/                # Operational and automation scripts
│   ├── docs_validator.py   # Validate doc frontmatter
│   ├── docs_normalize.py   # Normalize doc filenames
│   └── docs_audit/         # Documentation auditing
│
├── config/                 # Configuration files
│   ├── profiles/           # ADHD profiles
│   ├── mcp/                # MCP configurations
│   └── routing/            # Event routing
│
├── tests/                  # Test suites
├── .claude/                # Claude AI configuration
└── pyproject.toml          # Python project metadata
```

## Key Entry Points

### For Understanding the Project
1. [`README.md`](file:///Users/hue/code/dopemux-mvp/README.md) - Start here
2. [`docs/00-MASTER-INDEX.md`](file:///Users/hue/code/dopemux-mvp/docs/00-MASTER-INDEX.md) - Documentation navigation
3. [`docs/docs_index.yaml`](file:///Users/hue/code/dopemux-mvp/docs/docs_index.yaml) - Machine-readable doc index
4. [`services/registry.yaml`](file:///Users/hue/code/dopemux-mvp/services/registry.yaml) - Service registry

### For Development
- **Services**: Browse `services/` - each has README.md
- **Core Library**: `src/dopemux/` - main Python package
- **Docker Services**: `docker/mcp-servers/` - containerized MCP servers
- **Tests**: `tests/` - pytest test suites

### For Documentation
- **User Guides**: `docs/01-tutorials/` and `docs/02-how-to/`
- **API Reference**: `docs/03-reference/`
- **Architecture**: `docs/04-explanation/architecture/` and `docs/94-architecture/`
- **Historical**: `docs/archive/` - completed projects, session notes

## Common Tasks

### Building and Running

```bash
# Install dependencies
pip install -e .

# Run full stack (canonical entrypoint)
docker compose up -d

# Check services
docker compose ps

# Run tests
pytest tests/
```

### Service Information

All services are registered in [`services/registry.yaml`](file:///Users/hue/code/dopemux-mvp/services/registry.yaml) with:
- Port mappings
- Health check endpoints
- Docker Compose service names
- Categories (infrastructure, mcp, coordination, cognitive)

**Key Services:**
- **conport** (3004): Knowledge graph and context management
- **dopecon-bridge** (3016): Event routing and coordination
- **task-orchestrator** (8000): ADHD-aware task management
- **adhd-engine** (8095): Real-time ADHD accommodations (Serena)

### Documentation Validation

```bash
# Validate all docs have proper frontmatter
python scripts/docs_validator.py

# Auto-fix frontmatter issues
python scripts/docs_frontmatter_guard.py --fix

# Normalize doc filenames
python scripts/docs_normalize.py --apply
```

## Testing Strategy

- **Unit Tests**: `tests/` - pytest with coverage
- **Integration Tests**: `test-integration/`
- **Smoke Stack**: `docker-compose.smoke.yml` - core services health check
- **Service Registry**: Used for health monitoring

## Architecture Highlights

### Three-Layer Integration Pattern
1. **Infrastructure Layer**: postgres, redis, qdrant
2. **MCP Layer**: conport, zen, dope-context
3. **Coordination/Cognitive Layer**: dopecon-bridge, task-orchestrator, adhd-engine

See [ADR-207](file:///Users/hue/code/dopemux-mvp/docs/90-adr/ADR-207-architecture-3.0-three-layer-integration.md) for details.

### Event-Driven Coordination
- **Event Bus**: `src/dopemux/event_bus.py`
- **Bridge**: `services/dopecon-bridge/` routes events between services
- **MCP Events**: Captured and routed through dopecon-bridge

## Important Patterns

### Documentation
- **Frontmatter Required**: All docs must have YAML frontmatter
- **Diátaxis Structure**: tutorials, how-to, reference, explanation
- **Archive Policy**: Historical docs in `docs/archive/`, not deleted

### Service Development
- **Service Registry**: Register all services in `services/registry.yaml`
- **Health Endpoints**: All HTTP services must have `/health` endpoint
- **Docker First**: Services should be containerizable
- **Port Management**: Coordinated via registry.yaml

### Configuration
- **Profiles**: ADHD profiles in `config/profiles/`
- **Environment**: `.env.example` for reference, actual secrets in `.env`
- **MCP Servers**: Configured in `.claude.json`

### File Placement (Enforced)
- **Policy File**: `config/repo_hygiene/root_hygiene_policy.json`
- **Guard Script**: `scripts/check_root_hygiene.py`
- **CI/Pre-commit Gate**: New root entries must pass the root hygiene check

Put files in these locations:
- **Product code** (`*.py`, service code): `src/` or `services/<service>/`
- **Reusable automation scripts** (`*.py`, `*.sh`, `*.rb`): `scripts/`
- **Long-lived documentation** (`*.md`): `docs/` (or `docs/05-audit-reports/` for durable audit reports)
- **Generated machine output** (`*.json`, `*.xml`, `*.zip`): `reports/`
- **Runtime logs** (`*.log`): `logs/`
- **Temporary scratch files**: `tmp/`
- **Quarantined uncertain files**: `quarantine/`

Root-level files are allowlisted. If a new root file or top-level directory is truly intentional, update `config/repo_hygiene/root_hygiene_policy.json` in the same change.

## Planes

Specialized investigation and redesign workflows for subsystems.

- **PM Plane**: `docs/planes/pm/HUB.md` (kickoff prompt: `docs/planes/pm/SUPERVISOR.md`)

## Searching the Codebase

### Find Documentation
```bash
# All docs are in docs/ - use docs_index.yaml as reference
cat docs/docs_index.yaml

# Search docs
grep -r "search term" docs/
```

### Find Code
```bash
# Core library
grep -r "pattern" src/dopemux/

# Specific service
grep -r "pattern" services/task-orchestrator/

# All services
grep -r "pattern" services/
```

## MCP Server Configuration

MCP servers are configured in `.claude.json`. Active servers:
- **zen**: Code analysis MCP (stdio)
- **conport**: Knowledge graph MCP (SSE at localhost:3004)
- **task-orchestrator**: Task management MCP (stdio)
- **gpt-researcher**: Research MCP (Docker)
- **exa**: Neural search MCP (Docker)

## Next Steps for AI Assistants

1. **New to the Project?** Read [`README.md`](file:///Users/hue/code/dopemux-mvp/README.md) and [`QUICK_START.md`](file:///Users/hue/code/dopemux-mvp/QUICK_START.md)
2. **Working on Docs?** Check [`docs/docs_index.yaml`](file:///Users/hue/code/dopemux-mvp/docs/docs_index.yaml) for structure
3. **Working on Services?** Review [`services/registry.yaml`](file:///Users/hue/code/dopemux-mvp/services/registry.yaml) for service layout
4. **Need Architecture Context?** Start with [`docs/04-explanation/architecture/`](file:///Users/hue/code/dopemux-mvp/docs/04-explanation/architecture/)

---

**Last Updated**: 2026-02-01  
**Maintainer**: Repository restructure completed

---

## dopeTask Rails (Repo Identity)
This repo includes dopeTask-style identity rails:

- `.dopetaskroot` (repo marker)
- `.dopetask/project.json` (repo identity, packet header requirement)

Any task-packet-driven automation should validate identity before executing.
