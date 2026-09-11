"""DAG closure and authority-collision checks over a MacroPacket v2 fixture.

Uses fixtures/valid/macro_packet.v2__w01_w08_dag.json, which models
W01..W08 with parallel group A and the dependency edges: W06 depends on
W02 and W04; W07 depends on W04 and W06; W08 depends on W07. Also scans
every schema in the set for placeholder-for-authority property names.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from tests.governance.governed_execution.conftest import FIXTURES_DIR, SCHEMA_FILES

DAG_FIXTURE = FIXTURES_DIR / "valid" / "macro_packet.v2__w01_w08_dag.json"

_FORBIDDEN_PROPERTY_NAMES = {"merge_ready", "dispatch_eligible", "approved", "ready"}


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="ascii") as fh:
        return json.load(fh)


def _dependency_graph(macro: dict) -> dict[str, list[str]]:
    return {ws["workstream_id"]: list(ws["dependencies"]) for ws in macro["workstreams"]}


def _is_acyclic(graph: dict[str, list[str]]) -> bool:
    WHITE, GREY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def visit(node: str) -> bool:
        color[node] = GREY
        for dep in graph.get(node, []):
            if dep not in graph:
                continue  # unresolved deps are checked separately
            if color[dep] == GREY:
                return False
            if color[dep] == WHITE and not visit(dep):
                return False
        color[node] = BLACK
        return True

    return all(visit(node) for node in graph if color[node] == WHITE)


def _overlaps(a: str, b: str) -> bool:
    if a == b:
        return True
    a_dir = a if a.endswith("/") else None
    b_dir = b if b.endswith("/") else None
    if a_dir and b.startswith(a_dir):
        return True
    if b_dir and a.startswith(b_dir):
        return True
    return False


def _writer_collisions(macro: dict) -> list[tuple[str, str, str]]:
    collisions = []
    workstreams = macro["workstreams"]
    for i, ws_a in enumerate(workstreams):
        for ws_b in workstreams[i + 1 :]:
            shared_writers = set(ws_a["canonical_writers"]) & set(ws_b["canonical_writers"])
            if not shared_writers:
                continue
            for surface_a in ws_a["write_surface"]:
                for surface_b in ws_b["write_surface"]:
                    if _overlaps(surface_a, surface_b):
                        collisions.append((ws_a["workstream_id"], ws_b["workstream_id"], surface_a))
    return collisions


@pytest.fixture(scope="module")
def dag_macro() -> dict:
    return _load(DAG_FIXTURE)


def test_dag_fixture_is_acyclic(dag_macro) -> None:
    graph = _dependency_graph(dag_macro)
    assert _is_acyclic(graph), "W01..W08 DAG fixture must be acyclic"


def test_dag_fixture_dependencies_resolve(dag_macro) -> None:
    graph = _dependency_graph(dag_macro)
    ids = set(graph)
    for wid, deps in graph.items():
        unresolved = set(deps) - ids
        assert not unresolved, f"{wid}: dependencies do not resolve to a workstream_id: {unresolved}"


def test_w02_w03_w04_w05_write_surfaces_pairwise_disjoint(dag_macro) -> None:
    surfaces = {
        ws["workstream_id"]: ws["write_surface"]
        for ws in dag_macro["workstreams"]
        if ws["workstream_id"] in {"W02", "W03", "W04", "W05"}
    }
    ids = sorted(surfaces)
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            for surface_a in surfaces[a]:
                for surface_b in surfaces[b]:
                    assert not _overlaps(surface_a, surface_b), (
                        f"{a} write_surface {surface_a!r} overlaps {b} write_surface {surface_b!r}"
                    )


def test_parallel_group_a_is_w02_through_w05(dag_macro) -> None:
    group_a = {
        ws["workstream_id"] for ws in dag_macro["workstreams"] if ws["parallel_group"] == "A"
    }
    assert group_a == {"W02", "W03", "W04", "W05"}


def test_expected_dependency_edges(dag_macro) -> None:
    graph = _dependency_graph(dag_macro)
    assert set(graph["W06"]) == {"W02", "W04"}
    assert set(graph["W07"]) == {"W04", "W06"}
    assert set(graph["W08"]) == {"W07"}


def test_no_canonical_writer_overlap_in_dag_fixture(dag_macro) -> None:
    assert _writer_collisions(dag_macro) == []


def test_negative_cycle_is_detected(dag_macro) -> None:
    tampered = copy.deepcopy(dag_macro)
    # W02 depends on W01; inject W01 -> W02 -> ... -> W01 by making W01
    # (which has no declared deps) depend back on W08, which chains through
    # W07 -> W06 -> W02 -> W01.
    for ws in tampered["workstreams"]:
        if ws["workstream_id"] == "W01":
            ws["dependencies"] = ["W08"]
    cyclic_graph = _dependency_graph(tampered)
    assert not _is_acyclic(cyclic_graph), "tampered fixture with an injected cycle must be detected as cyclic"


def test_negative_writer_collision_is_detected(dag_macro) -> None:
    tampered = copy.deepcopy(dag_macro)
    for ws in tampered["workstreams"]:
        if ws["workstream_id"] == "W06":
            ws["canonical_writers"] = ["w02"]
            ws["write_surface"] = ["src/dopemux/w02/"]
    collisions = _writer_collisions(tampered)
    assert collisions, "tampered fixture with W06 sharing W02's writer and prefix must be detected as a collision"


@pytest.mark.parametrize("shortname,path", sorted(SCHEMA_FILES.items()))
def test_no_placeholder_authority_properties(shortname, path) -> None:
    schema = _load(path)

    def _walk(node: Any, hits: list[str]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    for prop_name in value:
                        if prop_name in _FORBIDDEN_PROPERTY_NAMES:
                            hits.append(prop_name)
                _walk(value, hits)
        elif isinstance(node, list):
            for item in node:
                _walk(item, hits)

    hits: list[str] = []
    _walk(schema, hits)
    assert not hits, f"{shortname}: forbidden placeholder-for-authority property name(s): {hits}"
