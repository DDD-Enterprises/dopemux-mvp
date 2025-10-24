"""
ConPort-KG Authentication Module
Part of Phase 1: Authentication & Authorization

Provides JWT-based authentication, password security, and user management.
"""

from .database import get_db, get_db_dependency, init_database, check_database_connection
from .jwt_utils import JWTManager
from .models import (
    ROLE_PERMISSIONS,
    VALID_ROLES,
    AuditLog,
    AuditLogResponse,
    RefreshToken,
    TokenResponse,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserWithWorkspaces,
    UserWorkspace,
    WorkspaceCreate,
    WorkspaceResponse,
    get_role_permissions,
)
from .password_utils import PasswordManager, PasswordValidationError

__all__ = [
    # Database
    "get_db",
    "get_db_dependency",
    "init_database",
    "check_database_connection",
    # JWT
    "JWTManager",
    # Password
    "PasswordManager",
    "PasswordValidationError",
    # Models (ORM)
    "User",
    "UserWorkspace",
    "RefreshToken",
    "AuditLog",
    # Schemas (Pydantic)
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserWithWorkspaces",
    "TokenResponse",
    "WorkspaceCreate",
    "WorkspaceResponse",
    "AuditLogResponse",
    # Constants
    "VALID_ROLES",
    "ROLE_PERMISSIONS",
    "get_role_permissions",
]
