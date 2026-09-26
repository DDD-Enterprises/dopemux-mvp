"""AggregateReturnEnvelope builder tests (W05).

Covers: the built envelope validates against
schemas/governed_execution/aggregate_return_envelope.v1.schema.json;
merge_authorized/activation_authorized/authority/is_canonical_truth are
fixed regardless of input; a model_calls total mismatch raises ValueError;
and no evidence bytes are copied in (no 'content' or 'payload' key
anywhere in the built envelope).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from dopemux.governed_execution.join.envelope import EnvelopeInvalid, build_envelope
from dopemux.governed_execution.join.evaluate import derive_macro_status, evaluate_all, next_legal_action
from dopemux.governed_execution.join.types import JoinDecl, ReturnRef, WorkstreamResult

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCHEMA_DIR = _REPO_ROOT / "schemas" / "governed_execution"

_FORBIDDEN_KEYS = {"content", "payload"}


def _ws(workstream_id: str, status: str) -> WorkstreamResult:
    return WorkstreamResult(
        workstream_id=workstream_id,
        status=status,
        subject_sha="NONE",
        return_ref=ReturnRef(path=f"artifacts/{workstream_id}.json", sha256="0" * 64),
    )


def _validator() -> Draft7Validator:
    resources = []
    for path in sorted(_SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="ascii"))
        resources.append(Resource(contents=schema, specification=DRAFT7))
    registry = Registry().with_resources((resource.id(), resource) for resource in resources)
    schema = json.loads((_SCHEMA_DIR / "aggregate_return_envelope.v1.schema.json").read_text(encoding="ascii"))
    return Draft7Validator(schema, registry=registry)


def _empty_mcp() -> dict[str, Any]:
    return {
        "preflight": "NOT_RUN",
        "servers_used": [],
        "tools_used": [],
        "domain_reads": 0,
        "domain_writes": 0,
        "fallbacks": [],
        "task_orchestrator_state": "NONE",
    }


def _assert_no_forbidden_keys(node: Any) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            assert key not in _FORBIDDEN_KEYS
            _assert_no_forbidden_keys(value)
    elif isinstance(node, list):
        for item in node:
            _assert_no_forbidden_keys(item)


def _build_fixture_envelope(macro_status_override: str | None = None) -> dict[str, Any]:
    results = (_ws("W01", "PASS"), _ws("W02", "BLOCKED"), _ws("W03", "PASS"), _ws("W04", "PASS"))
    decls = (
        JoinDecl(join_id="J_A", join_type="ALL_REQUIRED", requires=("W01",)),
        JoinDecl(join_id="J_PARALLEL", join_type="ALL_REQUIRED", requires=("W02", "W03", "W04")),
    )
    join_results = evaluate_all(decls, results)
    macro_status = macro_status_override or derive_macro_status(results, join_results)
    action = next_legal_action(results, macro_status)
    return build_envelope(
        macro_id="MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001",
        results=results,
        join_results=join_results,
        macro_status=macro_status,
        model_calls={"team_lead": 0, "implementers": 0, "auditors": 0, "total": 0},
        mcp=_empty_mcp(),
        github_mutations=0,
        drift_classifications=[],
        blockers=[],
        unknowns=[],
        residual_risks=[],
        operator_gates_used=[],
        operator_gates_needed=[],
        next_legal_action=action,
    )


def test_built_envelope_validates() -> None:
    envelope = _build_fixture_envelope()
    errors = list(_validator().iter_errors(envelope))
    assert errors == []


def test_envelope_authority_fields_are_fixed_regardless_of_input() -> None:
    envelope = _build_fixture_envelope()
    assert envelope["merge_authorized"] is False
    assert envelope["activation_authorized"] is False
    assert envelope["authority"] == "NONE"
    assert envelope["is_canonical_truth"] is False


def test_envelope_workstreams_sorted_by_id() -> None:
    envelope = _build_fixture_envelope()
    ids = [workstream["workstream_id"] for workstream in envelope["workstreams"]]
    assert ids == sorted(ids)


def test_model_calls_total_mismatch_raises_value_error() -> None:
    results = (_ws("W01", "PASS"),)
    decls: tuple[JoinDecl, ...] = ()
    join_results = evaluate_all(decls, results)
    with pytest.raises(ValueError):
        build_envelope(
            macro_id="x",
            results=results,
            join_results=join_results,
            macro_status="PASS_IMPLEMENTATION_PROGRAM_COMPLETE",
            model_calls={"team_lead": 1, "implementers": 0, "auditors": 0, "total": 0},
            mcp=_empty_mcp(),
            github_mutations=0,
            drift_classifications=[],
            blockers=[],
            unknowns=[],
            residual_risks=[],
            operator_gates_used=[],
            operator_gates_needed=[],
            next_legal_action="RETURN_TO_TEAM_LEAD",
        )


def test_invalid_macro_status_raises_envelope_invalid_with_sorted_errors() -> None:
    results = (_ws("W01", "PASS"),)
    decls: tuple[JoinDecl, ...] = ()
    join_results = evaluate_all(decls, results)
    with pytest.raises(EnvelopeInvalid) as excinfo:
        build_envelope(
            macro_id="x",
            results=results,
            join_results=join_results,
            macro_status="NOT_A_STATUS",
            model_calls={"team_lead": 0, "implementers": 0, "auditors": 0, "total": 0},
            mcp=_empty_mcp(),
            github_mutations=0,
            drift_classifications=[],
            blockers=[],
            unknowns=[],
            residual_risks=[],
            operator_gates_used=[],
            operator_gates_needed=[],
            next_legal_action="RETURN_TO_TEAM_LEAD",
        )
    errors = excinfo.value.errors
    assert errors == tuple(sorted(errors))
    assert any("macro_status" in error for error in errors)


def test_no_evidence_bytes_are_copied_in() -> None:
    envelope = _build_fixture_envelope()
    _assert_no_forbidden_keys(envelope)
