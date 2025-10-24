#!/usr/bin/env python3
"""
ConPort-KG Authentication Service
Phase 1 Week 1 Day 3

User management, authentication, and authorization services.
Integrates JWT, password security, and database models.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .jwt_utils import JWTManager
from .models import (
    ROLE_PERMISSIONS,
    AuditLog,
    RefreshToken,
    User,
    UserCreate,
    UserWorkspace,
    get_role_permissions,
)
from .password_utils import PasswordManager, PasswordValidationError


class AuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class AuthorizationError(Exception):
    """Raised when user lacks required permissions"""

    pass


class UserService:
    """
    User management and authentication service.

    Provides complete authentication flows:
    - User registration with password validation
    - Login with JWT token generation
    - Token refresh
    - Logout (token revocation)
    - Workspace membership management
    - Permission checking
    - Audit logging
    """

    def __init__(self):
        """Initialize service with JWT and password managers"""
        self.jwt_manager = JWTManager()
        self.password_manager = PasswordManager()

    # ========================================================================
    # User Registration
    # ========================================================================

    async def create_user(self, db: Session, user_data: UserCreate) -> User:
        """
        Create new user account.

        Validates password strength, checks for breaches, and creates user
        with hashed password. Logs audit event.

        Args:
            db: Database session
            user_data: User creation data (email, username, password)

        Returns:
            Created user object

        Raises:
            HTTPException: If user creation fails (duplicate email/username, weak password)
            PasswordValidationError: If password doesn't meet requirements

        Example:
            user = await service.create_user(db, UserCreate(
                email="user@example.com",
                username="johndoe",
                password="SecurePass123!"
            ))
        """
        try:
            # Step 1: Validate password strength
            self.password_manager.validate_password_strength(user_data.password)

            # Step 2: Check for breached password
            is_breached = await self.password_manager.check_password_breach(
                user_data.password
            )
            if is_breached:
                raise PasswordValidationError(
                    "Password found in breach database (HaveIBeenPwned). Please choose a different password."
                )

            # Step 3: Hash password
            password_hash = self.password_manager.hash_password(user_data.password)

            # Step 4: Create user
            user = User(
                email=user_data.email,
                username=user_data.username,
                password_hash=password_hash,
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            # Step 5: Audit log
            self._log_audit(
                db,
                user_id=user.id,
                action="user.created",
                details={"email": user.email, "username": user.username},
            )

            return user

        except IntegrityError as e:
            db.rollback()
            # Duplicate email or username
            error_msg = str(e)
            if "email" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )
            elif "username" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this username already exists",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User creation failed due to database constraint",
                )

        except PasswordValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            )

    # ========================================================================
    # User Authentication
    # ========================================================================

    async def authenticate_user(
        self,
        db: Session,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Authenticate user and return JWT tokens.

        Validates credentials, generates access and refresh tokens,
        stores refresh token in database for revocation capability.

        Args:
            db: Database session
            email: User email
            password: User password (plaintext)
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging

        Returns:
            Dictionary with:
            - access_token: JWT access token (15min)
            - refresh_token: JWT refresh token (30 days)
            - token_type: "bearer"
            - expires_in: Seconds until access token expires
            - user: User data (UserResponse format)

        Raises:
            AuthenticationError: If credentials invalid or account disabled

        Example:
            result = await service.authenticate_user(
                db, "user@example.com", "password123"
            )
            access_token = result["access_token"]
        """
        # Step 1: Get user by email
        user = db.query(User).filter(User.email == email.lower()).first()

        if not user:
            # User not found - log failed attempt
            self._log_audit(
                db,
                user_id=None,
                action="login.failed",
                details={"email": email, "reason": "user_not_found"},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthenticationError("Invalid email or password")

        # Step 2: Check if account is active
        if not user.is_active:
            self._log_audit(
                db,
                user_id=user.id,
                action="login.failed",
                details={"reason": "account_disabled"},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthenticationError("User account is disabled")

        # Step 3: Verify password
        is_valid = self.password_manager.verify_password(password, user.password_hash)

        if not is_valid:
            self._log_audit(
                db,
                user_id=user.id,
                action="login.failed",
                details={"reason": "invalid_password"},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthenticationError("Invalid email or password")

        # Step 4: Check if password needs rehashing (parameters upgraded)
        if self.password_manager.check_needs_rehash(user.password_hash):
            # Rehash with new parameters
            user.password_hash = self.password_manager.hash_password(password)
            db.commit()

        # Step 5: Create access token
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
        }
        access_token = self.jwt_manager.create_access_token(access_token_data)

        # Step 6: Create refresh token
        refresh_token_data = {"sub": str(user.id)}
        refresh_token = self.jwt_manager.create_refresh_token(refresh_token_data)

        # Step 7: Store refresh token (hashed) in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.add(refresh_token_obj)
        db.commit()

        # Step 8: Audit log successful login
        self._log_audit(
            db,
            user_id=user.id,
            action="login.success",
            details={"method": "password"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Step 9: Return tokens and user data
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,  # 15 minutes in seconds
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "created_at": user.created_at,
            },
        }

    # ========================================================================
    # Token Management
    # ========================================================================

    async def refresh_access_token(
        self, db: Session, refresh_token: str
    ) -> Dict[str, str]:
        """
        Refresh access token using valid refresh token.

        Validates refresh token, checks if revoked, and issues new access token.
        Optionally rotates refresh token for added security.

        Args:
            db: Database session
            refresh_token: JWT refresh token

        Returns:
            Dictionary with new access_token and expires_in

        Raises:
            AuthenticationError: If refresh token invalid, expired, or revoked

        Example:
            result = await service.refresh_access_token(db, refresh_token)
            new_access_token = result["access_token"]
        """
        try:
            # Step 1: Validate refresh token JWT signature and expiry
            payload = self.jwt_manager.validate_token(refresh_token, "refresh")
            user_id = int(payload["sub"])

        except Exception as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}")

        # Step 2: Check if token is in database (not revoked)
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        token_obj = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_id,
            )
            .first()
        )

        if not token_obj:
            raise AuthenticationError("Refresh token not found or already used")

        if token_obj.revoked:
            # Token was revoked (logout)
            self._log_audit(
                db,
                user_id=user_id,
                action="token.refresh.failed",
                details={"reason": "token_revoked"},
            )
            raise AuthenticationError("Refresh token has been revoked")

        if token_obj.is_expired:
            # Token expired
            self._log_audit(
                db,
                user_id=user_id,
                action="token.refresh.failed",
                details={"reason": "token_expired"},
            )
            raise AuthenticationError("Refresh token has expired")

        # Step 3: Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            raise AuthenticationError("User account not found or disabled")

        # Step 4: Create new access token
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
        }
        new_access_token = self.jwt_manager.create_access_token(access_token_data)

        # Step 5: Audit log
        self._log_audit(
            db, user_id=user.id, action="token.refreshed", details={"method": "refresh"}
        )

        return {"access_token": new_access_token, "token_type": "bearer", "expires_in": 900}

    async def logout_user(self, db: Session, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.

        Marks refresh token as revoked in database, preventing further use.

        Args:
            db: Database session
            refresh_token: JWT refresh token to revoke

        Raises:
            AuthenticationError: If token not found

        Example:
            await service.logout_user(db, refresh_token)
        """
        # Hash token
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        # Find and revoke
        token_obj = (
            db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        )

        if not token_obj:
            raise AuthenticationError("Refresh token not found")

        # Revoke token
        token_obj.revoked = True
        db.commit()

        # Audit log
        self._log_audit(
            db, user_id=token_obj.user_id, action="user.logout", details={"method": "token_revocation"}
        )

    # ========================================================================
    # User Management
    # ========================================================================

    async def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object or None if not found
        """
        return db.query(User).filter(User.id == user_id).first()

    async def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email (case-insensitive)

        Returns:
            User object or None if not found
        """
        return db.query(User).filter(User.email == email.lower()).first()

    async def update_user(
        self, db: Session, user_id: int, update_data: Dict[str, Any]
    ) -> User:
        """
        Update user account.

        Args:
            db: Database session
            user_id: User ID to update
            update_data: Fields to update

        Returns:
            Updated user object

        Raises:
            HTTPException: If user not found

        Example:
            user = await service.update_user(db, 123, {"username": "newname"})
        """
        user = await self.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update allowed fields
        allowed_fields = ["username", "email", "is_active"]
        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(user, field, value)

        db.commit()
        db.refresh(user)

        # Audit log
        self._log_audit(
            db,
            user_id=user.id,
            action="user.updated",
            details={"updated_fields": list(update_data.keys())},
        )

        return user

    async def delete_user(self, db: Session, user_id: int) -> None:
        """
        Delete user account (soft delete - mark inactive).

        Args:
            db: Database session
            user_id: User ID to delete

        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Soft delete (mark inactive)
        user.is_active = False
        db.commit()

        # Audit log
        self._log_audit(
            db, user_id=user.id, action="user.deleted", details={"soft_delete": True}
        )

    # ========================================================================
    # Workspace Management
    # ========================================================================

    async def add_user_to_workspace(
        self,
        db: Session,
        user_id: int,
        workspace_id: str,
        role: str = "member",
        added_by_user_id: Optional[int] = None,
    ) -> UserWorkspace:
        """
        Add user to workspace with specified role.

        Args:
            db: Database session
            user_id: User ID to add
            workspace_id: Workspace ID (absolute path)
            role: Role to assign (owner, admin, member, viewer)
            added_by_user_id: User ID who is adding (for audit)

        Returns:
            UserWorkspace object

        Raises:
            HTTPException: If user not found or already in workspace
            AuthorizationError: If added_by user lacks manage_users permission

        Example:
            uw = await service.add_user_to_workspace(
                db, user_id=123, workspace_id="/code/project", role="member"
            )
        """
        # Step 1: Verify user exists
        user = await self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Step 2: Check if user already in workspace
        existing = (
            db.query(UserWorkspace)
            .filter(
                UserWorkspace.user_id == user_id,
                UserWorkspace.workspace_id == workspace_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already member of this workspace",
            )

        # Step 3: Check authorization (if added_by specified)
        if added_by_user_id:
            can_manage = await self.check_workspace_permission(
                db, added_by_user_id, workspace_id, "manage_users"
            )
            if not can_manage:
                raise AuthorizationError(
                    "You don't have permission to manage users in this workspace"
                )

        # Step 4: Get default permissions for role
        permissions = get_role_permissions(role)

        # Step 5: Create workspace membership
        user_workspace = UserWorkspace(
            user_id=user_id,
            workspace_id=workspace_id,
            role=role,
            permissions=permissions,
        )

        db.add(user_workspace)
        db.commit()
        db.refresh(user_workspace)

        # Step 6: Audit log
        self._log_audit(
            db,
            user_id=added_by_user_id or user_id,
            action="workspace.user_added",
            resource_type="workspace",
            resource_id=workspace_id,
            details={
                "added_user_id": user_id,
                "role": role,
                "added_by": added_by_user_id,
            },
        )

        return user_workspace

    async def remove_user_from_workspace(
        self,
        db: Session,
        user_id: int,
        workspace_id: str,
        removed_by_user_id: Optional[int] = None,
    ) -> None:
        """
        Remove user from workspace.

        Args:
            db: Database session
            user_id: User ID to remove
            workspace_id: Workspace ID
            removed_by_user_id: User ID who is removing (for authorization check)

        Raises:
            HTTPException: If membership not found
            AuthorizationError: If removed_by user lacks manage_users permission
        """
        # Check authorization
        if removed_by_user_id and removed_by_user_id != user_id:
            can_manage = await self.check_workspace_permission(
                db, removed_by_user_id, workspace_id, "manage_users"
            )
            if not can_manage:
                raise AuthorizationError(
                    "You don't have permission to remove users from this workspace"
                )

        # Find and delete membership
        user_workspace = (
            db.query(UserWorkspace)
            .filter(
                UserWorkspace.user_id == user_id,
                UserWorkspace.workspace_id == workspace_id,
            )
            .first()
        )

        if not user_workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this workspace",
            )

        db.delete(user_workspace)
        db.commit()

        # Audit log
        self._log_audit(
            db,
            user_id=removed_by_user_id or user_id,
            action="workspace.user_removed",
            resource_type="workspace",
            resource_id=workspace_id,
            details={"removed_user_id": user_id, "removed_by": removed_by_user_id},
        )

    async def get_user_workspaces(
        self, db: Session, user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all workspaces for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of workspace dictionaries with role and permissions

        Example:
            workspaces = await service.get_user_workspaces(db, 123)
            # Returns: [{"workspace_id": "/code/project", "role": "member", ...}]
        """
        memberships = (
            db.query(UserWorkspace).filter(UserWorkspace.user_id == user_id).all()
        )

        return [
            {
                "workspace_id": m.workspace_id,
                "role": m.role,
                "permissions": m.permissions,
                "created_at": m.created_at,
            }
            for m in memberships
        ]

    async def update_user_role(
        self,
        db: Session,
        user_id: int,
        workspace_id: str,
        new_role: str,
        updated_by_user_id: Optional[int] = None,
    ) -> UserWorkspace:
        """
        Update user's role in workspace.

        Args:
            db: Database session
            user_id: User ID to update
            workspace_id: Workspace ID
            new_role: New role (owner, admin, member, viewer)
            updated_by_user_id: User ID making the change

        Returns:
            Updated UserWorkspace object

        Raises:
            HTTPException: If membership not found
            AuthorizationError: If updater lacks manage_users permission
        """
        # Check authorization
        if updated_by_user_id:
            can_manage = await self.check_workspace_permission(
                db, updated_by_user_id, workspace_id, "manage_users"
            )
            if not can_manage:
                raise AuthorizationError(
                    "You don't have permission to change user roles"
                )

        # Get membership
        membership = (
            db.query(UserWorkspace)
            .filter(
                UserWorkspace.user_id == user_id,
                UserWorkspace.workspace_id == workspace_id,
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User workspace membership not found",
            )

        # Update role and permissions
        old_role = membership.role
        membership.role = new_role
        membership.permissions = get_role_permissions(new_role)
        db.commit()
        db.refresh(membership)

        # Audit log
        self._log_audit(
            db,
            user_id=updated_by_user_id or user_id,
            action="workspace.role_changed",
            resource_type="workspace",
            resource_id=workspace_id,
            details={
                "target_user_id": user_id,
                "old_role": old_role,
                "new_role": new_role,
                "updated_by": updated_by_user_id,
            },
        )

        return membership

    # ========================================================================
    # Permission Checking
    # ========================================================================

    async def check_workspace_permission(
        self, db: Session, user_id: int, workspace_id: str, permission: str
    ) -> bool:
        """
        Check if user has specific permission in workspace.

        Args:
            db: Database session
            user_id: User ID to check
            workspace_id: Workspace ID
            permission: Permission key (e.g., "write_decisions", "manage_users")

        Returns:
            True if user has permission, False otherwise

        Example:
            can_write = await service.check_workspace_permission(
                db, user_id=123, workspace_id="/code/project", permission="write_decisions"
            )
        """
        # Get user's workspace membership
        membership = (
            db.query(UserWorkspace)
            .filter(
                UserWorkspace.user_id == user_id,
                UserWorkspace.workspace_id == workspace_id,
            )
            .first()
        )

        if not membership:
            return False  # Not a member

        # Check permission in custom permissions JSONB
        return membership.permissions.get(permission, False)

    async def require_workspace_permission(
        self, db: Session, user_id: int, workspace_id: str, permission: str
    ) -> None:
        """
        Require user to have permission (raises exception if not).

        Args:
            db: Database session
            user_id: User ID to check
            workspace_id: Workspace ID
            permission: Required permission

        Raises:
            AuthorizationError: If user lacks permission

        Example:
            await service.require_workspace_permission(
                db, user_id=123, workspace_id="/code/project", permission="delete_decisions"
            )
            # Continues if authorized, raises AuthorizationError if not
        """
        has_permission = await self.check_workspace_permission(
            db, user_id, workspace_id, permission
        )

        if not has_permission:
            raise AuthorizationError(
                f"User {user_id} lacks '{permission}' permission in workspace {workspace_id}"
            )

    async def get_user_role(
        self, db: Session, user_id: int, workspace_id: str
    ) -> Optional[str]:
        """
        Get user's role in workspace.

        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID

        Returns:
            Role string (owner/admin/member/viewer) or None if not a member
        """
        membership = (
            db.query(UserWorkspace)
            .filter(
                UserWorkspace.user_id == user_id,
                UserWorkspace.workspace_id == workspace_id,
            )
            .first()
        )

        return membership.role if membership else None

    # ========================================================================
    # Audit Logging
    # ========================================================================

    def _log_audit(
        self,
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log security event to audit log.

        Internal method called by all security-relevant operations.

        Args:
            db: Database session
            user_id: User ID (None for anonymous events)
            action: Action performed (e.g., "login.success", "user.created")
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional event details (JSONB)
            ip_address: Client IP address
            user_agent: Client user agent
        """
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(audit)
        db.commit()

    async def get_audit_logs(
        self,
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Query audit logs.

        Args:
            db: Database session
            user_id: Filter by user ID (optional)
            action: Filter by action (optional)
            limit: Maximum records to return

        Returns:
            List of AuditLog objects

        Example:
            # Get all login attempts for user 123
            logs = await service.get_audit_logs(db, user_id=123, action="login.failed")
        """
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if action:
            query = query.filter(AuditLog.action == action)

        query = query.order_by(AuditLog.created_at.desc()).limit(limit)

        return query.all()

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """
        Validate access token and return payload.

        Convenience method for middleware/dependencies.

        Args:
            token: JWT access token

        Returns:
            Token payload (sub, email, username, etc.)

        Raises:
            HTTPException: If token invalid or expired
        """
        try:
            payload = self.jwt_manager.validate_token(token, "access")
            return payload
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_current_user_from_token(
        self, db: Session, token: str
    ) -> User:
        """
        Get current user from access token.

        Validates token and returns user object.

        Args:
            db: Database session
            token: JWT access token

        Returns:
            User object

        Raises:
            HTTPException: If token invalid or user not found

        Example:
            user = await service.get_current_user_from_token(db, token)
        """
        payload = await self.validate_access_token(token)
        user_id = int(payload["sub"])

        user = await self.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
            )

        return user


# ============================================================================
# Convenience Functions for FastAPI
# ============================================================================


def get_user_service() -> UserService:
    """
    FastAPI dependency for UserService.

    Usage:
        @app.post("/register")
        async def register(
            user_data: UserCreate,
            service: UserService = Depends(get_user_service),
            db: Session = Depends(get_db_dependency)
        ):
            user = await service.create_user(db, user_data)
            return user
    """
    return UserService()
