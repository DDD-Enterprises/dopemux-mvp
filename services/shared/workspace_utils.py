#!/usr/bin/env python3
"""
Shared Multi-Workspace Utilities

Provides consistent workspace resolution across all dopemux services.
Supports single workspace (backward compat) and multiple workspaces (new).
"""

import os
from pathlib import Path
from typing import List, Optional, Union


def resolve_workspaces(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    fallback_to_current: bool = True,
    env_var_name: str = "DOPE_WORKSPACES",
) -> List[Path]:
    """
    Resolve workspace paths from various sources with consistent priority.

    Priority (highest to lowest):
    1. workspace_paths parameter (explicit list)
    2. workspace_path parameter (single explicit)
    3. Environment variable (env_var_name)
    4. Current working directory (if fallback_to_current=True)

    Args:
        workspace_path: Single workspace path (backward compatibility)
        workspace_paths: List of workspace paths (new multi-workspace support)
        fallback_to_current: If True, use cwd when no paths specified
        env_var_name: Name of environment variable to check (default: DOPE_WORKSPACES)

    Returns:
        List of resolved Path objects (always returns a list, even for single workspace)

    Examples:
        >>> # Single workspace (backward compatible)
        >>> resolve_workspaces(workspace_path="/path/to/project")
        [Path("/path/to/project")]

        >>> # Multiple workspaces
        >>> resolve_workspaces(workspace_paths=["/path/a", "/path/b"])
        [Path("/path/a"), Path("/path/b")]

        >>> # From environment variable
        >>> os.environ["DOPE_WORKSPACES"] = "/path/a,/path/b"
        >>> resolve_workspaces()
        [Path("/path/a"), Path("/path/b")]

        >>> # Fallback to current directory
        >>> resolve_workspaces(fallback_to_current=True)
        [Path("/current/working/directory")]
    """
    workspace_inputs: List[str] = []

    # Priority 1: Explicit list
    if workspace_paths:
        workspace_inputs.extend(workspace_paths)

    # Priority 2: Single explicit path
    elif workspace_path:
        workspace_inputs.append(workspace_path)

    # Priority 3: Environment variable
    if not workspace_inputs:
        env_value = os.getenv(env_var_name)
        if env_value:
            # Support both comma and semicolon as separators
            workspace_inputs.extend(
                [
                    item.strip()
                    for item in env_value.replace(";", ",").split(",")
                    if item.strip()
                ]
            )

    # Priority 4: Fallback to current directory
    if not workspace_inputs and fallback_to_current:
        workspace_inputs = [str(Path.cwd())]

    # Resolve all paths (expand user, resolve relative paths)
    resolved = [Path(path).expanduser().resolve() for path in workspace_inputs]

    return resolved


def is_multi_workspace(workspaces: List[Path]) -> bool:
    """
    Check if multiple workspaces are being used.

    Args:
        workspaces: List of workspace paths

    Returns:
        True if more than one workspace, False otherwise
    """
    return len(workspaces) > 1


def aggregate_multi_workspace_results(
    results: List[dict],
    workspaces: List[Path],
    result_key: str = "results",
) -> Union[dict, list]:
    """
    Aggregate results from multiple workspaces into standard format.

    Single workspace returns: Original result (backward compatible)
    Multiple workspaces returns: Aggregated dict with metadata

    Args:
        results: List of results (one per workspace)
        workspaces: List of workspace paths (must match results length)
        result_key: Key to use for results in aggregated response

    Returns:
        Single workspace: results[0] (original format)
        Multiple workspaces: {
            "workspace_count": 2,
            "total_results": 10,
            "results": [
                {"workspace": "/path1", "results": [...], "result_count": 5},
                {"workspace": "/path2", "results": [...], "result_count": 5}
            ]
        }

    Examples:
        >>> results = [
        ...     [{"file": "a.py"}, {"file": "b.py"}],
        ...     [{"file": "c.py"}]
        ... ]
        >>> workspaces = [Path("/ws1"), Path("/ws2")]
        >>> aggregate_multi_workspace_results(results, workspaces)
        {
            "workspace_count": 2,
            "total_results": 3,
            "results": [
                {"workspace": "/ws1", "results": [...], "result_count": 2},
                {"workspace": "/ws2", "results": [...], "result_count": 1}
            ]
        }
    """
    if len(results) != len(workspaces):
        raise ValueError(
            f"Results length ({len(results)}) must match workspaces length ({len(workspaces)})"
        )

    # Single workspace: return original result (backward compatible)
    if len(results) == 1:
        return results[0]

    # Multiple workspaces: aggregate with metadata
    aggregated = []
    total_count = 0

    for workspace, result in zip(workspaces, results):
        # Handle both list and dict results
        if isinstance(result, list):
            result_count = len(result)
        elif isinstance(result, dict):
            # Try to get count from result if available
            result_count = result.get("count", result.get("total_results", 0))
        else:
            result_count = 0

        aggregated.append(
            {
                "workspace": str(workspace),
                result_key: result,
                "result_count": result_count,
            }
        )
        total_count += result_count

    return {
        "workspace_count": len(aggregated),
        "total_results": total_count,
        result_key: aggregated,
    }


def workspace_to_identifier(workspace: Path) -> str:
    """
    Convert workspace path to a stable identifier for caching/keys.

    Args:
        workspace: Workspace path

    Returns:
        URL-safe identifier based on workspace path

    Example:
        >>> workspace_to_identifier(Path("/home/user/my-project"))
        "home_user_my-project"
    """
    # Use relative to home if possible for portability
    try:
        from pathlib import Path as _Path
        home = _Path.home()
        try:
            relative = workspace.relative_to(home)
            identifier = str(relative).replace("/", "_").replace("\\", "_")
        except ValueError:
            # Not relative to home, use absolute
            identifier = str(workspace.resolve()).replace("/", "_").replace("\\", "_").lstrip("_")
    except Exception as e:
        # Fallback: use absolute path
        identifier = str(workspace.resolve()).replace("/", "_").replace("\\", "_").lstrip("_")
    
        logger.error(f"Error: {e}")
    # Make URL/database safe: replace spaces and special chars
    identifier = identifier.replace(" ", "_")
    identifier = identifier.replace("-", "_")
    
    return identifier


def parse_workspace_cli_args(
    args: Optional[List[str]] = None,
    arg_name: str = "--workspace",
) -> List[str]:
    """
    Parse workspace paths from CLI arguments.

    Supports repeatable arguments: --workspace /path1 --workspace /path2

    Args:
        args: List of CLI arguments (defaults to sys.argv)
        arg_name: Name of the workspace argument (default: --workspace)

    Returns:
        List of workspace path strings

    Example:
        >>> args = ["script.py", "--workspace", "/path1", "--workspace", "/path2"]
        >>> parse_workspace_cli_args(args)
        ["/path1", "/path2"]
    """
    if args is None:
        import sys
        args = sys.argv

    workspaces = []
    i = 0
    while i < len(args):
        if args[i] == arg_name or args[i].startswith(f"{arg_name}="):
            if "=" in args[i]:
                # Handle --workspace=/path format
                workspaces.append(args[i].split("=", 1)[1])
            elif i + 1 < len(args):
                # Handle --workspace /path format
                workspaces.append(args[i + 1])
                i += 1
        i += 1

    return workspaces


# Backward compatibility aliases
resolve_explicit_workspaces = resolve_workspaces
_resolve_explicit_workspaces = resolve_workspaces
