#!/usr/bin/env python3
"""
ConPort-KG Models Tests
Phase 1 Week 1 Day 2

Test SQLAlchemy models and Pydantic schemas.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure auth package is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.models import (
    ROLE_PERMISSIONS,
    VALID_ROLES,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserWorkspace,
    WorkspaceCreate,
    get_role_permissions,
)


class TestUserModel:
    """Test User SQLAlchemy model"""

    def test_user_model_creation(self):
        """Test creating User model instance"""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="argon2id$test_hash",
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash == "argon2id$test_hash"
        # Note: is_active defaults applied when persisted to DB, not on model instantiation
        assert user.id is None  # Not persisted yet

    def test_user_model_repr(self):
        """Test User model string representation"""
        user = User(id=1, email="test@example.com", username="testuser", password_hash="hash")

        repr_str = repr(user)
        assert "User" in repr_str
        assert "id=1" in repr_str
        assert "test@example.com" in repr_str


class TestUserWorkspaceModel:
    """Test UserWorkspace SQLAlchemy model"""

    def test_user_workspace_creation(self):
        """Test creating UserWorkspace model"""
        uw = UserWorkspace(
            user_id=1, workspace_id="/Users/hue/code/dopemux-mvp", role="member"
        )

        assert uw.user_id == 1
        assert uw.workspace_id == "/Users/hue/code/dopemux-mvp"
        assert uw.role == "member"
        # Note: permissions default applied when persisted to DB

    def test_user_workspace_custom_permissions(self):
        """Test UserWorkspace with custom permissions"""
        permissions = {"read_decisions": True, "write_decisions": False}

        uw = UserWorkspace(
            user_id=1,
            workspace_id="/workspace",
            role="viewer",
            permissions=permissions,
        )

        assert uw.permissions == permissions


class TestPydanticSchemas:
    """Test Pydantic validation schemas"""

    def test_user_create_valid(self):
        """Test UserCreate with valid data"""
        data = {
            "email": "user@example.com",
            "username": "validuser",
            "password": "SecurePass123!@#",
        }

        user_create = UserCreate(**data)
        assert user_create.email == "user@example.com"
        assert user_create.username == "validuser"

    def test_user_create_invalid_email(self):
        """Test UserCreate rejects invalid email"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email", username="user", password="SecurePass123!@#"
            )

    def test_user_create_short_username(self):
        """Test UserCreate rejects short username"""
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", username="ab", password="SecurePass123!@#")

    def test_user_create_invalid_username_chars(self):
        """Test UserCreate rejects special chars in username"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="user@example.com",
                username="user@name",  # @ not allowed
                password="SecurePass123!@#",
            )

    def test_user_create_reserved_username(self):
        """Test UserCreate rejects reserved usernames"""
        reserved = ["admin", "root", "system"]

        for username in reserved:
            with pytest.raises(ValidationError, match="reserved"):
                UserCreate(
                    email="user@example.com",
                    username=username,
                    password="SecurePass123!@#",
                )

    def test_user_login_valid(self):
        """Test UserLogin schema"""
        login = UserLogin(email="user@example.com", password="password123")

        assert login.email == "user@example.com"
        assert login.password == "password123"

    def test_workspace_create_valid_role(self):
        """Test WorkspaceCreate with valid role"""
        workspace = WorkspaceCreate(workspace_id="/workspace", role="admin")

        assert workspace.workspace_id == "/workspace"
        assert workspace.role == "admin"

    def test_workspace_create_invalid_role(self):
        """Test WorkspaceCreate rejects invalid role"""
        with pytest.raises(ValidationError, match="owner, admin, member, viewer"):
            WorkspaceCreate(workspace_id="/workspace", role="superuser")


class TestRolePermissions:
    """Test role permission mappings"""

    def test_valid_roles_constant(self):
        """Test VALID_ROLES contains expected roles"""
        assert "owner" in VALID_ROLES
        assert "admin" in VALID_ROLES
        assert "member" in VALID_ROLES
        assert "viewer" in VALID_ROLES
        assert len(VALID_ROLES) == 4

    def test_get_role_permissions_owner(self):
        """Test owner role has all permissions"""
        perms = get_role_permissions("owner")

        assert perms["read_decisions"] is True
        assert perms["write_decisions"] is True
        assert perms["delete_decisions"] is True
        assert perms["manage_users"] is True
        assert perms["manage_workspace"] is True
        assert perms["delete_workspace"] is True

    def test_get_role_permissions_viewer(self):
        """Test viewer role has read-only permissions"""
        perms = get_role_permissions("viewer")

        assert perms["read_decisions"] is True
        assert perms["write_decisions"] is False
        assert perms["delete_decisions"] is False
        assert perms["read_progress"] is True
        assert perms["write_progress"] is False
        assert perms["manage_users"] is False

    def test_get_role_permissions_invalid_defaults_to_viewer(self):
        """Test invalid role returns viewer permissions (safe default)"""
        perms = get_role_permissions("invalid_role")

        # Should return viewer permissions
        viewer_perms = get_role_permissions("viewer")
        assert perms == viewer_perms

    def test_role_permissions_has_all_roles(self):
        """Test ROLE_PERMISSIONS dict contains all valid roles"""
        for role in VALID_ROLES:
            assert role in ROLE_PERMISSIONS, f"Role {role} missing from ROLE_PERMISSIONS"

    def test_member_cannot_delete(self):
        """Test member role has limited delete permissions"""
        perms = get_role_permissions("member")

        assert perms["write_decisions"] is True  # Can create
        assert perms["delete_decisions"] is False  # Can't delete
        assert perms["manage_users"] is False  # Can't manage users

    def test_admin_can_manage_users_not_workspace(self):
        """Test admin can manage users but not workspace"""
        perms = get_role_permissions("admin")

        assert perms["manage_users"] is True
        assert perms["manage_workspace"] is False
        assert perms["delete_workspace"] is False
