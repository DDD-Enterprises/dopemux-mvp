"""DAG closure and authority-collision checks over a MacroPacket v2 fixture.

Uses fixtures/valid/macro_packet.v2__w01_w08_dag.json, which models
W01..W08 with parallel group A and the dependency edges: W06 depends on
W02 and W04; W07 depends on W04 and W06; W08 depends on W07. W01 and W07
share the canonical contract document and must serialize its writes, with a
new freeze after composition. Also scans every schema in the set for
placeholder-for-authority property names.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

import pytest

from dopemux.governed_execution.audit_identity.location import exact_head_binding
from dopemux.governed_execution.freeze.lifecycle import (
    AuditBeforeFreeze,
    FreezeLifecycle,
    FreezeState,
    IllegalTransition,
    NewFreeze,
    Unfreeze,
    attach_audit_ref,
)
from dopemux.governed_execution.freeze.receipt import (
    FreezeSubject,
    RepoIdentity,
    author_freeze_receipt,
)
from dopemux.governed_execution.receipts.store import EvidenceRef
from dopemux.governed_execution.receipts.validate import Provenance
from tests.governance.governed_execution.conftest import (
    FIXTURES_DIR,
    REPO_ROOT,
    SCHEMA_FILES,
)

DAG_FIXTURE = FIXTURES_DIR / "valid" / "macro_packet.v2__w01_w08_dag.json"
SHARED_CONTRACT_DOC = "docs/03-reference/governance/governed-execution-contract-v2.md"

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


def _write_surface_collisions(macro: dict) -> list[tuple[str, str, str]]:
    """Report physical overlap even when workstream writer labels differ."""
    collisions = []
    workstreams = macro["workstreams"]
    for i, ws_a in enumerate(workstreams):
        for ws_b in workstreams[i + 1 :]:
            for surface_a in ws_a["write_surface"]:
                for surface_b in ws_b["write_surface"]:
                    if _overlaps(surface_a, surface_b):
                        collisions.append((ws_a["workstream_id"], ws_b["workstream_id"], surface_a))
    return collisions


@pytest.fixture(scope="module")
def dag_macro() -> dict:
    return _load(DAG_FIXTURE)


@pytest.fixture(scope="module")
def ct():
    """Load the existing CT classifier; do not dispatch or admit a package."""
    loader = SourceFileLoader("ct_dag_authority", str(REPO_ROOT / ".control-tower/bin/ct"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_w01_w07_share_canonical_contract_document(dag_macro) -> None:
    assert _write_surface_collisions(dag_macro) == [("W01", "W07", SHARED_CONTRACT_DOC)]
    w07 = next(ws for ws in dag_macro["workstreams"] if ws["workstream_id"] == "W07")
    assert "src/dopemux/w07/" not in w07["write_surface"]


def test_shared_document_writes_are_dependency_serialized(dag_macro, ct) -> None:
    pairs = {
        tuple(pair["workstreams"]): pair["classification"]
        for pair in ct.macro_pairs(dag_macro)
    }
    assert pairs[("W01", "W07")] == "DEPENDENCY_SERIALIZED"
    # Static validation only: this fixture's placeholder references cannot admit execution.
    assert ct.validate_macro_obj(dag_macro, REPO_ROOT) == []
    assert dag_macro["execution_authority"] == "NONE"


def test_shared_document_overlap_without_ordering_fails_closed(dag_macro, ct) -> None:
    tampered = copy.deepcopy(dag_macro)
    for ws in tampered["workstreams"]:
        if ws["workstream_id"] == "W07":
            ws["dependencies"] = []
    assert _is_acyclic(_dependency_graph(tampered))
    pairs = {
        tuple(pair["workstreams"]): pair["classification"]
        for pair in ct.macro_pairs(tampered)
    }
    assert pairs[("W01", "W07")] == "WRITE_OVERLAP"
    assert ct.validate_macro_obj(tampered, REPO_ROOT) == [
        "parallel conflict: W01/W07 WRITE_OVERLAP"
    ]


def test_w07_composition_requires_superseding_freeze(dag_macro) -> None:
    for wid in ("W01", "W07"):
        ws = next(ws for ws in dag_macro["workstreams"] if ws["workstream_id"] == wid)
        assert SHARED_CONTRACT_DOC in ws["write_surface"]

    # Synthetic subjects exercise the existing receipt/lifecycle contract, not a live audit.
    def freeze(content: bytes, head: str, supersedes: EvidenceRef | None = None):
        return author_freeze_receipt(
            FreezeSubject(
                repo_identity=RepoIdentity(
                    origin_url="https://github.com/DDD-Enterprises/dopemux-mvp.git",
                    toplevel="/fixture/repo",
                ),
                base_sha="0" * 40,
                head_sha=head,
                tree_sha=head,
                blobs={SHARED_CONTRACT_DOC: content},
            ),
            validation_refs=[EvidenceRef("proof/validation.json", "1" * 64)],
            review_refs=[],
            frozen_at="2026-09-20T00:00:00Z",
            packet_id="TP-COMPOSITION-TEST",
            macro_id=dag_macro["macro_id"],
            provenance=Provenance(
                verified_by="test_dag_and_authority.py",
                verified_at="2026-09-20T00:00:00Z",
                schema_set_digest="0" * 64,
            ),
            supersedes_freeze_ref=supersedes,
        )

    w01_head, composed_head = "1" * 40, "2" * 40
    original_receipt = freeze(b"W01 contract\n", w01_head)
    original_bytes = json.dumps(original_receipt, sort_keys=True)
    original = FreezeLifecycle.start(original_receipt)
    unfrozen = original.apply(Unfreeze(reason="W07 changes the shared canonical document"))
    with pytest.raises(IllegalTransition, match="supersedes_freeze_ref"):
        unfrozen.apply(NewFreeze(freeze(b"W01 contract plus W07 identity\n", composed_head)))

    old_ref = EvidenceRef("proof/W01/freeze.json", "3" * 64)
    composed_receipt = freeze(b"W01 contract plus W07 identity\n", composed_head, old_ref)
    composed = unfrozen.apply(NewFreeze(composed_receipt))
    assert composed.state is FreezeState.FROZEN
    assert composed.predecessor is not None
    assert composed.predecessor.state is FreezeState.SUPERSEDED
    assert composed_receipt["supersedes_freeze_ref"] == {
        "path": old_ref.path,
        "sha256": old_ref.sha256,
    }
    assert composed_receipt["candidate_digest"] != original_receipt["candidate_digest"]
    assert json.dumps(original_receipt, sort_keys=True) == original_bytes
    assert composed_receipt["authority"] == "NONE"

    old_audit = EvidenceRef("proof/W01/audit.json", "4" * 64)
    with pytest.raises(AuditBeforeFreeze):
        attach_audit_ref(composed, old_audit, w01_head)
    assert not exact_head_binding(w01_head, composed_head, composed_head).bound
    assert not exact_head_binding(w01_head, composed_head, w01_head).bound
    assert exact_head_binding(composed_head, composed_head, composed_head).bound


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
    collisions = _write_surface_collisions(tampered)
    assert ("W02", "W06", "src/dopemux/w02/") in collisions


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
