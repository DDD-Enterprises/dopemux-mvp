This repository is governed by .claude/PROJECT_INSTRUCTIONS.md.
Investigations and redesigns must follow .claude/PRIMER.md

# Dopemux Copilot Instructions (Repository Policy)

These instructions apply to all GitHub Copilot contributions in this repository.
Goal: produce deterministic, auditable changes that match Dopemux architecture and operator workflow.

## Quick Reference

### Build, Test, and Lint Commands

```bash
# Install dependencies
pip install -e .              # Production mode
pip install -e .[dev]         # Development mode with dev dependencies

# Testing
pytest tests/                 # All tests
pytest tests/ -m unit         # Unit tests only
pytest tests/ -m integration  # Integration tests only
pytest tests/ -m "not slow"   # Skip slow tests (fast feedback)
pytest tests/specific_test.py # Single test file
pytest tests/specific_test.py::test_name  # Single test

# Test coverage
pytest --cov=src/dopemux --cov-report=term-missing

# Quality checks
make lint                     # Run flake8
make format                   # Format with black + isort
make type-check               # Run mypy
make quality                  # All quality checks

# Docker stacks
docker-compose -f docker-compose.smoke.yml up    # Core services only
docker-compose -f docker-compose.master.yml up   # Full stack
docker compose config         # Validate compose file syntax

# Documentation validation
python scripts/docs_validator.py              # Validate frontmatter
python scripts/docs_frontmatter_guard.py --fix  # Auto-fix frontmatter
python scripts/docs_normalize.py --apply      # Normalize filenames
```

### Service Registry and Ports

All services are registered in `services/registry.yaml` with their ports and health endpoints:

- **postgres** (5432): PostgreSQL with AGE extension
- **redis** (6379): Caching and event streaming
- **qdrant** (6333): Vector database
- **dope-query** (3004): Knowledge graph MCP (formerly ConPort)
- **dopecon-bridge** (3016): Event routing and coordination
- **task-orchestrator** (8000): ADHD-aware task management
- **adhd-engine** (8095): Real-time ADHD accommodations (Serena)
- **dope-memory** (3020): Temporal chronicle and working-context

### Multi-Workspace Architecture

Dopemux supports isolated workspaces per project. All cognitive state, knowledge graphs, and sessions are scoped by `workspace_id` and `instance_id`. Environment variables:

- `DEFAULT_WORKSPACE_PATH`: Default workspace path
- `WORKSPACE_PATHS`: Comma-separated workspace paths for cross-workspace queries
- `ENABLE_WORKSPACE_ISOLATION=true`: Isolate data per workspace
- `ENABLE_CROSS_WORKSPACE_QUERIES=true`: Allow cross-workspace queries

## 0) Non-negotiables

1) Task packets are law
- If a TASK_PACKET.md (or equivalent) exists in the current work context, follow it exactly.
- If there is a conflict between these instructions and a task packet, the task packet wins.

2) No fabrication
- Do not invent files, functions, endpoints, tables, environment variables, ports, or behaviors.
- If something is unknown, say "UNKNOWN" and point to the specific file you need to inspect.

3) Smallest correct change
- Prefer minimal diffs and targeted fixes.
- Avoid refactors unless explicitly requested or required for correctness.

4) Deterministic behavior
- Defaults must be explicit.
- Avoid time-based randomness unless required and feature-flagged.

5) Evidence required
- For non-trivial behavior changes, include:
  - Where it is implemented (file + function)
  - How to test it (exact command)
  - What success looks like (expected output or condition)

## 1) Repository orientation

Dopemux is a multi-service developer workflow system with:
- A CLI/operator loop (start, worktree, instance management)
- Docker stacks (main, smoke, MCP servers, optional services like Leantime)
- Memory systems (DopeContext, ConPort, ConPort-KG, Dope-Memory)
- MCP servers providing tools/resources to LLM clients

