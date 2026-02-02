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
# __file__ is in services/serena/v2/, so parent.parent.parent.parent gives repo root
REPO_ROOT = Path(__file__).parent.parent.parent.parent
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
    
    async def find_similar_code_multi(
        self,
        query: str,
        top_k: int = 10,
        user_id: str = "default",
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Find semantically similar code across workspaces with unified ranking.
        
        Args:
            query: Natural language query
            top_k: Results per workspace
            user_id: User ID for ADHD config
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Aggregated results with cross-workspace ranking by relevance score
        """
        workspaces = resolve_workspaces(
            workspace_path,
            workspace_paths,
            env_var_name="SERENA_WORKSPACES",
            fallback_to_current=True,
        )
        
        all_results = []
        for workspace in workspaces:
            instance = await self.get_workspace_instance(workspace)
            result = await instance.find_similar_code_tool(
                query, top_k, user_id
            )
            import json
            if isinstance(result, str):
                result = json.loads(result)
            
            # Extract results array and tag with workspace
            workspace_id = workspace_to_identifier(workspace)
            if "results" in result:
                for item in result["results"]:
                    item["workspace"] = workspace_id
                    all_results.append(item)
        
        # Sort by relevance/similarity score (assuming higher is better)
        # Most semantic search returns a score field
        all_results.sort(
            key=lambda x: x.get("score", x.get("similarity", 0.0)),
            reverse=True
        )
        
        # Return top_k across all workspaces
        return {
            "query": query,
            "workspaces": [workspace_to_identifier(w) for w in workspaces],
            "total_found": len(all_results),
            "top_k": top_k,
            "results": all_results[:top_k],
        }
    
    async def get_unified_complexity_multi(
        self,
        file_path: str,
        symbol: Optional[str] = None,
        user_id: str = "default",
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Get unified complexity across workspaces.
        
        Args:
            file_path: File path to analyze
            symbol: Optional symbol name
            user_id: User ID for ADHD config
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Aggregated complexity data (avg/max/min across workspaces)
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
            result = await instance.get_unified_complexity_tool(
                file_path, symbol, user_id
            )
            import json
            if isinstance(result, str):
                result = json.loads(result)
            
            workspace_id = workspace_to_identifier(workspace)
            result["workspace"] = workspace_id
            results.append(result)
        
        # Aggregate complexity scores
        scores = [
            r.get("complexity_score", r.get("score", 0.5))
            for r in results
            if "error" not in r
        ]
        
        if not scores:
            return {"error": "No valid complexity results", "workspaces_checked": len(workspaces)}
        
        return {
            "file_path": file_path,
            "symbol": symbol,
            "workspaces": [workspace_to_identifier(w) for w in workspaces],
            "complexity": {
                "average": round(sum(scores) / len(scores), 3),
                "max": round(max(scores), 3),
                "min": round(min(scores), 3),
            },
            "per_workspace": results,
        }
    
    async def get_navigation_patterns_multi(
        self,
        days_back: int = 7,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Get navigation patterns across workspaces with pattern merging.
        
        Args:
            days_back: Days of history
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Merged navigation patterns
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
            result = await instance.get_navigation_patterns_tool(days_back)
            import json
            if isinstance(result, str):
                result = json.loads(result)
            
            workspace_id = workspace_to_identifier(workspace)
            result["workspace"] = workspace_id
            results.append(result)
        
        return aggregate_multi_workspace_results(results, workspaces)
    
    async def analyze_complexity_multi(
        self,
        file_path: str,
        symbol_name: Optional[str] = None,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Analyze complexity across workspaces.
        
        Args:
            file_path: File to analyze
            symbol_name: Optional symbol
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Aggregated complexity analysis
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
            result = await instance.analyze_complexity_tool(
                file_path, symbol_name
            )
            import json
            if isinstance(result, str):
                result = json.loads(result)
            
            workspace_id = workspace_to_identifier(workspace)
            result["workspace"] = workspace_id
            results.append(result)
        
        # Calculate aggregate metrics
        valid_results = [r for r in results if "error" not in r]
        
        if not valid_results:
            return {
                "error": "No valid complexity results",
                "workspaces_checked": len(workspaces),
                "per_workspace": results,
            }
        
        scores = [r.get("complexity", {}).get("score", 0.5) for r in valid_results]
        
        return {
            "file_path": file_path,
            "symbol": symbol_name,
            "workspaces": [workspace_to_identifier(w) for w in workspaces],
            "aggregate_complexity": {
                "average_score": round(sum(scores) / len(scores), 3),
                "max_score": round(max(scores), 3),
                "min_score": round(min(scores), 3),
                "interpretation": _complexity_interpretation(sum(scores) / len(scores)),
            },
            "per_workspace": results,
        }
    
    async def get_reading_order_multi(
        self,
        files: List[str],
        symbols: Optional[List[str]] = None,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Get optimal reading order across workspaces.
        
        Args:
            files: Files to order
            symbols: Optional symbol names
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Aggregated reading order with cross-workspace complexity ordering
        """
        workspaces = resolve_workspaces(
            workspace_path,
            workspace_paths,
            env_var_name="SERENA_WORKSPACES",
            fallback_to_current=True,
        )
        
        all_file_data = []
        for workspace in workspaces:
            instance = await self.get_workspace_instance(workspace)
            result = await instance.get_reading_order_tool(files, symbols)
            import json
            if isinstance(result, str):
                result = json.loads(result)
            
            workspace_id = workspace_to_identifier(workspace)
            
            # Extract reading order items
            if "reading_order" in result:
                for item in result["reading_order"]:
                    item["workspace"] = workspace_id
                    all_file_data.append(item)
        
        # Sort all files by complexity across workspaces
        all_file_data.sort(key=lambda x: x.get("complexity_score", 0.5))
        
        total_minutes = sum(f.get("reading_minutes", 5.0) for f in all_file_data)
        sessions_needed = max(1, round(total_minutes / 25))
        
        return {
            "workspaces": [workspace_to_identifier(w) for w in workspaces],
            "total_files": len(all_file_data),
            "reading_order": all_file_data,
            "session_plan": {
                "total_reading_minutes": round(total_minutes, 1),
                "pomodoro_sessions_needed": sessions_needed,
                "breaks_recommended": sessions_needed - 1,
            },
        }
    
    async def find_test_file_multi(
        self,
        file_path: str,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Find test files across workspaces.
        
        Args:
            file_path: File to find tests for
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Test file matches from all workspaces
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
            result = await instance.find_test_file_tool(file_path)
            import json
            if isinstance(result, str):
                result = json.loads(result)
            
            workspace_id = workspace_to_identifier(workspace)
            result["workspace"] = workspace_id
            
            # Only include if test was found
            if result.get("found"):
                results.append(result)
        
        return {
            "file_path": file_path,
            "workspaces": [workspace_to_identifier(w) for w in workspaces],
            "matches_found": len(results),
            "test_files": results,
        }


def _complexity_interpretation(score: float) -> str:
    """Helper to interpret complexity score."""
    if score < 0.3:
        return "LOW - Safe to read anytime"
    elif score < 0.6:
        return "MEDIUM - Needs focus"
    else:
        return "HIGH - Complex code, peak focus required"


# Export multi-workspace functions
__all__ = ["SerenaMultiWorkspace"]
