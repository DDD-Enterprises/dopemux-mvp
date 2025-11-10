import os

import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_auth_bypass_development_mode():
    """
    Test that authentication is bypassed when no API key is set.
    """
    # Simulate development mode (no TASK_ORCHESTRATOR_API_KEY set)
    os.environ.pop("TASK_ORCHESTRATOR_API_KEY", None)

    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert "tasks" in response.json()


def test_auth_with_valid_key():
    """
    Test authentication with valid API key.
    """
    # Set valid API key
    valid_key = "test-valid-key"
    os.environ["TASK_ORCHESTRATOR_API_KEY"] = valid_key

    # Restart app to pick up environment change (in real test, would use dependency override)
    # For simplicity, we'll test the verify_api_key function directly
    from auth import verify_api_key

    # This would be called by the dependency
    # In practice, FastAPI would handle this
    assert verify_api_key(valid_key) == valid_key


def test_auth_with_invalid_key():
    """
    Test authentication with invalid API key.
    """
    os.environ["TASK_ORCHESTRATOR_API_KEY"] = "valid-key"

    from auth import verify_api_key

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("invalid-key")

    assert exc_info.value.status_code == 403
    assert "Invalid API key" in exc_info.value.detail


def test_auth_missing_key():
    """
    Test authentication with missing API key.
    """
    os.environ["TASK_ORCHESTRATOR_API_KEY"] = "valid-key"

    from auth import verify_api_key

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(None)

    assert exc_info.value.status_code == 401
    assert "Missing API key" in exc_info.value.detail
