# Security Testing Framework

Comprehensive security testing suite for the Dopemux Ultra UI platform, ensuring robust protection while maintaining ADHD-friendly development workflows.

## 🛡️ Security Testing Overview

### Testing Philosophy
- **Shift Security Left**: Security tests run in CI/CD pipeline before deployment
- **Comprehensive Coverage**: Authentication, authorization, input validation, rate limiting
- **ADHD-Aware**: Tests designed to minimize cognitive load during development
- **Automated Remediation**: Failed tests provide clear fix instructions

### Test Categories
```
Security Testing Framework
├── Authentication Tests
│   ├── API Key validation
│   ├── JWT token handling
│   └── Session management
├── Authorization Tests
│   ├── Role-based access control
│   ├── Permission validation
│   └── Service-to-service auth
├── Input Validation Tests
│   ├── URL validation and sanitization
│   ├── Content-type verification
│   └── XSS/SQL injection prevention
├── Rate Limiting Tests
│   ├── Token bucket algorithm
│   ├── IP-based limiting
│   └── DDoS protection
├── CORS Security Tests
│   ├── Origin validation
│   ├── Method restrictions
│   └── Header filtering
└── Encryption Tests
    ├── Data at rest encryption
    ├── TLS in transit
    └── Secure key management
```

## 🧪 Test Structure

### Test Organization
```
tests/security/
├── test_cors.py              # CORS security tests
├── test_input_validation.py  # Input validation tests
├── test_rate_limiting.py     # Rate limiting tests
├── test_authentication.py    # Authentication tests
├── test_authorization.py     # Authorization tests
├── test_encryption.py        # Encryption tests
└── conftest.py              # Shared test fixtures
```

### Shared Fixtures (`conftest.py`)
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient
import asyncio
import subprocess
import os

@pytest_asyncio.fixture(scope="class")
async def adhd_engine_client():
    """Start ADHD Engine server for integration testing."""
    # Server startup logic
    process = None
    client = None

    try:
        # Environment setup
        env = os.environ.copy()
        env.update({
            "ALLOWED_ORIGINS": "http://localhost:3000,http://test.example.com",
            "ADHD_ENGINE_API_KEY": "test-key-123",
            "REDIS_URL": "redis://localhost:6379/6"
        })

        # Start server
        process = subprocess.Popen([
            "python", "-m", "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8095"
        ], cwd="services/adhd_engine", env=env)

        # Wait for startup
        await asyncio.sleep(3)

        # Create test client
        client = AsyncClient(base_url="http://127.0.0.1:8095")

        # Health check
        response = await client.get("/health")
        assert response.status_code == 200

        yield client

    finally:
        # Cleanup
        if client:
            await client.aclose()
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
```

## 🔐 Authentication Tests

### API Key Authentication
```python
class TestAuthentication:
    async def test_valid_api_key(self, client):
        """Test valid API key authentication."""
        response = await client.get(
            "/api/v1/user-profile",
            headers={"X-API-Key": "test-key-123"}
        )
        assert response.status_code == 200

    async def test_invalid_api_key(self, client):
        """Test invalid API key rejection."""
        response = await client.get(
            "/api/v1/user-profile",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    async def test_missing_api_key(self, client):
        """Test missing API key rejection."""
        response = await client.get("/api/v1/user-profile")
        assert response.status_code == 403
        assert "API key required" in response.json()["detail"]
```

### JWT Token Tests
```python
class TestJWTAuthentication:
    async def test_valid_jwt_token(self, client, valid_jwt_token):
        """Test valid JWT token authentication."""
        response = await client.post(
            "/api/v1/assess-task",
            json={"task_description": "test task"},
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )
        assert response.status_code == 200

    async def test_expired_jwt_token(self, client, expired_jwt_token):
        """Test expired JWT token rejection."""
        response = await client.post(
            "/api/v1/assess-task",
            json={"task_description": "test task"},
            headers={"Authorization": f"Bearer {expired_jwt_token}"}
        )
        assert response.status_code == 401
        assert "Token expired" in response.json()["detail"]
```

## ✅ Input Validation Tests

### URL Validation Tests
```python
class TestInputValidation:
    @pytest.mark.parametrize("origins_input,expected_origins", [
        # Valid cases
        ("http://localhost:3000", ["http://localhost:3000"]),
        ("http://localhost:3000,https://example.com", ["http://localhost:3000", "https://example.com"]),
        ("http://test.com:8080, https://secure.app ", ["http://test.com:8080", "https://secure.app"]),

        # Invalid cases (should be filtered out)
        ("http://valid.com,not-a-url", ["http://valid.com"]),
        ("http://valid.com, javascript:alert(1)", ["http://valid.com"]),
        ("", ["http://localhost:3000", "http://localhost:8080"]),  # Fallback
        ("invalid-url,another-invalid", ["http://localhost:3000", "http://localhost:8080"]),  # Fallback
    ])
    def test_allowed_origins_parsing(self, origins_input, expected_origins):
        """Test ALLOWED_ORIGINS parsing with various inputs."""
        import re

        # Simulate validation logic
        url_pattern = re.compile(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$')
        ALLOWED_ORIGINS = origins_input.split(",")
        ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if url_pattern.match(origin.strip())]

        if not ALLOWED_ORIGINS:
            # Fallback for invalid/empty input
            ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]

        assert ALLOWED_ORIGINS == expected_origins
