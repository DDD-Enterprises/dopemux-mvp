#!/usr/bin/env python3
"""
ConPort-KG UserService Tests
Phase 1 Week 1 Day 3

Comprehensive testing of authentication and authorization service.
"""

from pathlib import Path

import pytest
from fastapi import HTTPException

# Ensure auth package is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.models import UserCreate
from auth.service import UserService, AuthenticationError, AuthorizationError


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration flow"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_db, user_service, sample_user_create):
        """Test successful user creation"""
        user = await user_service.create_user(test_db, sample_user_create)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.password_hash.startswith("$argon2id$")

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, test_db, user_service, created_test_user
    ):
        """Test that duplicate email is rejected"""
        duplicate_data = UserCreate(
            email=created_test_user.email,  # Duplicate
            username="different",
            password="MyUn1que!DiffPass#2025$Test",  # Unique, non-breached
        )

        with pytest.raises(HTTPException) as exc:
            await user_service.create_user(test_db, duplicate_data)

        assert exc.value.status_code == 400
        assert "email" in str(exc.value.detail).lower()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(
        self, test_db, user_service, created_test_user
    ):
        """Test that duplicate username is rejected"""
        duplicate_data = UserCreate(
            email="different@example.com",
            username=created_test_user.username,  # Duplicate
            password="SecurePass123!@#",
        )

        with pytest.raises(HTTPException) as exc:
            await user_service.create_user(test_db, duplicate_data)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, test_db, user_service):
        """Test that weak password is rejected"""
        # Use 12+ chars but missing complexity (no special char)
        weak_data = UserCreate(
            email="user@example.com",
            username="uniqueuser",
            password="weakpassword123",  # 15 chars but no special char
        )

        with pytest.raises(HTTPException) as exc:
            await user_service.create_user(test_db, weak_data)

        assert exc.value.status_code == 400
        # Should reject due to missing special character
        detail_lower = str(exc.value.detail).lower()
        assert "special character" in detail_lower

    @pytest.mark.asyncio
    async def test_create_user_logs_audit_event(
        self, test_db, user_service, sample_user_create
    ):
        """Test that user creation logs audit event"""
        user = await user_service.create_user(test_db, sample_user_create)

        # Check audit log created
        logs = await user_service.get_audit_logs(
            test_db, user_id=user.id, action="user.created"
        )

        assert len(logs) == 1
        assert logs[0].action == "user.created"
        assert logs[0].details["email"] == user.email


@pytest.mark.auth
class TestUserAuthentication:
    """Test user authentication flow"""

    @pytest.mark.asyncio
    async def test_authenticate_valid_credentials(
        self, test_db, user_service, created_test_user
    ):
        """Test authentication with valid credentials"""
        result = await user_service.authenticate_user(
            test_db, email=created_test_user.email, password="MyUn1que!Test#Pass2025$ConPort"
        )

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 900
        assert result["user"]["id"] == created_test_user.id

    @pytest.mark.asyncio
    async def test_authenticate_invalid_email(self, test_db, user_service):
        """Test authentication with non-existent email"""
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await user_service.authenticate_user(
                test_db, email="nonexistent@example.com", password="password"
            )

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(
        self, test_db, user_service, created_test_user
    ):
        """Test authentication with wrong password"""
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await user_service.authenticate_user(
                test_db, email=created_test_user.email, password="WrongPassword"
            )

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, test_db, user_service, created_test_user):
        """Test that inactive users cannot login"""
        # Disable user
        created_test_user.is_active = False
        test_db.commit()

        with pytest.raises(AuthenticationError, match="disabled"):
            await user_service.authenticate_user(
                test_db, email=created_test_user.email, password="MyUn1que!Test#Pass2025$ConPort"
            )

    @pytest.mark.asyncio
    async def test_authenticate_logs_success(
        self, test_db, user_service, created_test_user
    ):
        """Test that successful login logs audit event"""
        await user_service.authenticate_user(
            test_db, email=created_test_user.email, password="MyUn1que!Test#Pass2025$ConPort"
        )

        logs = await user_service.get_audit_logs(
            test_db, user_id=created_test_user.id, action="login.success"
        )

        assert len(logs) == 1
        assert logs[0].details["method"] == "password"

    @pytest.mark.asyncio
    async def test_authenticate_logs_failure(self, test_db, user_service, created_test_user):
        """Test that failed login logs audit event"""
        try:
            await user_service.authenticate_user(
                test_db, email=created_test_user.email, password="WrongPassword"
            )
        except AuthenticationError:
            pass

        logs = await user_service.get_audit_logs(
            test_db, user_id=created_test_user.id, action="login.failed"
        )

        assert len(logs) == 1
        assert logs[0].details["reason"] == "invalid_password"


