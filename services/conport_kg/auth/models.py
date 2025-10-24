#!/usr/bin/env python3
"""
ConPort-KG Authentication Models
Phase 1 Week 1 Day 2

SQLAlchemy ORM models and Pydantic schemas for user management,
workspace membership, and authentication.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# SQLAlchemy base for ORM models
Base = declarative_base()

# ============================================================================
# SQLAlchemy ORM Models (Database Tables)
# ============================================================================


class User(Base):
    """
    User account model.

    Represents an authenticated user who can access one or more workspaces.
    Passwords are hashed with Argon2id, never stored plaintext.
    """

    __tablename__ = "users"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workspaces = relationship(
        "UserWorkspace", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class UserWorkspace(Base):
    """
    User workspace membership with role-based permissions.

    Links users to workspaces with specific roles:
    - owner: Full control (add/remove users, delete workspace)
    - admin: Manage content (create/edit/delete decisions, tasks)
    - member: Create and edit own content
    - viewer: Read-only access

    Permissions JSONB field allows fine-grained custom permissions.
    """

    __tablename__ = "user_workspaces"

    # Composite primary key (user_id, workspace_id)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    workspace_id = Column(String(255), primary_key=True)

    # Role and permissions
    role = Column(String(50), default="member", nullable=False)
    permissions = Column(JSON, default=dict, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="workspaces")

    def __repr__(self) -> str:
        return f"<UserWorkspace(user_id={self.user_id}, workspace_id={self.workspace_id}, role={self.role})>"


class RefreshToken(Base):
    """
    JWT refresh token storage for rotation and revocation.

    Refresh tokens are long-lived (30 days) and stored hashed in database.
    Can be revoked for logout or security incidents.
    """

    __tablename__ = "refresh_tokens"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)"""
        return not self.revoked and not self.is_expired


class AuditLog(Base):
    """
    Security audit log for tracking authentication and authorization events.

    Logs all security-relevant events:
    - User registration/login/logout
    - Failed authentication attempts
    - Permission changes
    - Workspace access
    - Token operations

    Supports compliance requirements (GDPR, SOC2, etc.)
    """

    __tablename__ = "audit_logs"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Event details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)  # Support IPv6 (39 chars + formatting)
    user_agent = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"


# ============================================================================
# Pydantic Schemas (API Request/Response Validation)
# ============================================================================

# Valid role values
VALID_ROLES = ["owner", "admin", "member", "viewer"]


class UserCreate(BaseModel):
    """
    Schema for user registration.

    Validates:
    - Email format (RFC 5322)
    - Username alphanumeric (allows _ and -)
    - Password strength (validated by PasswordManager)
    """

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=12)

    @validator("username")
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username is alphanumeric with underscores/hyphens"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, underscores, and hyphens"
            )
        return v

    @validator("username")
    def username_not_reserved(cls, v: str) -> str:
        """Prevent reserved usernames"""
        reserved = ["admin", "root", "system", "api", "auth", "conport"]
        if v.lower() in reserved:
            raise ValueError(f"Username '{v}' is reserved")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecurePass123!@#",
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "SecurePass123!@#"}
        }


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.

    Excludes password_hash for security.
    """

    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True,
                "created_at": "2025-10-23T12:00:00Z",
                "updated_at": "2025-10-23T12:00:00Z",
            }
        }


class TokenResponse(BaseModel):
    """Schema for JWT token response (login, refresh)"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }


class WorkspaceCreate(BaseModel):
    """Schema for creating workspace membership"""

    workspace_id: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="member")

    @validator("role")
    def role_valid(cls, v: str) -> str:
        """Validate role is one of allowed values"""
        if v not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(VALID_ROLES)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "workspace_id": "/Users/hue/code/dopemux-mvp",
                "role": "member",
            }
        }


class WorkspaceResponse(BaseModel):
    """Schema for workspace membership in API responses"""

    workspace_id: str
    role: str
    permissions: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "workspace_id": "/Users/hue/code/dopemux-mvp",
                "role": "admin",
                "permissions": {"read_decisions": True, "write_decisions": True},
                "created_at": "2025-10-23T12:00:00Z",
            }
        }


class UserWithWorkspaces(BaseModel):
    """Schema for user data including workspace memberships"""

    id: int
    email: str
    username: str
    is_active: bool
    workspaces: List[WorkspaceResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Schema for audit log entries in API responses"""

    id: int
    user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "action": "login.success",
                "resource_type": None,
                "resource_id": None,
                "details": {"method": "password"},
                "ip_address": "192.168.1.1",
                "created_at": "2025-10-23T12:00:00Z",
            }
        }


# ============================================================================
# Helper Constants and Enums
# ============================================================================

# Role permission mappings (default permissions per role)
ROLE_PERMISSIONS = {
    "owner": {
        "read_decisions": True,
        "write_decisions": True,
        "delete_decisions": True,
        "read_progress": True,
        "write_progress": True,
        "delete_progress": True,
        "read_patterns": True,
        "write_patterns": True,
        "manage_users": True,
        "manage_workspace": True,
        "delete_workspace": True,
    },
    "admin": {
        "read_decisions": True,
        "write_decisions": True,
        "delete_decisions": True,
        "read_progress": True,
        "write_progress": True,
        "delete_progress": True,
        "read_patterns": True,
        "write_patterns": True,
        "manage_users": True,
        "manage_workspace": False,
        "delete_workspace": False,
    },
    "member": {
        "read_decisions": True,
        "write_decisions": True,
        "delete_decisions": False,  # Can't delete others' decisions
        "read_progress": True,
        "write_progress": True,
        "delete_progress": False,
        "read_patterns": True,
        "write_patterns": True,
        "manage_users": False,
        "manage_workspace": False,
        "delete_workspace": False,
    },
    "viewer": {
        "read_decisions": True,
        "write_decisions": False,
        "delete_decisions": False,
        "read_progress": True,
        "write_progress": False,
        "delete_progress": False,
        "read_patterns": True,
        "write_patterns": False,
        "manage_users": False,
        "manage_workspace": False,
        "delete_workspace": False,
    },
}


def get_role_permissions(role: str) -> Dict[str, bool]:
    """
    Get default permissions for a role.

    Args:
        role: Role name (owner, admin, member, viewer)

    Returns:
        Dictionary of permissions

    Example:
        perms = get_role_permissions("member")
        # Returns: {"read_decisions": True, "write_decisions": True, ...}
    """
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])