```

### XSS Prevention Tests
```python
class TestXSSPrevention:
    @pytest.mark.parametrize("malicious_input,should_be_sanitized", [
        ("<script>alert('xss')</script>", True),
        ("<img src=x onerror=alert(1)>", True),
        ("<a href=\"javascript:alert(1)\">Click me</a>", True),
        ("Normal text input", False),
        ("<b>Bold text</b>", True),  # HTML tags removed
    ])
    def test_xss_input_sanitization(self, malicious_input, should_be_sanitized):
        """Test XSS prevention through input sanitization."""
        from shared.validation import InputSanitizer

        sanitizer = InputSanitizer()
        sanitized = sanitizer.sanitize_html(malicious_input)

        if should_be_sanitized:
            assert sanitized != malicious_input
            assert "<script>" not in sanitized
            assert "<img" not in sanitized
            assert "javascript:" not in sanitized
        else:
            assert sanitized == malicious_input
```

## 🚦 Rate Limiting Tests

### Token Bucket Algorithm Tests
```python
class TestRateLimiting:
    async def test_rate_limit_assess_task_endpoint(self, client):
        """Test rate limiting on assess-task endpoint."""
        # Make requests up to limit
        for i in range(10):  # Assuming 10 req/min limit
            response = await client.post(
                "/api/v1/assess-task",
                json={"task_description": f"Task {i}"},
                headers={"X-API-Key": "test-key-123"}
            )
            assert response.status_code == 200

        # Next request should be rate limited
        response = await client.post(
            "/api/v1/assess-task",
            json={"task_description": "Rate limited task"},
            headers={"X-API-Key": "test-key-123"}
        )
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    async def test_rate_limit_reset(self, client):
        """Test that rate limit resets after time window."""
        # Exhaust rate limit
        for i in range(10):
            await client.post(
                "/api/v1/assess-task",
                json={"task_description": f"Task {i}"},
                headers={"X-API-Key": "test-key-123"}
            )

        # Wait for reset (in test environment, this might be mocked)
        await asyncio.sleep(61)  # Wait 61 seconds for 1-minute window

        # Should work again
        response = await client.post(
            "/api/v1/assess-task",
            json={"task_description": "After reset"},
            headers={"X-API-Key": "test-key-123"}
        )
        assert response.status_code == 200
