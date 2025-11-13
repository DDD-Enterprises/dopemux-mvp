#!/usr/bin/env python3
"""
Tests for shared workspace utilities
"""

import os
import pytest
from pathlib import Path
from services.shared.workspace_utils import (
    resolve_workspaces,
    is_multi_workspace,
    aggregate_multi_workspace_results,
    workspace_to_identifier,
    parse_workspace_cli_args,
)


def test_resolve_workspaces_single_explicit(tmp_path):
    """Single workspace via workspace_path parameter."""
    ws = tmp_path / "workspace"
    ws.mkdir()

    result = resolve_workspaces(workspace_path=str(ws), fallback_to_current=False)

    assert len(result) == 1
    assert result[0] == ws


def test_resolve_workspaces_multiple_explicit(tmp_path):
    """Multiple workspaces via workspace_paths parameter."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    result = resolve_workspaces(
        workspace_paths=[str(ws1), str(ws2)], fallback_to_current=False
    )

    assert len(result) == 2
    assert result[0] == ws1
    assert result[1] == ws2


def test_resolve_workspaces_priority(tmp_path):
    """workspace_paths takes priority over workspace_path."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws3 = tmp_path / "ws3"
    ws1.mkdir()
    ws2.mkdir()
    ws3.mkdir()

    # workspace_paths should win
    result = resolve_workspaces(
        workspace_path=str(ws1),
        workspace_paths=[str(ws2), str(ws3)],
        fallback_to_current=False,
    )

    assert len(result) == 2
    assert result[0] == ws2
    assert result[1] == ws3


def test_resolve_workspaces_from_env(tmp_path, monkeypatch):
    """Resolve workspaces from environment variable."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    monkeypatch.setenv("DOPE_WORKSPACES", f"{ws1},{ws2}")

    result = resolve_workspaces(fallback_to_current=False)

    assert len(result) == 2
    assert result[0] == ws1
    assert result[1] == ws2


def test_resolve_workspaces_env_semicolon(tmp_path, monkeypatch):
    """Environment variable supports semicolon separator."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    monkeypatch.setenv("DOPE_WORKSPACES", f"{ws1};{ws2}")

    result = resolve_workspaces(fallback_to_current=False)

    assert len(result) == 2
    assert result[0] == ws1
    assert result[1] == ws2


def test_resolve_workspaces_env_mixed_separators(tmp_path, monkeypatch):
    """Environment variable supports mixed separators."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws3 = tmp_path / "ws3"
    ws1.mkdir()
    ws2.mkdir()
    ws3.mkdir()

    monkeypatch.setenv("DOPE_WORKSPACES", f"{ws1},{ws2};{ws3}")

    result = resolve_workspaces(fallback_to_current=False)

    assert len(result) == 3


def test_resolve_workspaces_custom_env_var(tmp_path, monkeypatch):
    """Custom environment variable name."""
    ws = tmp_path / "workspace"
    ws.mkdir()

    monkeypatch.setenv("CUSTOM_WORKSPACES", str(ws))

    result = resolve_workspaces(
        env_var_name="CUSTOM_WORKSPACES", fallback_to_current=False
    )

    assert len(result) == 1
    assert result[0] == ws


def test_resolve_workspaces_fallback_to_current():
    """Fallback to current directory when no paths specified."""
    result = resolve_workspaces(fallback_to_current=True)

    assert len(result) == 1
    assert result[0] == Path.cwd()


def test_resolve_workspaces_no_fallback():
    """No fallback returns empty list."""
    result = resolve_workspaces(fallback_to_current=False)

    assert len(result) == 0


def test_is_multi_workspace():
    """Test multi-workspace detection."""
    assert is_multi_workspace([Path("/ws1")]) is False
    assert is_multi_workspace([Path("/ws1"), Path("/ws2")]) is True
    assert is_multi_workspace([]) is False


def test_aggregate_single_workspace(tmp_path):
    """Single workspace returns original result."""
    ws = tmp_path / "ws"
    results = [[{"file": "a.py"}, {"file": "b.py"}]]
    workspaces = [ws]

    aggregated = aggregate_multi_workspace_results(results, workspaces)

    # Should return the original list (not wrapped)
    assert aggregated == [{"file": "a.py"}, {"file": "b.py"}]


def test_aggregate_multi_workspace(tmp_path):
    """Multiple workspaces returns aggregated dict."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    results = [
        [{"file": "a.py"}, {"file": "b.py"}],
        [{"file": "c.py"}],
    ]
    workspaces = [ws1, ws2]

    aggregated = aggregate_multi_workspace_results(results, workspaces)

    assert aggregated["workspace_count"] == 2
    assert aggregated["total_results"] == 3
    assert len(aggregated["results"]) == 2
    assert aggregated["results"][0]["workspace"] == str(ws1)
    assert aggregated["results"][0]["result_count"] == 2
    assert aggregated["results"][1]["workspace"] == str(ws2)
    assert aggregated["results"][1]["result_count"] == 1


def test_aggregate_dict_results(tmp_path):
    """Aggregate handles dict results with count field."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    results = [
        {"items": [1, 2], "count": 2},
        {"items": [3], "count": 1},
    ]
    workspaces = [ws1, ws2]

    aggregated = aggregate_multi_workspace_results(results, workspaces)

    assert aggregated["total_results"] == 3


def test_aggregate_mismatched_lengths(tmp_path):
    """Aggregate raises error on mismatched lengths."""
    ws = tmp_path / "ws"
    results = [[1], [2]]
    workspaces = [ws]

    with pytest.raises(ValueError, match="must match"):
        aggregate_multi_workspace_results(results, workspaces)


def test_workspace_to_identifier(tmp_path):
    """Convert workspace path to identifier."""
    ws = tmp_path / "my-project"
    ws.mkdir()

    identifier = workspace_to_identifier(ws)

    # Should be URL-safe
    assert "/" not in identifier
    assert "\\" not in identifier
    # Should contain project name
    assert "my-project" in identifier


def test_parse_workspace_cli_args():
    """Parse workspace arguments from CLI."""
    args = [
        "script.py",
        "--workspace",
        "/path/ws1",
        "--other",
        "value",
        "--workspace",
        "/path/ws2",
    ]

    workspaces = parse_workspace_cli_args(args)

    assert len(workspaces) == 2
    assert workspaces[0] == "/path/ws1"
    assert workspaces[1] == "/path/ws2"


def test_parse_workspace_cli_args_equals():
    """Parse workspace arguments with equals sign."""
    args = ["script.py", "--workspace=/path/ws1", "--workspace=/path/ws2"]

    workspaces = parse_workspace_cli_args(args)

    assert len(workspaces) == 2
    assert workspaces[0] == "/path/ws1"
    assert workspaces[1] == "/path/ws2"


def test_parse_workspace_cli_args_custom_name():
    """Parse custom argument name."""
    args = ["script.py", "-w", "/path/ws1", "-w", "/path/ws2"]

    workspaces = parse_workspace_cli_args(args, arg_name="-w")

    assert len(workspaces) == 2
