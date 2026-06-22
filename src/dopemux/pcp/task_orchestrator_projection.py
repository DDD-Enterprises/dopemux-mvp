"""
Generic PCP-Core Task-Orchestrator read/projection-only visibility.

This module provides a READ/PROJECTION-ONLY mapping of Task-Orchestrator state
(items + dependencies) into PCP evidence.  There is NO MCP write path of any
kind.  The projection is explicitly NOT proof, PM-metadata, merge, or
live-write authority.  Any write attempt FAILS CLOSED.

The fail-closed guard (``forbid_mcp_write``) denies all write tools AND any
unrecognised tool by default — unknown tool names are denied, not permitted.

Design invariants
-----------------
* ``is_proof`` is always ``False`` — a projection is never proof.
* ``authority`` is always ``"NONE"`` — this module holds no authority.
* ``mcp_write_performed`` is always ``False`` — const-style sentinel.
* Input lists are copied, never mutated.
* No Task-Orchestrator write tool is called anywhere in this module.

Usage::

    from dopemux.pcp.task_orchestrator_projection import (
        project_orchestrator_state,
        forbid_mcp_write,
        harvest_projection,
    )

    projection = project_orchestrator_state(
        items=[{"id": "abc", "title": "Do work", "role": "leaf",
                "depth": 1, "status_label": "queue"}],
        dependencies=[{"from_id": "abc", "to_id": "xyz", "type": "BLOCKS"}],
        source_ref="workspace:/path/to/project",
        generated_at="2026-06-22T00:00:00Z",
    )
"""

from __future__ import annotations

from typing import Any, Callable


# ---------------------------------------------------------------------------
# Exception: write operations are forbidden
# ---------------------------------------------------------------------------

class ProjectionWriteForbidden(Exception):
    """Raised when any write tool or unrecognised tool is invoked against the
    Task-Orchestrator projection surface.

    The fail-closed default means that unknown tool names are denied rather
    than allowed — only explicitly recognised read tools pass through.
    """


# ---------------------------------------------------------------------------
# Tool classification — immutable frozensets
# ---------------------------------------------------------------------------

_WRITE_TOOLS: frozenset[str] = frozenset({
    "manage_items",
    "advance_item",
    "manage_notes",
    "manage_dependencies",
    "claim_item",
    "complete_tree",
    "create_work_tree",
})

_READ_TOOLS: frozenset[str] = frozenset({
    "query_items",
    "query_dependencies",
    "query_notes",
    "get_context",
    "get_blocked_items",
    "get_next_item",
    "get_next_status",
})


# ---------------------------------------------------------------------------
# Fail-closed write guard
# ---------------------------------------------------------------------------

def forbid_mcp_write(tool_name: str) -> None:
    """Fail-closed guard: raise ``ProjectionWriteForbidden`` for any non-read tool.

    Rules (evaluated in order):
    1. If *tool_name* is in ``_WRITE_TOOLS`` → raise.
    2. If *tool_name* is NOT in ``_READ_TOOLS`` → raise (unknown = deny).
    3. Return ``None`` only for explicitly recognised read tools.

    Parameters
    ----------
    tool_name:
        The Task-Orchestrator MCP tool name to validate.

    Returns
    -------
    None
        Only when *tool_name* is an explicit member of ``_READ_TOOLS``.

    Raises
    ------
    ProjectionWriteForbidden
        For write tools, for unrecognised tool names, or for any other
        non-read tool.
    """
    if tool_name in _WRITE_TOOLS:
        raise ProjectionWriteForbidden(
            f"Write tool {tool_name!r} is forbidden in the TO projection surface. "
            "This module is READ/PROJECTION-ONLY — no MCP write path exists."
        )
    if tool_name not in _READ_TOOLS:
        raise ProjectionWriteForbidden(
            f"Unrecognised tool {tool_name!r} is denied by default (fail-closed). "
            "Only explicitly recognised read tools are permitted: "
            f"{sorted(_READ_TOOLS)!r}"
        )
    # tool_name is in _READ_TOOLS — permit


# ---------------------------------------------------------------------------
# Pure projection function
# ---------------------------------------------------------------------------

