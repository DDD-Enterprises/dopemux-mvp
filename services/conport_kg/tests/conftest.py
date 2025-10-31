#!/usr/bin/env python3
"""
ConPort-KG Test Configuration
Production-quality test fixtures and configuration for comprehensive testing.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
import tempfile
import shutil

# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5433/test_conport_kg"
)

# Test settings
TEST_SETTINGS = {
    "database_url": TEST_DATABASE_URL,
    "redis_url": os.getenv("TEST_REDIS_URL", "redis://localhost:6380/1"),
    "secret_key": "test_secret_key_for_jwt_tokens_123456789",
    "debug": True,
    "testing": True
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_settings() -> Dict[str, Any]:
    """Provide test settings for all tests."""
    return TEST_SETTINGS.copy()

@pytest.fixture(scope="session")
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for the test session."""
    temp_path = tempfile.mkdtemp(prefix="conport_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

# Database Fixtures

@pytest.fixture(scope="session")
def database_container():
    """PostgreSQL test container using testcontainers."""
    try:
        from testcontainers.postgres import PostgresContainer

        container = PostgresContainer(
            image="postgres:15-alpine",
            username="test_user",
            password="test_password",
            dbname="test_conport_kg",
            port=5433
        )

        container.start()
        db_url = container.get_connection_url()

        # Override the test database URL
        os.environ["TEST_DATABASE_URL"] = db_url

        yield container

        container.stop()

    except ImportError:
        # Fallback when testcontainers is not available
        pytest.skip("testcontainers not available - install with: pip install testcontainers[postgresql]")

@pytest.fixture(scope="function")
async def db_session(database_container):
    """Provide a database session for each test function."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    # Create async engine for testing
    engine = create_async_engine(
        TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
        pool_pre_ping=True
    )

    # Create session factory
    async_session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Start transaction for test isolation
        async with session.begin():
            try:
                yield session
                # Rollback changes after test
                await session.rollback()
            finally:
                await session.close()

    await engine.dispose()

@pytest.fixture(scope="function")
async def clean_db(db_session):
    """Ensure clean database state for each test."""
    # Drop all tables and recreate schema
    from conport_kg.auth.database import Base

    # Drop all tables
    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Run migrations if needed
    # TODO: Add alembic migration execution here

    yield db_session

# Authentication Fixtures

@pytest.fixture
def mock_user_data() -> Dict[str, Any]:
    """Provide mock user data for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": "hashed_password",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "workspaces": [
            {
                "workspace_id": "test-workspace",
                "role": "member",
                "permissions": ["read", "write"]
            }
        ]
    }

@pytest.fixture
def mock_jwt_token(mock_user_data) -> str:
    """Provide a mock JWT token for testing."""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": str(mock_user_data["id"]),
        "email": mock_user_data["email"],
        "username": mock_user_data["username"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "type": "access"
    }

    # Create token with test secret
    token = jwt.encode(payload, TEST_SETTINGS["secret_key"], algorithm="HS256")
    return token

@pytest.fixture
def mock_refresh_token(mock_user_data) -> str:
    """Provide a mock refresh token for testing."""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": str(mock_user_data["id"]),
        "email": mock_user_data["email"],
        "username": mock_user_data["username"],
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    # Create token with test secret
    token = jwt.encode(payload, TEST_SETTINGS["secret_key"], algorithm="HS256")
    return token

@pytest.fixture
async def auth_headers(mock_jwt_token) -> Dict[str, str]:
    """Provide authentication headers for API testing."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}

# Factory Fixtures for Test Data

@pytest.fixture
def user_factory(db_session):
    """Factory for creating test users."""
    try:
        import factory
        from factory.alchemy import SQLAlchemyModelFactory
        from conport_kg.auth.models import User

        class UserFactory(SQLAlchemyModelFactory):
            class Meta:
                model = User
                sqlalchemy_session = db_session

            email = factory.Sequence(lambda n: f"user{n}@example.com")
            username = factory.Sequence(lambda n: f"user{n}")
            password_hash = factory.LazyFunction(lambda: "hashed_password")
            is_active = True

        return UserFactory

    except ImportError:
        pytest.skip("factory-boy not available - install with: pip install factory-boy")

@pytest.fixture
def workspace_factory(db_session):
    """Factory for creating test workspaces."""
    try:
        import factory
        from factory.alchemy import SQLAlchemyModelFactory
        from conport_kg.auth.models import UserWorkspace

        class WorkspaceFactory(SQLAlchemyModelFactory):
            class Meta:
                model = UserWorkspace
                sqlalchemy_session = db_session

            workspace_id = factory.Sequence(lambda n: f"workspace-{n}")
            role = "member"
            permissions = ["read", "write"]

        return WorkspaceFactory

    except ImportError:
        pytest.skip("factory-boy not available - install with: pip install factory-boy")

# Mock Fixtures for External Services

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    return mock_client

@pytest.fixture
def mock_external_api():
    """Mock external API responses."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    return mock_response

# FastAPI Test Client

@pytest.fixture
async def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from conport_kg.main import app  # Import your FastAPI app

    # Override settings for testing
    app.state.settings = TEST_SETTINGS

    with TestClient(app) as test_client:
        yield test_client

# Async Test Client for httpx

@pytest.fixture
async def async_client():
    """Async HTTP client for testing FastAPI endpoints."""
    from httpx import AsyncClient
    from conport_kg.main import app  # Import your FastAPI app

    # Override settings for testing
    app.state.settings = TEST_SETTINGS

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

# Test Utilities

@pytest.fixture
def test_request_context():
    """Provide a test request context for middleware testing."""
    from unittest.mock import MagicMock

    request = MagicMock()
    request.method = "GET"
    request.url = MagicMock()
    request.url.path = "/test"
    request.headers = {"user-agent": "test-client"}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.state = MagicMock()
    request.state.request_id = "test-request-id"

    return request

# Cleanup and Teardown

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up after each test."""
    yield

    # Add any cleanup logic here
    # For example: clear caches, reset global state, etc.

# Test Markers

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "auth: Authentication related tests")
    config.addinivalue_line("markers", "db: Database related tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "security: Security related tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

# Environment Setup

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    original_env = {}

    # Store original values
    for key in ["DATABASE_URL", "REDIS_URL", "SECRET_KEY"]:
        if key in os.environ:
            original_env[key] = os.environ[key]

    # Set test values
    os.environ.update({
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": TEST_SETTINGS["redis_url"],
        "SECRET_KEY": TEST_SETTINGS["secret_key"],
        "TESTING": "true"
    })

    yield

    # Restore original values
    for key, value in original_env.items():
        os.environ[key] = value
    for key in ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "TESTING"]:
        if key not in original_env and key in os.environ:
            del os.environ[key]

# Performance Testing Fixtures

@pytest.fixture
def benchmark_config():
    """Configuration for performance benchmarks."""
    return {
        "min_rounds": 5,
        "max_time": 1.0,
        "warmup": True
    }