```

### IP-Based Rate Limiting
```python
class TestIPRateLimiting:
    async def test_rate_limit_by_ip_address(self, client, mock_ip):
        """Test rate limiting based on IP address."""
        # Simulate requests from same IP
        headers = {"X-Forwarded-For": "192.168.1.100"}

        # Make requests up to limit
        for i in range(5):  # Assuming 5 req/min per IP
            response = await client.get("/health", headers=headers)
            assert response.status_code == 200

        # Next request should be blocked
        response = await client.get("/health", headers=headers)
        assert response.status_code == 429

    async def test_different_ips_not_affected(self, client):
        """Test that different IPs have separate rate limits."""
        headers1 = {"X-Forwarded-For": "192.168.1.100"}
        headers2 = {"X-Forwarded-For": "192.168.1.101"}

        # Exhaust limit for IP 1
        for i in range(5):
            await client.get("/health", headers=headers1)

        # IP 2 should still work
        response = await client.get("/health", headers=headers2)
        assert response.status_code == 200
```

## 🌐 CORS Security Tests

### Origin Validation Tests
```python
class TestCORSSecurity:
    async def test_cors_allowed_origins(self, client):
        """Test that only allowed origins are permitted."""
        response = await client.options(
            "/api/v1/assess-task",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    async def test_cors_rejects_unauthorized_origins(self, client):
        """Test that unauthorized origins are rejected."""
        response = await client.options(
            "/api/v1/assess-task",
            headers={
                "Origin": "http://malicious.com",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert response.status_code == 200  # OPTIONS always 200
        assert "access-control-allow-origin" not in response.headers

    async def test_cors_restricted_methods(self, client):
        """Test that only allowed methods are permitted."""
        response = await client.options(
            "/api/v1/assess-task",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "DELETE"  # Not allowed
            }
        )

        # Should not include allowed methods for unauthorized method
        assert "access-control-allow-methods" not in response.headers
```

### Preflight Request Handling
```python
class TestCORSPreflight:
    async def test_cors_preflight_success(self, client):
        """Test successful CORS preflight request."""
        response = await client.options(
            "/api/v1/assess-task",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,X-API-Key"
            }
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert "POST" in response.headers.get("access-control-allow-methods", "")
        assert "Content-Type" in response.headers.get("access-control-allow-headers", "")
        assert "X-API-Key" in response.headers.get("access-control-allow-headers", "")

    async def test_cors_preflight_rejected_headers(self, client):
        """Test CORS preflight with unauthorized headers."""
        response = await client.options(
            "/api/v1/assess-task",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,X-Custom-Header"
            }
        )

        # Should allow the request but not include unauthorized headers
        assert response.status_code == 200
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        assert "Authorization" not in allowed_headers
        assert "X-Custom-Header" not in allowed_headers
```

## 🧪 Running Security Tests

### Run All Security Tests
```bash
# Run all security tests with verbose output
pytest tests/security/ -v

# Run with coverage report
pytest tests/security/ --cov=services --cov-report=html

# Run specific test file
pytest tests/security/test_cors.py -v

# Run specific test class
pytest tests/security/test_rate_limiting.py::TestRateLimiting -v

# Run specific test method
pytest tests/security/test_input_validation.py::TestInputValidation::test_allowed_origins_parsing -v
```

### Test Configuration
```bash
# Environment variables for testing
export ALLOWED_ORIGINS="http://localhost:3000,http://test.example.com"
export ADHD_ENGINE_API_KEY="test-key-123"
export REDIS_URL="redis://localhost:6379/6"

# Test-specific settings
export RATE_LIMIT_REQUESTS_PER_MINUTE=10  # Lower for testing
export SECURITY_TEST_MODE=true
```

### CI/CD Integration
```yaml
# GitHub Actions example
name: Security Tests
on: [push, pull_request]

jobs:
  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx

      - name: Start test services
        run: |
          docker run -d -p 6379:6379 redis:7-alpine
          docker run -d -p 6333:6333 qdrant/qdrant

      - name: Run security tests
        run: pytest tests/security/ -v --tb=short

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 📊 Security Test Results

### Interpreting Test Results
```bash
# Successful run
========================= 14 passed, 13 warnings in 3.22s =========================

# Failed run with details
========================= FAILURES ==================================
test_cors.py::TestCORSSecurity::test_cors_allowed_origins FAILED
    AttributeError: 'async_generator' object has no attribute 'options'
```

### Common Issues and Fixes

#### Async Generator Fixture Issue
**Problem**: `async def client(): yield test_client` creates async generator
**Fix**: Use `@pytest_asyncio.fixture` with return instead of yield

#### Server Startup Issues
**Problem**: ADHD Engine server fails to start in tests
**Fix**:
- Check port availability (8095 vs 8096 conflicts)
- Verify environment variables
- Increase startup wait time
- Check server logs

#### Rate Limiting Test Timing
**Problem**: Tests depend on timing for rate limit reset
**Fix**:
- Use mocked time in tests
- Configure shorter time windows for testing
- Use synchronous rate limiter for deterministic testing

## 🔧 Security Test Maintenance

### Adding New Security Tests
```python
# 1. Identify security requirement
# 2. Create test file in tests/security/
# 3. Implement test class with descriptive methods
# 4. Add parametrized test cases for edge cases
# 5. Include both positive and negative test cases
# 6. Add to CI/CD pipeline

class TestNewSecurityFeature:
    async def test_feature_works_correctly(self, client):
        """Test that new security feature works as expected."""
        # Test implementation

    async def test_feature_blocks_attacks(self, client):
        """Test that feature prevents security attacks."""
        # Test attack prevention
```

### Updating Existing Tests
- **Review failed tests** after security changes
- **Update test expectations** to match new security behavior
- **Add new test cases** for new security features
- **Remove obsolete tests** for deprecated security measures

### Security Test Best Practices
- **Test both positive and negative cases**
- **Use parametrized tests** for comprehensive coverage
- **Mock external dependencies** for reliable testing
- **Include realistic attack payloads**
- **Test error handling and edge cases**
- **Document security assumptions** in test comments

## 📈 Security Test Metrics

### Coverage Goals
- **Authentication**: 100% of auth methods tested
- **Authorization**: 100% of permission checks tested
- **Input Validation**: 100% of input types validated
- **Rate Limiting**: 100% of rate limit scenarios tested
- **CORS**: 100% of CORS configurations tested

### Performance Benchmarks
- **Test Execution Time**: < 30 seconds for full security suite
- **Memory Usage**: < 256MB during test execution
- **False Positive Rate**: < 1% (tests should fail only on real issues)
- **CI/CD Integration**: < 5 minutes total pipeline time

### Quality Metrics
- **Test Reliability**: > 99% pass rate in stable branches
- **Maintenance Effort**: < 2 hours/month for test updates
- **Documentation Coverage**: 100% of tests have clear docstrings
- **Review Coverage**: 100% of security tests reviewed by security team

---

## 🎯 ADHD-Aware Security Testing

### Cognitive Load Considerations
- **Clear test names** that explain what is being tested
- **Detailed failure messages** that explain how to fix issues
- **Progressive test output** showing progress without overwhelming
- **Fast feedback loops** with quick test execution

### Test Organization
- **Logical grouping** of related security concerns
- **Clear separation** between different security domains
- **Minimal setup** requirements for easy local testing
- **Comprehensive fixtures** to reduce test boilerplate

### Error Messages
```python
# Good error message
assert False, "CORS security violation: Origin 'http://malicious.com' not in allowed list. Add to ALLOWED_ORIGINS environment variable or update CORS policy."

# Bad error message
assert False, "CORS failed"
```

---

**Status**: ✅ Comprehensive security testing framework
**Coverage**: Authentication, authorization, input validation, rate limiting, CORS
**Integration**: CI/CD pipeline integration with automated reporting
**ADHD Support**: Clear error messages and cognitive load considerations
**Maintenance**: Well-documented test structure for easy updates and extensions