#!/usr/bin/env python3
"""
RBAC Middleware for ConPort-KG API
Phase 1 Week 2 Day 8

Enforces workspace permissions and sets RLS session variables.
"""

from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from auth.service import UserService


class WorkspaceAuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce workspace-based authorization.

    Workflow:
    1. Extract workspace_id from request (query param or body)
    2. Get current user from JWT (set by auth dependency)
    3. Verify user is member of workspace
    4. Set PostgreSQL RLS session variables
    5. Continue to route handler

    Sets session variables for RLS:
    - SET LOCAL app.current_user_id = '<user_id>'
    - SET LOCAL app.current_workspace_id = '<workspace_id>'
    """

    def __init__(self, app):
        super().__init__(app)
        self.user_service = UserService()

    async def dispatch(self, request: Request, call_next):
        """Process request with workspace authorization"""

        # Skip auth/health endpoints (don't need workspace)
        if request.url.path.startswith("/auth") or request.url.path == "/health":
            return await call_next(request)

        # Extract workspace_id from request
        workspace_id = self._extract_workspace_id(request)

        if not workspace_id:
            # No workspace_id required for this endpoint
            return await call_next(request)

        # Get current user (set by auth dependency earlier in chain)
        current_user = getattr(request.state, "current_user", None)

        if not current_user:
            # Endpoint requires workspace but user not authenticated
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for workspace access",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get database session (set by dependency)
        db = getattr(request.state, "db", None)

        if not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session not available",
            )

        # Check workspace membership
        role = await self.user_service.get_user_role(db, current_user.id, workspace_id)

        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User {current_user.id} is not a member of workspace {workspace_id}",
            )

        # Set PostgreSQL RLS session variables
        try:
            db.execute(text(f"SET LOCAL app.current_user_id = '{current_user.id}'"))
            db.execute(text(f"SET LOCAL app.current_workspace_id = '{workspace_id}'"))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to set RLS session variables: {str(e)}",
            )

        # Store workspace_id and role in request state for route handlers
        request.state.workspace_id = workspace_id
        request.state.user_role = role

        # Continue to route handler
        response = await call_next(request)

        return response

    def _extract_workspace_id(self, request: Request) -> Optional[str]:
        """
        Extract workspace_id from request.

        Checks (in order):
        1. Query parameter: ?workspace_id=/path/to/workspace
        2. Request body (JSON): {"workspace_id": "/path"}
        3. Path parameter: /workspaces/{workspace_id}/...

        Returns:
            workspace_id string or None if not present
        """
        # Check query parameters
        workspace_id = request.query_params.get("workspace_id")
        if workspace_id:
            return workspace_id

        # Check path parameters (e.g., /workspaces/{workspace_id}/decisions)
        if "workspace_id" in request.path_params:
            return request.path_params["workspace_id"]

        # For POST/PUT requests, check body (requires async read)
        # Note: Can't read body in middleware (consumed by route handler)
        # So we rely on query param or path param for now

        return None


async def set_workspace_context(
    db, user_id: int, workspace_id: str
) -> None:
    """
    Set PostgreSQL RLS session variables.

    Helper function for route handlers that need to set context.

    Args:
        db: Database session
        user_id: Current user ID
        workspace_id: Workspace to access

    Example:
        @router.get("/decisions")
        async def get_decisions(
            workspace_id: str,
            current_user = Depends(get_current_user),
            db: Session = Depends(get_db_dependency)
        ):
            await set_workspace_context(db, current_user.id, workspace_id)
            # RLS variables now set, queries are workspace-scoped
            decisions = overview.get_recent_decisions(workspace_id, limit=10)
            return decisions
    """
    try:
        db.execute(text(f"SET LOCAL app.current_user_id = '{user_id}'"))
        db.execute(text(f"SET LOCAL app.current_workspace_id = '{workspace_id}'"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set workspace context: {str(e)}",
        )
