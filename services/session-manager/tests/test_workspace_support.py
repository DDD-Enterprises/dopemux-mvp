#!/usr/bin/env python3
"""
Tests for orchestrator multi-workspace support
"""

import pytest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))
sys.path.insert(0, str(REPO_ROOT / "services" / "orchestrator" / "src"))

from workspace_support import (
    add_workspace_context,
    extract_workspace_from_request,
)


def test_add_workspace_context_single():
    """Add single workspace to request."""
    request = {"action": "search", "query": "test"}
    
    result = add_workspace_context(request, workspace_path="/path/to/ws")
    
    assert result["workspace_path"] == "/path/to/ws"
    assert "_workspace_context" in result
    assert result["_workspace_context"]["count"] == 1


def test_add_workspace_context_multiple():
    """Add multiple workspaces to request."""
    request = {"action": "search", "query": "test"}
    
    result = add_workspace_context(
        request,
        workspace_paths=["/ws1", "/ws2"]
    )
    
    assert result["workspace_paths"] == ["/ws1", "/ws2"]
    assert result["_workspace_context"]["count"] == 2


def test_add_workspace_context_priority():
    """workspace_paths takes priority over workspace_path."""
    request = {"action": "search"}
    
    result = add_workspace_context(
        request,
        workspace_path="/single",
        workspace_paths=["/multi1", "/multi2"]
    )
    
    # Should have both, but workspace_paths is primary
    assert result["workspace_paths"] == ["/multi1", "/multi2"]
    assert result["_workspace_context"]["count"] == 2


def test_extract_workspace_from_request_paths():
    """Extract multiple workspaces from request."""
    request = {"workspace_paths": ["/ws1", "/ws2"]}
    
    workspaces = extract_workspace_from_request(request)
    
    assert len(workspaces) == 2
    assert workspaces[0] == Path("/ws1")
    assert workspaces[1] == Path("/ws2")


def test_extract_workspace_from_request_path():
    """Extract single workspace from request."""
    request = {"workspace_path": "/workspace"}
    
    workspaces = extract_workspace_from_request(request)
    
    assert len(workspaces) == 1
    assert workspaces[0] == Path("/workspace")


def test_extract_workspace_from_metadata():
    """Extract workspaces from metadata."""
    request = {
        "_workspace_context": {
            "workspaces": ["/ws1", "/ws2"],
            "count": 2
        }
    }
    
    workspaces = extract_workspace_from_request(request)
    
    assert len(workspaces) == 2


def test_extract_workspace_none():
    """Return None when no workspace in request."""
    request = {"action": "search"}
    
    workspaces = extract_workspace_from_request(request)
    
    assert workspaces is None


def test_workspace_context_preserves_original():
    """Adding workspace context preserves original request fields."""
    original = {"action": "search", "query": "test", "filters": ["type:code"]}
    
    result = add_workspace_context(original.copy(), workspace_path="/ws")
    
    assert result["action"] == "search"
    assert result["query"] == "test"
    assert result["filters"] == ["type:code"]
    assert "workspace_path" in result
