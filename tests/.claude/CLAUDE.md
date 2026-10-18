# Tests Context

> **TL;DR**: pytest with AAA pattern. Fast unit tests (<100ms), slower integration. Use fixtures, mock external services. Coverage target 80%.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Test Structure

Key directories (≈40 total — `ls tests/`):

```
tests/
├── unit/              # Fast isolated tests
├── integration/       # Component interaction
├── dopemux/           # Core package tests
├── dopemux_cli/       # CLI integration tests
├── dopemux_init/      # Init workflow tests
├── orchestrator/      # Orchestrator tests
├── fixtures/          # Shared test data
├── resources/         # Test resources
├── arch/              # Architecture tests
├── audit/             # Audit tests
├── ci/                # CI-specific tests
├── mcp/               # MCP tests
├── security/          # Security tests
├── contracts/         # Contract tests
├── governance/        # Governance validators
├── commandcode_router/  # Persona catalog (hash-gated vs proof/CCAR-002)
├── shared/            # Shared test utilities
└── conftest.py        # Shared fixtures
```

Note: `e2e/` directory does **not** exist.

---

## Running Tests

Canonical runner is the Makefile (uv, frozen lockfile):

```bash
make test              # uv run --frozen --extra test pytest tests
make test-fast         # unit only, --maxfail=1, no coverage
make test-integration  # syncs --extra services first

# Direct pytest: use the repo venv (mise python 3.12)
.venv/bin/python -m pytest tests/ -v

# Specific category
.venv/bin/python -m pytest tests/unit/ -v
.venv/bin/python -m pytest tests/integration/ -v

# With coverage
.venv/bin/python -m pytest tests/ --cov=src/dopemux --cov-report=html

# Skip slow tests
.venv/bin/python -m pytest tests/ -m "not slow"
```

`pytest.ini` overrides `[tool.pytest.ini_options]` in pyproject.toml (pytest warns and ignores the latter) — edit `pytest.ini`. Markers are strict (`--strict-markers`): register new ones there.

---

## Test Pattern (AAA)

```python
def test_should_create_task_when_valid_input():
    # Arrange
    task_data = TaskCreate(title="Test", complexity=0.5)
    
    # Act
    result = task_service.create(task_data)
    
    # Assert
    assert result.id is not None
    assert result.title == "Test"
```

---

## Naming Conventions

- Unit: `test_should_[behavior]_when_[condition]`
- Integration: `test_integration_[component]_[scenario]`

---

## Targets

| Type | Speed | Coverage |
|------|-------|----------|
| Unit | <100ms each | 90% business logic |
| Integration | <5s each | 80% component interaction |

---

## Fixtures

Common fixtures in `conftest.py`:
- `temp_project_dir` - Temporary project directory
- `temp_config_dir` - Temporary config directory
- `sample_config_data` - Sample ADHD config dict
- `config_manager` - ConfigManager instance
- `context_manager` - ContextManager instance
- `attention_monitor` - AttentionMonitor instance
- `task_decomposer` - TaskDecomposer instance

Note: `app`, `db_session`, `mock_conport`, `adhd_profile` are **not** defined in conftest.py.