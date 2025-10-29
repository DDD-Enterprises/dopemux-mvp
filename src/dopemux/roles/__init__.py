"""Role management utilities for Dopemux."""

from .catalog import (
    activate_role,
    available_roles,
    resolve_role,
    RoleSpec,
    RoleActivationResult,
    RoleNotFoundError,
)

__all__ = [
    "activate_role",
    "available_roles",
    "resolve_role",
    "RoleSpec",
    "RoleActivationResult",
    "RoleNotFoundError",
]
