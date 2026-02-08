# Tests Context

> **TL;DR**: pytest with AAA pattern. Fast unit tests (<100ms), slower integration. Use fixtures, mock external services. Coverage target 80%.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Test Structure

```
tests/
├── unit/              # Fast isolated tests
├── integration/       # Component interaction
├── e2e/               # Full workflows
├── dopemux/           # Core package tests
├── orchestrator/      # Orchestrator tests
├── fixtures/          # Shared test data
├── resources/         # Test resources
└── conftest.py        # Shared fixtures
```

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
- `app` - FastAPI test client
- `db_session` - Test database session
- `mock_conport` - Mocked ConPort client
- `adhd_profile` - Test ADHD profile