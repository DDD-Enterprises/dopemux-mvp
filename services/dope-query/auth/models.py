#!/usr/bin/env python3
"""
ConPort-KG Authentication Models
Part of Phase 1 Security Hardening

SQLAlchemy models for user management and authentication.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

Base = declarative_base()

# SQLAlchemy Models

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspaces = relationship("UserWorkspace", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class UserWorkspace(Base):
    """User workspace permissions"""
    __tablename__ = "user_workspaces"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    workspace_id = Column(String(255), primary_key=True)
    role = Column(String(50), default="member")  # owner, admin, member, viewer
    permissions = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="workspaces")

class RefreshToken(Base):
    """JWT refresh tokens"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

class AuditLog(Base):
    """Security audit logging"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    details = Column(JSON)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

# Pydantic Models for API

class UserCreate(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123"
            }
        }

class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "username": "johndoe"
                }
            }
        }

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

class UserResponse(BaseModel):
    """User profile response"""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    workspaces: Optional[List[Dict[str, Any]]] = None

class WorkspacePermission(BaseModel):
    """Workspace permission model"""
    workspace_id: str
    role: str
    permissions: Dict[str, Any]

# Role definitions
ROLES = {
    "owner": {
        "description": "Full control over workspace",
        "permissions": {
            "read": True,
            "write": True,
            "delete": True,
            "manage_users": True,
            "manage_settings": True
        }
    },
    "admin": {
        "description": "Administrative control",
        "permissions": {
            "read": True,
            "write": True,
            "delete": True,
            "manage_users": True,
            "manage_settings": False
        }
    },
    "member": {
        "description": "Standard user access",
        "permissions": {
            "read": True,
            "write": True,
            "delete": False,
            "manage_users": False,
            "manage_settings": False
        }
    },
    "viewer": {
        "description": "Read-only access",
        "permissions": {
            "read": True,
            "write": False,
            "delete": False,
            "manage_users": False,
            "manage_settings": False
        }
    }
}