General folders you will see:
- `services/` - service implementations
- `docker/` - compose files, stack scripts, and container configs
- `.dopemux/` - instance env, state, runtime artifacts
- `scripts/` - operational scripts

Before changing architecture or wiring, locate the relevant service and its docker entrypoint.

## 2) Work style: how to execute tasks

### 2.1 Plan first, then implement
For any task larger than a few lines:
- Summarize intended edits as a checklist
- Identify files you will touch
- Identify tests to run
- Then implement

### 2.2 Prefer fast local verification
After changes, run the smallest relevant test first:
- Unit tests for the module you touched
- Then service-level tests
- Then docker smoke if needed

### 2.3 Keep logs actionable
If you add logging:
- Include enough context (service, instance_id, workspace_id, session_id)
- Avoid spam logs in hot loops
- Prefer structured logs where the codebase already uses them

## 3) Dopemux conventions

### 3.1 Instance and workspace scoping
Most state must be scoped by:
- `workspace_id`
- `instance_id`
- sometimes `session_id`

Never merge data across instances unless explicitly required.

### 3.2 Progressive disclosure
Default outputs should be small and legible.
If there is a top-k rule for a tool or endpoint, enforce it.

### 3.3 Feature flags
New integrations that can fail in dev should be feature-flagged with safe defaults.
Example pattern:
- `ENABLE_<FEATURE>=0` by default
- When disabled, the service should still run

## 4) Docker and Compose policy

### 4.1 Fail fast on invalid compose
When modifying compose files or scripts:
- Validate with `docker compose config` before attempting startup
- Do not swallow compose validation errors

### 4.2 Avoid duplicate networks and duplicate services
- Do not list the same network twice for a service.
- Avoid spawning multiple redis/postgres containers unless explicitly intended.
- If multiple compose stacks are required, unify via:
  - shared external network, or
  - consistent `COMPOSE_PROJECT_NAME`, or
  - profiles in a single compose file
Do not change topology unless the task requests it.

### 4.3 Health checks
Health checks should:
- Use stable URLs
- Use short timeouts
- Provide clear failure output
If a dependency is optional, gate its health check behind a flag.

## 5) MCP server policy

### 5.1 MCP startup must be deterministic
- No silent failure
- If a required MCP server fails, provide exact reason and remediation
- Prefer "skip with explicit flag" over "continue with reduced functionality" unless task specifies otherwise

### 5.2 Keep tool contracts stable
If you touch MCP tool schemas:
- Preserve parameter names and defaults unless task says otherwise
- Document changes
- Add or update tests that validate schema output

## 6) Memory system architecture policy

Dopemux memory is multi-tier:
- DopeContext: semantic archival retrieval (vector search)
- ConPort: structured truth and decisions
- ConPort-KG: graph relationships over structured entities
- Dope-Memory: temporal chronicle and reflective loop (work logs, reflections, trajectory)

Rules:
- Do not duplicate the same concept in multiple stores unless it is an intentional mirror with clear ownership.
- If mirroring SQLite to Postgres/AGE, define:
  - source of truth
  - replication triggers
  - conflict strategy
- Chronological events belong in Dope-Memory, not in ConPort.

## 7) Coding conventions

### Python Code Style
- **Formatting**: Black (line length 88) + isort (black profile)
- **Type hints**: Required for function signatures (mypy strict mode)
- **Linting**: flake8 for code quality
- **Testing**: pytest with markers (unit, integration, slow, adhd, database)
- **Coverage**: Minimum 80% branch coverage required

### Common Patterns
- Manager classes for resource lifecycle: `InstanceManager`, `ProfileManager`, `WorktreeTemplateManager`
- Service classes for business logic: `AutoDetectionService`, `ServiceHealth`
- Async/await for I/O-bound operations
- Early returns over deep nesting
- Explicit defaults over magic values

