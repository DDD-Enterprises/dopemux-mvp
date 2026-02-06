#!/usr/bin/env python3
"""
ConPort-KG Test Utilities
Common testing utilities and helpers for comprehensive test coverage.
"""

import os

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union, Callable
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Test Data Generators

def generate_test_user(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate test user data."""
    base_user = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!",
        "is_active": True
    }
    if overrides:
        base_user.update(overrides)
    return base_user

def generate_test_workspace(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate test workspace data."""
    base_workspace = {
        "workspace_id": "test-workspace",
        "role": "member",
        "permissions": ["read", "write"]
    }
    if overrides:
        base_workspace.update(overrides)
    return base_workspace

def generate_test_token(user_data: Optional[Dict[str, Any]] = None,
                       token_type: str = "access",
                       expires_in: int = 3600) -> str:
    """Generate a test JWT token."""
    import jwt
    from datetime import datetime, timedelta

    if user_data is None:
        user_data = generate_test_user()

    payload = {
        "sub": str(user_data.get("id", 1)),
        "email": user_data["email"],
        "username": user_data["username"],
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        "iat": datetime.utcnow(),
        "type": token_type
    }

    # Use test secret key
    secret_key = "test_secret_key_for_jwt_tokens_123456789"
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def generate_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Generate authentication headers."""
    if token is None:
        token = generate_test_token()
    return {"Authorization": f"Bearer {token}"}

# Database Test Helpers

async def create_test_user(db_session, user_data: Optional[Dict[str, Any]] = None):
    """Create a test user in the database."""
    from conport_kg.auth.models import User
    from conport_kg.auth.password_utils import PasswordManager

    if user_data is None:
        user_data = generate_test_user()

    # Hash password
    password_hash = PasswordManager.hash_password(user_data["password"])

    user = User(
        email=user_data["email"],
        username=user_data["username"],
        password_hash=password_hash,
        is_active=user_data.get("is_active", True)
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user

async def create_test_workspace(db_session, user_id: int,
                              workspace_data: Optional[Dict[str, Any]] = None):
    """Create a test workspace membership."""
    from conport_kg.auth.models import UserWorkspace

    if workspace_data is None:
        workspace_data = generate_test_workspace()

    workspace = UserWorkspace(
        user_id=user_id,
        workspace_id=workspace_data["workspace_id"],
        role=workspace_data["role"],
        permissions=workspace_data["permissions"]
    )

    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)

    return workspace

# API Test Helpers

def assert_api_response(response, expected_status: int = 200,
                       expected_keys: Optional[List[str]] = None):
    """Assert API response structure and status."""
    assert response.status_code == expected_status

    if expected_status == 200 and expected_keys:
        data = response.json()
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

def assert_api_error(response, expected_status: int,
                     expected_error_code: Optional[str] = None):
    """Assert API error response."""
    assert response.status_code == expected_status

    if expected_status >= 400:
        data = response.json()
        assert "error_code" in data
        assert "message" in data

        if expected_error_code:
            assert data["error_code"] == expected_error_code

async def async_assert_api_response(async_client: AsyncClient, method: str, url: str,
                                   expected_status: int = 200,
                                   json_data: Optional[Dict] = None,
                                   headers: Optional[Dict[str, str]] = None,
                                   expected_keys: Optional[List[str]] = None):
    """Async version of API response assertion."""
    if json_data is not None:
        response = await async_client.request(method, url, json=json_data, headers=headers)
    else:
        response = await async_client.request(method, url, headers=headers)

    assert response.status_code == expected_status

    if expected_status == 200 and expected_keys:
        data = response.json()
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

    return response

# Mock Helpers

def create_mock_redis():
    """Create a mock Redis client."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.expire.return_value = True
    mock_redis.exists.return_value = False
    return mock_redis

def create_mock_external_service(response_data: Optional[Dict[str, Any]] = None,
                               status_code: int = 200):
    """Create a mock external service response."""
    mock_response = AsyncMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = response_data or {"status": "success"}
    mock_response.text = json.dumps(mock_response.json.return_value)
    return mock_response

def mock_external_api_call(mock_response: Optional[AsyncMock] = None):
    """Context manager to mock external API calls."""
    if mock_response is None:
        mock_response = create_mock_external_service()

    return patch('httpx.AsyncClient.request', return_value=mock_response)

# Performance Testing Helpers

async def time_async_operation(operation: Callable, *args, **kwargs) -> tuple:
    """Time an async operation and return result and duration."""
    start_time = time.time()
    result = await operation(*args, **kwargs)
    duration = time.time() - start_time
    return result, duration

def benchmark_operation(iterations: int = 100):
    """Decorator for benchmarking operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            times = []
            for _ in range(iterations):
                start = time.time()
                result = func(*args, **kwargs)
                end = time.time()
                times.append(end - start)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            print(f"Benchmark results for {func.__name__}:")
            print(f"  Average: {avg_time:.6f}s")
            print(f"  Min: {min_time:.6f}s")
            print(f"  Max: {max_time:.6f}s")

            return result
        return wrapper
    return decorator

# Test Data Validation

def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate and decode a JWT token for testing."""
    import jwt

    secret_key = "test_secret_key_for_jwt_tokens_123456789"
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        pytest.fail("Token has expired")
    except jwt.InvalidTokenError as e:
        pytest.fail(f"Invalid token: {e}")

def assert_valid_token_structure(token_data: Dict[str, Any],
                               expected_user_id: Optional[int] = None,
                               expected_email: Optional[str] = None):
    """Assert that token data has valid structure."""
    required_keys = ["sub", "email", "username", "exp", "iat", "type"]
    for key in required_keys:
        assert key in token_data, f"Missing required token key: {key}"

    if expected_user_id is not None:
        assert token_data["sub"] == str(expected_user_id)

    if expected_email is not None:
        assert token_data["email"] == expected_email

    assert token_data["type"] in ["access", "refresh"]

# Async Test Helpers

async def wait_for_condition(condition_func: Callable[[], bool],
                           timeout: float = 5.0,
                           interval: float = 0.1) -> bool:
    """Wait for a condition to become true."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True
        await asyncio.sleep(interval)

    return False

async def async_retry(operation: Callable,
                     max_attempts: int = 3,
                     delay: float = 0.1):
    """Retry an async operation with exponential backoff."""
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay * (2 ** attempt))

    raise last_exception

# Test Result Helpers

def log_test_result(test_name: str, result: Dict[str, Any]):
    """Log detailed test results for analysis."""
    print(f"\nTest Result: {test_name}")
    print(f"Status: {'PASS' if result.get('success', False) else 'FAIL'}")
    print(f"Duration: {result.get('duration', 0):.3f}s")

    if 'error' in result:
        print(f"Error: {result['error']}")

    if 'metrics' in result:
        print("Metrics:")
        for key, value in result['metrics'].items():
            print(f"  {key}: {value}")

# Cleanup Helpers

async def cleanup_test_data(db_session):
    """Clean up test data from database."""
    # This would contain cleanup logic for test data
    # For now, rely on transaction rollback in conftest.py
    pass

def cleanup_temp_files(temp_dir: str):
    """Clean up temporary files created during testing."""
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

# Export key utilities
__all__ = [
    # Data generators
    "generate_test_user",
    "generate_test_workspace",
    "generate_test_token",
    "generate_auth_headers",

    # Database helpers
    "create_test_user",
    "create_test_workspace",

    # API helpers
    "assert_api_response",
    "assert_api_error",
    "async_assert_api_response",

    # Mock helpers
    "create_mock_redis",
    "create_mock_external_service",
    "mock_external_api_call",

    # Performance helpers
    "time_async_operation",
    "benchmark_operation",

    # Validation helpers
    "validate_jwt_token",
    "assert_valid_token_structure",

    # Async helpers
    "wait_for_condition",
    "async_retry",

    # Result helpers
    "log_test_result",

    # Cleanup helpers
    "cleanup_test_data",
    "cleanup_temp_files"
]
