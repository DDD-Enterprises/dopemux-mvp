#!/usr/bin/env python3
"""
Permission Decorators and Helpers
Phase 1 Week 2 Day 8

Decorators to enforce workspace permissions on route handlers.
"""

from functools import wraps
from typing import Callable

from fastapi import HTTPException, status

from .service import UserService, AuthorizationError


def require_permission(permission: str):
    """
    Decorator to require specific workspace permission.

    Checks that current user has the specified permission in the workspace.
    Raises 403 Forbidden if user lacks permission.

    Args:
        permission: Permission key (e.g., "write_decisions", "manage_users")

    Usage:
        from auth.permissions import require_permission

        @router.delete("/decisions/{id}")
        @require_permission("delete_decisions")
        async def delete_decision(
            id: int,
            workspace_id: str,
            current_user = Depends(get_current_user),
            db: Session = Depends(get_db_dependency)
        ):
            # Only called if user has delete_decisions permission
            ...

    Example:
        # User with "member" role tries to delete decision
        # member role has delete_decisions=False
        # Decorator raises 403 Forbidden before route handler executes
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_user = kwargs.get("current_user")
            workspace_id = kwargs.get("workspace_id")
            db = kwargs.get("db")

            if not all([current_user, workspace_id, db]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission decorator requires current_user, workspace_id, and db dependencies",
                )

            # Check permission
            service = UserService()
            try:
                await service.require_workspace_permission(
                    db, current_user.id, workspace_id, permission
                )
            except AuthorizationError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e),
                )

            # Permission granted - call route handler
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(required_role: str):
    """
    Decorator to require specific workspace role.

    Args:
        required_role: Required role (owner, admin, member, viewer)

    Usage:
        @router.delete("/workspaces/{workspace_id}")
        @require_role("owner")
        async def delete_workspace(workspace_id: str, current_user = Depends(get_current_user)):
            # Only owners can delete workspaces
            ...
    """

    ROLE_HIERARCHY = {"owner": 4, "admin": 3, "member": 2, "viewer": 1}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            workspace_id = kwargs.get("workspace_id")
            db = kwargs.get("db")

            if not all([current_user, workspace_id, db]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Role decorator requires current_user, workspace_id, and db dependencies",
                )

            # Get user's role
            service = UserService()
            user_role = await service.get_user_role(db, current_user.id, workspace_id)

            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User is not a member of workspace {workspace_id}",
                )

            # Check role hierarchy (owner > admin > member > viewer)
            if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(required_role, 99):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{user_role}' insufficient. Required: '{required_role}' or higher.",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def check_permission(
    db, user_id: int, workspace_id: str, permission: str
) -> bool:
    """
    Check if user has permission in workspace.

    Helper function for conditional logic in route handlers.

    Args:
        db: Database session
        user_id: User ID to check
        workspace_id: Workspace ID
        permission: Permission key

    Returns:
        True if user has permission, False otherwise

    Example:
        can_delete = await check_permission(db, user.id, workspace_id, "delete_decisions")
        if can_delete:
            # Show delete button
    """
    service = UserService()
    return await service.check_workspace_permission(db, user_id, workspace_id, permission)