def project_orchestrator_state(
    items: list[dict],
    dependencies: list[dict],
    *,
    source_ref: str,
    generated_at: str,
) -> dict:
    """Project Task-Orchestrator state into a read-only PCP evidence dict.

    This is a **pure**, **read-only** function.  Input lists are copied and
    never mutated.  The returned dict:

    * always has ``is_proof: False`` — a projection is NEVER proof.
    * always has ``authority: "NONE"`` — holds no authority.
    * always has ``mcp_write_performed: False`` — const-style sentinel.
    * always has ``surface_class: "PROJECTION"``.

    Parameters
    ----------
    items:
        List of item dicts from Task-Orchestrator (e.g. from ``query_items``).
        Each must contain at least an ``"id"`` key.  Malformed items (missing
        ``"id"``) raise ``ValueError``.
    dependencies:
        List of dependency dicts (e.g. from ``query_dependencies``).  Each
        should contain ``from_id``, ``to_id``, and ``type``.
    source_ref:
        Non-empty string identifying the Task-Orchestrator data source
        (e.g. ``"workspace:/path"`` or a root item UUID).
    generated_at:
        ISO 8601 datetime string for when the projection was assembled.

    Returns
    -------
    dict
        A projection dict with schema_version, surface_class, is_proof,
        authority, mcp_write_performed, source_truth_refs, generated_at,
        items (read-only subset), and dependencies.

    Raises
    ------
    ValueError
        If ``items`` or ``dependencies`` are not lists, if ``source_ref`` is
        empty, or if any item is missing the required ``"id"`` key.
    """
    if not isinstance(items, list):
        raise ValueError(
            f"items must be a list; got {type(items).__name__!r}"
        )
    if not isinstance(dependencies, list):
        raise ValueError(
            f"dependencies must be a list; got {type(dependencies).__name__!r}"
        )
    if not source_ref or not isinstance(source_ref, str):
        raise ValueError(
            f"source_ref must be a non-empty string; got {source_ref!r}"
        )

    # Project items — read-only subset, copy (no mutation of inputs)
    projected_items: list[dict[str, Any]] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            raise ValueError(
                f"Each item must be a dict; got {type(raw_item).__name__!r}: {raw_item!r}"
            )
        if "id" not in raw_item:
            raise ValueError(
                f"Item is missing required 'id' key: {raw_item!r}"
            )
        projected_items.append({
            "id": raw_item["id"],
            "title": raw_item.get("title", ""),
            "role": raw_item.get("role", ""),
            "depth": raw_item.get("depth", 0),
            "status_label": raw_item.get("status_label", ""),
        })

    # Project dependencies — copy (no mutation of inputs)
    projected_deps: list[dict[str, Any]] = []
    for raw_dep in dependencies:
        if not isinstance(raw_dep, dict):
            raise ValueError(
                f"Each dependency must be a dict; got {type(raw_dep).__name__!r}: {raw_dep!r}"
            )
        projected_deps.append({
            "from_id": raw_dep.get("from_id", ""),
            "to_id": raw_dep.get("to_id", ""),
            "type": raw_dep.get("type", ""),
        })

    return {
        "schema_version": "pcp.to_projection.v0",
        "surface_class": "PROJECTION",
        "is_proof": False,             # projection is NEVER proof
        "authority": "NONE",           # holds no authority
        "mcp_write_performed": False,  # const-style: always False
        "source_truth_refs": [source_ref],
        "generated_at": generated_at,
        "items": projected_items,
        "dependencies": projected_deps,
    }


# ---------------------------------------------------------------------------
# Injectable harvest (thin wrapper — no live MCP calls by default)
# ---------------------------------------------------------------------------

def harvest_projection(
    *,
    source_ref: str,
    generated_at: str,
    runner: Callable[..., dict] | None = None,
) -> dict:
    """Read-only harvest using an injectable runner, then project the result.

    The *runner* is called to obtain raw ``{"items": [...], "dependencies": [...]}``
    data from read-only Task-Orchestrator tools (``query_items`` overview +
    ``query_dependencies``).  If *runner* is ``None``, ``NotImplementedError``
    is raised — no live MCP call is made by default.

    Only read tools are permitted inside *runner*.  Callers must ensure their
    runner uses ``query_items`` / ``query_dependencies`` exclusively; the
    module itself cannot enforce this at the runner boundary, but
    ``forbid_mcp_write`` is available for runners to self-validate.

    Parameters
    ----------
    source_ref:
        Non-empty string identifying the data source (passed through to
        ``project_orchestrator_state``).
    generated_at:
        ISO 8601 datetime string (passed through).
    runner:
        Optional callable that returns ``{"items": list, "dependencies": list}``
        from Task-Orchestrator read tools.  Defaults to ``None`` (raises
        ``NotImplementedError``).  Tests supply a fake runner with canned data.

    Returns
    -------
    dict
        Projection dict produced by ``project_orchestrator_state``.

    Raises
    ------
    NotImplementedError
        If *runner* is ``None`` (no live MCP call is made by default).
    ValueError
        Propagated from ``project_orchestrator_state`` on malformed data.
    """
    if runner is None:
        raise NotImplementedError(
            "harvest_projection requires an injectable runner. "
            "No live MCP call is made by default. "
            "Supply a runner that calls only read tools "
            f"(one of: {sorted(_READ_TOOLS)!r})."
        )

    raw = runner(source_ref=source_ref)
    return project_orchestrator_state(
        raw.get("items", []),
        raw.get("dependencies", []),
        source_ref=source_ref,
        generated_at=generated_at,
    )
