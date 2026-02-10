---
id: 04-installation
title: 04 Installation
type: explanation
date: '2026-01-25'
author: '@hu3mann'
owner: '@hu3mann'
last_review: '2026-01-25'
next_review: '2026-04-25'
prelude: Explanation of 04 Installation.
---
# Installation Guide

Complete installation guide for Dopemux CLI, library, and service stack.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [CLI & Library Installation](#cli--library-installation)
- [Optional Extras](#optional-extras)
- [Development Tooling Setup](#development-tooling-setup)
- [Running Tests](#running-tests)
- [Service Deployment](#service-deployment)
- [Common Issues & Solutions](#common-issues--solutions)
- [Verification](#verification)

---

## Prerequisites

### Required

- **Python 3.11+** (CI parity version)
- **pip 21.0+**
- **git 2.30+**

### Optional (for services)

- **Docker 20.10+**
- **docker-compose v2.0+**

### Verify Prerequisites

```bash
# Check Python version (must be 3.11+)
python3 --version

# Check pip version
python3 -m pip --version

# Check git version
git --version

# Check Docker (optional, for services)
docker --version
docker compose version
```

---

## Quick Start

**One-command install for development:**

```bash
pip install -e ".[dev]"
```

This installs:
- Core `dopemux` library
- CLI tool (`dopemux` command)
- All development dependencies (pytest, black, mypy, pre-commit)

**Verify installation:**

```bash
# Test import
python -c "import dopemux; print('✅ dopemux installed')"

# Test CLI
dopemux --help
```

---

## CLI & Library Installation

### Development Install (Editable)

For local development with live code changes:

```bash
# Clone repository
git clone https://github.com/DDD-Enterprises/dopemux-mvp.git
cd dopemux-mvp

# Install in editable mode with dev extras
pip install -e ".[dev]"
```

### Production Install

For deployment or CI environments:

```bash
pip install .
```

### User Install (from PyPI - future)

Once published to PyPI:

```bash
pip install dopemux
```

---

## Optional Extras

Dopemux provides optional dependency groups for specific features.

### Memory Stack Extra

For memory services (ConPort, Working Memory Assistant, etc.):

```bash
pip install -e ".[memory]"
```

Includes:
- PostgreSQL drivers (psycopg2-binary, asyncpg)
- SQLAlchemy & Alembic
- Redis client
- Zep integration
- Neo4j graph database
- MCP framework
- FastAPI & uvicorn
- OpenTelemetry observability

### Combined Install

Install both dev and memory extras:

```bash
pip install -e ".[dev,memory]"
```

---

## Development Tooling Setup

### Pre-commit Hooks

Dopemux uses pre-commit for code quality enforcement.

```bash
# Install pre-commit hooks
pre-commit install --install-hooks

# Run manually on all files
pre-commit run --all-files

# Skip specific hooks (if needed)
SKIP=docs-graph-validator pre-commit run --all-files
```

### Linting & Formatting

Tools configured in `pyproject.toml`:
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

```bash
# Format code
black .

# Sort imports
isort .

# Type check
mypy src/
```

---

## Running Tests

Dopemux uses pytest with tiered test organization.

### Quick Unit Tests

```bash
# Run unit tests only
pytest tests/unit

# Run with minimal output
pytest tests/unit -q

# Run specific test file
pytest tests/unit/test_workspace.py -v
```

### Contract Tests

```bash
# Run ConPort client contract tests
PYTEST_ADDOPTS=--no-cov pytest tests/contracts/test_conport_client_contract.py
```

### Full Test Suite

```bash
# Run all tests with coverage (requires 80% coverage)
pytest

# Run without coverage requirement (quick check)
PYTEST_ADDOPTS=--no-cov pytest -q
```

### Test Configuration

- **pytest.ini** - Test discovery, markers, coverage
- Coverage target: 80% minimum
- HTML coverage report: `htmlcov/index.html`
- XML coverage: `coverage.xml`

For detailed testing guide, see [docs/03-testing.md](./03-testing.md).

---

## Service Deployment

### Smoke Stack (Minimal Services)

Run core services for local development:

```bash
# Start smoke stack
docker compose -f docker-compose.smoke.yml up --build -d

# Verify service health
python tools/ports_health_audit.py --mode runtime --services conport,task-orchestrator,dopecon-bridge

# View logs
docker compose -f docker-compose.smoke.yml logs -f

# Stop stack
docker compose -f docker-compose.smoke.yml down
```

### Service Build Matrix

Validate all service Dockerfiles build successfully:

```bash
# Build all services and generate scoreboard
python tools/docker_build_matrix.py --mode build --scoreboard

# View build report
cat reports/docker_build_scoreboard.json
```

### Port Configuration

**Core Stack Ports:**
- 5432 - PostgreSQL (AGE extension)
- 6379 - Redis (event bus)
- 6333, 6334 - Qdrant (vector DB)
- 3004 - ConPort MCP server
- 8000 - ADHD Engine API
- 8095 - Task Orchestrator

**Full Stack Additional Ports:**
- 3002, 3003, 3011, 3016 - MCP services
- 4000 - DopeconBridge
- 8081, 8090 - Monitoring/dashboards

**Conflict Resolution:**

```bash
# Set custom port base (shifts all ports up)
PORT_BASE=10000 docker compose -f docker-compose.smoke.yml up -d
```

---

## Service Packaging Standard

### Dependency Declaration

**Each service MUST use ONE dependency source:**

- **Option A (Preferred):** `pyproject.toml` + `pip install .`
- **Option B:** `requirements.txt` + `pip install -r requirements.txt` (only if no pyproject.toml)

**DO NOT** maintain both `pyproject.toml` AND `requirements.txt` in the same service (drift risk).

### Dockerfile Pattern

Standard Dockerfile pattern for services:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install root dopemux library first
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --no-cache-dir /app

# Copy shared library (if needed)
COPY services/shared /app/services/shared
RUN pip install --no-cache-dir /app/services/shared

# Copy service code
COPY services/<service-name> /app/services/<service-name>
WORKDIR /app/services/<service-name>

# Install service dependencies
RUN pip install --no-cache-dir .

# Service-specific commands...
CMD ["python", "server.py"]
```

### Migration from requirements.txt to pyproject.toml

If a service has both files:

1. **Compare dependencies** - ensure no drift
2. **Migrate to pyproject.toml** as single source
3. **Update Dockerfile** - change `pip install -r requirements.txt` to `pip install .`
4. **Test build** - `docker build -t <service> -f services/<service>/Dockerfile .`
5. **Delete requirements.txt** after validation

### Service Audit

Check for dependency drift:

```bash
# Run service dependency audit
python tools/service_dep_audit.py

# Or quick pattern check
find services -name "pyproject.toml" -o -name "requirements.txt" | sort
```

**Current state (2026-01-25):**
- 16 services have BOTH files (drift risk) - migration needed
- 10 services use pyproject.toml only ✅
- 1 service uses requirements.txt only (valid)
- 16 services have no declared deps (may rely on root or shared)

### Import Path Discipline

**Services should NOT depend on running from repo root.**

❌ **Bad Practice:**
```python
# DON'T manipulate sys.path
import sys
sys.path.append("/path/to/repo")
from dopemux import something
```

✅ **Good Practice:**
```python
# Install package properly
# pip install -e .
from dopemux import something
```

**Docker Best Practice:**

In Docker images, install packages rather than mounting code with PYTHONPATH:

```dockerfile
# ✅ Install package (production)
RUN pip install --no-cache-dir /app

# ⚠️ Editable install (dev only)
RUN pip install --no-cache-dir -e /app

# ❌ PYTHONPATH hack (avoid)
ENV PYTHONPATH=/app/src
```

**Audit Tools:**

```bash
# Check for sys.path hacks
python tools/pythonpath_audit.py --strict

# Run architectural tests
pytest tests/arch/test_pythonpath_discipline.py -v
```

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'dopemux'`

**Cause:** Package not installed or wrong virtual environment active.

**Solution:**

```bash
# Ensure you're in repo root
cd /path/to/dopemux-mvp

# Install in current environment
pip install -e ".[dev]"

# Verify installation
python -c "import dopemux"
```

### Issue: `ImportError: cannot import name 'asyncpg'`

**Cause:** Memory stack dependencies not installed.

**Solution:**

```bash
# Install memory extra
pip install -e ".[memory]"
```

### Issue: Port conflicts when starting Docker stack

**Cause:** Another process using required ports (especially 5432, 6379, 6333).

**Solution:**

```bash
# Check what's using ports
lsof -i :5432
lsof -i :6379

# Stop conflicting services or use PORT_BASE
PORT_BASE=10000 docker compose -f docker-compose.smoke.yml up -d
```

### Issue: Coverage below 80%, tests fail

**Cause:** `pytest.ini` enforces 80% coverage threshold.

**Solution:**

```bash
# Run without coverage for quick validation
PYTEST_ADDOPTS=--no-cov pytest -q

# Or improve test coverage in failing modules
pytest --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Issue: Pre-commit hook fails on docs-graph-validator

**Cause:** Documentation graph validation has pre-existing issues.

**Solution:**

```bash
# Skip docs-graph-validator hook
SKIP=docs-graph-validator pre-commit run --all-files
```

### Issue: Docker build fails with "COPY failed"

**Cause:** Service Dockerfile expects repo structure (root deps, shared lib).

**Solution:**

```bash
# Build from repo root, not service directory
cd /path/to/dopemux-mvp
docker compose -f docker-compose.smoke.yml build <service-name>
```

### Issue: Python version mismatch

**Cause:** Using Python < 3.11 (CI uses 3.11).

**Solution:**

```bash
# Use pyenv or similar to install Python 3.11
pyenv install 3.11.7
pyenv local 3.11.7

# Recreate venv with correct Python
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows
pip install -e ".[dev]"
```

---

## Verification

### Verify CLI Installation

```bash
# Check version
dopemux --version

# View help
dopemux --help

# Test workspace command (if available)
dopemux workspace status
```

### Verify Library Import

```bash
# Test core imports
python -c "
from dopemux.workspace import resolve_workspace_root
from dopemux.clients import get_conport_client
print('✅ Core modules import successfully')
"
```

### Verify Service Stack

```bash
# Check Docker containers running
docker compose -f docker-compose.smoke.yml ps

# Test service health endpoints
curl -s http://localhost:8000/health  # ADHD Engine
curl -s http://localhost:8095/health  # Task Orchestrator
curl -s http://localhost:3004/health  # ConPort MCP

# Run port health audit
python tools/ports_health_audit.py --mode runtime
```

### Verify Development Tooling

```bash
# Test pre-commit hooks
pre-commit run --all-files

# Run quick test suite
pytest tests/unit -q

# Verify import smoke-tier (CI gate)
python tools/import_smoke_tier.py
```

---

## Next Steps

- **Explore the codebase:** See [docs/00-repo-map.md](./00-repo-map.md)
- **Run tests:** See [docs/03-testing.md](./03-testing.md)
- **Understand architecture:** See [docs/94-architecture/](./94-architecture/)
- **Review refactor gates:** See [docs/engineering/refactor_gates.md](./engineering/refactor_gates.md)

---

## Support

- **Issues:** [GitHub Issues](https://github.com/DDD-Enterprises/dopemux-mvp/issues)
- **Documentation:** [docs/](.)
- **Repository:** [dopemux/dopemux-mvp](https://github.com/DDD-Enterprises/dopemux-mvp)

---

*Last updated: 2026-01-25*
*Installation verified with Python 3.11, Docker 24.0, macOS/Linux*
