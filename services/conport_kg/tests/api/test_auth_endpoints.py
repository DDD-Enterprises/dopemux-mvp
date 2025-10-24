#!/usr/bin/env python3
"""
ConPort-KG Auth Endpoints Tests
Phase 1 Week 1 Day 4

Integration tests for authentication API endpoints.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure modules are importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app

# Create test client with clean database for each test
@pytest.fixture(scope="function")
def api_client():
    """Test client with database cleanup"""
    with TestClient(app) as client:
        yield client
        # Cleanup happens via database transaction rollback


@pytest.mark.integration
class TestAppHealth:
    """Test application health endpoints"""

    def test_root_endpoint(self, api_client):
        """Test GET /"""
        response = api_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ConPort-KG 2.0"
        assert data["version"] == "2.0.0"

    def test_health_endpoint(self, api_client):
        """Test GET /health"""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data

    def test_auth_health_endpoint(self, api_client):
        """Test GET /auth/health"""
        response = api_client.get("/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "auth"


@pytest.mark.integration
class TestRegistrationEndpoint:
    """Test POST /auth/register"""

    def test_register_success(self, api_client):
        """Test successful user registration"""
        response = api_client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "MyStr0ng!NewPass#2025$Test",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "password" not in data  # Password not in response
        assert data["is_active"] is True

    def test_register_duplicate_email(self, api_client):
        """Test registration with duplicate email fails"""
        # First registration
        api_client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "MyStr0ng!Dup1#2025$Test",
            },
        )

        # Second registration with same email
        response = api_client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "MyStr0ng!Dup2#2025$Test",
            },
        )

        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    def test_register_invalid_email(self, api_client):
        """Test registration with invalid email format"""
        response = api_client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "username": "user",
                "password": "MyStr0ng!Pass#2025$Test",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self, api_client):
        """Test registration with weak password"""
        response = api_client.post(
            "/auth/register",
            json={"email": "user@example.com", "username": "user", "password": "weak"},
        )

        assert response.status_code == 422  # Pydantic validation (< 12 chars)


@pytest.mark.integration
class TestLoginEndpoint:
    """Test POST /auth/login"""

    @pytest.fixture(autouse=True)
    def setup_user(self, api_client):
        """Create test user before each test"""
        self.client = api_client
        self.client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "MyL0gin!Pass#2025$Test",
            },
        )

    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "MyL0gin!Pass#2025$Test"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = self.client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "password"},
        )

        assert response.status_code == 401

    def test_login_invalid_password(self):
        """Test login with wrong password"""
        response = self.client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "WrongPassword"},
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestProtectedEndpoints:
    """Test endpoints requiring authentication"""

    @pytest.fixture(autouse=True)
    def setup_user(self, api_client):
        """Create and login test user"""
        self.client = api_client

        # Register
        self.client.post(
            "/auth/register",
            json={
                "email": "protected@example.com",
                "username": "protecteduser",
                "password": "MyPr0tected!Pass#2025$Test",
            },
        )

        # Login
        login_response = self.client.post(
            "/auth/login",
            json={"email": "protected@example.com", "password": "MyPr0tected!Pass#2025$Test"},
        )

        self.access_token = login_response.json()["access_token"]
        self.refresh_token = login_response.json()["refresh_token"]

    def test_get_me_success(self):
        """Test GET /auth/me with valid token"""
        response = self.client.get(
            "/auth/me", headers={"Authorization": f"Bearer {self.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protected@example.com"
        assert data["username"] == "protecteduser"

    def test_get_me_no_token(self):
        """Test GET /auth/me without token"""
        response = self.client.get("/auth/me")

        assert response.status_code == 403  # No Authorization header

    def test_get_me_invalid_token(self):
        """Test GET /auth/me with invalid token"""
        response = self.client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_refresh_token_success(self):
        """Test POST /auth/refresh"""
        import time
        time.sleep(1)  # Ensure different iat timestamp

        response = self.client.post("/auth/refresh", params={"refresh_token": self.refresh_token})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # New token should be different (different iat)
        assert data["access_token"] != self.access_token

    def test_logout_success(self):
        """Test POST /auth/logout"""
        response = self.client.post(
            "/auth/logout",
            params={"refresh_token": self.refresh_token},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        assert response.status_code == 204

        # Try to use revoked refresh token
        refresh_response = self.client.post(
            "/auth/refresh", params={"refresh_token": self.refresh_token}
        )

        assert refresh_response.status_code == 401  # Token revoked


@pytest.mark.integration
class TestWorkspaceEndpoints:
    """Test workspace management endpoints"""

    @pytest.fixture(autouse=True)
    def setup_user(self, api_client):
        """Create and login test user"""
        self.client = api_client

        self.client.post(
            "/auth/register",
            json={
                "email": "workspace@example.com",
                "username": "workspaceuser",
                "password": "MyW0rkspace!Pass#2025$Test",
            },
        )

        login_response = self.client.post(
            "/auth/login",
            json={"email": "workspace@example.com", "password": "MyW0rkspace!Pass#2025$Test"},
        )

        self.access_token = login_response.json()["access_token"]

    def test_join_workspace_success(self):
        """Test POST /auth/workspaces (join workspace)"""
        response = self.client.post(
            "/auth/workspaces",
            json={"workspace_id": "/Users/hue/code/test-project", "role": "member"},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["workspace_id"] == "/Users/hue/code/test-project"
        assert data["role"] == "member"

    def test_get_workspaces_success(self):
        """Test GET /auth/workspaces"""
        # Join workspace first
        self.client.post(
            "/auth/workspaces",
            json={"workspace_id": "/workspace1", "role": "member"},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        # Get workspaces
        response = self.client.get(
            "/auth/workspaces", headers={"Authorization": f"Bearer {self.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["workspace_id"] == "/workspace1"

    def test_leave_workspace_success(self):
        """Test DELETE /auth/workspaces/{workspace_id}"""
        # Join first
        self.client.post(
            "/auth/workspaces",
            json={"workspace_id": "/workspace_to_leave", "role": "member"},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        # Leave
        response = self.client.delete(
            "/auth/workspaces//workspace_to_leave",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        assert response.status_code == 204

        # Verify no longer member
        workspaces = self.client.get(
            "/auth/workspaces", headers={"Authorization": f"Bearer {self.access_token}"}
        )
        workspace_ids = [w["workspace_id"] for w in workspaces.json()]
        assert "/workspace_to_leave" not in workspace_ids