@pytest.mark.auth
class TestTokenManagement:
    """Test token refresh and logout"""

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self, test_db, user_service, created_test_user
    ):
        """Test refreshing access token with valid refresh token"""
        import time

        # Login to get tokens
        auth_result = await user_service.authenticate_user(
            test_db, email=created_test_user.email, password="MyUn1que!Test#Pass2025$ConPort"
        )

        refresh_token = auth_result["refresh_token"]

        # Wait 1 second to ensure different iat (issued at) time
        time.sleep(1)

        # Refresh
        result = await user_service.refresh_access_token(test_db, refresh_token)

        assert "access_token" in result
        # Tokens should be different due to different iat timestamp
        assert result["access_token"] != auth_result["access_token"]
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_token(self, test_db, user_service):
        """Test that invalid refresh token is rejected"""
        with pytest.raises(AuthenticationError):
            await user_service.refresh_access_token(test_db, "invalid_token")

    @pytest.mark.asyncio
    async def test_logout_user_success(self, test_db, user_service, created_test_user):
        """Test successful logout (token revocation)"""
        # Login
        auth_result = await user_service.authenticate_user(
            test_db, email=created_test_user.email, password="MyUn1que!Test#Pass2025$ConPort"
        )

        refresh_token = auth_result["refresh_token"]

        # Logout
        await user_service.logout_user(test_db, refresh_token)

        # Try to use revoked token
        with pytest.raises(AuthenticationError, match="revoked"):
            await user_service.refresh_access_token(test_db, refresh_token)

    @pytest.mark.asyncio
    async def test_logout_logs_audit_event(
        self, test_db, user_service, created_test_user
    ):
        """Test that logout logs audit event"""
        auth_result = await user_service.authenticate_user(
            test_db, email=created_test_user.email, password="MyUn1que!Test#Pass2025$ConPort"
        )

        await user_service.logout_user(test_db, auth_result["refresh_token"])

        logs = await user_service.get_audit_logs(
            test_db, user_id=created_test_user.id, action="user.logout"
        )

        assert len(logs) == 1


