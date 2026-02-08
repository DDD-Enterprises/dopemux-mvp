#!/usr/bin/env python3
"""
ConPort-KG Authentication Service
Part of Phase 1 Security Hardening

User management, authentication, and authorization services.
"""

from typing import Tuple

import os

import logging

logger = logging.getLogger(__name__)

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from .models import User, UserWorkspace, RefreshToken, AuditLog, UserCreate, ROLES
from .jwt_utils import JWTManager
from .password_utils import PasswordManager, PasswordValidationError
from .database import get_db

class AuthenticationError(Exception):
    """Authentication-related errors"""
    pass

class AuthorizationError(Exception):
    """Authorization-related errors"""
    pass

class UserService:
    """User management service"""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Create a new user account.

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            Created user object

        Raises:
            HTTPException: If user creation fails
        """
        try:
            # Validate password strength
            PasswordManager.validate_password_strength(user_data.password)

            # Hash password
            password_hash = PasswordManager.hash_password(user_data.password)

            # Create user
            user = User(
                email=user_data.email.lower(),
                username=user_data.username,
                password_hash=password_hash
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            # Log user creation
            AuditService.log_action(
                db, None, "user.registered",
                "user", str(user.id),
                {"email": user.email, "username": user.username}
            )

            logger.info(f"✅ User created: {user.username} ({user.email})")
            return user

        except PasswordValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {str(e)}"
            )
        except IntegrityError as e:
            db.rollback()
            if "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address already registered"
                )
            elif "username" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User creation failed"
                )
        except Exception as e:
            db.rollback()
            logger.error(f"❌ User creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed"
            )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            User object if authenticated, None otherwise
        """
        try:
            user = db.query(User).filter(
                User.email == email.lower(),
                User.is_active == True
            ).first()

            if not user:
                return None

            if PasswordManager.verify_password(password, user.password_hash):
                # Log successful login
                AuditService.log_action(
                    db, user.id, "user.login",
                    "user", str(user.id),
                    {"email": user.email, "ip_address": None}  # IP logged by middleware
                )
                return user
            else:
                # Log failed login attempt
                AuditService.log_action(
                    db, user.id, "user.login_failed",
                    "user", str(user.id),
                    {"email": user.email, "reason": "invalid_password"}
                )
                return None

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return None

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()

    @staticmethod
    def get_user_with_workspaces(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user with workspace information.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User data with workspaces if found, None otherwise
        """
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        workspaces = []
        for uw in user.workspaces:
            workspaces.append({
                "workspace_id": uw.workspace_id,
                "role": uw.role,
                "permissions": uw.permissions
            })

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "workspaces": workspaces
        }

class WorkspaceService:
    """Workspace permission management"""

    @staticmethod
    def add_user_to_workspace(
        db: Session,
        user_id: int,
        workspace_id: str,
        role: str = "member",
        requesting_user_id: Optional[int] = None
    ) -> UserWorkspace:
        """
        Add user to workspace with specified role.

        Args:
            db: Database session
            user_id: User ID to add
            workspace_id: Workspace ID
            role: User role in workspace
            requesting_user_id: User making the request (for audit)

        Returns:
            UserWorkspace object

        Raises:
            HTTPException: If operation fails
        """
        try:
            # Validate role
            if role not in ROLES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}"
                )

            # Check if user exists
            user = UserService.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check if already in workspace
            existing = db.query(UserWorkspace).filter(
                UserWorkspace.user_id == user_id,
                UserWorkspace.workspace_id == workspace_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already in workspace"
                )

            # Create workspace membership
            workspace_user = UserWorkspace(
                user_id=user_id,
                workspace_id=workspace_id,
                role=role,
                permissions=ROLES[role]["permissions"]
            )

            db.add(workspace_user)
            db.commit()
            db.refresh(workspace_user)

            # Log action
            AuditService.log_action(
                db, requesting_user_id, "workspace.user_added",
                "workspace", workspace_id,
                {"user_id": user_id, "role": role}
            )

            logger.info(f"✅ User {user_id} added to workspace {workspace_id} as {role}")
            return workspace_user

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Add user to workspace error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add user to workspace"
            )

    @staticmethod
    def check_workspace_permission(
        db: Session,
        user_id: int,
        workspace_id: str,
        required_permission: str
    ) -> bool:
        """
        Check if user has required permission in workspace.

        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            required_permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        try:
            workspace_user = db.query(UserWorkspace).filter(
                UserWorkspace.user_id == user_id,
                UserWorkspace.workspace_id == workspace_id
            ).first()

            if not workspace_user:
                return False

            permissions = workspace_user.permissions or {}
            return permissions.get(required_permission, False)

        except Exception as e:
            logger.error(f"❌ Permission check error: {e}")
            return False

class TokenService:
    """JWT token management service"""

    @staticmethod
    def create_token_pair(db: Session, user: User) -> Tuple[str, str]:
        """
        Create access and refresh tokens for user.

        Args:
            db: Database session
            user: User object

        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Create user data for token
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }

        # Create tokens
        access_token, refresh_token = JWTManager.create_token_pair(user_data)

        # Store refresh token hash
        refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=30)  # 30 days

        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at
        )

        db.add(refresh_token_obj)
        db.commit()

        return access_token, refresh_token

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        Refresh access token using refresh token.

        Args:
            db: Database session
            refresh_token: Refresh token string

        Returns:
            Tuple of (new_access_token, new_refresh_token) if valid, None otherwise
        """
        try:
            # Validate refresh token
            user_data = JWTManager.validate_refresh_token(refresh_token)
            if not user_data:
                return None

            # Check if refresh token exists in database
            refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            token_obj = db.query(RefreshToken).filter(
                RefreshToken.token_hash == refresh_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            ).first()

            if not token_obj:
                return None

            # Get user
            user = UserService.get_user_by_id(db, user_data["user_id"])
            if not user:
                return None

            # Revoke old refresh token
            token_obj.revoked = True
            db.commit()

            # Create new token pair
            return TokenService.create_token_pair(db, user)

        except Exception as e:
            logger.error(f"❌ Token refresh error: {e}")
            return None

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str, user_id: int) -> bool:
        """
        Revoke a refresh token.

        Args:
            db: Database session
            refresh_token: Refresh token to revoke
            user_id: User ID for validation

        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            token_obj = db.query(RefreshToken).filter(
                RefreshToken.token_hash == refresh_hash,
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).first()

            if token_obj:
                token_obj.revoked = True
                db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Token revocation error: {e}")
            return False

class AuditService:
    """Security audit logging service"""

    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log an audit event.

        Args:
            db: Database session
            user_id: User performing action (None for system actions)
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional action details
            ip_address: Client IP address
            user_agent: Client user agent
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )

            db.add(audit_log)
            db.commit()

        except Exception as e:
            # Don't fail the main operation due to audit logging failure
            logger.error(f"⚠️ Audit logging failed: {e}")

# Export services
__all__ = [
    "UserService",
    "WorkspaceService",
    "TokenService",
    "AuditService",
    "AuthenticationError",
    "AuthorizationError"
]
