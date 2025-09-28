# Testing Development Context

**Scope**: All testing code, test utilities, and quality assurance
**Inherits**: Two-Plane Architecture from project root
**Focus**: Comprehensive testing with ADHD-friendly test patterns and clear feedback

## 🧪 Testing Philosophy

### ADHD-Optimized Testing
- **Fast Feedback**: Quick test execution for immediate validation
- **Clear Names**: Descriptive test names that explain intent
- **Visual Results**: Easy-to-read test output with clear pass/fail indicators
- **Incremental Testing**: Build test coverage gradually without overwhelming complexity

### Test Categories
- **Unit Tests**: Fast, isolated tests for individual functions and classes
- **Integration Tests**: Component interaction testing with external dependencies
- **End-to-End Tests**: Full workflow validation for critical user paths
- **Performance Tests**: Load testing and performance regression detection

## 🎯 Testing Standards

### Test Structure (AAA Pattern)
```python
def test_should_create_user_when_valid_data_provided():
    """Test names should clearly describe the expected behavior."""
    # Arrange
    user_data = UserCreateModel(
        email="test@example.com",
        username="testuser"
    )

    # Act
    result = user_service.create_user(user_data)

    # Assert
    assert result.id is not None
    assert result.email == "test@example.com"
    assert result.username == "testuser"
```

### Test Naming Conventions
- **Unit Tests**: `test_should_[expected_behavior]_when_[condition]`
- **Integration Tests**: `test_integration_[component]_[scenario]`
- **E2E Tests**: `test_e2e_[user_workflow]_[outcome]`
- **Performance Tests**: `test_performance_[operation]_[constraint]`

### Fixture Organization
```python
# conftest.py - Shared fixtures
@pytest.fixture
def user_session():
    """Create a test user session with cleanup."""
    session = create_test_session()
    yield session
    cleanup_test_session(session)

@pytest.fixture
def sample_user():
    """Provide a standard test user."""
    return User(
        id=1,
        email="test@example.com",
        username="testuser"
    )
```

## 🚀 Agent Coordination

### Developer Agent (Primary)
**For Test Implementation**:
- Generate comprehensive test suites for new code
- Ensure test coverage meets project standards (80% minimum)
- Create clear, descriptive test names and documentation
- Implement test utilities and helper functions

### Researcher Agent (Support)
**For Testing Patterns**:
- Research testing best practices and frameworks
- Find solutions for complex testing scenarios
- Validate testing approaches against industry standards
- Provide examples of effective test patterns

### Quality Assurance Focus
- **Test Coverage**: Maintain comprehensive coverage without test bloat
- **Performance**: Keep test suite execution time reasonable for ADHD workflow
- **Maintainability**: Tests that are easy to understand and modify
- **Reliability**: Consistent test results with minimal flaky tests

## 🔧 Testing Tools and Patterns

### pytest Configuration
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (external dependencies)
    e2e: End-to-end tests (full workflow)
    slow: Tests that take >1 second to run
    performance: Performance and load tests
```

### Mocking Patterns
```python
# Preferred mocking approach
@pytest.fixture
def mock_user_repository():
    """Mock repository with predictable behavior."""
    mock_repo = Mock(spec=UserRepository)
    mock_repo.get_by_id.return_value = User(id=1, email="test@example.com")
    return mock_repo

def test_user_service_with_mock_repository(mock_user_repository):
    """Test service layer with mocked dependencies."""
    service = UserService(repository=mock_user_repository)

    result = service.get_user(1)

    assert result.email == "test@example.com"
    mock_user_repository.get_by_id.assert_called_once_with(1)
```

### Test Data Management
```python
# Factory pattern for test data
class UserFactory:
    """Generate test users with sensible defaults."""

    @staticmethod
    def create(email="test@example.com", username="testuser", **kwargs):
        """Create user with optional overrides."""
        return User(
            email=email,
            username=username,
            **kwargs
        )

    @staticmethod
    def create_batch(count=3, **kwargs):
        """Create multiple test users."""
        return [
            UserFactory.create(email=f"user{i}@example.com", **kwargs)
            for i in range(count)
        ]
```

## 📁 Test Organization

### Directory Structure
```
tests/
├── unit/              # Fast, isolated unit tests
│   ├── api/          # API layer tests
│   ├── core/         # Business logic tests
│   └── services/     # Service layer tests
├── integration/       # Component integration tests
│   ├── database/     # Database integration
│   ├── external/     # External service integration
│   └── api/          # Full API integration
├── e2e/              # End-to-end workflow tests
├── performance/      # Load and performance tests
├── fixtures/         # Shared test data and fixtures
└── utils/            # Test utilities and helpers
```

### Test File Conventions
- **Mirror Source Structure**: Test files mirror the structure of source code
- **Clear Naming**: `test_[module_name].py` for unit tests
- **Grouped Tests**: Use test classes to group related test scenarios
- **Shared Setup**: Use conftest.py for shared fixtures and configuration

## 🎯 ADHD-Friendly Testing Patterns

### Progressive Test Development
1. **Red**: Write failing test that describes desired behavior
2. **Green**: Write minimal code to make test pass
3. **Refactor**: Improve code while keeping tests green
4. **Repeat**: Build functionality incrementally

### Visual Test Feedback
```python
# Custom assertions with clear error messages
def assert_user_created_successfully(user, expected_email):
    """Assert user creation with detailed feedback."""
    assert user is not None, "User should not be None after creation"
    assert user.id is not None, "User should have an ID after creation"
    assert user.email == expected_email, f"Expected email {expected_email}, got {user.email}"
    assert user.created_at is not None, "User should have creation timestamp"
```

### Test Categorization
```python
# Use markers for different test types
@pytest.mark.unit
def test_fast_unit_test():
    """Quick test for immediate feedback."""
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_database_integration():
    """Slower test for comprehensive validation."""
    pass

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_user_workflow():
    """Full end-to-end workflow test."""
    pass
```

## 🔍 Quality Metrics

### Coverage Standards
- **Unit Tests**: 90% coverage for business logic
- **Integration Tests**: 80% coverage for component interactions
- **E2E Tests**: 100% coverage for critical user workflows
- **Overall**: Minimum 80% combined coverage

### Performance Standards
- **Unit Test Suite**: Complete in <30 seconds
- **Integration Test Suite**: Complete in <5 minutes
- **E2E Test Suite**: Complete in <15 minutes
- **Individual Tests**: Unit tests <100ms, integration tests <5s

### Test Quality Indicators
- **Reliability**: <1% flaky test rate
- **Maintainability**: Tests require minimal updates for source changes
- **Clarity**: Test intent clear from name and structure
- **Speed**: Fast enough for continuous development workflow

---

**Testing Excellence**: Comprehensive coverage with clear, maintainable tests
**ADHD Integration**: Fast feedback and visual clarity for immediate validation
**Quality Assurance**: Reliable testing that supports confident development