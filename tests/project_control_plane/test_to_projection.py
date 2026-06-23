"""
Tests for the generic PCP-Core Task-Orchestrator projection-only visibility module.

Covers:
- project_orchestrator_state on sample items+deps → correct structure.
- Projection is NEVER proof: is_proof False, authority "NONE", surface_class "PROJECTION".
- mcp_write_performed is always False.
- Input lists are NOT mutated.
- forbid_mcp_write raises ProjectionWriteForbidden for EACH write tool.
- forbid_mcp_write raises ProjectionWriteForbidden for unknown tools (fail-closed).
- forbid_mcp_write returns None for each recognised read tool.
- No-write source scan: module source contains write-tool names only in _WRITE_TOOLS,
  not as invocations.
- ValueError on malformed input (non-list items, empty source_ref, missing id).
- harvest_projection with a FAKE runner → valid projection; no live MCP.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from dopemux.pcp.task_orchestrator_projection import (
    ProjectionWriteForbidden,
    _READ_TOOLS,
    _WRITE_TOOLS,
    forbid_mcp_write,
    harvest_projection,
    project_orchestrator_state,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

_SOURCE_REF = "workspace:/test/project"
_GENERATED_AT = "2026-06-22T00:00:00Z"

_SAMPLE_ITEMS: list[dict] = [
    {
        "id": "item-001",
        "title": "Root task",
        "role": "root",
        "depth": 0,
        "status_label": "queue",
    },
    {
        "id": "item-002",
        "title": "Child task",
        "role": "leaf",
        "depth": 1,
        "status_label": "work",
    },
]

_SAMPLE_DEPS: list[dict] = [
    {"from_id": "item-001", "to_id": "item-002", "type": "BLOCKS"},
]


def _project(**kwargs: Any) -> dict:
    """Shorthand: call project_orchestrator_state with defaults."""
    return project_orchestrator_state(
        kwargs.get("items", list(_SAMPLE_ITEMS)),
        kwargs.get("dependencies", list(_SAMPLE_DEPS)),
        source_ref=kwargs.get("source_ref", _SOURCE_REF),
        generated_at=kwargs.get("generated_at", _GENERATED_AT),
    )


# ---------------------------------------------------------------------------
# 1. Basic structure and field values
# ---------------------------------------------------------------------------

class TestProjectOrchestratorStateStructure:
    def test_schema_version(self) -> None:
        result = _project()
        assert result["schema_version"] == "pcp.to_projection.v0"

    def test_surface_class(self) -> None:
        result = _project()
        assert result["surface_class"] == "PROJECTION"

    def test_is_proof_false(self) -> None:
        result = _project()
        assert result["is_proof"] is False

    def test_authority_none(self) -> None:
        result = _project()
        assert result["authority"] == "NONE"

    def test_mcp_write_performed_false(self) -> None:
        result = _project()
        assert result["mcp_write_performed"] is False

    def test_source_truth_refs_contains_source_ref(self) -> None:
        result = _project()
        assert _SOURCE_REF in result["source_truth_refs"]

    def test_generated_at_preserved(self) -> None:
        result = _project()
        assert result["generated_at"] == _GENERATED_AT

    def test_items_projected_with_read_only_fields(self) -> None:
        result = _project()
        assert len(result["items"]) == 2
        item_ids = {it["id"] for it in result["items"]}
        assert item_ids == {"item-001", "item-002"}

    def test_item_fields_are_read_only_subset(self) -> None:
        result = _project()
        for item in result["items"]:
            assert set(item.keys()) == {"id", "title", "role", "depth", "status_label"}

    def test_items_values_correct(self) -> None:
        result = _project()
        by_id = {it["id"]: it for it in result["items"]}
        assert by_id["item-001"]["title"] == "Root task"
        assert by_id["item-001"]["role"] == "root"
        assert by_id["item-001"]["depth"] == 0
        assert by_id["item-001"]["status_label"] == "queue"
        assert by_id["item-002"]["title"] == "Child task"
        assert by_id["item-002"]["status_label"] == "work"

    def test_dependencies_projected(self) -> None:
        result = _project()
        assert len(result["dependencies"]) == 1
        dep = result["dependencies"][0]
        assert dep["from_id"] == "item-001"
        assert dep["to_id"] == "item-002"
        assert dep["type"] == "BLOCKS"

    def test_dependency_fields_are_subset(self) -> None:
        result = _project()
        for dep in result["dependencies"]:
            assert set(dep.keys()) == {"from_id", "to_id", "type"}

    def test_empty_items_and_deps(self) -> None:
        result = project_orchestrator_state(
            [], [], source_ref=_SOURCE_REF, generated_at=_GENERATED_AT
        )
        assert result["items"] == []
        assert result["dependencies"] == []
        assert result["is_proof"] is False


# ---------------------------------------------------------------------------
# 2. Projection is NEVER labelled proof
# ---------------------------------------------------------------------------

class TestProjectionIsNeverProof:
    def test_is_proof_is_false(self) -> None:
        result = _project()
        assert result["is_proof"] is False

    def test_authority_is_none_string(self) -> None:
        result = _project()
        assert result["authority"] == "NONE"

    def test_no_key_claims_proof(self) -> None:
        result = _project()
        # No key anywhere in the result should have a value that claims proof
        assert result.get("is_proof") is not True
        assert result.get("authority") != "FULL"
        assert result.get("authority") != "MERGE"
        assert result.get("authority") != "PM"

    def test_surface_class_is_projection_not_proof(self) -> None:
        result = _project()
        assert result["surface_class"] == "PROJECTION"
        assert result["surface_class"] != "PROOF"

    def test_is_proof_and_authority_together(self) -> None:
        result = _project()
        assert result["is_proof"] is False
        assert result["authority"] == "NONE"


# ---------------------------------------------------------------------------
# 3. Input lists are NOT mutated
# ---------------------------------------------------------------------------

class TestInputListsNotMutated:
    def test_items_list_not_mutated(self) -> None:
        items = [{"id": "x", "title": "X", "role": "leaf", "depth": 0, "status_label": "queue"}]
        items_original_len = len(items)
        items_original_first = dict(items[0])
        _project(items=items, dependencies=[])
        assert len(items) == items_original_len
        assert items[0] == items_original_first

    def test_deps_list_not_mutated(self) -> None:
        deps = [{"from_id": "a", "to_id": "b", "type": "BLOCKS"}]
        deps_original = [dict(d) for d in deps]
        _project(items=[{"id": "a"}], dependencies=deps)
        assert deps == deps_original

    def test_projection_items_are_new_dicts(self) -> None:
        items = [{"id": "item-001", "title": "T", "role": "root", "depth": 0, "status_label": "q"}]
        result = _project(items=items, dependencies=[])
        # Mutating the projected item should not affect the original
        result["items"][0]["title"] = "MUTATED"
        assert items[0]["title"] == "T"


# ---------------------------------------------------------------------------
# 4. forbid_mcp_write: write tools raise ProjectionWriteForbidden
# ---------------------------------------------------------------------------

class TestForbidMcpWriteRaisesForWriteTools:
    @pytest.mark.parametrize("tool_name", sorted(_WRITE_TOOLS))
    def test_write_tool_raises(self, tool_name: str) -> None:
        with pytest.raises(ProjectionWriteForbidden):
            forbid_mcp_write(tool_name)

    def test_manage_items_specifically(self) -> None:
        with pytest.raises(ProjectionWriteForbidden, match="manage_items"):
            forbid_mcp_write("manage_items")

    def test_advance_item_specifically(self) -> None:
        with pytest.raises(ProjectionWriteForbidden, match="advance_item"):
            forbid_mcp_write("advance_item")

    def test_manage_notes_specifically(self) -> None:
        with pytest.raises(ProjectionWriteForbidden):
            forbid_mcp_write("manage_notes")

    def test_manage_dependencies_specifically(self) -> None:
        with pytest.raises(ProjectionWriteForbidden):
            forbid_mcp_write("manage_dependencies")

    def test_claim_item_specifically(self) -> None:
        with pytest.raises(ProjectionWriteForbidden):
            forbid_mcp_write("claim_item")

    def test_complete_tree_specifically(self) -> None:
        with pytest.raises(ProjectionWriteForbidden):
            forbid_mcp_write("complete_tree")

    def test_create_work_tree_specifically(self) -> None:
        with pytest.raises(ProjectionWriteForbidden):
            forbid_mcp_write("create_work_tree")


# ---------------------------------------------------------------------------
# 5. forbid_mcp_write: unknown tools raise ProjectionWriteForbidden (fail-closed)
# ---------------------------------------------------------------------------

class TestForbidMcpWriteFailClosedForUnknownTools:
    @pytest.mark.parametrize("unknown", [
        "delete_everything",
        "drop_table",
        "exec_sql",
        "unknown_tool",
        "",
        "QUERY_ITEMS",  # case-sensitive: uppercase not recognised
        "Query_Items",
        "bogus",
        "rm_rf",
    ])
    def test_unknown_tool_raises(self, unknown: str) -> None:
        with pytest.raises(ProjectionWriteForbidden):
            forbid_mcp_write(unknown)

    def test_error_message_mentions_deny_default(self) -> None:
        with pytest.raises(ProjectionWriteForbidden, match="fail-closed"):
            forbid_mcp_write("delete_everything")


# ---------------------------------------------------------------------------
# 6. forbid_mcp_write: read tools return None (no raise)
# ---------------------------------------------------------------------------

class TestForbidMcpWritePermitsReadTools:
    @pytest.mark.parametrize("tool_name", sorted(_READ_TOOLS))
    def test_read_tool_returns_none(self, tool_name: str) -> None:
        result = forbid_mcp_write(tool_name)
        assert result is None

    def test_query_items_returns_none(self) -> None:
        assert forbid_mcp_write("query_items") is None

    def test_query_dependencies_returns_none(self) -> None:
        assert forbid_mcp_write("query_dependencies") is None

    def test_get_context_returns_none(self) -> None:
        assert forbid_mcp_write("get_context") is None


# ---------------------------------------------------------------------------
# 7. No-write source scan: write-tool names appear only in _WRITE_TOOLS
# ---------------------------------------------------------------------------

class TestNoWriteSourceScan:
    """Assert the module source never calls a write tool."""

    def _get_source(self) -> str:
        import dopemux.pcp.task_orchestrator_projection as _mod
        return inspect.getsource(_mod)

    def test_advance_item_not_called(self) -> None:
        src = self._get_source()
        assert "advance_item(" not in src, (
            "advance_item( appears in module source as a call — forbidden"
        )

    def test_manage_items_not_called(self) -> None:
        src = self._get_source()
        assert "manage_items(" not in src, (
            "manage_items( appears in module source as a call — forbidden"
        )

    def test_manage_notes_not_called(self) -> None:
        src = self._get_source()
        assert "manage_notes(" not in src

    def test_manage_dependencies_not_called(self) -> None:
        src = self._get_source()
        assert "manage_dependencies(" not in src

    def test_claim_item_not_called(self) -> None:
        src = self._get_source()
        assert "claim_item(" not in src

    def test_complete_tree_not_called(self) -> None:
        src = self._get_source()
        assert "complete_tree(" not in src

    def test_create_work_tree_not_called(self) -> None:
        src = self._get_source()
        assert "create_work_tree(" not in src

    def test_write_tool_names_only_in_frozenset_definition(self) -> None:
        """Write-tool strings appear ONLY in _WRITE_TOOLS literal, not as invocations."""
        src = self._get_source()
        # Each write tool name must appear at least once (in the frozenset definition)
        # but must NOT appear with a trailing '(' (invocation pattern)
        for tool in _WRITE_TOOLS:
            assert tool in src, f"{tool!r} not found in module source at all"
            assert f"{tool}(" not in src, (
                f"{tool}( found in module source — write tool invocation is forbidden"
            )


# ---------------------------------------------------------------------------
# 8. ValueError on malformed input
# ---------------------------------------------------------------------------

class TestValueErrorOnMalformedInput:
    def test_non_list_items_raises(self) -> None:
        with pytest.raises(ValueError, match="items"):
            project_orchestrator_state(
                "not a list",  # type: ignore[arg-type]
                [],
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
            )

    def test_none_items_raises(self) -> None:
        with pytest.raises(ValueError, match="items"):
            project_orchestrator_state(
                None,  # type: ignore[arg-type]
                [],
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
            )

    def test_dict_items_raises(self) -> None:
        with pytest.raises(ValueError, match="items"):
            project_orchestrator_state(
                {},  # type: ignore[arg-type]
                [],
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
            )

    def test_non_list_dependencies_raises(self) -> None:
        with pytest.raises(ValueError, match="dependencies"):
            project_orchestrator_state(
                [],
                "not a list",  # type: ignore[arg-type]
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
            )

    def test_empty_source_ref_raises(self) -> None:
        with pytest.raises(ValueError, match="source_ref"):
            project_orchestrator_state(
                [], [], source_ref="", generated_at=_GENERATED_AT
            )

    def test_none_source_ref_raises(self) -> None:
        with pytest.raises(ValueError, match="source_ref"):
            project_orchestrator_state(
                [], [], source_ref=None, generated_at=_GENERATED_AT  # type: ignore[arg-type]
            )

    def test_item_missing_id_raises(self) -> None:
        with pytest.raises(ValueError, match="'id'"):
            project_orchestrator_state(
                [{"title": "no id here"}],
                [],
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
            )

    def test_non_dict_item_raises(self) -> None:
        with pytest.raises(ValueError):
            project_orchestrator_state(
                ["not a dict"],  # type: ignore[list-item]
                [],
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
            )


# ---------------------------------------------------------------------------
# 9. harvest_projection with a FAKE runner
# ---------------------------------------------------------------------------

class TestHarvestProjectionWithFakeRunner:
    """harvest_projection must use the injected runner and produce a valid projection."""

    _CANNED_DATA = {
        "items": [
            {
                "id": "root-001",
                "title": "Root",
                "role": "root",
                "depth": 0,
                "status_label": "work",
            },
            {
                "id": "leaf-002",
                "title": "Leaf",
                "role": "leaf",
                "depth": 1,
                "status_label": "queue",
            },
        ],
        "dependencies": [
            {"from_id": "root-001", "to_id": "leaf-002", "type": "BLOCKS"},
        ],
    }

    def _make_fake_runner(self) -> tuple[list, Any]:
        calls: list[dict] = []

        def fake_runner(*, source_ref: str) -> dict:
            calls.append({"source_ref": source_ref})
            return self._CANNED_DATA

        return calls, fake_runner

    def test_fake_runner_is_used(self) -> None:
        calls, fake_runner = self._make_fake_runner()
        harvest_projection(
            source_ref=_SOURCE_REF,
            generated_at=_GENERATED_AT,
            runner=fake_runner,
        )
        assert len(calls) == 1, "Fake runner was never called"

    def test_source_ref_passed_to_runner(self) -> None:
        calls, fake_runner = self._make_fake_runner()
        harvest_projection(
            source_ref=_SOURCE_REF,
            generated_at=_GENERATED_AT,
            runner=fake_runner,
        )
        assert calls[0]["source_ref"] == _SOURCE_REF

    def test_returns_valid_projection(self) -> None:
        _, fake_runner = self._make_fake_runner()
        result = harvest_projection(
            source_ref=_SOURCE_REF,
            generated_at=_GENERATED_AT,
            runner=fake_runner,
        )
        assert result["schema_version"] == "pcp.to_projection.v0"
        assert result["is_proof"] is False
        assert result["authority"] == "NONE"
        assert result["surface_class"] == "PROJECTION"
        assert result["mcp_write_performed"] is False

    def test_items_from_canned_data(self) -> None:
        _, fake_runner = self._make_fake_runner()
        result = harvest_projection(
            source_ref=_SOURCE_REF,
            generated_at=_GENERATED_AT,
            runner=fake_runner,
        )
        assert len(result["items"]) == 2
        ids = {it["id"] for it in result["items"]}
        assert ids == {"root-001", "leaf-002"}

    def test_dependencies_from_canned_data(self) -> None:
        _, fake_runner = self._make_fake_runner()
        result = harvest_projection(
            source_ref=_SOURCE_REF,
            generated_at=_GENERATED_AT,
            runner=fake_runner,
        )
        assert len(result["dependencies"]) == 1
        assert result["dependencies"][0]["type"] == "BLOCKS"

    def test_no_runner_raises_not_implemented_error(self) -> None:
        with pytest.raises(NotImplementedError, match="runner"):
            harvest_projection(
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
                runner=None,
            )

    def test_no_live_mcp_when_runner_provided(self) -> None:
        """Verify no subprocess or live MCP call happens when a fake runner is supplied."""
        import subprocess as _subprocess
        original_run = _subprocess.run
        calls_to_real_subprocess: list = []

        def _spy_run(*args: Any, **kwargs: Any) -> Any:
            calls_to_real_subprocess.append(args)
            return original_run(*args, **kwargs)

        calls, fake_runner = self._make_fake_runner()
        # monkeypatch subprocess.run temporarily
        _subprocess.run = _spy_run  # type: ignore[assignment]
        try:
            harvest_projection(
                source_ref=_SOURCE_REF,
                generated_at=_GENERATED_AT,
                runner=fake_runner,
            )
        finally:
            _subprocess.run = original_run  # type: ignore[assignment]

        assert calls_to_real_subprocess == [], (
            "subprocess.run was called unexpectedly — harvest_projection "
            "with a fake runner must not make live subprocess/MCP calls"
        )
