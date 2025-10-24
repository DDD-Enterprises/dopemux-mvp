#!/usr/bin/env python3
"""
ConPort-KG Authentication API Routes
Phase 1 Week 1 Day 4

FastAPI endpoints for user registration, authentication, and workspace management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.database import get_db_dependency
from auth.models import (
    AuditLogResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserWithWorkspaces,
    WorkspaceCreate,
    WorkspaceResponse,
)
from auth.service import AuthenticationError, AuthorizationError, UserService, get_user_service

# ============================================================================
# Router and Security
# ============================================================================

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


# ============================================================================
# Dependency: Get Current User from Token
# ============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """
    FastAPI dependency to get current authenticated user.

    Extracts JWT from Authorization header, validates, and returns user.

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    token = credentials.credentials
    user = await service.get_current_user_from_token(db, token)
    return user


# ============================================================================
# Public Endpoints (No Authentication Required)
# ============================================================================


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="""
    Create a new user account with email, username, and password.

    Password Requirements:
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character (!@#$%^&*...)
    - Not in HaveIBeenPwned breach database

    Returns:
    - Created user data (excludes password hash)
    - 201 Created on success
    - 400 Bad Request if validation fails or user exists
    """,
)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Register new user account"""
    try:
        # Extract client info for audit logging
        ip_address = request.client.host if request.client else None

        # Create user (service handles validation and breach check)
        user = await service.create_user(db, user_data)

        return UserResponse.from_orm(user)

    except HTTPException:
        # Re-raise HTTP exceptions (from service)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User registration failed: {str(e)}",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
    description="""
    Authenticate with email and password.

    Returns:
    - access_token: Short-lived JWT for API authentication (15 minutes)
    - refresh_token: Long-lived JWT for token refresh (30 days)
    - token_type: "bearer"
    - expires_in: Seconds until access token expires (900)

    The access token should be included in subsequent requests:
    Authorization: Bearer <access_token>
    """,
)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Login and receive JWT tokens"""
    try:
        # Extract client info for audit logging
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Authenticate user
        result = await service.authenticate_user(
            db,
            email=login_data.email,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
    Get a new access token using a valid refresh token.

    Send the refresh token in the request body.
    Returns a new access token (refresh token stays valid).

    This should be called when the access token expires (after 15 minutes).
    """,
)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Refresh access token using refresh token"""
    try:
        result = await service.refresh_access_token(db, refresh_token)

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=refresh_token,  # Same refresh token
            token_type=result["token_type"],
            expires_in=result["expires_in"],
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# Protected Endpoints (Authentication Required)
# ============================================================================


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="""
    Logout by revoking the refresh token.

    After logout, the refresh token cannot be used to get new access tokens.
    Any existing access tokens will still work until they expire (15 min).

    Returns 204 No Content on success.
    """,
)
async def logout(
    refresh_token: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Logout user by revoking refresh token"""
    try:
        await service.logout_user(db, refresh_token)
        return None  # 204 No Content

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=UserWithWorkspaces,
    summary="Get current user info",
    description="""
    Get information about the currently authenticated user.

    Requires valid access token in Authorization header.

    Returns:
    - User profile data
    - List of workspace memberships with roles
    """,
)
async def get_current_user_info(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Get current user information"""
    # Get user's workspaces
    workspaces = await service.get_user_workspaces(db, current_user.id)

    return UserWithWorkspaces(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        workspaces=[WorkspaceResponse(**w) for w in workspaces],
        created_at=current_user.created_at,
    )


@router.get(
    "/workspaces",
    response_model=List[WorkspaceResponse],
    summary="Get user's workspaces",
    description="""
    Get list of all workspaces the authenticated user belongs to.

    Returns workspace ID, role, permissions, and join date.
    """,
)
async def get_my_workspaces(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Get authenticated user's workspaces"""
    workspaces = await service.get_user_workspaces(db, current_user.id)
    return [WorkspaceResponse(**w) for w in workspaces]


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join a workspace",
    description="""
    Add current user to a workspace.

    This is a self-service endpoint - users can join workspaces directly.
    Default role is 'member'. Admins can upgrade roles later.
    """,
)
async def join_workspace(
    workspace_data: WorkspaceCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Join a workspace"""
    try:
        membership = await service.add_user_to_workspace(
            db,
            user_id=current_user.id,
            workspace_id=workspace_data.workspace_id,
            role=workspace_data.role,
        )

        return WorkspaceResponse(
            workspace_id=membership.workspace_id,
            role=membership.role,
            permissions=membership.permissions,
            created_at=membership.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join workspace: {str(e)}",
        )


@router.delete(
    "/workspaces/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave a workspace",
    description="""
    Remove current user from a workspace.

    Returns 204 No Content on success.
    """,
)
async def leave_workspace(
    workspace_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Leave a workspace"""
    try:
        await service.remove_user_from_workspace(
            db, user_id=current_user.id, workspace_id=workspace_id
        )
        return None  # 204 No Content

    except HTTPException:
        raise


@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    summary="Get user's audit logs",
    description="""
    Get security audit logs for the authenticated user.

    Returns last 100 audit events (login, logout, permission changes, etc.).
    Useful for security monitoring and compliance.
    """,
)
async def get_my_audit_logs(
    action: str = None,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Get authenticated user's audit logs"""
    logs = await service.get_audit_logs(
        db, user_id=current_user.id, action=action, limit=limit
    )

    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in logs
    ]


# ============================================================================
# Admin Endpoints (Manage Other Users)
# ============================================================================


@router.post(
    "/workspaces/{workspace_id}/users",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add user to workspace (Admin)",
    description="""
    Add another user to a workspace (requires manage_users permission).

    Only admins and owners can add users to workspaces.
    """,
)
async def add_user_to_workspace(
    workspace_id: str,
    user_id: int,
    role: str = "member",
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Add user to workspace (admin operation)"""
    try:
        membership = await service.add_user_to_workspace(
            db,
            user_id=user_id,
            workspace_id=workspace_id,
            role=role,
            added_by_user_id=current_user.id,
        )

        return WorkspaceResponse(
            workspace_id=membership.workspace_id,
            role=membership.role,
            permissions=membership.permissions,
            created_at=membership.created_at,
        )

    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except HTTPException:
        raise


@router.delete(
    "/workspaces/{workspace_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove user from workspace (Admin)",
    description="""
    Remove a user from a workspace (requires manage_users permission).

    Only admins and owners can remove users.
    """,
)
async def remove_user_from_workspace(
    workspace_id: str,
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Remove user from workspace (admin operation)"""
    try:
        await service.remove_user_from_workspace(
            db,
            user_id=user_id,
            workspace_id=workspace_id,
            removed_by_user_id=current_user.id,
        )
        return None  # 204 No Content

    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except HTTPException:
        raise


@router.patch(
    "/workspaces/{workspace_id}/users/{user_id}/role",
    response_model=WorkspaceResponse,
    summary="Update user role (Admin)",
    description="""
    Change a user's role in a workspace (requires manage_users permission).

    Valid roles: owner, admin, member, viewer
    """,
)
async def update_user_role(
    workspace_id: str,
    user_id: int,
    new_role: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dependency),
    service: UserService = Depends(get_user_service),
):
    """Update user's role in workspace"""
    try:
        membership = await service.update_user_role(
            db,
            user_id=user_id,
            workspace_id=workspace_id,
            new_role=new_role,
            updated_by_user_id=current_user.id,
        )

        return WorkspaceResponse(
            workspace_id=membership.workspace_id,
            role=membership.role,
            permissions=membership.permissions,
            created_at=membership.created_at,
        )

    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except HTTPException:
        raise


# ============================================================================
# Health Check
# ============================================================================


@router.get(
    "/health",
    summary="Auth service health check",
    description="Check if authentication service is operational",
)
async def health_check(db: Session = Depends(get_db_dependency)):
    """Health check endpoint"""
    from auth.database import check_database_connection

    db_healthy = check_database_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "service": "auth",
        "version": "2.0.0",
    }
