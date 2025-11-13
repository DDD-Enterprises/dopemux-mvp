#!/usr/bin/env python3
"""
Serena Multi-Workspace Wrapper

Provides multi-workspace support for Serena MCP server without
requiring full refactoring of the stateful components.

Strategy: Create per-workspace Serena instances and aggregate results.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add shared utilities to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))

from shared.workspace_utils import (
    resolve_workspaces,
    aggregate_multi_workspace_results,
    workspace_to_identifier,
)


class SerenaMultiWorkspace:
    """
    Multi-workspace wrapper for Serena.
    
    Creates per-workspace Serena instances and aggregates their results.
    """
    
    def __init__(self):
        """Initialize multi-workspace manager."""
        self._workspace_instances: Dict[str, Any] = {}
    
    async def get_workspace_instance(self, workspace: Path):
        """
        Get or create Serena instance for a workspace.
        
        Args:
            workspace: Workspace path
            
        Returns:
            Serena instance for that workspace
        """
        workspace_key = str(workspace)
        
        if workspace_key not in self._workspace_instances:
            # Import SerenaServer here to avoid circular deps
            from mcp_server import SerenaServer
            
            # Create instance for this workspace
            # Note: This requires changing directory or passing workspace
            instance = SerenaServer()
            # TODO: Initialize with specific workspace
            # This may require modifying SerenaServer.__init__
            
            self._workspace_instances[workspace_key] = instance
        
        return self._workspace_instances[workspace_key]
    
    async def find_symbol_multi(
        self,
        query: str,
        symbol_type: Optional[str] = None,
        max_results: int = 10,
        user_id: str = "default",
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Search for symbols across multiple workspaces.
        
        Args:
            query: Symbol search query
            symbol_type: Optional symbol type filter
            max_results: Max results per workspace
            user_id: User ID for ADHD config
            workspace_path: Single workspace (backward compat)
            workspace_paths: Multiple workspaces
            
        Returns:
            Single workspace: Original format
            Multi workspace: Aggregated dict
        """
        workspaces = resolve_workspaces(
            workspace_path,
            workspace_paths,
            env_var_name="SERENA_WORKSPACES",
            fallback_to_current=True,
        )
        
        results = []
        for workspace in workspaces:
            instance = await self.get_workspace_instance(workspace)
            result = await instance.find_symbol_tool(
                query, symbol_type, max_results, user_id
            )
            # Parse JSON result back to dict if needed
            import json
            if isinstance(result, str):
                result = json.loads(result)
            results.append(result)
        
        return aggregate_multi_workspace_results(results, workspaces)
    
    async def get_context_multi(
        self,
        file_path: str,
        line: Optional[int] = None,
        context_lines: int = 10,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Get code context across multiple workspaces.
        
        Args:
            file_path: Relative file path
            line: Optional line number
            context_lines: Context lines around target
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Aggregated context results
        """
        workspaces = resolve_workspaces(
            workspace_path,
            workspace_paths,
            env_var_name="SERENA_WORKSPACES",
            fallback_to_current=True,
        )
        
        results = []
        for workspace in workspaces:
            instance = await self.get_workspace_instance(workspace)
            result = await instance.get_context_tool(
                file_path, line, context_lines
            )
            import json
            if isinstance(result, str):
                result = json.loads(result)
            results.append(result)
        
        return aggregate_multi_workspace_results(results, workspaces)
    
    async def find_relationships_multi(
        self,
        symbol_name: str,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Find code relationships across workspaces.
        
        Args:
            symbol_name: Symbol to analyze
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Aggregated relationship data
        """
        workspaces = resolve_workspaces(
            workspace_path,
            workspace_paths,
            env_var_name="SERENA_WORKSPACES",
            fallback_to_current=True,
        )
        
        results = []
        for workspace in workspaces:
            instance = await self.get_workspace_instance(workspace)
            result = await instance.find_relationships_tool(symbol_name)
            import json
            if isinstance(result, str):
                result = json.loads(result)
            results.append(result)
        
        return aggregate_multi_workspace_results(results, workspaces)


# Export multi-workspace functions
__all__ = ["SerenaMultiWorkspace"]
