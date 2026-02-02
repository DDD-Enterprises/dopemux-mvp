#!/usr/bin/env python3
"""
Tests for ConPort KG multi-workspace support
"""

import pytest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))
sys.path.insert(0, str(REPO_ROOT / "services" / "conport_kg"))

from workspace_support import (
    get_workspace_graph_name,
    create_workspace_scoped_query,
    create_workspace_graph_schema,
)
from services.shared.workspace_utils import resolve_workspaces


def test_workspace_graph_name():
    """Test graph name generation for workspace."""
    ws = Path("/home/user/my-project")
    
    graph_name = get_workspace_graph_name(ws)
    
    assert graph_name.startswith("workspace_")
    # Dashes are converted to underscores for safety
    assert "my_project" in graph_name
    # Should be stable (same input = same output)
    assert get_workspace_graph_name(ws) == graph_name


def test_workspace_graph_name_unique():
    """Different workspaces should have different graph names."""
    ws1 = Path("/home/user/project1")
    ws2 = Path("/home/user/project2")
    
    name1 = get_workspace_graph_name(ws1)
    name2 = get_workspace_graph_name(ws2)
    
    assert name1 != name2


def test_create_workspace_scoped_query():
    """Test scoping query to workspace."""
    query = "MATCH (n:Context) RETURN n"
    ws = Path("/workspace")
    
    scoped_query, params = create_workspace_scoped_query(query, ws)
    
    assert "workspace_graph" in params
    assert params["workspace_graph"].startswith("workspace_")


def test_workspace_scoped_query_preserves_content():
    """Scoped query should preserve original query structure."""
    original = "MATCH (n:Context {id: $context_id}) RETURN n"
    ws = Path("/workspace")
    
    scoped, params = create_workspace_scoped_query(original, ws)
    
    # Query structure preserved
    assert "MATCH (n:Context" in scoped
    assert "RETURN n" in scoped
    # Workspace param added
    assert "workspace_graph" in params


def test_create_workspace_graph_schema():
    """Test workspace graph schema generation."""
    ws = Path("/my/workspace")
    
    schema = create_workspace_graph_schema(ws)
    
    # Should create graph
    assert "create_graph" in schema
    # Should have workspace-specific name
    assert "workspace_" in schema
    # Should create constraints
    assert "CONSTRAINT" in schema
    assert "Context" in schema
    assert "Decision" in schema
    assert "Task" in schema


def test_workspace_resolution_conport():
    """Test workspace resolution with CONPORT_KG_WORKSPACES env."""
    # Just test the utility works
    ws = Path("/workspace")
    
    workspaces = resolve_workspaces(
        workspace_path=str(ws),
        env_var_name="CONPORT_KG_WORKSPACES",
        fallback_to_current=False,
    )
    
    assert len(workspaces) == 1
    assert workspaces[0] == ws


@pytest.mark.anyio
async def test_workspace_graph_names_stable():
    """Graph names should be stable across calls."""
    ws = Path("/home/user/my-project")
    
    names = [get_workspace_graph_name(ws) for _ in range(10)]
    
    # All should be the same
    assert len(set(names)) == 1


def test_workspace_graph_name_url_safe():
    """Graph names should be URL/database safe."""
    ws = Path("/home/user/my project with spaces")
    
    name = get_workspace_graph_name(ws)
    
    # Should not have spaces or special chars that break SQL
    assert " " not in name
    assert "/" not in name or name.count("/") == 0  # No path separators
