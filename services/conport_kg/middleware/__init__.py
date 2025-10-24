"""
ConPort-KG Middleware
Phase 1 Week 2 Day 8

Authorization and security middleware for FastAPI.
"""

from .rbac_middleware import WorkspaceAuthorizationMiddleware, set_workspace_context

__all__ = ["WorkspaceAuthorizationMiddleware", "set_workspace_context"]