### Adding New Modules
- Add `__init__.py` for Python packages
- Add unit tests in `tests/` with appropriate markers
- Use type hints for all public functions
- Follow existing patterns in the service you are editing
- Update imports in canonical entrypoint only after module is stable

### Pre-commit Hooks
The repository uses pre-commit hooks for:
- Documentation frontmatter validation
- Knowledge graph schema validation
- Prohibited file pattern checks (no TEMP*.md, TODO*.md, etc.)
- Markdown linting
- Trailing whitespace and EOF fixes

## 8) Output requirements for Copilot responses

When you propose or complete changes, include:

1) Files changed
- List exact paths

2) What changed
- Bullet summary of behavior changes

3) How to test
- Exact commands

4) Risk notes
- Any migration, compatibility, or runtime risks

If anything is uncertain, state it clearly and name the file(s) that would resolve it.

## 9) Merge checklist

Before you conclude:
- `docker compose config` passes for any compose file you touched
- Unit tests pass: `pytest tests/path/to/modified_test.py`
- Type checking passes: `mypy src/dopemux/modified_file.py`
- Formatting applied: `black src/ && isort src/`
- If modifying docs: `python scripts/docs_validator.py` passes
- Smoke stack unchanged unless requested
- No duplicated networks in compose
- Feature flags default safe
- Logs are helpful, not noisy
- Service registry updated if ports or health endpoints changed

## 10) Architecture patterns to follow

### Three-Layer Integration (ADR-207)
1. **Infrastructure Layer**: postgres, redis, qdrant
2. **MCP Layer**: dope-query, zen, dope-context
3. **Coordination/Cognitive Layer**: dopecon-bridge, task-orchestrator, adhd-engine

### Event-Driven Coordination
- Events flow through `dopecon-bridge` (port 3016)
- MCP events captured and routed via bridge
- Event bus implementation in `src/dopemux/event_bus.py`
- Services subscribe to specific event types

### Memory System Separation
- **DopeContext**: Semantic archival retrieval (vector search in Qdrant)
- **DopeQuery** (ConPort): Structured truth and decisions (PostgreSQL + AGE)
- **ConPort-KG**: Graph relationships over structured entities
- **Dope-Memory**: Temporal chronicle and reflective loop (work logs, trajectory)

Do not duplicate concepts across stores. Define source of truth clearly.

### Service Health Endpoints
All HTTP services must implement `/health` endpoint returning:
```json
{
  "status": "healthy|degraded|unhealthy",
  "service": "service-name",
  "timestamp": "ISO-8601",
  "checks": {...}
}
```

## 11) Documentation structure (Diátaxis)

Documentation follows Diátaxis methodology in `docs/`:
- `01-tutorials/`: Learning-oriented guides
- `02-how-to/`: Problem-solving guides  
- `03-reference/`: Technical specifications
- `04-explanation/`: Understanding-oriented docs
- `90-adr/`: Architecture Decision Records
- `91-rfc/`: Request for Comments
- `archive/`: Completed work, session notes (never deleted, always archived)

All docs must have YAML frontmatter with:
```yaml
---
title: "Document Title"
type: tutorial|how-to|reference|explanation|adr|rfc
status: draft|active|deprecated|superseded
prelude: "Brief description ≤100 tokens for embeddings"
tags: [tag1, tag2]
---
```

## 12) Finding your way around

### Service-Specific README Files
Each service has its own README: `services/[service-name]/README.md`

### Key Reference Files
- `services/registry.yaml`: Port mappings and health endpoints
- `docs/docs_index.yaml`: Machine-readable doc index
- `.env.example`: Environment variable reference
- `pyproject.toml`: Python dependencies and tool configs
- `pytest.ini`: Test configuration and markers

### When Making Changes
1. Check `AGENTS.md` for AI-specific guidance
2. Check `services/registry.yaml` for port conflicts
3. Check `docs/90-adr/` for relevant architectural decisions
4. Check existing tests in `tests/` for patterns
5. Check `.pre-commit-config.yaml` for validation rules