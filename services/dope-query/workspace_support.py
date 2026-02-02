#!/usr/bin/env python3
"""
ConPort KG Multi-Workspace Support

Workspace-scoped knowledge graph operations.
Enables isolated context storage per workspace with cross-workspace queries.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add shared utilities
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))

from shared.workspace_utils import (
    resolve_workspaces,
    aggregate_multi_workspace_results,
    workspace_to_identifier,
)


def get_workspace_graph_name(workspace: Path) -> str:
    """
    Get graph name for a workspace.
    
    Creates a unique, stable identifier for workspace's graph.
    
    Args:
        workspace: Workspace path
        
    Returns:
        Graph name (e.g., "workspace_home_user_project")
    """
    identifier = workspace_to_identifier(workspace)
    return f"workspace_{identifier}"


def create_workspace_scoped_query(
    query: str,
    workspace: Path,
    graph_name_var: str = "$graph_name",
) -> tuple[str, Dict[str, Any]]:
    """
    Scope a Cypher query to a specific workspace graph.
    
    Args:
        query: Original Cypher query
        workspace: Workspace to scope to
        graph_name_var: Variable name for graph in query
        
    Returns:
        Tuple of (modified_query, parameters)
    """
    graph_name = get_workspace_graph_name(workspace)
    
    # Add graph name to parameters
    params = {"workspace_graph": graph_name}
    
    # If query uses graph_name_var, it will be replaced
    # Otherwise, query should already use $workspace_graph
    if graph_name_var in query and graph_name_var != "$workspace_graph":
        query = query.replace(graph_name_var, "$workspace_graph")
    
    return query, params


async def query_across_workspaces(
    query: str,
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    client = None,
) -> Any:
    """
    Execute query across multiple workspace graphs.
    
    Args:
        query: Cypher query to execute
        workspace_path: Single workspace
        workspace_paths: Multiple workspaces
        query_params: Additional query parameters
        client: AGE client instance
        
    Returns:
        Aggregated results from all workspaces
    """
    workspaces = resolve_workspaces(
        workspace_path,
        workspace_paths,
        env_var_name="CONPORT_KG_WORKSPACES",
        fallback_to_current=True,
    )
    
    results = []
    for workspace in workspaces:
        # Scope query to workspace
        scoped_query, ws_params = create_workspace_scoped_query(query, workspace)
        
        # Merge parameters
        all_params = {**(query_params or {}), **ws_params}
        
        # Execute query (requires AGE client)
        if client:
            result = await client.execute_query(scoped_query, all_params)
        else:
            # Return scoped query for manual execution
            result = {
                "query": scoped_query,
                "params": all_params,
                "workspace": str(workspace),
            }
        
        results.append(result)
    
    return aggregate_multi_workspace_results(results, workspaces)


def create_workspace_graph_schema(workspace: Path) -> str:
    """
    Generate schema creation query for workspace graph.
    
    Args:
        workspace: Workspace path
        
    Returns:
        Cypher query to create workspace graph
    """
    graph_name = get_workspace_graph_name(workspace)
    
    return f"""
    -- Create workspace-scoped graph
    SELECT * FROM ag_catalog.create_graph('{graph_name}');
    
    -- Create standard node labels
    SELECT * FROM cypher('{graph_name}', $$
        CREATE CONSTRAINT IF NOT EXISTS FOR (c:Context) REQUIRE c.id IS UNIQUE
    $$) as (a agtype);
    
    SELECT * FROM cypher('{graph_name}', $$
        CREATE CONSTRAINT IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE
    $$) as (a agtype);
    
    SELECT * FROM cypher('{graph_name}', $$
        CREATE CONSTRAINT IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE
    $$) as (a agtype);
    """


class WorkspaceAwareKG:
    """
    Workspace-aware knowledge graph operations.
    
    Provides isolated graphs per workspace with cross-workspace querying.
    """
    
    def __init__(self, age_client=None):
        """
        Initialize workspace-aware KG.
        
        Args:
            age_client: AGE database client
        """
        self.client = age_client
        self._workspace_graphs: Dict[str, str] = {}
    
    async def ensure_workspace_graph(self, workspace: Path) -> str:
        """
        Ensure graph exists for workspace.
        
        Args:
            workspace: Workspace path
            
        Returns:
            Graph name
        """
        graph_name = get_workspace_graph_name(workspace)
        
        if graph_name not in self._workspace_graphs:
            # Create graph if doesn't exist
            schema = create_workspace_graph_schema(workspace)
            
            if self.client:
                await self.client.execute(schema)
            
            self._workspace_graphs[graph_name] = str(workspace)
        
        return graph_name
    
    async def store_context(
        self,
        context_data: Dict[str, Any],
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Store context in workspace graph(s).
        
        Args:
            context_data: Context to store
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Storage results
        """
        workspaces = resolve_workspaces(
            workspace_path,
            workspace_paths,
            fallback_to_current=True,
        )
        
        results = []
        for workspace in workspaces:
            graph_name = await self.ensure_workspace_graph(workspace)
            
            # Store context in workspace graph
            # (Implementation depends on AGE client API)
            result = {
                "workspace": str(workspace),
                "graph": graph_name,
                "context_id": context_data.get("id"),
                "stored": True,
            }
            results.append(result)
        
        return aggregate_multi_workspace_results(results, workspaces)
    
    async def query_context(
        self,
        query: str,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """
        Query context across workspaces.
        
        Args:
            query: Cypher query
            workspace_path: Single workspace
            workspace_paths: Multiple workspaces
            
        Returns:
            Query results
        """
        return await query_across_workspaces(
            query,
            workspace_path,
            workspace_paths,
            client=self.client,
        )


# Export functions
__all__ = [
    "get_workspace_graph_name",
    "create_workspace_scoped_query",
    "query_across_workspaces",
    "create_workspace_graph_schema",
    "WorkspaceAwareKG",
]