@pytest.mark.auth
class TestWorkspaceManagement:
    """Test workspace membership management"""

    @pytest.mark.asyncio
    async def test_add_user_to_workspace_success(
        self, test_db, user_service, created_test_user
    ):
        """Test adding user to workspace"""
        workspace_id = "/Users/hue/code/test-project"

        membership = await user_service.add_user_to_workspace(
            test_db,
            user_id=created_test_user.id,
            workspace_id=workspace_id,
            role="member",
        )

        assert membership.user_id == created_test_user.id
        assert membership.workspace_id == workspace_id
        assert membership.role == "member"
        assert "read_decisions" in membership.permissions

    @pytest.mark.asyncio
    async def test_add_user_to_workspace_duplicate(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test that adding user to same workspace twice fails"""
        user, workspace = created_test_user_with_workspace

        with pytest.raises(HTTPException) as exc:
            await user_service.add_user_to_workspace(
                test_db,
                user_id=user.id,
                workspace_id=workspace.workspace_id,
                role="member",
            )

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_remove_user_from_workspace_success(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test removing user from workspace"""
        user, workspace = created_test_user_with_workspace

        await user_service.remove_user_from_workspace(
            test_db, user_id=user.id, workspace_id=workspace.workspace_id
        )

        # Verify removed
        workspaces = await user_service.get_user_workspaces(test_db, user.id)
        assert len(workspaces) == 0

    @pytest.mark.asyncio
    async def test_get_user_workspaces(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test getting user's workspaces"""
        user, workspace = created_test_user_with_workspace

        workspaces = await user_service.get_user_workspaces(test_db, user.id)

        assert len(workspaces) == 1
        assert workspaces[0]["workspace_id"] == workspace.workspace_id
        assert workspaces[0]["role"] == "member"

    @pytest.mark.asyncio
    async def test_update_user_role_success(
        self, test_db, user_service, created_test_user_with_workspace, admin_user
    ):
        """Test updating user role in workspace"""
        user, workspace = created_test_user_with_workspace

        updated = await user_service.update_user_role(
            test_db,
            user_id=user.id,
            workspace_id=workspace.workspace_id,
            new_role="admin",
            updated_by_user_id=admin_user.id,
        )

        assert updated.role == "admin"
        assert updated.permissions["manage_users"] is True


@pytest.mark.auth
class TestPermissionChecking:
    """Test permission checking methods"""

    @pytest.mark.asyncio
    async def test_check_workspace_permission_has_permission(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test permission check when user has permission"""
        user, workspace = created_test_user_with_workspace

        can_read = await user_service.check_workspace_permission(
            test_db,
            user_id=user.id,
            workspace_id=workspace.workspace_id,
            permission="read_decisions",
        )

        assert can_read is True

    @pytest.mark.asyncio
    async def test_check_workspace_permission_lacks_permission(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test permission check when user lacks permission"""
        user, workspace = created_test_user_with_workspace

        can_delete = await user_service.check_workspace_permission(
            test_db,
            user_id=user.id,
            workspace_id=workspace.workspace_id,
            permission="delete_decisions",
        )

        assert can_delete is False  # Member can't delete

    @pytest.mark.asyncio
    async def test_check_workspace_permission_not_member(
        self, test_db, user_service, created_test_user
    ):
        """Test permission check when user not member of workspace"""
        can_read = await user_service.check_workspace_permission(
            test_db,
            user_id=created_test_user.id,
            workspace_id="/some/other/workspace",
            permission="read_decisions",
        )

        assert can_read is False

    @pytest.mark.asyncio
    async def test_require_workspace_permission_authorized(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test require_workspace_permission when authorized"""
        user, workspace = created_test_user_with_workspace

        # Should not raise exception
        await user_service.require_workspace_permission(
            test_db,
            user_id=user.id,
            workspace_id=workspace.workspace_id,
            permission="read_decisions",
        )

    @pytest.mark.asyncio
    async def test_require_workspace_permission_unauthorized(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test require_workspace_permission when not authorized"""
        user, workspace = created_test_user_with_workspace

        with pytest.raises(AuthorizationError, match="lacks.*permission"):
            await user_service.require_workspace_permission(
                test_db,
                user_id=user.id,
                workspace_id=workspace.workspace_id,
                permission="delete_workspace",  # Member can't delete workspace
            )

    @pytest.mark.asyncio
    async def test_get_user_role_success(
        self, test_db, user_service, created_test_user_with_workspace
    ):
        """Test getting user's role in workspace"""
        user, workspace = created_test_user_with_workspace

        role = await user_service.get_user_role(
            test_db, user_id=user.id, workspace_id=workspace.workspace_id
        )

        assert role == "member"

    @pytest.mark.asyncio
    async def test_get_user_role_not_member(self, test_db, user_service, created_test_user):
        """Test getting role when not a member"""
        role = await user_service.get_user_role(
            test_db, user_id=created_test_user.id, workspace_id="/other/workspace"
        )

        assert role is None


@pytest.mark.auth
class TestUserManagement:
    """Test user CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, test_db, user_service, created_test_user
    ):
        """Test getting user by ID"""
        user = await user_service.get_user_by_id(test_db, created_test_user.id)

        assert user is not None
        assert user.id == created_test_user.id
        assert user.email == created_test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, test_db, user_service):
        """Test getting non-existent user"""
        user = await user_service.get_user_by_id(test_db, 99999)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(
        self, test_db, user_service, created_test_user
    ):
        """Test getting user by email"""
        user = await user_service.get_user_by_email(test_db, created_test_user.email)

        assert user is not None
        assert user.email == created_test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_email_case_insensitive(
        self, test_db, user_service, created_test_user
    ):
        """Test that email lookup is case-insensitive"""
        user = await user_service.get_user_by_email(
            test_db, created_test_user.email.upper()
        )

        assert user is not None
        assert user.email == created_test_user.email

    @pytest.mark.asyncio
    async def test_update_user_success(self, test_db, user_service, created_test_user):
        """Test updating user account"""
        updated_user = await user_service.update_user(
            test_db, user_id=created_test_user.id, update_data={"username": "newusername"}
        )

        assert updated_user.username == "newusername"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, test_db, user_service):
        """Test updating non-existent user"""
        with pytest.raises(HTTPException) as exc:
            await user_service.update_user(
                test_db, user_id=99999, update_data={"username": "new"}
            )

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_success(self, test_db, user_service, created_test_user):
        """Test deleting user (soft delete)"""
        await user_service.delete_user(test_db, user_id=created_test_user.id)

        # Verify soft deleted (is_active = False)
        user = await user_service.get_user_by_id(test_db, created_test_user.id)
        assert user.is_active is False


@pytest.mark.auth
class TestUtilityMethods:
    """Test utility methods"""

    @pytest.mark.asyncio
    async def test_validate_access_token_valid(self, user_service):
        """Test validating valid access token"""
        # Use service's own jwt_manager (same keys)
        token = user_service.jwt_manager.create_access_token({
            "sub": "123",
            "email": "test@example.com",
            "username": "test"
        })

        payload = await user_service.validate_access_token(token)

        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_validate_access_token_invalid(self, user_service):
        """Test validating invalid access token"""
        with pytest.raises(HTTPException) as exc:
            await user_service.validate_access_token("invalid_token")

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_from_token_success(
        self, test_db, user_service, created_test_user
    ):
        """Test getting current user from valid token"""
        # Use service's jwt_manager (same keys)
        token = user_service.jwt_manager.create_access_token({
            "sub": str(created_test_user.id),
            "email": created_test_user.email,
            "username": created_test_user.username,
        })

        user = await user_service.get_current_user_from_token(test_db, token)

        assert user.id == created_test_user.id
        assert user.email == created_test_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_from_token_user_not_found(
        self, test_db, user_service
    ):
        """Test getting user from token when user deleted"""
        # Use service's jwt_manager
        token = user_service.jwt_manager.create_access_token({
            "sub": "99999",
            "email": "deleted@example.com",
            "username": "deleted"
        })

        with pytest.raises(HTTPException) as exc:
            await user_service.get_current_user_from_token(test_db, token)

        assert exc.value.status_code == 404
