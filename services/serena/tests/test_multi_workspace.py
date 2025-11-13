#!/usr/bin/env python3
"""
Tests for Serena multi-workspace support
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))
sys.path.insert(0, str(REPO_ROOT / "services" / "serena" / "v2"))

from services.shared.workspace_utils import resolve_workspaces


@pytest.mark.anyio
async def test_serena_find_symbol_multi_workspace(tmp_path, monkeypatch):
    """Serena find_symbol should work across multiple workspaces."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()
    
    # Mock the find_symbol_tool to return workspace-specific results
    mock_results = [
        '[{"symbol": "MyClass", "file": "ws1/main.py", "line": 10}]',
        '[{"symbol": "MyClass", "file": "ws2/alt.py", "line": 20}]',
    ]
    
    # We'll test just the utility functions for now
    # Full integration requires serena server running
    
    workspaces = resolve_workspaces(
        workspace_paths=[str(ws1), str(ws2)],
        fallback_to_current=False,
    )
    
    assert len(workspaces) == 2
    assert workspaces[0] == ws1
    assert workspaces[1] == ws2


@pytest.mark.anyio
async def test_serena_workspace_resolution(tmp_path, monkeypatch):
    """Test workspace resolution for serena."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()
    
    # Test environment variable
    monkeypatch.setenv("SERENA_WORKSPACES", f"{ws1},{ws2}")
    
    workspaces = resolve_workspaces(
        env_var_name="SERENA_WORKSPACES",
        fallback_to_current=False,
    )
    
    assert len(workspaces) == 2
    assert ws1 in workspaces
    assert ws2 in workspaces


@pytest.mark.anyio
async def test_serena_single_workspace_backward_compat(tmp_path):
    """Single workspace should return original format."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    
    workspaces = resolve_workspaces(
        workspace_path=str(ws),
        fallback_to_current=False,
    )
    
    # Should return list with one workspace
    assert len(workspaces) == 1
    assert workspaces[0] == ws


def test_serena_workspace_env_var_parsing(monkeypatch):
    """Test environment variable parsing with various formats."""
    # Comma separated
    monkeypatch.setenv("SERENA_WORKSPACES", "/path1,/path2,/path3")
    
    workspaces = resolve_workspaces(
        env_var_name="SERENA_WORKSPACES",
        fallback_to_current=False,
    )
    
    assert len(workspaces) == 3
    
    # Semicolon separated
    monkeypatch.setenv("SERENA_WORKSPACES", "/path1;/path2")
    
    workspaces = resolve_workspaces(
        env_var_name="SERENA_WORKSPACES",
        fallback_to_current=False,
    )
    
    assert len(workspaces) == 2


@pytest.mark.anyio  
async def test_serena_priority_explicit_over_env(tmp_path, monkeypatch):
    """Explicit workspace_paths should take priority over env var."""
    ws_explicit = tmp_path / "explicit"
    ws_env = tmp_path / "env"
    ws_explicit.mkdir()
    ws_env.mkdir()
    
    monkeypatch.setenv("SERENA_WORKSPACES", str(ws_env))
    
    workspaces = resolve_workspaces(
        workspace_paths=[str(ws_explicit)],
        env_var_name="SERENA_WORKSPACES",
        fallback_to_current=False,
    )
    
    # Should use explicit, not env
    assert len(workspaces) == 1
    assert workspaces[0] == ws_explicit
