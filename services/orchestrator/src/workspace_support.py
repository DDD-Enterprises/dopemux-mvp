#!/usr/bin/env python3
"""
Orchestrator Multi-Workspace Support

Adds workspace context to orchestrator requests and routing.
Simple parameter forwarding - orchestrator doesn't need full multi-workspace,
it just needs to pass workspace context to downstream services.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add shared utilities
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))

from shared.workspace_utils import resolve_workspaces


def add_workspace_context(
    request: Dict[str, Any],
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Add workspace context to orchestrator request.
    
    This allows workspace-aware routing to downstream services.
    
    Args:
        request: Original request dict
        workspace_path: Single workspace
        workspace_paths: Multiple workspaces
        
    Returns:
        Request with workspace context added
    """
    # Add workspace parameters to request
    if workspace_paths:
        request["workspace_paths"] = workspace_paths
    elif workspace_path:
        request["workspace_path"] = workspace_path
    
    # Also resolve and add as metadata
    workspaces = resolve_workspaces(
        workspace_path,
        workspace_paths,
        env_var_name="ORCHESTRATOR_WORKSPACES",
        fallback_to_current=False,  # Don't assume workspace
    )
    
    if workspaces:
        request["_workspace_context"] = {
            "workspaces": [str(w) for w in workspaces],
            "count": len(workspaces),
        }
    
    return request


def extract_workspace_from_request(request: Dict[str, Any]) -> Optional[List[Path]]:
    """
    Extract workspace context from request.
    
    Args:
        request: Request dict
        
    Returns:
        List of workspace paths if present, None otherwise
    """
    # Try workspace_paths first
    if "workspace_paths" in request:
        return [Path(p) for p in request["workspace_paths"]]
    
    # Try workspace_path
    if "workspace_path" in request:
        return [Path(request["workspace_path"])]
    
    # Try metadata
    if "_workspace_context" in request:
        return [Path(p) for p in request["_workspace_context"]["workspaces"]]
    
    return None


class WorkspaceAwareRouter:
    """
    Router that forwards workspace context to services.
    
    This is a thin wrapper that adds workspace awareness without
    changing orchestrator's core routing logic.
    """
    
    def __init__(self, base_router):
        """
        Initialize workspace-aware router.
        
        Args:
            base_router: Original orchestrator router
        """
        self.base_router = base_router
    
    async def route(
        self,
        request: Dict[str, Any],
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Route request with workspace context.
        
        Args:
            request: Request to route
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Routed response
        """
        # Add workspace context to request
        enhanced_request = add_workspace_context(
            request,
            workspace_path,
            workspace_paths,
        )
        
        # Forward to base router
        return await self.base_router.route(enhanced_request)


# Export functions
__all__ = [
    "add_workspace_context",
    "extract_workspace_from_request",
    "WorkspaceAwareRouter",
]
