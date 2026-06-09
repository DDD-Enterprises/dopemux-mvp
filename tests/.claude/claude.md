# Tests Context

> **TL;DR**: pytest with AAA pattern. Fast unit tests (<100ms), slower integration. Use fixtures, mock external services. Coverage target 80%.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Test Structure

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
├── shared/            # Shared test utilities
└── conftest.py        # Shared fixtures
```

Note: `e2e/` directory does **not** exist.

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific category
pytest tests/unit/ -v
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=src/dopemux --cov-report=html

# Skip slow tests
pytest tests/ -m "not slow"
```

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
- E2E: `test_e2e_[workflow]_[outcome]`

---

## Targets

| Type | Speed | Coverage |
|------|-------|----------|
| Unit | <100ms each | 90% business logic |
| Integration | <5s each | 80% component interaction |
| E2E | <15min total | 100% critical workflows |

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